from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_expected_shape() -> None:
    response = client.get("/health")
    body = response.json()

    assert body["status"] == "ok"
    assert "service" in body
    assert "environment" in body
