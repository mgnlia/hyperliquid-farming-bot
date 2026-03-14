from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_shape() -> None:
    response = client.get("/api/status")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "simulation_mode" in payload
    assert "portfolio_value" in payload
