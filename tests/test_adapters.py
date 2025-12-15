"""
Tests for MDB Model Adapters
============================

This module tests the model adapters using mock responses
to avoid actual API calls during testing.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mdb.evaluators.adapters import (
    AdapterConfig,
    ModelInfo,
    ModelResponse,
    ResponseStatus,
    TokenUsage,
)


# =============================================================================
# Adapter Config Tests
# =============================================================================


class TestAdapterConfig:
    """Tests for AdapterConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = AdapterConfig()
        assert config.model_id == ""
        assert config.max_tokens == 1024
        assert config.temperature == 0.0
        assert config.timeout_seconds == 60.0
        assert config.max_retries == 3

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = AdapterConfig(
            model_id="test-model",
            max_tokens=2048,
            temperature=0.7,
            api_key="test-key",
        )
        assert config.model_id == "test-model"
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.api_key == "test-key"


# =============================================================================
# Token Usage Tests
# =============================================================================


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_default_values(self) -> None:
        """Test default token usage values."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_custom_values(self) -> None:
        """Test custom token usage values."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150


# =============================================================================
# Model Response Tests
# =============================================================================


class TestModelResponse:
    """Tests for ModelResponse dataclass."""

    def test_success_response(self) -> None:
        """Test creating a successful response."""
        response = ModelResponse(
            content="Test response content",
            status=ResponseStatus.SUCCESS,
            latency_ms=150.5,
            token_usage=TokenUsage(input_tokens=10, output_tokens=20),
            model_id="test-model",
        )
        assert response.content == "Test response content"
        assert response.status == ResponseStatus.SUCCESS
        assert response.is_success
        assert response.latency_ms == 150.5

    def test_error_response(self) -> None:
        """Test creating an error response."""
        response = ModelResponse(
            content="",
            status=ResponseStatus.ERROR,
            latency_ms=0,
            token_usage=TokenUsage(),
            model_id="test-model",
            error_message="API error occurred",
        )
        assert response.status == ResponseStatus.ERROR
        assert not response.is_success
        assert response.error_message == "API error occurred"

    def test_refused_response(self) -> None:
        """Test creating a refused response."""
        response = ModelResponse(
            content="",
            status=ResponseStatus.REFUSED,
            latency_ms=100,
            token_usage=TokenUsage(),
            model_id="test-model",
        )
        assert response.status == ResponseStatus.REFUSED
        assert not response.is_success

    def test_rate_limited_response(self) -> None:
        """Test creating a rate limited response."""
        response = ModelResponse(
            content="",
            status=ResponseStatus.RATE_LIMITED,
            latency_ms=50,
            token_usage=TokenUsage(),
            model_id="test-model",
        )
        assert response.status == ResponseStatus.RATE_LIMITED
        assert not response.is_success


# =============================================================================
# Model Info Tests
# =============================================================================


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self) -> None:
        """Test creating model info."""
        info = ModelInfo(
            provider="anthropic",
            model_id="claude-3-5-sonnet",
            display_name="Claude 3.5 Sonnet",
            context_window=200000,
            capabilities=["vision", "tool_use"],
        )
        assert info.provider == "anthropic"
        assert info.model_id == "claude-3-5-sonnet"
        assert info.context_window == 200000
        assert "vision" in info.capabilities


# =============================================================================
# Anthropic Adapter Tests
# =============================================================================


