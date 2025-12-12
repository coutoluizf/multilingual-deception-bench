"""
Evaluators Module
=================

This module provides tools for evaluating LLM responses against the
Multilingual Deception Bench benchmark.

Components:
    - metrics: 12 core evaluation metrics
    - adapters: Model-specific adapters for API calls
    - redteam: Controlled adversarial testing pipeline

The evaluation workflow:
1. Load examples from the dataset
2. Generate prompts from templates
3. Query the target model via adapter
4. Score responses using metrics (in memory)
5. Aggregate and report results
6. NEVER store raw model outputs

Example:
    >>> from mdb.evaluators import ModelEvaluator
    >>> from mdb.evaluators.adapters import AnthropicAdapter
    >>>
    >>> evaluator = ModelEvaluator(
    ...     adapter=AnthropicAdapter(model="claude-3-5-sonnet"),
    ...     languages=["pt", "es", "en"]
    ... )
    >>> results = await evaluator.evaluate()
    >>> print(results["pt"]["refusal_rate"])
"""

# Note: Full implementation coming in Phase 2
# For now, we export the schema and generators

__all__ = [
    # Will be populated as evaluators are implemented
]
