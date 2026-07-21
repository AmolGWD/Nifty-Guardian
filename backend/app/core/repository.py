"""
Generic repository pattern for SQLAlchemy models.

Concrete repositories (introduced alongside their domain models in
later phases) should subclass Repository[ModelType] to get common CRUD
operations for free, adding domain-specific query methods as needed.
This keeps data-access logic out of routes and services.

Deliberately bound to DeclarativeBase rather than this app's own Base,
so the pattern is reusable independent of which declarative base a
model happens to use.
"""

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session


class Repository[ModelType: DeclarativeBase]:
    def __init__(self, session: Session, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    def get(self, id_: int) -> ModelType | None:
        return self._session.get(self._model, id_)

    def get_all(self) -> list[ModelType]:
        return list(self._session.scalars(select(self._model)).all())

    def add(self, instance: ModelType) -> ModelType:
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        self._session.delete(instance)
        self._session.commit()
