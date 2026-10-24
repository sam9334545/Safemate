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
