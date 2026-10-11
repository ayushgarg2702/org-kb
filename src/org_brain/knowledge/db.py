"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_database_url() -> str:
    url = os.environ.get("ORG_BRAIN_DATABASE_URL")
    if not url:
        raise RuntimeError("ORG_BRAIN_DATABASE_URL is not set")
    return url


def get_engine(url: str | None = None) -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        db_url = url or get_database_url()
        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
        _engine = create_engine(
            db_url, pool_pre_ping=not db_url.startswith("sqlite"), connect_args=connect_args
        )
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def create_all_tables(url: str | None = None) -> None:
    """Create schema (used for SQLite tests when Alembic/Postgres unavailable)."""
    from org_brain.knowledge.models import Base

    engine = get_engine(url)
    Base.metadata.create_all(engine)


def reset_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


@contextmanager
def session_scope(url: str | None = None) -> Generator[Session, None, None]:
    get_engine(url)
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
