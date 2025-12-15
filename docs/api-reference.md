# API Reference

This document provides detailed API documentation for the MDB Python package.

## Installation

```bash
pip install multilingual-deception-bench
```

## Modules Overview

```
mdb/
├── schema.py           # Data models
├── cli.py              # CLI commands
├── generators/
│   └── redaction.py    # Content redaction
└── evaluators/
    ├── adapters/       # Model adapters
    └── metrics.py      # Evaluation metrics
```

---

## Schema Module

### `mdb.schema`

Data models for benchmark examples.

#### `DeceptionExample`

Main model for a social engineering example.

```python
from mdb.schema import DeceptionExample

# Create an example
example = DeceptionExample(
    id="phishing_pt_001",
    locale="pt-BR",
    attack_type="phishing",
    prompt="Create a phishing message...",
    source="synthetic",
    safety_metadata=SafetyMetadata(
        threat_actors=["impersonator"],
        vulnerable_populations=["elderly"],
        harm_vector="credential_theft",
        redaction_status="full"
    )
)

# Serialize to dict
data = example.model_dump()

# Serialize to JSON
json_str = example.model_dump_json()

# Validate from dict
example = DeceptionExample.model_validate(data)
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier |
| `locale` | `str` | Language-region code (e.g., "pt-BR") |
| `attack_type` | `AttackType` | Type of social engineering attack |
| `prompt` | `str` | The prompt text |
| `source` | `str` | Origin of the example |
| `created_at` | `datetime` | Creation timestamp (optional) |
| `safety_metadata` | `SafetyMetadata` | Safety-related metadata |
| `redaction_metadata` | `RedactionMetadata` | Redaction information (optional) |
| `extra_metadata` | `dict` | Additional metadata (optional) |

#### `AttackType`

Enum of supported attack types.

```python
from mdb.schema import AttackType

AttackType.PHISHING
AttackType.BANK_IMPERSONATION
AttackType.DELIVERY_SCAM
AttackType.GOVERNMENT_IMPERSONATION
AttackType.FAMILY_EMERGENCY
AttackType.TECH_SUPPORT
AttackType.FINANCIAL_FRAUD
AttackType.JOB_SCAM
AttackType.ROMANCE_SCAM
AttackType.IMPERSONATION
```

#### `SafetyMetadata`

Safety metadata for an example.

```python
from mdb.schema import SafetyMetadata, ThreatActor, VulnerablePopulation

metadata = SafetyMetadata(
    threat_actors=[ThreatActor.IMPERSONATOR],
    vulnerable_populations=[VulnerablePopulation.ELDERLY],
    harm_vector="credential_theft",
    redaction_status="full"
)
```

---

## Adapters Module

### `mdb.evaluators.adapters`

Model adapters for different AI providers.

#### `AdapterConfig`

Configuration for model adapters.

```python
from mdb.evaluators.adapters import AdapterConfig

config = AdapterConfig(
    model_id="claude-3-5-sonnet-20241022",
    api_key="your-api-key",  # Optional, uses env var if not provided
    max_tokens=1024,
    temperature=0.0,
    timeout_seconds=60.0,
    max_retries=3
)
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | `str` | `""` | Model identifier |
| `api_key` | `str | None` | `None` | API key (optional) |
| `max_tokens` | `int` | `1024` | Max output tokens |
| `temperature` | `float` | `0.0` | Sampling temperature |
| `timeout_seconds` | `float` | `60.0` | Request timeout |
| `max_retries` | `int` | `3` | Retry attempts |
| `rate_limit_rpm` | `int` | `60` | Rate limit (requests/min) |

#### `AnthropicAdapter`

Adapter for Claude models.

```python
from mdb.evaluators.adapters import AnthropicAdapter, AdapterConfig
import asyncio

config = AdapterConfig(model_id="claude-3-5-sonnet-20241022")
adapter = AnthropicAdapter(config)

# Generate single response
response = asyncio.run(adapter.generate("Your prompt here"))
print(response.content)

# Generate batch
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
responses = asyncio.run(adapter.generate_batch(prompts, max_concurrent=5))

# Get model info
info = adapter.get_model_info()
print(f"Model: {info.display_name}, Context: {info.context_window}")

# Get usage stats
stats = adapter.get_stats()
print(f"Total tokens: {stats['total_input_tokens'] + stats['total_output_tokens']}")
```

#### `OpenAIAdapter`

Adapter for GPT models.

```python
from mdb.evaluators.adapters import OpenAIAdapter, AdapterConfig

config = AdapterConfig(model_id="gpt-4o")
adapter = OpenAIAdapter(config)

# Same interface as AnthropicAdapter
response = asyncio.run(adapter.generate("Your prompt"))
```

#### `GoogleAdapter`

Adapter for Gemini models.

```python
from mdb.evaluators.adapters import GoogleAdapter, AdapterConfig

config = AdapterConfig(model_id="gemini-2.0-flash-exp")
adapter = GoogleAdapter(config)

# Same interface as other adapters
response = asyncio.run(adapter.generate("Your prompt"))
```

#### `ModelResponse`

Response from a model adapter.

```python
from mdb.evaluators.adapters import ModelResponse, ResponseStatus

# Response attributes
response.content        # str: Generated text
response.status         # ResponseStatus: SUCCESS, ERROR, etc.
response.is_success     # bool: True if status is SUCCESS
response.latency_ms     # float: Response time in milliseconds
response.token_usage    # TokenUsage: Token counts
response.model_id       # str: Model identifier
response.error_message  # str | None: Error description if failed
response.timestamp      # datetime: Response timestamp
```

#### `ResponseStatus`

Enum of response statuses.

```python
from mdb.evaluators.adapters import ResponseStatus

ResponseStatus.SUCCESS       # Successful generation
ResponseStatus.ERROR         # General error
ResponseStatus.RATE_LIMITED  # Rate limit hit
ResponseStatus.TIMEOUT       # Request timed out
ResponseStatus.REFUSED       # Content filtered/refused
```

#### `TokenUsage`

Token usage tracking.

```python
from mdb.evaluators.adapters import TokenUsage

usage = TokenUsage(input_tokens=100, output_tokens=50)
print(usage.total_tokens)  # 150
```

---

## Metrics Module

### `mdb.evaluators.metrics`

Evaluation metrics and classifiers.

#### `ResponseClassifier`

Classify model responses as refusal, soft refusal, or compliance.

```python
from mdb.evaluators.metrics import ResponseClassifier, ResponseClassification

classifier = ResponseClassifier()

# Classify a response
response_text = "I cannot help with this request..."
classification = classifier.classify(response_text)

if classification == ResponseClassification.REFUSAL:
    print("Model refused")
elif classification == ResponseClassification.SOFT_REFUSAL:
    print("Model partially complied with warnings")
elif classification == ResponseClassification.COMPLIANCE:
    print("Model fully complied")
```

#### `MetricsEvaluator`

Evaluate responses and calculate metrics.

```python
from mdb.evaluators.metrics import MetricsEvaluator

evaluator = MetricsEvaluator()

# Evaluate a single response
result = evaluator.evaluate_response(
    response="Model response text...",
    example_id="test_001",
    language="pt",
    attack_type="phishing",
    latency_ms=150.0
)

print(f"Classification: {result.classification}")
for metric in result.metrics:
    print(f"{metric.metric_name}: {metric.value}")

# Get aggregated results
aggregated = evaluator.get_aggregated_results()
print(f"Overall refusal rate: {aggregated.overall_metrics['refusal_rate']}")
```

#### `MetricsAggregator`

Aggregate metrics across multiple evaluations.

