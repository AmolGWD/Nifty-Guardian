"""
Database engine, session management, and declarative base.

Concrete models (introduced in later phases) should subclass `Base`.
Routes and services obtain a session exclusively via the `get_db`
FastAPI dependency, never by importing `SessionLocal` directly - this
keeps session lifecycle (open/commit/close) in one place.
"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_directory_exists(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    db_path = Path(database_url.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory_exists(settings.database_url)

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
