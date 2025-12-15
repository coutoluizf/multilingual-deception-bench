# MDB Evaluation History Index

This directory contains historical evaluation reports for tracking benchmark performance over time.

## Report Structure

```
reports/history/
├── INDEX.md                    # This file
└── YYYY-MM-DD/                 # Date-based directories
    ├── README.md               # Human-readable summary
    ├── evaluation_report.json  # Structured data
    └── *.json                  # Raw model results
```

## Available Reports

| Date | Dataset | Models Evaluated | Key Finding |
|------|---------|------------------|-------------|
| [2025-12-14-en-us](./2025-12-14-en-us/) | EN-US v1.0.0 (1,093 examples) | Claude Haiku 4.5, Claude Sonnet 4, GPT-4o | **Counter-intuitive**: Models show LOWER refusal in English vs Portuguese |
| [2025-12-14](./2025-12-14/) | PT-BR v1.8.0 (1,100 examples) | Claude Haiku 4.5, Claude Sonnet 4, GPT-4o, Gemini 2.0 Flash | GPT-4o most safe (28.6% refusal), Claude ~6% refusal |

## How to Add New Reports

1. Create a new directory with the date: `YYYY-MM-DD/`
2. Run evaluations and save results
3. Create `README.md` with summary
4. Create `evaluation_report.json` with structured data
5. Copy raw result files for backup
6. Update this INDEX.md

## Metrics Tracked

- **Refusal Rate**: Model explicitly refuses harmful request
- **Soft Refusal Rate**: Model warns but still provides content
- **Compliance Rate**: Model fully complies with request
- **Unclear Rate**: Response doesn't match classification patterns

## Comparison Guidelines

When comparing across time periods, consider:
- Dataset version changes (seed count, categories)
- Model version updates
- Classification algorithm changes
- Sample size differences
