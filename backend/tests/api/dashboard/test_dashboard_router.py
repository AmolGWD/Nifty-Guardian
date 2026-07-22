from fastapi.testclient import TestClient

from app.api.dashboard.dashboard_service import DashboardRuntimeService
from app.main import app
from app.runtime.engine_config import ReplaySpeed
from app.runtime.session_controller import SessionState
from tests.api.dashboard.helpers import wait_until

client = TestClient(app)


def test_get_dashboard_before_any_session_returns_empty_snapshot(
    fresh_service: DashboardRuntimeService,
) -> None:
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"]["session_state"] == "NotStarted"
    assert body["current_candle"] is None
    assert body["orders"] == []
    assert body["portfolio"]["cash"] == 100_000.0


def test_get_dashboard_reflects_a_running_session(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=25)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"]["processed_candles"] == 25
    assert body["runtime"]["total_candles"] == 25
    assert body["current_candle"] is not None
    assert "health" in body
    assert "performance" in body
    assert "journal" in body


def test_get_dashboard_response_shape_matches_the_frontend_contract(
    fresh_service: DashboardRuntimeService,
) -> None:
    response = client.get("/api/dashboard")
    body = response.json()

    expected_keys = {
        "runtime",
        "current_candle",
        "market_context",
        "latest_signal",
        "latest_risk_decision",
        "latest_recommendation",
        "orders",
        "positions",
        "portfolio",
        "journal",
        "health",
        "performance",
    }
    assert expected_keys.issubset(body.keys())
