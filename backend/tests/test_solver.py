"""Solver engine tests.

Each test verifies a specific calculation from the prompt specification.
"""

from __future__ import annotations

import math

import pytest

from app.solver.engine import solve
from app.solver.models import SolverInput


# ────────────────────────────────────────────────────────
# Test 1: Charleston DR-9 on 10,000 SF lot
# ────────────────────────────────────────────────────────
def test_charleston_dr9_10k_lot():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="DR-9",
        lot_size_sf=10_000,
        use_type="residential",
    )
    out = solve(inp)

    assert out.solver_mode == "full"
    env = out.envelope

    # lot_occupancy 50% -> max footprint = 5,000 SF
    assert env.lot_occupancy_pct == 50
    assert env.max_building_footprint_sf == 5_000

    # 3 stories -> max GFA = 15,000 SF
    assert env.effective_height_stories == 3
    assert env.max_gross_floor_area_sf == 15_000

    # density 9 du/ac -> floor(10000/43560 * 9) = floor(2.066) = 2
    expected_density_units = math.floor(10_000 / 43_560 * 9)
    assert expected_density_units == 2
    assert env.max_units == 2

    # Verify density is the binding constraint
    binding_names = {bc.constraint_name for bc in out.binding_constraints if bc.is_binding}
    assert "Density" in binding_names


# ────────────────────────────────────────────────────────
# Test 2: Charleston DR-12 on 1 acre (43,560 SF)
# ────────────────────────────────────────────────────────
def test_charleston_dr12_one_acre():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="DR-12",
        lot_size_sf=43_560,
        use_type="residential",
    )
    out = solve(inp)

    assert out.solver_mode == "full"
    env = out.envelope

    # lot_occupancy 50% -> 21,780 SF footprint
    assert env.max_building_footprint_sf == 21_780

    # 3 stories -> GFA = 65,340 SF
    assert env.max_gross_floor_area_sf == 65_340

    # density 12 du/ac -> floor(1.0 * 12) = 12
    assert env.max_units == 12

    # floor area would yield floor(65340 * 0.85 / 750) = 74
    units_from_gfa = math.floor(65_340 * 0.85 / 750)
    assert units_from_gfa == 74

    # Binding is density
    binding_names = {bc.constraint_name for bc in out.binding_constraints if bc.is_binding}
    assert "Density" in binding_names


# ────────────────────────────────────────────────────────
# Test 3: Charleston MU-2 (NR everything) + height district "6"
# ────────────────────────────────────────────────────────
def test_charleston_mu2_hd6_10k_lot():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="MU-2",
        lot_size_sf=10_000,
        use_type="residential",
        height_district="6",
        on_peninsula=True,
    )
    out = solve(inp)

    assert out.solver_mode == "full"
    env = out.envelope

    # Footnote 8 is evaluated against BASE height district (6 stories = 72 ft),
    # NOT the BAR bonus total (7 stories = 84 ft). BAR bonus is exempt from fn8.
    # Default half-ROW 25 ft + 0 front setback (NR) = 25 ft → fn8 cap = 75 ft.
    # 72 < 75 → fn8 NOT binding → effective = 6 + 1 BAR = 7 stories.

    # No lot occupancy cap (NR)
    assert env.lot_occupancy_pct is None

    # Full lot as footprint (NR setbacks, NR lot occupancy)
    assert env.max_building_footprint_sf == 10_000

    # 7 stories effective (6 base + 1 BAR)
    assert env.effective_height_stories == 7

    # GFA = 70,000
    assert env.max_gross_floor_area_sf == 70_000

    # Max units = floor(70000 * 0.85 / 750) = 79
    assert env.max_units == 79

    # Parking: on-peninsula MU district = 1/unit (MU multi_family_wh rate)
    # Actually MU-2 (not MU-2/WH), so rate = 1.5/unit on peninsula for multi_family
    # Wait, the spec says "Parking at 1/unit (on-peninsula) = 79 spaces"
    # The spec says MU-1 and MU-2 use the MU/WH rate of 1/unit for multi-family.
    # Looking at the parking table: "Multi-family (3+): 1.5/unit (1/unit in MU/WH districts)"
    # MU-2 is an MU district, so rate = 1/unit.
    assert env.parking_required == 79


# ────────────────────────────────────────────────────────
# Test 4: Charleston SR-2 correct values
# ────────────────────────────────────────────────────────
def test_charleston_sr2_values():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="SR-2",
        lot_size_sf=6_000,
        use_type="residential",
    )
    out = solve(inp)
    env = out.envelope

    # lot_occupancy = 50% (NOT 35%)
    assert env.lot_occupancy_pct == 50

    # height = 35'/2.5 stories
    assert env.max_height_ft == 35
    assert env.max_height_stories == 2.5

    # min lot 6,000 SF/unit — with a 6,000 SF lot = 1 unit
    assert env.max_units == 1


