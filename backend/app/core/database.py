from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine with production-grade pooling
engine = None
async_session_factory = None


def create_engine():
    """Create database engine with production-grade settings"""
    global engine, async_session_factory

    database_url = settings.get_database_url()
    if not database_url:
        logger.warning("DATABASE_URL not configured, using in-memory storage")
        return None, None

    # Async engine with production-grade pooling
    engine = create_async_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,  # Base connections
        max_overflow=30,  # Additional connections under load
        pool_timeout=30,  # Wait time for connection
        pool_recycle=3600,  # Recycle connections every hour
        pool_pre_ping=True,  # Validate connections before use
        echo=settings.DEBUG,  # Log SQL queries only in debug mode
    )

    # Session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )

    return engine, async_session_factory


async def get_db_session():
    """Database session dependency"""
    if not async_session_factory:
        logger.warning("Database not configured, using in-memory storage")
        yield None
        return

    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection"""
    global engine, async_session_factory
    engine, async_session_factory = create_engine()

    if engine:
        logger.info("Database connection initialized")
    else:
        logger.warning("Database not configured, continuing with in-memory storage")


async def close_db():
    """Close database connections"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")
