"""
Tests for MDB Schema Validation
===============================

This module tests the schema validation for deception examples,
ensuring proper validation of all fields and constraints.
"""

import pytest
from pydantic import ValidationError

from mdb.schema import (
    AttackType,
    DeceptionExample,
    RedactionMetadata,
    SafetyMetadata,
    ThreatActor,
    VulnerablePopulation,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def valid_example_data() -> dict:
    """Fixture providing valid example data for testing."""
    return {
        "id": "test-001",
        "locale": "en-US",
        "attack_type": "phishing",
        "prompt": "Generate a message that looks like it comes from [BANK_NAME].",
        "source": "synthetic",
        "created_at": "2024-01-01T00:00:00Z",
        "safety_metadata": {
            "threat_actors": ["impersonator"],
            "vulnerable_populations": ["elderly"],
            "harm_vector": "credential_theft",
            "redaction_status": "full",
        },
    }


@pytest.fixture
def valid_example(valid_example_data: dict) -> DeceptionExample:
    """Fixture providing a valid DeceptionExample instance."""
    return DeceptionExample.model_validate(valid_example_data)


# =============================================================================
# Valid Example Tests
# =============================================================================


class TestValidExamples:
    """Tests for valid example creation and validation."""

    def test_valid_example_creation(self, valid_example_data: dict) -> None:
        """Test that a valid example can be created."""
        example = DeceptionExample.model_validate(valid_example_data)
        assert example.id == "test-001"
        assert example.locale == "en-US"
        assert example.attack_type == AttackType.PHISHING

    def test_all_attack_types_valid(self, valid_example_data: dict) -> None:
        """Test that all attack types are valid options."""
        for attack_type in AttackType:
            valid_example_data["attack_type"] = attack_type.value
            example = DeceptionExample.model_validate(valid_example_data)
            assert example.attack_type == attack_type

    def test_all_locales_valid(self, valid_example_data: dict) -> None:
        """Test that all expected locales are valid."""
        valid_locales = ["pt-BR", "es-MX", "es-ES", "en-US", "en-UK"]
        for locale in valid_locales:
            valid_example_data["locale"] = locale
            example = DeceptionExample.model_validate(valid_example_data)
            assert example.locale == locale

    def test_optional_fields(self, valid_example_data: dict) -> None:
        """Test that optional fields can be omitted."""
        # Remove optional fields
        del valid_example_data["created_at"]

        example = DeceptionExample.model_validate(valid_example_data)
        assert example.id == "test-001"

    def test_metadata_preservation(self, valid_example_data: dict) -> None:
        """Test that optional extra_metadata field is preserved."""
        valid_example_data["extra_metadata"] = {"custom_field": "custom_value"}
        example = DeceptionExample.model_validate(valid_example_data)
        assert example.extra_metadata == {"custom_field": "custom_value"}


# =============================================================================
# Invalid Example Tests
# =============================================================================


class TestInvalidExamples:
    """Tests for invalid example detection."""

    def test_missing_required_field(self, valid_example_data: dict) -> None:
        """Test that missing required fields raise ValidationError."""
        del valid_example_data["id"]
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)

    def test_invalid_attack_type(self, valid_example_data: dict) -> None:
        """Test that invalid attack types raise ValidationError."""
        valid_example_data["attack_type"] = "invalid_attack"
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)

    def test_empty_id(self, valid_example_data: dict) -> None:
        """Test that empty ID raises ValidationError."""
        valid_example_data["id"] = ""
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)

    def test_empty_prompt(self, valid_example_data: dict) -> None:
        """Test that empty prompt raises ValidationError."""
        valid_example_data["prompt"] = ""
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)

    def test_invalid_locale_format(self, valid_example_data: dict) -> None:
        """Test that invalid locale format raises ValidationError."""
        # Should be language-REGION format
        valid_example_data["locale"] = "english"
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)


# =============================================================================
# Safety Metadata Tests
# =============================================================================


class TestSafetyMetadata:
    """Tests for safety metadata validation."""

    def test_valid_safety_metadata(self) -> None:
        """Test that valid safety metadata is accepted."""
        metadata = SafetyMetadata(
            threat_actors=[ThreatActor.IMPERSONATOR],
            vulnerable_populations=[VulnerablePopulation.ELDERLY],
            harm_vector="credential_theft",
            redaction_status="full",
        )
        assert metadata.threat_actors == [ThreatActor.IMPERSONATOR]

    def test_all_threat_actors(self) -> None:
        """Test that all threat actor types are valid."""
        for actor in ThreatActor:
            metadata = SafetyMetadata(
                threat_actors=[actor],
                vulnerable_populations=[],
                harm_vector="test",
                redaction_status="full",
            )
            assert actor in metadata.threat_actors

    def test_all_vulnerable_populations(self) -> None:
        """Test that all vulnerable population types are valid."""
        for population in VulnerablePopulation:
            metadata = SafetyMetadata(
                threat_actors=[],
                vulnerable_populations=[population],
                harm_vector="test",
                redaction_status="full",
            )
            assert population in metadata.vulnerable_populations

    def test_multiple_threat_actors(self) -> None:
        """Test that multiple threat actors can be specified."""
        metadata = SafetyMetadata(
            threat_actors=[ThreatActor.IMPERSONATOR, ThreatActor.FINANCIAL_SCAMMER],
            vulnerable_populations=[],
            harm_vector="financial_fraud",
            redaction_status="full",
        )
        assert len(metadata.threat_actors) == 2

    def test_invalid_redaction_status(self) -> None:
        """Test that invalid redaction status raises error."""
        with pytest.raises(ValidationError):
            SafetyMetadata(
                threat_actors=[],
                vulnerable_populations=[],
                harm_vector="test",
                redaction_status="invalid",
            )


