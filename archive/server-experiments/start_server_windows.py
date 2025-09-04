#!/usr/bin/env python3
"""
Windows-compatible server startup script for bash terminal
"""

import os
import sys

# Change to backend directory and add to path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("🚀 Starting Content Repurposing Tool API...")
    print("   Server will run on: http://127.0.0.1:8000")
    print("   Use http://127.0.0.1:8000/docs for API documentation")
    print("   Press Ctrl+C to stop")

    # Import and run
    import uvicorn
    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,  # Disable reload to avoid signal issues
    )
