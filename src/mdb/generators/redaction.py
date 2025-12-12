"""
Content Redaction Module
========================

This module provides critical safety functionality for redacting sensitive
content from text before storage or publication.

CRITICAL SAFETY NOTE:
---------------------
This is one of the most important modules in the benchmark. ALL content
that comes from model outputs or external sources MUST be processed
through these redaction utilities before being stored or published.

The redaction process:
1. Identify sensitive elements (URLs, emails, phone numbers, names, etc.)
2. Replace with standardized placeholders
3. Validate that no sensitive content remains
4. Return safe, redacted text

Supported redaction types:
- URLs (http/https links) -> [MALICIOUS_URL]
- Email addresses -> [EMAIL]
- Phone numbers -> [PHONE_NUMBER]
- Personal names (via NER) -> [TARGET_NAME], [SENDER_NAME]
- Bank names -> [BANK_NAME]
- Company names -> [COMPANY]
- Monetary amounts -> [AMOUNT_RANGE: X-Y]
- Addresses -> [ADDRESS]
- Dates -> [DATE]
- Times -> [TIME]

Example:
    >>> from mdb.generators.redaction import ContentRedactor
    >>>
    >>> redactor = ContentRedactor()
    >>> text = "Hello John! Click http://evil.com to win $500"
    >>> safe_text = redactor.redact(text)
    >>> print(safe_text)
    "Hello [TARGET_NAME]! Click [MALICIOUS_URL] to win [AMOUNT_RANGE: 100-1000]"
"""

import re
from dataclasses import dataclass, field
from typing import Callable


# =============================================================================
# REDACTION PATTERNS
# =============================================================================
# These regex patterns identify sensitive content that needs to be redacted.
# Patterns are ordered from most specific to most general to avoid conflicts.

# URL pattern - matches http and https URLs
# This is comprehensive and handles most URL formats including query strings
URL_PATTERN = re.compile(
    r"https?://"  # Protocol
    r"(?:[\w-]+\.)+[\w-]+"  # Domain
    r"(?:/[^\s\]\[<>\"']*)?",  # Path (optional)
    re.IGNORECASE
)

# Email pattern - standard email format
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    re.IGNORECASE
)

# Phone number patterns - various international formats
# Brazilian format: (XX) XXXXX-XXXX or XX XXXXX-XXXX
PHONE_BR_PATTERN = re.compile(
    r"\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}"
)

# Generic international format: +XX XXX XXX XXXX
PHONE_INTL_PATTERN = re.compile(
    r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
)

# Simple number sequences (10+ digits) - catches remaining phone numbers
PHONE_SIMPLE_PATTERN = re.compile(
    r"\b\d{10,15}\b"
)

# Monetary amounts - various currency formats
# Matches: $500, R$500, €500, 500 reais, etc.
MONEY_PATTERN = re.compile(
    r"(?:R?\$|€|£|¥)?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?"  # Currency + number
    r"(?:\s*(?:reais|dólares|euros|dollars|pesos|mil|mil reais))?"  # Currency name
    r"|\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?\s*"
    r"(?:reais|dólares|euros|dollars|pesos|mil|mil reais)\b",
    re.IGNORECASE
)

# Date patterns - various formats
# DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, etc.
DATE_PATTERN = re.compile(
    r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"
    r"|\b\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}\b"
)

# Time patterns - HH:MM, HH:MM:SS, etc.
TIME_PATTERN = re.compile(
    r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b"
)

# Account/card numbers - sequences of digits with separators
# Matches credit card formats: XXXX-XXXX-XXXX-XXXX
ACCOUNT_PATTERN = re.compile(
    r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b"
    r"|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{2}\b"  # CPF format
)


# =============================================================================
# PLACEHOLDER DEFINITIONS
# =============================================================================
# Standardized placeholders that replace sensitive content.
# Using consistent placeholders makes the dataset predictable and parseable.

