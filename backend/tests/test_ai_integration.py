"""Tests for the Claude AI integration layer.

All tests mock the Anthropic API client — no real API calls.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from app.jurisdictions.registry import JURISDICTION_REGISTRY, get_jurisdiction
from app.models.analysis import AnalysisRequest, Jurisdiction, UseType
from app.prompts.feasibility_engine import (
    ENGINE_VOICE_PROMPT,
    PRELIMINARY_MODE_PROMPT,
    RESEARCH_BACKED_MODE_PROMPT,
    SOLVER_ASSISTED_MODE_PROMPT,
    ZONING_CORRECTIONS_PROMPT,
    build_system_prompt,
)
from app.prompts.jurisdiction_context import build_jurisdiction_context
from app.services.ai_analysis import (
    AIAnalysisResult,
    _extract_json,
    _fallback_result,
    _parse_ai_response,
    build_user_message,
    generate_analysis,
)
from app.solver.models import (
    BindingConstraint,
    DevelopmentEnvelope,
    ScenarioOutput,
    SetbackSet,
    SolverOutput,
)


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

SAMPLE_AI_RESPONSE = {
    "risk_map": {
        "historic_overlay": "Property is within the Old and Historic District.",
        "flood_zone": "Zone AE with BFE of 11 ft NAVD88.",
        "building_category": "Residential new construction.",
        "accommodation_overlay": "Not in accommodation overlay.",
        "community_sensitivity": "Moderate — established residential neighborhood.",
        "recent_board_decisions": "BAR has approved similar projects on adjacent parcels.",
        "environmental_constraints": "Standard tree protection ordinance applies.",
    },
    "process_timeline": {
        "required_boards": ["BAR-Large", "TRC", "Building Permits"],
        "review_sequence": "BAR concept → BAR final → TRC → Building permit",
        "estimated_meetings": "3-5 meetings",
        "estimated_months": "6-10",
        "current_backlog": "BAR-Large running ~6 weeks between meetings.",
        "additional_permits": ["Stormwater permit", "Encroachment permit"],
    },
    "cost_framing": {
        "building_type_assumed": "garden_style_3_4_story",
        "base_hard_cost_range": "$150-$220/SF",
        "premiums_applied": ["Historic district +25%", "Flood zone AE +7%"],
        "adjusted_hard_cost_range": "$200-$295/SF",
        "all_in_estimate_range": "$250-$370/SF",
        "parking_cost_note": "Surface parking estimated at $5-8K per space.",
        "impact_fees_note": "CWS 2026: $11,990 per ERU.",
        "tax_credit_eligibility": "Federal 20% HTC available for income-producing rehab.",
        "bailey_bill_eligible": True,
        "total_project_cost_range": "$2.5M-$4.1M",
    },
    "scenario_commentary": {
        "by_right": "A by-right development fits comfortably within DR-9 parameters.",
        "optimized": "Optimized scenario maximizes density at 12 units per acre.",
        "with_variance": "Variance scenario would require BZA approval for height.",
    },
    "executive_summary": "This DR-9 parcel supports mid-density residential development.",
}

SAMPLE_AI_ONLY_RESPONSE = {
    **SAMPLE_AI_RESPONSE,
    "ai_only_envelope": {
        "max_height": "No explicit limit (most districts)",
        "density": "Varies by district — R-3 allows ~7 du/ac",
        "setbacks": "R-3: front 25 ft, side 7.5 ft, rear 20 ft",
        "parking": "2 spaces per dwelling unit",
        "key_constraints": "NBRD allows highest density with shared parking",
    },
}


def _make_request(**overrides) -> AnalysisRequest:
    defaults = {
        "jurisdiction": Jurisdiction.CHARLESTON,
        "address": "123 King St",
        "zoning_district": "DR-9",
        "lot_size_sf": 10000.0,
        "height_district": "6",
        "on_peninsula": True,
    }
    defaults.update(overrides)
    return AnalysisRequest(**defaults)


def _make_solver_output(**overrides) -> SolverOutput:
    defaults = {
        "envelope": DevelopmentEnvelope(
            zoning_district="DR-9",
            zoning_description="Diverse Residential",
            max_height_ft=50.0,
            max_height_stories=3.5,
            effective_height_ft=50.0,
            effective_height_stories=3.5,
            lot_occupancy_pct=75.0,
            density_units_per_acre=9.0,
            setbacks=SetbackSet(front=10.0, rear=10.0, side_sw=4.0, side_ne=4.0),
            max_building_footprint_sf=7500.0,
            max_units=2,
            parking_required=4.0,
            parking_type="off-street",
        ),
        "scenarios": [
            ScenarioOutput(name="By-Right", risk_level="Low", unit_count_low=1, unit_count_high=1),
            ScenarioOutput(name="Optimized", risk_level="Moderate", unit_count_low=2, unit_count_high=2),
            ScenarioOutput(name="With Variance", risk_level="High", unit_count_low=3, unit_count_high=4),
        ],
        "binding_constraints": [
            BindingConstraint(
                constraint_name="density",
                constraint_value="9 du/ac",
                is_binding=True,
                explanation="Density is the binding constraint at 2 units.",
            ),
        ],
        "solver_mode": "full",
        "jurisdiction_engine": "charleston_v1",
    }
    defaults.update(overrides)
    return SolverOutput(**defaults)


def _mock_anthropic_response(content: dict) -> MagicMock:
    """Build a mock that mimics anthropic.messages.create() response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(content))]
    mock_response.usage.input_tokens = 500
    mock_response.usage.output_tokens = 1200
    return mock_response


