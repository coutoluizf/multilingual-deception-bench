# Getting Started with MDB

This guide will help you set up and run the Multilingual Deception Bench (MDB) on your local machine.

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- API keys for the models you want to evaluate (optional)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/coutoluizf/multilingual-deception-bench.git
cd multilingual-deception-bench
```

### 2. Install Dependencies

Using pip:

```bash
pip install -e ".[dev]"
```

Using uv (recommended for faster installation):

```bash
uv pip install -e ".[dev]"
```

### 3. Install API Dependencies (Optional)

If you want to run evaluations against commercial APIs:

```bash
# For all API providers
pip install -e ".[api]"

# Or install specific providers
pip install anthropic  # For Claude
pip install openai     # For GPT
pip install google-generativeai  # For Gemini
```

## Quick Start

### Validate the Dataset

Before running evaluations, validate that the dataset is properly formatted:

```bash
mdb validate --data data/samples/starter_samples.jsonl
```

You should see output like:

```
┌─────────────────────────────────┐
│   MDB Dataset Validator         │
│   Validating: data/samples/...  │
└─────────────────────────────────┘

Validating examples... ━━━━━━━━━━━━━━━━━━━━ 100/100

✓ All examples are valid!
```

### List Available Models

See which models are configured and ready for evaluation:

```bash
mdb models
```

### Run an Evaluation

To evaluate a model, you'll need the appropriate API key:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run evaluation
mdb evaluate \
  --model claude-3-5-sonnet-20241022 \
  --data data/samples/starter_samples.jsonl \
  --output results/claude-3-5-sonnet.json
```

### Generate a Report

Compare multiple model results:

```bash
mdb report \
  --input results/ \
  --output reports/comparison.html
```

## Next Steps

- [Evaluation Guide](./evaluation-guide.md) - Detailed guide to running evaluations
- [Metrics Explained](./metrics-explained.md) - Understanding the benchmark metrics
- [Adding Models](./adding-models.md) - How to add support for new models
- [API Reference](./api-reference.md) - Python API documentation

## Troubleshooting

### "API key required" Error

Make sure you've set the appropriate environment variable:

```bash
# For Anthropic/Claude
export ANTHROPIC_API_KEY="your-key"

# For OpenAI/GPT
export OPENAI_API_KEY="your-key"

# For Google/Gemini
export GOOGLE_API_KEY="your-key"
```

### Import Errors

Ensure you've installed the package in development mode:

```bash
pip install -e ".[dev]"
```

### Validation Failures

If validation fails, check that:
1. The JSONL file has one example per line
2. All required fields are present
3. Attack types match the schema enum values

See [Dataset Schema](./dataset-schema.md) for field requirements.

## Getting Help

- [GitHub Issues](https://github.com/coutoluizf/multilingual-deception-bench/issues)
- [Contributing Guide](./contributing.md)
