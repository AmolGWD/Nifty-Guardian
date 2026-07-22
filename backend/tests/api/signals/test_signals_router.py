import time

from fastapi.testclient import TestClient

from app.api.signals.signals_service import SignalEngineRuntimeService
from app.main import app

client = TestClient(app)


def test_get_state_before_start(fresh_service: SignalEngineRuntimeService) -> None:
    response = client.get("/api/signals/state")
    assert response.status_code == 200
    assert response.json()["signals_sent_today"] == 0


def test_get_performance_before_start(fresh_service: SignalEngineRuntimeService) -> None:
    response = client.get("/api/signals/performance")
    assert response.status_code == 200
    assert response.json()["open_trades"] == []


def test_get_trades_before_start(fresh_service: SignalEngineRuntimeService) -> None:
    response = client.get("/api/signals/trades")
    assert response.status_code == 200
    assert response.json() == []


def test_get_report_today_before_start(fresh_service: SignalEngineRuntimeService) -> None:
    response = client.get("/api/signals/report/today")
    assert response.status_code == 200
    assert response.json()["total_signals"] == 0


def test_post_start_then_stop(fresh_service: SignalEngineRuntimeService) -> None:
    start_response = client.post("/api/signals/start")
    assert start_response.status_code == 200
    assert start_response.json()["running"] is True

    time.sleep(1.0)

    trades_response = client.get("/api/signals/trades")
    assert len(trades_response.json()) > 0

    stop_response = client.post("/api/signals/stop")
    assert stop_response.status_code == 200
    assert stop_response.json()["running"] is False


def test_post_start_twice_returns_409(fresh_service: SignalEngineRuntimeService) -> None:
    client.post("/api/signals/start")
    response = client.post("/api/signals/start")
    assert response.status_code == 409
    client.post("/api/signals/stop")


def test_post_stop_without_start_returns_409(fresh_service: SignalEngineRuntimeService) -> None:
    response = client.post("/api/signals/stop")
    assert response.status_code == 409


def test_get_status_reflects_start(fresh_service: SignalEngineRuntimeService) -> None:
    client.post("/api/signals/start")
    response = client.get("/api/signals/status")
    assert response.json()["running"] is True
    client.post("/api/signals/stop")