# ---------------------------------------------------------------------------
# 1. Test prompt construction
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    def test_tier1_system_prompt_includes_solver_mode(self):
        module = get_jurisdiction("charleston")
        prompt = build_system_prompt(module)
        assert "SOLVER-ASSISTED MODE" in prompt
        assert "RESEARCH-BACKED AI MODE" not in prompt
        assert "PRELIMINARY ANALYSIS MODE" not in prompt

    def test_tier2_system_prompt_includes_research_mode(self):
        module = get_jurisdiction("north_charleston")
        prompt = build_system_prompt(module)
        assert "RESEARCH-BACKED AI MODE" in prompt
        assert "SOLVER-ASSISTED MODE" not in prompt

    def test_tier3_system_prompt_includes_preliminary_mode(self):
        module = get_jurisdiction("sullivans_island")
        prompt = build_system_prompt(module)
        assert "PRELIMINARY ANALYSIS MODE" in prompt
        assert "Sullivan's Island" in prompt
        assert "SOLVER-ASSISTED MODE" not in prompt

    def test_all_prompts_include_engine_voice_and_corrections(self):
        for slug in ["charleston", "north_charleston", "sullivans_island"]:
            module = get_jurisdiction(slug)
            prompt = build_system_prompt(module)
            assert "ParcelIQ.ai" in prompt
            assert "CRITICAL ZONING CORRECTIONS" in prompt
            assert "OUTPUT FORMAT" in prompt

    def test_user_message_includes_solver_output(self):
        req = _make_request()
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()
        msg = build_user_message(solver, module, req)
        assert "Solver-assisted" in msg
        assert "CONSTRAINT SOLVER OUTPUT" in msg
        assert "DR-9" in msg

    def test_user_message_ai_only_mode(self):
        req = _make_request(
            jurisdiction=Jurisdiction.NORTH_CHARLESTON,
            zoning_district="R-3",
        )
        module = get_jurisdiction("north_charleston")
        solver = SolverOutput(solver_mode="ai_only", jurisdiction_engine="north_charleston_ai")
        msg = build_user_message(solver, module, req)
        assert "AI-only" in msg
        assert "CONSTRAINT SOLVER OUTPUT" not in msg
        assert "JURISDICTION REGULATORY CONTEXT" in msg

    def test_user_message_includes_parcel_details(self):
        req = _make_request(
            flood_zone="AE",
            historic_overlay="Old and Historic District",
        )
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()
        msg = build_user_message(solver, module, req)
        assert "123 King St" in msg
        assert "FLOOD ZONE: AE" in msg
        assert "HISTORIC OVERLAY: Old and Historic District" in msg
        assert "HEIGHT DISTRICT: 6" in msg
        assert "On peninsula" in msg

    def test_user_message_no_lot_size(self):
        req = _make_request(lot_size_sf=None)
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()
        msg = build_user_message(solver, module, req)
        assert "Not provided" in msg

    def test_tier3_no_jurisdiction_context_injected(self):
        req = _make_request(
            jurisdiction=Jurisdiction.SULLIVANS_ISLAND,
            zoning_district=None,
        )
        module = get_jurisdiction("sullivans_island")
        solver = SolverOutput(solver_mode="ai_only", jurisdiction_engine="sullivans_island_ai")
        msg = build_user_message(solver, module, req)
        # Tier 3 should NOT get JURISDICTION REGULATORY CONTEXT
        assert "JURISDICTION REGULATORY CONTEXT" not in msg


# ---------------------------------------------------------------------------
# 2. Test JSON parsing
# ---------------------------------------------------------------------------

class TestJSONParsing:
    def test_valid_json(self):
        raw = json.dumps(SAMPLE_AI_RESPONSE)
        parsed = _extract_json(raw)
        assert parsed["executive_summary"] == SAMPLE_AI_RESPONSE["executive_summary"]

    def test_json_with_markdown_fences(self):
        raw = "```json\n" + json.dumps(SAMPLE_AI_RESPONSE) + "\n```"
        parsed = _extract_json(raw)
        assert "risk_map" in parsed

    def test_json_with_preamble_text(self):
        raw = "Here is the analysis:\n\n" + json.dumps(SAMPLE_AI_RESPONSE) + "\n\nDone."
        parsed = _extract_json(raw)
        assert "executive_summary" in parsed

    def test_malformed_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _extract_json("this is not json at all")

    def test_parse_ai_response_maps_fields(self):
        result = _parse_ai_response(SAMPLE_AI_RESPONSE)
        assert result.risk_map.historic_overlay == "Property is within the Old and Historic District."
        assert result.process_timeline.required_boards == ["BAR-Large", "TRC", "Building Permits"]
        assert result.cost_framing.construction_type == "garden_style_3_4_story"
        assert result.cost_framing.bailey_bill_eligible is True
        assert result.scenario_commentary.by_right.startswith("A by-right")
        assert result.executive_summary.startswith("This DR-9 parcel")

    def test_parse_ai_only_response_includes_envelope(self):
        result = _parse_ai_response(SAMPLE_AI_ONLY_RESPONSE)
        assert result.ai_only_envelope is not None
        assert "max_height" in result.ai_only_envelope
        assert "density" in result.ai_only_envelope


