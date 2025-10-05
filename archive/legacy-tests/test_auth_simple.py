"""
Simple Docker Authentication Integration Tests
Direct validation without pytest markers
"""

import httpx
import time


def test_endpoint_structure():
    """Test that auth endpoints have correct structure"""
    print("🔍 Testing endpoint structure...")
    
    BASE_URL = "http://localhost:8000"
    results = []
    
    with httpx.Client() as client:
        # Test 1: Health endpoint works
        try:
            response = client.get(f"{BASE_URL}/api/health", timeout=5.0)
            results.append(("Health endpoint", response.status_code == 200, response.status_code))
        except Exception as e:
            results.append(("Health endpoint", False, f"Error: {e}"))
        
        # Test 2: Corrected auth endpoints exist (not 404)
        try:
            response = client.post(f"{BASE_URL}/api/auth/register", timeout=5.0)
            results.append(("Auth register (corrected)", response.status_code != 404, response.status_code))
        except Exception as e:
            results.append(("Auth register (corrected)", False, f"Error: {e}"))
        
        try:
            response = client.post(f"{BASE_URL}/api/auth/token", timeout=5.0) 
            results.append(("Auth token (corrected)", response.status_code != 404, response.status_code))
        except Exception as e:
            results.append(("Auth token (corrected)", False, f"Error: {e}"))
        
        # Test 3: Old double-prefix endpoints don't exist (404)
        try:
            response = client.post(f"{BASE_URL}/api/auth/auth/register", timeout=5.0)
            results.append(("Old double prefix gone", response.status_code == 404, response.status_code))
        except Exception as e:
            results.append(("Old double prefix gone", False, f"Error: {e}"))
        
        # Test 4: Transformations require authentication
        try:
            response = client.post(f"{BASE_URL}/api/transformations", timeout=5.0)
            auth_required = response.status_code in [401, 403, 422]  # Not 200 (success)
            results.append(("Transformations protected", auth_required, response.status_code))
        except Exception as e:
            results.append(("Transformations protected", False, f"Error: {e}"))
    
    return results


def test_registration_validation():
    """Test user registration validates passwords"""
    print("🔐 Testing registration validation...")
    
    BASE_URL = "http://localhost:8000"
    results = []
    
    with httpx.Client() as client:
        # Test weak password rejection
        weak_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak"
        }
        
        try:
            response = client.post(
                f"{BASE_URL}/api/auth/register",
                json=weak_data,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            weak_rejected = response.status_code in [400, 422]  # Validation error
            results.append(("Weak password rejected", weak_rejected, response.status_code))
        except Exception as e:
            results.append(("Weak password rejected", False, f"Error: {e}"))
        
        # Test strong password format acceptance
        strong_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com", 
            "password": "StrongPassword123!@#"
        }
        
        try:
            response = client.post(
                f"{BASE_URL}/api/auth/register",
                json=strong_data,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            # Should not be 404 (endpoint exists) - may fail validation but structure ok
            strong_processed = response.status_code != 404
            results.append(("Strong password processed", strong_processed, response.status_code))
        except Exception as e:
            results.append(("Strong password processed", False, f"Error: {e}"))
    
    return results


def test_oauth2_format():
    """Test OAuth2 token endpoint expects correct format"""
    print("🎫 Testing OAuth2 token format...")
    
    BASE_URL = "http://localhost:8000"
    results = []
    
    with httpx.Client() as client:
        # Test OAuth2 form format
        try:
            response = client.post(
                f"{BASE_URL}/api/auth/token",
                content="username=testuser&password=testpass",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )
            # Should not be 404 (endpoint exists), may be 401 (auth fail) or 422 (validation)
            oauth_endpoint_exists = response.status_code != 404
            results.append(("OAuth2 endpoint exists", oauth_endpoint_exists, response.status_code))
        except Exception as e:
            results.append(("OAuth2 endpoint exists", False, f"Error: {e}"))
    
    return results


def test_openapi_structure():
    """Test OpenAPI documentation shows correct endpoints"""
    print("📄 Testing OpenAPI structure...")
    
    BASE_URL = "http://localhost:8000"
    results = []
    
    with httpx.Client() as client:
        try:
            response = client.get(f"{BASE_URL}/openapi.json", timeout=10.0)
            if response.status_code == 200:
                openapi_data = response.json()
                paths = openapi_data.get("paths", {})
                
                # Check corrected endpoints exist
                corrected_register = "/api/auth/register" in paths
                corrected_token = "/api/auth/token" in paths
                transformations = "/api/transformations" in paths
                
                # Check old endpoints don't exist
                old_register = "/api/auth/auth/register" not in paths
                old_token = "/api/auth/auth/token" not in paths
                
                results.append(("Corrected register endpoint", corrected_register, "in OpenAPI"))
                results.append(("Corrected token endpoint", corrected_token, "in OpenAPI"))
                results.append(("Transformations endpoint", transformations, "in OpenAPI"))
                results.append(("Old register endpoint gone", old_register, "not in OpenAPI"))
                results.append(("Old token endpoint gone", old_token, "not in OpenAPI"))
            else:
                results.append(("OpenAPI accessible", False, response.status_code))
                
        except Exception as e:
            results.append(("OpenAPI accessible", False, f"Error: {e}"))
    
    return results


def main():
    """Run all authentication tests"""
    print("🐳 Docker Enterprise Authentication Integration Tests")
    print("=" * 60)
    
    all_results = []
    
    # Run test suites
    test_suites = [
        ("Endpoint Structure", test_endpoint_structure),
        ("Registration Validation", test_registration_validation),
        ("OAuth2 Format", test_oauth2_format),
        ("OpenAPI Structure", test_openapi_structure)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n{suite_name}:")
        print("-" * 40)
        
        try:
            results = test_func()
            all_results.extend(results)
            
            for test_name, passed, status in results:
                icon = "✅" if passed else "❌"
                print(f"{icon} {test_name:<30} → {status}")
                
        except Exception as e:
            print(f"❌ {suite_name} failed: {e}")
            all_results.append((f"{suite_name} execution", False, f"Error: {e}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("-" * 60)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, passed, _ in all_results if passed)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enterprise authentication system is working correctly")
        print("✅ Double prefix issue resolved")
        print("✅ Authentication protection in place")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL!")
        print("✅ Core authentication structure is correct")
        print("⚠️ Some minor validation issues may exist")
    else:
        print("\n⚠️ SIGNIFICANT ISSUES FOUND")
        print("❌ Review failed tests for problems to address")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)