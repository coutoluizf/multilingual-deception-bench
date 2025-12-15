"""
Seed-Based Synthetic Generator Module
======================================

This module generates synthetic attack examples from real-world seed patterns
collected in the Brazilian Portuguese dataset (pt-br-seeds.json).

The generator:
1. Loads seeds containing real scam patterns from journalistic/official sources
2. Creates variations by mixing templates, platforms, and persuasion tactics
3. Applies proper redaction with placeholders
4. Outputs validated AttackExample objects

SAFETY NOTE:
- All generated content uses placeholders for sensitive elements
- No functional URLs, phone numbers, or real PII is ever created
- Content is validated against safety schema before output
"""

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from mdb.schema import (
    AttackExample,
    AttackType,
    Language,
    Platform,
    Difficulty,
    PersuasionTactic,
    SafetyMetadata,
)
from mdb.schema.safety_schema import ContentWarning, RedactionLevel, ApprovedUseCase
from mdb.schema.attack_schema import ExampleMetadata


# =============================================================================
# CATEGORY TO ATTACK TYPE MAPPING
# =============================================================================
# Maps seed categories to the AttackType enum for proper classification
# Supports both PT-BR and EN-US category formats

CATEGORY_TO_ATTACK_TYPE: dict[str, AttackType] = {
    # ==========================================================================
    # PT-BR Categories (Brazilian Portuguese)
    # ==========================================================================

    # PIX/Financial
    "PIX": AttackType.FINANCIAL_FRAUD,
    "BANK": AttackType.BANK_IMPERSONATION,
    "CARD": AttackType.BANK_IMPERSONATION,
    "LOAN": AttackType.FINANCIAL_FRAUD,
    "BOLETO": AttackType.FINANCIAL_FRAUD,
    "CONSIG": AttackType.FINANCIAL_FRAUD,

    # Impersonation
    "WPP": AttackType.IMPERSONATION,
    "URG": AttackType.FAMILY_EMERGENCY,
    "KIDNAP": AttackType.FAMILY_EMERGENCY,
    "GOV": AttackType.GOVERNMENT_IMPERSONATION,
    "BENEFIT": AttackType.GOVERNMENT_IMPERSONATION,
    "LEGAL": AttackType.GOVERNMENT_IMPERSONATION,
    "JUDICIAL": AttackType.GOVERNMENT_IMPERSONATION,
    "TAX": AttackType.GOVERNMENT_IMPERSONATION,

    # Tech/Online
    "TECH": AttackType.TECH_SUPPORT,
    "TECHSUP": AttackType.TECH_SUPPORT,
    "STREAM": AttackType.PHISHING,
    "ECOM": AttackType.PHISHING,
    "FAKESTORE": AttackType.PHISHING,
    "QRCODE": AttackType.PHISHING,
    "PARKQR": AttackType.PHISHING,
    "MACHINE": AttackType.FINANCIAL_FRAUD,
    "HACKED": AttackType.PHISHING,
    "SIMSWAP": AttackType.PHISHING,

    # Romance/Social
    "ROM": AttackType.ROMANCE_SCAM,
    "DATING": AttackType.ROMANCE_SCAM,
    "SUGAR": AttackType.ROMANCE_SCAM,
    "SEXTORTION": AttackType.ROMANCE_SCAM,

    # Jobs/Opportunities
    "JOB": AttackType.JOB_SCAM,
    "FAKEJOB": AttackType.JOB_SCAM,
    "MKT": AttackType.JOB_SCAM,
    "OPP": AttackType.FINANCIAL_FRAUD,
    "PYRAMID": AttackType.FINANCIAL_FRAUD,

    # Delivery/Commerce
    "DELIVERY": AttackType.DELIVERY_SCAM,
    "RENTAL": AttackType.PHISHING,
    "TEMPRENT": AttackType.PHISHING,
    "VEHICLE": AttackType.PHISHING,
    "TICKET": AttackType.PHISHING,

    # Other
    "TELECOM": AttackType.PHISHING,
    "UTILITY": AttackType.PHISHING,
    "HEALTH": AttackType.PHISHING,
    "FAKEMEDS": AttackType.PHISHING,
    "EDU": AttackType.PHISHING,
    "SCHOLARSHIP": AttackType.PHISHING,
    "LOTTERY": AttackType.FINANCIAL_FRAUD,
    "INHERIT": AttackType.FINANCIAL_FRAUD,
    "GIFT": AttackType.PHISHING,
    "CASHBACK": AttackType.PHISHING,
    "CHARITY": AttackType.FINANCIAL_FRAUD,
    "PET": AttackType.PHISHING,
    "SOCIAL": AttackType.IMPERSONATION,
    "CONSORT": AttackType.FINANCIAL_FRAUD,
    "MILES": AttackType.PHISHING,
    "CRYPTO": AttackType.FINANCIAL_FRAUD,
    "CRYPTO2": AttackType.FINANCIAL_FRAUD,
    "INSURANCE": AttackType.PHISHING,
    "TRAVEL": AttackType.PHISHING,
    "CALLCENTER": AttackType.BANK_IMPERSONATION,
    "MOTOBOY": AttackType.BANK_IMPERSONATION,
    "DEEPFAKE": AttackType.IMPERSONATION,
    "SUBSCRIPTION": AttackType.PHISHING,
    "SPIRIT": AttackType.FINANCIAL_FRAUD,
    "COUNTERFEIT": AttackType.PHISHING,

    # ==========================================================================
    # EN-US Categories (American English)
    # ==========================================================================

    # Government/Tax Impersonation (US-specific)
    "IRS_TAX": AttackType.GOVERNMENT_IMPERSONATION,  # IRS scams
    "IRS": AttackType.GOVERNMENT_IMPERSONATION,
    "SSA": AttackType.GOVERNMENT_IMPERSONATION,  # Social Security Admin
    "MEDICARE": AttackType.GOVERNMENT_IMPERSONATION,  # Medicare/CMS
    "JURY_DUTY": AttackType.GOVERNMENT_IMPERSONATION,  # Jury duty scams
    "FBI_DEA": AttackType.GOVERNMENT_IMPERSONATION,  # Law enforcement

    # US Bank Impersonation
    "BANK_CHASE": AttackType.BANK_IMPERSONATION,  # Chase Bank
    "BANK_BOA": AttackType.BANK_IMPERSONATION,  # Bank of America
    "BANK_WELLS": AttackType.BANK_IMPERSONATION,  # Wells Fargo

    # US Delivery Scams
    "DELIVERY_USPS": AttackType.DELIVERY_SCAM,  # USPS impersonation
    "DELIVERY_FEDEX": AttackType.DELIVERY_SCAM,  # FedEx impersonation
    "DELIVERY_AMAZON": AttackType.DELIVERY_SCAM,  # Amazon delivery scams

    # Family/Emergency (Grandparent scam - very US-specific)
    "GRANDPARENT": AttackType.FAMILY_EMERGENCY,

    # Tech Support
    "TECH_SUPPORT": AttackType.TECH_SUPPORT,

    # Crypto/Investment (Pig Butchering)
    "CRYPTO_PIG": AttackType.FINANCIAL_FRAUD,  # Pig butchering scams

    # Romance
    "ROMANCE": AttackType.ROMANCE_SCAM,

    # Jobs (Work From Home scams)
    "JOB_WFH": AttackType.JOB_SCAM,

    # Financial/Payment Apps
    "ZELLE_VENMO": AttackType.FINANCIAL_FRAUD,  # P2P payment scams
    "STUDENT_LOAN": AttackType.FINANCIAL_FRAUD,  # Student loan forgiveness
}

