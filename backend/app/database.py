"""SQLAlchemy Engine/Session/Base fuer SQLite."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLite: check_same_thread=False fuer FastAPI (mehrere Threads).
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}, future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass
