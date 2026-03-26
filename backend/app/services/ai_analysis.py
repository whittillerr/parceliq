"""Claude API orchestration for ParcelIQ feasibility intelligence.

Calls Claude to generate the narrative intelligence layers (risk map,
process timeline, cost framing, scenario commentary, executive summary).
For Tier 2/3 jurisdictions Claude also generates the development envelope.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import anthropic

from app.jurisdictions.base import JurisdictionModule
from app.models.analysis import (
    AnalysisRequest,
    CostFraming,
    ProcessTimeline,
    RiskMap,
    ScenarioCommentary,
)
from app.prompts.feasibility_engine import build_system_prompt
from app.prompts.jurisdiction_context import build_jurisdiction_context
from app.solver.models import SolverOutput

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
TEMPERATURE = 0.3
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AIAnalysisResult:
    risk_map: RiskMap = field(default_factory=RiskMap)
    process_timeline: ProcessTimeline = field(
        default_factory=lambda: ProcessTimeline(
            required_boards=[],
            review_sequence="",
            estimated_meetings="",
            estimated_months="",
            additional_permits=[],
        )
    )
    cost_framing: CostFraming = field(default_factory=CostFraming)
    scenario_commentary: ScenarioCommentary = field(default_factory=ScenarioCommentary)
    executive_summary: str = ""
    ai_only_envelope: Optional[Dict[str, Any]] = None
    model_used: str = MODEL
    tokens_used: int = 0
    generation_time_ms: int = 0
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Prompt construction helpers
# ---------------------------------------------------------------------------

def _format_parcel_info(req: AnalysisRequest, module: JurisdictionModule) -> str:
    """Build the parcel identification block for the user message."""
    lines = [
        f"PARCEL: {req.address} in {module.name}",
    ]
    if req.zoning_district:
        lines.append(f"ZONING DISTRICT: {req.zoning_district}")
    if req.lot_size_sf:
        acres = req.lot_size_sf / 43560
        lines.append(f"LOT SIZE: {req.lot_size_sf:,.0f} SF ({acres:.2f} acres)")
    else:
        lines.append("LOT SIZE: Not provided — use qualitative analysis")
    if req.height_district:
        lines.append(f"HEIGHT DISTRICT: {req.height_district} (Sec. 54-306)")
    if req.on_peninsula is not None:
        loc = "On peninsula" if req.on_peninsula else "Off peninsula"
        lines.append(f"LOCATION: {loc}")
    if req.flood_zone:
        lines.append(f"FLOOD ZONE: {req.flood_zone}")
    if req.historic_overlay:
        lines.append(f"HISTORIC OVERLAY: {req.historic_overlay}")
    return "\n".join(lines)


def _format_user_description(req: AnalysisRequest) -> str:
    """Build the user project description block."""
    use_str = ", ".join(u.value for u in req.use_types) if req.use_types else "Not specified"
    lines = [
        "USER'S PROJECT DESCRIPTION:",
        f"- Considering: {use_str}",
        f"- Scale: {req.approximate_scale or 'Not specified'}",
        f"- Existing conditions: {req.existing_conditions or 'Not specified'}",
        f"- Additional context: {req.additional_context or 'Not specified'}",
    ]
    return "\n".join(lines)


def _solver_output_to_dict(solver_output: SolverOutput) -> dict:
    """Serialize solver output to a JSON-safe dict via dataclass fields."""
    from dataclasses import asdict
    return asdict(solver_output)


def build_user_message(
    solver_output: Optional[SolverOutput],
    module: JurisdictionModule,
    req: AnalysisRequest,
) -> str:
    """Assemble the full user message for Claude."""
    parts = [_format_parcel_info(req, module)]

    # Analysis mode indicator
    if solver_output and solver_output.solver_mode == "full":
        parts.append(
            "ANALYSIS MODE: Solver-assisted — envelope numbers are "
            "code-calculated"
        )
        parts.append(
            "CONSTRAINT SOLVER OUTPUT:\n"
            + json.dumps(_solver_output_to_dict(solver_output), indent=2)
        )
        if solver_output.binding_constraints:
            bc_lines = ["BINDING CONSTRAINTS:"]
            for bc in solver_output.binding_constraints:
                if bc.is_binding:
                    bc_lines.append(
                        f"- {bc.constraint_name}: {bc.explanation}"
                    )
            if len(bc_lines) > 1:
                parts.append("\n".join(bc_lines))
    else:
        parts.append(
            "ANALYSIS MODE: AI-only — generate full analysis from "
            "jurisdiction context"
        )

    # Inject jurisdiction context for Tier 1 and 2
    if module.tier <= 2:
        parts.append(
            "JURISDICTION REGULATORY CONTEXT:\n"
            + build_jurisdiction_context(module)
        )

    parts.append(_format_user_description(req))
    parts.append("Generate the feasibility intelligence layers for this parcel.")

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# JSON parsing
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Parse JSON from Claude's response, handling markdown fences."""
    cleaned = text.strip()

    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Find first { to last }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]

    return json.loads(cleaned)


