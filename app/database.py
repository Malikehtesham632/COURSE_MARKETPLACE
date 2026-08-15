"""
Database connection setup: the engine, the session factory, and the
get_db dependency every route uses to talk to the database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# check_same_thread is only needed for SQLite (used for local testing).
# PostgreSQL, the real database used in production, doesn't need it.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency (layer 1): opens a fresh database session for one request,
    hands it to whichever route needs it, then closes it automatically
    once the request is finished - even if an error happened.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
