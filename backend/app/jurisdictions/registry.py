"""Jurisdiction registry — maps slugs to module instances for all 12 jurisdictions."""

from app.jurisdictions.ai_only import AIOnlyJurisdiction
from app.jurisdictions.base import JurisdictionModule
from app.jurisdictions.charleston import CharlestonModule
from app.jurisdictions.mount_pleasant import MtPleasantModule
from app.jurisdictions.north_charleston import NorthCharlestonModule
from app.jurisdictions.unincorporated_county import UnincorporatedCountyModule

JURISDICTION_REGISTRY: dict[str, JurisdictionModule] = {
    # Tier 1 — Full solver with validated data
    "charleston": CharlestonModule(),
    "mount_pleasant": MtPleasantModule(),

    # Tier 2 — Research-backed AI (no solver, but injected audit data)
    "north_charleston": NorthCharlestonModule(),
    "unincorporated_county": UnincorporatedCountyModule(),

    # Tier 3 — AI-only with training data + disclaimers
    "sullivans_island": AIOnlyJurisdiction(
        name="Town of Sullivan's Island",
        slug="sullivans_island",
        planning_phone="843-883-3198",
    ),
    "isle_of_palms": AIOnlyJurisdiction(
        name="City of Isle of Palms",
        slug="isle_of_palms",
        planning_phone="843-886-6428",
    ),
    "folly_beach": AIOnlyJurisdiction(
        name="City of Folly Beach",
        slug="folly_beach",
        planning_phone="843-588-2447",
    ),
    "james_island": AIOnlyJurisdiction(
        name="Town of James Island",
        slug="james_island",
        planning_phone="843-795-4141",
    ),
    "kiawah": AIOnlyJurisdiction(
        name="Town of Kiawah Island",
        slug="kiawah",
        planning_phone="843-768-9166",
    ),
    "summerville": AIOnlyJurisdiction(
        name="Town of Summerville",
        slug="summerville",
        planning_phone="843-871-6000",
    ),
    "goose_creek": AIOnlyJurisdiction(
        name="City of Goose Creek",
        slug="goose_creek",
        planning_phone="843-797-6220",
    ),
    "hanahan": AIOnlyJurisdiction(
        name="City of Hanahan",
        slug="hanahan",
        planning_phone="843-747-5381",
    ),
}


def get_jurisdiction(slug: str) -> JurisdictionModule:
    """Return the jurisdiction module for *slug*.

    Raises ``ValueError`` for unknown slugs — every valid Charleston County
    jurisdiction should be in the registry.
    """
    module = JURISDICTION_REGISTRY.get(slug)
    if module is None:
        raise ValueError(
            f"Unknown jurisdiction: {slug!r}. "
            f"Valid slugs: {', '.join(sorted(JURISDICTION_REGISTRY))}"
        )
    return module


def list_jurisdictions() -> list[str]:
    """Return all registered jurisdiction slugs."""
    return list(JURISDICTION_REGISTRY.keys())
