#!/usr/bin/env python3
"""
Test script to verify workspace isolation and multi-tenancy functionality.
"""

import asyncio
import aiohttp

# Base URL for our API
BASE_URL = "http://127.0.0.1:8000"

async def test_workspace_api():
    """Test workspace API endpoints and multi-tenancy."""
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Health check
        print("🔍 Testing health endpoint...")
        async with session.get(f"{BASE_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Health check passed: {data}")
            else:
                print(f"❌ Health check failed: {response.status}")
                return
        
        # Test 2: Get workspaces (should show default workspace)
        print("\n🔍 Testing workspace listing...")
        async with session.get(f"{BASE_URL}/api/workspaces") as response:
            if response.status == 200:
                workspaces = await response.json()
                print(f"✅ Found {len(workspaces)} workspace(s)")
                for ws in workspaces:
                    print(f"   - {ws['name']} ({ws['slug']}) - {ws['plan']}")
                    
                if workspaces:
                    default_workspace_id = workspaces[0]['id']
                    print(f"   Default workspace ID: {default_workspace_id}")
                else:
                    print("❌ No workspaces found!")
                    return
            else:
                print(f"❌ Workspace listing failed: {response.status}")
                error = await response.text()
                print(f"   Error: {error}")
                return
        
        # Test 3: Create a new workspace
        print("\n🔍 Testing workspace creation...")
        new_workspace_data = {
            "name": "Test Workspace",
            "description": "A test workspace for multi-tenancy validation"
        }
        
        async with session.post(
            f"{BASE_URL}/api/workspaces", 
            json=new_workspace_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 201:
                new_workspace = await response.json()
                print(f"✅ Created new workspace: {new_workspace['name']} ({new_workspace['slug']})")
                test_workspace_id = new_workspace['id']
            else:
                print(f"❌ Workspace creation failed: {response.status}")
                error = await response.text()
                print(f"   Error: {error}")
                return
        
        # Test 4: Get workspace details
        print("\n🔍 Testing workspace details...")
        async with session.get(f"{BASE_URL}/api/workspaces/{test_workspace_id}") as response:
            if response.status == 200:
                workspace_details = await response.json()
                print(f"✅ Retrieved workspace details: {workspace_details['name']}")
                print(f"   Created: {workspace_details['created_at']}")
                print(f"   Plan: {workspace_details['plan']}")
                print(f"   Settings: {workspace_details.get('settings', {})}")
            else:
                print(f"❌ Workspace details failed: {response.status}")
                error = await response.text()
                print(f"   Error: {error}")
        
        # Test 5: List all workspaces again (should now show 2)
        print("\n🔍 Testing updated workspace listing...")
        async with session.get(f"{BASE_URL}/api/workspaces") as response:
            if response.status == 200:
                workspaces = await response.json()
                print(f"✅ Now found {len(workspaces)} workspace(s)")
                for ws in workspaces:
                    print(f"   - {ws['name']} ({ws['slug']}) - {ws['plan']}")
            else:
                print(f"❌ Updated workspace listing failed: {response.status}")
        
        print("\n🎉 Basic workspace API testing completed!")
        print("\n📝 Next steps:")
        print("   1. Test user registration with workspace assignment")
        print("   2. Test document upload with workspace isolation")
        print("   3. Test RLS policies by switching workspace context")
        print("   4. Verify data isolation between workspaces")

if __name__ == "__main__":
    print("🚀 Starting multi-tenant workspace isolation tests...")
    print("=" * 60)
    
    try:
        asyncio.run(test_workspace_api())
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()