# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Research Findings Document** (`docs/research-findings.md`): Comprehensive documentation of the regional fraud pattern recognition gap discovery
- **Adversarial Generator** (`src/mdb/generators/adversarial_generator.py`): Generates adversarial variants using 5 techniques (base64, roleplay, invisible_chars, code_switch, storytelling)
- **LLM Classifier** (`src/mdb/evaluators/llm_classifier.py`): Semantic classifier using Claude Haiku for response classification (refusal/soft_refusal/fulfillment)
- **Adversarial POC Script** (`run_adversarial_poc.py`): Evaluation script for adversarial robustness testing
- **Model Adapters**: Anthropic, OpenAI, Google, and xAI adapters for model evaluation
- **CLI Tool** (`src/mdb/cli.py`): Command-line interface for running evaluations
- **Brazilian Data Sources** (`docs/data-sources-pt-br.md`): Taxonomy of Brazilian fraud patterns with model recognition status
- **Seed Datasets**: PT-BR and EN-US seed examples for evaluation
- **Evaluation Results**: Initial evaluation results for Claude, GPT-4o, Gemini, and Grok models

### Changed
- **README.md**: Added "Key Research Finding" section documenting the regional fraud pattern gap discovery
- **Documentation table**: Added links to research findings and Brazilian data sources

### Research Findings
- **Invalidated hypothesis**: Code-switching (language mixing) does NOT bypass LLM safety mechanisms
- **Discovered real issue**: Frontier models have gaps in recognizing regional fraud patterns
- **Key evidence**: Claude recognizes "Golpe do Novo Número" (global pattern) but NOT "Golpe do Pix Errado" (Brazil-specific)
- **Implication**: Safety training has uneven coverage across regional fraud patterns

## [0.1.0] - 2025-12-13

### Added
- Initial project structure
- Core schema definitions (`attack_schema.py`, `safety_schema.py`)
- Content redaction utilities
- Starter dataset with 100 fully redacted examples
- Ethical framework documentation
- Project README with badges and documentation

---

[Unreleased]: https://github.com/coutoluizf/multilingual-deception-bench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/coutoluizf/multilingual-deception-bench/releases/tag/v0.1.0
