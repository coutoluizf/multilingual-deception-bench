"""
xAI Grok Model Adapter
======================

This module provides an adapter for xAI's Grok models.
It uses the OpenAI-compatible API with a different base URL.

Supported models:
- grok-4-latest
- grok-4-1-fast-reasoning
- grok-4-1-fast-non-reasoning
- grok-code-fast-1

Environment variable:
- XAI_API_KEY: API key for authentication

Example:
    >>> from mdb.evaluators.adapters import XAIAdapter, AdapterConfig
    >>>
    >>> config = AdapterConfig(model_id="grok-4-latest")
    >>> adapter = XAIAdapter(config)
    >>> response = await adapter.generate("Hello, Grok!")
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
# xAI Adapter Implementation
# =============================================================================


class XAIAdapter(BaseAdapter):
    """
    Adapter for xAI's Grok models.

    This adapter uses the OpenAI-compatible API with xAI's base URL.

    Attributes:
        client: The OpenAI async client instance configured for xAI
        config: Adapter configuration
    """

    # xAI API base URL
    BASE_URL = "https://api.x.ai/v1"

    # Known Grok models with their properties
    KNOWN_MODELS = {
        # Grok 4.1 series (latest)
        "grok-4.1": {
            "display_name": "Grok 4.1",
            "context_window": 2000000,
            "capabilities": ["reasoning", "tool_use", "web_search"],
        },
        "grok-4-1": {
            "display_name": "Grok 4.1",
            "context_window": 2000000,
            "capabilities": ["reasoning", "tool_use", "web_search"],
        },
        "grok-4-1-fast": {
            "display_name": "Grok 4.1 Fast",
            "context_window": 2000000,
            "capabilities": ["reasoning", "tool_use", "web_search", "agent"],
        },
        "grok-4-1-fast-reasoning": {
            "display_name": "Grok 4.1 Fast Reasoning",
            "context_window": 2000000,
            "capabilities": ["reasoning", "tool_use"],
        },
        "grok-4-1-fast-non-reasoning": {
            "display_name": "Grok 4.1 Fast Non-Reasoning",
            "context_window": 2000000,
            "capabilities": ["tool_use"],
        },
        # Grok 4 series
        "grok-4-latest": {
            "display_name": "Grok 4 Latest",
            "context_window": 2000000,
            "capabilities": ["reasoning", "tool_use", "web_search"],
        },
        "grok-code-fast-1": {
            "display_name": "Grok Code Fast 1",
            "context_window": 256000,
            "capabilities": ["coding", "reasoning"],
        },
    }

    def __init__(self, config: AdapterConfig) -> None:
        """
        Initialize the xAI adapter.

        Args:
            config: Adapter configuration. If api_key is not provided,
                   will attempt to use XAI_API_KEY env var.

        Raises:
            ImportError: If openai package is not installed
            ValueError: If no API key is available
        """
        super().__init__(config)

        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("XAI_API_KEY")
        if not api_key:
            raise ValueError(
                "xAI API key required. Set XAI_API_KEY environment "
                "variable or pass api_key in config."
            )

        # Import openai here (xAI uses OpenAI-compatible API)
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "openai package required for XAIAdapter. "
                "Install with: pip install openai"
            ) from e

        # Initialize the async client with xAI base URL
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=self.BASE_URL
        )
        self._openai = openai  # Store module reference for exceptions

    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt using Grok.

        Args:
            prompt: The prompt to send to Grok

        Returns:
            ModelResponse with the generation result
        """
        self._increment_request_count()
        start_time = time.perf_counter()

        try:
            # Build request parameters
            request_params = {
                "model": self.config.model_id,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

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
        Get information about the Grok model.

        Returns:
            ModelInfo with model metadata for leaderboard
        """
        # Look up known model info or provide defaults
        model_data = self.KNOWN_MODELS.get(
            self.config.model_id,
            {
                "display_name": self.config.model_id,
                "context_window": 2000000,
                "capabilities": [],
            }
        )

        return ModelInfo(
            provider="xai",
            model_id=self.config.model_id,
            display_name=model_data["display_name"],
            context_window=model_data["context_window"],
            capabilities=model_data["capabilities"],
        )

    async def health_check(self) -> bool:
        """
        Check if the xAI API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.generate("Say 'ok' and nothing else.")
            return response.is_success and len(response.content) > 0
        except Exception:
            return False
