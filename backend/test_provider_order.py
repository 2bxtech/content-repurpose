#!/usr/bin/env python3
"""
Quick test to verify AI provider fallback order
"""
import asyncio
from app.services.ai_providers.manager import AIProviderManager
from app.core.config import settings

async def test_provider_order():
    """Test the provider order and fallback logic"""
    print("=== AI Provider Configuration Test ===")
    
    # Check current configuration
    print(f"AI_PROVIDER setting: {settings.AI_PROVIDER}")
    print(f"ENVIRONMENT setting: {settings.ENVIRONMENT}")
    print(f"OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")
    print(f"CLAUDE_API_KEY present: {bool(settings.CLAUDE_API_KEY)}")
    
    # Initialize manager and check provider configs
    manager = AIProviderManager()
    print(f"\nConfigured providers: {list(manager.provider_configs.keys())}")
    
    for name, config in manager.provider_configs.items():
        provider = manager.providers[name]
        print(f"\n{name}:")
        print(f"  - enabled: {config.enabled}")
        print(f"  - priority: {config.priority}")
        print(f"  - provider_type: {config.provider_type}")
        print(f"  - is_available(): {provider.is_available()}")
    
    # Test provider order
    print("\n=== Provider Order Test ===")
    provider_order = manager._get_provider_order()
    print(f"Provider order: {provider_order}")
    
    # Test a simple generation to see failover
    print("\n=== Testing Text Generation (with failover) ===")
    try:
        response = await manager.generate_text(
            prompt="Test prompt for AI provider",
            max_tokens=50
        )
        print(f"✅ Success! Used provider: {response.provider}")
        print(f"Response: {response.content[:100]}...")
        print(f"Cost: ${response.usage_metrics.total_cost:.6f}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_provider_order())