from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["product"] == "parceliq"


def test_analyze_tier1_requires_zoning_district():
    """Tier 1 (Charleston) without zoning_district should return 422."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King St",
    })
    assert response.status_code == 422
    data = response.json()
    assert "Zoning district is required" in data["detail"]


def test_analyze_tier1_with_zoning_district():
    """Tier 1 (Charleston) with zoning_district should be accepted."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King St",
        "zoning_district": "MU-2",
    })
    # Will be 200 if ANTHROPIC_API_KEY is set, 502 if not — either is valid wiring
    assert response.status_code in (200, 502)


def test_analyze_mount_pleasant_requires_zoning():
    """Tier 1 (Mt Pleasant) without zoning_district should return 422."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "mount_pleasant",
        "address": "456 Coleman Blvd",
        "lot_size_sf": 12000.0,
    })
    assert response.status_code == 422


def test_analyze_tier2_no_zoning_required():
    """Tier 2 (North Charleston) should NOT require zoning_district."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "north_charleston",
        "address": "789 Rivers Ave",
    })
    # 200 or 502 (no API key) — but NOT 422
    assert response.status_code != 422


def test_analyze_tier3_no_zoning_required():
    """Tier 3 jurisdictions should NOT require zoning_district."""
    response = client.post("/api/analyze", json={
        "jurisdiction": "folly_beach",
        "address": "100 Center St",
    })
    assert response.status_code != 422


def test_analyze_invalid_jurisdiction():
    response = client.post("/api/analyze", json={
        "jurisdiction": "imaginary_town",
        "address": "123 Fake St",
    })
    assert response.status_code == 422