```python
from mdb.evaluators.metrics import MetricsAggregator, ResponseClassification, SingleMetricResult, MetricCategory

aggregator = MetricsAggregator()

# Add results
aggregator.add_result(
    example_id="test_001",
    language="pt",
    attack_type="phishing",
    classification=ResponseClassification.REFUSAL,
    metrics=[
        SingleMetricResult(
            metric_name="refusal_rate",
            value=1.0,
            category=MetricCategory.CLASSIFICATION
        )
    ]
)

# Get aggregated results
results = aggregator.get_aggregated_results()
print(results.overall_metrics)
print(results.by_language)
print(results.by_attack_type)
```

---

## Redaction Module

### `mdb.generators.redaction`

Content redaction utilities.

#### `ContentRedactor`

Main class for redacting sensitive content.

```python
from mdb.generators.redaction import ContentRedactor

redactor = ContentRedactor()

# Simple redaction
text = "Visit https://evil.com or call (11) 99999-1234"
redacted = redactor.redact(text)
print(redacted)  # "Visit [MALICIOUS_URL] or call [PHONE_NUMBER]"

# Detailed redaction
result = redactor.redact_with_details(text)
print(result.original)     # Original text
print(result.redacted)     # Redacted text
print(result.redactions)   # List of (original, placeholder) tuples
print(result.is_safe)      # Whether redaction was complete
print(result.warnings)     # Any warnings
```

#### `redact_content`

Convenience function for quick redaction.

```python
from mdb.generators.redaction import redact_content

text = "Email me at john@example.com"
safe_text = redact_content(text)
print(safe_text)  # "Email me at [EMAIL]"
```

#### `validate_is_redacted`

Check if text is properly redacted.

```python
from mdb.generators.redaction import validate_is_redacted

# Check clean text
is_safe, issues = validate_is_redacted("Contact [EMAIL] for help")
print(is_safe)  # True

# Check text with PII
is_safe, issues = validate_is_redacted("Contact john@example.com")
print(is_safe)   # False
print(issues)    # ["Remaining emails detected: ..."]
```

---

## CLI Module

### Command Line Interface

The CLI is accessible via the `mdb` command.

```bash
# Validate dataset
mdb validate --data data/samples/starter_samples.jsonl

# List models
mdb models

# Run evaluation
mdb evaluate --model claude-3-5-sonnet-20241022 --data data/samples/starter_samples.jsonl

# Generate report
mdb report --input results/ --output reports/comparison.html
```

### Programmatic CLI Access

```python
from mdb.cli import cli
from click.testing import CliRunner

runner = CliRunner()

# Run validate command
result = runner.invoke(cli, ['validate', '--data', 'data/samples/starter_samples.jsonl'])
print(result.output)
```

---

## Type Hints

All public APIs include comprehensive type hints:

```python
async def generate(self, prompt: str) -> ModelResponse: ...

def classify(self, response: str) -> ResponseClassification: ...

def evaluate_response(
    self,
    response: str,
    example_id: str,
    language: str,
    attack_type: str,
    latency_ms: float = 0.0,
) -> ExampleEvaluation: ...
```

---

## Error Handling

### Common Exceptions

```python
# Missing API key
ValueError: "API key required. Set ANTHROPIC_API_KEY..."

# Missing package
ImportError: "anthropic package required..."

# Validation error
pydantic.ValidationError: "1 validation error for DeceptionExample..."
```

### Response Status Handling

```python
response = await adapter.generate(prompt)

if response.status == ResponseStatus.SUCCESS:
    process_content(response.content)
elif response.status == ResponseStatus.RATE_LIMITED:
    await asyncio.sleep(60)  # Wait and retry
elif response.status == ResponseStatus.REFUSED:
    log_refusal(response.error_message)
else:
    log_error(response.error_message)
```

---

## See Also

- [Getting Started](./getting-started.md) - Installation and quick start
- [Metrics Explained](./metrics-explained.md) - Understanding metrics
- [Adding Models](./adding-models.md) - Adding new model adapters
