"""Tests for the construction cost framing engine."""

import pytest

from app.solver.cost_engine import estimate_costs, CostEstimate, HARD_TO_ALL_IN_MULTIPLIER


# ---------------------------------------------------------------------------
# 1. Garden-style 50,000 SF no premiums → hard cost $7.5M-$11M
# ---------------------------------------------------------------------------

def test_garden_style_no_premiums():
    est = estimate_costs(
        building_type="garden_style_3_4_story",
        gross_sf=50_000,
        unit_count=60,
        premiums=[],
    )
    assert isinstance(est, CostEstimate)
    # low: 150 * 50,000 = 7,500,000
    assert est.hard_cost_range["low"] == 150 * 50_000
    # high: 220 * 50,000 = 11,000,000
    assert est.hard_cost_range["high"] == 220 * 50_000
    assert 7_500_000 <= est.hard_cost_range["low"] <= est.hard_cost_range["high"] <= 11_000_000


# ---------------------------------------------------------------------------
# 2. Historic + flood AE premiums stack correctly
# ---------------------------------------------------------------------------

def test_premium_stacking():
    est = estimate_costs(
        building_type="garden_style_3_4_story",
        gross_sf=50_000,
        unit_count=60,
        premiums=["historic_district", "flood_zone_ae"],
    )
    # Low multiplier: 1.20 * 1.05 = 1.26
    expected_low_mult = 1.20 * 1.05
    assert abs(est.premium_multiplier["low"] - expected_low_mult) < 0.001

    # Mid multiplier: 1.25 * 1.07 = 1.3375
    expected_mid_mult = 1.25 * 1.07
    assert abs(est.premium_multiplier["mid"] - expected_mid_mult) < 0.001

    # High multiplier: 1.35 * 1.10 = 1.485
    expected_high_mult = 1.35 * 1.10
    assert abs(est.premium_multiplier["high"] - expected_high_mult) < 0.001

    # Verify hard cost includes premiums
    base_low = 150 * 50_000
    assert abs(est.hard_cost_range["low"] - base_low * expected_low_mult) < 1.0


# ---------------------------------------------------------------------------
# 3. Below-grade parking triggers red flag warning
# ---------------------------------------------------------------------------

def test_below_grade_parking_warning():
    est = estimate_costs(
        building_type="garden_style_3_4_story",
        gross_sf=50_000,
        unit_count=60,
        parking_type="below_grade_parking",
        parking_count=60,
    )
    assert len(est.warnings) > 0
    assert any("water table" in w.lower() for w in est.warnings)
    # Verify parking costs calculated
    assert est.parking_cost_range["low"] == 80_000 * 60
    assert est.parking_cost_range["high"] == 120_000 * 60


# ---------------------------------------------------------------------------
# 4. All-in multiplier (1.25x) applied correctly
# ---------------------------------------------------------------------------

def test_all_in_multiplier():
    est = estimate_costs(
        building_type="garden_style_3_4_story",
        gross_sf=50_000,
        unit_count=60,
    )
    assert HARD_TO_ALL_IN_MULTIPLIER == 1.25
    assert abs(est.all_in_range["mid"] - est.hard_cost_range["mid"] * 1.25) < 1.0


# ---------------------------------------------------------------------------
# 5. CWS impact fees for 40-unit multifamily
# ---------------------------------------------------------------------------

def test_cws_impact_fees_40_units():
    est = estimate_costs(
        building_type="garden_style_3_4_story",
        gross_sf=40_000,
        unit_count=40,
    )
    # CWS 2026 total_per_eru = 11,990
    assert est.impact_fees["total_per_eru"] == 11_990
    assert est.impact_fees["total"] == 11_990 * 40


# ---------------------------------------------------------------------------
# Edge case: unknown building type raises ValueError
# ---------------------------------------------------------------------------

def test_unknown_building_type():
    with pytest.raises(ValueError, match="Unknown building type"):
        estimate_costs(
            building_type="space_station",
            gross_sf=10_000,
            unit_count=1,
        )
