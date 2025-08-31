import redis.asyncio as redis
import json
from typing import Any, Optional, Dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for caching and session management"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            connection_kwargs = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB,
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5
            }
            
            # Add password if configured
            if settings.REDIS_PASSWORD:
                connection_kwargs["password"] = settings.REDIS_PASSWORD
            
            self.redis_client = redis.Redis(**connection_kwargs)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}. Continuing without caching.")
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set a value in Redis"""
        if not self.redis_client:
            return False
        
        try:
            json_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self.redis_client.set(key, json_value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON, fall back to string
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        if not self.redis_client:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False
    
    async def cache_document_content(self, document_id: str, content: Dict[str, Any]) -> bool:
        """Cache extracted document content"""
        key = f"document_content:{document_id}"
        return await self.set(key, content, expire=86400)  # 24 hours
    
    async def get_cached_document_content(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get cached document content"""
        key = f"document_content:{document_id}"
        return await self.get(key)
    
    async def cache_user_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache user session data"""
        key = f"user_session:{user_id}"
        return await self.set(key, session_data, expire=1800)  # 30 minutes
    
    async def get_cached_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user session"""
        key = f"user_session:{user_id}"
        return await self.get(key)
    
    async def blacklist_token(self, token_jti: str, expire_time: int) -> bool:
        """Add token to blacklist"""
        key = f"blacklist:{token_jti}"
        return await self.set(key, "blacklisted", expire=expire_time)
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        key = f"blacklist:{token_jti}"
        result = await self.get(key)
        return result is not None

# Global instance
redis_service = RedisService()