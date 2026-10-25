"""Database connection, engine initialization, and session management using SQLAlchemy."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Environment Variables Loading via python-dotenv
# ---------------------------------------------------------------------------
# Attempt loading from backend/.env or root workspace .env
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(dotenv_path=BACKEND_DIR / ".env")
load_dotenv(dotenv_path=ROOT_DIR / ".env")
load_dotenv()  # Fallback to current working directory

# ---------------------------------------------------------------------------
# 2. Database URL Resolution & Engine Setup
# ---------------------------------------------------------------------------
# Read securely from environment; NEVER hardcode secrets
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning(
        "DATABASE_URL is not set in environment or .env. "
        "Falling back to local SQLite database ('sqlite:///./safemate.db') for development."
    )
    DATABASE_URL = "sqlite:///./safemate.db"

# Ensure SQLAlchemy 2.0+ compatibility with postgresql:// driver prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure engine connection parameters based on dialect
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Production-ready PostgreSQL connection pool settings
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(DATABASE_URL, **engine_kwargs)

# ---------------------------------------------------------------------------
# 3. Sessionmaker & Declarative Base
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# 4. FastAPI Session Dependency Generator
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Dependency generator that yields an isolated database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def safe_migrate_tables(db_engine, declarative_base_cls) -> None:
    """Inspect and add any missing columns from model metadata to existing tables.
    
    Guarantees that database upgrades (e.g. SQLite breadcrumbs or alert_id columns)
    are applied automatically at startup without dropping or altering existing user records.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db_engine)
    existing_table_names = set(inspector.get_table_names())

    with db_engine.connect() as conn:
        for table_name, table in declarative_base_cls.metadata.tables.items():
            if table_name not in existing_table_names:
                continue

            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = col.type.compile(db_engine.dialect)
                    default_clause = ""
                    if col.default is not None and hasattr(col.default, "arg"):
                        default_val = col.default.arg
                        if isinstance(default_val, str):
                            default_clause = f" DEFAULT '{default_val}'"
                        elif isinstance(default_val, (int, float)):
                            default_clause = f" DEFAULT {default_val}"
                    elif col.nullable:
                        default_clause = " DEFAULT NULL"

                    alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_clause}"
                    logger.info(f"Applying safe schema migration: {alter_stmt}")
                    try:
                        conn.execute(text(alter_stmt))
                        conn.commit()
                    except Exception as err:
                        logger.warning(f"Failed to execute alter statement '{alter_stmt}': {err}")