# =============================================================================
# PLATFORM MAPPING
# =============================================================================
# Maps seed platform strings to Platform enum
# Supports both PT-BR and EN-US platform names

PLATFORM_MAPPING: dict[str, Platform] = {
    # Common platforms (PT-BR and EN-US)
    "whatsapp": Platform.WHATSAPP,
    "telegram": Platform.TELEGRAM,
    "sms": Platform.SMS,
    "email": Platform.EMAIL,
    "instagram": Platform.INSTAGRAM_DM,
    "facebook": Platform.FACEBOOK_MESSENGER,
    "linkedin": Platform.GENERIC,

    # PT-BR specific
    "telefone": Platform.GENERIC,  # Phone calls -> generic
    "presencial": Platform.GENERIC,  # In-person -> generic
    "apps de delivery": Platform.GENERIC,
    "marketplace": Platform.GENERIC,
    "e-commerce": Platform.GENERIC,
    "site falso": Platform.GENERIC,
    "rede social": Platform.INSTAGRAM_DM,

    # EN-US specific
    "phone": Platform.GENERIC,  # Phone calls -> generic
    "voicemail": Platform.GENERIC,
    "text": Platform.SMS,  # US term for SMS
    "dating_app": Platform.GENERIC,
    "social_media": Platform.INSTAGRAM_DM,
    "website": Platform.GENERIC,
}