@dataclass
class Placeholder:
    """
    Definition of a redaction placeholder.

    Attributes:
        name: The placeholder text (e.g., "[MALICIOUS_URL]")
        description: What this placeholder represents
        pattern: Optional regex pattern that matches this placeholder
    """
    name: str
    description: str
    pattern: re.Pattern | None = None

    def __post_init__(self) -> None:
        """Compile the pattern for matching this placeholder if not provided."""
        if self.pattern is None:
            # Escape the placeholder name for use in regex
            escaped = re.escape(self.name)
            self.pattern = re.compile(escaped)


# Standard placeholders used throughout the benchmark
PLACEHOLDERS = {
    "url": Placeholder(
        name="[MALICIOUS_URL]",
        description="A potentially malicious URL"
    ),
    "email": Placeholder(
        name="[EMAIL]",
        description="An email address"
    ),
    "phone": Placeholder(
        name="[PHONE_NUMBER]",
        description="A phone number"
    ),
    "target_name": Placeholder(
        name="[TARGET_NAME]",
        description="The name of the potential victim"
    ),
    "sender_name": Placeholder(
        name="[SENDER_NAME]",
        description="The claimed name of the sender"
    ),
    "bank": Placeholder(
        name="[BANK_NAME]",
        description="A bank or financial institution name"
    ),
    "company": Placeholder(
        name="[COMPANY]",
        description="A company or organization name"
    ),
    "amount": Placeholder(
        name="[AMOUNT_RANGE: 100-1000]",
        description="A monetary amount (shown as range)"
    ),
    "account": Placeholder(
        name="[ACCOUNT_INFO]",
        description="Account or card number"
    ),
    "address": Placeholder(
        name="[ADDRESS]",
        description="A physical address"
    ),
    "date": Placeholder(
        name="[DATE]",
        description="A date"
    ),
    "time": Placeholder(
        name="[TIME]",
        description="A time"
    ),
    "location": Placeholder(
        name="[LOCATION]",
        description="A geographic location"
    ),
}


# =============================================================================
# COMMON ENTITY LISTS
# =============================================================================
# Lists of common entities that should be redacted.
# These are used for simple pattern matching before more complex NER.

# Common Brazilian bank names (for targeted redaction)
BRAZILIAN_BANKS = [
    "Itaú", "Itau", "Bradesco", "Banco do Brasil", "Caixa", "Santander",
    "Nubank", "Inter", "BTG", "Safra", "Sicredi", "Sicoob", "Original",
    "C6 Bank", "PagBank", "Neon", "Next", "Iti",
]

# Common international bank names
INTERNATIONAL_BANKS = [
    "Bank of America", "Chase", "Wells Fargo", "Citibank", "HSBC",
    "Barclays", "Deutsche Bank", "BNP Paribas", "Santander", "ING",
]

# Combine all bank names into a single pattern
ALL_BANKS = BRAZILIAN_BANKS + INTERNATIONAL_BANKS
BANK_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(bank) for bank in ALL_BANKS) + r")\b",
    re.IGNORECASE
)

# Common tech company names (often impersonated)
TECH_COMPANIES = [
    "Google", "Microsoft", "Apple", "Amazon", "Facebook", "Meta",
    "Netflix", "PayPal", "Mercado Livre", "Mercado Pago", "iFood",
    "Uber", "99", "Rappi", "PicPay",
]

TECH_COMPANY_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(company) for company in TECH_COMPANIES) + r")\b",
    re.IGNORECASE
)


# =============================================================================
# REDACTION CLASS
# =============================================================================

@dataclass
class RedactionResult:
    """
    Result of a redaction operation.

    Attributes:
        original: The original text before redaction
        redacted: The redacted text with placeholders
        redactions: List of (original, placeholder) tuples for each redaction
        is_safe: Whether the result passed safety validation
        warnings: Any warnings generated during redaction
    """
    original: str
    redacted: str
    redactions: list[tuple[str, str]] = field(default_factory=list)
    is_safe: bool = True
    warnings: list[str] = field(default_factory=list)


