#!/usr/bin/env python3
"""
Smart server launcher that detects terminal type and adjusts accordingly
Works with Git Bash, PowerShell, CMD, and WSL
"""

import os
import sys


def detect_terminal():
    """Detect the terminal environment"""
    # Check environment variables
    shell = os.environ.get("SHELL", "").lower()
    msystem = os.environ.get("MSYSTEM")
    term = os.environ.get("TERM", "").lower()
    wsl = os.environ.get("WSL_DISTRO_NAME")

    if wsl:
        return "wsl"
    elif msystem or "bash" in shell or "mingw" in term:
        return "gitbash"
    elif "pwsh" in shell or "powershell" in shell:
        return "powershell"
    else:
        return "cmd"


def run_gitbash_mode():
    """Run with Git Bash compatibility"""
    print("🔧 Git Bash detected - using compatibility mode")

    # Setup paths
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        sys.path.insert(0, backend_dir)

    import signal
    import uvicorn
    from main import app

    # Ignore problematic signals
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)

    # Custom shutdown handler
    shutdown_count = 0

    def custom_handler(signum, frame):
        nonlocal shutdown_count
        shutdown_count += 1
        if shutdown_count >= 2:
            print("\n🛑 Force shutdown")
            os._exit(0)
        else:
            print("\n⚠️  Press Ctrl+C again to shutdown")

    signal.signal(signal.SIGINT, custom_handler)

    # Run with modified config
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
        use_colors=False,
        access_log=True,
    )


def run_standard_mode():
    """Run in standard mode for PowerShell/CMD/WSL"""
    print("✅ Standard terminal detected - running normally")

    # Setup paths
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if os.path.exists(backend_dir):
        os.chdir(backend_dir)
        sys.path.insert(0, backend_dir)

    import uvicorn
    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True,  # Can use reload in standard terminals
        access_log=True,
    )


def suggest_alternative():
    """Suggest using PowerShell if Git Bash issues persist"""
    print("\n" + "=" * 60)
    print("💡 TIP: If you continue having issues in Git Bash:")
    print("   1. Open PowerShell: Start → 'powershell'")
    print("   2. Navigate to project: cd C:\\Code\\content-repurpose")
    print("   3. Activate venv: .\\venv\\Scripts\\Activate.ps1")
    print("   4. Run server: python smart_windows_server.py")
    print("=" * 60 + "\n")


def main():
    """Main entry point with terminal detection"""
    terminal = detect_terminal()

    print(f"🖥️  Detected terminal: {terminal}")
    print("🚀 Starting Content Repurposing Tool API...")
    print("   Server: http://127.0.0.1:8000")
    print("   Docs: http://127.0.0.1:8000/docs\n")

    try:
        if terminal == "gitbash":
            run_gitbash_mode()
        else:
            run_standard_mode()
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        if terminal == "gitbash":
            suggest_alternative()
        raise


if __name__ == "__main__":
    main()
