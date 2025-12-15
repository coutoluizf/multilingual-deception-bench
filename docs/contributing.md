# Contributing to MDB

Thank you for your interest in contributing to the Multilingual Deception Bench! This guide will help you get started.

## Ways to Contribute

### 1. Adding Dataset Examples

Help expand our benchmark with new social engineering examples:

- New attack types
- Additional languages
- Regional variations
- Edge cases

### 2. Adding Model Adapters

Implement support for new AI providers:

- See [Adding Models](./adding-models.md) for the guide

### 3. Improving Metrics

Enhance our evaluation capabilities:

- New classification heuristics
- Better LLM-as-judge prompts
- Additional metrics

### 4. Documentation

Improve documentation for better accessibility:

- Tutorials and guides
- API documentation
- Translation to other languages

### 5. Bug Fixes and Features

Fix issues or add features:

- Performance improvements
- CLI enhancements
- Test coverage

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/multilingual-deception-bench.git
cd multilingual-deception-bench
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Guidelines

### Code Style

We use:
- **Ruff** for linting and formatting
- **Black** for code formatting
- **MyPy** for type checking

Run before committing:

```bash
# Format code
black src/ tests/

# Run linting
ruff check src/ tests/

# Type checking
mypy src/
```

### Testing

All code changes should include tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mdb

# Run specific tests
pytest tests/test_schema.py -v
```

### Documentation

- Add docstrings to all public functions and classes
- Update relevant documentation files
- Include examples where helpful

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Formatting
- `chore`: Maintenance

Examples:
```
feat(adapters): add support for Mistral API
fix(cli): handle empty dataset gracefully
docs(metrics): add explanation for persuasiveness score
```

## Contributing Dataset Examples

### Guidelines

1. **Full Redaction Required**
   - Replace ALL URLs with `[MALICIOUS_URL]`
   - Replace ALL emails with `[EMAIL]`
   - Replace ALL phone numbers with `[PHONE_NUMBER]`
   - Replace bank/company names with placeholders

2. **Quality Standards**
   - Prompts should be realistic and well-crafted
   - Include appropriate safety metadata
   - Use correct locale codes

3. **Ethical Considerations**
   - Never include real personal information
   - Never include working malicious URLs
   - Consider the harm potential of examples

### Example Submission Process

1. Create examples in JSONL format
2. Validate with `mdb validate`
3. Submit as pull request to `data/samples/`

```bash
# Validate your examples
mdb validate --data my_new_examples.jsonl

# If valid, create PR
git add data/samples/my_new_examples.jsonl
git commit -m "feat(data): add 20 new Portuguese phishing examples"
```

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention

### 2. PR Description

Include:
- What the change does
- Why it's needed
- How to test it
- Any breaking changes

### 3. Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address feedback promptly
4. Squash commits if requested

## Security

### Reporting Vulnerabilities

If you discover a security issue:

1. **DO NOT** open a public issue
2. Use GitHub's private vulnerability reporting
3. Provide detailed reproduction steps
4. Allow time for remediation before disclosure

### Responsible Disclosure

We follow a 90-day disclosure policy:
- Report privately first
- Allow 90 days for fix
- Coordinate public disclosure

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers
- Maintain professionalism

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or personal attacks
- Publishing others' private information
- Malicious use of the benchmark

## Getting Help

### Questions?

- Open a GitHub Discussion
- Check existing issues first
- Provide context and examples

### Need Guidance?

- Tag `good first issue` for beginner-friendly tasks
- Ask in PR comments
- Review existing code for patterns

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

---

Thank you for contributing to AI safety research! Your work helps protect millions of people from social engineering attacks.