# ────────────────────────────────────────────────────────
# Test 5: Charleston GB non-residential — all NR
# ────────────────────────────────────────────────────────
def test_charleston_gb_non_residential():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="GB",
        lot_size_sf=10_000,
        use_type="commercial",
    )
    out = solve(inp)
    env = out.envelope

    # All setbacks NR
    assert env.setbacks.front is None
    assert env.setbacks.rear is None
    assert env.setbacks.side_total is None

    # Lot occupancy NR
    assert env.lot_occupancy_pct is None

    # Height = 55'
    assert env.max_height_ft == 55

    # Full lot buildable (NR setbacks + NR lot occupancy)
    assert env.max_building_footprint_sf == 10_000


# ────────────────────────────────────────────────────────
# Test 6: Charleston GB residential — split row
# ────────────────────────────────────────────────────────
def test_charleston_gb_residential():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="GB",
        lot_size_sf=10_000,
        use_type="residential",
    )
    out = solve(inp)
    env = out.envelope

    # lot_occupancy 50%
    assert env.lot_occupancy_pct == 50

    # height 55'
    assert env.max_height_ft == 55

    # Setbacks: front_rear_total=3, front=None(NR), rear=3
    # → front derived = max(3 - 3, 0) = 0
    assert env.setbacks.front_rear_total == 3
    assert env.setbacks.front == 0  # derived from total - rear
    assert env.setbacks.rear == 3

    # side_total=15, side_sw=9, side_ne=3
    assert env.setbacks.side_total == 15
    assert env.setbacks.side_sw == 9
    assert env.setbacks.side_ne == 3


# ────────────────────────────────────────────────────────
# Test 7: Mt Pleasant UC-OD on 20,000 SF
# ────────────────────────────────────────────────────────
def test_mt_pleasant_uc_od_20k():
    # Single-use residential
    inp = SolverInput(
        jurisdiction="mount_pleasant",
        zoning_district="UC-OD",
        lot_size_sf=20_000,
        use_type="residential",
    )
    out = solve(inp)

    assert out.solver_mode == "full"
    env = out.envelope

    # FAR 1.5 -> max GFA = 30,000 SF
    assert env.far == 1.5
    assert env.max_gross_floor_area_sf == 30_000

    # Density 16 du/ac -> floor(20000/43560 * 16) = floor(7.346) = 7
    assert env.max_units == 7

    # From floor area: floor(30000 * 0.85 / 750) = 34
    units_from_gfa = math.floor(30_000 * 0.85 / 750)
    assert units_from_gfa == 34

    # Binding is density
    binding = {bc.constraint_name: bc.is_binding for bc in out.binding_constraints}
    assert binding.get("Density") is True


def test_mt_pleasant_uc_od_mixed_use():
    inp = SolverInput(
        jurisdiction="mount_pleasant",
        zoning_district="UC-OD",
        lot_size_sf=20_000,
        use_type="mixed_use",
    )
    out = solve(inp)
    env = out.envelope

    # Mixed-use density: 20 du/ac -> floor(20000/43560 * 20) = floor(9.183) = 9
    assert env.max_units == 9
    assert env.density_units_per_acre == 20


# ────────────────────────────────────────────────────────
# Test 8: North Charleston → ai_only
# ────────────────────────────────────────────────────────
def test_north_charleston_ai_only():
    inp = SolverInput(
        jurisdiction="north_charleston",
        zoning_district="NBRD",
        use_type="mixed_use",
    )
    out = solve(inp)

    assert out.solver_mode == "ai_only"
    assert out.scenarios == []
    assert out.binding_constraints == []


# ────────────────────────────────────────────────────────
# Test 9: By-Right < Optimized < With-Variance in units
# ────────────────────────────────────────────────────────
def test_scenario_ordering_charleston():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="DR-12",
        lot_size_sf=43_560,
        use_type="residential",
    )
    out = solve(inp)
    assert len(out.scenarios) == 3

    br, opt, var = out.scenarios
    assert br.name == "By-Right"
    assert opt.name == "Optimized"
    assert var.name == "With Variance"

    # Unit counts should be ascending
    br_u = br.unit_count_high or 0
    opt_u = opt.unit_count_high or 0
    var_u = var.unit_count_high or 0
    assert br_u <= opt_u <= var_u
    assert br_u < var_u  # strict inequality between first and last


