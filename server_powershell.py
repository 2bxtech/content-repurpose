#!/usr/bin/env python3
"""
PowerShell-optimized server launcher
Avoids Git Bash signal handling issues entirely
"""
import os
import sys

def main():
    """Main entry point for PowerShell/CMD"""
    # Setup paths
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        sys.path.insert(0, backend_dir)
    
    print("🚀 Starting Content Repurposing Tool API (PowerShell Mode)")
    print("   Server: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   Health: http://127.0.0.1:8000/api/health")
    print("   Press Ctrl+C to stop\n")
    
    # Import and run with standard uvicorn
    import uvicorn
    from main import app
    
    # Run with reload enabled for development
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,  # Disable reload to avoid file watching issues
        access_log=True
    )

if __name__ == "__main__":
    main()