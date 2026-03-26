"""Construction cost framing engine.

Uses an additive-premiums model: base hard cost by building type, then
Charleston-specific premiums layered as multipliers.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Cost tables
# ---------------------------------------------------------------------------

_BASE_HARD_COSTS: dict[str, dict] = {
    # Residential
    "garden_style_3_4_story":   {"low": 150, "mid": 175, "high": 220, "unit": "$/SF"},
    "five_over_one_5_6_story":  {"low": 185, "mid": 225, "high": 310, "unit": "$/SF"},
    "townhouse_attached":       {"low": 130, "mid": 165, "high": 225, "unit": "$/SF"},
    "mid_rise_concrete_6_10":   {"low": 250, "mid": 325, "high": 440, "unit": "$/SF"},
    "high_rise_10_plus":        {"low": 325, "mid": 425, "high": 600, "unit": "$/SF"},
    "production_single_family": {"low": 120, "mid": 150, "high": 185, "unit": "$/SF"},
    "custom_peninsula":         {"low": 250, "mid": 375, "high": 600, "unit": "$/SF"},
    "custom_sullivans":         {"low": 375, "mid": 500, "high": 750, "unit": "$/SF"},
    # Mixed-use
    "mixed_use_wood_3_5":       {"low": 185, "mid": 240, "high": 325, "unit": "$/SF"},
    "mixed_use_podium_5_7":     {"low": 225, "mid": 290, "high": 400, "unit": "$/SF"},
    # Hospitality
    "hotel_boutique":           {"low": 225, "mid": 350, "high": 500, "unit": "$/SF", "allin_per_key_median": 500_000},
    "hotel_full_service":       {"low": 200, "mid": 300, "high": 425, "unit": "$/SF", "allin_per_key_median": 409_000},
    "hotel_limited_service":    {"low": 140, "mid": 200, "high": 275, "unit": "$/SF", "allin_per_key_median": 167_000},
    # Commercial
    "office_class_a":           {"low": 275, "mid": 375, "high": 525, "unit": "$/SF"},
    "flex_creative_conversion": {"low": 175, "mid": 250, "high": 375, "unit": "$/SF"},
    "flex_creative_new":        {"low": 225, "mid": 300, "high": 400, "unit": "$/SF"},
    # Adaptive reuse
    "warehouse_to_residential": {"low": 125, "mid": 200, "high": 375, "unit": "$/SF"},
    "warehouse_to_commercial":  {"low": 125, "mid": 225, "high": 375, "unit": "$/SF"},
    "historic_home_renovation": {"low": 250, "mid": 400, "high": 600, "unit": "$/SF"},
}

_PREMIUMS: dict[str, dict] = {
    "historic_district":    {"low": 1.20, "mid": 1.25, "high": 1.35, "label": "Historic District Compliance (+20-35%)"},
    "wind_load_coastal":    {"low": 1.07, "mid": 1.12, "high": 1.20, "label": "Coastal Wind Engineering (+7-20%)"},
    "flood_zone_ae":        {"low": 1.05, "mid": 1.07, "high": 1.10, "label": "Flood Zone AE (+5-10%)"},
    "flood_zone_coastal_a": {"low": 1.08, "mid": 1.10, "high": 1.12, "label": "Coastal A Zone (+8-12%)"},
    "flood_zone_ve":        {"low": 1.15, "mid": 1.15, "high": 1.15, "label": "Flood Zone VE (~+15%)"},
    "peninsula_logistics":  {"low": 1.10, "mid": 1.12, "high": 1.15, "label": "Peninsula Site Logistics (+10-15%)"},
}

HARD_TO_ALL_IN_MULTIPLIER = 1.25

_SITE_COSTS: dict[str, dict] = {
    "structured_parking_above_grade": {"low": 25_000, "mid": 30_000, "high": 35_000, "unit": "per space"},
    "below_grade_parking":            {"low": 80_000, "mid": 100_000, "high": 120_000, "unit": "per space",
                                       "red_flag": True,
                                       "warning": "Extremely problematic in Charleston due to high water table. Avoid if possible."},
    "surface_parking":                {"low": 3_000,  "mid": 5_000,   "high": 10_000,  "unit": "per space"},
    "site_development_per_unit":      {"low": 8_000,  "mid": 15_000,  "high": 25_000,  "unit": "per unit"},
}

_IMPACT_FEES: dict[str, dict] = {
    "cws_2026": {
        "water_impact_3_4": 4_620,
        "sewer_impact_per_eru": 6_670,
        "tap_fee_3_4": 500,
        "total_per_eru": 11_990,
    },
    "cws_2027": {
        "sewer_impact_per_eru": 8_160,
        "note": "Escalating ~10%+ annually through 2027",
    },
    "mt_pleasant_per_sfr": 6_509,
    "charleston_county": {
        "note": "No impact fees currently. ~2-year study underway as of March 2025.",
    },
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class CostEstimate:
    building_type: str
    gross_sf: int
    unit_count: int
    hard_cost_range: dict[str, float]
    premium_multiplier: dict[str, float]
    all_in_range: dict[str, float]
    parking_cost_range: dict[str, float]
    impact_fees: dict[str, float]
    total_range: dict[str, float]
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_base_costs() -> dict[str, dict]:
    """Return the full base hard-cost table."""
    return dict(_BASE_HARD_COSTS)


def get_premiums() -> dict[str, dict]:
    """Return the full premiums table."""
    return dict(_PREMIUMS)


def get_site_costs() -> dict[str, dict]:
    """Return the full site-cost table."""
    return dict(_SITE_COSTS)


def get_impact_fees() -> dict[str, dict]:
    """Return the full impact-fee table."""
    return dict(_IMPACT_FEES)


def estimate_costs(
    building_type: str,
    gross_sf: int,
    unit_count: int,
    premiums: Optional[list[str]] = None,
    parking_type: Optional[str] = None,
    parking_count: int = 0,
) -> CostEstimate:
    """Produce a cost estimate using the additive-premiums model.

    Args:
        building_type: Key into ``_BASE_HARD_COSTS``.
        gross_sf: Total gross square footage.
        unit_count: Number of dwelling / hotel units (for impact fees).
        premiums: List of premium keys to apply.
        parking_type: Key into ``_SITE_COSTS`` (e.g. ``"structured_parking_above_grade"``).
        parking_count: Number of parking spaces.

    Returns:
        A ``CostEstimate`` with low/mid/high ranges for every component.

    Raises:
        ValueError: If *building_type* is unknown.
    """
    if building_type not in _BASE_HARD_COSTS:
        raise ValueError(f"Unknown building type: {building_type!r}")

    base = _BASE_HARD_COSTS[building_type]
    premiums = premiums or []
    warnings: list[str] = []

    # 1. Base hard cost
    hard = {
        "low":  base["low"] * gross_sf,
        "mid":  base["mid"] * gross_sf,
        "high": base["high"] * gross_sf,
    }

    # 2. Compound premium multiplier
    mult = {"low": 1.0, "mid": 1.0, "high": 1.0}
    for p in premiums:
        if p not in _PREMIUMS:
            warnings.append(f"Unknown premium ignored: {p!r}")
            continue
        pdata = _PREMIUMS[p]
        mult["low"] *= pdata["low"]
        mult["mid"] *= pdata["mid"]
        mult["high"] *= pdata["high"]

    premiumed_hard = {
        "low":  hard["low"] * mult["low"],
        "mid":  hard["mid"] * mult["mid"],
        "high": hard["high"] * mult["high"],
    }

    # 3. All-in (hard-to-all-in multiplier)
    all_in = {
        "low":  premiumed_hard["low"] * HARD_TO_ALL_IN_MULTIPLIER,
        "mid":  premiumed_hard["mid"] * HARD_TO_ALL_IN_MULTIPLIER,
        "high": premiumed_hard["high"] * HARD_TO_ALL_IN_MULTIPLIER,
    }

    # 4. Parking
    parking_cost = {"low": 0.0, "mid": 0.0, "high": 0.0}
    if parking_type and parking_count > 0:
        if parking_type not in _SITE_COSTS:
            warnings.append(f"Unknown parking type: {parking_type!r}")
        else:
            pdata = _SITE_COSTS[parking_type]
            parking_cost = {
                "low":  pdata["low"] * parking_count,
                "mid":  pdata["mid"] * parking_count,
                "high": pdata["high"] * parking_count,
            }
            if pdata.get("red_flag"):
                warnings.append(pdata["warning"])

    # 5. Impact fees (CWS 2026 as default)
    cws = _IMPACT_FEES["cws_2026"]
    impact = {
        "total_per_eru": cws["total_per_eru"],
        "total": cws["total_per_eru"] * unit_count,
    }

    # 6. Grand total
    total = {
        "low":  all_in["low"] + parking_cost["low"] + impact["total"],
        "mid":  all_in["mid"] + parking_cost["mid"] + impact["total"],
        "high": all_in["high"] + parking_cost["high"] + impact["total"],
    }

    return CostEstimate(
        building_type=building_type,
        gross_sf=gross_sf,
        unit_count=unit_count,
        hard_cost_range=premiumed_hard,
        premium_multiplier=mult,
        all_in_range=all_in,
        parking_cost_range=parking_cost,
        impact_fees=impact,
        total_range=total,
        warnings=warnings,
    )
