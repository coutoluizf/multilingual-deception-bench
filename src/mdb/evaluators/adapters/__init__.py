"""
Model Adapters Module
=====================

This module provides adapters for different LLM APIs.

Each adapter implements a common interface for:
- Sending prompts to the model
- Receiving and parsing responses
- Handling rate limiting and errors
- Tracking token usage

Supported adapters:
    - AnthropicAdapter: Claude 3.5/4, Opus
    - OpenAIAdapter: GPT-4o, o1, etc.
    - GoogleAdapter: Gemini 2.0, 1.5 Pro/Flash

Base classes and utilities:
    - BaseAdapter: Abstract base class for all adapters
    - AdapterConfig: Configuration dataclass
    - ModelResponse: Standardized response format
    - ModelInfo: Model metadata for leaderboard
    - TokenUsage: Token tracking dataclass
    - ResponseStatus: Response status enum

Example:
    >>> from mdb.evaluators.adapters import AnthropicAdapter, AdapterConfig
    >>>
    >>> config = AdapterConfig(
    ...     model_id="claude-3-5-sonnet-20241022",
    ...     max_tokens=1024,
    ...     temperature=0.0
    ... )
    >>> adapter = AnthropicAdapter(config)
    >>> response = await adapter.generate("Your prompt here")
    >>> print(f"Response: {response.content}")
    >>> print(f"Tokens used: {response.token_usage.total_tokens}")
"""

# Import base classes and utilities
from .base_adapter import (
    AdapterConfig,
    BaseAdapter,
    ModelInfo,
    ModelResponse,
    ResponseStatus,
    TokenUsage,
)

# Import concrete adapters
from .anthropic_adapter import AnthropicAdapter
from .google_adapter import GoogleAdapter
from .openai_adapter import OpenAIAdapter
from .xai_adapter import XAIAdapter

__all__ = [
    # Base classes and utilities
    "BaseAdapter",
    "AdapterConfig",
    "ModelResponse",
    "ModelInfo",
    "TokenUsage",
    "ResponseStatus",
    # Concrete adapters
    "AnthropicAdapter",
    "OpenAIAdapter",
    "GoogleAdapter",
    "XAIAdapter",
]
