from core.config import settings
from core.dependencies import get_secret_provider
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

connection_uri = settings.db.get_database_url_async(get_secret_provider().get_db_password())
if connection_uri.startswith("postgres://"):
    connection_uri = connection_uri.replace("postgres://", "postgresql://", 1)

engine = create_async_engine(
    connection_uri,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
