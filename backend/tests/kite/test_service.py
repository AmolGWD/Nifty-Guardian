from collections.abc import Iterator
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.kite.repository import KiteSessionRepository
from app.kite.service import KiteAuthService

IST = ZoneInfo("Asia/Kolkata")


class _FakeKiteClient:
    def __init__(self, session_response: dict[str, Any]) -> None:
        self._session_response = session_response
        self.requested_login_url = False
        self.last_request_token: str | None = None
        self.last_api_secret: str | None = None

    def login_url(self) -> str:
        self.requested_login_url = True
        return "https://kite.zerodha.com/connect/login?api_key=fake&v=3"

    def generate_session(self, request_token: str, api_secret: str) -> dict[str, Any]:
        self.last_request_token = request_token
        self.last_api_secret = api_secret
        return self._session_response


@pytest.fixture
def engine() -> Iterator[Engine]:
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def test_login_url_delegates_to_client(session: Session) -> None:
    fake_client = _FakeKiteClient(session_response={})
    service = KiteAuthService(fake_client, KiteSessionRepository(session))

    url = service.login_url()

    assert fake_client.requested_login_url
    assert url == "https://kite.zerodha.com/connect/login?api_key=fake&v=3"


def test_complete_login_persists_session_and_returns_summary(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.kite.service.settings.kite_api_secret", "fake-secret")

    fake_client = _FakeKiteClient(
        session_response={
            "user_id": "AB1234",
            "user_name": "Test User",
            "access_token": "real-looking-token",
            "login_time": datetime.now(IST),
        }
    )
    repository = KiteSessionRepository(session)
    service = KiteAuthService(fake_client, repository)

    result = service.complete_login("incoming-request-token")

    assert result == {"user_id": "AB1234", "user_name": "Test User"}
    assert fake_client.last_request_token == "incoming-request-token"
    assert fake_client.last_api_secret == "fake-secret"
    assert repository.get_valid_access_token() == "real-looking-token"


def test_complete_login_raises_without_api_secret_configured(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.kite.service.settings.kite_api_secret", "")

    fake_client = _FakeKiteClient(session_response={})
    service = KiteAuthService(fake_client, KiteSessionRepository(session))

    with pytest.raises(RuntimeError, match="KITE_API_SECRET"):
        service.complete_login("some-token")
