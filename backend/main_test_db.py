from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Add database imports
from app.core.database import init_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Test with database initialization only"""
    logger.info("=== STARTUP: Application starting ===")
    
    try:
        logger.info("=== STARTUP: Initializing database ===")
        await init_db()
        logger.info("=== STARTUP: Database initialized successfully ===")
    except Exception as e:
        logger.error(f"=== STARTUP: Database initialization failed: {e} ===")
        # Continue anyway for testing
    
    yield
    
    logger.info("=== SHUTDOWN: Application shutting down ===")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Content Repurpose API",
        description="API for content repurposing and transformation",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

app = create_app()

# Simple test route
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Include auth routes
from app.api.routes import auth
app.include_router(auth.router, prefix="/api")

# Simple test route for registration debugging
class TestUser(BaseModel):
    email: str
    username: str
    password: str

@app.post("/api/auth/test-register-simple")
async def test_register(user: TestUser):
    """Minimal test registration endpoint"""
    logger.info(f"Test registration attempt: {user.email}")
    return {
        "message": "Test registration successful",
        "email": user.email,
        "username": user.username,
        "note": "This is a minimal test endpoint"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)