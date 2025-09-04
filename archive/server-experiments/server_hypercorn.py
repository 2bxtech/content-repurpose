#!/usr/bin/env python3
"""
Alternative ASGI server test using Hypercorn
Hypercorn might handle Windows signals differently than uvicorn
"""

import os
import sys

# Setup paths
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if os.path.exists(backend_dir):
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)


def main():
    """Test with Hypercorn instead of uvicorn"""
    print("🔄 Installing Hypercorn...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "hypercorn"], check=True)

    print("🚀 Starting with Hypercorn ASGI server...")
    print("   Server: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   Press Ctrl+C to stop\n")

    # Import and run with Hypercorn
    import hypercorn.asyncio
    from hypercorn import Config
    from main import app

    config = Config()
    config.bind = ["127.0.0.1:8000"]
    config.accesslog = "-"

    # Run hypercorn
    import asyncio

    asyncio.run(hypercorn.asyncio.serve(app, config))


if __name__ == "__main__":
    main()
