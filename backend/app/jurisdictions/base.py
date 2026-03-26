"""Abstract base class for jurisdiction data modules."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class JurisdictionModule(ABC):
    """Base class that every jurisdiction module must implement.

    Attributes:
        name: Human-readable jurisdiction name.
        state: Two-letter state code.
        slug: URL-safe identifier used in the registry.
        tier: Confidence tier (1=Verified Data, 2=Research-Backed, 3=Preliminary).
        confidence_label: Human-readable tier label.
        solver_enabled: True if this jurisdiction has structured constraint data
            suitable for the deterministic solver. False means AI-only context.
        has_height_district_overlays: True if height districts can override base zoning.
        bulk_control_type: How the jurisdiction limits building mass.
            "lot_occupancy" (Charleston), "far" (Mt Pleasant UC-OD),
            "building_coverage" (County), "none" (North Charleston).
        height_unit: Primary unit for height limits.
            "stories" (Charleston), "feet" (Mt Pleasant), "unspecified" (North Charleston).
    """

    name: str
    state: str = "SC"
    slug: str
    tier: int  # 1, 2, or 3
    confidence_label: str
    # Tier 1 = "Verified Data" — full constraint solver with validated zoning data
    # Tier 2 = "Research-Backed" — no solver, but Claude gets injected research data
    # Tier 3 = "Preliminary — Verify with Local Planning" — AI training knowledge only
    solver_enabled: bool
    has_height_district_overlays: bool
    bulk_control_type: str
    height_unit: str

    @property
    def has_solver(self) -> bool:
        return self.tier == 1

    # -- Data accessors -------------------------------------------------------

    def get_district(self, code: str, use_type: str = "residential") -> Optional[dict]:
        """Return dimensional standards for a zoning district.

        For split-row districts (e.g. GB non-res / GB residential) the
        *use_type* parameter selects which row to return.
        """
        return None

    def get_height_district(self, code: str) -> Optional[dict]:
        """Return height-district overlay data, or None if not applicable."""
        return None

    def get_parking_table(self, on_peninsula: bool = False) -> dict:
        """Return the parking requirements table.

        Charleston distinguishes on-peninsula vs off-peninsula rates.
        Other jurisdictions may ignore the flag.
        """
        return {}

    def get_overlay_data(self) -> dict:
        """Return overlay district metadata (historic, accommodation, etc.)."""
        return {}

    def get_review_boards(self) -> list[dict]:
        """Return review-board schedule and capacity info."""
        return []

    def get_fee_schedule(self) -> dict:
        """Return permit / application fee schedule."""
        return {}

    def get_construction_costs(self) -> dict:
        """Return jurisdiction-adjusted construction cost tables."""
        return {}

    @abstractmethod
    def get_ai_context(self) -> str:
        """Return a formatted text blob for Claude prompt injection.

        Every module must produce context — solver-backed modules include
        structured summaries; AI-only modules include the full research text.
        """
        ...

    def list_districts(self) -> list[str]:
        """Return all district codes available in this jurisdiction."""
        return []
