#!/usr/bin/env python3
"""
Quick Phase 5 WebSocket Validation
Fast validation of core WebSocket functionality without full test suite
"""
import sys
import os
import asyncio
import subprocess
from pathlib import Path

def validate_imports():
    """Quick import validation"""
    print("🔍 Validating WebSocket imports...")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        # Also add the project root to handle absolute imports
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from app.core.websocket_manager import manager, WebSocketMessage
        print("  ✅ WebSocket manager")
        
        from app.core.websocket_auth import get_websocket_user
        print("  ✅ WebSocket auth")
        
        from app.api.routes.websockets import router
        print("  ✅ WebSocket routes")
        
        # Test basic functionality
        test_msg = WebSocketMessage(type="test", data={"test": True})
        stats = manager.get_connection_count()
        
        print("  ✅ Core functionality working")
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking dependencies...")
    
    required_packages = ["websockets", "httpx", "fastapi", "uvicorn"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install " + " ".join(missing))
        return False
    
    return True

def check_services():
    """Check if services are accessible"""
    print("🔌 Checking services...")
    
    try:
        import httpx
        import asyncio
        
        async def check_api():
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/api/health", timeout=2.0)
                    if response.status_code == 200:
                        print("  ✅ FastAPI server")
                        return True
                    else:
                        print(f"  ❌ FastAPI server - status {response.status_code}")
                        return False
            except Exception as e:
                print(f"  ❌ FastAPI server - {str(e)[:50]}...")
                return False
        
        return asyncio.run(check_api())
        
    except Exception as e:
        print(f"  ❌ Service check failed: {e}")
        return False

def main():
    """Quick validation main"""
    print("🚀 Phase 5 WebSocket Quick Validation")
    print("=" * 40)
    
    results = {
        "dependencies": check_dependencies(),
        "imports": validate_imports(),
        "services": check_services()
    }
    
    print("\n📊 Validation Summary:")
    print("=" * 40)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check.title()}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    
    if all_passed:
        print("🎉 Phase 5 WebSocket validation PASSED!")
        print("\nReady for:")
        print("  • WebSocket connections")
        print("  • Real-time transformations")
        print("  • Collaborative features")
        print("\nNext: Run full test suite with:")
        print("  python test_phase5_automated.py")
    else:
        print("⚠️  Phase 5 WebSocket validation FAILED!")
        print("\nRequired actions:")
        if not results["dependencies"]:
            print("  • Install missing dependencies")
        if not results["imports"]:
            print("  • Fix import/module issues")
        if not results["services"]:
            print("  • Start required services (Redis, Celery, FastAPI)")
        
        print("\nSetup instructions:")
        print("  1. pip install websockets httpx")
        print("  2. redis-server")
        print("  3. cd backend && celery -A app.core.celery_app worker --loglevel=info")
        print("  4. cd backend && python main.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())