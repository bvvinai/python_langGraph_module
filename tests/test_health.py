from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
