#!/usr/bin/env python3
"""
Test script to make HTTP requests to our server
"""

import asyncio
import httpx


async def test_server():
    """Test the server with proper HTTP client"""
    print("Testing server with HTTP client...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8001/api/health", timeout=5.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_server())
