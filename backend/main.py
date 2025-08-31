import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import auth, documents, transformations, health
from app.core.config import settings
from app.services.redis_service import redis_service
from app.middleware.rate_limit import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Content Repurposing Tool API v2.0.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize Redis connection
    try:
        await redis_service.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {str(e)}")
        if settings.ENVIRONMENT == "production":
            raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Content Repurposing Tool API")
from app.core.database import init_db, close_db
from app.services.redis_service import redis_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    await redis_service.connect()
    yield
    # Shutdown
    await redis_service.disconnect()
    await close_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade Content Repurposing Tool API with JWT refresh tokens, session management, and rate limiting",
    version="2.0.0",
    lifespan=lifespan
    description="Content Repurposing Tool API - Production Ready",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Configure CORS with production-ready settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])

@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "2.0.0",
        "status": "ok",
        "message": "Production-grade Content Repurposing Tool API with enhanced security",
        "features": [
            "JWT refresh tokens",
            "Session management",
            "Rate limiting",
            "Token blacklisting",
            "Password strength validation",
            "Audit logging"
        ],
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )