#!/usr/bin/env python3
"""
Test that mimics the exact frontend request from the browser screenshot
"""
import requests

def test_exact_frontend_request():
    """Recreate the exact request the frontend is making"""
    
    # Extract the exact token from your screenshot
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MTIzYzFkMy1lNjMxLTQ4YzQtOTIyNS01NmQ3NTRmODIyMmQiLCJlbWFpbCI6ImNjQHNoYWtldGhlaGVhdmVucy5jb20iLCJleHAiOjE3NTc3OTk1ODUsImlhdCI6MTc1Nzc5ODY4NSwidHlwZSI6ImFjY2VzcyIsImp0aSI6ImNlZGE4ZjAwLTY0YTQtNDM3OS1iMzQyLWJhMTRjYTNhMjdiZSJ9.6BVu6B-aBhnfFHizbzTOvowDDN8Cxy3-3EXik9g3kbs"
    
    # Exact headers from the frontend request
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd", 
        "Accept-Language": "en-US,en;q=0.5",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DNT": "1",
        "Host": "localhost:8000",
        "Origin": "http://localhost:3000",
        "Priority": "u=0", 
        "Referer": "http://localhost:3000/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors", 
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"
    }
    
    # Sample transformation data (you can adjust based on what you're trying to create)
    data = {
        "document_id": "01c6ffd-4a9a-43bc-bce3-bf4084736422",  # From your URL
        "transformation_type": "BLOG_POST",
        "parameters": {
            "word_count": 555,
            "tone": "Academic"
        }
    }
    
    print("🔍 Testing exact frontend request...")
    print("URL: http://localhost:8000/api/transformations")
    print(f"Data: {data}")
    print(f"Token: {token[:50]}...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/transformations",
            json=data,
            headers=headers,
            timeout=10
        )
        
        print("\n✅ Response received!")
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 500:
            print("\n❌ 500 Error - this matches the frontend issue!")
            print("This suggests the problem might be:")
            print("1. Invalid document_id format")
            print("2. Database connection issues") 
            print("3. Authentication token expired")
            print("4. Backend dependency missing")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_exact_frontend_request()