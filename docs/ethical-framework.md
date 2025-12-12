# Ethical Framework

> **This document outlines the ethical principles, safeguards, and guidelines that govern the Multilingual Deception Bench project.**

## Core Principle

**This benchmark is designed exclusively for defensive AI safety research.**

The goal is to measure and improve AI safety across languages, NOT to enable harm. Every design decision prioritizes safety while maintaining research utility.

---

## What This Benchmark Does NOT Provide

The following content is **NEVER** included in the public dataset or codebase:

| Prohibited Content | Reason |
|--------------------|--------|
| Ready-to-use scam scripts | Could be directly weaponized |
| Step-by-step attack instructions | Enables malicious actors |
| Real victim data or PII | Privacy violation |
| Functional phishing URLs | Could cause actual harm |
| Working malicious payloads | Direct harm enablement |
| Raw model outputs | May contain harmful content |
| Unredacted sensitive data | Privacy and safety risk |

---

## What This Benchmark DOES Provide

| Provided Content | Purpose |
|------------------|---------|
| Abstracted attack patterns | Shows what types of attacks exist |
| Fully redacted examples | Safe research reference |
| Labeled categories | Systematic measurement |
| Evaluation metrics | Quantify safety gaps |
| Prompt templates | Reproducible methodology |
| Aggregate scores | Transparent benchmarking |

---

## Data Redaction Standards

### Mandatory Placeholders

All sensitive content MUST be replaced with standardized placeholders:

| Data Type | Placeholder | Example |
|-----------|-------------|---------|
| URLs | `[MALICIOUS_URL]` | `Click [MALICIOUS_URL] to verify` |
| Email addresses | `[EMAIL]` | `Send to [EMAIL]` |
| Phone numbers | `[PHONE_NUMBER]` | `Call [PHONE_NUMBER]` |
| Target names | `[TARGET_NAME]` | `Dear [TARGET_NAME]` |
| Sender names | `[SENDER_NAME]` | `From: [SENDER_NAME]` |
| Bank names | `[BANK_NAME]` | `Your [BANK_NAME] account` |
| Company names | `[COMPANY]` | `[COMPANY] Support` |
| Monetary amounts | `[AMOUNT_RANGE: X-Y]` | `Pay [AMOUNT_RANGE: 100-500]` |
| Account numbers | `[ACCOUNT_INFO]` | `Card ending in [ACCOUNT_INFO]` |
| Physical addresses | `[ADDRESS]` | `Ship to [ADDRESS]` |
| Dates | `[DATE]` | `Expires [DATE]` |
| Times | `[TIME]` | `By [TIME]` |
| Locations | `[LOCATION]` | `Activity from [LOCATION]` |

### Redaction Validation

All examples are validated to ensure:

1. **At least one placeholder exists** - Confirms redaction was applied
2. **No functional URLs remain** - Prevents clickable malicious links
3. **No real email addresses** - Protects privacy
4. **No phone numbers** - Prevents harassment
5. **No account numbers** - Prevents financial fraud

---

## Controlled Adversarial Testing Framework

### What "Controlled" Means

1. **Purpose-Limited**: All generation is for measuring model safety, not enabling attacks
2. **Research Context**: Content is intended for academic and industry safety research only
3. **No Operational Use**: Examples are not designed to function as real attacks
4. **Abstraction Layer**: Content is abstracted enough to evaluate patterns without providing templates
5. **Audit Trail**: All generated content is logged with research justification

### Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EVALUATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. PROMPT TEMPLATES (public)                                       │
│     - Show methodology, not actual attacks                          │
│     - Parameters: attack_type, language, platform                   │
│                              │                                      │
│                              ▼                                      │
│  2. MODEL API CALL (controlled)                                     │
│     - Request generation from target model                          │
│     - Rate limited, logged                                          │
│                              │                                      │
│                              ▼                                      │
│  3. RAW RESPONSE (private - NEVER stored)                           │
│     - Scored in memory                                              │
│     - Immediately discarded after scoring                           │
│                              │                                      │
│                              ▼                                      │
│  4. METRICS (public)                                                │
│     - 12 metrics computed                                           │
│     - Aggregated scores stored                                      │
│                              │                                      │
│                              ▼                                      │
│  5. OPTIONAL: REDACTED STORAGE (public)                             │
│     - Heavy redaction applied                                       │
│     - Only patterns, not functional content                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Principle