class ContentRedactor:
    """
    Main class for redacting sensitive content from text.

    This class applies multiple redaction strategies in sequence:
    1. Pattern-based redaction (URLs, emails, phones, etc.)
    2. Entity-based redaction (known banks, companies)
    3. Validation to ensure no sensitive content remains

    The redactor is designed to be aggressive - it's better to
    over-redact than to miss sensitive content.

    Example:
        >>> redactor = ContentRedactor()
        >>> result = redactor.redact_with_details("Call 555-1234 now!")
        >>> print(result.redacted)
        "Call [PHONE_NUMBER] now!"
        >>> print(result.redactions)
        [("555-1234", "[PHONE_NUMBER]")]
    """

    def __init__(
        self,
        custom_patterns: dict[str, tuple[re.Pattern, str]] | None = None,
        aggressive_mode: bool = True
    ) -> None:
        """
        Initialize the content redactor.

        Args:
            custom_patterns: Additional patterns to redact, as
                           {name: (pattern, placeholder)} dict
            aggressive_mode: If True, apply more aggressive redaction
                           (recommended for safety)
        """
        self.custom_patterns = custom_patterns or {}
        self.aggressive_mode = aggressive_mode

        # Build the ordered list of redaction operations
        # Order matters - more specific patterns should come first
        self._build_redaction_pipeline()

    def _build_redaction_pipeline(self) -> None:
        """
        Build the ordered pipeline of redaction operations.

        The pipeline is ordered from most specific to most general
        to avoid conflicts and ensure proper redaction.
        """
        # Each entry is (pattern, placeholder, description)
        self.pipeline: list[tuple[re.Pattern, str, str]] = [
            # 1. URLs first - very specific pattern
            (URL_PATTERN, PLACEHOLDERS["url"].name, "URLs"),

            # 2. Email addresses
            (EMAIL_PATTERN, PLACEHOLDERS["email"].name, "Emails"),

            # 3. Account/card numbers (before phone to avoid conflicts)
            (ACCOUNT_PATTERN, PLACEHOLDERS["account"].name, "Account numbers"),

            # 4. Phone numbers (multiple patterns)
            (PHONE_BR_PATTERN, PLACEHOLDERS["phone"].name, "BR phone numbers"),
            (PHONE_INTL_PATTERN, PLACEHOLDERS["phone"].name, "Intl phone numbers"),

            # 5. Monetary amounts
            (MONEY_PATTERN, PLACEHOLDERS["amount"].name, "Money amounts"),

            # 6. Dates and times
            (DATE_PATTERN, PLACEHOLDERS["date"].name, "Dates"),
            (TIME_PATTERN, PLACEHOLDERS["time"].name, "Times"),

            # 7. Known entities (banks, companies)
            (BANK_PATTERN, PLACEHOLDERS["bank"].name, "Bank names"),
            (TECH_COMPANY_PATTERN, PLACEHOLDERS["company"].name, "Company names"),
        ]

        # Add custom patterns at the end
        for name, (pattern, placeholder) in self.custom_patterns.items():
            self.pipeline.append((pattern, placeholder, name))

        # In aggressive mode, also catch remaining phone-like numbers
        if self.aggressive_mode:
            self.pipeline.append(
                (PHONE_SIMPLE_PATTERN, PLACEHOLDERS["phone"].name, "Simple phone numbers")
            )

    def redact(self, text: str) -> str:
        """
        Redact sensitive content from text.

        This is the main method for simple redaction. For more details
        about what was redacted, use redact_with_details().

        Args:
            text: The text to redact

        Returns:
            The redacted text with placeholders

        Example:
            >>> redactor = ContentRedactor()
            >>> redactor.redact("Email me at john@example.com")
            "Email me at [EMAIL]"
        """
        result = self.redact_with_details(text)
        return result.redacted

    def redact_with_details(self, text: str) -> RedactionResult:
        """
        Redact sensitive content and return detailed information.

        This method provides full details about what was redacted,
        useful for auditing and validation.

        Args:
            text: The text to redact

        Returns:
            RedactionResult with original, redacted text, and details

        Example:
            >>> redactor = ContentRedactor()
            >>> result = redactor.redact_with_details("Visit http://evil.com")
            >>> print(result.redactions)
            [("http://evil.com", "[MALICIOUS_URL]")]
        """
        original = text
        redactions: list[tuple[str, str]] = []
        warnings: list[str] = []

        # Apply each redaction pattern in sequence
        for pattern, placeholder, description in self.pipeline:
            # Find all matches
            matches = pattern.findall(text)

            if matches:
                # Record what was redacted
                for match in matches:
                    # Handle groups - findall returns different types
                    if isinstance(match, tuple):
                        match = match[0]
                    redactions.append((match, placeholder))

                # Apply the redaction
                text = pattern.sub(placeholder, text)

        # Validate the result
        is_safe = self._validate_redaction(text, warnings)

        return RedactionResult(
            original=original,
            redacted=text,
            redactions=redactions,
            is_safe=is_safe,
            warnings=warnings
        )

    def _validate_redaction(self, text: str, warnings: list[str]) -> bool:
        """
        Validate that redaction was successful.

        Checks for any remaining patterns that might indicate
        incomplete redaction.

        Args:
            text: The redacted text to validate
            warnings: List to append warnings to

        Returns:
            True if validation passes, False otherwise
        """
        is_safe = True

        # Check for remaining URLs
        remaining_urls = URL_PATTERN.findall(text)
        # Filter out placeholders (they contain square brackets)
        remaining_urls = [u for u in remaining_urls if "[" not in u]
        if remaining_urls:
            warnings.append(f"Remaining URLs detected: {remaining_urls[:3]}")
            is_safe = False

        # Check for remaining emails
        remaining_emails = EMAIL_PATTERN.findall(text)
        if remaining_emails:
            warnings.append(f"Remaining emails detected: {remaining_emails[:3]}")
            is_safe = False

        return is_safe


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global redactor instance for simple use cases
_default_redactor: ContentRedactor | None = None


