"""
Test with database completely disabled
This will prove if the database is causing the auth requirement
"""

import os

# Override all database environment variables BEFORE any imports
os.environ['DATABASE_URL'] = ''
os.environ['DATABASE_URL_SYNC'] = ''
os.environ['DATABASE_HOST'] = ''
os.environ['DATABASE_PORT'] = ''
os.environ['DATABASE_NAME'] = ''
os.environ['DATABASE_USER'] = ''
os.environ['DATABASE_PASSWORD'] = ''

# Now import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="No Database Test")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TransformationParameters(BaseModel):
    wordCount: int
    tone: str

class TransformationRequest(BaseModel):
    sourceDocument: str
    transformationType: str
    parameters: TransformationParameters

class TransformationResponse(BaseModel):
    id: str
    status: str
    message: str
    sourceDocument: str
    transformationType: str
    parameters: Dict[str, Any]

# The problematic endpoint path
@app.post("/api/transformations", response_model=TransformationResponse)
async def create_transformation(request: TransformationRequest):
    """Test the exact path that's failing"""
    logger.info("✅ No-DB transformation endpoint hit successfully")
    
    return TransformationResponse(
        id=str(uuid.uuid4()),
        status="success",
        message="Transformation created (no database)",
        sourceDocument=request.sourceDocument[:100] + "..." if len(request.sourceDocument) > 100 else request.sourceDocument,
        transformationType=request.transformationType,
        parameters={
            "wordCount": request.parameters.wordCount,
            "tone": request.parameters.tone
        }
    )

@app.get("/")
async def root():
    return {"message": "No database test", "database": "DISABLED"}

# Now try to import your app's routers to see if they work without DB
try:
    from app.api.routes import transformations
    app.include_router(transformations.router, prefix="/api/alt")
    logger.info("✅ Your transformations router loaded at /api/alt")
except Exception as e:
    logger.warning(f"Could not load transformations router: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("\n🔬 NO DATABASE TEST")
    print("All database connections disabled")
    print("\nTest the problematic path:")
    print('curl -X POST http://localhost:8003/api/transformations -H "Content-Type: application/json" -d \'{"sourceDocument": "test", "transformationType": "summary", "parameters": {"wordCount": 100, "tone": "professional"}}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8003)