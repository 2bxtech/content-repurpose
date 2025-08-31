import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import auth, documents, transformations
from app.core.config import settings
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
    description="Content Repurposing Tool API - Production Ready",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])

@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "message": "Content Repurposing Tool API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)