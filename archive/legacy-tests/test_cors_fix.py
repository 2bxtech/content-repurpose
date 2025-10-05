#!/usr/bin/env python3
"""
Quick unit test to debug the CORS + transformation creation issue
"""
import requests

def test_cors_and_transformation():
    """Test CORS headers and transformation creation"""
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("🔍 Test 1: Health check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: OPTIONS preflight request
    print("\n🔍 Test 2: CORS preflight (OPTIONS)...")
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization"
    }
    try:
        response = requests.options(f"{base_url}/api/transformations", headers=headers)
        print(f"✅ OPTIONS: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ OPTIONS failed: {e}")
    
    # Test 3: POST without auth (should get 401 with CORS headers)
    print("\n🔍 Test 3: POST without auth...")
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3000"
    }
    data = {
        "document_id": "12345678-1234-1234-1234-123456789012",
        "transformation_type": "BLOG_POST", 
        "parameters": {"word_count": 500}
    }
    try:
        response = requests.post(f"{base_url}/api/transformations", 
                               json=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ POST failed: {e}")
    
    # Test 4: POST with invalid UUID (should get 422 with CORS headers)
    print("\n🔍 Test 4: POST with invalid UUID...")
    data["document_id"] = "invalid-uuid"
    try:
        response = requests.post(f"{base_url}/api/transformations", 
                               json=data, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ POST with invalid UUID failed: {e}")
    
    # Test 5: Check if backend is handling exceptions properly
    print("\n🔍 Test 5: Test exception handling...")
    try:
        # Send malformed JSON to trigger an exception
        response = requests.post(f"{base_url}/api/transformations", 
                               data="invalid-json", 
                               headers={"Content-Type": "application/json",
                                      "Origin": "http://localhost:3000"})
        print(f"Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Exception test failed: {e}")

if __name__ == "__main__":
    test_cors_and_transformation()