"""Town of Mount Pleasant constraint solver engine.

Two modes:
  MODE 1 — UC-OD (Urban Corridor Overlay District): FAR-based (the only
           jurisdiction that uses FAR as primary bulk control).
  MODE 2 — Base Residential: 35 ft / 2.5 stories, building coverage-based.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from app.solver.base_engine import BaseSolverEngine
from app.solver.data.charleston_zoning import (
    AVG_UNIT_SIZE_SF,
    EFFICIENCY_RATIO,
    SF_PER_ACRE,
)
from app.solver.models import (
    BindingConstraint,
    DevelopmentEnvelope,
    ScenarioOutput,
    SetbackSet,
    SolverInput,
)

# ── UC-OD sub-district height limits ──
UC_OD_HEIGHTS: Dict[str, Dict[str, Any]] = {
    "UC-CBS": {
        "default_ft": 45,
        "default_stories": 3,
        "d1_e3_frontage_ft": 45,
        "d1_e3_interior_ft": 55,
        "near_residential_ft": 40,
        "near_residential_stories": 3,
    },
    "UC-JDB": {
        "neighborhood_commercial_ft": 55,
        "hospitality_ft": 80,
        "econ_dev_ft": 80,
        "health_wellness_ft": 80,
        "near_residential_ft": 40,
    },
}

UC_OD_DATA: Dict[str, Any] = {
    "name": "Urban Corridor Overlay District",
    "far": 1.5,
    "density_single_use_du_per_acre": 16,
    "density_mixed_use_du_per_acre": 20,
    "mixed_use_nonres_pct_min": 33,
    "ground_floor_retail_frontage_pct": 60,
    "min_setback_ft": 5,
    "open_space_pct": 8,
    "max_building_footprint_sf": 50000,
    "parking": {
        "single_family": 2.0,
        "duplex": 2.0,
        "townhouse": 2.0,
        "multi_family_low": 1.5,
        "multi_family_high": 2.0,
    },
}

BASE_RESIDENTIAL_DEFAULTS: Dict[str, Any] = {
    "name": "Base Residential District",
    "max_height_ft": 35,
    "max_height_stories": 2.5,
    "building_coverage_pct": 40,  # 30-50 range, 40 default
    "max_impervious_np_od_pct": 40,
    "parking_per_unit": 2.0,
    "setbacks": {
        "front": 25,
        "rear": 20,
        "side_total": 15,
        "side_sw": None,
        "side_ne": None,
    },
}


class MtPleasantSolverEngine(BaseSolverEngine):
    """Solver for Town of Mount Pleasant."""

    def _is_uc_od(self, solver_input: SolverInput) -> bool:
        district = solver_input.zoning_district.upper()
        return district.startswith("UC-") or district == "UC-OD"

    # ── MODE 1: UC-OD ──

    def _calculate_uc_od_envelope(
        self, solver_input: SolverInput
    ) -> DevelopmentEnvelope:
        data = UC_OD_DATA
        far = data["far"]

        # Height
        sub_district = solver_input.zoning_district.upper()
        height_ft: float = 45  # default
        height_stories: float = 3
        if sub_district in UC_OD_HEIGHTS:
            hd = UC_OD_HEIGHTS[sub_district]
            height_ft = hd.get("default_ft", 45)
            height_stories = hd.get("default_stories", height_ft / 12)

        # Setbacks
        sb_val = data["min_setback_ft"]
        setbacks = SetbackSet(
            front=sb_val, rear=sb_val,
            side_total=sb_val * 2, side_sw=sb_val, side_ne=sb_val,
        )

        # Footprint cap
        footprint_cap: Optional[float] = data["max_building_footprint_sf"]

        # Lot-based calculations
        max_gfa: Optional[float] = None
        max_footprint: Optional[float] = None
        max_units: Optional[int] = None
        density_basis: Optional[str] = None
        parking: Optional[float] = None

        if solver_input.lot_size_sf is not None:
            lot = solver_input.lot_size_sf
            lot_acres = lot / SF_PER_ACRE
            max_gfa = lot * far

            # Footprint: GFA / stories, capped at 50,000 SF
            raw_fp = max_gfa / height_stories if height_stories > 0 else max_gfa
            max_footprint = min(raw_fp, footprint_cap) if footprint_cap else raw_fp

            # Density
            is_mixed = solver_input.use_type == "mixed_use"
            density = (
                data["density_mixed_use_du_per_acre"]
                if is_mixed
                else data["density_single_use_du_per_acre"]
            )
            units_from_density = math.floor(lot_acres * density)
            units_from_gfa = math.floor(max_gfa * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF)
            max_units = min(units_from_density, units_from_gfa)
            density_basis = "per_acre_cap"

            # Parking
            subtype = solver_input.use_subtype or "multi_family"
            rate = data["parking"].get(subtype, 1.5)
            parking = math.ceil(max_units * rate)

        return DevelopmentEnvelope(
            zoning_district=solver_input.zoning_district,
            zoning_description=data["name"],
            max_height_ft=height_ft,
            max_height_stories=height_stories,
            effective_height_ft=height_ft,
            effective_height_stories=height_stories,
            height_controlling_factor="base_zoning",
            lot_occupancy_pct=None,
            far=far,
            density_units_per_acre=(
                data["density_mixed_use_du_per_acre"]
                if solver_input.use_type == "mixed_use"
                else data["density_single_use_du_per_acre"]
            ),
            density_basis=density_basis,
            setbacks=setbacks,
            max_building_footprint_sf=max_footprint,
            max_gross_floor_area_sf=max_gfa,
            max_units=max_units,
            parking_required=parking,
            parking_type="uc_od",
        )

    # ── MODE 2: Base Residential ──

    def _calculate_base_res_envelope(
        self, solver_input: SolverInput
    ) -> DevelopmentEnvelope:
        data = BASE_RESIDENTIAL_DEFAULTS
        height_ft = data["max_height_ft"]
        height_stories = data["max_height_stories"]
        coverage = data["building_coverage_pct"]

        sb_data = data["setbacks"]
        setbacks = SetbackSet(
            front=sb_data["front"],
            rear=sb_data["rear"],
            side_total=sb_data["side_total"],
            side_sw=sb_data.get("side_sw"),
            side_ne=sb_data.get("side_ne"),
        )

        max_footprint: Optional[float] = None
        max_gfa: Optional[float] = None
        max_units: Optional[int] = None
        parking: Optional[float] = None

        if solver_input.lot_size_sf is not None:
            lot = solver_input.lot_size_sf
            max_footprint = lot * (coverage / 100.0)
            max_gfa = max_footprint * height_stories
            units_from_gfa = math.floor(max_gfa * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF)
            # Conservative: 1 unit for base residential unless large lot
            if solver_input.use_subtype in ("single_family", None):
                max_units = 1
            else:
                max_units = units_from_gfa
            parking = math.ceil((max_units or 1) * data["parking_per_unit"])

        return DevelopmentEnvelope(
            zoning_district=solver_input.zoning_district,
            zoning_description=data["name"],
            max_height_ft=height_ft,
            max_height_stories=height_stories,
            effective_height_ft=height_ft,
            effective_height_stories=height_stories,
            height_controlling_factor="base_zoning",
            lot_occupancy_pct=coverage,
            far=None,
            density_units_per_acre=None,
            density_basis="min_lot_area_per_unit",
            setbacks=setbacks,
            max_building_footprint_sf=max_footprint,
            max_gross_floor_area_sf=max_gfa,
            max_units=max_units,
            parking_required=parking,
            parking_type="base_residential",
        )

    # ── Interface ──

    def calculate_envelope(
        self, district_data: Dict[str, Any], solver_input: SolverInput
    ) -> DevelopmentEnvelope:
        if self._is_uc_od(solver_input):
            return self._calculate_uc_od_envelope(solver_input)
        return self._calculate_base_res_envelope(solver_input)

    def calculate_scenarios(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[ScenarioOutput]:
        max_u = envelope.max_units
        max_gfa = envelope.max_gross_floor_area_sf
        eff_stories = envelope.effective_height_stories

        br_units = math.floor(max_u * 0.8) if max_u is not None else None
        if br_units is not None and br_units < 1 and max_u and max_u >= 1:
            br_units = 1

        by_right = ScenarioOutput(
            name="By-Right",
            risk_level="Low",
            unit_count_low=br_units,
            unit_count_high=br_units,
            gross_floor_area_sf=max_gfa * 0.8 if max_gfa else None,
            stories=eff_stories,
            description="Conservative development within all current standards.",
            constraints_satisfied=self._satisfied(envelope),
            constraints_exceeded=[],
            variance_needed=[],
        )

        optimized = ScenarioOutput(
            name="Optimized",
            risk_level="Moderate",
            unit_count_low=max_u,
            unit_count_high=max_u,
            gross_floor_area_sf=max_gfa,
            stories=eff_stories,
            description="Maximizes yield within all dimensional constraints.",
            constraints_satisfied=self._satisfied(envelope),
            constraints_exceeded=[],
            variance_needed=[],
        )

        # Variance: +15-20% density
        var_units = None
        var_gfa = max_gfa
        variances: List[str] = []
        if max_u is not None:
            bump = max(math.ceil(max_u * 0.15), 1)
            var_units = max_u + bump
            variances.append(
                f"Density: requesting {bump} additional units via variance"
            )

        with_variance = ScenarioOutput(
            name="With Variance",
            risk_level="High",
            unit_count_low=var_units,
            unit_count_high=var_units,
            gross_floor_area_sf=var_gfa,
            stories=eff_stories,
            description="Exceeds density cap — requires Town Council variance.",
            constraints_satisfied=self._satisfied(envelope),
            constraints_exceeded=[v.split(":")[0] for v in variances],
            variance_needed=variances,
        )

        return [by_right, optimized, with_variance]

    def _satisfied(self, envelope: DevelopmentEnvelope) -> List[str]:
        out = []
        if envelope.effective_height_ft is not None:
            out.append(f"Height: {envelope.effective_height_ft:.0f} ft")
        if envelope.far is not None:
            out.append(f"FAR: {envelope.far}")
        if envelope.lot_occupancy_pct is not None:
            out.append(f"Building coverage: {envelope.lot_occupancy_pct}%")
        if envelope.parking_required is not None:
            out.append(f"Parking: {envelope.parking_required:.0f} spaces")
        return out

    def identify_binding_constraints(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[BindingConstraint]:
        constraints: List[BindingConstraint] = []

        if envelope.far is not None:
            constraints.append(
                BindingConstraint(
                    constraint_name="FAR",
                    constraint_value=str(envelope.far),
                    is_binding=True,
                    explanation="Floor Area Ratio is the primary bulk control in UC-OD",
                )
            )

        if envelope.max_units is not None and envelope.max_gross_floor_area_sf is not None:
            units_from_gfa = math.floor(
                envelope.max_gross_floor_area_sf * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF
            )
            density_binding = envelope.max_units < units_from_gfa
            constraints.append(
                BindingConstraint(
                    constraint_name="Density",
                    constraint_value=f"{envelope.max_units} units",
                    is_binding=density_binding,
                    explanation=(
                        f"Density cap: {envelope.density_units_per_acre} du/ac"
                        if envelope.density_units_per_acre
                        else "Density limit"
                    ),
                )
            )

        if envelope.effective_height_ft is not None:
            constraints.append(
                BindingConstraint(
                    constraint_name="Height",
                    constraint_value=f"{envelope.effective_height_ft:.0f} ft",
                    is_binding=True,
                    explanation="Mount Pleasant uses feet-based height caps",
                )
            )

        return constraints
