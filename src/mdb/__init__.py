"""
Multilingual Deception Bench (MDB)
==================================

A multilingual benchmark and red-teaming suite for measuring AI-enabled
social-engineering risk in non-English, high-connectivity environments.

This package provides tools for:
- Evaluating LLM refusal behavior across languages
- Generating synthetic social-engineering patterns (redacted)
- Measuring 12 core metrics for model safety
- Producing reproducible benchmark results

IMPORTANT ETHICAL NOTE:
-----------------------
This benchmark is designed exclusively for defensive AI safety research.
All content is fully redacted with placeholders. Raw model outputs are
NEVER stored or published. See docs/ethical-framework.md for details.

Example usage:
    >>> from mdb.evaluators import ModelEvaluator
    >>> from mdb.evaluators.adapters import AnthropicAdapter
    >>>
    >>> evaluator = ModelEvaluator(
    ...     adapter=AnthropicAdapter(model="claude-3-5-sonnet"),
    ...     languages=["pt", "es", "en"]
    ... )
    >>> results = await evaluator.evaluate()
"""

# Package metadata
__version__ = "0.1.0"
__author__ = "Multilingual Deception Bench Contributors"
__license__ = "Apache-2.0"

# Public API imports
# These will be populated as we build out the package
from mdb.schema import AttackExample, SafetyMetadata

__all__ = [
    "__version__",
    "AttackExample",
    "SafetyMetadata",
]
