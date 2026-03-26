"""City of Charleston jurisdiction module.

Loads validated Table 3.1, height districts, parking, and Upper Peninsula
data from the JSON files in ``data/``.
"""

import json
from pathlib import Path
from typing import Optional

from app.jurisdictions.base import JurisdictionModule

_DATA = Path(__file__).parent / "data"

# Districts that have separate non-residential / residential rows in Table 3.1.
_SPLIT_ROW_BASES = {"CT", "LB", "GB", "LI", "HI"}

# Districts whose Table 3.1 values are all NR — constraints come from overlays.
_OVERLAY_GOVERNED = {"MU-1", "MU-1_WH", "MU-2", "MU-2_WH", "GP", "UP"}


def _load_json(filename: str) -> dict:
    with open(_DATA / filename) as f:
        return json.load(f)


class CharlestonModule(JurisdictionModule):
    name = "City of Charleston"
    state = "SC"
    slug = "charleston"
    tier = 1
    confidence_label = "Verified Data"
    solver_enabled = True
    has_height_district_overlays = True
    bulk_control_type = "lot_occupancy"
    height_unit = "stories"

    def __init__(self) -> None:
        self._table31 = _load_json("charleston_table_3_1.json")
        self._height = _load_json("charleston_height_districts.json")
        self._parking = _load_json("charleston_parking.json")
        self._up = _load_json("charleston_up_district.json")

    # -- districts ------------------------------------------------------------

    def get_district(self, code: str, use_type: str = "residential") -> Optional[dict]:
        districts = self._table31["districts"]

        # Split-row districts: append suffix based on use_type.
        base = code.split("_")[0] if "_" in code else code
        if base in _SPLIT_ROW_BASES:
            suffix = "_residential" if use_type == "residential" else "_non_res"
            key = f"{base}{suffix}"
            data = districts.get(key)
            if data:
                return data
            return None

        # Overlay-governed districts — return raw data with convenience flag.
        if code in _OVERLAY_GOVERNED:
            data = districts.get(code)
            if data:
                result = dict(data)
                result["_constraints_from_overlay"] = True
                return result
            return None

        return districts.get(code)

    def list_districts(self) -> list[str]:
        return list(self._table31["districts"].keys())

    # -- height districts -----------------------------------------------------

    def get_height_district(self, code: str) -> Optional[dict]:
        return self._height["districts"].get(code)

    # -- parking --------------------------------------------------------------

    def get_parking_table(self, on_peninsula: bool = False) -> dict:
        key = "on_peninsula" if on_peninsula else "off_peninsula"
        return self._parking.get(key, {})

    # -- overlays & boards ----------------------------------------------------

    def get_overlay_data(self) -> dict:
        return {
            "old_historic_district": {
                "abbrev": "OHD",
                "note": "BAR review required for all exterior work.",
            },
            "old_city_district": {
                "abbrev": "OCD",
                "note": "BAR review required. Demolition requires BAR approval.",
            },
            "historic_corridor": {
                "note": "BAR reviews visible-from-ROW facades.",
            },
            "historic_materials_demolition_purview": {
                "note": "BAR reviews demolition of structures >50 years old.",
            },
            "accommodation_overlay": {
                "note": "Permits hotel/inn use in certain residential zones with conditions.",
            },
            "landmark_overlay": {
                "note": "Individual landmarks — BAR review regardless of location.",
            },
        }

    def get_review_boards(self) -> list[dict]:
        return [
            {
                "name": "BAR-Large",
                "schedule": "2nd and 4th Wednesday",
                "max_items": 8,
                "note": "Major projects, new construction, demolition.",
            },
            {
                "name": "BAR-Small",
                "schedule": "1st and 3rd Wednesday",
                "max_items": 15,
                "note": "Minor exterior alterations, signs, fences.",
            },
            {
                "name": "BZA",
                "schedule": "3rd Tuesday",
                "note": "Variances, special exceptions, appeals.",
            },
            {
                "name": "Planning Commission",
                "schedule": "3rd Wednesday",
                "note": "Rezonings, comprehensive plan amendments, PUDs.",
            },
            {
                "name": "TRC",
                "schedule": "Weekly",
                "note": "Technical Review Committee — site plan review.",
            },
            {
                "name": "DRB",
                "schedule": "As needed",
                "note": "Design Review Board — DR district site plans.",
            },
        ]

    def get_fee_schedule(self) -> dict:
        return {
            "building_permit": {
                "base": 1660,
                "per_additional_1k_over_500k": 2,
                "plan_review_surcharge_pct": 50,
                "note": "$1,660 base + $2 per additional $1K of construction value over $500K, plus 50% plan review surcharge.",
            },
            "bar_application": {
                "residential_range": [25, 200],
                "commercial_range": [500, 1000],
            },
        }

    def get_construction_costs(self) -> dict:
        return {
            "adu_rules": {
                "max_sf": 850,
                "max_per_lot": 1,
                "max_total_units": 2,
                "additional_parking": 1,
                "owner_occupancy_required": True,
                "str_prohibited_if_adu": True,
            },
        }

    # -- AI context -----------------------------------------------------------

    def get_ai_context(self) -> str:
        district_count = len(self._table31["districts"])
        height_count = len(self._height["districts"])
        footnotes = self._table31.get("footnotes", {})
        return (
            f"City of Charleston — {district_count} zoning districts loaded from "
            f"Table 3.1 (Sec. 54-301, Nov 14 2025). {height_count} height district "
            f"overlays (Sec. 54-306). Footnote 8: universal 3× height cap. "
            f"Footnote 9: Old City Height Districts override Table 3.1. "
            f"Split-row districts (CT, LB, GB, LI, HI) have separate non-residential "
            f"and residential dimensional standards. MU-1, MU-2, GP, UP districts "
            f"have NO Table 3.1 dimensional limits — height controlled entirely by "
            f"overlay. Upper Peninsula uses incentive points system (base 4 stories, "
            f"max 12 via points, mandatory 10% workforce housing above 4 stories). "
            f"ADU rules: max 850 SF, 1 per lot, owner-occupancy required, no STR on "
            f"lots with ADUs. On-peninsula parking is less restrictive than off-peninsula "
            f"for office and retail. MU-WH zones have reduced parking: 0.5/workforce "
            f"unit, 1.0/market-rate unit, first 5,000 SF non-res exempt."
        )
