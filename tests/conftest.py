"""
Simplified test configuration that assumes Docker containers are already running.
No complex Docker client dependencies - just HTTP requests.
"""

import pytest
import asyncio
import httpx
from typing import AsyncGenerator

# Test configuration
TEST_API_URL = "http://localhost:8002"
TEST_DB_URL = (
    "postgresql://postgres:test_password@localhost:5434/content_repurpose_test"
)
TEST_REDIS_URL = "redis://localhost:6380"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=False)  # Changed to function scope
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Simple HTTP client for API testing.
    Assumes test API is already running on port 8002.
    
    Note: Tests must explicitly request this fixture to use it.
    Schema validation tests don't request it, so they won't try to connect to API.
    """
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(
        base_url=TEST_API_URL,
        timeout=timeout,
        headers={"Content-Type": "application/json"},
    ) as client:
        # Verify API is accessible
        try:
            response = await client.get("/api/health")
            if response.status_code != 200:
                pytest.fail(f"API health check failed: {response.status_code}")
        except Exception as e:
            pytest.fail(f"Cannot connect to test API at {TEST_API_URL}: {e}")

        yield client


@pytest.fixture(scope="function")  # Changed to function scope
async def authenticated_client(
    api_client: httpx.AsyncClient,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    API client with authentication token.
    """
    # Create test user and get token with unique email for each test
    import uuid
    test_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"testuser_{test_id}",
        "email": f"test_{test_id}@example.com",
        "password": "TestPassword123!",  # Must meet password requirements
    }

    # Register user
    register_resp = await api_client.post("/api/auth/register", json=test_user)
    if register_resp.status_code != 201:
        pytest.fail(f"Failed to register test user: {register_resp.status_code} - {register_resp.text}")

    # Login to get token (using /token endpoint with form data)
    # OAuth2 username field should contain the email
    login_data = {"username": test_user["email"], "password": test_user["password"]}

    # OAuth2 requires form-urlencoded, not JSON
    response = await api_client.post(
        "/api/auth/token", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        try:
            error_detail = response.json()
            pytest.fail(f"Failed to authenticate test user: {response.status_code} - {error_detail}")
        except Exception:
            pytest.fail(f"Failed to authenticate test user: {response.status_code}")

    token_data = response.json()
    access_token = token_data["access_token"]

    # Create new client with auth header
    api_client.headers.update({"Authorization": f"Bearer {access_token}"})

    yield api_client


@pytest.fixture(autouse=False)  # Changed to False - only runs when explicitly needed
async def cleanup_test_data(api_client: httpx.AsyncClient):
    """
    Clean up test data before and after each test.
    This assumes your API has cleanup endpoints or test workspace isolation.
    
    Note: Tests must explicitly request this fixture to enable auto-cleanup.
    """
    # Setup: Clean before test
    yield
    # Teardown: Clean after test (if needed)
    pass


# Test data fixtures
@pytest.fixture
def sample_text():
    """Sample text for transformation tests."""
    return "This is a sample text for testing content transformation features."


@pytest.fixture
def sample_transformation_config():
    """Sample transformation configuration."""
    return {
        "target_platform": "linkedin",
        "content_type": "post",
        "tone": "professional",
        "length": "medium",
    }


# Mock fixtures for AI services
@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a professional LinkedIn post created from your content."
                }
            }
        ]
    }


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [{"text": "This is content transformed using Anthropic's Claude."}]
    }
