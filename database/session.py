from typing import Optional

from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def init_database_session(db_password: str):
    global _SessionLocal
    if _SessionLocal is None:
        connection_uri = settings.db.get_database_url_async(db_password)
        if connection_uri.startswith("postgres://"):
            connection_uri = connection_uri.replace("postgres://", "postgresql://", 1)

        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(
            connection_uri,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

        _SessionLocal = async_sessionmaker(
            autoflush=False,
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


def get_session_local() -> async_sessionmaker[AsyncSession]:
    if _SessionLocal is None:
        raise RuntimeError("Database session not initialized. Call init_database_session() first.")
    return _SessionLocal
