"""Tests for jurisdiction data modules and registry."""

import pytest

from app.jurisdictions.ai_only import AIOnlyJurisdiction
from app.jurisdictions.charleston import CharlestonModule
from app.jurisdictions.mount_pleasant import MtPleasantModule
from app.jurisdictions.north_charleston import NorthCharlestonModule
from app.jurisdictions.unincorporated_county import UnincorporatedCountyModule
from app.jurisdictions.registry import get_jurisdiction, list_jurisdictions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chs():
    return CharlestonModule()


@pytest.fixture(scope="module")
def mtp():
    return MtPleasantModule()


@pytest.fixture(scope="module")
def nch():
    return NorthCharlestonModule()


@pytest.fixture(scope="module")
def county():
    return UnincorporatedCountyModule()


# ---------------------------------------------------------------------------
# 1. Charleston loads all districts without error
# ---------------------------------------------------------------------------

def test_charleston_loads_all_districts(chs):
    districts = chs.list_districts()
    assert len(districts) >= 40  # Table 3.1 has 42+ entries
    for code in districts:
        # Should not raise
        chs.get_district(code)


# ---------------------------------------------------------------------------
# 2. SR-2 lot occupancy is 50 (NOT 35)
# ---------------------------------------------------------------------------

def test_sr2_lot_occupancy(chs):
    d = chs.get_district("SR-2")
    assert d is not None
    assert d["lot_occupancy_pct"] == 50


# ---------------------------------------------------------------------------
# 3. MU-2 returns all-NR with special_rules flag
# ---------------------------------------------------------------------------

def test_mu2_all_nr(chs):
    d = chs.get_district("MU-2")
    assert d is not None
    assert "all_fields" in d["unrestricted_fields"]
    assert d.get("special_rules") is not None
    assert d.get("_constraints_from_overlay") is True


# ---------------------------------------------------------------------------
# 4. GB residential split row returns setbacks
# ---------------------------------------------------------------------------

def test_gb_residential(chs):
    d = chs.get_district("GB", use_type="residential")
    assert d is not None
    assert d["name"] == "General Business (Residential Use)"
    assert d["setbacks"]["side_sw"] == 9
    assert d["lot_occupancy_pct"] == 50


# ---------------------------------------------------------------------------
# 5. GB commercial split row returns NR everything
# ---------------------------------------------------------------------------

def test_gb_commercial(chs):
    d = chs.get_district("GB", use_type="commercial")
    assert d is not None
    assert d["name"] == "General Business (Non-Residential)"
    assert d["setbacks"]["front"] is None
    assert "all_setbacks" in d["unrestricted_fields"]


# ---------------------------------------------------------------------------
# 6. Height district 6: max_stories=6, bar_bonus=1.0
# ---------------------------------------------------------------------------

def test_height_district_6(chs):
    hd = chs.get_height_district("6")
    assert hd is not None
    assert hd["max_stories"] == 6
    assert hd["bar_bonus"] == 1.0


# ---------------------------------------------------------------------------
# 7. Height district 4-12: incentive_max_stories=12
# ---------------------------------------------------------------------------

def test_height_district_4_12(chs):
    hd = chs.get_height_district("4-12")
    assert hd is not None
    assert hd["incentive_max_stories"] == 12
    assert hd["max_stories"] == 4  # base


# ---------------------------------------------------------------------------
# 8. On-peninsula parking: office at 1/500 SF
# ---------------------------------------------------------------------------

def test_on_peninsula_parking(chs):
    p = chs.get_parking_table(on_peninsula=True)
    assert p["office"]["spaces_per_sf"] == 500


# ---------------------------------------------------------------------------
# 9. Off-peninsula parking: office at 1/240 SF
# ---------------------------------------------------------------------------

def test_off_peninsula_parking(chs):
    p = chs.get_parking_table(on_peninsula=False)
    assert p["office"]["spaces_per_sf"] == 240


# ---------------------------------------------------------------------------
# 10. Mt Pleasant UC-OD FAR = 1.5
# ---------------------------------------------------------------------------

def test_mt_pleasant_far(mtp):
    d = mtp.get_district("UC-OD")
    assert d is not None
    assert d["far"] == 1.5


# ---------------------------------------------------------------------------
# 11. North Charleston solver_enabled = False
# ---------------------------------------------------------------------------

def test_north_charleston_ai_only(nch):
    assert nch.solver_enabled is False


# ---------------------------------------------------------------------------
# 12. Registry returns correct module for each slug (all 12)
# ---------------------------------------------------------------------------

def test_registry_all_slugs():
    slugs = list_jurisdictions()
    assert len(slugs) == 12
    assert "charleston" in slugs
    assert "mount_pleasant" in slugs
    assert "north_charleston" in slugs
    assert "unincorporated_county" in slugs
    assert "sullivans_island" in slugs
    assert "isle_of_palms" in slugs
    assert "folly_beach" in slugs
    assert "james_island" in slugs
    assert "kiawah" in slugs
    assert "summerville" in slugs
    assert "goose_creek" in slugs
    assert "hanahan" in slugs

    chs = get_jurisdiction("charleston")
    assert chs.name == "City of Charleston"

    mtp = get_jurisdiction("mount_pleasant")
    assert mtp.name == "Town of Mount Pleasant"


# ---------------------------------------------------------------------------
# 13. Sullivan's Island is Tier 3 AIOnlyJurisdiction
# ---------------------------------------------------------------------------

def test_registry_sullivans_island_tier3():
    si = get_jurisdiction("sullivans_island")
    assert isinstance(si, AIOnlyJurisdiction)
    assert si.tier == 3
    assert si.confidence_label == "Preliminary — Verify with Local Planning"
    assert si.solver_enabled is False
    assert si.planning_phone == "843-883-3198"


# ---------------------------------------------------------------------------
# 14. Unknown slug raises ValueError
# ---------------------------------------------------------------------------

def test_registry_unknown_slug_raises():
    with pytest.raises(ValueError, match="Unknown jurisdiction"):
        get_jurisdiction("beaufort_county")


# ---------------------------------------------------------------------------
# 15. Tier assignments are correct
# ---------------------------------------------------------------------------

def test_tier_assignments():
    assert get_jurisdiction("charleston").tier == 1
    assert get_jurisdiction("mount_pleasant").tier == 1
    assert get_jurisdiction("north_charleston").tier == 2
    assert get_jurisdiction("unincorporated_county").tier == 2
    assert get_jurisdiction("folly_beach").tier == 3
    assert get_jurisdiction("goose_creek").tier == 3


# ---------------------------------------------------------------------------
# 16. has_solver property
# ---------------------------------------------------------------------------

def test_has_solver_property():
    assert get_jurisdiction("charleston").has_solver is True
    assert get_jurisdiction("mount_pleasant").has_solver is True
    assert get_jurisdiction("north_charleston").has_solver is False
    assert get_jurisdiction("sullivans_island").has_solver is False


# ---------------------------------------------------------------------------
# 17. AIOnlyJurisdiction get_ai_context includes disclaimer
# ---------------------------------------------------------------------------

def test_ai_only_context_includes_disclaimer():
    si = get_jurisdiction("sullivans_island")
    ctx = si.get_ai_context()
    assert "NOT INDEPENDENTLY RESEARCHED" in ctx
    assert "Sullivan's Island" in ctx
    assert "843-883-3198" in ctx
    assert "halfdays.ai" in ctx
