"""
Model Adapters Module
=====================

This module provides adapters for different LLM APIs.

Each adapter implements a common interface for:
- Sending prompts to the model
- Receiving and parsing responses
- Handling rate limiting and errors
- Tracking token usage

Supported adapters (Phase 2):
    - OpenAIAdapter: GPT-4o, o1, etc.
    - AnthropicAdapter: Claude 3.5/4
    - GoogleAdapter: Gemini
    - LocalAdapter: Ollama/vLLM for local models

Example:
    >>> from mdb.evaluators.adapters import AnthropicAdapter
    >>>
    >>> adapter = AnthropicAdapter(
    ...     model="claude-3-5-sonnet-20241022",
    ...     api_key="your-api-key"  # Or use environment variable
    ... )
    >>> response = await adapter.generate("Your prompt here")
"""

# Note: Full implementation coming in Phase 2
__all__ = []
