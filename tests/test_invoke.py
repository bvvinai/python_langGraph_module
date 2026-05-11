from fastapi.testclient import TestClient

from app.main import create_app


def test_invoke_with_unknown_provider_returns_400() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/v1/ai/invoke",
        json={
            "input": "hello",
            "provider": "unknown-provider",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "provider_not_found"


def test_invoke_with_invalid_rag_mode_returns_400() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/v1/ai/invoke",
        json={
            "input": "hello",
            "rag_mode": "invalid",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid_rag_mode"