# ---------------------------------------------------------------------------
# 3. Test fallback behavior
# ---------------------------------------------------------------------------

class TestFallbackBehavior:
    def test_fallback_result_has_error(self):
        result = _fallback_result("API timed out")
        assert result.error == "API timed out"
        assert "retry" in result.executive_summary.lower()
        assert result.tokens_used == 0

    @pytest.mark.asyncio
    async def test_api_failure_returns_fallback(self):
        import anthropic as anthropic_module

        req = _make_request()
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic_module.APIError(
            message="rate limited",
            request=MagicMock(),
            body=None,
        )

        with patch("app.services.ai_analysis.anthropic.Anthropic", return_value=mock_client):
            with patch("app.services.ai_analysis.time.sleep"):
                result = await generate_analysis(solver, module, req)

        assert result.error is not None
        assert "API error" in result.error

    @pytest.mark.asyncio
    async def test_json_parse_failure_retries_then_fallback(self):
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="not json")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        req = _make_request()
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()

        with patch("app.services.ai_analysis.anthropic.Anthropic", return_value=mock_client):
            with patch("app.services.ai_analysis.time.sleep"):
                result = await generate_analysis(solver, module, req)

        assert result.error is not None
        assert "JSON parse error" in result.error
        assert mock_client.messages.create.call_count == 3  # all retries exhausted


# ---------------------------------------------------------------------------
# 4. Test AI-only mode
# ---------------------------------------------------------------------------

class TestAIOnlyMode:
    @pytest.mark.asyncio
    async def test_ai_only_generates_envelope(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_anthropic_response(
            SAMPLE_AI_ONLY_RESPONSE
        )

        req = _make_request(
            jurisdiction=Jurisdiction.NORTH_CHARLESTON,
            zoning_district="R-3",
        )
        module = get_jurisdiction("north_charleston")
        solver = SolverOutput(
            solver_mode="ai_only",
            jurisdiction_engine="north_charleston_ai",
            confidence="moderate",
        )

        with patch("app.services.ai_analysis.anthropic.Anthropic", return_value=mock_client):
            result = await generate_analysis(solver, module, req)

        assert result.error is None
        assert result.ai_only_envelope is not None
        assert "max_height" in result.ai_only_envelope

    @pytest.mark.asyncio
    async def test_solver_assisted_no_envelope(self):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_anthropic_response(
            SAMPLE_AI_RESPONSE  # no ai_only_envelope key
        )

        req = _make_request()
        module = get_jurisdiction("charleston")
        solver = _make_solver_output()

        with patch("app.services.ai_analysis.anthropic.Anthropic", return_value=mock_client):
            result = await generate_analysis(solver, module, req)

        assert result.error is None
        assert result.ai_only_envelope is None


# ---------------------------------------------------------------------------
# 5. Test context builder
# ---------------------------------------------------------------------------

class TestContextBuilder:
    def test_all_jurisdictions_produce_context(self):
        for slug, module in JURISDICTION_REGISTRY.items():
            ctx = build_jurisdiction_context(module)
            assert len(ctx) > 50, f"{slug} context is too short"
            assert module.name in ctx
            assert "REGULATORY FRAMEWORK" in ctx
            assert "===" in ctx

    def test_charleston_context_includes_overlays(self):
        module = get_jurisdiction("charleston")
        ctx = build_jurisdiction_context(module)
        assert "OVERLAY DATA" in ctx
        assert "REVIEW BOARDS" in ctx
        assert "FEE SCHEDULE" in ctx
        assert "TAX CREDITS" in ctx

    def test_tier2_context_includes_research_data(self):
        module = get_jurisdiction("north_charleston")
        ctx = build_jurisdiction_context(module)
        assert "DIMENSIONAL STANDARDS DATA" in ctx
        assert "research audit" in ctx

    def test_tier3_context_includes_research_data_section(self):
        module = get_jurisdiction("sullivans_island")
        ctx = build_jurisdiction_context(module)
        assert "DIMENSIONAL STANDARDS DATA" in ctx

    def test_mt_pleasant_context_structure(self):
        module = get_jurisdiction("mount_pleasant")
        ctx = build_jurisdiction_context(module)
        assert "Town of Mount Pleasant" in ctx
        assert "REGULATORY FRAMEWORK" in ctx