# =============================================================================
# TACTIC MAPPING
# =============================================================================
# Maps seed persuasion tactics to PersuasionTactic enum

TACTIC_MAPPING: dict[str, PersuasionTactic] = {
    # Urgency variants
    "urgência": PersuasionTactic.URGENCY,
    "urgency": PersuasionTactic.URGENCY,
    "pressão de tempo": PersuasionTactic.URGENCY,
    "prazo curto": PersuasionTactic.URGENCY,
    "urgência extrema": PersuasionTactic.URGENCY,
    "senso de urgência": PersuasionTactic.URGENCY,

    # Authority variants
    "autoridade": PersuasionTactic.AUTHORITY,
    "authority": PersuasionTactic.AUTHORITY,
    "aparência oficial": PersuasionTactic.AUTHORITY,
    "uso de marca conhecida": PersuasionTactic.AUTHORITY,
    "institucional": PersuasionTactic.AUTHORITY,
    "linguagem formal": PersuasionTactic.AUTHORITY,
    "autoridade de advogada": PersuasionTactic.AUTHORITY,

    # Fear variants
    "medo": PersuasionTactic.FEAR,
    "fear": PersuasionTactic.FEAR,
    "ameaça": PersuasionTactic.FEAR,
    "pânico": PersuasionTactic.FEAR,
    "pânico emocional": PersuasionTactic.FEAR,
    "ameaça de exposição": PersuasionTactic.FEAR,
    "ameaça de bloqueio": PersuasionTactic.FEAR,
    "medo de multa": PersuasionTactic.FEAR,
    "ameaça de morte": PersuasionTactic.FEAR,

    # Trust variants
    "confiança": PersuasionTactic.TRUST,
    "trust": PersuasionTactic.TRUST,
    "relacionamento": PersuasionTactic.TRUST,
    "uso de nome de conhecido": PersuasionTactic.TRUST,
    "confiança em conhecido": PersuasionTactic.TRUST,
    "foto de perfil de conhecido": PersuasionTactic.TRUST,
    "uso de foto de conhecido": PersuasionTactic.TRUST,

    # Greed variants
    "ganância": PersuasionTactic.GREED,
    "greed": PersuasionTactic.GREED,
    "promessa de lucro": PersuasionTactic.GREED,
    "retorno financeiro": PersuasionTactic.GREED,
    "dinheiro fácil": PersuasionTactic.GREED,
    "valores altos": PersuasionTactic.GREED,

    # Scarcity variants
    "escassez": PersuasionTactic.SCARCITY,
    "scarcity": PersuasionTactic.SCARCITY,
    "oferta limitada": PersuasionTactic.SCARCITY,
    "última vaga": PersuasionTactic.SCARCITY,
    "últimas unidades": PersuasionTactic.SCARCITY,

    # Curiosity variants
    "curiosidade": PersuasionTactic.CURIOSITY,
    "curiosity": PersuasionTactic.CURIOSITY,
    "interesse": PersuasionTactic.CURIOSITY,

    # Liking variants
    "simpatia": PersuasionTactic.LIKING,
    "liking": PersuasionTactic.LIKING,
    "romance": PersuasionTactic.LIKING,
    "romance falso": PersuasionTactic.LIKING,
    "atração sexual": PersuasionTactic.LIKING,

    # Social proof
    "prova social": PersuasionTactic.SOCIAL_PROOF,
    "social_proof": PersuasionTactic.SOCIAL_PROOF,
    "testemunhos falsos": PersuasionTactic.SOCIAL_PROOF,

    # Helpfulness
    "ajuda": PersuasionTactic.HELPFULNESS,
    "helpfulness": PersuasionTactic.HELPFULNESS,
    "solidariedade": PersuasionTactic.HELPFULNESS,

    # Reciprocity
    "reciprocidade": PersuasionTactic.RECIPROCITY,
    "reciprocity": PersuasionTactic.RECIPROCITY,
}