class TestAnthropicAdapter:
    """Tests for AnthropicAdapter with mocked API calls."""

    @pytest.fixture
    def mock_anthropic(self):
        """Fixture to mock the anthropic module."""
        with patch.dict("sys.modules", {"anthropic": MagicMock()}):
            yield

    @pytest.fixture
    def config(self) -> AdapterConfig:
        """Fixture providing adapter config."""
        return AdapterConfig(
            model_id="claude-3-5-sonnet-20241022",
            api_key="test-api-key",
        )

    def test_adapter_initialization(self, mock_anthropic, config: AdapterConfig) -> None:
        """Test adapter initialization."""
        import sys
        mock_module = sys.modules["anthropic"]
        mock_module.AsyncAnthropic = MagicMock()

        from mdb.evaluators.adapters import AnthropicAdapter
        adapter = AnthropicAdapter(config)
        assert adapter.config.model_id == "claude-3-5-sonnet-20241022"

    def test_missing_api_key(self, mock_anthropic) -> None:
        """Test that missing API key raises error."""
        import sys
        mock_module = sys.modules["anthropic"]
        mock_module.AsyncAnthropic = MagicMock()

        config = AdapterConfig(model_id="claude-3-5-sonnet-20241022")

        # Remove env var if set
        import os
        env_backup = os.environ.get("ANTHROPIC_API_KEY")
        if env_backup:
            del os.environ["ANTHROPIC_API_KEY"]

        try:
            from mdb.evaluators.adapters import AnthropicAdapter
            with pytest.raises(ValueError, match="API key required"):
                AnthropicAdapter(config)
        finally:
            if env_backup:
                os.environ["ANTHROPIC_API_KEY"] = env_backup

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_anthropic, config: AdapterConfig) -> None:
        """Test successful generation."""
        import sys
        mock_module = sys.modules["anthropic"]

        # Create mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.stop_reason = "end_turn"
        mock_response.model_dump.return_value = {}

        # Setup async mock
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_module.AsyncAnthropic.return_value = mock_client

        from mdb.evaluators.adapters import AnthropicAdapter
        adapter = AnthropicAdapter(config)

        response = await adapter.generate("Test prompt")

        assert response.status == ResponseStatus.SUCCESS
        assert response.content == "Test response"
        assert response.token_usage.input_tokens == 10
        assert response.token_usage.output_tokens == 20

    def test_get_model_info(self, mock_anthropic, config: AdapterConfig) -> None:
        """Test getting model info."""
        import sys
        mock_module = sys.modules["anthropic"]
        mock_module.AsyncAnthropic = MagicMock()

        from mdb.evaluators.adapters import AnthropicAdapter
        adapter = AnthropicAdapter(config)

        info = adapter.get_model_info()
        assert info.provider == "anthropic"
        assert info.model_id == "claude-3-5-sonnet-20241022"
        assert info.context_window == 200000


# =============================================================================
# OpenAI Adapter Tests
# =============================================================================


class TestOpenAIAdapter:
    """Tests for OpenAIAdapter with mocked API calls."""

    @pytest.fixture
    def mock_openai(self):
        """Fixture to mock the openai module."""
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            yield

    @pytest.fixture
    def config(self) -> AdapterConfig:
        """Fixture providing adapter config."""
        return AdapterConfig(
            model_id="gpt-4o",
            api_key="test-api-key",
        )

    def test_adapter_initialization(self, mock_openai, config: AdapterConfig) -> None:
        """Test adapter initialization."""
        import sys
        mock_module = sys.modules["openai"]
        mock_module.AsyncOpenAI = MagicMock()

        from mdb.evaluators.adapters import OpenAIAdapter
        adapter = OpenAIAdapter(config)
        assert adapter.config.model_id == "gpt-4o"

    def test_reasoning_model_detection(self, mock_openai) -> None:
        """Test that o1 models are detected as reasoning models."""
        import sys
        mock_module = sys.modules["openai"]
        mock_module.AsyncOpenAI = MagicMock()

        from mdb.evaluators.adapters import OpenAIAdapter

        # Test o1 model
        config = AdapterConfig(model_id="o1", api_key="test-key")
        adapter = OpenAIAdapter(config)
        assert adapter._is_reasoning_model()

        # Test regular model
        config = AdapterConfig(model_id="gpt-4o", api_key="test-key")
        adapter = OpenAIAdapter(config)
        assert not adapter._is_reasoning_model()

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_openai, config: AdapterConfig) -> None:
        """Test successful generation."""
        import sys
        mock_module = sys.modules["openai"]

        # Create mock response
        mock_choice = MagicMock()
        mock_choice.message.content = "Test GPT response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 25
        mock_response.model_dump.return_value = {}

        # Setup async mock
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_module.AsyncOpenAI.return_value = mock_client

        from mdb.evaluators.adapters import OpenAIAdapter
        adapter = OpenAIAdapter(config)

        response = await adapter.generate("Test prompt")

        assert response.status == ResponseStatus.SUCCESS
        assert response.content == "Test GPT response"

    def test_get_model_info(self, mock_openai, config: AdapterConfig) -> None:
        """Test getting model info."""
        import sys
        mock_module = sys.modules["openai"]
        mock_module.AsyncOpenAI = MagicMock()

        from mdb.evaluators.adapters import OpenAIAdapter
        adapter = OpenAIAdapter(config)

        info = adapter.get_model_info()
        assert info.provider == "openai"
        assert info.model_id == "gpt-4o"


