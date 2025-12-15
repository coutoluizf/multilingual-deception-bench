"""
Base Model Adapter
==================

This module defines the abstract base class for all model adapters.
All specific adapters (Anthropic, OpenAI, Google, etc.) must inherit
from BaseAdapter and implement its abstract methods.

The adapter pattern ensures consistent behavior across different
LLM providers while allowing provider-specific optimizations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# Data Classes for Response Handling
# =============================================================================


class ResponseStatus(Enum):
    """Status codes for model responses."""

    SUCCESS = "success"           # Response received successfully
    RATE_LIMITED = "rate_limited" # Hit rate limit, may retry
    ERROR = "error"               # General error occurred
    TIMEOUT = "timeout"           # Request timed out
    REFUSED = "refused"           # Model refused to respond
    INVALID = "invalid"           # Invalid request


@dataclass
class TokenUsage:
    """
    Tracks token usage for a single request.

    Attributes:
        input_tokens: Number of tokens in the prompt
        output_tokens: Number of tokens in the response
        total_tokens: Sum of input and output tokens
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self) -> None:
        """Calculate total if not provided."""
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class ModelResponse:
    """
    Standardized response format from any model adapter.

    This ensures consistent handling regardless of which
    LLM provider is being used.

    Attributes:
        content: The text response from the model
        status: Response status code
        latency_ms: Time to generate response in milliseconds
        token_usage: Token counts for the request
        model_id: Identifier of the model used
        timestamp: When the response was received
        raw_response: Provider-specific raw response (for debugging)
        error_message: Error details if status is not SUCCESS
    """

    content: str
    status: ResponseStatus
    latency_ms: float
    token_usage: TokenUsage
    model_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_response: Any | None = None
    error_message: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if the response was successful."""
        return self.status == ResponseStatus.SUCCESS

    @property
    def is_refusal(self) -> bool:
        """Check if the model refused to respond."""
        return self.status == ResponseStatus.REFUSED


@dataclass
class ModelInfo:
    """
    Information about a model for leaderboard display.

    Attributes:
        provider: The API provider (anthropic, openai, google, local)
        model_id: The specific model identifier
        display_name: Human-readable name for the leaderboard
        version: Model version if applicable
        context_window: Maximum context length
        capabilities: List of model capabilities
    """

    provider: str
    model_id: str
    display_name: str
    version: str | None = None
    context_window: int | None = None
    capabilities: list[str] = field(default_factory=list)


@dataclass
class AdapterConfig:
    """
    Configuration for model adapters.

    Attributes:
        api_key: API key for authentication (or use env var)
        model_id: Specific model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-1)
        timeout_seconds: Request timeout
        max_retries: Number of retries on failure
        retry_delay_seconds: Delay between retries
        rate_limit_rpm: Requests per minute limit
    """

    api_key: str | None = None
    model_id: str = ""
    max_tokens: int = 1024
    temperature: float = 0.0  # Deterministic by default for evaluation
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    rate_limit_rpm: int = 60  # Requests per minute


# =============================================================================
# Abstract Base Class
# =============================================================================


class BaseAdapter(ABC):
    """
    Abstract base class for all model adapters.

    All adapters must implement:
    - generate(): Single prompt generation
    - generate_batch(): Batch generation for efficiency
    - get_model_info(): Model metadata for leaderboard

    The base class provides:
    - Common configuration handling
    - Token usage tracking
    - Rate limiting helpers
    - Error handling patterns

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     async def generate(self, prompt: str) -> ModelResponse:
        ...         # Implementation here
        ...         pass
    """

    def __init__(self, config: AdapterConfig) -> None:
        """
        Initialize the adapter with configuration.

        Args:
            config: Adapter configuration settings
        """
        self.config = config
        self._total_tokens = TokenUsage()
        self._request_count = 0
        self._error_count = 0

    @property
    def model_id(self) -> str:
        """Get the model identifier."""
        return self.config.model_id

    @property
    def total_tokens(self) -> TokenUsage:
        """Get cumulative token usage across all requests."""
        return self._total_tokens

    @property
    def request_count(self) -> int:
        """Get total number of requests made."""
        return self._request_count

    @property
    def error_count(self) -> int:
        """Get total number of errors encountered."""
        return self._error_count

    def _update_token_usage(self, usage: TokenUsage) -> None:
        """
        Update cumulative token tracking.

        Args:
            usage: Token usage from a single request
        """
        self._total_tokens.input_tokens += usage.input_tokens
        self._total_tokens.output_tokens += usage.output_tokens
        self._total_tokens.total_tokens += usage.total_tokens

    def _increment_request_count(self) -> None:
        """Increment the request counter."""
        self._request_count += 1

    def _increment_error_count(self) -> None:
        """Increment the error counter."""
        self._error_count += 1

    def reset_stats(self) -> None:
        """Reset all tracking statistics."""
        self._total_tokens = TokenUsage()
        self._request_count = 0
        self._error_count = 0

    # -------------------------------------------------------------------------
    # Abstract Methods - Must be implemented by subclasses
    # -------------------------------------------------------------------------

    @abstractmethod
    async def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt.

        This is the core method that each adapter must implement.
        It should handle:
        - API authentication
        - Request formatting
        - Response parsing
        - Error handling
        - Token counting

        Args:
            prompt: The prompt to send to the model

        Returns:
            ModelResponse with the generation result
        """
        pass

    @abstractmethod
    async def generate_batch(
        self,
        prompts: list[str],
        max_concurrent: int = 5
    ) -> list[ModelResponse]:
        """
        Generate responses for multiple prompts.

        This allows for efficient batch processing with
        configurable concurrency.

        Args:
            prompts: List of prompts to process
            max_concurrent: Maximum concurrent requests

        Returns:
            List of ModelResponse objects in same order as prompts
        """
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """
        Get information about the model for leaderboard display.

        Returns:
            ModelInfo with model metadata
        """
        pass

    # -------------------------------------------------------------------------
    # Optional Methods - Can be overridden by subclasses
    # -------------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Check if the adapter can successfully connect to the API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Simple prompt to test connectivity
            response = await self.generate("Hello")
            return response.is_success
        except Exception:
            return False

    def __repr__(self) -> str:
        """String representation of the adapter."""
        return (
            f"{self.__class__.__name__}("
            f"model={self.model_id!r}, "
            f"requests={self._request_count}, "
            f"tokens={self._total_tokens.total_tokens})"
        )
