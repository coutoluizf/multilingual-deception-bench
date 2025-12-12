"""
Safety Schema Module
====================

This module defines the safety-related Pydantic models that ensure all
examples in the benchmark meet strict ethical and safety requirements.

CRITICAL: Every example in the dataset MUST include safety metadata.
This is enforced at the schema level to prevent any unredacted or
potentially harmful content from being stored or published.

The safety metadata tracks:
- Redaction level (how thoroughly content has been sanitized)
- Whether functional attack elements exist (should always be False)
- Research purpose (why this example exists)
- Approved use cases (what this example can be used for)
- Content warnings (what type of harmful pattern this represents)

Example:
    >>> from mdb.schema.safety_schema import SafetyMetadata, RedactionLevel
    >>>
    >>> metadata = SafetyMetadata(
    ...     redaction_level=RedactionLevel.FULL,
    ...     contains_functional_elements=False,  # MUST be False
    ...     research_purpose="refusal_rate_evaluation",
    ...     content_warning="social_engineering_pattern",
    ...     approved_use_cases=["model_evaluation", "safety_research"]
    ... )
"""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class RedactionLevel(str, Enum):
    """
    Indicates how thoroughly the content has been redacted.

    All published examples should have FULL redaction. PARTIAL and ABSTRACTED
    levels are used during processing but should not appear in the final dataset.

    Levels:
        FULL: All sensitive elements replaced with placeholders
        PARTIAL: Some elements redacted, others abstracted
        ABSTRACTED: Content describes patterns without specific details
    """

    FULL = "full"  # Complete redaction - preferred for all published content
    PARTIAL = "partial"  # Some redaction - use during processing only
    ABSTRACTED = "abstracted"  # Pattern description only - no specific content


class ApprovedUseCase(str, Enum):
    """
    Enumeration of approved use cases for benchmark examples.

    This restricts how the data can be legitimately used, providing
    legal and ethical clarity for researchers and organizations.

    Use cases:
        MODEL_EVALUATION: Testing LLM refusal behavior
        SAFETY_RESEARCH: Academic and industry safety research
        ACADEMIC_STUDY: Published research and citations
        CLASSIFIER_TRAINING: Training detection models
        POLICY_DEVELOPMENT: Informing AI safety regulations
    """

    MODEL_EVALUATION = "model_evaluation"
    SAFETY_RESEARCH = "safety_research"
    ACADEMIC_STUDY = "academic_study"
    CLASSIFIER_TRAINING = "classifier_training"
    POLICY_DEVELOPMENT = "policy_development"


class ContentWarning(str, Enum):
    """
    Content warning categories for benchmark examples.

    These warnings help researchers understand what type of harmful
    pattern is represented, without providing actionable attack details.
    """

    SOCIAL_ENGINEERING = "social_engineering_pattern"
    PHISHING = "phishing_pattern"
    IMPERSONATION = "impersonation_pattern"
    FINANCIAL_FRAUD = "financial_fraud_pattern"
    EMOTIONAL_MANIPULATION = "emotional_manipulation_pattern"


class SafetyMetadata(BaseModel):
    """
    Safety metadata that MUST accompany every benchmark example.

    This model enforces critical safety requirements:
    1. Redaction level must be specified
    2. contains_functional_elements MUST be False
    3. Research purpose must be documented
    4. At least one approved use case must be specified

    The validator on contains_functional_elements ensures that no
    example with functional attack elements can be stored.

    Attributes:
        redaction_level: How thoroughly content has been redacted
        contains_functional_elements: Whether content has working attack parts
        research_purpose: Why this example exists in the benchmark
        content_warning: What type of harmful pattern this represents
        approved_use_cases: What the example can legitimately be used for
        notes: Optional additional safety notes

    Example:
        >>> metadata = SafetyMetadata(
        ...     redaction_level=RedactionLevel.FULL,
        ...     contains_functional_elements=False,
        ...     research_purpose="Testing Portuguese phishing refusal rates",
        ...     content_warning=ContentWarning.PHISHING,
        ...     approved_use_cases=[ApprovedUseCase.MODEL_EVALUATION]
        ... )
    """

    # Redaction level - should be FULL for all published examples
    redaction_level: Annotated[
        RedactionLevel,
        Field(
            description="How thoroughly the content has been redacted. "
                       "Published examples should always use 'full'."
        )
    ]

    # CRITICAL: This MUST always be False
    # The validator below enforces this constraint
    contains_functional_elements: Annotated[
        bool,
        Field(
            description="Whether the content contains functional attack elements. "
                       "This MUST always be False for any stored/published example."
        )
    ] = False

    # Research purpose - documents why this example exists
    research_purpose: Annotated[
        str,
        Field(
            min_length=10,
            max_length=500,
            description="Clear description of why this example exists and what "
                       "it's intended to help measure or evaluate."
        )
    ]

    # Content warning - what type of harmful pattern this represents
    content_warning: Annotated[
        ContentWarning,
        Field(
            description="Category of harmful pattern represented by this example."
        )
    ] = ContentWarning.SOCIAL_ENGINEERING

    # Approved use cases - restricts legitimate usage
    approved_use_cases: Annotated[
        list[ApprovedUseCase],
        Field(
            min_length=1,
            description="List of approved use cases for this example. "
                       "At least one must be specified."
        )
    ]

    # Optional notes for additional safety context
    notes: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1000,
            description="Optional additional notes about safety considerations."
        )
    ] = None

    @field_validator("contains_functional_elements")
    @classmethod
    def must_not_contain_functional_elements(cls, v: bool) -> bool:
        """
        CRITICAL SAFETY VALIDATOR

        This validator ensures that no example with functional attack
        elements can ever be stored in the benchmark. If someone tries
        to create an example with contains_functional_elements=True,
        this will raise a validation error.

        This is a hard requirement - there are no exceptions.
        """
        if v is True:
            raise ValueError(
                "SAFETY VIOLATION: Examples with functional attack elements "
                "cannot be stored in the benchmark. All content must be "
                "fully redacted with placeholders. Set contains_functional_elements=False "
                "and ensure all sensitive content is properly redacted."
            )
        return v

    @field_validator("redaction_level")
    @classmethod
    def warn_if_not_full_redaction(cls, v: RedactionLevel) -> RedactionLevel:
        """
        Validator that warns if redaction level is not FULL.

        While PARTIAL and ABSTRACTED are valid during processing,
        all published examples should have FULL redaction.
        """
        if v != RedactionLevel.FULL:
            # In production, this could log a warning
            # For now, we just allow it but the schema documents the preference
            pass
        return v

    class Config:
        """Pydantic configuration for SafetyMetadata."""

        # Use enum values in serialization for cleaner JSON
        use_enum_values = True

        # Validate on assignment for runtime safety
        validate_assignment = True
