#!/usr/bin/env python3
"""
Windows Git Bash compatible FastAPI server
Disables signal handlers that cause shutdown issues
"""

import os
import sys
import signal

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if os.path.exists(backend_dir):
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)


def run_server():
    """Run server with Git Bash compatibility"""

    # SOLUTION 1: Disable signal handlers in Git Bash
    if os.environ.get("MSYSTEM") or "bash" in os.environ.get("SHELL", "").lower():
        print("🔧 Detected Git Bash environment - disabling signal handlers")
        # Override signal handlers to prevent shutdown
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    import uvicorn
    from main import app

    print("🚀 Starting Content Repurposing Tool API (Git Bash Mode)...")
    print("   Server: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs")
    print("   Press Ctrl+C multiple times to stop")

    # SOLUTION 2: Use uvicorn Config object to control signals
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
        # Disable uvicorn's signal handlers
        use_colors=False,  # Helps with Git Bash compatibility
        access_log=True,
    )

    server = uvicorn.Server(config)

    # SOLUTION 3: Custom signal handling for graceful shutdown
    shutdown = False

    def handle_exit(signum, frame):
        nonlocal shutdown
        if not shutdown:
            print("\n⚠️  Shutdown requested - press Ctrl+C again to force")
            shutdown = True
        else:
            print("\n🛑 Force shutdown")
            sys.exit(0)

    # Re-enable Ctrl+C but with custom handler
    signal.signal(signal.SIGINT, handle_exit)

    # Run server (blocking)
    server.run()


if __name__ == "__main__":
    run_server()
