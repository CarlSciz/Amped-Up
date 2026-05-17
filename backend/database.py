from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .db_url import normalize_database_url

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_URL = f"sqlite:///{PROJECT_ROOT / 'amped_up_dev.db'}"
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL)
USING_DEFAULT_SQLITE = DATABASE_URL == DEFAULT_SQLITE_URL

engine_kwargs = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
