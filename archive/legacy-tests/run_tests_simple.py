#!/usr/bin/env python3
"""
Simplified test runner that focuses on running tests against already-running containers.
No complex Docker client dependencies.
"""
import sys
import time
import subprocess
import argparse
from pathlib import Path
import requests

# Configuration
TEST_API_URL = "http://localhost:8002"
PROJECT_ROOT = Path(__file__).parent

def check_service_health(url: str, timeout: int = 30) -> bool:
    """Check if a service is healthy via HTTP."""
    print(f"🔍 Checking service health: {url}")
    
    for attempt in range(timeout):
        try:
            response = requests.get(f"{url}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Service healthy: {url}")
                return True
        except requests.RequestException:
            pass
        
        if attempt < timeout - 1:
            print(f"⏳ Waiting for service... (attempt {attempt + 1}/{timeout})")
            time.sleep(1)
    
    print(f"❌ Service not healthy: {url}")
    return False

def setup_test_environment() -> bool:
    """Setup the test environment using Docker Compose."""
    print("\n🐳 SETTING UP TEST ENVIRONMENT")
    print("-" * 50)
    
    # Check if Docker Compose is available
    try:
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker Compose: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose not available")
        return False
    
    # Clean up existing test containers
    print("🧹 Cleaning up existing test containers...")
    subprocess.run([
        "docker-compose", "-f", "docker-compose.test.yml", 
        "-p", "content-repurpose-test", "down", "-v", "--remove-orphans"
    ], capture_output=True)
    
    # Start test services
    print("🚀 Starting test services...")
    result = subprocess.run([
        "docker-compose", "-f", "docker-compose.test.yml",
        "-p", "content-repurpose-test", "up", "-d", "--build"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Failed to start test services:")
        print(result.stderr)
        return False
    
    print("✅ Test services started successfully")
    
    # Wait for services to be healthy
    print("⏳ Waiting for services to be healthy...")
    if not check_service_health(TEST_API_URL, timeout=60):
        print("❌ Test services are not healthy")
        return False
    
    return True

def run_pytest(args: list) -> int:
    """Run pytest with the given arguments."""
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        "--tb=short",
        "--strict-markers",
        "-v"
    ] + args
    
    print("\n🧪 RUNNING TESTS")
    print("-" * 50)
    print(f"Command: {' '.join(pytest_cmd)}")
    print()
    
    return subprocess.call(pytest_cmd)

def cleanup_test_environment():
    """Clean up the test environment."""
    print("\n🧹 CLEANING UP TEST ENVIRONMENT")
    print("-" * 50)
    
    subprocess.run([
        "docker-compose", "-f", "docker-compose.test.yml",
        "-p", "content-repurpose-test", "down", "-v", "--remove-orphans"
    ], capture_output=True)
    
    print("✅ Test environment cleaned up")

def main():
    parser = argparse.ArgumentParser(description="Content Repurpose Test Runner")
    parser.add_argument("--setup-only", action="store_true", 
                       help="Only set up test environment, don't run tests")
    parser.add_argument("--cleanup-only", action="store_true",
                       help="Only clean up test environment")
    parser.add_argument("--no-setup", action="store_true",
                       help="Skip test environment setup (assume it's already running)")
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Skip cleanup after tests")
    parser.add_argument("--unit", action="store_true",
                       help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true",
                       help="Run end-to-end tests only")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick tests (unit + basic integration)")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("tests", nargs="*", 
                       help="Specific test files or directories")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 CONTENT REPURPOSE - AUTOMATED TEST SUITE")
    print("   Enterprise-Grade Testing Framework")
    print("=" * 80)
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"⏰ Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Handle cleanup-only
    if args.cleanup_only:
        cleanup_test_environment()
        return 0
    
    # Setup test environment unless skipped
    if not args.no_setup:
        if not setup_test_environment():
            return 1
    
    # Handle setup-only
    if args.setup_only:
        print("\n✅ Test environment setup complete!")
        print(f"🌐 API available at: {TEST_API_URL}")
        print(f"📖 API docs at: {TEST_API_URL}/docs")
        return 0
    
    # Build pytest arguments
    pytest_args = []
    
    # Add coverage if requested
    if args.coverage:
        pytest_args.extend([
            "--cov=backend/app",
            "--cov-report=html:reports/coverage",
            "--cov-report=term-missing"
        ])
    
    # Add verbose if requested  
    if args.verbose:
        pytest_args.append("-vv")
    
    # Select test types
    if args.unit:
        pytest_args.append("tests/test_basic.py::TestUtilities")
    elif args.integration:
        pytest_args.extend(["tests/test_basic.py::TestAPIHealth", "tests/test_basic.py::TestAuthentication"])
    elif args.e2e:
        pytest_args.append("tests/test_basic.py::TestContentTransformation")
    elif args.quick:
        pytest_args.extend([
            "tests/test_basic.py::TestUtilities", 
            "tests/test_basic.py::TestAPIHealth"
        ])
    elif args.tests:
        pytest_args.extend(args.tests)
    else:
        pytest_args.append("tests/test_basic.py")
    
    # Run tests
    exit_code = run_pytest(pytest_args)
    
    # Cleanup unless skipped
    if not args.no_cleanup:
        cleanup_test_environment()
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())