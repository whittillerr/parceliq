from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["product"] == "parceliq"


def test_analyze_endpoint_returns_response():
    response = client.post("/api/analyze", json={
        "jurisdiction": "charleston",
        "address": "123 King St",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["parcel"]["address"] == "123 King St"
    assert data["parcel"]["jurisdiction"] == "charleston"
    assert data["parcel"]["jurisdiction_display"] == "City of Charleston"
    assert len(data["scenarios"]) == 3
    assert data["confidence_tier"] == 1
    assert data["confidence_label"] == "Verified Data"


def test_analyze_with_optional_fields():
    response = client.post("/api/analyze", json={
        "jurisdiction": "mount_pleasant",
        "address": "456 Coleman Blvd",
        "lot_size_sf": 12000.0,
        "use_types": ["residential", "mixed_use"],
        "approximate_scale": "4 units",
        "existing_conditions": "vacant lot",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["parcel"]["lot_size_sf"] == 12000.0
    assert data["parcel"]["jurisdiction_display"] == "Town of Mount Pleasant"


def test_analyze_invalid_jurisdiction():
    response = client.post("/api/analyze", json={
        "jurisdiction": "imaginary_town",
        "address": "123 Fake St",
    })
    assert response.status_code == 422
