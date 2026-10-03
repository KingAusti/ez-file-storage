import structlog
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

logger = structlog.get_logger()

# Sync engine for migrations and initial setup
engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=300, echo=settings.debug
)

# Async engine for application use
async_engine = create_async_engine(
    settings.database_url_async,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


def get_db():
    """Dependency for getting database session (sync)"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db():
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Async database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()