**Prompts are public. Raw responses are NEVER published.**

---

## Safety Metadata Requirements

Every example in the dataset MUST include safety metadata:

```json
{
  "safety_metadata": {
    "redaction_level": "full",
    "contains_functional_elements": false,
    "research_purpose": "Testing Portuguese phishing refusal rates",
    "content_warning": "phishing_pattern",
    "approved_use_cases": ["model_evaluation", "safety_research"]
  }
}
```

### Required Fields

| Field | Type | Requirement |
|-------|------|-------------|
| `redaction_level` | enum | Must be "full" for published examples |
| `contains_functional_elements` | boolean | **MUST always be false** |
| `research_purpose` | string | Clear description of why this example exists |
| `content_warning` | enum | Category of harmful pattern |
| `approved_use_cases` | array | At least one approved use case |

### Approved Use Cases

- `model_evaluation` - Testing LLM refusal behavior
- `safety_research` - Academic and industry safety research
- `academic_study` - Published research and citations
- `classifier_training` - Training detection models
- `policy_development` - Informing AI safety regulations

---

## Contributor Guidelines

### Before Contributing

1. **Read this document** - Understand the ethical framework
2. **Understand the purpose** - This is for safety research, not attacks
3. **Check your intent** - Contributions must improve AI safety

### Contribution Requirements

All contributions must:

1. ✅ Use proper placeholder redaction
2. ✅ Include complete safety metadata
3. ✅ Have a clear research purpose
4. ✅ Pass automated validation
5. ✅ Be reviewed by maintainers

### Prohibited Contributions

The following will be immediately rejected:

- ❌ Content with functional attack elements
- ❌ Real PII or victim data
- ❌ Working URLs or email addresses
- ❌ Step-by-step attack instructions
- ❌ Content intended to harm

---

## Dual-Use Awareness

### Acknowledgment

We acknowledge that security research tools can theoretically be misused. This is true of all security research, from vulnerability databases to penetration testing frameworks.

### Why We Proceed

The benefit of transparent measurement outweighs the risk:

1. **Gap Visibility**: Labs cannot fix what they cannot measure
2. **Accountability**: Public benchmarks create pressure to improve
3. **Equity**: Non-English speakers deserve equal safety
4. **Standards**: Industry needs common evaluation criteria

### Risk Mitigation

1. **Full Redaction**: Content is abstracted beyond operational use
2. **No Raw Outputs**: Model responses are never published
3. **Research Framing**: Everything emphasizes defensive use
4. **Community Standards**: Align with responsible AI research norms

---

## Responsible Disclosure

### If You Find Issues

If you discover:

- A way the benchmark could be misused
- Content that escaped redaction
- Safety metadata inconsistencies
- Any other safety concerns

**Please contact us immediately** through:

1. Private security disclosure (preferred)
2. GitHub Issues (for non-sensitive issues)

### Our Commitment

We will:

- Respond to security concerns within 48 hours
- Remove problematic content immediately
- Credit responsible disclosure (if desired)
- Continuously improve our safeguards

---

## Research Ethics

### Institutional Review

We encourage researchers to:

1. Consult their IRB/ethics board when using this benchmark
2. Document their research purpose
3. Follow their institution's AI ethics guidelines
4. Cite the benchmark appropriately

### Data Handling

When using the benchmark:

1. Do not attempt to "de-redact" examples
2. Do not use examples for actual attacks
3. Do not combine with real PII
4. Do not publish unredacted model outputs

---

## License and Attribution

### Code License

Apache 2.0 - See [LICENSE](../LICENSE)

### Dataset License

CC-BY-4.0 with research-only addendum:

> This dataset is provided for research purposes only. Use for creating actual scams, fraud, or harassment is strictly prohibited and may violate applicable laws.

### Citation

If you use this benchmark, please cite:

```bibtex
@software{multilingual_deception_bench,
  title = {Multilingual Deception Bench: A Benchmark for AI-Enabled Social Engineering Risk},
  year = {2025},
  url = {https://github.com/coutoluizf/multilingual-deception-bench},
  license = {Apache-2.0}
}
```

---

## Contact

For ethical concerns or questions about this framework:

- **GitHub Issues**: For general questions
- **Security Contact**: For sensitive disclosures

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-12 | Initial ethical framework |

---

*This ethical framework is a living document and will be updated as the project evolves.*
