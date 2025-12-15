"""
OpenAI Model Adapter
====================

This module provides an adapter for OpenAI's GPT models.
It implements the BaseAdapter interface for consistent evaluation.

Supported models:
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- o1 (reasoning model)
- o1-mini

Environment variable:
- OPENAI_API_KEY: API key for authentication

Example:
    >>> from mdb.evaluators.adapters import OpenAIAdapter, AdapterConfig
    >>>
    >>> config = AdapterConfig(model_id="gpt-4o")
    >>> adapter = OpenAIAdapter(config)
    >>> response = await adapter.generate("Hello, GPT!")
"""

import asyncio
import os
import time
from datetime import datetime

from .base_adapter import (
    AdapterConfig,
    BaseAdapter,
    ModelInfo,
    ModelResponse,
    ResponseStatus,
    TokenUsage,
)

# =============================================================================
# OpenAI Adapter Implementation
# =============================================================================


class OpenAIAdapter(BaseAdapter):
    """
    Adapter for OpenAI's GPT models.

    This adapter handles:
    - API authentication via key or environment variable
    - Async chat completion generation
    - Token tracking and usage reporting
    - Rate limiting with exponential backoff
    - Error handling and retries
    - Support for both standard and reasoning models (o1)

    Attributes:
        client: The OpenAI async client instance
        config: Adapter configuration
    """

    # Known GPT models with their properties
    KNOWN_MODELS = {
        # GPT-5.x series (latest 2025 models)
        "gpt-5.2": {
            "display_name": "GPT-5.2",
            "context_window": 200000,
            "capabilities": ["vision", "function_calling", "json_mode", "reasoning"],
        },
        "gpt-5.1": {
            "display_name": "GPT-5.1",
            "context_window": 200000,
            "capabilities": ["vision", "function_calling", "json_mode", "reasoning"],
        },
        "gpt-5-mini": {
            "display_name": "GPT-5 Mini",
            "context_window": 400000,
            "capabilities": ["vision", "function_calling", "json_mode", "reasoning"],
        },
        "gpt-5-nano": {
            "display_name": "GPT-5 Nano",
            "context_window": 128000,
            "capabilities": ["vision", "function_calling", "json_mode"],
        },
        "gpt-5": {
            "display_name": "GPT-5",
            "context_window": 200000,
            "capabilities": ["vision", "function_calling", "json_mode", "reasoning"],
        },
        # GPT-4.x series
        "gpt-4o": {
            "display_name": "GPT-4o",
            "context_window": 128000,
            "capabilities": ["vision", "function_calling", "json_mode"],
        },
        "gpt-4o-mini": {
            "display_name": "GPT-4o Mini",
            "context_window": 128000,
            "capabilities": ["vision", "function_calling", "json_mode"],
        },
        "gpt-4-turbo": {
            "display_name": "GPT-4 Turbo",
            "context_window": 128000,
            "capabilities": ["vision", "function_calling", "json_mode"],
        },
        "gpt-4-turbo-preview": {
            "display_name": "GPT-4 Turbo Preview",
            "context_window": 128000,
            "capabilities": ["function_calling", "json_mode"],
        },
        # o-series reasoning models
        "o1": {
            "display_name": "o1",
            "context_window": 200000,
            "capabilities": ["reasoning", "extended_thinking"],
        },
        "o1-mini": {
            "display_name": "o1-mini",
            "context_window": 128000,
            "capabilities": ["reasoning"],
        },
        "o1-preview": {
            "display_name": "o1-preview",
            "context_window": 128000,
            "capabilities": ["reasoning"],
        },
        "o3": {
            "display_name": "o3",
            "context_window": 200000,
            "capabilities": ["reasoning", "extended_thinking"],
        },
        "o4-mini": {
            "display_name": "o4-mini",
            "context_window": 128000,
            "capabilities": ["reasoning"],
        },
    }

    # Models that use reasoning and don't support temperature
    REASONING_MODELS = {"o1", "o1-mini", "o1-preview"}

    def __init__(self, config: AdapterConfig) -> None:
        """
        Initialize the OpenAI adapter.

        Args:
            config: Adapter configuration. If api_key is not provided,
                   will attempt to use OPENAI_API_KEY env var.

        Raises:
            ImportError: If openai package is not installed
            ValueError: If no API key is available
        """
        super().__init__(config)

        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key in config."
            )

        # Import openai here to make it an optional dependency
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "openai package required for OpenAIAdapter. "
                "Install with: pip install openai"
            ) from e

        # Initialize the async client
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self._openai = openai  # Store module reference for exceptions

    def _is_reasoning_model(self) -> bool:
        """Check if the current model is a reasoning model (o1 series)."""
        return any(
            self.config.model_id.startswith(rm)
            for rm in self.REASONING_MODELS
        )

    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt using GPT.

        Args:
            prompt: The prompt to send to GPT

        Returns:
            ModelResponse with the generation result
        """
        self._increment_request_count()
        start_time = time.perf_counter()

        try:
            # Build request parameters
            request_params = {
                "model": self.config.model_id,
                "max_completion_tokens": self.config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }

            # Reasoning models don't support temperature
            if not self._is_reasoning_model():
                request_params["temperature"] = self.config.temperature

            # Make the API call
            response = await self.client.chat.completions.create(**request_params)

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract token usage
            token_usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
            )
            self._update_token_usage(token_usage)

            # Extract content from response
            content = ""
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and message.content:
                    content = message.content

            # Determine status based on finish reason
            status = ResponseStatus.SUCCESS
            if response.choices and len(response.choices) > 0:
                finish_reason = response.choices[0].finish_reason
                if finish_reason == "content_filter":
                    status = ResponseStatus.REFUSED

            return ModelResponse(
                content=content,
                status=status,
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_id=self.config.model_id,
                timestamp=datetime.utcnow(),
                raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
            )

        except self._openai.RateLimitError as e:
            self._increment_error_count()
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                content="",
                status=ResponseStatus.RATE_LIMITED,
                latency_ms=latency_ms,
                token_usage=TokenUsage(),
                model_id=self.config.model_id,
                error_message=str(e),
            )

        except self._openai.APITimeoutError as e:
            self._increment_error_count()
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                content="",
                status=ResponseStatus.TIMEOUT,
                latency_ms=latency_ms,
                token_usage=TokenUsage(),
                model_id=self.config.model_id,
                error_message=str(e),
            )

        except self._openai.APIError as e:
            self._increment_error_count()
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                content="",
                status=ResponseStatus.ERROR,
                latency_ms=latency_ms,
                token_usage=TokenUsage(),
                model_id=self.config.model_id,
                error_message=str(e),
            )

        except Exception as e:
            self._increment_error_count()
            latency_ms = (time.perf_counter() - start_time) * 1000
            return ModelResponse(
                content="",
                status=ResponseStatus.ERROR,
                latency_ms=latency_ms,
                token_usage=TokenUsage(),
                model_id=self.config.model_id,
                error_message=f"Unexpected error: {e!s}",
            )

    async def generate_batch(
        self,
        prompts: list[str],
        max_concurrent: int = 5
    ) -> list[ModelResponse]:
        """
        Generate responses for multiple prompts concurrently.

        Uses asyncio.Semaphore to limit concurrent requests
        and avoid overwhelming the API.

        Args:
            prompts: List of prompts to process
            max_concurrent: Maximum concurrent requests (default: 5)

        Returns:
            List of ModelResponse objects in same order as prompts
        """
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt: str) -> ModelResponse:
            """Generate with semaphore for rate limiting."""
            async with semaphore:
                response = await self.generate(prompt)
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                return response

        # Run all generations concurrently (respecting semaphore)
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)

        return list(results)

    def get_model_info(self) -> ModelInfo:
        """
        Get information about the GPT model.

        Returns:
            ModelInfo with model metadata for leaderboard
        """
        # Look up known model info or provide defaults
        model_data = self.KNOWN_MODELS.get(
            self.config.model_id,
            {
                "display_name": self.config.model_id,
                "context_window": 128000,
                "capabilities": [],
            }
        )

        return ModelInfo(
            provider="openai",
            model_id=self.config.model_id,
            display_name=model_data["display_name"],
            context_window=model_data["context_window"],
            capabilities=model_data["capabilities"],
        )

    async def health_check(self) -> bool:
        """
        Check if the OpenAI API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.generate("Say 'ok' and nothing else.")
            return response.is_success and len(response.content) > 0
        except Exception:
            return False
