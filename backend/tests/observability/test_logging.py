import json
import logging

from app.observability.logging import JsonFormatter, get_request_id, set_request_id


def _make_record(message: str, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test.logger", level=logging.INFO, pathname="test.py", lineno=1,
        msg=message, args=(), exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_produces_valid_json_with_expected_fields() -> None:
    formatter = JsonFormatter()
    record = _make_record("hello world")

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.logger"
    assert "timestamp" in payload


def test_json_formatter_includes_request_id_when_set() -> None:
    formatter = JsonFormatter()
    set_request_id("req-abc-123")
    try:
        payload = json.loads(formatter.format(_make_record("with request id")))
        assert payload["request_id"] == "req-abc-123"
    finally:
        set_request_id(None)


def test_json_formatter_omits_request_id_when_not_set() -> None:
    formatter = JsonFormatter()
    set_request_id(None)

    payload = json.loads(formatter.format(_make_record("no request id")))

    assert "request_id" not in payload


def test_json_formatter_includes_extra_fields() -> None:
    formatter = JsonFormatter()
    record = _make_record("with extra", order_id="ord-1", strategy="EMABreakout")

    payload = json.loads(formatter.format(record))

    assert payload["order_id"] == "ord-1"
    assert payload["strategy"] == "EMABreakout"


def test_json_formatter_includes_exception_info() -> None:
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="test.logger", level=logging.ERROR, pathname="test.py", lineno=1,
            msg="failed", args=(), exc_info=sys.exc_info(),
        )

    payload = json.loads(formatter.format(record))

    assert "exception" in payload
    assert "ValueError" in payload["exception"]
    assert "boom" in payload["exception"]


def test_get_and_set_request_id_round_trip() -> None:
    set_request_id("round-trip-id")
    try:
        assert get_request_id() == "round-trip-id"
    finally:
        set_request_id(None)
    assert get_request_id() is None
