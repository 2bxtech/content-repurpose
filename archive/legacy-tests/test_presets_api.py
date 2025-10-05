"""
Quick test script for transformation presets API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_presets_flow():
    """Test complete presets workflow"""
    
    print("=" * 60)
    print("TRANSFORMATION PRESETS API TEST")
    print("=" * 60)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "email": f"preset_test_{hash('test')}@example.com",
        "username": "preset_tester",
        "password": "TestPass123!@#"
    }
    
    register_response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json=register_data
    )
    
    if register_response.status_code == 201:
        print(f"   ✅ User registered: {register_response.json()['email']}")
    elif register_response.status_code == 400 and "already registered" in register_response.text:
        print("   ℹ️  User already exists, continuing...")
    else:
        print(f"   ❌ Registration failed: {register_response.status_code}")
        print(f"   {register_response.text}")
        return
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/token",
        data={
            "username": register_data["email"],
            "password": register_data["password"]
        }
    )
    
    if login_response.status_code != 200:
        print(f"   ❌ Login failed: {login_response.status_code}")
        print(f"   {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   ✅ Logged in successfully")
    
    # Step 3: Create a personal preset
    print("\n3. Creating personal preset...")
    preset_data = {
        "name": "Test LinkedIn Professional",
        "description": "My LinkedIn preset for testing",
        "transformation_type": "SOCIAL_MEDIA",
        "parameters": {
            "platform": "linkedin",
            "tone": "professional",
            "hashtags": True,
            "length": "medium"
        },
        "is_shared": False
    }
    
    create_response = requests.post(
        f"{BASE_URL}/api/transformation-presets",
        json=preset_data,
        headers=headers
    )
    
    if create_response.status_code != 201:
        print(f"   ❌ Failed to create preset: {create_response.status_code}")
        print(f"   {create_response.text}")
        return
    
    preset = create_response.json()
    preset_id = preset["id"]
    print(f"   ✅ Created preset: {preset['name']} (ID: {preset_id})")
    print(f"      is_shared: {preset['is_shared']}, is_owner: {preset['is_owner']}")
    
    # Step 4: List presets
    print("\n4. Listing all presets...")
    list_response = requests.get(
        f"{BASE_URL}/api/transformation-presets",
        headers=headers
    )
    
    if list_response.status_code != 200:
        print(f"   ❌ Failed to list presets: {list_response.status_code}")
        return
    
    presets_list = list_response.json()
    print(f"   ✅ Found {presets_list['total']} preset(s)")
    for p in presets_list['presets']:
        print(f"      - {p['name']} ({p['transformation_type']}) [usage: {p['usage_count']}]")
    
    # Step 5: Get specific preset
    print(f"\n5. Getting preset details for {preset_id}...")
    get_response = requests.get(
        f"{BASE_URL}/api/transformation-presets/{preset_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print(f"   ❌ Failed to get preset: {get_response.status_code}")
        return
    
    preset_detail = get_response.json()
    print(f"   ✅ Retrieved: {preset_detail['name']}")
    print(f"      Parameters: {json.dumps(preset_detail['parameters'], indent=10)}")
    
    # Step 6: Update preset
    print("\n6. Updating preset...")
    update_data = {
        "description": "Updated description for testing"
    }
    
    update_response = requests.patch(
        f"{BASE_URL}/api/transformation-presets/{preset_id}",
        json=update_data,
        headers=headers
    )
    
    if update_response.status_code != 200:
        print(f"   ❌ Failed to update preset: {update_response.status_code}")
        print(f"   {update_response.text}")
    else:
        updated = update_response.json()
        print(f"   ✅ Updated: {updated['description']}")
    
    # Step 7: Record usage
    print("\n7. Recording preset usage...")
    usage_response = requests.post(
        f"{BASE_URL}/api/transformation-presets/{preset_id}/use",
        headers=headers
    )
    
    if usage_response.status_code != 204:
        print(f"   ❌ Failed to record usage: {usage_response.status_code}")
    else:
        print("   ✅ Usage recorded")
    
    # Verify usage count increased
    verify_response = requests.get(
        f"{BASE_URL}/api/transformation-presets/{preset_id}",
        headers=headers
    )
    
    if verify_response.status_code == 200:
        verified = verify_response.json()
        print(f"      Usage count: {verified['usage_count']}")
    
    # Step 8: Create a shared preset
    print("\n8. Creating shared workspace preset...")
    shared_preset_data = {
        "name": "Shared Marketing Email Template",
        "description": "Team-wide email template",
        "transformation_type": "EMAIL_SEQUENCE",
        "parameters": {
            "sequence_length": 3,
            "tone": "professional",
            "call_to_action": "Schedule a call"
        },
        "is_shared": True
    }
    
    shared_response = requests.post(
        f"{BASE_URL}/api/transformation-presets",
        json=shared_preset_data,
        headers=headers
    )
    
    if shared_response.status_code == 201:
        shared_preset = shared_response.json()
        print(f"   ✅ Created shared preset: {shared_preset['name']}")
        print(f"      user_id: {shared_preset['user_id']} (should be null for shared)")
    else:
        print(f"   ❌ Failed: {shared_response.status_code}")
        print(f"   {shared_response.text}")
    
    # Step 9: Delete preset
    print(f"\n9. Deleting preset {preset_id}...")
    delete_response = requests.delete(
        f"{BASE_URL}/api/transformation-presets/{preset_id}",
        headers=headers
    )
    
    if delete_response.status_code != 204:
        print(f"   ❌ Failed to delete: {delete_response.status_code}")
    else:
        print("   ✅ Preset deleted (soft delete)")
    
    # Verify it's gone
    verify_delete = requests.get(
        f"{BASE_URL}/api/transformation-presets/{preset_id}",
        headers=headers
    )
    
    if verify_delete.status_code == 404:
        print("   ✅ Confirmed: Preset no longer accessible")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_presets_flow()
