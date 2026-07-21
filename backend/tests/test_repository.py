"""
Tests for the generic Repository pattern.

Uses a throwaway model on its own isolated DeclarativeBase, fully
decoupled from the application's real Base/metadata - this is
test-only infrastructure to prove the generic repository works, not a
preview of any real domain model. Concrete domain models arrive in
later phases alongside the features that need them.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.repository import Repository


class _TestBase(DeclarativeBase):
    pass


class _Widget(_TestBase):
    __tablename__ = "test_widgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


@pytest.fixture
def engine() -> Iterator[Engine]:
    test_engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(test_engine)
    yield test_engine
    _TestBase.metadata.drop_all(test_engine)


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def test_add_and_get(session: Session) -> None:
    repo = Repository(session, _Widget)

    created = repo.add(_Widget(name="first"))
    fetched = repo.get(created.id)

    assert fetched is not None
    assert fetched.name == "first"


def test_get_all(session: Session) -> None:
    repo = Repository(session, _Widget)
    repo.add(_Widget(name="a"))
    repo.add(_Widget(name="b"))

    assert len(repo.get_all()) == 2


def test_delete(session: Session) -> None:
    repo = Repository(session, _Widget)
    widget = repo.add(_Widget(name="to-delete"))

    repo.delete(widget)

    assert repo.get(widget.id) is None


def test_get_missing_returns_none(session: Session) -> None:
    repo = Repository(session, _Widget)

    assert repo.get(999) is None
