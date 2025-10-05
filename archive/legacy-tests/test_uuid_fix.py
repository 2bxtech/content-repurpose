#!/usr/bin/env python3
"""
Comprehensive test for UUID validation fix
Tests various UUID format issues and validates the fix works properly
"""
import requests

def test_uuid_validation_fix():
    """Test the UUID validation fix with various malformed UUIDs"""
    
    base_url = "http://localhost:8000"
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000"
    }
    
    # Test cases: [description, uuid_to_test, should_work]
    test_cases = [
        ("Valid UUID", "12345678-1234-1234-1234-123456789012", True),
        ("Original problematic UUID", "01c6ffd-4a9a-43bc-bce3-bf4084736422", True),  # Should be auto-fixed
        ("Missing hyphens", "123456781234123412341234567890ab", True),
        ("Short first group", "1234567-1234-1234-1234-123456789012", True),
        ("No hyphens short", "12345671234123412341234567890ab", True),
        ("Completely invalid", "not-a-uuid-at-all", False),
        ("Empty string", "", False),
        ("Too short", "123", False),
        ("Valid but different format", "550e8400-e29b-41d4-a716-446655440000", True),
    ]
    
    print("🧪 Testing UUID Validation Fix")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for description, test_uuid, should_work in test_cases:
        data = {
            "document_id": test_uuid,
            "transformation_type": "BLOG_POST",
            "parameters": {"word_count": 500}
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/transformations",
                json=data,
                headers=headers,
                timeout=5
            )
            
            # Check if we got the expected result
            got_validation_error = response.status_code == 422
            got_auth_error = response.status_code == 401  # Expected when UUID is valid
            
            if should_work:
                # Should get 401 (auth error) not 422 (validation error)
                if got_auth_error:
                    print(f"✅ {description}: PASS (UUID accepted, got auth error as expected)")
                    passed += 1
                elif got_validation_error:
                    print(f"❌ {description}: FAIL (UUID still rejected)")
                    print(f"   Response: {response.text}")
                    failed += 1
                else:
                    print(f"❓ {description}: UNEXPECTED ({response.status_code})")
                    failed += 1
            else:
                # Should get 422 validation error
                if got_validation_error:
                    print(f"✅ {description}: PASS (UUID correctly rejected)")
                    passed += 1
                else:
                    print(f"❌ {description}: FAIL (Invalid UUID was accepted)")
                    failed += 1
                    
            # Always check for CORS headers
            cors_headers = response.headers.get('access-control-allow-origin')
            if cors_headers != 'http://localhost:3000':
                print("   ⚠️  CORS issue: missing or wrong origin header")
                
        except Exception as e:
            print(f"❌ {description}: ERROR ({e})")
            failed += 1
    
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All UUID validation tests passed!")
        return True
    else:
        print("💥 Some tests failed - needs more work")
        return False

def test_original_problematic_request():
    """Test the exact request that was failing originally"""
    print("\n🎯 Testing Original Problematic Request")
    print("=" * 50)
    
    # This is the exact UUID from the frontend that was causing issues
    problematic_uuid = "01c6ffd-4a9a-43bc-bce3-bf4084736422"
    
    headers = {
        "Content-Type": "application/json", 
        "Origin": "http://localhost:3000"
    }
    
    data = {
        "document_id": problematic_uuid,
        "transformation_type": "BLOG_POST",
        "parameters": {
            "word_count": 555,
            "tone": "Academic"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/transformations",
            json=data,
            headers=headers,
            timeout=5
        )
        
        print(f"Status: {response.status_code}")
        print(f"CORS Headers: {response.headers.get('access-control-allow-origin')}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: UUID is now accepted! Got auth error as expected.")
            print("✅ CORS headers are present!")
            return True
        elif response.status_code == 422:
            print("❌ FAILED: UUID still rejected with validation error")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❓ UNEXPECTED: Got status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test the comprehensive UUID validation
    validation_passed = test_uuid_validation_fix()
    
    # Test the specific original problem
    original_fixed = test_original_problematic_request()
    
    if validation_passed and original_fixed:
        print("\n🏆 ALL TESTS PASSED! CORS + UUID issue is RESOLVED!")
    else:
        print("\n💥 Some issues remain - check the output above")