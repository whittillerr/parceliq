"""Unincorporated Charleston County jurisdiction module (AI-only).

County zoning uses the ZLDR (Zoning and Land Development Regulations).
This module provides comprehensive research context for Claude prompt injection.
"""

from app.jurisdictions.base import JurisdictionModule


class UnincorporatedCountyModule(JurisdictionModule):
    name = "Unincorporated Charleston County"
    state = "SC"
    slug = "unincorporated_county"
    tier = 2
    confidence_label = "Research-Backed"
    solver_enabled = False
    has_height_district_overlays = False
    bulk_control_type = "building_coverage"
    height_unit = "feet"

    def get_parking_table(self, on_peninsula: bool = False) -> dict:
        return {
            "residential": {"spaces_per": 2, "per": "dwelling_unit"},
            "transit_oriented_affordable": {
                "note": "Reduced rates available for affordable housing near transit.",
            },
        }

    def get_review_boards(self) -> list[dict]:
        return [
            {
                "name": "Planning Commission",
                "note": "Rezonings, comprehensive plan, subdivision review.",
            },
            {
                "name": "BZA",
                "note": "Variances, special exceptions, appeals.",
            },
        ]

    def get_ai_context(self) -> str:
        return (
            "Unincorporated Charleston County — AI-ONLY (no deterministic solver data). "
            "Uses ZLDR (Zoning and Land Development Regulations). "
            "IMPORTANT DISTRICT NAME CORRECTIONS: "
            "RM = Resource Management (NOT multi-family residential). "
            "There is NO RSH, CO, CG, or LI district — these codes do not exist in "
            "the County ZLDR. Do not hallucinate these districts. "
            "Agricultural districts: AG-8 (8 ac min), AG-15 (15 ac min), AG-25 (25 ac). "
            "Residential: R-4 (4 du/ac), R-1 (1 du/ac estate lots), RS (Rural Suburban). "
            "Commercial: CC (Community Commercial), RC (Resort Commercial), "
            "HC (Highway Commercial). Industrial: LI (Light Industrial), HI (Heavy Industrial). "
            "Overlays: ARRC-O (Ashley River Road Corridor Overlay — 50 ft buffer, "
            "enhanced landscaping, architectural standards). ARSC-O (Ashley River "
            "Special Conservation Overlay). "
            "PD (Planned Development) districts: flexible zoning for large tracts, "
            "requires master plan approval. Widely used for new subdivisions. "
            "Building coverage is the primary bulk control (not lot occupancy or FAR). "
            "Parking: 2 spaces per dwelling unit standard. "
            "No impact fees currently — a ~2-year study was underway as of March 2025. "
            "Recent ZLDR amendments have focused on sea-level rise adaptation, "
            "stormwater management, and rural character preservation."
        )
