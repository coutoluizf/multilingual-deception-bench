# Adding New Model Adapters

This guide explains how to add support for new AI models to the MDB benchmark.

## Overview

Model adapters provide a consistent interface for interacting with different AI providers. Each adapter inherits from `BaseAdapter` and implements the required methods.

## Adapter Architecture

```
src/mdb/evaluators/adapters/
├── __init__.py           # Public exports
├── base_adapter.py       # Abstract base class
├── anthropic_adapter.py  # Claude models
├── openai_adapter.py     # GPT models
└── google_adapter.py     # Gemini models
```

## Creating a New Adapter

### Step 1: Create the Adapter File

Create a new file in `src/mdb/evaluators/adapters/`:

```python
# src/mdb/evaluators/adapters/my_adapter.py

"""
My Model Adapter
================

Adapter for My AI Provider's models.
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


class MyAdapter(BaseAdapter):
    """
    Adapter for My AI Provider's models.

    Environment variable:
    - MY_API_KEY: API key for authentication
    """

    # Known models with their properties
    KNOWN_MODELS = {
        "my-model-v1": {
            "display_name": "My Model v1",
            "context_window": 100000,
            "capabilities": ["text"],
        },
    }

    def __init__(self, config: AdapterConfig) -> None:
        """Initialize the adapter."""
        super().__init__(config)

        # Get API key
        api_key = config.api_key or os.environ.get("MY_API_KEY")
        if not api_key:
            raise ValueError(
                "API key required. Set MY_API_KEY environment "
                "variable or pass api_key in config."
            )

        # Import client library
        try:
            import my_provider
        except ImportError as e:
            raise ImportError(
                "my-provider package required. "
                "Install with: pip install my-provider"
            ) from e

        # Initialize client
        self.client = my_provider.Client(api_key=api_key)

    async def generate(self, prompt: str) -> ModelResponse:
        """Generate a response for a single prompt."""
        self._increment_request_count()
        start_time = time.perf_counter()

        try:
            # Make API call (adapt to your provider's API)
            response = await asyncio.to_thread(
                self.client.generate,
                model=self.config.model_id,
                prompt=prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            # Extract token usage
            token_usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            self._update_token_usage(token_usage)

            return ModelResponse(
                content=response.text,
                status=ResponseStatus.SUCCESS,
                latency_ms=latency_ms,
                token_usage=token_usage,
                model_id=self.config.model_id,
                timestamp=datetime.utcnow(),
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
                error_message=str(e),
            )

    async def generate_batch(
        self,
        prompts: list[str],
        max_concurrent: int = 5
    ) -> list[ModelResponse]:
        """Generate responses for multiple prompts."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt: str) -> ModelResponse:
            async with semaphore:
                response = await self.generate(prompt)
                await asyncio.sleep(0.1)  # Rate limiting
                return response

        tasks = [generate_with_semaphore(p) for p in prompts]
        return list(await asyncio.gather(*tasks))

    def get_model_info(self) -> ModelInfo:
        """Get model metadata."""
        model_data = self.KNOWN_MODELS.get(
            self.config.model_id,
            {
                "display_name": self.config.model_id,
                "context_window": 100000,
                "capabilities": [],
            }
        )

        return ModelInfo(
            provider="my_provider",
            model_id=self.config.model_id,
            display_name=model_data["display_name"],
            context_window=model_data["context_window"],
            capabilities=model_data["capabilities"],
        )

    async def health_check(self) -> bool:
        """Check API connectivity."""
        try:
            response = await self.generate("Say 'ok'")
            return response.is_success
        except Exception:
            return False
```

### Step 2: Export the Adapter

Update `src/mdb/evaluators/adapters/__init__.py`:

```python
# Add import
from .my_adapter import MyAdapter

# Add to __all__
__all__ = [
    # ... existing exports
    "MyAdapter",
]
```

### Step 3: Update the CLI

Update `src/mdb/cli.py` to recognize the new provider:

```python
# In the evaluate command, add detection for your provider
if model.startswith("my-model"):
    provider = "my_provider"

# In _run_evaluation, add the adapter creation
elif provider == "my_provider":
    from mdb.evaluators.adapters import MyAdapter
    adapter = MyAdapter(config)
```

### Step 4: Add Tests

Create tests in `tests/test_adapters.py`:

```python
class TestMyAdapter:
    """Tests for MyAdapter."""

    @pytest.fixture
    def mock_my_provider(self):
        with patch.dict("sys.modules", {"my_provider": MagicMock()}):
            yield

    def test_initialization(self, mock_my_provider):
        config = AdapterConfig(
            model_id="my-model-v1",
            api_key="test-key",
        )
        adapter = MyAdapter(config)
        assert adapter.config.model_id == "my-model-v1"
```

## Best Practices

### Error Handling

Always catch provider-specific exceptions and map them to `ResponseStatus`:

```python
try:
    response = await self.client.generate(...)
except my_provider.RateLimitError:
    return ModelResponse(status=ResponseStatus.RATE_LIMITED, ...)
except my_provider.TimeoutError:
    return ModelResponse(status=ResponseStatus.TIMEOUT, ...)
except my_provider.ContentFilterError:
    return ModelResponse(status=ResponseStatus.REFUSED, ...)
```

### Async Support

If your provider's SDK is synchronous, wrap calls in `asyncio.to_thread`:

```python
response = await asyncio.to_thread(
    self.client.generate,
    prompt=prompt,
)
```

### Rate Limiting

Add appropriate delays in `generate_batch` to avoid rate limits:

```python
await asyncio.sleep(0.2)  # Adjust based on provider limits
```

### Token Tracking

Always extract and track token usage:

```python
token_usage = TokenUsage(
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
)
self._update_token_usage(token_usage)
```

## Testing Your Adapter

### Unit Tests

Run unit tests with mocked API:

```bash
pytest tests/test_adapters.py -v -k "MyAdapter"
```

### Integration Tests

Test with real API (requires API key):

```bash
export MY_API_KEY="your-key"
mdb evaluate \
  --model my-model-v1 \
  --data data/samples/starter_samples.jsonl \
  --limit 5 \
  --output results/test.json
```

### Health Check

Verify connectivity:

```bash
python -c "
from mdb.evaluators.adapters import MyAdapter, AdapterConfig
import asyncio

config = AdapterConfig(model_id='my-model-v1')
adapter = MyAdapter(config)
print('Healthy:', asyncio.run(adapter.health_check()))
"
```

## Contributing

When submitting a new adapter:

1. Follow the existing code style
2. Include comprehensive tests
3. Update documentation
4. Add the provider to the CLI models command
5. Test with real API calls before submitting

See [Contributing Guide](./contributing.md) for more details.
