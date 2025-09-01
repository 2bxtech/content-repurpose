#!/usr/bin/env python3
"""
Phase 5 WebSocket testing script.
Tests real-time features and WebSocket connectivity.
"""
import asyncio
import websockets
import json
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_connection():
    """Test basic WebSocket connection and messaging"""
    
    # Test configuration
    WS_URL = "ws://localhost:8000/api/ws"
    TEST_TOKEN = "test_jwt_token"  # You'll need to replace with a real token
    TEST_WORKSPACE = "test-workspace-id"  # You'll need to replace with real workspace ID
    
    print("🔌 Phase 5 WebSocket Testing")
    print("=" * 50)
    
    try:
        # Build WebSocket URL with authentication
        ws_url_with_auth = f"{WS_URL}?token={TEST_TOKEN}&workspace_id={TEST_WORKSPACE}"
        
        print(f"📡 Connecting to: {ws_url_with_auth}")
        
        async with websockets.connect(ws_url_with_auth) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Test 1: Wait for welcome message
            print("\n🔸 Test 1: Waiting for welcome message...")
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                print(f"✅ Received welcome: {welcome_data['type']}")
                print(f"   Data: {welcome_data['data']}")
            except asyncio.TimeoutError:
                print("❌ No welcome message received")
            
            # Test 2: Send ping message
            print("\n🔸 Test 2: Sending ping...")
            ping_message = {
                "type": "ping",
                "data": {"timestamp": datetime.utcnow().isoformat()}
            }
            await websocket.send(json.dumps(ping_message))
            
            # Wait for pong response
            try:
                pong_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_msg)
                if pong_data['type'] == 'pong':
                    print("✅ Received pong response")
                else:
                    print(f"📬 Received other message: {pong_data['type']}")
            except asyncio.TimeoutError:
                print("❌ No pong response received")
            
            # Test 3: Request workspace presence
            print("\n🔸 Test 3: Requesting workspace presence...")
            presence_request = {
                "type": "get_workspace_presence",
                "data": {}
            }
            await websocket.send(json.dumps(presence_request))
            
            # Wait for presence response
            try:
                presence_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                presence_data = json.loads(presence_msg)
                if presence_data['type'] == 'workspace_presence':
                    print("✅ Received workspace presence")
                    print(f"   Users online: {len(presence_data['data'].get('users', []))}")
                else:
                    print(f"📬 Received other message: {presence_data['type']}")
            except asyncio.TimeoutError:
                print("❌ No presence response received")
            
            # Test 4: Send workspace message
            print("\n🔸 Test 4: Sending workspace message...")
            workspace_message = {
                "type": "workspace_message",
                "data": {
                    "message": "Hello from Phase 5 test!",
                    "test_timestamp": datetime.utcnow().isoformat()
                }
            }
            await websocket.send(json.dumps(workspace_message))
            print("✅ Workspace message sent")
            
            # Test 5: Listen for any additional messages
            print("\n🔸 Test 5: Listening for additional messages (5 seconds)...")
            try:
                for i in range(5):
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    msg_data = json.loads(msg)
                    print(f"📬 Received: {msg_data['type']} - {msg_data.get('data', {})}")
            except asyncio.TimeoutError:
                print("⏱️  No more messages received")
            
            print("\n✅ WebSocket tests completed successfully!")
            
    except websockets.exceptions.ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Make sure the server is running:")
        print("   cd backend && python main.py")
        
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Invalid WebSocket URI: {e}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def test_websocket_broadcast_api():
    """Test the HTTP broadcast API"""
    import httpx
    
    print("\n📡 Testing WebSocket Broadcast API")
    print("=" * 40)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test broadcast message
            broadcast_data = {
                "type": "test_broadcast",
                "data": {
                    "message": "Test broadcast from API",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "target": "broadcast"
            }
            
            response = await client.post(
                "http://localhost:8000/api/ws/broadcast",
                json=broadcast_data,
                headers={"Authorization": "Bearer test_token"}  # Replace with real token
            )
            
            if response.status_code == 200:
                print("✅ Broadcast API call successful")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Broadcast API failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Broadcast API test error: {e}")


async def test_websocket_stats():
    """Test WebSocket statistics endpoint"""
    import httpx
    
    print("\n📊 Testing WebSocket Stats API")
    print("=" * 35)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/ws/stats")
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ WebSocket stats retrieved")
                print(f"   Total connections: {stats['websocket_stats']['total_connections']}")
                print(f"   Unique users: {stats['websocket_stats']['unique_users']}")
                print(f"   Active workspaces: {stats['websocket_stats']['active_workspaces']}")
            else:
                print(f"❌ Stats API failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Stats API test error: {e}")


def print_setup_instructions():
    """Print setup instructions for testing"""
    print("\n🚀 Phase 5 WebSocket Setup Instructions")
    print("=" * 50)
    print("1. Start Redis server:")
    print("   redis-server")
    print()
    print("2. Start Celery worker:")
    print("   cd backend")
    print("   celery -A app.core.celery_app worker --loglevel=info")
    print()
    print("3. Start FastAPI server:")
    print("   cd backend")
    print("   python main.py")
    print()
    print("4. Get a JWT token:")
    print("   - Login via /api/auth/login")
    print("   - Use the access_token for WebSocket authentication")
    print()
    print("5. Update this script with real token and workspace ID")
    print()
    print("6. Run the tests:")
    print("   python test_phase5_websockets.py")


async def main():
    """Main testing function"""
    print_setup_instructions()
    
    # Ask user if they want to proceed with tests
    response = input("\nDo you want to run the WebSocket tests now? (y/n): ")
    if response.lower() != 'y':
        print("Skipping tests. Make sure to update the tokens first!")
        return
    
    # Run all tests
    await test_websocket_connection()
    await test_websocket_broadcast_api()
    await test_websocket_stats()
    
    print("\n🎉 Phase 5 WebSocket testing complete!")
    print("\nNext steps:")
    print("- Update frontend to use WebSocket service")
    print("- Test real transformation progress updates")
    print("- Test collaborative features")


if __name__ == "__main__":
    asyncio.run(main())