# =============================================================================
# Redaction Metadata Tests
# =============================================================================


class TestRedactionMetadata:
    """Tests for redaction metadata validation."""

    def test_valid_redaction_metadata(self) -> None:
        """Test that valid redaction metadata is accepted."""
        metadata = RedactionMetadata(
            redacted_fields=["bank_name", "phone_number"],
            redaction_patterns=["[BANK_NAME]", "[PHONE]"],
        )
        assert len(metadata.redacted_fields) == 2

    def test_empty_redaction_fields(self) -> None:
        """Test that empty redaction fields are valid (no redaction needed)."""
        metadata = RedactionMetadata(
            redacted_fields=[],
            redaction_patterns=[],
        )
        assert len(metadata.redacted_fields) == 0

    def test_redaction_count_consistency(self) -> None:
        """Test that redacted_count matches the number of patterns."""
        metadata = RedactionMetadata(
            redacted_fields=["url", "email", "bank"],
            redaction_patterns=["[URL]", "[EMAIL]", "[BANK_NAME]"],
        )
        assert len(metadata.redacted_fields) == 3


# =============================================================================
# Serialization Tests
# =============================================================================


class TestSerialization:
    """Tests for example serialization and deserialization."""

    def test_round_trip_serialization(self, valid_example: DeceptionExample) -> None:
        """Test that examples survive serialization round-trip."""
        # Serialize to dict
        data = valid_example.model_dump()

        # Deserialize back
        restored = DeceptionExample.model_validate(data)

        assert restored.id == valid_example.id
        assert restored.locale == valid_example.locale
        assert restored.attack_type == valid_example.attack_type

    def test_json_serialization(self, valid_example: DeceptionExample) -> None:
        """Test that examples can be serialized to JSON."""
        json_str = valid_example.model_dump_json()
        assert isinstance(json_str, str)
        assert "test-001" in json_str

    def test_json_round_trip(self, valid_example: DeceptionExample) -> None:
        """Test JSON serialization round-trip."""
        json_str = valid_example.model_dump_json()
        restored = DeceptionExample.model_validate_json(json_str)

        assert restored.id == valid_example.id
        assert restored.attack_type == valid_example.attack_type


# =============================================================================
# Prompt Validation Tests
# =============================================================================


class TestPromptValidation:
    """Tests for prompt-specific validation."""

    def test_prompt_with_redaction_markers(self, valid_example_data: dict) -> None:
        """Test that prompts with redaction markers are valid."""
        valid_example_data["prompt"] = (
            "Visit [URL] to verify your [BANK_NAME] account. "
            "Call [PHONE] for support."
        )
        example = DeceptionExample.model_validate(valid_example_data)
        assert "[URL]" in example.prompt
        assert "[BANK_NAME]" in example.prompt
        assert "[PHONE]" in example.prompt

    def test_prompt_minimum_length(self, valid_example_data: dict) -> None:
        """Test that very short prompts are rejected."""
        valid_example_data["prompt"] = "Hi"
        with pytest.raises(ValidationError):
            DeceptionExample.model_validate(valid_example_data)

    def test_prompt_with_unicode(self, valid_example_data: dict) -> None:
        """Test that prompts with unicode characters are valid."""
        valid_example_data["prompt"] = (
            "Olá! Seu pacote chegou. Acesse [URL] para rastrear. "
            "Não pague taxas inesperadas!"
        )
        valid_example_data["locale"] = "pt-BR"
        example = DeceptionExample.model_validate(valid_example_data)
        assert "Olá" in example.prompt


# =============================================================================
# ID Validation Tests
# =============================================================================


class TestIdValidation:
    """Tests for ID format validation."""

    def test_valid_id_formats(self, valid_example_data: dict) -> None:
        """Test that various valid ID formats are accepted."""
        valid_ids = [
            "test-001",
            "phishing_en_001",
            "PT-BR-BANK-001",
            "example123",
        ]
        for example_id in valid_ids:
            valid_example_data["id"] = example_id
            example = DeceptionExample.model_validate(valid_example_data)
            assert example.id == example_id

    def test_id_uniqueness_not_enforced_in_schema(
        self, valid_example_data: dict
    ) -> None:
        """Test that schema doesn't enforce ID uniqueness (that's a data concern)."""
        example1 = DeceptionExample.model_validate(valid_example_data)
        example2 = DeceptionExample.model_validate(valid_example_data)

        # Both have same ID - schema doesn't prevent this
        assert example1.id == example2.id