def _parse_ai_response(raw: dict) -> AIAnalysisResult:
    """Map Claude's JSON response to an AIAnalysisResult."""
    result = AIAnalysisResult()

    # risk_map
    rm = raw.get("risk_map", {})
    result.risk_map = RiskMap(
        historic_overlay=rm.get("historic_overlay"),
        flood_zone=rm.get("flood_zone"),
        building_category=rm.get("building_category"),
        accommodation_overlay=rm.get("accommodation_overlay"),
        community_sensitivity=rm.get("community_sensitivity"),
        recent_board_decisions=rm.get("recent_board_decisions"),
        environmental_constraints=rm.get("environmental_constraints"),
    )

    # process_timeline
    pt = raw.get("process_timeline", {})
    result.process_timeline = ProcessTimeline(
        required_boards=pt.get("required_boards", []),
        review_sequence=pt.get("review_sequence", ""),
        estimated_meetings=pt.get("estimated_meetings", ""),
        estimated_months=pt.get("estimated_months", ""),
        current_backlog=pt.get("current_backlog"),
        additional_permits=pt.get("additional_permits", []),
    )

    # cost_framing — map Claude's output keys to our model fields
    cf = raw.get("cost_framing", {})
    result.cost_framing = CostFraming(
        construction_type=cf.get("building_type_assumed"),
        base_hard_cost_range=cf.get("base_hard_cost_range"),
        applicable_premiums=cf.get("premiums_applied"),
        premium_adjusted_range=cf.get("adjusted_hard_cost_range"),
        all_in_estimate_range=cf.get("all_in_estimate_range"),
        impact_fees_estimate=cf.get("impact_fees_note"),
        tax_credit_eligibility=cf.get("tax_credit_eligibility"),
        bailey_bill_eligible=cf.get("bailey_bill_eligible"),
        total_cost_range=cf.get("total_project_cost_range"),
        cws_fee_warning=cf.get("parking_cost_note"),
    )

    # scenario_commentary
    sc = raw.get("scenario_commentary", {})
    result.scenario_commentary = ScenarioCommentary(
        by_right=sc.get("by_right", ""),
        optimized=sc.get("optimized", ""),
        with_variance=sc.get("with_variance", ""),
    )

    # executive_summary
    result.executive_summary = raw.get("executive_summary", "")

    # ai_only_envelope (only present for Tier 2/3)
    if "ai_only_envelope" in raw:
        result.ai_only_envelope = raw["ai_only_envelope"]

    return result


def _fallback_result(error_msg: str) -> AIAnalysisResult:
    """Return a graceful fallback when Claude API or parsing fails."""
    result = AIAnalysisResult(
        executive_summary=(
            "Analysis could not be completed. Please retry or contact support "
            "if the issue persists."
        ),
        error=error_msg,
    )
    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def generate_analysis(
    solver_output: Optional[SolverOutput],
    module: JurisdictionModule,
    user_input: AnalysisRequest,
) -> AIAnalysisResult:
    """Call Claude to generate feasibility intelligence layers.

    Parameters
    ----------
    solver_output:
        Constraint solver output (None or ai_only mode for Tier 2/3).
    module:
        The jurisdiction module providing regulatory context.
    user_input:
        The user's analysis request.

    Returns
    -------
    AIAnalysisResult with all intelligence layers populated.
    """
    system_prompt = build_system_prompt(module)
    user_message = build_user_message(solver_output, module, user_input)

    client = anthropic.Anthropic()
    last_error: Optional[str] = None

    for attempt in range(MAX_RETRIES):
        start_ms = int(time.time() * 1000)
        try:
            logger.info(
                "Claude API call attempt %d/%d for %s",
                attempt + 1,
                MAX_RETRIES,
                user_input.address,
            )

            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            elapsed_ms = int(time.time() * 1000) - start_ms
            raw_text = response.content[0].text
            tokens_used = (
                response.usage.input_tokens + response.usage.output_tokens
            )

            logger.info(
                "Claude response: %d tokens in %dms",
                tokens_used,
                elapsed_ms,
            )

            parsed = _extract_json(raw_text)
            result = _parse_ai_response(parsed)
            result.model_used = MODEL
            result.tokens_used = tokens_used
            result.generation_time_ms = elapsed_ms
            return result

        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error on attempt {attempt + 1}: {exc}"
            logger.warning(last_error)
        except anthropic.APIError as exc:
            last_error = f"Anthropic API error on attempt {attempt + 1}: {exc}"
            logger.warning(last_error)
        except Exception as exc:
            last_error = f"Unexpected error on attempt {attempt + 1}: {exc}"
            logger.warning(last_error)

        # Exponential backoff before retry
        if attempt < MAX_RETRIES - 1:
            time.sleep(BACKOFF_SECONDS[attempt])

    logger.error("All %d Claude API attempts failed: %s", MAX_RETRIES, last_error)
    return _fallback_result(last_error or "Unknown error")
