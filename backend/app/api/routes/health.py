from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from app.services.redis_service import redis_service
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "2.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including service dependencies"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Check Redis connection
    try:
        redis_connected = redis_service.is_connected()
        health_status["services"]["redis"] = {
            "status": "healthy" if redis_connected else "unhealthy",
            "connected": redis_connected
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check authentication service
    try:
        from app.services.auth_service import auth_service
        # Test password hashing (basic functionality test)
        test_hash = auth_service.get_password_hash("test_password_123")
        auth_working = len(test_hash) > 0
        
        health_status["services"]["auth"] = {
            "status": "healthy" if auth_working else "unhealthy",
            "password_hashing": auth_working
        }
    except Exception as e:
        health_status["services"]["auth"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Overall status
    if health_status["status"] == "degraded":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status

@router.get("/health/redis")
async def redis_health():
    """Redis-specific health check"""
    try:
        connected = redis_service.is_connected()
        if connected:
            # Test basic operations
            test_key = "health_check_test"
            redis_service.set(test_key, "test_value", expire=10)
            test_value = redis_service.get(test_key)
            
            return {
                "status": "healthy",
                "connected": True,
                "operations_working": test_value == "test_value"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Redis connection failed"
                }
            )
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "error": str(e)
            }
        )