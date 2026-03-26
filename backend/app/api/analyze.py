"""POST /api/analyze — Parcel feasibility analysis endpoint.

Orchestrates the constraint solver and Claude AI intelligence layers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.jurisdictions.registry import get_jurisdiction
from app.models import (
    AnalysisMetadata,
    AnalysisRequest,
    AnalysisResponse,
    CostFraming,
    DevelopmentEnvelope,
    ParcelInfo,
    ProcessTimeline,
    RiskMap,
    Scenario,
    Setbacks,
)
from app.services.ai_analysis import generate_analysis
from app.solver.engine import solve
from app.solver.models import SolverInput

logger = logging.getLogger(__name__)

router = APIRouter()


def _solver_envelope_to_response(env, solver_output) -> DevelopmentEnvelope:
    """Map solver DevelopmentEnvelope dataclass to the response model."""
    setbacks = Setbacks(
        front=env.setbacks.front,
        rear=env.setbacks.rear,
        side_sw=env.setbacks.side_sw,
        side_ne=env.setbacks.side_ne,
        front_rear_total=env.setbacks.front_rear_total,
        setback_notes="; ".join(env.setbacks.notes) if env.setbacks.notes else None,
    )

    return DevelopmentEnvelope(
        zoning_district=env.zoning_district,
        zoning_description=env.zoning_description,
        permitted_uses=[],
        conditional_uses=[],
        max_height_ft=env.effective_height_ft or env.max_height_ft,
        max_stories=int(env.effective_height_stories) if env.effective_height_stories else (
            int(env.max_height_stories) if env.max_height_stories else None
        ),
        far=env.far,
        max_lot_coverage_pct=None,
        density_units_per_acre=env.density_units_per_acre,
        setbacks=setbacks,
        buildable_area_sf=env.max_building_footprint_sf,
        parking_requirements=(
            f"{int(env.parking_required)} spaces ({env.parking_type})"
            if env.parking_required else None
        ),
        lot_occupancy_pct=env.lot_occupancy_pct,
        height_source=env.height_controlling_factor,
        binding_constraint=None,
    )


def _solver_scenarios_to_response(scenarios) -> list[Scenario]:
    """Map solver ScenarioOutput list to response Scenario models."""
    result = []
    for s in scenarios:
        unit_range = None
        if s.unit_count_low is not None:
            if s.unit_count_high and s.unit_count_high != s.unit_count_low:
                unit_range = f"{s.unit_count_low}-{s.unit_count_high} units"
            else:
                unit_range = f"{s.unit_count_low} unit{'s' if s.unit_count_low != 1 else ''}"

        constraints = list(s.constraints_satisfied)
        if s.variance_needed:
            constraints.extend(f"VARIANCE: {v}" for v in s.variance_needed)

        result.append(Scenario(
            name=s.name,
            unit_count_range=unit_range,
            description=s.description,
            constraints=constraints,
            risk_level=s.risk_level,
            estimated_timeline="",
            board_engagement="",
        ))
    return result


def _empty_envelope(req: AnalysisRequest) -> DevelopmentEnvelope:
    """Placeholder envelope for AI-only mode before Claude fills it in."""
    return DevelopmentEnvelope(
        zoning_district=req.zoning_district or "Unknown",
        zoning_description="AI-generated analysis",
        permitted_uses=[],
        conditional_uses=[],
        setbacks=Setbacks(),
    )


def _empty_scenarios() -> list[Scenario]:
    """Placeholder scenarios populated by AI commentary."""
    names = ["By-Right", "Optimized", "With Variance"]
    return [
        Scenario(
            name=n,
            description="See scenario commentary for AI-generated analysis.",
            constraints=[],
            risk_level="Moderate",
            estimated_timeline="See process timeline",
            board_engagement="See process timeline",
        )
        for n in names
    ]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_parcel(request: AnalysisRequest):
    module = get_jurisdiction(request.jurisdiction.value)

    # Build solver input
    solver_input = SolverInput(
        jurisdiction=request.jurisdiction.value,
        zoning_district=request.zoning_district or "",
        lot_size_sf=request.lot_size_sf,
        height_district=request.height_district,
        on_peninsula=request.on_peninsula,
        flood_zone=request.flood_zone,
        historic_overlay=request.historic_overlay,
    )

    # Run constraint solver
    solver_output = solve(solver_input)

    # Run Claude AI analysis
    ai_result = await generate_analysis(solver_output, module, request)

    # Build envelope from solver or AI
    if solver_output.solver_mode == "full" and solver_output.scenarios:
        envelope = _solver_envelope_to_response(
            solver_output.envelope, solver_output
        )
        scenarios = _solver_scenarios_to_response(solver_output.scenarios)
        # Enrich scenarios with AI timeline/board data
        if ai_result.scenario_commentary:
            commentary = {
                "By-Right": ai_result.scenario_commentary.by_right,
                "Optimized": ai_result.scenario_commentary.optimized,
                "With Variance": ai_result.scenario_commentary.with_variance,
            }
            for s in scenarios:
                if s.name in commentary and commentary[s.name]:
                    s.description = commentary[s.name]
    else:
        # AI-only: use AI envelope if available
        envelope = _empty_envelope(request)
        if ai_result.ai_only_envelope:
            ae = ai_result.ai_only_envelope
            envelope.max_height_ft = _safe_float(ae.get("max_height"))
            envelope.density_units_per_acre = _safe_float(ae.get("density"))
            envelope.parking_requirements = ae.get("parking")
            envelope.binding_constraint = ae.get("key_constraints")
        scenarios = _empty_scenarios()
        if ai_result.scenario_commentary:
            commentary = {
                "By-Right": ai_result.scenario_commentary.by_right,
                "Optimized": ai_result.scenario_commentary.optimized,
                "With Variance": ai_result.scenario_commentary.with_variance,
            }
            for s in scenarios:
                if s.name in commentary and commentary[s.name]:
                    s.description = commentary[s.name]

    # Set confidence fields based on tier
    confidence_tier = module.tier
    confidence_label = module.confidence_label
    disclaimer = None

    if module.tier == 3:
        disclaimer = module.get_ai_context()
    elif module.tier == 2:
        disclaimer = (
            f"This analysis uses AI-assisted estimates based on validated "
            f"research data for {module.name}. Dimensional standards have been "
            f"verified against the official ordinance but calculations are not "
            f"deterministic. Confirm critical figures with the local Planning "
            f"Department."
        )

    # Solver version string
    if solver_output.solver_mode == "full":
        solver_version = solver_output.jurisdiction_engine
    else:
        solver_version = f"{solver_output.jurisdiction_engine} (ai_only)"

    return AnalysisResponse(
        parcel=ParcelInfo(
            address=request.address,
            jurisdiction=request.jurisdiction.value,
            jurisdiction_display=module.name,
            zoning_district=request.zoning_district,
            lot_size_sf=request.lot_size_sf,
        ),
        envelope=envelope,
        scenarios=scenarios,
        risk_map=ai_result.risk_map,
        process_timeline=ai_result.process_timeline,
        cost_framing=ai_result.cost_framing,
        metadata=AnalysisMetadata(
            generated_at=datetime.now(timezone.utc),
            solver_version=solver_version,
            ai_model=ai_result.model_used,
            jurisdiction_module_version=f"{module.slug}-0.1.0",
        ),
        confidence_tier=confidence_tier,
        confidence_label=confidence_label,
        disclaimer=disclaimer,
    )


def _safe_float(val) -> float | None:
    """Try to extract a float from a value that might be a string."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        # Extract first number from string like "45 ft (unverified)"
        import re
        m = re.search(r"[\d.]+", val)
        return float(m.group()) if m else None
    return None
