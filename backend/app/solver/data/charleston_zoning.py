"""
City of Charleston Zoning Data — Table 3.1 Dimensional Standards.

Values are encoded from the City of Charleston Zoning Ordinance Table 3.1.
None means "NR" (Not Required / No Restriction) in the original table.

For split-row districts (LB, GB, LI, HI), the "residential" key contains
standards that apply when the use is residential, and "non_residential"
contains the commercial/industrial standards.

Density is expressed two ways:
  - "du_per_acre": units per gross acre (DR-6, DR-9, DR-12, UP)
  - "min_lot_per_unit": minimum lot area in SF per dwelling unit (SR-1, SR-2, DR-1, etc.)
  - None: density not regulated (MU districts, UP above 4 stories)
"""

from __future__ import annotations

from typing import Any, Dict

# Each district key maps to a dict with:
#   "name": human-readable name
#   "category": "residential" | "commercial" | "mixed_use" | "special"
#   "has_split_row": bool — whether residential vs non-res rows differ
#   "nr_everything": bool — all dimensional standards are NR
#   "workforce_housing_pct": float or None — required affordable %
#   "data" or "residential"/"non_residential": dimensional values dict
#
# Dimensional values dict keys:
#   min_lot_area_sf, min_lot_width_ft,
#   max_height_ft, max_height_stories,
#   lot_occupancy_pct,
#   setbacks: {front_rear_total, front, rear, side_total, side_sw, side_ne}
#   density_type: "du_per_acre" | "min_lot_per_unit" | None
#   density_value: float or None
#   permitted_uses: List[str]
#   conditional_uses: List[str]

