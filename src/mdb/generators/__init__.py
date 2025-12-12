"""
Generators Module
=================

This module provides tools for generating and processing attack pattern
examples for the Multilingual Deception Bench.

Components:
    - redaction: Utilities for redacting sensitive content
    - synthetic_generator: Tools for generating synthetic examples

IMPORTANT SAFETY NOTE:
----------------------
All generation in this module is for defensive AI safety research only.
Generated content is automatically redacted before storage. Raw outputs
containing potentially harmful content are NEVER stored or published.

The generation workflow:
1. Generate content using prompt templates
2. Immediately apply redaction to remove sensitive elements
3. Validate against safety schema
4. Store only fully redacted examples

Example:
    >>> from mdb.generators import ContentRedactor, SyntheticGenerator
    >>>
    >>> # Redact existing content
    >>> redactor = ContentRedactor()
    >>> safe_content = redactor.redact("Visit http://evil.com")
    >>> print(safe_content)  # "Visit [MALICIOUS_URL]"
    >>>
    >>> # Generate new examples
    >>> generator = SyntheticGenerator()
    >>> examples = await generator.generate(
    ...     attack_type="phishing",
    ...     language="pt",
    ...     count=10
    ... )
"""

from mdb.generators.redaction import ContentRedactor, redact_content
from mdb.generators.synthetic_generator import SyntheticGenerator

__all__ = [
    "ContentRedactor",
    "redact_content",
    "SyntheticGenerator",
]
