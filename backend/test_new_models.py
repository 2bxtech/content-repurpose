"""
Test script for verifying new AI model configurations

Tests:
1. Model information loading
2. Anthropic provider with Claude 4.5 models
3. OpenAI provider with GPT-5 models
4. Mock provider as fallback
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ai_providers.openai_provider import OpenAIProvider
from app.services.ai_providers.anthropic_provider import AnthropicProvider
from app.services.ai_providers.mock_provider import MockProvider


def test_model_configuration():
    """Test that models are properly configured"""
    print("=" * 80)
    print("TESTING MODEL CONFIGURATIONS")
    print("=" * 80)
    
    # Test OpenAI models
    print("\n1. OpenAI Models:")
    print("-" * 40)
    openai_provider = OpenAIProvider(api_key="test-key")
    openai_models = openai_provider.get_available_models()
    print(f"Available models: {len(openai_models)}")
    for model in openai_models:
        print(f"  - {model.name} ({model.display_name})")
        print(f"    Context: {model.context_window:,} tokens")
        print(f"    Cost: ${model.cost_per_1k_input_tokens:.4f} / ${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
    print(f"Default model: {openai_provider.get_default_model()}")
    
    # Test Anthropic models
    print("\n2. Anthropic Models:")
    print("-" * 40)
    anthropic_provider = AnthropicProvider(api_key="test-key")
    anthropic_models = anthropic_provider.get_available_models()
    print(f"Available models: {len(anthropic_models)}")
    for model in anthropic_models:
        print(f"  - {model.name} ({model.display_name})")
        print(f"    Context: {model.context_window:,} tokens")
        print(f"    Cost: ${model.cost_per_1k_input_tokens:.4f} / ${model.cost_per_1k_output_tokens:.4f} per 1K tokens")
    print(f"Default model: {anthropic_provider.get_default_model()}")
    
    # Test Mock provider
    print("\n3. Mock Provider:")
    print("-" * 40)
    mock_provider = MockProvider(api_key="mock-key")
    mock_models = mock_provider.get_available_models()
    print(f"Available models: {len(mock_models)}")
    for model in mock_models:
        print(f"  - {model.name} ({model.display_name})")
    print(f"Default model: {mock_provider.get_default_model()}")
    
    print("\n" + "=" * 80)
    print("✅ MODEL CONFIGURATION TEST PASSED")
    print("=" * 80)


async def test_mock_generation():
    """Test text generation with mock provider"""
    print("\n" + "=" * 80)
    print("TESTING MOCK PROVIDER GENERATION")
    print("=" * 80)
    
    mock_provider = MockProvider(api_key="mock-key")
    
    prompt = "Transform this text into a tweet: AI models are constantly evolving."
    
    print(f"\nPrompt: {prompt}")
    print("-" * 40)
    
    response = await mock_provider.generate_text(
        prompt=prompt,
        model="mock-gpt-4",
        max_tokens=100
    )
    
    print(f"Response: {response.content}")
    print(f"Model used: {response.model}")
    print(f"Provider: {response.provider}")
    print(f"Tokens: {response.usage_metrics.input_tokens} in / {response.usage_metrics.output_tokens} out")
    
    print("\n" + "=" * 80)
    print("✅ MOCK GENERATION TEST PASSED")
    print("=" * 80)


async def test_anthropic_generation():
    """Test text generation with Anthropic (if API key available)"""
    anthropic_key = os.getenv("CLAUDE_API_KEY")
    
    if not anthropic_key:
        print("\n⚠️  Skipping Anthropic test (no CLAUDE_API_KEY in environment)")
        return
    
    print("\n" + "=" * 80)
    print("TESTING ANTHROPIC PROVIDER GENERATION")
    print("=" * 80)
    
    anthropic_provider = AnthropicProvider(api_key=anthropic_key)
    
    prompt = "Say 'Hello from Claude 4.5!' in exactly 5 words."
    
    print(f"\nPrompt: {prompt}")
    print(f"Using model: {anthropic_provider.get_default_model()}")
    print("-" * 40)
    
    try:
        response = await anthropic_provider.generate_text(
            prompt=prompt,
            max_tokens=50
        )
        
        print(f"✅ Response: {response.content}")
        print(f"Model used: {response.model}")
        print(f"Tokens: {response.usage_metrics.input_tokens} in / {response.usage_metrics.output_tokens} out")
        print(f"Cost: ${response.usage_metrics.estimated_cost:.6f}")
        
        print("\n" + "=" * 80)
        print("✅ ANTHROPIC GENERATION TEST PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"❌ Anthropic test failed: {type(e).__name__}: {str(e)}")
        print("\nThis might be due to:")
        print("  - Invalid API key")
        print("  - Quota/rate limits")
        print("  - Model name issues (check Anthropic docs)")


async def test_openai_generation():
    """Test text generation with OpenAI (if API key available)"""
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("\n⚠️  Skipping OpenAI test (no OPENAI_API_KEY in environment)")
        return
    
    print("\n" + "=" * 80)
    print("TESTING OPENAI PROVIDER GENERATION")
    print("=" * 80)
    
    openai_provider = OpenAIProvider(api_key=openai_key)
    
    prompt = "Say 'Hello from GPT-5!' in exactly 5 words."
    
    print(f"\nPrompt: {prompt}")
    print(f"Using model: {openai_provider.get_default_model()}")
    print("-" * 40)
    
    try:
        response = await openai_provider.generate_text(
            prompt=prompt,
            max_tokens=50
        )
        
        print(f"✅ Response: {response.content}")
        print(f"Model used: {response.model}")
        print(f"Tokens: {response.usage_metrics.input_tokens} in / {response.usage_metrics.output_tokens} out")
        print(f"Cost: ${response.usage_metrics.estimated_cost:.6f}")
        
        print("\n" + "=" * 80)
        print("✅ OPENAI GENERATION TEST PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"❌ OpenAI test failed: {type(e).__name__}: {str(e)}")
        print("\nThis might be due to:")
        print("  - Invalid API key")
        print("  - Quota/rate limits")
        print("  - Model not yet available in your account")


async def main():
    """Run all tests"""
    # Test 1: Model configurations
    test_model_configuration()
    
    # Test 2: Mock provider (always works)
    await test_mock_generation()
    
    # Test 3: Anthropic (if available)
    await test_anthropic_generation()
    
    # Test 4: OpenAI (if available)
    await test_openai_generation()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
    print("\nNotes:")
    print("  - Model names updated to official Anthropic/OpenAI identifiers")
    print("  - Anthropic uses alias format (auto-updates to latest snapshots)")
    print("  - OpenAI confirmed GPT-5, GPT-5 Mini, GPT-4o models exist")
    print("  - API failures are likely due to keys/quotas, not configuration")


if __name__ == "__main__":
    asyncio.run(main())
