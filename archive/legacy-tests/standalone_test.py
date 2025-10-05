"""
Standalone test server - completely isolated from your app
This bypasses ALL your existing code to prove the concept works
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uuid
import uvicorn

# Create a NEW app, not importing anything from your codebase
app = FastAPI(title="Standalone Test")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define models directly here
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

# Create the endpoint directly
@app.post("/api/transformations", response_model=TransformationResponse)
async def create_transformation(request: TransformationRequest):
    """Transformation endpoint with NO authentication"""
    print(f"✅ Received transformation request: {request.transformationType}")
    
    return TransformationResponse(
        id=str(uuid.uuid4()),
        status="success",
        message="Transformation created successfully",
        sourceDocument=request.sourceDocument[:100] + "..." if len(request.sourceDocument) > 100 else request.sourceDocument,
        transformationType=request.transformationType,
        parameters={
            "wordCount": request.parameters.wordCount,
            "tone": request.parameters.tone
        }
    )

@app.get("/")
async def root():
    return {"message": "Standalone test server running"}

if __name__ == "__main__":
    print("\n🔬 STANDALONE TEST SERVER")
    print("This server has ZERO dependencies on your existing code")
    print("If this works but your main.py doesn't, the problem is in your app structure\n")
    print("Starting on port 8001...")
    print("\nTest with:")
    print('curl -X POST http://localhost:8001/api/transformations -H "Content-Type: application/json" -d \'{"sourceDocument": "test", "transformationType": "summary", "parameters": {"wordCount": 100, "tone": "professional"}}\'')
    
    uvicorn.run(app, host="0.0.0.0", port=8001)