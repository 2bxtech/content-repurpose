#!/usr/bin/env python3
"""
Simple test runner that assumes Docker test environment is already running
Use this when you have already started the test containers via:
python run_tests.py --setup-only
"""

import subprocess
import sys
import requests
import time
from pathlib import Path


def check_test_environment():
    """Check if test environment is running and accessible"""
    print("🔍 Checking test environment...")
    
    endpoints = [
        ("API", "http://localhost:8002/api/health"),
        ("Detailed Health", "http://localhost:8002/api/health/detailed")
    ]
    
    all_healthy = True
    for service_name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: Healthy")
            else:
                print(f"❌ {service_name}: Status {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {service_name}: {str(e)}")
            all_healthy = False
    
    return all_healthy


def run_simple_tests():
    """Run tests against running environment"""
    print("\n🧪 Running pytest...")
    
    # Build pytest command
    cmd = [
        "python", "-m", "pytest",
        "tests/test_simple.py",
        "-v",
        "--tb=short"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Run tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print("\n✅ Tests passed!")
    else:
        print(f"\n❌ Tests failed with code {result.returncode}")
    
    return result.returncode


def main():
    """Main function"""
    print("🚀 SIMPLE TEST RUNNER")
    print("=" * 50)
    
    if not check_test_environment():
        print("\n❌ Test environment not ready!")
        print("💡 Start test environment first with:")
        print("   python run_tests.py --setup-only")
        return 1
    
    return run_simple_tests()


if __name__ == "__main__":
    sys.exit(main())