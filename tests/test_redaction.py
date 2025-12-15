"""
Tests for MDB Redaction Utilities
=================================

This module tests the redaction utilities that remove sensitive
information from deception examples before publication.
"""

import pytest

from mdb.generators.redaction import (
    PLACEHOLDERS,
    URL_PATTERN,
    EMAIL_PATTERN,
    PHONE_BR_PATTERN,
    PHONE_INTL_PATTERN,
    BANK_PATTERN,
    ContentRedactor,
    RedactionResult,
    redact_content,
    validate_is_redacted,
)


# =============================================================================
# Pattern Detection Tests
# =============================================================================


class TestPatternDetection:
    """Tests for detecting sensitive patterns in text."""

    def test_url_detection(self) -> None:
        """Test that URLs are detected."""
        text = "Visit https://example.com/login for details"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted
        assert len(result.redactions) > 0

    def test_http_url_detection(self) -> None:
        """Test that HTTP URLs are detected."""
        text = "Go to http://malicious-site.com now"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted

    def test_email_detection(self) -> None:
        """Test that email addresses are detected."""
        text = "Contact support@example.com for help"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[EMAIL]" in result.redacted

    def test_phone_detection_br(self) -> None:
        """Test that Brazilian phone formats are detected."""
        text = "Ligue para (11) 99999-1234 agora"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[PHONE_NUMBER]" in result.redacted

    def test_phone_detection_intl(self) -> None:
        """Test that international phone formats are detected."""
        text = "Contact +55 11 99999-8888 now"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[PHONE_NUMBER]" in result.redacted


# =============================================================================
# Entity Redaction Tests
# =============================================================================


class TestEntityRedaction:
    """Tests for entity-specific redaction."""

    def test_bank_name_redaction(self) -> None:
        """Test that common bank names are redacted."""
        # Brazilian banks
        text = "Seu cartão do Banco do Brasil foi bloqueado"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[BANK_NAME]" in result.redacted

    def test_tech_company_redaction(self) -> None:
        """Test that tech company names are redacted."""
        text = "Sua conta do Google foi comprometida"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[COMPANY]" in result.redacted

    def test_placeholder_preservation(self) -> None:
        """Test that already-redacted placeholders are preserved."""
        text = "O [COMPANY] confirmou sua transação"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        # Already redacted, should remain
        assert "[COMPANY]" in result.redacted


# =============================================================================
# Complete Redaction Tests
# =============================================================================


