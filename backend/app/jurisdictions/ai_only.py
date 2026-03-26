"""Tier 3 jurisdiction module — AI-only with training data + disclaimers.

Used for Sullivan's Island, Isle of Palms, Folly Beach, James Island,
Kiawah Island, Summerville, Goose Creek, Hanahan.
"""

from typing import Optional

from app.jurisdictions.base import JurisdictionModule


class AIOnlyJurisdiction(JurisdictionModule):
    """Tier 3 jurisdiction — no solver data, no research data.

    Claude generates analysis from training knowledge only.
    All outputs include prominent disclaimers directing users to verify
    with the local planning department.
    """

    tier = 3
    confidence_label = "Preliminary — Verify with Local Planning"
    solver_enabled = False
    has_height_district_overlays = False
    bulk_control_type = "none"
    height_unit = "unspecified"

    def __init__(
        self,
        name: str,
        slug: str,
        planning_phone: Optional[str] = None,
    ) -> None:
        self.name = name
        self.slug = slug
        self.state = "SC"
        self.planning_phone = planning_phone

    def get_district(self, code: str, use_type: str = "residential") -> Optional[dict]:
        return None

    def get_height_district(self, code: str) -> Optional[dict]:
        return None

    def get_parking_table(self, on_peninsula: bool = False) -> dict:
        return {"note": "Parking requirements not researched. Contact local planning department."}

    def get_overlay_data(self) -> dict:
        return {}

    def get_review_boards(self) -> list[dict]:
        return [{"note": f"Contact {self.name} for review board information."}]

    def get_fee_schedule(self) -> dict:
        return {"note": "Fee schedule not researched. Contact local planning department."}

    def get_construction_costs(self) -> dict:
        return {"note": "use_regional_defaults"}

    def get_ai_context(self) -> str:
        phone_str = f" at {self.planning_phone}" if self.planning_phone else ""
        return (
            f"JURISDICTION NOT INDEPENDENTLY RESEARCHED\n\n"
            f"ParcelIQ has not conducted a detailed zoning audit for {self.name}. "
            f"The analysis below is generated from Claude's general training knowledge "
            f"of {self.name} zoning and land use regulations. "
            f"ALL dimensional standards, height limits, setbacks, density figures, "
            f"and regulatory references should be independently verified with the "
            f"{self.name} Planning Department{phone_str} before making any "
            f"development decisions.\n\n"
            f"Construction cost estimates use Charleston metro benchmarks (RS Means CCI "
            f"0.84-0.88) and may not reflect conditions specific to {self.name}.\n\n"
            f"For verified feasibility analysis, contact Halfdays AI at only@halfdays.ai "
            f"to request a jurisdiction research audit for {self.name}."
        )

    def list_districts(self) -> list[str]:
        return []