CHARLESTON_DISTRICTS: Dict[str, Dict[str, Any]] = {
    # ── Single-Family Residential ──
    "SR-1": {
        "name": "Single-Family Residential (Large Lot)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 9000,
            "min_lot_width_ft": 75,
            "max_height_ft": 35,
            "max_height_stories": 2.5,
            "lot_occupancy_pct": 40,
            "setbacks": {
                "front_rear_total": 50,
                "front": 25,
                "rear": 25,
                "side_total": 12,
                "side_sw": 6,
                "side_ne": 6,
            },
            "density_type": "min_lot_per_unit",
            "density_value": 9000,
            "permitted_uses": [
                "Single-family detached",
                "Accessory dwelling unit",
                "Home occupation",
            ],
            "conditional_uses": ["Group home", "Religious institution"],
        },
    },
    "SR-2": {
        "name": "Single-Family Residential (Standard)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 6000,
            "min_lot_width_ft": 60,
            "max_height_ft": 35,
            "max_height_stories": 2.5,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 40,
                "front": 20,
                "rear": 20,
                "side_total": 10,
                "side_sw": 5,
                "side_ne": 5,
            },
            "density_type": "min_lot_per_unit",
            "density_value": 6000,
            "permitted_uses": [
                "Single-family detached",
                "Accessory dwelling unit",
                "Home occupation",
            ],
            "conditional_uses": ["Duplex", "Bed and breakfast", "Group home"],
        },
    },
    "SR-3": {
        "name": "Single-Family Residential (Small Lot)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 35,
            "max_height_stories": 2.5,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 35,
                "front": 15,
                "rear": 20,
                "side_total": 8,
                "side_sw": 4,
                "side_ne": 4,
            },
            "density_type": "min_lot_per_unit",
            "density_value": 4500,
            "permitted_uses": [
                "Single-family detached",
                "Accessory dwelling unit",
                "Home occupation",
            ],
            "conditional_uses": ["Duplex", "Bed and breakfast", "Group home"],
        },
    },
    # ── Diverse Residential ──
    "DR-1": {
        "name": "Diverse Residential (Low Density)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 45,
            "max_height_stories": 3,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 30,
                "front": 15,
                "rear": 15,
                "side_total": 8,
                "side_sw": 3,
                "side_ne": 3,
            },
            "density_type": "min_lot_per_unit",
            "density_value": 2250,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
                "Accessory dwelling unit",
            ],
            "conditional_uses": ["Bed and breakfast", "Group home"],
        },
    },
    "DR-1F": {
        "name": "Diverse Residential (Flexible)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 2250,
            "min_lot_width_ft": 25,
            "max_height_ft": 45,
            "max_height_stories": 3,
            "lot_occupancy_pct": 75,
            "setbacks": {
                "front_rear_total": 3,
                "front": 25,
                "rear": 25,
                "side_total": 3,
                "side_sw": 0,
                "side_ne": 0,
            },
            "density_type": "min_lot_per_unit",
            "density_value": 2250,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
                "Accessory dwelling unit",
            ],
            "conditional_uses": ["Bed and breakfast", "Group home"],
        },
    },
    "DR-6": {
        "name": "Diverse Residential (6 du/ac)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 45,
            "max_height_stories": 3,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 30,
                "front": 15,
                "rear": 15,
                "side_total": 10,
                "side_sw": 5,
                "side_ne": 5,
            },
            "density_type": "du_per_acre",
            "density_value": 6,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
                "Accessory dwelling unit",
            ],
            "conditional_uses": [
                "Bed and breakfast",
                "Group home",
                "Religious institution",
            ],
        },
    },
    "DR-9": {
        "name": "Diverse Residential (9 du/ac)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 50,
            "max_height_stories": 3,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 20,
                "front": 10,
                "rear": 10,
                "side_total": 8,
                "side_sw": 3,
                "side_ne": 3,
            },
            "density_type": "du_per_acre",
            "density_value": 9,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
                "Accessory dwelling unit",
            ],
            "conditional_uses": [
                "Bed and breakfast",
                "Group home",
                "Live-work unit",
            ],
        },
    },
    "DR-12": {
        "name": "Diverse Residential (12 du/ac)",
        "category": "residential",
        "has_split_row": False,
        "nr_everything": False,
        "data": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 50,
            "max_height_stories": 3,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 20,
                "front": 10,
                "rear": 10,
                "side_total": 8,
                "side_sw": 3,
                "side_ne": 3,
            },
            "density_type": "du_per_acre",
            "density_value": 12,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
                "Accessory dwelling unit",
            ],
            "conditional_uses": [
                "Bed and breakfast",
                "Group home",
                "Live-work unit",
            ],
        },
    },
    # ── Commercial / Business ──
    "LB": {
        "name": "Limited Business",
        "category": "commercial",
        "has_split_row": True,
        "nr_everything": False,
        "residential": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 45,
            "max_height_stories": 3,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 20,
                "front": 10,
                "rear": 10,
                "side_total": 8,
                "side_sw": 3,
                "side_ne": 3,
            },
            "density_type": "du_per_acre",
            "density_value": 12,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
            ],
            "conditional_uses": ["Bed and breakfast", "Live-work unit"],
        },
        "non_residential": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": 45,
            "max_height_stories": 3,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Retail",
                "Office",
                "Restaurant",
                "Personal services",
            ],
            "conditional_uses": ["Drive-through", "Gas station"],
        },
    },
    "GB": {
        "name": "General Business",
        "category": "commercial",
        "has_split_row": True,
        "nr_everything": False,
        "residential": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 55,
            "max_height_stories": None,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 3,
                "front": None,
                "rear": 3,
                "side_total": 15,
                "side_sw": 9,
                "side_ne": 3,
            },
            "density_type": "du_per_acre",
            "density_value": 12,
            "permitted_uses": [
                "Single-family detached",
                "Duplex",
                "Townhouse",
                "Multi-family",
            ],
            "conditional_uses": ["Bed and breakfast", "Group home"],
        },
        "non_residential": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": 55,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
                "Personal services",
                "Entertainment",
            ],
            "conditional_uses": [
                "Drive-through",
                "Gas station",
                "Auto repair",
            ],
        },
    },
    "LI": {
        "name": "Light Industrial",
        "category": "commercial",
        "has_split_row": True,
        "nr_everything": False,
        "residential": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 55,
            "max_height_stories": None,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 20,
                "front": 10,
                "rear": 10,
                "side_total": 10,
                "side_sw": 5,
                "side_ne": 5,
            },
            "density_type": "du_per_acre",
            "density_value": 12,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
            ],
            "conditional_uses": [],
        },
        "non_residential": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": 55,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Light manufacturing",
                "Warehouse",
                "Office",
                "Flex space",
            ],
            "conditional_uses": ["Heavy manufacturing", "Outdoor storage"],
        },
    },
    "HI": {
        "name": "Heavy Industrial",
        "category": "commercial",
        "has_split_row": True,
        "nr_everything": False,
        "residential": {
            "min_lot_area_sf": 4500,
            "min_lot_width_ft": 45,
            "max_height_ft": 55,
            "max_height_stories": None,
            "lot_occupancy_pct": 50,
            "setbacks": {
                "front_rear_total": 20,
                "front": 10,
                "rear": 10,
                "side_total": 10,
                "side_sw": 5,
                "side_ne": 5,
            },
            "density_type": "du_per_acre",
            "density_value": 12,
            "permitted_uses": ["Multi-family", "Townhouse"],
            "conditional_uses": [],
        },
        "non_residential": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": 75,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Heavy manufacturing",
                "Warehouse",
                "Distribution",
                "Outdoor storage",
            ],
            "conditional_uses": ["Hazardous materials"],
        },
    },
    # ── Mixed-Use (NR-everything districts) ──
    "MU-1": {
        "name": "Mixed-Use 1",
        "category": "mixed_use",
        "has_split_row": False,
        "nr_everything": True,
        "workforce_housing_pct": None,
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
            ],
            "conditional_uses": ["Entertainment", "Religious institution"],
        },
    },
    "MU-2": {
        "name": "Mixed-Use 2",
        "category": "mixed_use",
        "has_split_row": False,
        "nr_everything": True,
        "workforce_housing_pct": None,
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
                "Entertainment",
            ],
            "conditional_uses": [],
        },
    },
    "MU-1/WH": {
        "name": "Mixed-Use 1 / Workforce Housing",
        "category": "mixed_use",
        "has_split_row": False,
        "nr_everything": True,
        "workforce_housing_pct": 20,
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
            ],
            "conditional_uses": [],
        },
    },
    "MU-2/WH": {
        "name": "Mixed-Use 2 / Workforce Housing",
        "category": "mixed_use",
        "has_split_row": False,
        "nr_everything": True,
        "workforce_housing_pct": 20,
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
                "Entertainment",
            ],
            "conditional_uses": [],
        },
    },
    # ── Special Districts (NR-everything) ──
    "GP": {
        "name": "General Planned",
        "category": "special",
        "has_split_row": False,
        "nr_everything": True,
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": None,
            "density_value": None,
            "permitted_uses": [
                "Per approved master plan",
            ],
            "conditional_uses": [],
        },
    },
    "UP": {
        "name": "Upper Peninsula",
        "category": "special",
        "has_split_row": False,
        "nr_everything": True,
        "workforce_housing_pct": 10,  # above 4 stories
        "up_base_density": 26.4,  # du/ac for buildings ≤4 stories
        "data": {
            "min_lot_area_sf": None,
            "min_lot_width_ft": None,
            "max_height_ft": None,
            "max_height_stories": None,
            "lot_occupancy_pct": None,
            "setbacks": {
                "front_rear_total": None,
                "front": None,
                "rear": None,
                "side_total": None,
                "side_sw": None,
                "side_ne": None,
            },
            "density_type": "du_per_acre",
            "density_value": 26.4,
            "permitted_uses": [
                "Multi-family",
                "Townhouse",
                "Live-work unit",
                "Retail",
                "Office",
                "Restaurant",
                "Hotel",
                "Light manufacturing",
            ],
            "conditional_uses": ["Entertainment", "Heavy manufacturing"],
        },
    },
}


