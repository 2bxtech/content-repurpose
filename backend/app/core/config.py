import os
from typing import List, Set
from pydantic import Field, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Content Repurposing Tool"
    API_V1_STR: str = "/api/v1"
    
    # Security: Production-grade JWT settings
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7-day refresh
    
    # Database with validation
    DATABASE_URL: str = Field(default="", description="PostgreSQL connection URL")
    
    # Redis for caching, sessions, and token blacklist
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = Field(6379, ge=1, le=65535)
    REDIS_DB: int = Field(0, ge=0, le=15)
    REDIS_PASSWORD: str = Field(default="", description="Redis password")
    
    # AI Services
    CLAUDE_API_KEY: str = Field(..., min_length=10)
    
    # Enhanced file settings with security
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: Set[str] = {"pdf", "docx", "txt", "md"}
    
    # Rate limiting
    RATE_LIMIT_AUTH_ATTEMPTS: str = "5/15m"
    RATE_LIMIT_API_CALLS: str = "100/1m"
    RATE_LIMIT_TRANSFORMATIONS: str = "30/1h"
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12
    
    # Environment configuration
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=True)
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if v and not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must be a PostgreSQL connection string')
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "forbid",
    }

settings = Settings()