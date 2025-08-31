import os
from typing import List, Set, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Content Repurposing Tool"
    API_V1_STR: str = "/api/v1"
    
    # Security: Production-grade JWT settings
    SECRET_KEY: str = Field(..., min_length=32)
    REFRESH_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7-day refresh tokens
    
    # Password security
    PASSWORD_MIN_LENGTH: int = 12
    BCRYPT_ROUNDS: int = 12
    
    # Session management
    MAX_SESSIONS_PER_USER: int = 5
    
    # Rate limiting
    RATE_LIMIT_AUTH_ATTEMPTS: str = "5/15m"  # 5 attempts per 15 minutes
    RATE_LIMIT_API_CALLS: str = "100/1m"     # 100 calls per minute
    RATE_LIMIT_TRANSFORMATIONS: str = "30/1h" # 30 transformations per hour
    
    # Redis settings for session management and rate limiting
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # AI Provider Configuration (Flexible multi-provider support)
    AI_PROVIDER: str = Field(default="openai", pattern="^(openai|anthropic|azure|local)$")
    
    # AI API Keys (configure based on chosen provider)
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    CLAUDE_API_KEY: str = Field(default="", description="Anthropic Claude API key") 
    AZURE_OPENAI_API_KEY: str = Field(default="", description="Azure OpenAI API key")
    AZURE_OPENAI_ENDPOINT: str = Field(default="", description="Azure OpenAI endpoint")
    
    # AI Model Configuration
    DEFAULT_AI_MODEL: str = Field(default="gpt-4o-mini", description="Default AI model to use")
    AI_MAX_TOKENS: int = Field(default=4000, description="Maximum tokens per AI request")
    AI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="AI response creativity")
    
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
    
    # Database settings
    DATABASE_URL: str = Field(default="", description="PostgreSQL database URL")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "content_repurpose")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "postgres")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @field_validator('SECRET_KEY', 'REFRESH_SECRET_KEY')
    @classmethod
    def validate_secret_keys(cls, v):
        if len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v
    
    @field_validator('PASSWORD_MIN_LENGTH')
    @classmethod
    def validate_password_length(cls, v):
        if v < 8:
            raise ValueError('Password minimum length must be at least 8')
        return v
    
    def get_database_url(self) -> str:
        """Construct DATABASE_URL if not provided"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file

settings = Settings()