import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, documents, transformations, health, workspaces
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
        if redis_service.is_connected():
            logger.info("Redis connection established")
        else:
            logger.warning("Redis not available - continuing without Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {str(e)} - continuing without Redis")
        if settings.ENVIRONMENT == "production":
            raise
    
    yield        
    
    try:
        await redis_service.disconnect()  # or whatever cleanup method exists
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Redis cleanup failed: {str(e)}")
    
    # Shutdown
    logger.info("Shutting down Content Repurposing Tool API")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade Content Repurposing Tool API with JWT refresh tokens, session management, and rate limiting",
    version="2.0.0",
    lifespan=lifespan
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
app.include_router(workspaces.router, prefix="/api", tags=["workspaces"])
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