def test_scenario_ordering_mt_pleasant():
    inp = SolverInput(
        jurisdiction="mount_pleasant",
        zoning_district="UC-OD",
        lot_size_sf=20_000,
        use_type="residential",
    )
    out = solve(inp)
    assert len(out.scenarios) == 3

    br, opt, var = out.scenarios
    br_u = br.unit_count_high or 0
    opt_u = opt.unit_count_high or 0
    var_u = var.unit_count_high or 0
    assert br_u <= opt_u <= var_u
    assert br_u < var_u


# ────────────────────────────────────────────────────────
# Test 10: Footnote 8 test cases
# ────────────────────────────────────────────────────────
def test_footnote8_dr9_not_binding():
    """10a: DR-9, front setback 10, half-ROW 25 → cap 105. Base 50'. NOT binding."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="DR-9",
        lot_size_sf=10_000,
        use_type="residential",
        half_row_width_ft=25,
    )
    out = solve(inp)
    env = out.envelope

    # fn8: distance = 25 + 10 = 35; cap = 105 ft
    # Base zoning = 50 ft / 3 stories. 50 < 105 → fn8 NOT binding
    assert env.height_controlling_factor == "base_zoning"
    assert env.effective_height_ft == 50
    assert env.effective_height_stories == 3


def test_footnote8_mu2_hd6_25ft_not_binding():
    """10b: MU-2 NR setback, half-ROW 25, HD 6 (72 ft). cap=75. NOT binding."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="MU-2",
        lot_size_sf=10_000,
        use_type="residential",
        height_district="6",
        half_row_width_ft=25,
    )
    out = solve(inp)
    env = out.envelope

    # fn8: distance = 25 + 0 = 25; cap = 75 ft
    # HD 6 base = 6 stories = 72 ft. 72 < 75 → fn8 NOT binding
    # Effective = HD 6 + 1 BAR bonus = 7 stories
    assert env.height_controlling_factor == "height_district_overlay"
    assert env.effective_height_stories == 7


def test_footnote8_mu2_hd6_narrow_row_binding():
    """10c: MU-2 NR setback, half-ROW 15, HD 6 (72 ft). cap=45. IS binding."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="MU-2",
        lot_size_sf=10_000,
        use_type="residential",
        height_district="6",
        half_row_width_ft=15,
    )
    out = solve(inp)
    env = out.envelope

    # fn8: distance = 15 + 0 = 15; cap = 45 ft
    # HD 6 base = 6 stories = 72 ft. 45 < 72 → fn8 IS binding
    assert env.height_controlling_factor == "footnote_8_row_cap"
    assert env.effective_height_ft == 45
    assert env.effective_height_stories == pytest.approx(45 / 12, rel=1e-2)


def test_footnote8_sr1_not_binding():
    """10d: SR-1, front setback 25, half-ROW 15 → cap 120. Base 35'. NOT binding."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="SR-1",
        lot_size_sf=9_000,
        use_type="residential",
        half_row_width_ft=15,
    )
    out = solve(inp)
    env = out.envelope

    # fn8: distance = 15 + 25 = 40; cap = 120 ft
    # Base = 35 ft / 2.5 stories. 35 < 120 → fn8 NOT binding
    assert env.height_controlling_factor == "base_zoning"
    assert env.effective_height_ft == 35
    assert env.effective_height_stories == 2.5


# ────────────────────────────────────────────────────────
# Additional edge cases
# ────────────────────────────────────────────────────────
def test_unknown_jurisdiction():
    inp = SolverInput(
        jurisdiction="unknown_place",
        zoning_district="R-1",
        use_type="residential",
    )
    out = solve(inp)
    assert out.solver_mode == "ai_only"


def test_unknown_district_charleston():
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="FAKE-99",
        use_type="residential",
    )
    out = solve(inp)
    assert out.solver_mode == "ai_only"


def test_charleston_no_lot_size():
    """Solver should still return envelope without lot-based calculations."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="DR-9",
        use_type="residential",
    )
    out = solve(inp)

    assert out.solver_mode == "full"
    env = out.envelope
    assert env.lot_occupancy_pct == 50
    assert env.max_height_ft == 50
    assert env.max_building_footprint_sf is None
    assert env.max_gross_floor_area_sf is None
    assert env.max_units is None


def test_charleston_mu2_no_height_district():
    """NR-everything district without height district should flag it."""
    inp = SolverInput(
        jurisdiction="charleston",
        zoning_district="MU-2",
        lot_size_sf=10_000,
        use_type="residential",
    )
    out = solve(inp)
    env = out.envelope

    assert env.height_district_required is True
