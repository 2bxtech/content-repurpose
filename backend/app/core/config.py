import os
from typing import List, Set, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Content Repurposing Tool"
    API_V1_STR: str = "/api/v1"

    # Security: Production-grade JWT settings
    SECRET_KEY: str = Field(..., min_length=32)
    REFRESH_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7-day refresh tokens

    # Password security
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12

    # Session management
    MAX_SESSIONS_PER_USER: int = 5

    # Rate limiting
    RATE_LIMIT_AUTH_ATTEMPTS: str = "5/15m"  # 5 attempts per 15 minutes
    RATE_LIMIT_API_CALLS: str = "100/1m"  # 100 calls per minute
    RATE_LIMIT_TRANSFORMATIONS: str = "30/1h"  # 30 transformations per hour

    # Redis settings for session management and rate limiting
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Celery settings for background task processing
    CELERY_BROKER_URL: str = Field(default="")
    CELERY_RESULT_BACKEND: str = Field(default="")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)  # Set to True for testing

    def get_celery_broker_url(self) -> str:
        """Construct Celery broker URL"""
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL

        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_celery_result_backend(self) -> str:
        """Construct Celery result backend URL"""
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND

        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # AI Provider Configuration (Enhanced multi-provider support with failover)
    AI_PROVIDER: str = Field(
        default="openai", pattern="^(openai|anthropic|azure|local|mock)$"
    )

    # AI API Keys (configure based on chosen provider)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    CLAUDE_API_KEY: str = Field(default="", description="Anthropic Claude API key")
    AZURE_OPENAI_API_KEY: str = Field(default="", description="Azure OpenAI API key")
    AZURE_OPENAI_ENDPOINT: str = Field(default="", description="Azure OpenAI endpoint")

    # AI Model Configuration
    DEFAULT_AI_MODEL: str = Field(
        default="gpt-4o-mini", description="Default AI model to use"
    )
    AI_MAX_TOKENS: int = Field(
        default=4000, description="Maximum tokens per AI request"
    )
    AI_TEMPERATURE: float = Field(
        default=0.7, ge=0.0, le=2.0, description="AI response creativity"
    )

    # Enhanced AI Provider Management
    AI_PROVIDER_SELECTION_STRATEGY: str = Field(
        default="primary_failover", description="Provider selection strategy"
    )
    AI_ENABLE_FAILOVER: bool = Field(
        default=True, description="Enable automatic provider failover"
    )
    AI_COST_TRACKING: bool = Field(
        default=True, description="Enable cost tracking and limits"
    )
    AI_RATE_LIMITING: bool = Field(
        default=True, description="Enable per-provider rate limiting"
    )

    # AI Cost Management
    AI_MAX_COST_PER_HOUR: float = Field(
        default=10.0, description="Maximum cost per hour across all providers"
    )
    AI_MAX_REQUESTS_PER_MINUTE: int = Field(
        default=60, description="Maximum requests per minute per provider"
    )
    AI_BUDGET_ALERT_THRESHOLD: float = Field(
        default=0.8, description="Alert when budget reaches this percentage"
    )

    # AI Performance Monitoring
    AI_RESPONSE_TIME_THRESHOLD_MS: int = Field(
        default=30000, description="Response time threshold for provider health"
    )
    AI_ERROR_RATE_THRESHOLD: float = Field(
        default=0.1, description="Error rate threshold for provider health"
    )
    AI_PERFORMANCE_WINDOW_MINUTES: int = Field(
        default=60, description="Performance monitoring window"
    )

    # Database settings
    DATABASE_HOST: str = Field(default="localhost")
    DATABASE_PORT: int = Field(default=5433)
    DATABASE_NAME: str = Field(default="content_repurpose")
    DATABASE_USER: str = Field(default="postgres")
    DATABASE_PASSWORD: str = Field(default="postgres")
    DATABASE_URL: Optional[str] = Field(default=None)

    # Sync database URL for Alembic migrations
    DATABASE_URL_SYNC: Optional[str] = Field(default=None)

    def get_database_url(self, async_driver: bool = True) -> str:
        """Construct database URL if not provided"""
        if async_driver and self.DATABASE_URL:
            return self.DATABASE_URL
        elif not async_driver and self.DATABASE_URL_SYNC:
            return self.DATABASE_URL_SYNC

        # Construct URL
        driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"
        return f"{driver}://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"

    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # File upload settings
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {"pdf", "docx", "txt", "md"}

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    @field_validator("SECRET_KEY", "REFRESH_SECRET_KEY")
    @classmethod
    def validate_secret_keys(cls, v):
        if len(v) < 32:
            raise ValueError("Secret keys must be at least 32 characters long")
        return v

    @field_validator("PASSWORD_MIN_LENGTH")
    @classmethod
    def validate_password_length(cls, v):
        if v < 8:
            raise ValueError("Password minimum length must be at least 8")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
