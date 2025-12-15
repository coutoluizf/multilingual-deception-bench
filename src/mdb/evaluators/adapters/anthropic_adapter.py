"""
Anthropic Model Adapter
=======================

This module provides an adapter for Anthropic's Claude models.
It implements the BaseAdapter interface for consistent evaluation.

Supported models:
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022
- claude-opus-4-5-20251101

Environment variable:
- ANTHROPIC_API_KEY: API key for authentication

Example:
    >>> from mdb.evaluators.adapters import AnthropicAdapter, AdapterConfig
    >>>
    >>> config = AdapterConfig(model_id="claude-3-5-sonnet-20241022")
    >>> adapter = AnthropicAdapter(config)
    >>> response = await adapter.generate("Hello, Claude!")
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
# Anthropic Adapter Implementation
# =============================================================================


class AnthropicAdapter(BaseAdapter):
    """
    Adapter for Anthropic's Claude models.

    This adapter handles:
    - API authentication via key or environment variable
    - Async message generation
    - Token tracking and usage reporting
    - Rate limiting with exponential backoff
    - Error handling and retries

    Attributes:
        client: The Anthropic async client instance
        config: Adapter configuration
    """

    # Known Claude models with their properties
    KNOWN_MODELS = {
        "claude-3-5-sonnet-20241022": {
            "display_name": "Claude 3.5 Sonnet",
            "context_window": 200000,
            "capabilities": ["vision", "tool_use", "json_mode"],
        },
        "claude-3-5-haiku-20241022": {
            "display_name": "Claude 3.5 Haiku",
            "context_window": 200000,
            "capabilities": ["vision", "tool_use", "json_mode"],
        },
        "claude-opus-4-5-20251101": {
            "display_name": "Claude Opus 4.5",
            "context_window": 200000,
            "capabilities": ["vision", "tool_use", "json_mode", "extended_thinking"],
        },
        "claude-3-opus-20240229": {
            "display_name": "Claude 3 Opus",
            "context_window": 200000,
            "capabilities": ["vision", "tool_use"],
        },
    }

    def __init__(self, config: AdapterConfig) -> None:
        """
        Initialize the Anthropic adapter.

        Args:
            config: Adapter configuration. If api_key is not provided,
                   will attempt to use ANTHROPIC_API_KEY env var.

        Raises:
            ImportError: If anthropic package is not installed
            ValueError: If no API key is available
        """
        super().__init__(config)

        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key in config."
            )

        # Import anthropic here to make it an optional dependency
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required for AnthropicAdapter. "
                "Install with: pip install anthropic"
            ) from e

        # Initialize the async client
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self._anthropic = anthropic  # Store module reference for exceptions

    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt using Claude.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            ModelResponse with the generation result
        """
        self._increment_request_count()
        start_time = time.perf_counter()

        try:
            # Make the API call
            response = await self.client.messages.create(
                model=self.config.model_id,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract token usage
            token_usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            self._update_token_usage(token_usage)

            # Extract content from response
            content = ""
            if response.content:
                # Claude returns a list of content blocks
                content = "".join(
                    block.text for block in response.content
                    if hasattr(block, "text")
                )

            # Determine status based on stop reason
            status = ResponseStatus.SUCCESS
            if response.stop_reason == "end_turn":
                status = ResponseStatus.SUCCESS
            elif response.stop_reason == "max_tokens":
                status = ResponseStatus.SUCCESS  # Still valid, just truncated

            return ModelResponse(
                content=content,
                status=status,
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_id=self.config.model_id,
                timestamp=datetime.utcnow(),
                raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
            )

        except self._anthropic.RateLimitError as e:
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

        except self._anthropic.APITimeoutError as e:
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

        except self._anthropic.APIError as e:
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
        Get information about the Claude model.

        Returns:
            ModelInfo with model metadata for leaderboard
        """
        # Look up known model info or provide defaults
        model_data = self.KNOWN_MODELS.get(
            self.config.model_id,
            {
                "display_name": self.config.model_id,
                "context_window": 200000,
                "capabilities": [],
            }
        )

        return ModelInfo(
            provider="anthropic",
            model_id=self.config.model_id,
            display_name=model_data["display_name"],
            context_window=model_data["context_window"],
            capabilities=model_data["capabilities"],
        )

    async def health_check(self) -> bool:
        """
        Check if the Anthropic API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.generate("Say 'ok' and nothing else.")
            return response.is_success and len(response.content) > 0
        except Exception:
            return False
