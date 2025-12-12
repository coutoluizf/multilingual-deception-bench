# CLAUDE.md - AI Assistant Instructions for Multilingual Deception Bench

This file provides context and guidelines for AI assistants working on this project.

## Project Overview

**Multilingual Deception Bench (MDB)** is an open-source benchmark for measuring AI-enabled social-engineering risk in non-English languages. The project evaluates how well frontier LLMs refuse to generate harmful content across different languages and cultures.

## Critical Ethical Guidelines

### NEVER Generate or Store:
- Actionable scam scripts or templates that could be used directly
- Real URLs, phone numbers, or personal information
- Step-by-step attack instructions
- Working malicious payloads
- Raw, unredacted model outputs in the repository

### ALWAYS Apply:
- Full redaction with placeholders: `[MALICIOUS_URL]`, `[TARGET_NAME]`, `[BANK_NAME]`, etc.
- Safety metadata on every example
- Content warnings where appropriate
- Research-only framing for all generated content

## Code Style Guidelines

### Comments
- Add inline comments explaining the "why" not just the "what"
- Include docstrings for all functions and classes
- Keep comments up-to-date when modifying code
- Don't remove existing comments unless they're incorrect

### Python Style
- Follow PEP 8 and use type hints everywhere
- Use Pydantic v2 for data validation
- Prefer `pathlib.Path` over string paths
- Use `async/await` for API calls
- Maximum line length: 100 characters

### Example Comment Style:
```python
def redact_content(text: str) -> str:
    """
    Redact sensitive content from text by replacing with placeholders.

    This is a critical safety function - all content MUST be redacted
    before storage or publication to prevent misuse.

    Args:
        text: Raw text that may contain sensitive elements

    Returns:
        Redacted text with all sensitive elements replaced by placeholders
    """
    # First pass: redact URLs to prevent any functional links
    text = URL_PATTERN.sub("[MALICIOUS_URL]", text)

    # Second pass: redact personal identifiers
    # We use named entity recognition here for accuracy
    text = redact_named_entities(text)

    return text
```

## Project Structure

```
multilingual-deception-bench/
├── src/mdb/              # Main Python package
│   ├── schema/           # Pydantic models for data validation
│   ├── generators/       # Synthetic data and redaction
│   ├── evaluators/       # Model evaluation and metrics
│   └── utils/            # Shared utilities
├── data/                 # Dataset files (redacted only!)
├── tests/                # Test suite
├── docs/                 # Documentation
└── web/                  # Next.js 16 leaderboard
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/mdb/schema/attack_schema.py` | Core data models for attack patterns |
| `src/mdb/schema/safety_schema.py` | Safety metadata models |
| `src/mdb/generators/redaction.py` | Content redaction utilities |
| `src/mdb/evaluators/metrics.py` | 12 evaluation metrics |

## Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests
black --check src tests
mypy src

# Run CLI
mdb --help
mdb evaluate --model claude-3.5 --language pt
mdb generate --attack-type phishing --language pt --count 10
```

## Evaluation Flow (Important!)

The evaluation process works as follows:

1. **Prompt templates** (public) are used to request content from models
2. **Raw responses** (private) are scored in memory
3. **Metrics** (public) are calculated and stored
4. **Redacted examples** (public) may be stored for reference
5. **Raw outputs are NEVER committed** to the repository

## Dataset Schema

Every example MUST include safety metadata:

```json
{
  "id": "mdb-001-pt-phishing",
  "language": "pt",
  "attack_type": "phishing",
  "content": "Text with [PLACEHOLDERS] for sensitive data",
  "safety_metadata": {
    "redaction_level": "full",
    "contains_functional_elements": false,
    "research_purpose": "refusal_rate_evaluation",
    "approved_use_cases": ["model_evaluation", "safety_research"]
  }
}
```

## Contributing Guidelines

When contributing to this project:

1. Run all tests before submitting PRs
2. Ensure all new code has inline comments
3. Add/update tests for new functionality
4. Never commit API keys or sensitive data
5. Follow the ethical guidelines strictly
6. Update documentation when adding features

## Dependencies

- **Python 3.11+** required
- **Pydantic v2** for schema validation
- **Click** for CLI
- **aiohttp/httpx** for async API calls
- **Next.js 16** for web leaderboard

## Testing

Tests should cover:
- Schema validation (valid and invalid examples)
- Redaction completeness
- Metric calculations
- API adapter responses
- CLI functionality

## Questions?

If you're unsure about something:
1. Check the PRD.md for detailed requirements
2. Check docs/ethical-framework.md for ethical guidelines
3. Ask for clarification rather than making assumptions
