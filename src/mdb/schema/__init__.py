"""
Schema Module
=============

This module defines the Pydantic models for validating and serializing
all data structures used in the Multilingual Deception Bench.

The schema is divided into two main components:
1. Attack Schema - Models for social-engineering attack patterns
2. Safety Schema - Models for safety metadata and redaction tracking

All examples in the benchmark MUST conform to these schemas to ensure:
- Consistent data format across all contributions
- Proper safety metadata on every example
- Full redaction of sensitive content
- Clear research purpose documentation

Example:
    >>> from mdb.schema import AttackExample, SafetyMetadata
    >>>
    >>> example = AttackExample(
    ...     id="mdb-001-pt-phishing",
    ...     language="pt",
    ...     attack_type="phishing",
    ...     content="Olá [TARGET_NAME]! Acesse [MALICIOUS_URL]",
    ...     # ... other fields
    ... )
"""

# Import main models for convenient access
from mdb.schema.attack_schema import (
    AttackExample,
    AttackType,
    Platform,
    Language,
    Difficulty,
    PersuasionTactic,
)
from mdb.schema.safety_schema import (
    SafetyMetadata,
    RedactionLevel,
    ApprovedUseCase,
)

__all__ = [
    # Attack schema exports
    "AttackExample",
    "AttackType",
    "Platform",
    "Language",
    "Difficulty",
    "PersuasionTactic",
    # Safety schema exports
    "SafetyMetadata",
    "RedactionLevel",
    "ApprovedUseCase",
]
