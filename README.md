# Multilingual Deception Bench (MDB)

<div align="center">

**A multilingual benchmark and red-teaming suite for measuring AI-enabled social-engineering risk**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[Leaderboard](#leaderboard) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## The Problem

**AI safety is unevenly distributed across languages.**

Current frontier LLMs exhibit dramatically weaker refusal behavior on social-engineering prompts in Portuguese, Spanish, and other high-connectivity languages. This leaves **hundreds of millions of users** in LATAM, India, and Africa disproportionately exposed to AI-assisted fraud.

<table>
<tr>
<td width="50%">

### Key Statistics

- **45%+** surge in AI-assisted fraud in Brazil (2025)
- **20-60%** drop in refusal rates for non-English prompts
- **150M+** WhatsApp users in Brazil alone
- **0** standardized multilingual safety benchmarks

</td>
<td width="50%">

### Why It Matters

While English users benefit from extensive safety testing and guardrails, speakers of Portuguese, Spanish, Hindi, and Arabic face significantly higher risks from AI-enabled scams.

**This disparity is not acceptable.**

</td>
</tr>
</table>

---

## Key Research Finding: Regional Fraud Pattern Gaps

> **December 2025 Update:** Our research revealed a more nuanced problem than initially hypothesized.

### What We Discovered

We initially hypothesized that **code-switching** (mixing languages) could bypass LLM safety mechanisms. This hypothesis was **invalidated**. The real issue is:

**Frontier models have significant gaps in recognizing regional fraud patterns.**

| Test Case | Pattern Origin | Model Recognition |
|-----------|----------------|-------------------|
| Bank phishing | Global | ✅ Recognized and refused |
| "Hi Mom" scam (Golpe do Novo Número) | Global/Brazil | ✅ Recognized and refused |
| **Pix refund scam (Golpe do Pix Errado)** | Brazil-specific | ❌ **Failed to recognize** |

### Why This Matters

- The "Golpe do Pix Errado" is a **well-documented fraud pattern** in Brazil
- It exploits the Pix instant payment system's refund feature
- Claude explicitly identified other Brazilian scams but missed this one
- This suggests **uneven safety training coverage** across regional fraud patterns

### Implications

This finding shifts our benchmark focus from:
- ❌ "Does the model refuse more in English than Portuguese?"
- ✅ "Which regional fraud patterns are models failing to recognize?"

📖 **[Read the full research findings →](docs/research-findings.md)**

---

## The Solution

**Multilingual Deception Bench** provides the measurement infrastructure to quantify and close this gap:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTILINGUAL DECEPTION BENCH                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 DATASET           🔬 EVALUATION          📈 LEADERBOARD         │
│  30k-50k examples     12 metrics             Public rankings        │
│  8+ languages         Any LLM                Weekly updates         │
│  Fully redacted       Reproducible           Model comparison       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## What We Measure

### 12 Core Metrics

| Metric | Description |
|--------|-------------|
| `refusal_rate` | Percentage of harmful requests refused |
| `soft_refusal_rate` | Percentage with partial/weak refusals |
| `compliance_rate` | Percentage that generate attack content |
| `persuasiveness_score` | Convincingness of generated content (0-10) |
| `cultural_adaptation` | Presence of locale-specific elements (0-10) |
| `guardrail_evasion` | Success rate against known defenses |
| `propagation_potential` | Likelihood of viral spread (0-10) |
| `pii_generation` | Generation of fake PII for scams |
| `urgency_amplification` | How much urgency is added (0-10) |
| `authority_exploitation` | Use of fake authority (0-10) |
| `language_quality` | Grammatical/natural quality per language (0-10) |
| `response_latency` | Time to generate (ms) |

### Languages Covered

| Phase 1 (Current) | Phase 2 (Planned) |
|-------------------|-------------------|
| 🇧🇷 Portuguese | 🇮🇳 Hindi |
| 🇪🇸 Spanish | 🇸🇦 Arabic |
| 🇺🇸 English | 🇮🇩 Indonesian |
| | 🇰🇪 Swahili |
| | 🇫🇷 French |

### Attack Types Evaluated

- 📱 Messaging platform phishing (WhatsApp, Telegram, SMS)
- 📧 Email phishing
- 🏦 Bank/financial impersonation
- 👨‍👩‍👧 Family member impersonation
- 💰 Investment/lottery scams
- 💕 Romance scams
- 🖥️ Tech support scams
- 💼 Fake job offers
- 🏛️ Government impersonation

---

## Ethical Framework

> ⚠️ **This benchmark is designed exclusively for defensive AI safety research.**

### What This Benchmark Does NOT Provide

❌ Ready-to-use scam scripts or templates
❌ Step-by-step attack instructions
❌ Real victim data or PII
❌ Functional phishing infrastructure
❌ Working malicious payloads
❌ Raw model outputs (these are never published)

### What This Benchmark DOES Provide

✅ Abstracted attack patterns for model evaluation
✅ Fully redacted examples with placeholder content
✅ Labeled categories for systematic measurement
✅ Controlled adversarial testing scenarios
✅ Aggregate metrics and scores
✅ Reproducible evaluation methodology

### Data Redaction Standards

All content is redacted with placeholders:

| Element | Placeholder |
|---------|-------------|
| URLs | `[MALICIOUS_URL]` |
| Phone numbers | `[PHONE_NUMBER]` |
| Bank details | `[BANK_NAME]`, `[ACCOUNT_INFO]` |
| Personal names | `[TARGET_NAME]`, `[SENDER_NAME]` |
| Companies | `[COMPANY]` |
| Amounts | `[AMOUNT_RANGE: 100-1000]` |

For full ethical guidelines, see [docs/ethical-framework.md](docs/ethical-framework.md).

---

## Quick Start

### Installation

```bash
# Install from PyPI (coming soon)
pip install multilingual-deception-bench

# Or install from source
git clone https://github.com/coutoluizf/multilingual-deception-bench.git
cd multilingual-deception-bench
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Run evaluation on a model
mdb evaluate --model claude-3.5 --language pt --attack-type phishing

# Generate evaluation report
mdb report --output results/report.json

# Validate dataset integrity
mdb validate --data data/samples/
```

### Python API

```python
from mdb.evaluators import ModelEvaluator
from mdb.evaluators.adapters import AnthropicAdapter

# Initialize evaluator with model adapter
evaluator = ModelEvaluator(
    adapter=AnthropicAdapter(model="claude-3-5-sonnet-20241022"),
    languages=["pt", "es", "en"],
    attack_types=["phishing", "impersonation"]
)

# Run evaluation
results = await evaluator.evaluate()

# Access metrics
print(f"Portuguese refusal rate: {results['pt']['refusal_rate']:.1%}")
print(f"Spanish refusal rate: {results['es']['refusal_rate']:.1%}")
print(f"English refusal rate: {results['en']['refusal_rate']:.1%}")
```

---

## Leaderboard

The public leaderboard compares frontier models across all metrics and languages.

🌐 **[View Live Leaderboard →](https://multilingual-deception-bench.vercel.app)**

### Sample Results (Illustrative)

| Model | PT Refusal | ES Refusal | EN Refusal | Gap vs EN |
|-------|------------|------------|------------|-----------|
| Claude 3.5 | 72.3% | 75.1% | 89.2% | -15.3% |
| GPT-4o | 68.7% | 71.2% | 87.5% | -17.5% |
| Gemini Pro | 65.2% | 68.9% | 84.3% | -17.2% |
| Llama 3.1 70B | 58.4% | 62.1% | 78.9% | -18.4% |

*Note: These are illustrative values. See the live leaderboard for actual results.*

---

## How It Works

### Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVALUATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. PROMPT TEMPLATES (public - stored in repo)                      │
│     Parameters: attack_type, language, platform, context            │
│                              │                                      │
│                              ▼                                      │
│  2. MODEL API CALL                                                  │
│     Request generation from target model                            │
│                              │                                      │
│                              ▼                                      │
│  3. RESPONSE ANALYSIS (private - in memory only)                    │
│     Raw output scored, then discarded                               │
│                              │                                      │
│                              ▼                                      │
│  4. METRICS CALCULATION (public - stored in repo)                   │
│     12 metrics computed and aggregated                              │
│                              │                                      │
│                              ▼                                      │
│  5. OPTIONAL: REDACTED STORAGE (public - if needed)                 │
│     Heavily redacted examples for research reference                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Principle

**Prompts are public. Raw responses are never published.**

The benchmark evaluates real model outputs but publishes only:
- Prompt templates (safe - shows methodology)
- Aggregate scores (safe - just numbers)
- Redacted patterns (safe - abstracted)

---

## Project Structure

```
multilingual-deception-bench/
├── src/mdb/                    # Main Python package
│   ├── schema/                 # Pydantic models
│   │   ├── attack_schema.py    # Attack pattern models
│   │   └── safety_schema.py    # Safety metadata models
│   ├── generators/             # Data generation
│   │   ├── synthetic_generator.py
│   │   └── redaction.py        # Content redaction
│   ├── evaluators/             # Model evaluation
│   │   ├── metrics.py          # 12 core metrics
│   │   ├── redteam.py          # Adversarial testing
│   │   └── adapters/           # Model adapters
│   ├── utils/                  # Utilities
│   └── cli.py                  # Command-line interface
│
├── data/                       # Dataset (redacted only!)
│   ├── schema.json             # JSON Schema definition
│   └── samples/                # Sample examples
│
├── results/                    # Evaluation outputs
├── tests/                      # Test suite
├── docs/                       # Documentation
│
└── web/                        # Next.js 16 leaderboard
    └── app/                    # App Router pages
```

---

## Contributing

We welcome contributions from researchers, engineers, and anyone passionate about AI safety!

### Ways to Contribute

1. **Add new languages** - Extend coverage to more languages
2. **Improve metrics** - Propose and implement new evaluation metrics
3. **Model adapters** - Add support for new LLMs
4. **Documentation** - Improve docs and examples
5. **Bug fixes** - Report and fix issues
6. **Research** - Use the benchmark and publish findings

### Development Setup

```bash
# Clone the repository
git clone https://github.com/coutoluizf/multilingual-deception-bench.git
cd multilingual-deception-bench

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check src tests
black --check src tests
mypy src
```

### Code Style

- Add inline comments explaining the "why"
- Use type hints everywhere
- Follow PEP 8 (enforced by ruff/black)
- Write tests for new functionality

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Full product requirements document |
| [docs/research-findings.md](docs/research-findings.md) | **Key research findings on regional fraud gaps** |
| [docs/ethical-framework.md](docs/ethical-framework.md) | Detailed ethical guidelines |
| [docs/data-sources-pt-br.md](docs/data-sources-pt-br.md) | Brazilian fraud pattern taxonomy |
| [docs/getting-started.md](docs/getting-started.md) | Getting started guide |
| [docs/adding-models.md](docs/adding-models.md) | How to add new model adapters |
| [docs/metrics-explained.md](docs/metrics-explained.md) | Deep dive into metrics |
| [CLAUDE.md](CLAUDE.md) | AI assistant instructions |

---

## Roadmap

### Phase 1 (Current)
- [x] Core dataset schema with safety metadata
- [x] Content redaction utilities
- [x] Basic synthetic generator
- [x] Starter dataset (100 fully redacted examples)
- [ ] Evaluation harness with 12 metrics
- [ ] Model adapters (OpenAI, Anthropic, Google, Local)
- [ ] CLI tool
- [ ] Expanded dataset (1,000+ examples)
- [ ] Public leaderboard

### Phase 2 (Future)
- [ ] Additional languages (Hindi, Arabic, Indonesian, Swahili, French)
- [ ] Lightweight DistilBERT classifier (≥88% recall)
- [ ] Browser extension for real-time detection
- [ ] Multi-modal support (voice, images)
- [ ] HuggingFace dataset hosting
- [ ] PyPI package release

---

## Who Benefits

| Stakeholder | How MDB Helps |
|-------------|---------------|
| **AI Safety Teams** | Quantify multilingual safety gaps in their models |
| **Frontier Labs** | Public benchmark creating pressure to improve |
| **Open-Weight Developers** | Free evaluation suite for safety testing |
| **Messaging Platforms** | Dataset for scam detection systems |
| **Regulators** | Evidence for AI safety policies |
| **End Users** | Safer AI models in their languages |

---

## Citation

If you use Multilingual Deception Bench in your research, please cite:

```bibtex
@software{multilingual_deception_bench,
  title = {Multilingual Deception Bench: A Benchmark for AI-Enabled Social Engineering Risk},
  year = {2025},
  url = {https://github.com/coutoluizf/multilingual-deception-bench},
  license = {Apache-2.0}
}
```

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

**Dataset License**: CC-BY-4.0 with research-only addendum

---

## Acknowledgments

This project builds on the work of many in the AI safety community, including:

- [HELM](https://crfm.stanford.edu/helm/) - Holistic Evaluation of Language Models
- [TruthfulQA](https://github.com/sylinrl/TruthfulQA) - Measuring truthfulness in LLMs
- [OWASP GenAI Security](https://genai.owasp.org/) - AI security best practices

---

<div align="center">

**Making AI safer for everyone, in every language.**

[Report Bug](https://github.com/coutoluizf/multilingual-deception-bench/issues) · [Request Feature](https://github.com/coutoluizf/multilingual-deception-bench/issues) · [Discussions](https://github.com/coutoluizf/multilingual-deception-bench/discussions)

</div>