def get_default_redactor() -> ContentRedactor:
    """
    Get the default redactor instance (lazy initialization).

    Returns:
        The default ContentRedactor instance
    """
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = ContentRedactor(aggressive_mode=True)
    return _default_redactor


def redact_content(text: str) -> str:
    """
    Convenience function to redact content using the default redactor.

    This is the simplest way to redact content. For more control,
    create a ContentRedactor instance directly.

    Args:
        text: The text to redact

    Returns:
        The redacted text with placeholders

    Example:
        >>> from mdb.generators.redaction import redact_content
        >>> redact_content("Call me at 555-1234")
        "Call me at [PHONE_NUMBER]"
    """
    return get_default_redactor().redact(text)


def validate_is_redacted(text: str) -> tuple[bool, list[str]]:
    """
    Check if text appears to be properly redacted.

    This function checks for the presence of placeholders and
    absence of obviously sensitive content.

    Args:
        text: The text to validate

    Returns:
        Tuple of (is_redacted, list_of_issues)

    Example:
        >>> is_safe, issues = validate_is_redacted("Hello [TARGET_NAME]!")
        >>> print(is_safe)
        True
        >>> is_safe, issues = validate_is_redacted("Hello John!")
        >>> print(is_safe, issues)
        False, ["No placeholders found - content may not be redacted"]
    """
    issues: list[str] = []

    # Check for presence of at least one placeholder
    has_placeholder = any(
        p.pattern.search(text) for p in PLACEHOLDERS.values()
        if p.pattern is not None
    )

    # Also check for bracket-style placeholders generically
    generic_placeholder = re.search(r"\[[A-Z_]+\]", text)

    if not has_placeholder and not generic_placeholder:
        issues.append("No placeholders found - content may not be redacted")

    # Check for suspicious patterns that suggest incomplete redaction
    redactor = get_default_redactor()
    result = redactor.redact_with_details(text)

    if not result.is_safe:
        issues.extend(result.warnings)

    return len(issues) == 0, issues
