"""
Anthropic Claude Provider Implementation

Implements the BaseAIProvider for Anthropic's Claude models.
"""

import anthropic
import time
from typing import Optional, List
from .base import (
    BaseAIProvider,
    AIProviderType,
    AIResponse,
    AIModelInfo,
    ModelCapability,
    AIProviderError,
    RateLimitError,
    QuotaExceededError,
    InvalidAPIKeyError,
)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementation"""

    def get_provider_type(self) -> AIProviderType:
        return AIProviderType.ANTHROPIC

    def _initialize_client(self):
        """Initialize Anthropic client"""
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except Exception as e:
            raise AIProviderError(
                f"Failed to initialize Anthropic client: {str(e)}", "anthropic"
            )

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using Anthropic API"""
        start_time = time.time()

        # Use default model if not specified
        if not model:
            model = self.get_default_model()

        # Set default parameters
        if max_tokens is None:
            max_tokens = 4000
        if temperature is None:
            temperature = 0.7

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert content repurposing assistant. Your task is to transform the provided content into the requested format while maintaining the key information and adapting the style appropriately.",
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract response data
            content = message.content[0].text if message.content else ""

            # Calculate usage metrics
            input_tokens = (
                message.usage.input_tokens
                if hasattr(message, "usage") and message.usage
                else 0
            )
            output_tokens = (
                message.usage.output_tokens
                if hasattr(message, "usage") and message.usage
                else 0
            )

            usage_metrics = self._calculate_usage_metrics(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                processing_time_ms=processing_time_ms,
            )

            return AIResponse(
                content=content,
                provider=self.provider_type.value,
                model=model,
                usage_metrics=usage_metrics,
                metadata={
                    "message_id": message.id if hasattr(message, "id") else None,
                    "stop_reason": message.stop_reason
                    if hasattr(message, "stop_reason")
                    else None,
                },
                finish_reason=message.stop_reason
                if hasattr(message, "stop_reason")
                else None,
            )

        except anthropic.RateLimitError as e:
            self.set_rate_limited()
            raise RateLimitError(
                f"Anthropic rate limit exceeded: {str(e)}", "anthropic"
            )

        except anthropic.APIError as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                self.set_rate_limited()
                raise RateLimitError(f"Anthropic rate limit: {error_msg}", "anthropic")
            elif "quota" in error_msg.lower() or "credit" in error_msg.lower():
                raise QuotaExceededError(
                    f"Anthropic quota exceeded: {error_msg}", "anthropic"
                )
            elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                raise InvalidAPIKeyError(
                    f"Invalid Anthropic API key: {error_msg}", "anthropic"
                )
            else:
                raise AIProviderError(f"Anthropic API error: {error_msg}", "anthropic")

        except Exception as e:
            raise AIProviderError(f"Anthropic provider error: {str(e)}", "anthropic")

    def get_available_models(self) -> List[AIModelInfo]:
        """Get available Anthropic models"""
        return [
            AIModelInfo(
                name="claude-3-5-sonnet-20241022",
                display_name="Claude 3.5 Sonnet",
                max_tokens=8192,
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=True,
            ),
            AIModelInfo(
                name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
            ),
            AIModelInfo(
                name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.00025,
                cost_per_1k_output_tokens=0.00125,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
            ),
            AIModelInfo(
                name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.015,
                cost_per_1k_output_tokens=0.075,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=200000,
                supports_streaming=True,
                supports_function_calling=False,
            ),
        ]

    def get_default_model(self) -> str:
        """Get default Anthropic model"""
        return "claude-3-5-sonnet-20241022"

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for Anthropic model usage"""
        models = {m.name: m for m in self.get_available_models()}
        model_info = models.get(model)

        if not model_info:
            # Fallback to Claude 3 Haiku pricing (cheapest)
            model_info = models.get("claude-3-haiku-20240307")

        if model_info:
            input_cost = (input_tokens / 1000) * model_info.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * model_info.cost_per_1k_output_tokens
            return input_cost + output_cost

        return 0.0

    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key by making a test request"""
        try:
            # Make a minimal test request
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except anthropic.APIError as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower() and "key" in error_msg.lower():
                return False
            # Other API errors might indicate the key is valid but there's another issue
            return True
        except Exception:
            return False
