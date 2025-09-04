#!/usr/bin/env python3
"""
Quick health check for the running server - Windows bash compatible
"""

import requests
import sys


def test_server():
    """Test the server health endpoint"""
    try:
        print("🔍 Testing server health...")
        response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print("✅ Server is healthy!")
            print(f"   Status: {data['status']}")
            print(f"   Environment: {data['environment']}")
            print(f"   Version: {data['version']}")
            print(f"   Timestamp: {data['timestamp']}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on http://127.0.0.1:8000?")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False


if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
