from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_returns_200_and_alive_status() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_returns_200_when_everything_is_healthy() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert {check["name"] for check in body["checks"]} == {"database", "configuration"}
    assert all(check["ok"] for check in body["checks"])


def test_metadata_reports_app_name_and_environment() -> None:
    response = client.get("/health/metadata")

    assert response.status_code == 200
    body = response.json()
    assert body["app"]["name"]
    assert body["app"]["environment"]
    assert "uptime_seconds" in body["runtime"]


def test_metrics_reflects_requests_already_made_in_this_test_run() -> None:
    client.get("/health/live")

    response = client.get("/health/metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["counters"]["http_requests_total"] >= 1


def test_every_response_carries_an_x_request_id_header() -> None:
    response = client.get("/health/live")

    assert "X-Request-ID" in response.headers


def test_incoming_x_request_id_is_echoed_back() -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "caller-supplied-id"})

    assert response.headers["X-Request-ID"] == "caller-supplied-id"


def test_existing_health_endpoint_is_unaffected_by_the_new_routes() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
