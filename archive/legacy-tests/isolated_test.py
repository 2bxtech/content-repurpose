"""
Completely isolated test - new port, new endpoint name, no imports
Run this to test if the issue is environmental
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uuid
import uvicorn

# Create a COMPLETELY NEW app instance
isolated_app = FastAPI(title="Isolated Test")

# Add CORS
isolated_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# New model names to avoid any conflicts
class TestInput(BaseModel):
    content: str
    action: str
    settings: Dict[str, Any]

class TestOutput(BaseModel):
    id: str
    result: str
    echo: str

# Completely different endpoint name
@isolated_app.post("/test/process", response_model=TestOutput)
async def process_test(data: TestInput):
    """Completely new endpoint with different name"""
    return TestOutput(
        id=str(uuid.uuid4()),
        result="success",
        echo=f"Processed {data.action} on {len(data.content)} chars"
    )

@isolated_app.get("/test/status")
async def test_status():
    return {"status": "running", "auth": "none"}

if __name__ == "__main__":
    print("\n🧪 ISOLATED TEST SERVER")
    print("Using different port (8002) and endpoint names")
    print("\nTest with:")
    print('curl -X POST http://localhost:8002/test/process -H "Content-Type: application/json" -d \'{"content": "test", "action": "process", "settings": {}}\'')
    
    # Run on different port with different app name
    uvicorn.run(isolated_app, host="0.0.0.0", port=8002)