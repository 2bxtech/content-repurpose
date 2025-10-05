import requests

# Test if backend is running
try:
    response = requests.get("http://localhost:8000/")
    print("✅ Backend is running:", response.json())
except Exception as e:
    print("❌ Backend is not running:", e)
    print("Please start the backend with: python -m uvicorn main:app --reload")
    exit(1)

# Test CORS headers
response = requests.options(
    "http://localhost:8000/api/transformations",
    headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
)
print("\n✅ CORS Headers present:" if "access-control-allow-origin" in response.headers else "❌ CORS Headers missing")
for header, value in response.headers.items():
    if "access-control" in header.lower():
        print(f"  {header}: {value}")

# Test the transformation endpoint
test_data = {
    "sourceDocument": "Test document content",
    "transformationType": "Blog Post",
    "parameters": {
        "wordCount": 555,
        "tone": "Professional"
    }
}

response = requests.post(
    "http://localhost:8000/api/transformations",
    json=test_data,
    headers={"Origin": "http://localhost:3000"}
)

if response.status_code == 200:
    print("\n✅ Transformation endpoint working:", response.json())
else:
    print(f"\n❌ Transformation endpoint failed with status {response.status_code}")
    print("Response:", response.text)