#!/usr/bin/env python3
"""
Minimal server test to isolate the shutdown issue
"""

import os
import sys

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from fastapi import FastAPI
import uvicorn

# Create minimal app without our complex setup
test_app = FastAPI(title="Test API")


@test_app.get("/test")
async def test_endpoint():
    return {"message": "test successful", "status": "ok"}


@test_app.get("/health")
async def simple_health():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("🔧 Testing minimal FastAPI server...")
    uvicorn.run(test_app, host="127.0.0.1", port=8002, log_level="info")
