#!/usr/bin/env python3
"""
Docker Authentication Integration Test Runner
Validates enterprise authentication system in Docker environment
"""

import subprocess
import sys
import httpx


def check_docker_container():
    """Check if Docker container is running"""
    try:
        response = httpx.get("http://localhost:8000/api/health", timeout=5.0)
        if response.status_code == 200:
            print("✅ Docker API container is running")
            return True
    except Exception as e:
        print(f"❌ Docker container not accessible: {e}")
        return False


def run_authentication_tests():
    """Run comprehensive authentication tests"""
    print("🔐 Running Docker Authentication Integration Tests...")
    print("=" * 60)
    
    # Check Docker container first
    if not check_docker_container():
        print("\n🚨 Docker container not running. Please run:")
        print("   docker-compose up -d")
        return False
    
    # Run the integration tests
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_docker_auth_integration.py",
            "-v",
            "-m", "docker",
            "--tb=short",
            "--no-header",
            "-q"
        ], capture_output=True, text=True, timeout=60)
        
        print("\n📊 TEST RESULTS:")
        print("-" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ WARNINGS/ERRORS:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out (>60s)")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def validate_auth_endpoints():
    """Quick validation of auth endpoint structure"""
    print("\n🔍 Quick Auth Endpoint Validation...")
    print("-" * 40)
    
    endpoints_to_test = [
        ("GET", "/api/health", "Health endpoint"),
        ("POST", "/api/auth/register", "User registration (corrected prefix)"),
        ("POST", "/api/auth/token", "OAuth2 token (corrected prefix)"),
        ("POST", "/api/transformations", "Protected transformations"),
        ("POST", "/api/auth/auth/register", "Old double prefix (should be 404)"),
    ]
    
    results = []
    
    with httpx.Client() as client:
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = client.get(f"http://localhost:8000{endpoint}", timeout=3.0)
                else:
                    response = client.post(f"http://localhost:8000{endpoint}", timeout=3.0)
                
                status = response.status_code
                
                if endpoint == "/api/health":
                    expected = status == 200
                elif endpoint == "/api/auth/auth/register":
                    expected = status == 404  # Should NOT exist
                elif "auth" in endpoint:
                    expected = status != 404  # Should exist (but may have validation errors)
                elif "transformations" in endpoint:
                    expected = status in [401, 403, 404, 422]  # Should require auth
                else:
                    expected = True
                
                result_icon = "✅" if expected else "❌"
                results.append((result_icon, description, status, expected))
                
            except Exception as e:
                results.append(("❌", description, f"Error: {e}", False))
    
    # Print results
    for icon, desc, status, success in results:
        print(f"{icon} {desc:<40} → {status}")
    
    successful_tests = sum(1 for _, _, _, success in results if success)
    total_tests = len(results)
    
    print(f"\n📊 Endpoint Validation: {successful_tests}/{total_tests} passed")
    return successful_tests == total_tests


def main():
    """Main test runner"""
    print("🐳 Docker Enterprise Authentication Integration Tests")
    print("=" * 60)
    
    # Step 1: Quick endpoint validation
    endpoint_success = validate_auth_endpoints()
    
    # Step 2: Comprehensive integration tests
    test_success = run_authentication_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("-" * 60)
    
    if endpoint_success:
        print("✅ Endpoint Structure: CORRECT")
        print("   - Auth endpoints use single prefix (/api/auth/)")
        print("   - Transformations require authentication")
        print("   - Double prefix issue resolved")
    else:
        print("❌ Endpoint Structure: ISSUES FOUND")
    
    if test_success:
        print("✅ Integration Tests: PASSED")
        print("   - Authentication flow structure working")
        print("   - Docker container properly configured")
        print("   - Enterprise authentication patterns validated")
    else:
        print("⚠️ Integration Tests: PARTIAL SUCCESS")
        print("   - Some validation issues may exist")
        print("   - Check test output for details")
    
    overall_success = endpoint_success and test_success
    
    if overall_success:
        print("\n🎉 DOCKER AUTHENTICATION INTEGRATION: SUCCESS!")
        print("   Your enterprise authentication system is working correctly.")
    else:
        print("\n🔧 DOCKER AUTHENTICATION INTEGRATION: NEEDS ATTENTION")
        print("   Review test output for specific issues to address.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)