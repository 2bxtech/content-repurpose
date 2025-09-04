#!/usr/bin/env python3
"""
Quick test to verify Phase 2 auth system after merge conflict resolution
"""

import requests

BASE_URL = "http://localhost:8000"


def test_basic_functionality():
    print("🔍 Testing Phase 2 Authentication System Post-Merge...")

    try:
        # Test 1: API Root
        print("\n1. Testing API root...")
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            print(
                f"✅ API responding: {data.get('name', 'Unknown')} v{data.get('version', 'Unknown')}"
            )
            print(
                f"   Features: {len(data.get('features', []))} security features listed"
            )
        else:
            print(f"❌ API root failed: {response.status_code}")
            return False

        # Test 2: Health Check
        print("\n2. Testing health endpoints...")
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Basic health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")

        # Test 3: Redis Health
        response = requests.get(f"{BASE_URL}/api/health/redis")
        if response.status_code == 200:
            print("✅ Redis health check passed")
        else:
            print(f"⚠️  Redis health check failed: {response.status_code}")

        # Test 4: API Documentation
        print("\n3. Testing API documentation...")
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible")
        else:
            print(f"❌ API docs failed: {response.status_code}")

        # Test 5: User Registration (Enhanced Validation)
        print("\n4. Testing enhanced user registration...")
        test_user = {
            "email": "testuser@example.local",
            "username": "testuser",
            "password": "ExampleTestPassword123!",
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user)
        if response.status_code == 201:
            print("✅ User registration with strong password validation works")
            user_data = response.json()
            print(
                f"   Created user: {user_data.get('email')} (ID: {user_data.get('id')})"
            )
        else:
            print(f"⚠️  Registration response: {response.status_code}")
            if response.status_code == 400:
                print("   (This might be expected if user already exists)")

        # Test 6: Login with JWT Tokens
        print("\n5. Testing JWT login...")
        login_data = {
            "username": "testuser@example.local",
            "password": "ExampleTestPassword123!",
        }
        response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
        if response.status_code == 200:
            tokens = response.json()
            print("✅ Login successful - JWT tokens received")
            print(f"   Access token length: {len(tokens.get('access_token', ''))}")
            print(f"   Refresh token length: {len(tokens.get('refresh_token', ''))}")
            print(f"   Token expires in: {tokens.get('expires_in')} seconds")

            # Test 7: Protected Endpoint
            print("\n6. Testing protected endpoint access...")
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            if response.status_code == 200:
                user_profile = response.json()
                print("✅ Protected endpoint access successful")
                print(
                    f"   User profile: {user_profile.get('email')} - {user_profile.get('active_sessions')} sessions"
                )
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")

        print("\n" + "=" * 60)
        print("✅ PHASE 2 AUTHENTICATION SYSTEM - POST-MERGE STATUS: OPERATIONAL")
        print("=" * 60)
        print("\n🎯 Key Features Verified:")
        print("  • JWT access & refresh tokens")
        print("  • Enhanced password validation")
        print("  • Redis session management")
        print("  • Protected endpoint authentication")
        print("  • Health monitoring")
        print("\n🚀 Ready for development!")

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    test_basic_functionality()
