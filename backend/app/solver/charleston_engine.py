"""City of Charleston constraint solver engine.

Implements the 11-step calculation sequence for the City of Charleston
zoning ordinance, using lot occupancy (NOT FAR) as the primary bulk
control and stories (NOT feet) as the primary height control.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from app.solver.base_engine import BaseSolverEngine
from app.solver.data.charleston_zoning import (
    AVG_UNIT_SIZE_SF,
    CHARLESTON_DISTRICTS,
    CHARLESTON_HEIGHT_DISTRICTS,
    CHARLESTON_PARKING,
    DEFAULT_HALF_ROW_WIDTH_FT,
    EFFICIENCY_RATIO,
    FT_PER_STORY,
    SF_PER_ACRE,
    SF_PER_PARKING_SPACE_SURFACE,
)
from app.solver.models import (
    BindingConstraint,
    DevelopmentEnvelope,
    ScenarioOutput,
    SetbackSet,
    SolverInput,
)


class CharlestonSolverEngine(BaseSolverEngine):
    """Solver for City of Charleston jurisdiction."""

    # ── Step 1: Load district data ──

    def _load_district(self, solver_input: SolverInput) -> Optional[Dict[str, Any]]:
        return CHARLESTON_DISTRICTS.get(solver_input.zoning_district)

    # ── Step 2: Resolve split-row (commercial districts) ──

    def _resolve_row(
        self, district: Dict[str, Any], solver_input: SolverInput
    ) -> Dict[str, Any]:
        if district.get("has_split_row"):
            if solver_input.use_type == "residential":
                return district["residential"]
            return district["non_residential"]
        return district["data"]

    # ── Step 3: Detect NR-everything districts ──

    def _is_nr_district(self, district: Dict[str, Any]) -> bool:
        return district.get("nr_everything", False)

    # ── Step 4: Resolve effective height ──

    def _resolve_height(
        self,
        row: Dict[str, Any],
        solver_input: SolverInput,
        district: Dict[str, Any],
    ) -> Tuple[
        Optional[float],  # effective_height_ft
        Optional[float],  # effective_height_stories
        Optional[str],    # controlling_factor
        Optional[float],  # base_height_ft
        Optional[float],  # base_height_stories
    ]:
        base_ft = row.get("max_height_ft")
        base_stories = row.get("max_height_stories")

        # Footnote 8 universal cap: height <= 3 * distance_from_ROW_center
        half_row = solver_input.half_row_width_ft or DEFAULT_HALF_ROW_WIDTH_FT
        front_setback = self._get_front_setback(row)
        fn8_distance = half_row + front_setback
        fn8_cap_ft = 3.0 * fn8_distance
        fn8_cap_stories = fn8_cap_ft / FT_PER_STORY

        # Candidates for fn8 comparison use BASE values (no BAR bonus).
        # BAR bonus is added AFTER fn8 check if fn8 doesn't bind.
        # (height_ft, height_stories, factor_name)
        candidates: List[Tuple[float, float, str]] = []

        # a. Base zoning height
        if base_ft is not None and base_stories is not None:
            candidates.append((base_ft, base_stories, "base_zoning"))
        elif base_ft is not None:
            candidates.append((base_ft, base_ft / FT_PER_STORY, "base_zoning"))
        elif base_stories is not None:
            candidates.append(
                (base_stories * FT_PER_STORY, base_stories, "base_zoning")
            )

        # b. Height district overlay (BASE stories only — no BAR bonus yet)
        hd_base_stories: Optional[float] = None
        hd_bar_bonus: float = 0
        if solver_input.height_district:
            hd = CHARLESTON_HEIGHT_DISTRICTS.get(solver_input.height_district)
            if hd:
                hd_base_stories = hd["max_stories"]
                hd_bar_bonus = hd["bar_bonus_stories"]
                hd_base_ft = hd_base_stories * FT_PER_STORY
                candidates.append(
                    (hd_base_ft, hd_base_stories, "height_district_overlay")
                )

        # c. Footnote 8
        candidates.append((fn8_cap_ft, fn8_cap_stories, "footnote_8_row_cap"))

        if not candidates:
            return None, None, None, base_ft, base_stories

        # d. effective = minimum of all candidates (using base values)
        winner = min(candidates, key=lambda c: c[0])
        eff_ft, eff_stories, controlling = winner

        # If fn8 did NOT bind (i.e., height district or base zoning won),
        # add BAR bonus on top. BAR bonus is exempt from fn8.
        if controlling != "footnote_8_row_cap" and hd_bar_bonus > 0:
            eff_stories = eff_stories + hd_bar_bonus
            eff_ft = eff_stories * FT_PER_STORY

        return eff_ft, eff_stories, controlling, base_ft, base_stories

    def _get_front_setback(self, row: Dict[str, Any]) -> float:
        """Extract front setback from row, applying override rules.

        Returns 0 for NR (None) setbacks.
        """
        sb = row.get("setbacks", {})
        front = sb.get("front")
        rear = sb.get("rear")
        total = sb.get("front_rear_total")

        # Specific values override total
        if front is not None:
            return front
        # Front is NR/null — derive from total if possible
        if total is not None and rear is not None:
            derived = total - rear
            return max(derived, 0)
        return 0.0  # NR = no setback

    # ── Step 5: Calculate net buildable footprint ──

    def _resolve_setbacks(self, row: Dict[str, Any]) -> SetbackSet:
        """Resolve setback values applying the override rule."""
        sb = row.get("setbacks", {})
        raw_total = sb.get("front_rear_total")
        raw_front = sb.get("front")
        raw_rear = sb.get("rear")
        raw_side_total = sb.get("side_total")
        raw_side_sw = sb.get("side_sw")
        raw_side_ne = sb.get("side_ne")

        notes: List[str] = []

        # Apply SETBACK OVERRIDE RULE for front/rear
        front = raw_front
        rear = raw_rear

        if raw_front is not None and raw_rear is not None:
            # Both specified — use specific values, ignore total
            pass
        elif raw_front is not None and raw_rear is None:
            if raw_total is not None:
                rear = max(raw_total - raw_front, 0)
                notes.append(f"Rear setback derived: {raw_total} - {raw_front} = {rear}")
            else:
                notes.append("NR = Not Required — no rear setback minimum")
        elif raw_front is None and raw_rear is not None:
            if raw_total is not None:
                front = max(raw_total - raw_rear, 0)
                notes.append(
                    f"Front setback derived: {raw_total} - {raw_rear} = {front}"
                )
            else:
                notes.append("NR = Not Required — no front setback minimum")
        else:
            # Both NR
            if raw_front is None:
                notes.append("NR = Not Required — no front setback minimum")
            if raw_rear is None and raw_front is not None:
                pass  # already handled
            elif raw_rear is None and raw_front is None:
                notes.append("NR = Not Required — no rear setback minimum")

        if raw_side_total is None:
            notes.append("NR = Not Required — no minimum side setback")

        return SetbackSet(
            front_rear_total=raw_total,
            front=front,
            rear=rear,
            side_total=raw_side_total,
            side_sw=raw_side_sw,
            side_ne=raw_side_ne,
            notes=notes,
        )

    def _calculate_buildable_area(
        self,
        solver_input: SolverInput,
        setbacks: SetbackSet,
        lot_occupancy_pct: Optional[float],
    ) -> Tuple[Optional[float], Optional[float]]:
        """Returns (buildable_area_after_setbacks, max_footprint_from_occupancy)."""
        if solver_input.lot_size_sf is None:
            return None, None

        buildable_area: Optional[float] = None
        if (
            solver_input.lot_width_ft is not None
            and solver_input.lot_depth_ft is not None
        ):
            front_sb = setbacks.front or 0
            rear_sb = setbacks.rear or 0
            side_total_sb = setbacks.side_total or 0

            buildable_width = solver_input.lot_width_ft - side_total_sb
            buildable_depth = solver_input.lot_depth_ft - front_sb - rear_sb
            if buildable_width > 0 and buildable_depth > 0:
                buildable_area = buildable_width * buildable_depth
            else:
                buildable_area = 0
        else:
            # No dimensions — assume full lot minus occupancy constraint
            buildable_area = solver_input.lot_size_sf

        max_footprint: Optional[float] = None
        if lot_occupancy_pct is not None:
            max_footprint = solver_input.lot_size_sf * (lot_occupancy_pct / 100.0)
        else:
            # NR lot occupancy — full lot is buildable
            max_footprint = solver_input.lot_size_sf

        return buildable_area, max_footprint

    # ── Step 6 & 7: GFA and units ──

    def _calculate_gfa(
        self,
        footprint: Optional[float],
        effective_stories: Optional[float],
    ) -> Optional[float]:
        if footprint is None or effective_stories is None:
            return None
        return footprint * effective_stories

    def _calculate_max_units(
        self,
        row: Dict[str, Any],
        district: Dict[str, Any],
        solver_input: SolverInput,
        gfa: Optional[float],
        effective_stories: Optional[float],
    ) -> Tuple[Optional[int], Optional[str]]:
        """Returns (max_units, density_basis)."""
        density_type = row.get("density_type")
        density_value = row.get("density_value")

        units_from_density: Optional[int] = None
        density_basis: Optional[str] = None

        if density_type == "du_per_acre" and density_value is not None:
            if solver_input.lot_size_sf is not None:
                lot_acres = solver_input.lot_size_sf / SF_PER_ACRE
                units_from_density = math.floor(lot_acres * density_value)
                density_basis = "per_acre_cap"
            else:
                density_basis = "per_acre_cap"
        elif density_type == "min_lot_per_unit" and density_value is not None:
            if solver_input.lot_size_sf is not None:
                units_from_density = math.floor(
                    solver_input.lot_size_sf / density_value
                )
                density_basis = "min_lot_area_per_unit"
            else:
                density_basis = "min_lot_area_per_unit"
        else:
            # NR density — UP above 4 stories, MU districts
            if effective_stories is not None and effective_stories > 4:
                density_basis = "controlled_by_height_and_parking"
            elif district.get("nr_everything"):
                density_basis = "not_regulated"
            else:
                density_basis = "not_regulated"

            # Check UP base density for <=4 stories
            up_base = district.get("up_base_density")
            if (
                up_base
                and effective_stories is not None
                and effective_stories <= 4
                and solver_input.lot_size_sf is not None
            ):
                lot_acres = solver_input.lot_size_sf / SF_PER_ACRE
                units_from_density = math.floor(lot_acres * up_base)
                density_basis = "per_acre_cap"

        # Units from floor area
        units_from_gfa: Optional[int] = None
        if gfa is not None:
            units_from_gfa = math.floor(gfa * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF)

        # Take minimum
        if units_from_density is not None and units_from_gfa is not None:
            return min(units_from_density, units_from_gfa), density_basis
        if units_from_density is not None:
            return units_from_density, density_basis
        if units_from_gfa is not None:
            return units_from_gfa, density_basis or "controlled_by_height_and_parking"
        return None, density_basis

    # ── Step 8: Parking ──

    def _calculate_parking(
        self,
        solver_input: SolverInput,
        district: Dict[str, Any],
        max_units: Optional[int],
        gfa: Optional[float],
    ) -> Tuple[Optional[float], Optional[str]]:
        """Returns (parking_spaces_required, parking_type)."""
        if max_units is None and gfa is None:
            return None, None

        wh_pct = district.get("workforce_housing_pct")
        district_code = solver_input.zoning_district

        # Determine parking table
        if district_code in ("MU-1/WH", "MU-2/WH"):
            return self._calc_parking_mu_wh(max_units, gfa, wh_pct or 20), "mu_wh"
        if district_code == "UP":
            return self._calc_parking_up(
                max_units, solver_input, district
            ), "up"

        on_pen = solver_input.on_peninsula
        if on_pen is None:
            on_pen = True  # default to peninsula for City of Charleston
        table_key = "on_peninsula" if on_pen else "off_peninsula"
        table = CHARLESTON_PARKING[table_key]

        use = solver_input.use_type
        subtype = solver_input.use_subtype

        if use == "residential":
            if subtype in ("single_family", "duplex"):
                rate = table["single_family"]
            elif district_code in ("MU-1", "MU-2"):
                rate = table.get("multi_family_wh", table["multi_family"])
            else:
                rate = table["multi_family"]
            spaces = (max_units or 0) * rate
        elif use == "hospitality":
            rate = table["hotel"]
            spaces = (max_units or 0) * rate
        elif use == "commercial":
            if subtype == "office_class_a" or subtype == "office":
                spaces = (gfa or 0) * table["office_per_sf"]
            elif subtype == "retail":
                spaces = (gfa or 0) * table["retail_per_sf"]
            elif subtype == "restaurant":
                # Use 60% of GFA as patron area estimate
                spaces = (gfa or 0) * 0.6 * table["restaurant_per_sf"]
            else:
                spaces = (gfa or 0) * table["office_per_sf"]
        elif use == "mixed_use":
            # Estimate: 70% residential, 30% commercial
            res_units = int((max_units or 0) * 0.7) if max_units else 0
            comm_gfa = (gfa or 0) * 0.3
            if district_code in ("MU-1", "MU-2"):
                res_rate = table.get("multi_family_wh", table["multi_family"])
            else:
                res_rate = table["multi_family"]
            spaces = res_units * res_rate + comm_gfa * table["office_per_sf"]
        else:
            spaces = (max_units or 0) * table.get("multi_family", 1.5)

        return math.ceil(spaces), table_key

    def _calc_parking_mu_wh(
        self,
        max_units: Optional[int],
        gfa: Optional[float],
        wh_pct: float,
    ) -> float:
        table = CHARLESTON_PARKING["mu_wh"]
        units = max_units or 0
        wh_units = math.ceil(units * wh_pct / 100)
        market_units = units - wh_units
        res_spaces = wh_units * table["workforce_housing"] + market_units * table[
            "market_rate"
        ]
        # Non-residential: first 5,000 SF exempt
        comm_gfa = max((gfa or 0) * 0.3 - 5000, 0)
        comm_spaces = comm_gfa * table["office_per_sf"]
        return math.ceil(res_spaces + comm_spaces)

    def _calc_parking_up(
        self,
        max_units: Optional[int],
        solver_input: SolverInput,
        district: Dict[str, Any],
    ) -> Tuple[float, str]:
        table = CHARLESTON_PARKING["up"]
        units = max_units or 0
        wh_pct = district.get("workforce_housing_pct", 10)
        wh_units = math.ceil(units * wh_pct / 100)
        other_units = units - wh_units
        spaces = (
            wh_units * table["workforce_housing"]
            + other_units * table["all_other_residential"]
        )
        return math.ceil(spaces), "up"

    # ── Step 9: Parking as binding constraint ──

    def _parking_land_impact(
        self,
        parking_required: Optional[float],
        lot_size_sf: Optional[float],
    ) -> List[str]:
        warnings: List[str] = []
        if parking_required is None or lot_size_sf is None:
            return warnings
        surface_area = parking_required * SF_PER_PARKING_SPACE_SURFACE
        if surface_area > lot_size_sf * 0.5:
            warnings.append(
                f"Surface parking ({parking_required:.0f} spaces) would consume "
                f"{surface_area:,.0f} SF — over 50% of the lot. "
                "Structured parking likely required."
            )
        warnings.append(
            "Below-grade parking is extremely problematic in Charleston due to "
            "high water table. Budget $80,000-$120,000+/space. Avoid if possible."
        )
        return warnings

    # ── Main calculate_envelope (Steps 1-9) ──

    def calculate_envelope(
        self, district_data: Dict[str, Any], solver_input: SolverInput
    ) -> DevelopmentEnvelope:
        district = district_data
        row = self._resolve_row(district, solver_input)

        # Step 3: NR-everything check
        is_nr = self._is_nr_district(district)
        needs_hd = is_nr and solver_input.height_district is None

        # Step 4: Height
        eff_ft, eff_stories, controlling, base_ft, base_stories = self._resolve_height(
            row, solver_input, district
        )

        # Step 5: Setbacks and buildable area
        setbacks = self._resolve_setbacks(row)
        lot_occ = row.get("lot_occupancy_pct")
        buildable_area, max_footprint = self._calculate_buildable_area(
            solver_input, setbacks, lot_occ
        )

        # Actual footprint = min(buildable, occupancy cap)
        actual_footprint: Optional[float] = None
        if buildable_area is not None and max_footprint is not None:
            actual_footprint = min(buildable_area, max_footprint)
        elif max_footprint is not None:
            actual_footprint = max_footprint
        elif buildable_area is not None:
            actual_footprint = buildable_area

        # Step 6: GFA
        gfa = self._calculate_gfa(actual_footprint, eff_stories)

        # Step 7: Units
        max_units, density_basis = self._calculate_max_units(
            row, district, solver_input, gfa, eff_stories
        )

        # Density for display
        density_type = row.get("density_type")
        density_value = row.get("density_value")
        density_du_per_acre: Optional[float] = None
        if density_type == "du_per_acre" and density_value is not None:
            density_du_per_acre = density_value
        elif (
            density_type == "min_lot_per_unit"
            and density_value is not None
            and density_value > 0
        ):
            density_du_per_acre = SF_PER_ACRE / density_value

        # Step 8: Parking
        parking, parking_type = self._calculate_parking(
            solver_input, district, max_units, gfa
        )

        return DevelopmentEnvelope(
            zoning_district=solver_input.zoning_district,
            zoning_description=district.get("name", solver_input.zoning_district),
            max_height_ft=base_ft,
            max_height_stories=base_stories,
            effective_height_ft=eff_ft,
            effective_height_stories=eff_stories,
            height_controlling_factor=controlling,
            lot_occupancy_pct=lot_occ,
            far=None,  # Charleston never uses FAR
            density_units_per_acre=density_du_per_acre,
            density_basis=density_basis,
            setbacks=setbacks,
            max_building_footprint_sf=actual_footprint,
            max_gross_floor_area_sf=gfa,
            max_units=max_units,
            parking_required=parking,
            parking_type=parking_type,
            height_district_required=needs_hd,
        )

    # ── Step 10: Scenarios ──

    def calculate_scenarios(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[ScenarioOutput]:
        max_u = envelope.max_units
        max_gfa = envelope.max_gross_floor_area_sf
        eff_stories = envelope.effective_height_stories

        # By-Right: 80% of theoretical max
        br_units = math.floor(max_u * 0.8) if max_u is not None else None
        br_gfa = max_gfa * 0.8 if max_gfa is not None else None
        br_stories = eff_stories

        # Ensure at least 1 unit for by-right on small lots
        if br_units is not None and br_units < 1 and max_u is not None and max_u >= 1:
            br_units = 1

        by_right = ScenarioOutput(
            name="By-Right",
            risk_level="Low",
            unit_count_low=br_units,
            unit_count_high=br_units,
            gross_floor_area_sf=br_gfa,
            stories=br_stories,
            description=(
                "Conservative build within all current zoning parameters. "
                "No variances or special approvals needed."
            ),
            constraints_satisfied=self._satisfied_constraints(envelope),
            constraints_exceeded=[],
            variance_needed=[],
        )

        # Optimized: 100% of theoretical max
        opt_units = max_u
        opt_gfa = max_gfa
        opt_stories = eff_stories

        optimized = ScenarioOutput(
            name="Optimized",
            risk_level="Moderate",
            unit_count_low=opt_units,
            unit_count_high=opt_units,
            gross_floor_area_sf=opt_gfa,
            stories=opt_stories,
            description=(
                "Maximizes development within all dimensional constraints. "
                "May require structured parking and efficient floor plates."
            ),
            constraints_satisfied=self._satisfied_constraints(envelope),
            constraints_exceeded=[],
            variance_needed=[],
        )

        # With Variance: exceed binding constraint
        var_units, var_gfa, var_stories, variances = self._variance_scenario(
            envelope, solver_input
        )

        with_variance = ScenarioOutput(
            name="With Variance",
            risk_level="High",
            unit_count_low=var_units,
            unit_count_high=var_units,
            gross_floor_area_sf=var_gfa,
            stories=var_stories,
            description=(
                "Exceeds one or more dimensional constraints — requires "
                "BZA variance or special approval."
            ),
            constraints_satisfied=self._satisfied_constraints(envelope),
            constraints_exceeded=[v.split(":")[0] for v in variances] if variances else [],
            variance_needed=variances,
        )

        return [by_right, optimized, with_variance]

    def _satisfied_constraints(self, envelope: DevelopmentEnvelope) -> List[str]:
        constraints = []
        if envelope.effective_height_ft is not None:
            constraints.append(
                f"Height: {envelope.effective_height_ft:.0f} ft / "
                f"{envelope.effective_height_stories:.1f} stories"
            )
        if envelope.lot_occupancy_pct is not None:
            constraints.append(f"Lot occupancy: {envelope.lot_occupancy_pct}%")
        if envelope.max_building_footprint_sf is not None:
            constraints.append(
                f"Max footprint: {envelope.max_building_footprint_sf:,.0f} SF"
            )
        if envelope.parking_required is not None:
            constraints.append(
                f"Parking: {envelope.parking_required:.0f} spaces required"
            )
        return constraints

    def _variance_scenario(
        self,
        envelope: DevelopmentEnvelope,
        solver_input: SolverInput,
    ) -> Tuple[Optional[int], Optional[float], Optional[float], List[str]]:
        """Calculate the with-variance scenario by exceeding the binding constraint."""
        variances: List[str] = []

        eff_stories = envelope.effective_height_stories
        max_units = envelope.max_units
        max_gfa = envelope.max_gross_floor_area_sf
        footprint = envelope.max_building_footprint_sf

        # Determine what's binding and push it
        var_stories = eff_stories
        var_units = max_units
        var_gfa = max_gfa

        # Check if density is the binding constraint
        density_binding = False
        if max_units is not None and max_gfa is not None:
            units_from_gfa = math.floor(
                max_gfa * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF
            )
            if max_units < units_from_gfa:
                density_binding = True

        if density_binding and var_units is not None:
            # Request 20% density increase
            bump = max(math.ceil(var_units * 0.2), 1)
            var_units = var_units + bump
            if var_gfa is not None:
                var_gfa = var_units * AVG_UNIT_SIZE_SF / EFFICIENCY_RATIO
            variances.append(
                f"Density: requesting {bump} additional units "
                f"(+20% via BZA variance or PUD)"
            )
        elif eff_stories is not None and var_stories is not None:
            # Add 1-2 stories via variance
            bonus = 2 if eff_stories >= 4 else 1
            var_stories = eff_stories + bonus
            if footprint is not None:
                var_gfa = footprint * var_stories
                var_units_from_gfa = math.floor(
                    var_gfa * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF
                )
                # Use the lesser of density-bumped and gfa-based
                if var_units is not None:
                    var_units = max(var_units, var_units_from_gfa)
                else:
                    var_units = var_units_from_gfa
            variances.append(
                f"Height: adding {bonus} stories via BZA variance "
                f"({eff_stories:.1f} → {var_stories:.1f} stories)"
            )

        # UP district: note points system
        if solver_input.zoning_district == "UP":
            variances.append(
                "UP district bonus height requires community benefit points"
            )

        return var_units, var_gfa, var_stories, variances

    # ── Step 11: Binding constraints ──

    def identify_binding_constraints(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[BindingConstraint]:
        constraints: List[BindingConstraint] = []

        # Height
        if envelope.effective_height_ft is not None:
            is_binding_height = True
            constraints.append(
                BindingConstraint(
                    constraint_name="Height",
                    constraint_value=(
                        f"{envelope.effective_height_ft:.0f} ft / "
                        f"{envelope.effective_height_stories:.1f} stories"
                    ),
                    is_binding=is_binding_height,
                    explanation=(
                        f"Controlled by {envelope.height_controlling_factor or 'base zoning'}"
                    ),
                )
            )

        # Lot occupancy
        if envelope.lot_occupancy_pct is not None:
            constraints.append(
                BindingConstraint(
                    constraint_name="Lot Occupancy",
                    constraint_value=f"{envelope.lot_occupancy_pct}%",
                    is_binding=True,
                    explanation="Max percentage of lot that can be covered by buildings",
                )
            )

        # Density
        if envelope.max_units is not None and envelope.max_gross_floor_area_sf is not None:
            units_from_gfa = math.floor(
                envelope.max_gross_floor_area_sf * EFFICIENCY_RATIO / AVG_UNIT_SIZE_SF
            )
            density_is_binding = envelope.max_units < units_from_gfa
            constraints.append(
                BindingConstraint(
                    constraint_name="Density",
                    constraint_value=(
                        f"{envelope.max_units} units"
                        + (
                            f" (vs {units_from_gfa} from floor area)"
                            if density_is_binding
                            else ""
                        )
                    ),
                    is_binding=density_is_binding,
                    explanation=(
                        f"Basis: {envelope.density_basis or 'unknown'}"
                    ),
                )
            )

        # Parking
        if envelope.parking_required is not None and solver_input.lot_size_sf is not None:
            surface_area = envelope.parking_required * SF_PER_PARKING_SPACE_SURFACE
            parking_binding = surface_area > solver_input.lot_size_sf * 0.3
            warnings = self._parking_land_impact(
                envelope.parking_required, solver_input.lot_size_sf
            )
            constraints.append(
                BindingConstraint(
                    constraint_name="Parking",
                    constraint_value=f"{envelope.parking_required:.0f} spaces",
                    is_binding=parking_binding,
                    explanation="; ".join(warnings) if warnings else "Within lot capacity",
                )
            )

        return constraints
