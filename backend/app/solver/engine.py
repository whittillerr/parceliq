"""Main solver orchestrator.

Dispatches to jurisdiction-specific engines based on the tier system,
or returns ai_only mode for Tier 2/3 jurisdictions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.jurisdictions.registry import get_jurisdiction
from app.solver.charleston_engine import CharlestonSolverEngine
from app.solver.data.charleston_zoning import CHARLESTON_DISTRICTS
from app.solver.models import (
    DevelopmentEnvelope,
    SolverInput,
    SolverOutput,
)
from app.solver.mt_pleasant_engine import MtPleasantSolverEngine


def _empty_output(jurisdiction: str, engine_name: str) -> SolverOutput:
    return SolverOutput(
        envelope=DevelopmentEnvelope(),
        scenarios=[],
        binding_constraints=[],
        solver_mode="ai_only",
        jurisdiction_engine=engine_name,
    )


def solve(solver_input: SolverInput) -> SolverOutput:
    """Run the constraint solver for a given parcel.

    Tier 1 (Charleston, Mt Pleasant): Full solver path if zoning district provided.
    Tier 2 (N. Charleston, Unincorporated): AI-only with research context.
    Tier 3 (all others): AI-only with training knowledge + disclaimers.
    """
    module = get_jurisdiction(solver_input.jurisdiction)

    if module.tier == 1 and solver_input.zoning_district:
        # Full solver path
        if module.slug == "charleston":
            engine = CharlestonSolverEngine()
        elif module.slug == "mount_pleasant":
            engine = MtPleasantSolverEngine()
        else:
            return _empty_output(solver_input.jurisdiction, f"{module.slug}_stub")

        district_data = _load_district_data(module.slug, solver_input.zoning_district)
        if district_data is None:
            return SolverOutput(
                envelope=DevelopmentEnvelope(
                    zoning_district=solver_input.zoning_district,
                    zoning_description=f"Unknown district: {solver_input.zoning_district}",
                ),
                scenarios=[],
                binding_constraints=[],
                solver_mode="ai_only",
                jurisdiction_engine=f"{module.slug}_v1",
            )

        envelope = engine.calculate_envelope(district_data, solver_input)
        scenarios = engine.calculate_scenarios(envelope, solver_input)
        binding = engine.identify_binding_constraints(envelope, solver_input)

        return SolverOutput(
            envelope=envelope,
            scenarios=scenarios,
            binding_constraints=binding,
            solver_mode="full",
            jurisdiction_engine=f"{module.slug}_v1",
        )

    elif module.tier == 1 and not solver_input.zoning_district:
        # Tier 1 but no district — can't run solver
        lookup_hint = (
            "charleston-sc.gov/GIS" if module.slug == "charleston"
            else "mtpleasantgis.com"
        )
        return SolverOutput(
            envelope=DevelopmentEnvelope(),
            scenarios=[],
            binding_constraints=[],
            solver_mode="partial",
            jurisdiction_engine=f"{module.slug}_v1",
            warnings=[
                f"Zoning district not provided. Provide the district code for precise "
                f"calculations. Check your zoning at {lookup_hint}."
            ],
            confidence="moderate",
            ai_context=module.get_ai_context(),
        )

    else:
        # Tier 2 or 3 — no solver, AI handles everything
        return SolverOutput(
            envelope=DevelopmentEnvelope(),
            scenarios=[],
            binding_constraints=[],
            solver_mode="ai_only",
            jurisdiction_engine=f"{module.slug}_ai",
            confidence="moderate" if module.tier == 2 else "low",
            ai_context=module.get_ai_context(),
        )


def _load_district_data(
    jurisdiction: str, zoning_district: str
) -> Optional[Dict[str, Any]]:
    if jurisdiction == "charleston":
        return CHARLESTON_DISTRICTS.get(zoning_district)
    if jurisdiction == "mount_pleasant":
        return {"_mt_pleasant": True}
    return None
