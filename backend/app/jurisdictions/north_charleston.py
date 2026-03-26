"""City of North Charleston jurisdiction module (AI-only).

North Charleston has limited publicly available dimensional data. This module
provides comprehensive research context for Claude prompt injection.
"""

from app.jurisdictions.base import JurisdictionModule


class NorthCharlestonModule(JurisdictionModule):
    name = "City of North Charleston"
    state = "SC"
    slug = "north_charleston"
    tier = 2
    confidence_label = "Research-Backed"
    solver_enabled = False
    has_height_district_overlays = False
    bulk_control_type = "none"
    height_unit = "unspecified"

    def get_review_boards(self) -> list[dict]:
        return [
            {
                "name": "Planning Commission",
                "note": "Rezonings, subdivisions, site plans.",
            },
            {
                "name": "Architectural/Design Review Board",
                "note": "Required in Olde North Charleston and Park Circle districts.",
            },
        ]

    def get_ai_context(self) -> str:
        return (
            "City of North Charleston — AI-ONLY (no deterministic solver data). "
            "Key zoning districts: "
            "R-1 (Single-family, min 10,000 SF lot, 25 ft front/10 ft side/25 ft rear), "
            "R-2 (Single/two-family, min 7,500 SF, 25/7.5/25 ft setbacks), "
            "R-3 (Multi-family, min 6,000 SF, 25/7.5/20 ft setbacks). "
            "B-1 (Neighborhood Business, 0 ft front/0 ft side/10 ft rear), "
            "B-2 (General Business, 0/0/10 ft setbacks). "
            "CRITICAL: Most districts have NO explicit height limit in the zoning code. "
            "The ONLY explicit height limit found is in the ON (Olde North Charleston) "
            "district at 25 ft. All other height limits come from building code or "
            "special overlay restrictions, not base zoning. "
            "NBRD (Navy Base Redevelopment District) is the major mixed-use framework — "
            "form-based code with sub-areas, separate from standard Euclidean zones. "
            "Recent amendments have focused on NBRD expansion and Park Circle area "
            "design standards. No impact fees currently. "
            "Architectural review required in Olde North Charleston and Park Circle."
        )