# Height district overlays (City of Charleston peninsula).
# Each maps to max stories allowed. BAR (Board of Architectural Review)
# bonus stories are tracked separately.
# Feet are calculated at 12 ft/story for residential.
CHARLESTON_HEIGHT_DISTRICTS: Dict[str, Dict[str, Any]] = {
    "2": {"max_stories": 2, "max_ft": 35, "bar_bonus_stories": 0},
    "2.5": {"max_stories": 2.5, "max_ft": 35, "bar_bonus_stories": 0},
    "3": {"max_stories": 3, "max_ft": 40, "bar_bonus_stories": 0},
    "3.5": {"max_stories": 3.5, "max_ft": 45, "bar_bonus_stories": 0},
    "4": {"max_stories": 4, "max_ft": 48, "bar_bonus_stories": 0},
    "4-12": {"max_stories": 4, "max_ft": 48, "bar_bonus_stories": 8},
    "5": {"max_stories": 5, "max_ft": 60, "bar_bonus_stories": 0},
    "6": {"max_stories": 6, "max_ft": 72, "bar_bonus_stories": 1},
    "7": {"max_stories": 7, "max_ft": 84, "bar_bonus_stories": 0},
    "8": {"max_stories": 8, "max_ft": 96, "bar_bonus_stories": 0},
    "85/200": {"max_stories": 7, "max_ft": 85, "bar_bonus_stories": 0},
    "12": {"max_stories": 12, "max_ft": 144, "bar_bonus_stories": 0},
}

# Parking rates — City of Charleston
CHARLESTON_PARKING = {
    "on_peninsula": {
        "single_family": 2.0,
        "duplex": 2.0,
        "multi_family": 1.5,
        "multi_family_wh": 1.0,       # MU/WH districts
        "affordable_housing": 0.25,    # 1 per 4 units
        "hotel": 0.667,               # 2 per 3 sleeping units
        "office_per_sf": 1 / 500,
        "retail_per_sf": 1 / 400,
        "restaurant_per_sf": 1 / 100,  # per patron area SF
    },
    "off_peninsula": {
        "single_family": 2.0,
        "duplex": 2.0,
        "multi_family": 1.5,
        "multi_family_wh": 1.0,
        "hotel": 0.667,
        "office_per_sf": 1 / 240,
        "retail_per_sf": 1 / 200,
        "restaurant_per_sf": 1 / 90,
    },
    "mu_wh": {
        "workforce_housing": 0.5,      # 1 per 2 units
        "market_rate": 1.0,
        "first_5000_sf_exempt": True,   # first 5,000 SF non-res exempt
        "office_per_sf": 1 / 600,
        "retail_per_sf": 1 / 400,
    },
    "up": {
        "workforce_housing": 0.5,
        "all_other_residential": 1.0,
        "offsite_allowed_ft": 1500,     # within 1,500 ft with 10-yr lease
    },
}

FT_PER_STORY = 12.0
DEFAULT_HALF_ROW_WIDTH_FT = 25.0
AVG_UNIT_SIZE_SF = 750.0
EFFICIENCY_RATIO = 0.85
SF_PER_ACRE = 43560.0
SF_PER_PARKING_SPACE_SURFACE = 325.0  # 300-350 average
STRUCTURED_PARKING_COST_PER_SPACE = 30000  # $25k-$35k midpoint
BELOW_GRADE_PARKING_COST_PER_SPACE_LOW = 80000
BELOW_GRADE_PARKING_COST_PER_SPACE_HIGH = 120000
