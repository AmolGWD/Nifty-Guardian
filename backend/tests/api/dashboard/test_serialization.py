"""
Verifies DashboardSnapshotResponse/RuntimeStatsResponse/HealthSnapshot
serialize to JSON with the exact field names and enum string values
the frontend's `services/api/` client (camelCase-mapping adapter,
frontend/src/services/api/dashboard.ts) expects to read.
"""

from fastapi.testclient import TestClient

from app.api.dashboard.dashboard_service import DashboardRuntimeService
from app.main import app
from app.runtime.engine_config import ReplaySpeed
from app.runtime.session_controller import SessionState
from tests.api.dashboard.helpers import wait_until

client = TestClient(app)


def test_runtime_stats_fields_are_snake_case(fresh_service: DashboardRuntimeService) -> None:
    response = client.get("/api/dashboard")
    runtime = response.json()["runtime"]

    assert set(runtime.keys()) == {
        "session_state",
        "replay_speed",
        "processed_candles",
        "total_candles",
        "events_published",
        "orders_generated",
        "uptime_seconds",
    }


def test_session_state_serializes_as_the_enum_string_value(
    fresh_service: DashboardRuntimeService,
) -> None:
    fresh_service.start()
    response = client.get("/api/dashboard")
    assert response.json()["runtime"]["session_state"] in (
        SessionState.RUNNING.value,
        SessionState.PAUSED.value,
        SessionState.STOPPED.value,
    )


def test_replay_speed_serializes_as_the_enum_string_value(
    fresh_service: DashboardRuntimeService,
) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.X5, maximum_candles=5)
    response = client.get("/api/dashboard")
    assert response.json()["runtime"]["replay_speed"] == "5x"


def test_order_serializes_with_the_full_frozen_order_shape(
    fresh_service: DashboardRuntimeService,
) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=40)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    response = client.get("/api/dashboard")
    orders = response.json()["orders"]
    assert len(orders) >= 1
    order = orders[0]
    assert set(order.keys()) == {
        "order_id",
        "strategy_name",
        "direction",
        "requested_price",
        "requested_quantity",
        "filled_quantity",
        "average_fill_price",
        "stop_loss",
        "target",
        "status",
        "rejection_reason",
        "created_at",
        "updated_at",
    }


def test_portfolio_serializes_computed_properties_too(
    fresh_service: DashboardRuntimeService,
) -> None:
    response = client.get("/api/dashboard")
    portfolio = response.json()["portfolio"]

    # drawdown/drawdown_percent are @property on the frozen Portfolio
    # model, not stored fields - confirms Pydantic still serializes them.
    assert "drawdown" in portfolio
    assert "drawdown_percent" in portfolio


def test_journal_entries_serialize_with_expected_shape(
    fresh_service: DashboardRuntimeService,
) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=40)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    response = client.get("/api/dashboard")
    journal = response.json()["journal"]
    assert len(journal) > 0
    entry = journal[0]
    assert set(entry.keys()) == {
        "entry_id",
        "entry_type",
        "timestamp",
        "source_event_id",
        "description",
    }


def test_health_endpoint_matches_dashboard_health_field(
    fresh_service: DashboardRuntimeService,
) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=20)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    health_response = client.get("/api/runtime/health").json()
    dashboard_response = client.get("/api/dashboard").json()["health"]

    assert health_response["processed_candles"] == dashboard_response["processed_candles"]
    assert health_response["current_state"] == dashboard_response["current_state"]