class TestCompleteRedaction:
    """Tests for complete redaction scenarios."""

    def test_multiple_patterns(self) -> None:
        """Test that multiple patterns in one text are all redacted."""
        text = (
            "Acesse https://banco.fake.com ou ligue (11) 99999-1234. "
            "Email: suporte@banco.fake.com"
        )
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted
        assert "[PHONE_NUMBER]" in result.redacted
        assert "[EMAIL]" in result.redacted

    def test_redaction_count(self) -> None:
        """Test that redactions are tracked."""
        text = "Email: a@b.com and b@c.com"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        # Should have redactions recorded
        assert len(result.redactions) >= 1

    def test_already_redacted_text(self) -> None:
        """Test that already-redacted text doesn't add new redactions for placeholders."""
        text = "Acesse [MALICIOUS_URL] e ligue para [PHONE_NUMBER]"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        # Should have no URL/email patterns detected
        assert result.is_safe


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_redact_content_function(self) -> None:
        """Test the redact_content convenience function."""
        text = "Call 555-1234 and visit http://example.com"
        result = redact_content(text)
        assert "[MALICIOUS_URL]" in result
        # Phone might be redacted depending on pattern match

    def test_validate_is_redacted_clean(self) -> None:
        """Test validation of properly redacted text."""
        text = "Acesse [MALICIOUS_URL] para verificar sua conta [BANK_NAME]"
        is_safe, issues = validate_is_redacted(text)
        assert is_safe
        assert len(issues) == 0

    def test_validate_is_redacted_with_url(self) -> None:
        """Test that text with URL fails validation."""
        text = "Visit https://malicious.com now"
        is_safe, issues = validate_is_redacted(text)
        assert not is_safe
        assert len(issues) > 0


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases in redaction."""

    def test_empty_text(self) -> None:
        """Test redaction of empty text."""
        redactor = ContentRedactor()
        result = redactor.redact_with_details("")
        assert result.redacted == ""
        assert len(result.redactions) == 0

    def test_text_without_patterns(self) -> None:
        """Test text that needs no redaction."""
        text = "Esta é uma mensagem genérica sem informações sensíveis"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert result.redacted == text
        assert len(result.redactions) == 0

    def test_unicode_text(self) -> None:
        """Test redaction in unicode text."""
        text = "Olá! Acesse https://exemplo.com.br para más información"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted
        # Original unicode characters should be preserved
        assert "Olá" in result.redacted

    def test_multiline_text(self) -> None:
        """Test redaction across multiple lines."""
        text = """Prezado cliente,

        Acesse https://banco.fake.com
        Ou ligue: (11) 99999-1234

        Atenciosamente"""
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted
        assert "[PHONE_NUMBER]" in result.redacted


# =============================================================================
# Pattern Tests
# =============================================================================


class TestPatterns:
    """Tests for redaction patterns."""

    def test_url_pattern_matches(self) -> None:
        """Test URL pattern matching."""
        test_urls = [
            "https://example.com",
            "http://malicious.net/path",
            "https://sub.domain.com/path?query=1",
        ]
        for url in test_urls:
            match = URL_PATTERN.search(url)
            assert match is not None, f"URL pattern should match: {url}"

    def test_email_pattern_matches(self) -> None:
        """Test email pattern matching."""
        test_emails = [
            "test@example.com",
            "user.name@domain.org",
            "admin@sub.domain.co.uk",
        ]
        for email in test_emails:
            match = EMAIL_PATTERN.search(email)
            assert match is not None, f"Email pattern should match: {email}"

    def test_phone_br_pattern_matches(self) -> None:
        """Test Brazilian phone pattern matching."""
        test_phones = [
            "(11) 99999-1234",
            "11 99999-1234",
            "(21) 3456-7890",
        ]
        for phone in test_phones:
            match = PHONE_BR_PATTERN.search(phone)
            assert match is not None, f"BR phone pattern should match: {phone}"


# =============================================================================
# Language-Specific Tests
# =============================================================================


class TestLanguageSpecific:
    """Tests for language-specific redaction."""

    def test_portuguese_text(self) -> None:
        """Test redaction in Portuguese text."""
        text = (
            "Seu CPF foi bloqueado. Acesse https://receita.fake.gov.br "
            "ou ligue (11) 3003-1234"
        )
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted
        assert "[PHONE_NUMBER]" in result.redacted

    def test_spanish_text(self) -> None:
        """Test redaction in Spanish text."""
        text = (
            "Tu cuenta ha sido suspendida. Visita https://banco.fake.mx "
            "o llama al +52 55 1234 5678"
        )
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted

    def test_mixed_language_text(self) -> None:
        """Test redaction in mixed-language text."""
        text = (
            "Dear customer, su cuenta está bloqueada. "
            "Visit https://support.example.com for help."
        )
        redactor = ContentRedactor()
        result = redactor.redact_with_details(text)
        assert "[MALICIOUS_URL]" in result.redacted


# =============================================================================
# Result Object Tests
# =============================================================================


class TestRedactionResult:
    """Tests for RedactionResult object."""

    def test_result_fields(self) -> None:
        """Test that result has all expected fields."""
        redactor = ContentRedactor()
        result = redactor.redact_with_details("Test https://example.com")
        assert hasattr(result, "redacted")
        assert hasattr(result, "redactions")
        assert hasattr(result, "original")
        assert hasattr(result, "is_safe")
        assert hasattr(result, "warnings")

    def test_result_preserves_original(self) -> None:
        """Test that result preserves original text."""
        original = "Contact test@email.com"
        redactor = ContentRedactor()
        result = redactor.redact_with_details(original)
        assert result.original == original
        assert result.redacted != original


# =============================================================================
# Placeholder Tests
# =============================================================================


class TestPlaceholders:
    """Tests for placeholder definitions."""

    def test_standard_placeholders_exist(self) -> None:
        """Test that standard placeholders are defined."""
        expected_keys = ["url", "email", "phone", "bank", "company"]
        for key in expected_keys:
            assert key in PLACEHOLDERS

    def test_placeholder_structure(self) -> None:
        """Test that placeholders have required attributes."""
        for key, placeholder in PLACEHOLDERS.items():
            assert hasattr(placeholder, "name")
            assert hasattr(placeholder, "description")
            assert placeholder.name.startswith("[")
            assert placeholder.name.endswith("]")
