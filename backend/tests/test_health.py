from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["product"] == "parceliq"


def test_analyze_mock():
    response = client.post("/api/analyze", json={"parcel_id": "TMS-123-45-67-890"})
    assert response.status_code == 200
    data = response.json()
    assert data["parcel_id"] == "TMS-123-45-67-890"
    assert data["feasibility"] == "favorable"
