from fastapi.testclient import TestClient

from app.main import create_app


def test_invoke_with_mock_provider() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/v1/ai/invoke",
        json={
            "input": "hello",
            "provider": "mock",
            "temperature": 0.1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert "Mock response" in body["output"]
    assert "trace_id" in body
