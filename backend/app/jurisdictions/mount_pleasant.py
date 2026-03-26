"""Town of Mount Pleasant jurisdiction module.

Partial solver support: UC-OD overlay and base residential standards are
loaded from the validated JSON. Other districts are AI-context only.
"""

import json
from pathlib import Path
from typing import Optional

from app.jurisdictions.base import JurisdictionModule

_DATA = Path(__file__).parent / "data"


def _load_json(filename: str) -> dict:
    with open(_DATA / filename) as f:
        return json.load(f)


class MtPleasantModule(JurisdictionModule):
    name = "Town of Mount Pleasant"
    state = "SC"
    slug = "mount_pleasant"
    tier = 1
    confidence_label = "Verified Data"
    solver_enabled = True  # partial — UC-OD and base residential
    has_height_district_overlays = False
    bulk_control_type = "far"
    height_unit = "feet"

    def __init__(self) -> None:
        self._uc_od = _load_json("mt_pleasant_uc_od.json")

    # -- districts ------------------------------------------------------------

    def get_district(self, code: str, use_type: str = "residential") -> Optional[dict]:
        code_upper = code.upper().replace("-", "_")
        if code_upper in ("UC_OD", "UC-OD", "UCOD"):
            return self._uc_od.get("uc_od_base")
        if code_upper in ("UC_CBS", "UC-CBS"):
            return self._uc_od["sub_districts"].get("UC-CBS")
        if code_upper in ("UC_JDB", "UC-JDB"):
            return self._uc_od["sub_districts"].get("UC-JDB")
        # Base residential data is available for AI context.
        if code_upper in ("R_1", "R_2", "R_3", "R_4", "TH", "RM"):
            return self._uc_od.get("residential_base")
        return None

    def list_districts(self) -> list[str]:
        return ["UC-OD", "UC-CBS", "UC-JDB", "R-1", "R-2", "R-3", "R-4", "TH", "RM"]

    # -- parking --------------------------------------------------------------

    def get_parking_table(self, on_peninsula: bool = False) -> dict:
        return self._uc_od.get("parking", {})

    # -- review boards --------------------------------------------------------

    def get_review_boards(self) -> list[dict]:
        return [
            {
                "name": "DRB",
                "note": "Required in CDR-OD, UC-OD, SCW-OD, WG districts.",
            },
            {
                "name": "HDPC",
                "note": "Historic District Preservation Commission. Required in OV-HD.",
            },
        ]

    # -- fees -----------------------------------------------------------------

    def get_fee_schedule(self) -> dict:
        return {
            "impact_fee_per_sfr": 6509,
            "year": 2025,
        }

    # -- AI context -----------------------------------------------------------

    def get_ai_context(self) -> str:
        uc = self._uc_od.get("uc_od_base", {})
        return (
            f"Town of Mount Pleasant — UC-OD overlay: FAR {uc.get('far')}, "
            f"single-use residential density {uc.get('density_single_use_residential')} du/ac, "
            f"mixed-use density {uc.get('density_mixed_use')} du/ac (requires min 33% "
            f"nonresidential floor area). Max building footprint 50,000 SF. "
            f"Base residential: 35 ft / 2.5 stories max, flood hazard areas 40 ft. "
            f"UC-CBS sub-district: 45 ft / 3 floors default. UC-JDB sub-district: "
            f"55 ft neighborhood commercial, 80 ft hospitality/health. "
            f"Impact fee: $6,509 per single-family home (2025). "
            f"DRB required in UC-OD. January 2025 code rewrite effective May 1, 2025."
        )
