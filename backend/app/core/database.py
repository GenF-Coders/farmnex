from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.base import Base
from app.core.config import settings


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=settings.db_pool_pre_ping,
    poolclass=NullPool,
)


# ============================================================
# SESSION FACTORY
# ============================================================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# DATABASE SESSION DEPENDENCY
# ============================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session to a FastAPI request.

    The session is automatically closed after the request.
    If an unexpected exception occurs, the transaction is
    rolled back before the exception is re-raised.
    """

    async with AsyncSessionLocal() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise

        finally:
            await session.close()


# ============================================================
# DATABASE CONNECTION CHECK
# ============================================================

async def check_database_connection() -> None:
    """
    Verify that the application can connect to PostgreSQL.
    """

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


# ============================================================
# CREATE TABLES
# ============================================================

async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


# ============================================================
# DATABASE SHUTDOWN
# ============================================================

async def close_database() -> None:
    """
    Close the SQLAlchemy connection pool when the application
    shuts down.
    """

    await engine.dispose()