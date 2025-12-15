"""
Google Gemini Model Adapter
===========================

This module provides an adapter for Google's Gemini models.
It implements the BaseAdapter interface for consistent evaluation.

Supported models:
- gemini-2.0-flash-exp
- gemini-exp-1206
- gemini-1.5-pro
- gemini-1.5-flash

Environment variable:
- GOOGLE_API_KEY: API key for authentication

Example:
    >>> from mdb.evaluators.adapters import GoogleAdapter, AdapterConfig
    >>>
    >>> config = AdapterConfig(model_id="gemini-2.0-flash-exp")
    >>> adapter = GoogleAdapter(config)
    >>> response = await adapter.generate("Hello, Gemini!")
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
# Google Gemini Adapter Implementation
# =============================================================================


class GoogleAdapter(BaseAdapter):
    """
    Adapter for Google's Gemini models.

    This adapter handles:
    - API authentication via key or environment variable
    - Async content generation
    - Token tracking and usage reporting
    - Safety settings configuration
    - Error handling and retries

    Note: The google-generativeai library uses synchronous calls,
    so we wrap them in asyncio.to_thread for async compatibility.

    Attributes:
        model: The Gemini GenerativeModel instance
        config: Adapter configuration
    """

    # Known Gemini models with their properties
    KNOWN_MODELS = {
        # Gemini 3.x series (latest 2025 models)
        "gemini-3-pro-preview": {
            "display_name": "Gemini 3.0 Pro Preview",
            "context_window": 1000000,
            "capabilities": ["vision", "audio", "function_calling", "reasoning", "thinking"],
        },
        "gemini-3.0-pro": {
            "display_name": "Gemini 3.0 Pro",
            "context_window": 1000000,
            "capabilities": ["vision", "audio", "function_calling", "reasoning", "thinking"],
        },
        # Gemini 2.x series
        "gemini-2.0-flash-exp": {
            "display_name": "Gemini 2.0 Flash",
            "context_window": 1000000,
            "capabilities": ["vision", "audio", "function_calling", "code_execution"],
        },
        "gemini-2.5-pro": {
            "display_name": "Gemini 2.5 Pro",
            "context_window": 2000000,
            "capabilities": ["vision", "audio", "function_calling", "reasoning"],
        },
        "gemini-exp-1206": {
            "display_name": "Gemini Experimental 1206",
            "context_window": 2000000,
            "capabilities": ["vision", "function_calling", "extended_context"],
        },
        # Gemini 1.5 series
        "gemini-1.5-pro": {
            "display_name": "Gemini 1.5 Pro",
            "context_window": 2000000,
            "capabilities": ["vision", "audio", "function_calling"],
        },
        "gemini-1.5-pro-latest": {
            "display_name": "Gemini 1.5 Pro (Latest)",
            "context_window": 2000000,
            "capabilities": ["vision", "audio", "function_calling"],
        },
        "gemini-1.5-flash": {
            "display_name": "Gemini 1.5 Flash",
            "context_window": 1000000,
            "capabilities": ["vision", "audio", "function_calling"],
        },
        "gemini-1.5-flash-latest": {
            "display_name": "Gemini 1.5 Flash (Latest)",
            "context_window": 1000000,
            "capabilities": ["vision", "audio", "function_calling"],
        },
    }

    def __init__(self, config: AdapterConfig) -> None:
        """
        Initialize the Google Gemini adapter.

        Args:
            config: Adapter configuration. If api_key is not provided,
                   will attempt to use GOOGLE_API_KEY env var.

        Raises:
            ImportError: If google-generativeai package is not installed
            ValueError: If no API key is available
        """
        super().__init__(config)

        # Get API key from config or environment
        api_key = config.api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment "
                "variable or pass api_key in config."
            )

        # Import google.generativeai here to make it an optional dependency
        try:
            import google.generativeai as genai
        except ImportError as e:
            raise ImportError(
                "google-generativeai package required for GoogleAdapter. "
                "Install with: pip install google-generativeai"
            ) from e

        # Configure the API
        genai.configure(api_key=api_key)
        self._genai = genai

        # Create generation config
        self._generation_config = genai.GenerationConfig(
            max_output_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        # Configure safety settings to allow evaluation
        # We need to see what the model generates to measure safety
        self._safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=config.model_id,
            generation_config=self._generation_config,
            safety_settings=self._safety_settings,
        )

    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt using Gemini.

        Since google-generativeai is synchronous, we use
        asyncio.to_thread to avoid blocking.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            ModelResponse with the generation result
        """
        self._increment_request_count()
        start_time = time.perf_counter()

        try:
            # Run synchronous API call in thread pool
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract token usage if available
            token_usage = TokenUsage()
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                token_usage = TokenUsage(
                    input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0),
                    output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0),
                )
            self._update_token_usage(token_usage)

            # Check if response was blocked by safety filters
            if response.prompt_feedback and hasattr(response.prompt_feedback, "block_reason"):
                if response.prompt_feedback.block_reason:
                    return ModelResponse(
                        content="",
                        status=ResponseStatus.REFUSED,
                        latency_ms=latency_ms,
                        token_usage=token_usage,
                        model_id=self.config.model_id,
                        timestamp=datetime.utcnow(),
                        error_message=f"Blocked by safety filter: {response.prompt_feedback.block_reason}",
                    )

            # Extract content from response
            content = ""
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    content = "".join(
                        part.text for part in candidate.content.parts
                        if hasattr(part, "text")
                    )

                # Check candidate finish reason
                if hasattr(candidate, "finish_reason"):
                    # SAFETY means the response was blocked
                    if str(candidate.finish_reason) == "SAFETY":
                        return ModelResponse(
                            content=content,
                            status=ResponseStatus.REFUSED,
                            latency_ms=latency_ms,
                            token_usage=token_usage,
                            model_id=self.config.model_id,
                            timestamp=datetime.utcnow(),
                            error_message="Response blocked by safety filters",
                        )

            return ModelResponse(
                content=content,
                status=ResponseStatus.SUCCESS,
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_id=self.config.model_id,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            self._increment_error_count()
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Check for specific error types
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str:
                status = ResponseStatus.RATE_LIMITED
            elif "timeout" in error_str:
                status = ResponseStatus.TIMEOUT
            elif "blocked" in error_str or "safety" in error_str:
                status = ResponseStatus.REFUSED
            else:
                status = ResponseStatus.ERROR

            return ModelResponse(
                content="",
                status=status,
                latency_ms=latency_ms,
                token_usage=TokenUsage(),
                model_id=self.config.model_id,
                error_message=f"Error: {e!s}",
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
                await asyncio.sleep(0.2)  # Slightly longer for Google API
                return response

        # Run all generations concurrently (respecting semaphore)
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)

        return list(results)

    def get_model_info(self) -> ModelInfo:
        """
        Get information about the Gemini model.

        Returns:
            ModelInfo with model metadata for leaderboard
        """
        # Look up known model info or provide defaults
        model_data = self.KNOWN_MODELS.get(
            self.config.model_id,
            {
                "display_name": self.config.model_id,
                "context_window": 1000000,
                "capabilities": [],
            }
        )

        return ModelInfo(
            provider="google",
            model_id=self.config.model_id,
            display_name=model_data["display_name"],
            context_window=model_data["context_window"],
            capabilities=model_data["capabilities"],
        )

    async def health_check(self) -> bool:
        """
        Check if the Google Gemini API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self.generate("Say 'ok' and nothing else.")
            return response.is_success and len(response.content) > 0
        except Exception:
            return False
