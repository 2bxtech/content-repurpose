# backend/app/core/database.py
# Production-grade async SQLAlchemy configuration

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
from .config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global variables
engine = None
async_session_factory = None

class DatabaseConfig:
    """Database configuration manager"""
    
    @staticmethod
    def get_async_database_url():
        """Get properly formatted async database URL"""
        database_url = settings.get_database_url()
        if not database_url:
            return None
        
        # Ensure proper async URL format
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif not database_url.startswith("postgresql+asyncpg://"):
            # Handle bare connection strings
            if "@" in database_url and "/" in database_url:
                database_url = f"postgresql+asyncpg://{database_url}"
        
        return database_url
    
    @staticmethod
    def create_engine_config():
        """Create engine configuration"""
        database_url = DatabaseConfig.get_async_database_url()
        if not database_url:
            return None
        
        return {
            'url': database_url,
            'poolclass': QueuePool,
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': settings.DEBUG,
            'future': True,
            # Critical for avoiding greenlet issues
            'pool_reset_on_return': 'commit',
        }

def _initialize_engine():
    """Initialize async engine and session factory"""
    global engine, async_session_factory
    
    if engine is not None:
        return engine, async_session_factory
    
    try:
        config = DatabaseConfig.create_engine_config()
        if config:
            engine = create_async_engine(**config)
            
            # Critical: expire_on_commit=False prevents lazy loading issues
            async_session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,  # CRITICAL: Prevents MissingGreenlet
                autoflush=False,
                autocommit=False,
            )
            logger.info("✅ Async database engine initialized successfully")
        else:
            logger.warning("⚠️ DATABASE_URL not configured")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize database engine: {e}")
        engine = None
        async_session_factory = None
    
    return engine, async_session_factory

async def get_db_session():
    """
    Database session dependency with proper async handling
    This is the core dependency injection for database sessions
    """
    engine, session_factory = _initialize_engine()
    
    if not session_factory:
        logger.debug("Database not configured, yielding None for in-memory mode")
        yield None
        return

    async with session_factory() as session:
        try:
            # Test the connection
            await session.execute(text("SELECT 1"))
            yield session
            
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            # Session cleanup is handled by async context manager
            pass

async def test_database_connection():
    """Test database connection and return status"""
    try:
        engine, session_factory = _initialize_engine()
        if not session_factory:
            return False, "Database not configured"
        
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True, "Database connection successful"
            
    except Exception as e:
        return False, f"Database connection failed: {e}"

async def init_db():
    """Initialize database and create tables"""
    engine, _ = _initialize_engine()
    
    if not engine:
        logger.warning("⚠️ Database not configured, skipping table creation")
        return
    
    try:
        # Import all models to ensure they're registered
        from app.core.models import Base
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("✅ Database tables created/verified")
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

async def close_db():
    """Close database connections gracefully"""
    global engine, async_session_factory
    
    if engine:
        await engine.dispose()
        engine = None
        async_session_factory = None
        logger.info("✅ Database connections closed gracefully")

# Health check function
async def database_health_check():
    """Comprehensive database health check"""
    try:
        is_connected, message = await test_database_connection()
        if is_connected:
            return {"status": "healthy", "message": message}
        else:
            return {"status": "unhealthy", "message": message}
    except Exception as e:
        return {"status": "error", "message": str(e)}