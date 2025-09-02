import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, documents, transformations, health, workspaces, websockets, ai_providers, security, monitoring
from app.core.config import settings
from app.services.redis_service import redis_service
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware, InputValidationMiddleware
from app.services.audit_service import audit_service
from app.services.health_monitoring import health_monitor
from app.services.metrics_service import metrics_collector, performance_monitor
from app.services.secret_management import secret_manager
from app.core.websocket_manager import manager

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
    logger.info("Starting Content Repurposing Tool API v2.0.0 with Phase 8 Security & Monitoring")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize Redis connection
    try:
        await redis_service.connect()
        if redis_service.is_connected():
            logger.info("Redis connection established")
            # Start WebSocket Redis listener
            await manager.start_redis_listener()
            logger.info("WebSocket Redis listener started")
        else:
            logger.warning("Redis not available - continuing without Redis")
    except Exception as e:
        logger.warning(f"Redis connection failed: {str(e)} - continuing without Redis")
        if settings.ENVIRONMENT == "production":
            raise
    
    # Initialize Phase 8 services
    try:
        # Initialize audit service
        await audit_service.initialize()
        logger.info("Audit service initialized")
        
        # Initialize health monitoring
        await health_monitor.initialize()
        logger.info("Health monitoring service initialized")
        
        # Initialize metrics collection
        await metrics_collector.initialize()
        await performance_monitor.initialize()
        logger.info("Metrics and performance monitoring initialized")
        
        # Initialize secret management
        await secret_manager.initialize()
        logger.info("Secret management service initialized")
        
        # Log startup audit event
        await audit_service.log_system_event(
            event_type="system_startup",
            details={"version": "2.0.0", "environment": settings.ENVIRONMENT}
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize Phase 8 services: {e}")
        if settings.ENVIRONMENT == "production":
            raise
    
    yield        
    
    try:
        # Log shutdown audit event
        await audit_service.log_system_event(
            event_type="system_shutdown",
            details={"version": "2.0.0", "environment": settings.ENVIRONMENT}
        )
        
        # Stop WebSocket Redis listener
        await manager.stop_redis_listener()
        logger.info("WebSocket Redis listener stopped")
        
        # Cleanup Phase 8 services
        await performance_monitor.cleanup()
        await metrics_collector.cleanup()
        await health_monitor.cleanup()
        await audit_service.cleanup()
        logger.info("Phase 8 services cleaned up")
        
        await redis_service.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Cleanup failed: {str(e)}")
    
    # Shutdown
    logger.info("Shutting down Content Repurposing Tool API")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade Content Repurposing Tool API with comprehensive security and monitoring",
    version="2.0.0",
    lifespan=lifespan
)

# Add Phase 8 security middleware (order matters!)
app.add_middleware(SecurityMiddleware)  # Security headers and CSP
app.add_middleware(InputValidationMiddleware)  # Input validation and sanitization
app.add_middleware(RateLimitMiddleware)  # Rate limiting

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
app.include_router(websockets.router, prefix="/api", tags=["websockets"])
app.include_router(ai_providers.router, prefix="/api/ai", tags=["ai-providers"])
# Phase 8: Security and Monitoring routes
app.include_router(security.router, prefix="/api", tags=["security"])
app.include_router(monitoring.router, prefix="/api", tags=["monitoring"])

@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "2.0.0",
        "status": "ok",
        "message": "Production-grade Content Repurposing Tool API with Phase 8 Security & Monitoring",
        "features": [
            "JWT refresh tokens",
            "Session management", 
            "Rate limiting",
            "Token blacklisting",
            "Password strength validation",
            "Comprehensive audit logging",
            "Security headers and CSP",
            "Health monitoring",
            "Performance metrics",
            "Secret management",
            "Error tracking and alerting"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "security": "/api/security",
            "monitoring": "/api/monitoring"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )