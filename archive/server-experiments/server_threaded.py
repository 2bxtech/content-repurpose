#!/usr/bin/env python3
"""
Alternative threaded server approach for Windows Git Bash
Runs uvicorn in a thread to avoid signal issues
"""

import os
import sys
import threading
import time

# Setup paths
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if os.path.exists(backend_dir):
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)


def run_in_thread():
    """Run uvicorn server in a separate thread"""
    import uvicorn
    from main import app

    # Create server without signal handlers
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            loop="asyncio",  # Explicit event loop
            reload=False,
        )
    )

    # Disable install_signal_handlers
    server.install_signal_handlers = lambda: None

    # Run server
    server.run()


def main():
    """Main entry point with thread management"""
    print("🚀 Starting FastAPI server in thread (Git Bash safe mode)")
    print("   Server: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   Press Ctrl+C to stop\n")

    # Start server in daemon thread
    server_thread = threading.Thread(target=run_in_thread, daemon=True)
    server_thread.start()

    # Keep main thread alive
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        sys.exit(0)


if __name__ == "__main__":
    main()
