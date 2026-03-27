"""End-to-end flow tests for ParcelIQ.

These tests verify the full pipeline: form → solver → Claude → response.
Tests that call Claude require ANTHROPIC_API_KEY in environment.
Tests marked with `needs_api_key` are skipped when the key is absent.
"""

import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

needs_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live Claude tests",
)


# ---------------------------------------------------------------------------
# Test 1: Full Tier 1 flow — Charleston MU-2 with all fields
# ---------------------------------------------------------------------------

@needs_api_key
def test_charleston_mu2_full_analysis():
    """Submit 123 King Street, Charleston, MU-2, 10,000 SF, Residential.

    Should return a complete analysis. MU-2 allows ~30-40 units/acre density.
    """
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King Street",
        "zoning_district": "MU-2",
        "height_district": "4",
        "on_peninsula": True,
        "lot_size_sf": 10000,
        "use_types": ["residential"],
        "approximate_scale": "30-40 units",
    })
    assert response.status_code == 200
    data = response.json()

    # Parcel info
    assert data["parcel"]["address"] == "123 King Street"
    assert data["parcel"]["jurisdiction"] == "charleston"
    assert data["parcel"]["jurisdiction_display"] == "City of Charleston"
    assert data["parcel"]["zoning_district"] == "MU-2"
    assert data["parcel"]["lot_size_sf"] == 10000

    # Envelope — solver should produce real numbers
    env = data["envelope"]
    assert env["zoning_district"] == "MU-2"
    assert env["max_height_ft"] is not None  # 48 ft from height district 4
    assert env["buildable_area_sf"] is not None  # solver calculates footprint

    # 3 scenarios
    assert len(data["scenarios"]) == 3
    names = {s["name"] for s in data["scenarios"]}
    assert "By-Right" in names

    # Risk map populated by Claude
    assert data["risk_map"] is not None

    # Process timeline
    assert len(data["process_timeline"]["required_boards"]) > 0

    # Cost framing
    assert data["cost_framing"] is not None

    # Confidence
    assert data["confidence_tier"] == 1
    assert data["disclaimer"] is None

    # Metadata
    assert data["metadata"]["solver_version"] != ""
    assert data["metadata"]["ai_model"] != ""


# ---------------------------------------------------------------------------
# Test 2: Minimal input — just address + jurisdiction + zoning
# ---------------------------------------------------------------------------

@needs_api_key
def test_charleston_minimal_input():
    """Submit just address + jurisdiction + zoning (no optional fields).

    Should still return a general analysis.
    """
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "456 Meeting Street",
        "zoning_district": "GB",
    })
    assert response.status_code == 200
    data = response.json()

    assert data["parcel"]["address"] == "456 Meeting Street"
    assert len(data["scenarios"]) == 3
    assert data["confidence_tier"] == 1


# ---------------------------------------------------------------------------
# Test 3: Invalid jurisdiction — validation error
# ---------------------------------------------------------------------------

def test_invalid_jurisdiction_returns_422():
    """Invalid jurisdiction should return a Pydantic validation error."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "atlantis",
        "address": "1 Ocean Drive",
    })
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Test 4: Missing zoning for Tier 1 — structured error
# ---------------------------------------------------------------------------

def test_tier1_missing_zoning_returns_422():
    """Tier 1 without zoning_district returns 422 with helpful message."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King St",
    })
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Zoning district is required" in detail
    assert "gis.charleston-sc.gov" in detail


def test_tier1_mt_pleasant_missing_zoning():
    """Mt Pleasant (Tier 1) also requires zoning."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "mount_pleasant",
        "address": "100 Coleman Blvd",
    })
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Zoning district is required" in detail


# ---------------------------------------------------------------------------
# Test 5: Tier 2/3 work without zoning
# ---------------------------------------------------------------------------

@needs_api_key
def test_tier2_north_charleston_no_zoning():
    """Tier 2 should work without zoning_district (AI handles it)."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "north_charleston",
        "address": "4600 Rivers Ave",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_tier"] == 2
    assert data["disclaimer"] is not None


@needs_api_key
def test_tier3_folly_beach():
    """Tier 3 should work with AI-only + disclaimers."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "folly_beach",
        "address": "100 Center Street",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_tier"] == 3
    assert data["disclaimer"] is not None


# ---------------------------------------------------------------------------
# Test 6: Claude API failure handling (without API key)
# ---------------------------------------------------------------------------

def test_claude_failure_returns_graceful_fallback():
    """If ANTHROPIC_API_KEY is unset/invalid, should return 200 with fallback data."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("API key is set — can't test failure path")

    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King St",
        "zoning_district": "MU-2",
    })
    # The AI service gracefully degrades — returns 200 with placeholder data
    assert response.status_code == 200
    data = response.json()
    # Solver-generated envelope should still be present
    assert data["envelope"]["zoning_district"] == "MU-2"
    # Scenarios should exist (3 of them)
    assert len(data["scenarios"]) == 3


# ---------------------------------------------------------------------------
# Test 7: Response schema completeness
# ---------------------------------------------------------------------------

@needs_api_key
def test_response_schema_complete():
    """Verify all required response fields are present and typed correctly."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "99 Broad Street",
        "zoning_district": "SR-2",
        "lot_size_sf": 5000,
    })
    assert response.status_code == 200
    data = response.json()

    # Top-level keys
    required_keys = {
        "parcel", "envelope", "scenarios", "risk_map",
        "process_timeline", "cost_framing", "metadata",
        "confidence_tier", "confidence_label",
    }
    assert required_keys.issubset(data.keys())

    # Envelope has setbacks
    assert "setbacks" in data["envelope"]

    # Scenarios are exactly 3
    assert len(data["scenarios"]) == 3
    for s in data["scenarios"]:
        assert "name" in s
        assert "description" in s
        assert "risk_level" in s
        assert s["risk_level"] in ("Low", "Moderate", "High")

    # Metadata
    assert "generated_at" in data["metadata"]
    assert "solver_version" in data["metadata"]
    assert "ai_model" in data["metadata"]
