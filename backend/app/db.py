from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(os.environ.get("SAF_DB_PATH", str(Path(__file__).resolve().parent.parent / "saf.db")))
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def persist(db, obj):
    """Add *obj* to the session, commit, refresh it and return it."""
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
