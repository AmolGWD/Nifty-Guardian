from app.observability.diagnostics import get_app_metadata, get_runtime_diagnostics


def test_get_app_metadata_reflects_given_name_and_environment() -> None:
    metadata = get_app_metadata(app_name="Test App", environment="staging")

    assert metadata.name == "Test App"
    assert metadata.environment == "staging"
    assert metadata.version
    assert metadata.python_version.count(".") == 2


def test_get_runtime_diagnostics_reports_a_non_negative_uptime() -> None:
    diagnostics = get_runtime_diagnostics()

    assert diagnostics.uptime_seconds >= 0
    assert diagnostics.process_id > 0
    assert diagnostics.hostname


def test_uptime_increases_between_two_calls() -> None:
    first = get_runtime_diagnostics()
    second = get_runtime_diagnostics()

    assert second.uptime_seconds >= first.uptime_seconds