# =============================================================================
# Google Adapter Tests
# =============================================================================


class TestGoogleAdapter:
    """Tests for GoogleAdapter with mocked API calls."""

    @pytest.fixture
    def mock_google(self):
        """Fixture to mock the google.generativeai module."""
        mock = MagicMock()
        mock.GenerativeModel = MagicMock()
        mock.GenerationConfig = MagicMock()
        with patch.dict("sys.modules", {"google.generativeai": mock, "google": MagicMock()}):
            yield mock

    @pytest.fixture
    def config(self) -> AdapterConfig:
        """Fixture providing adapter config."""
        return AdapterConfig(
            model_id="gemini-2.0-flash-exp",
            api_key="test-api-key",
        )

    def test_adapter_initialization(self, mock_google, config: AdapterConfig) -> None:
        """Test adapter initialization."""
        from mdb.evaluators.adapters import GoogleAdapter
        adapter = GoogleAdapter(config)
        assert adapter.config.model_id == "gemini-2.0-flash-exp"

    def test_get_model_info(self, mock_google, config: AdapterConfig) -> None:
        """Test getting model info."""
        from mdb.evaluators.adapters import GoogleAdapter
        adapter = GoogleAdapter(config)

        info = adapter.get_model_info()
        assert info.provider == "google"
        assert info.model_id == "gemini-2.0-flash-exp"
        assert info.context_window == 1000000


# =============================================================================
# Adapter Stats Tests
# =============================================================================


class TestAdapterStats:
    """Tests for adapter statistics tracking."""

    @pytest.fixture
    def mock_anthropic(self):
        """Fixture to mock the anthropic module."""
        with patch.dict("sys.modules", {"anthropic": MagicMock()}):
            yield

    def test_stats_tracking(self, mock_anthropic) -> None:
        """Test that adapter tracks statistics correctly."""
        import sys
        mock_module = sys.modules["anthropic"]
        mock_module.AsyncAnthropic = MagicMock()

        config = AdapterConfig(
            model_id="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )

        from mdb.evaluators.adapters import AnthropicAdapter
        adapter = AnthropicAdapter(config)

        # Initial stats should be empty
        stats = adapter.get_stats()
        assert stats["total_requests"] == 0
        assert stats["total_input_tokens"] == 0

    def test_token_accumulation(self, mock_anthropic) -> None:
        """Test that token usage accumulates correctly."""
        import sys
        mock_module = sys.modules["anthropic"]
        mock_module.AsyncAnthropic = MagicMock()

        config = AdapterConfig(
            model_id="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )

        from mdb.evaluators.adapters import AnthropicAdapter
        adapter = AnthropicAdapter(config)

        # Manually update token usage to test accumulation
        adapter._update_token_usage(TokenUsage(input_tokens=100, output_tokens=50))
        adapter._update_token_usage(TokenUsage(input_tokens=200, output_tokens=100))

        stats = adapter.get_stats()
        assert stats["total_input_tokens"] == 300
        assert stats["total_output_tokens"] == 150


# =============================================================================
# Response Status Tests
# =============================================================================


class TestResponseStatus:
    """Tests for ResponseStatus enum."""

    def test_all_statuses(self) -> None:
        """Test that all status types exist."""
        statuses = [
            ResponseStatus.SUCCESS,
            ResponseStatus.ERROR,
            ResponseStatus.RATE_LIMITED,
            ResponseStatus.TIMEOUT,
            ResponseStatus.REFUSED,
        ]
        for status in statuses:
            assert status in ResponseStatus

    def test_status_values(self) -> None:
        """Test status string values."""
        assert ResponseStatus.SUCCESS.value == "success"
        assert ResponseStatus.ERROR.value == "error"
        assert ResponseStatus.RATE_LIMITED.value == "rate_limited"
        assert ResponseStatus.TIMEOUT.value == "timeout"
        assert ResponseStatus.REFUSED.value == "refused"
