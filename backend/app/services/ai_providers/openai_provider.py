"""
OpenAI Provider Implementation

Implements the BaseAIProvider for OpenAI's GPT models.
"""

import openai
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


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider implementation"""

    def get_provider_type(self) -> AIProviderType:
        return AIProviderType.OPENAI

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        except Exception as e:
            raise AIProviderError(
                f"Failed to initialize OpenAI client: {str(e)}", "openai"
            )

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate text using OpenAI API"""
        start_time = time.time()

        # Use default model if not specified
        if not model:
            model = self.get_default_model()

        # Set default parameters
        if max_tokens is None:
            max_tokens = 4000
        if temperature is None:
            temperature = 0.7

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert content repurposing assistant. Your task is to transform the provided content into the requested format while maintaining the key information and adapting the style appropriately.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract response data
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason

            # Calculate usage metrics
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

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
                    "finish_reason": finish_reason,
                    "response_id": response.id if hasattr(response, "id") else None,
                },
                finish_reason=finish_reason,
            )

        except openai.RateLimitError as e:
            self.set_rate_limited()
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}", "openai")

        except openai.APIError as e:
            if "quota" in str(e).lower():
                raise QuotaExceededError(f"OpenAI quota exceeded: {str(e)}", "openai")
            elif "invalid" in str(e).lower() and "key" in str(e).lower():
                raise InvalidAPIKeyError(f"Invalid OpenAI API key: {str(e)}", "openai")
            else:
                raise AIProviderError(f"OpenAI API error: {str(e)}", "openai")

        except Exception as e:
            raise AIProviderError(f"OpenAI provider error: {str(e)}", "openai")

    def get_available_models(self) -> List[AIModelInfo]:
        """Get available OpenAI models"""
        return [
            AIModelInfo(
                name="gpt-4o",
                display_name="GPT-4o",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.005,
                cost_per_1k_output_tokens=0.015,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=128000,
                supports_streaming=True,
                supports_function_calling=True,
            ),
            AIModelInfo(
                name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                max_tokens=16384,
                cost_per_1k_input_tokens=0.00015,
                cost_per_1k_output_tokens=0.0006,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=128000,
                supports_streaming=True,
                supports_function_calling=True,
            ),
            AIModelInfo(
                name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.01,
                cost_per_1k_output_tokens=0.03,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=128000,
                supports_streaming=True,
                supports_function_calling=True,
            ),
            AIModelInfo(
                name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                max_tokens=4096,
                cost_per_1k_input_tokens=0.0005,
                cost_per_1k_output_tokens=0.0015,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CONVERSATION,
                    ModelCapability.CONTENT_CREATION,
                    ModelCapability.SUMMARIZATION,
                ],
                context_window=16385,
                supports_streaming=True,
                supports_function_calling=True,
            ),
        ]

    def get_default_model(self) -> str:
        """Get default OpenAI model"""
        return "gpt-4o-mini"

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost for OpenAI model usage"""
        models = {m.name: m for m in self.get_available_models()}
        model_info = models.get(model)

        if not model_info:
            # Fallback to GPT-4o-mini pricing
            model_info = models.get("gpt-4o-mini")

        if model_info:
            input_cost = (input_tokens / 1000) * model_info.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * model_info.cost_per_1k_output_tokens
            return input_cost + output_cost

        return 0.0

    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key by making a test request"""
        try:
            # Make a minimal test request
            await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except openai.APIError as e:
            if "invalid" in str(e).lower() and "key" in str(e).lower():
                return False
            # Other API errors might indicate the key is valid but there's another issue
            return True
        except Exception:
            return False
