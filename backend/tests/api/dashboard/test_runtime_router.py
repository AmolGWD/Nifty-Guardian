from fastapi.testclient import TestClient

from app.api.dashboard.dashboard_service import DashboardRuntimeService
from app.main import app
from app.runtime.session_controller import SessionState
from tests.api.dashboard.helpers import wait_until

client = TestClient(app)


def test_get_runtime_state_before_start(fresh_service: DashboardRuntimeService) -> None:
    response = client.get("/api/runtime/state")
    assert response.status_code == 200
    assert response.json() == {"state": "NotStarted"}


def test_get_runtime_health_before_start(fresh_service: DashboardRuntimeService) -> None:
    response = client.get("/api/runtime/health")
    assert response.status_code == 200
    body = response.json()
    assert body["processed_candles"] == 0
    assert body["current_state"] == "NotStarted"


def test_start_returns_running_stats(fresh_service: DashboardRuntimeService) -> None:
    response = client.post("/api/runtime/start")
    assert response.status_code == 200
    assert response.json()["session_state"] == "Running"


def test_start_twice_returns_409(fresh_service: DashboardRuntimeService) -> None:
    client.post("/api/runtime/start")
    response = client.post("/api/runtime/start")
    assert response.status_code == 409
    assert "detail" in response.json()


def test_pause_before_start_returns_409(fresh_service: DashboardRuntimeService) -> None:
    response = client.post("/api/runtime/pause")
    assert response.status_code == 409


def test_pause_and_resume_round_trip(fresh_service: DashboardRuntimeService) -> None:
    client.post("/api/runtime/start")

    response = client.post("/api/runtime/pause")
    assert response.status_code == 200
    assert response.json()["session_state"] == "Paused"

    response = client.post("/api/runtime/resume")
    assert response.status_code == 200
    assert response.json()["session_state"] == "Running"


def test_stop_returns_stopped_state(fresh_service: DashboardRuntimeService) -> None:
    client.post("/api/runtime/start")
    response = client.post("/api/runtime/stop")
    assert response.status_code == 200
    assert response.json()["session_state"] == "Stopped"


def test_resume_without_pause_returns_409(fresh_service: DashboardRuntimeService) -> None:
    client.post("/api/runtime/start")
    response = client.post("/api/runtime/resume")
    assert response.status_code == 409


def test_replay_accepts_speed_and_maximum_candles(fresh_service: DashboardRuntimeService) -> None:
    response = client.post(
        "/api/runtime/replay", json={"replay_speed": "Unlimited", "maximum_candles": 12}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["replay_speed"] == "Unlimited"
    assert body["total_candles"] == 12


def test_replay_defaults_when_body_omitted(fresh_service: DashboardRuntimeService) -> None:
    response = client.post("/api/runtime/replay", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["replay_speed"] == "1x"


def test_replay_can_be_called_repeatedly(fresh_service: DashboardRuntimeService) -> None:
    client.post("/api/runtime/replay", json={"replay_speed": "Unlimited", "maximum_candles": 10})
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    response = client.post(
        "/api/runtime/replay", json={"replay_speed": "Unlimited", "maximum_candles": 15}
    )
    assert response.status_code == 200
    assert response.json()["total_candles"] == 15


def test_full_lifecycle_via_http(fresh_service: DashboardRuntimeService) -> None:
    assert client.post("/api/runtime/start").status_code == 200
    assert client.post("/api/runtime/pause").status_code == 200
    assert client.get("/api/runtime/state").json()["state"] == "Paused"
    assert client.post("/api/runtime/resume").status_code == 200
    assert client.post("/api/runtime/stop").status_code == 200
    assert client.get("/api/runtime/state").json()["state"] == "Stopped"
