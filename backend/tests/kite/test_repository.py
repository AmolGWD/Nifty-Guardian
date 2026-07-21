from collections.abc import Iterator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.kite.repository import KiteSessionRepository

IST = ZoneInfo("Asia/Kolkata")


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


def test_save_and_get_valid_access_token_today(session: Session) -> None:
    repo = KiteSessionRepository(session)

    repo.save_session(
        user_id="AB1234",
        user_name="Test User",
        access_token="plaintext-token",
        login_time=datetime.now(IST),
    )

    assert repo.get_valid_access_token() == "plaintext-token"


def test_stored_token_is_encrypted_at_rest(session: Session) -> None:
    repo = KiteSessionRepository(session)

    repo.save_session(
        user_id="AB1234",
        user_name="Test User",
        access_token="plaintext-token",
        login_time=datetime.now(IST),
    )

    stored = repo.get_latest()

    assert stored is not None
    assert stored.encrypted_access_token != "plaintext-token"


def test_no_session_returns_none(session: Session) -> None:
    repo = KiteSessionRepository(session)

    assert repo.get_valid_access_token() is None


def test_stale_session_returns_none(session: Session) -> None:
    repo = KiteSessionRepository(session)

    repo.save_session(
        user_id="AB1234",
        user_name="Test User",
        access_token="yesterdays-token",
        login_time=datetime.now(IST) - timedelta(days=1),
    )

    assert repo.get_valid_access_token() is None


def test_get_latest_returns_most_recent_session(session: Session) -> None:
    repo = KiteSessionRepository(session)

    repo.save_session(
        user_id="OLD",
        user_name="Old User",
        access_token="old-token",
        login_time=datetime.now(IST) - timedelta(days=1),
    )
    repo.save_session(
        user_id="NEW",
        user_name="New User",
        access_token="new-token",
        login_time=datetime.now(IST),
    )

    latest = repo.get_latest()

    assert latest is not None
    assert latest.user_id == "NEW"
