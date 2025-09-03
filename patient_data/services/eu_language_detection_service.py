"""
EU Language Detection Service for CDA Documents
CTS-compliant langu            # Method 1: Check explicit language declarations
            # Handle XML namespaces properly
            xml_lang_attrs = [
                'xml:lang',
                'language',
                'lang',
                '{http://www.w3.org/XML/1998/namespace}lang'  # Namespaced xml:lang
            ]
            for attr in xml_lang_attrs:
                lang_code = root.get(attr)
                if lang_code:
                    normalized = self._normalize_language_code(lang_code)
                    return normalizedtection without hardcoded patterns
"""

from typing import Dict, Optional, List
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EULanguageDetectionService:
    """
    CTS-based language detection service for EU member state CDA documents
    """

    def __init__(self):
        # EU member states with their primary languages
        # This maps EU country codes to ISO 639-1 language codes
        self.eu_member_state_languages = {
            # EU-27 Member States
            "AT": "de",  # Austria - German
            "BE": "nl",  # Belgium - Dutch (also French, German)
            "BG": "bg",  # Bulgaria - Bulgarian
            "HR": "hr",  # Croatia - Croatian
            "CY": "el",  # Cyprus - Greek
            "CZ": "cs",  # Czech Republic - Czech
            "DK": "da",  # Denmark - Danish
            "EE": "et",  # Estonia - Estonian
            "FI": "fi",  # Finland - Finnish
            "FR": "fr",  # France - French
            "DE": "de",  # Germany - German
            "GR": "el",  # Greece - Greek
            "HU": "hu",  # Hungary - Hungarian
            "IE": "en",  # Ireland - English
            "IT": "it",  # Italy - Italian
            "LV": "lv",  # Latvia - Latvian
            "LT": "lt",  # Lithuania - Lithuanian
            "LU": "fr",  # Luxembourg - French (also German, Luxembourgish)
            "MT": "mt",  # Malta - Maltese
            "NL": "nl",  # Netherlands - Dutch
            "PL": "pl",  # Poland - Polish
            "PT": "pt",  # Portugal - Portuguese
            "RO": "ro",  # Romania - Romanian
            "SK": "sk",  # Slovakia - Slovak
            "SI": "sl",  # Slovenia - Slovenian
            "ES": "es",  # Spain - Spanish
            "SE": "sv",  # Sweden - Swedish
        }

        # Common multilingual countries with alternative languages
        self.multilingual_countries = {
            "BE": ["nl", "fr", "de"],  # Belgium
            "LU": ["fr", "de", "lb"],  # Luxembourg
            "CH": ["de", "fr", "it"],  # Switzerland (not EU but often in medical data)
        }

    def detect_from_cda_metadata(self, cda_content: str) -> Optional[str]:
        """
        Detect language from CDA document metadata and XML attributes

        Args:
            cda_content: Raw CDA XML content

        Returns:
            ISO 639-1 language code or None if not detected
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(cda_content)

            # Method 1: Check explicit language declarations
            # Handle XML namespaces properly
            xml_lang_attrs = [
                "xml:lang",
                "language",
                "lang",
                "{http://www.w3.org/XML/1998/namespace}lang",  # Namespaced xml:lang
            ]
            for attr in xml_lang_attrs:
                lang_code = root.get(attr)
                if lang_code:
                    normalized = self._normalize_language_code(lang_code)
                    return normalized

            # Method 2: Check languageCode elements in CDA structure
            for elem in root.iter():
                if "languageCode" in elem.tag.lower():
                    code = elem.get("code")
                    if code:
                        return self._normalize_language_code(code)

            # Method 3: Check country code in document origin
            country_code = self._extract_country_code(root)
            if country_code:
                return self.eu_member_state_languages.get(country_code.upper())

        except ET.ParseError as e:
            logger.warning(f"XML parsing failed during language detection: {e}")

        return None

    def detect_from_country_origin(self, country_code: str) -> Optional[str]:
        """
        Detect language based on document country of origin

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            ISO 639-1 language code or None
        """
        if not country_code or len(country_code) != 2:
            return None

        return self.eu_member_state_languages.get(country_code.upper())

    def get_supported_languages(self) -> List[str]:
        """
        Get all supported EU languages

        Returns:
            List of ISO 639-1 language codes
        """
        return list(set(self.eu_member_state_languages.values()))

    def get_country_languages(self, country_code: str) -> List[str]:
        """
        Get all possible languages for a given country

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            List of possible language codes for the country
        """
        country_upper = country_code.upper()

        if country_upper in self.multilingual_countries:
            return self.multilingual_countries[country_upper]
        elif country_upper in self.eu_member_state_languages:
            return [self.eu_member_state_languages[country_upper]]
        else:
            return []

    def _normalize_language_code(self, lang_code: str) -> str:
        """
        Normalize language code to ISO 639-1 format

        Args:
            lang_code: Raw language code from document

        Returns:
            Normalized ISO 639-1 language code
        """
        if not lang_code:
            return "en"

        # Extract first 2 characters and convert to lowercase
        normalized = lang_code[:2].lower()

        # Validate against supported languages
        if normalized in self.get_supported_languages():
            return normalized

        return "en"  # Default to English

    def _extract_country_code(self, xml_root) -> Optional[str]:
        """
        Extract country code from CDA document structure

        Args:
            xml_root: Parsed XML root element

        Returns:
            Country code or None
        """
        # Look for country codes in various CDA elements
        country_elements = [
            ".//addr/country",
            ".//assigningAuthorityName",
            ".//representedOrganization/addr/country",
            ".//custodian//addr/country",
        ]

        for xpath in country_elements:
            try:
                elements = xml_root.findall(xpath)
                for elem in elements:
                    if elem.text and len(elem.text) == 2:
                        return elem.text.upper()
            except Exception:
                continue

        return None


def detect_cda_language(cda_content: str, country_hint: Optional[str] = None) -> str:
    """
    Main function to detect CDA document language using CTS-compliant approach

    Args:
        cda_content: Raw CDA XML content
        country_hint: Optional country code hint from session/context

    Returns:
        ISO 639-1 language code (defaults to 'en')
    """
    service = EULanguageDetectionService()

    # Priority 1: Extract from CDA metadata
    detected_lang = service.detect_from_cda_metadata(cda_content)
    if detected_lang:
        logger.info(f"Language detected from CDA metadata: {detected_lang}")
        return detected_lang

    # Priority 2: Use country hint if provided
    if country_hint:
        detected_lang = service.detect_from_country_origin(country_hint)
        if detected_lang:
            logger.info(
                f"Language detected from country hint {country_hint}: {detected_lang}"
            )
            return detected_lang

    # Priority 3: Default to English for EU interoperability
    logger.info("Language detection fallback: defaulting to English")
    return "en"


def get_eu_supported_languages() -> Dict[str, str]:
    """
    Get all EU supported languages with their names

    Returns:
        Dictionary mapping language codes to language names
    """
    return {
        "bg": "Bulgarian",
        "cs": "Czech",
        "da": "Danish",
        "de": "German",
        "el": "Greek",
        "en": "English",
        "es": "Spanish",
        "et": "Estonian",
        "fi": "Finnish",
        "fr": "French",
        "hr": "Croatian",
        "hu": "Hungarian",
        "it": "Italian",
        "lt": "Lithuanian",
        "lv": "Latvian",
        "mt": "Maltese",
        "nl": "Dutch",
        "pl": "Polish",
        "pt": "Portuguese",
        "ro": "Romanian",
        "sk": "Slovak",
        "sl": "Slovenian",
        "sv": "Swedish",
    }