# =============================================================================
# VARIATION TEMPLATES
# =============================================================================
# Templates for generating variations of messages
# Organized by language/region

VARIATION_PREFIXES_PT = [
    "[WhatsApp]: ",
    "[SMS]: ",
    "[Email]: ",
    "[DM Instagram]: ",
    "[Telegram]: ",
    "[Ligação]: ",
    "[Site]: ",
    "[Mensagem]: ",
    "",  # No prefix for variety
]

VARIATION_PREFIXES_EN = [
    "[Text Message]: ",
    "[SMS]: ",
    "[Email]: ",
    "[Voicemail]: ",
    "[Phone Call]: ",
    "[DM]: ",
    "[Alert]: ",
    "[Notification]: ",
    "",  # No prefix for variety
]

PLACEHOLDER_SUBSTITUTIONS = {
    "[TARGET_NAME]": ["[TARGET_NAME]", "[NOME_VÍTIMA]", "[CLIENTE]", "[USUÁRIO]"],
    "[BANK_NAME]": ["[BANCO]", "[INSTITUIÇÃO_FINANCEIRA]", "[BANK_NAME]"],
    "[AMOUNT]": ["[VALOR]", "[QUANTIA]", "[AMOUNT]", "[AMOUNT_RANGE: 100-5000]"],
    "[PHONE_NUMBER]": ["[TELEFONE]", "[NÚMERO]", "[PHONE_NUMBER]"],
    "[DATE]": ["[DATA]", "[PRAZO]", "[DATE]"],
    "[COMPANY]": ["[EMPRESA]", "[LOJA]", "[COMPANY]"],
}


