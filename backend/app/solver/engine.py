"""Main solver orchestrator.

Dispatches to jurisdiction-specific engines or returns ai_only mode
for unsupported jurisdictions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.solver.charleston_engine import CharlestonSolverEngine
from app.solver.data.charleston_zoning import CHARLESTON_DISTRICTS
from app.solver.models import (
    DevelopmentEnvelope,
    SolverInput,
    SolverOutput,
)
from app.solver.mt_pleasant_engine import MtPleasantSolverEngine

# Registry of supported jurisdictions
JURISDICTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "charleston": {
        "solver_enabled": True,
        "engine_class": CharlestonSolverEngine,
        "engine_name": "charleston_v1",
    },
    "mount_pleasant": {
        "solver_enabled": True,
        "engine_class": MtPleasantSolverEngine,
        "engine_name": "mt_pleasant_v1",
    },
    # These jurisdictions fall through to ai_only
    "north_charleston": {"solver_enabled": False, "engine_name": "north_charleston_stub"},
    "unincorporated": {"solver_enabled": False, "engine_name": "unincorporated_stub"},
    "sullivans_island": {"solver_enabled": False, "engine_name": "sullivans_island_stub"},
    "isle_of_palms": {"solver_enabled": False, "engine_name": "isle_of_palms_stub"},
    "folly_beach": {"solver_enabled": False, "engine_name": "folly_beach_stub"},
    "james_island": {"solver_enabled": False, "engine_name": "james_island_stub"},
    "kiawah": {"solver_enabled": False, "engine_name": "kiawah_stub"},
    "summerville": {"solver_enabled": False, "engine_name": "summerville_stub"},
    "goose_creek": {"solver_enabled": False, "engine_name": "goose_creek_stub"},
    "hanahan": {"solver_enabled": False, "engine_name": "hanahan_stub"},
}


def _empty_output(jurisdiction: str, engine_name: str) -> SolverOutput:
    return SolverOutput(
        envelope=DevelopmentEnvelope(),
        scenarios=[],
        binding_constraints=[],
        solver_mode="ai_only",
        jurisdiction_engine=engine_name,
    )


def solve(solver_input: SolverInput) -> SolverOutput:
    """Run the constraint solver for a given parcel.

    Returns SolverOutput with solver_mode="full" if a jurisdiction engine
    exists, or solver_mode="ai_only" if the jurisdiction isn't supported
    (letting Claude generate the full analysis).
    """
    jurisdiction = solver_input.jurisdiction
    registry_entry = JURISDICTION_REGISTRY.get(jurisdiction)

    if registry_entry is None:
        return _empty_output(jurisdiction, "unknown")

    engine_name = registry_entry["engine_name"]

    if not registry_entry.get("solver_enabled"):
        return _empty_output(jurisdiction, engine_name)

    engine = registry_entry["engine_class"]()

    # Load district data
    district_data = _load_district_data(jurisdiction, solver_input.zoning_district)
    if district_data is None:
        # Unknown zoning district — fall back to ai_only
        return SolverOutput(
            envelope=DevelopmentEnvelope(
                zoning_district=solver_input.zoning_district,
                zoning_description=f"Unknown district: {solver_input.zoning_district}",
            ),
            scenarios=[],
            binding_constraints=[],
            solver_mode="ai_only",
            jurisdiction_engine=engine_name,
        )

    # Run the engine
    envelope = engine.calculate_envelope(district_data, solver_input)
    scenarios = engine.calculate_scenarios(envelope, solver_input)
    binding = engine.identify_binding_constraints(envelope, solver_input)

    return SolverOutput(
        envelope=envelope,
        scenarios=scenarios,
        binding_constraints=binding,
        solver_mode="full",
        jurisdiction_engine=engine_name,
    )


def _load_district_data(
    jurisdiction: str, zoning_district: str
) -> Optional[Dict[str, Any]]:
    if jurisdiction == "charleston":
        return CHARLESTON_DISTRICTS.get(zoning_district)
    if jurisdiction == "mount_pleasant":
        # Mt Pleasant engine handles its own data lookup internally
        return {"_mt_pleasant": True}
    return None
