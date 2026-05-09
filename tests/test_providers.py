from fastapi.testclient import TestClient

from app.main import create_app


def test_list_providers() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.get("/v1/ai/providers")
    assert response.status_code == 200
    body = response.json()
    assert "default_provider" in body
    providers = {item["name"] for item in body["providers"]}
    assert "anthropic" in providers
    assert "openai" in providers
    assert "ollama" in providers