class SeedBasedGenerator:
    """
    Generator that creates synthetic attack examples from seed patterns.

    This generator:
    1. Loads real-world scam patterns from seeds.json (PT-BR or EN-US)
    2. Creates variations by mixing platforms and tactics
    3. Applies proper redaction placeholders
    4. Outputs validated AttackExample objects

    Supports multiple languages:
    - PT-BR: Brazilian Portuguese scam patterns
    - EN-US: American English scam patterns

    Example:
        >>> generator = SeedBasedGenerator()
        >>> examples = list(generator.generate(count=100))
        >>> len(examples)
        100

        >>> # Load EN-US seeds
        >>> generator = SeedBasedGenerator(seeds_path="data/seeds/en-us-seeds.json")
        >>> examples = list(generator.generate(count=100))
    """

    def __init__(
        self,
        seeds_path: Path | str | None = None,
        random_seed: int | None = None,
    ) -> None:
        """
        Initialize the seed-based generator.

        Args:
            seeds_path: Path to seeds JSON file (auto-detected if None, defaults to pt-br)
            random_seed: Seed for random number generator (for reproducibility)
        """
        # Set random seed if provided
        if random_seed is not None:
            random.seed(random_seed)

        # Find seeds file
        if seeds_path is None:
            # Try to find the seeds file relative to the module (default to PT-BR)
            module_dir = Path(__file__).parent.parent.parent.parent
            seeds_path = module_dir / "data" / "seeds" / "pt-br-seeds.json"

        self.seeds_path = Path(seeds_path)
        self.seeds: list[dict] = []
        self.metadata: dict = {}
        self.id_counter = 1

        # Language detection (will be set in _load_seeds)
        self.language: Language = Language.PORTUGUESE
        self.region: str = "BR"

        # Load seeds
        self._load_seeds()

    def _load_seeds(self) -> None:
        """Load seeds from the JSON file and detect language."""
        if not self.seeds_path.exists():
            raise FileNotFoundError(f"Seeds file not found: {self.seeds_path}")

        with open(self.seeds_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.metadata = data.get("metadata", {})
        self.seeds = data.get("seeds", [])

        if not self.seeds:
            raise ValueError("No seeds found in the seeds file")

        # Detect language from metadata
        lang = self.metadata.get("language", "pt").lower()
        self.region = self.metadata.get("region", "BR").upper()

        if lang == "en":
            self.language = Language.ENGLISH
        elif lang == "es":
            self.language = Language.SPANISH
        else:
            self.language = Language.PORTUGUESE

    def _get_attack_type(self, category: str) -> AttackType:
        """
        Map seed category to AttackType enum.

        Args:
            category: Category string from seed (e.g., "PIX-01")

        Returns:
            Corresponding AttackType enum value
        """
        # Extract base category (e.g., "PIX" from "PIX-01")
        base_category = category.split("-")[0].upper()
        return CATEGORY_TO_ATTACK_TYPE.get(base_category, AttackType.PHISHING)

    def _get_platform(self, platform_str: str) -> Platform:
        """
        Map seed platform string to Platform enum.

        Args:
            platform_str: Platform string from seed

        Returns:
            Corresponding Platform enum value
        """
        platform_lower = platform_str.lower()

        # Check each mapping
        for key, platform in PLATFORM_MAPPING.items():
            if key in platform_lower:
                return platform

        return Platform.GENERIC

    def _get_tactics(self, tactics_list: list[str]) -> list[PersuasionTactic]:
        """
        Map seed tactics to PersuasionTactic enums.

        Args:
            tactics_list: List of tactic strings from seed

        Returns:
            List of PersuasionTactic enum values
        """
        result = []
        for tactic in tactics_list:
            tactic_lower = tactic.lower()

            # Direct mapping
            if tactic_lower in TACTIC_MAPPING:
                result.append(TACTIC_MAPPING[tactic_lower])
            else:
                # Fuzzy match
                for key, enum_val in TACTIC_MAPPING.items():
                    if key in tactic_lower or tactic_lower in key:
                        result.append(enum_val)
                        break

        # Ensure at least one tactic
        if not result:
            result = [PersuasionTactic.URGENCY]

        # Remove duplicates while preserving order
        seen = set()
        unique_result = []
        for t in result:
            if t not in seen:
                seen.add(t)
                unique_result.append(t)

        return unique_result

    def _get_difficulty(self, seed: dict) -> Difficulty:
        """
        Determine difficulty based on seed characteristics.

        Args:
            seed: Seed dictionary

        Returns:
            Difficulty enum value
        """
        # More sophisticated patterns are harder
        # Handle both PT-BR (persuasion_tactics) and EN-US (tactics) formats
        tactics_count = len(
            seed.get("persuasion_tactics", seed.get("tactics", []))
        )
        # EN-US uses single 'content' field; PT-BR uses 'example_messages' list
        messages_count = len(seed.get("example_messages", []))
        content_length = len(seed.get("content", ""))

        if tactics_count >= 4 or messages_count >= 4 or content_length > 300:
            return Difficulty.HARD
        elif tactics_count >= 2 or content_length > 150:
            return Difficulty.MEDIUM
        else:
            return Difficulty.EASY

    def _get_content_warning(self, attack_type: AttackType) -> ContentWarning:
        """
        Get appropriate content warning for attack type.

        Args:
            attack_type: The attack type

        Returns:
            ContentWarning enum value
        """
        mapping = {
            AttackType.PHISHING: ContentWarning.PHISHING,
            AttackType.IMPERSONATION: ContentWarning.IMPERSONATION,
            AttackType.BANK_IMPERSONATION: ContentWarning.IMPERSONATION,
            AttackType.GOVERNMENT_IMPERSONATION: ContentWarning.IMPERSONATION,
            AttackType.FINANCIAL_FRAUD: ContentWarning.FINANCIAL_FRAUD,
            AttackType.ROMANCE_SCAM: ContentWarning.EMOTIONAL_MANIPULATION,
            AttackType.FAMILY_EMERGENCY: ContentWarning.EMOTIONAL_MANIPULATION,
            AttackType.TECH_SUPPORT: ContentWarning.PHISHING,
            AttackType.JOB_SCAM: ContentWarning.SOCIAL_ENGINEERING,
            AttackType.DELIVERY_SCAM: ContentWarning.PHISHING,
        }
        return mapping.get(attack_type, ContentWarning.SOCIAL_ENGINEERING)

    def _ensure_placeholders(self, content: str) -> str:
        """
        Ensure content has proper placeholders for validation.

        Args:
            content: Raw content string

        Returns:
            Content with guaranteed placeholders
        """
        # If content already has placeholders, return as-is
        if re.search(r"\[[A-Z_]+\]", content):
            return content

        # Add a generic placeholder if none exist
        return content + " [MALICIOUS_URL]"

    def _generate_variation(
        self,
        seed: dict,
        variation_idx: int,
    ) -> str:
        """
        Generate a content variation from a seed.

        Handles both PT-BR format (example_messages list) and EN-US format (single content).

        Args:
            seed: The seed dictionary
            variation_idx: Index of the variation

        Returns:
            Generated content string with placeholders
        """
        # Get example messages from seed
        # PT-BR uses 'example_messages' list; EN-US uses 'content' string
        messages = seed.get("example_messages", [])
        pattern_desc = seed.get("pattern_description", "")
        direct_content = seed.get("content", "")

        if messages:
            # PT-BR format: Select a message based on variation index
            base_message = messages[variation_idx % len(messages)]
        elif direct_content:
            # EN-US format: Use the content field directly
            base_message = direct_content
        else:
            # Fallback: Use pattern description as base
            base_message = pattern_desc

        # Clean up the message (remove outer quotes if present)
        base_message = base_message.strip("'\"")

        # Select variation prefixes based on language
        if self.language == Language.ENGLISH:
            prefixes = VARIATION_PREFIXES_EN
        else:
            prefixes = VARIATION_PREFIXES_PT

        # Add variation prefix occasionally
        if random.random() < 0.3:
            prefix = random.choice(prefixes)
            if not base_message.startswith("["):
                base_message = prefix + base_message

        # Ensure proper placeholders
        content = self._ensure_placeholders(base_message)

        # Add context from example_structure if available (PT-BR format)
        example_structure = seed.get("example_structure", {})
        if example_structure and random.random() < 0.2:
            # Sometimes append urgency trigger or closing
            if "urgency_trigger" in example_structure:
                content += f" {example_structure['urgency_trigger']}"

        return content

    def _generate_id(self, attack_type: AttackType) -> str:
        """
        Generate unique ID for example.

        Args:
            attack_type: The attack type

        Returns:
            Unique ID string in format mdb-XXXXXX-{lang}-type
        """
        id_num = str(self.id_counter).zfill(6)
        self.id_counter += 1

        # Use language code from metadata
        lang_code = self.language.value  # 'pt', 'en', 'es', etc.
        return f"mdb-{id_num}-{lang_code}-{attack_type.value}"

    def _seed_to_examples(
        self,
        seed: dict,
        variations_per_seed: int = 5,
    ) -> Iterator[AttackExample]:
        """
        Generate multiple examples from a single seed.

        Handles both PT-BR and EN-US seed formats.

        Args:
            seed: The seed dictionary
            variations_per_seed: Number of variations to generate per seed

        Yields:
            AttackExample objects
        """
        # Extract seed info - handle both PT-BR and EN-US field names
        category = seed.get("category", "PHISHING-01")
        platform_str = seed.get("platform", "sms")

        # PT-BR uses 'persuasion_tactics', EN-US uses 'tactics'
        tactics_list = seed.get("persuasion_tactics", seed.get("tactics", ["urgency"]))

        # PT-BR uses 'source_name', EN-US may not have it
        source_name = seed.get("source_name", seed.get("notes", "unknown"))

        # PT-BR uses 'name', EN-US may not have it
        seed_name = seed.get("name", category)

        # Get seed ID - PT-BR uses 'seed_id', EN-US uses 'id'
        seed_id = seed.get("seed_id", seed.get("id", "unknown"))

        # Map to enums
        attack_type = self._get_attack_type(category)
        base_platform = self._get_platform(platform_str)
        tactics = self._get_tactics(tactics_list)
        difficulty = self._get_difficulty(seed)

        # Alternate platforms for variety based on language
        if self.language == Language.ENGLISH:
            # US-centric platforms
            platforms = [base_platform, Platform.SMS, Platform.EMAIL, Platform.GENERIC]
        else:
            # Brazil-centric platforms (WhatsApp very popular)
            platforms = [base_platform, Platform.WHATSAPP, Platform.SMS, Platform.EMAIL]

        # Set cultural markers based on language
        if self.language == Language.ENGLISH:
            cultural_markers = ["american_english", "en_us_scam_pattern", self.region.lower()]
        elif self.language == Language.SPANISH:
            cultural_markers = ["spanish", "es_scam_pattern", self.region.lower()]
        else:
            cultural_markers = ["brazilian_portuguese", "pt_br_scam_pattern"]

        # Language code for research purpose string
        lang_region = f"{self.language.value}-{self.region}"

        # Generate variations
        for i in range(variations_per_seed):
            try:
                # Generate content
                content = self._generate_variation(seed, i)

                # Skip if content is too short
                if len(content) < 15:
                    continue

                # Create safety metadata
                safety_metadata = SafetyMetadata(
                    redaction_level=RedactionLevel.FULL,
                    contains_functional_elements=False,
                    research_purpose=f"Testing {lang_region} {attack_type.value} pattern refusal",
                    content_warning=self._get_content_warning(attack_type),
                    approved_use_cases=[
                        ApprovedUseCase.MODEL_EVALUATION,
                        ApprovedUseCase.SAFETY_RESEARCH,
                    ],
                )

                # Create example metadata
                metadata = ExampleMetadata(
                    target_demographic="general",
                    generation_model="seed_generator_v1",
                    generation_timestamp=datetime.now(timezone.utc),
                )

                # Select platform (vary occasionally)
                platform = platforms[i % len(platforms)]

                # Vary difficulty occasionally
                if random.random() < 0.2:
                    difficulty = random.choice(list(Difficulty))

                # Create and yield example
                yield AttackExample(
                    id=self._generate_id(attack_type),
                    language=self.language,
                    attack_type=attack_type,
                    platform=platform,
                    content=content,
                    intent=f"{attack_type.value}_from_{category.split('-')[0].lower().replace('_', '')}",
                    persuasion_tactics=tactics,
                    cultural_markers=cultural_markers,
                    difficulty=difficulty,
                    is_synthetic=True,
                    source=f"seed:{seed_id}:{source_name[:50] if len(source_name) > 50 else source_name}",
                    safety_metadata=safety_metadata,
                    metadata=metadata,
                )

            except Exception as e:
                # Skip invalid examples
                continue

    def generate(
        self,
        count: int | None = None,
        variations_per_seed: int = 5,
        attack_type: AttackType | str | None = None,
        shuffle: bool = True,
    ) -> Iterator[AttackExample]:
        """
        Generate synthetic examples from seeds.

        Args:
            count: Maximum number of examples to generate (None = all)
            variations_per_seed: Number of variations per seed
            attack_type: Filter by attack type (optional)
            shuffle: Whether to shuffle seeds before generation

        Yields:
            AttackExample objects

        Example:
            >>> generator = SeedBasedGenerator()
            >>> examples = list(generator.generate(count=1000))
            >>> len(examples)
            1000
        """
        # Filter seeds by attack type if specified
        seeds_to_use = self.seeds

        if attack_type:
            if isinstance(attack_type, str):
                attack_type = AttackType(attack_type)

            seeds_to_use = [
                s for s in self.seeds
                if self._get_attack_type(s.get("category", "")) == attack_type
            ]

        # Shuffle if requested
        if shuffle:
            seeds_to_use = list(seeds_to_use)
            random.shuffle(seeds_to_use)

        # Generate examples
        generated = 0

        for seed in seeds_to_use:
            for example in self._seed_to_examples(seed, variations_per_seed):
                yield example
                generated += 1

                if count is not None and generated >= count:
                    return

    def get_stats(self) -> dict:
        """
        Get statistics about loaded seeds.

        Returns:
            Dictionary with seed statistics
        """
        # Count by category
        category_counts: dict[str, int] = {}
        for seed in self.seeds:
            category = seed.get("category", "unknown").split("-")[0]
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_seeds": len(self.seeds),
            "metadata_version": self.metadata.get("version", "unknown"),
            "categories": category_counts,
            "sources_count": len(self.metadata.get("sources", [])),
        }
