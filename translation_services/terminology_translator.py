"""
Terminology Translation Service
Provides real-time translation of clinical terminology using MVC data
"""

from typing import Dict, List, Optional, Tuple
from django.core.cache import cache
from django.utils import translation
from .models import ValueSetCatalogue, ValueSetConcept, ConceptTranslation
import logging
import re

logger = logging.getLogger(__name__)


class TerminologyTranslator:
    """Service for translating clinical terminology"""

    def __init__(self, target_language: str = None):
        """
        Initialize translator

        Args:
            target_language: Target language code (e.g., 'de', 'fr').
                           If None, uses current Django language.
        """
        self.target_language = target_language or translation.get_language()
        self.cache_timeout = 3600  # 1 hour cache

    def translate_clinical_document(
        self, document_content: str, source_language: str = "en"
    ) -> Dict:
        """
        Translate terminology in a clinical document

        Args:
            document_content: Raw FHIR/CDA document content
            source_language: Source language of the document

        Returns:
            Dict with translation information and enhanced content
        """
        if self.target_language == source_language:
            return {
                "content": document_content,
                "translations_applied": 0,
                "terminology_map": {},
                "untranslated_terms": [],
                "language": self.target_language,
            }

        # Extract terminology codes from document
        extracted_terms = self._extract_terminology_codes(document_content)

        # Translate the extracted terms
        translation_map = {}
        untranslated_terms = []

        for term in extracted_terms:
            translation = self._translate_term(
                code=term["code"],
                system=term["system"],
                original_display=term.get("display"),
            )

            if translation:
                translation_map[term["code"]] = translation
            else:
                untranslated_terms.append(term)

        # Apply translations to document content
        enhanced_content = self._apply_translations_to_content(
            document_content, translation_map
        )

        return {
            "content": enhanced_content,
            "translations_applied": len(translation_map),
            "terminology_map": translation_map,
            "untranslated_terms": untranslated_terms,
            "language": self.target_language,
            "source_language": source_language,
        }

    def translate_concept_list(self, concepts: List[Dict]) -> List[Dict]:
        """
        Translate a list of concepts

        Args:
            concepts: List of concept dictionaries with 'code', 'system', 'display'

        Returns:
            List of concepts with added translation information
        """
        translated_concepts = []

        for concept in concepts:
            translation = self._translate_term(
                code=concept.get("code"),
                system=concept.get("system"),
                original_display=concept.get("display"),
            )

            enhanced_concept = concept.copy()
            if translation:
                enhanced_concept.update(
                    {
                        "translated_display": translation["display"],
                        "translated_definition": translation.get("definition"),
                        "translation_source": translation["source"],
                        "translation_quality": translation["quality"],
                    }
                )
            else:
                enhanced_concept["translation_available"] = False

            translated_concepts.append(enhanced_concept)

        return translated_concepts

    def _translate_term(
        self, code: str, system: str, original_display: str = None
    ) -> Optional[Dict]:
        """
        Translate a single terminology term

        Args:
            code: The concept code
            system: The code system identifier
            original_display: Original display text (optional)

        Returns:
            Translation dictionary or None if no translation found
        """
        if not code or not system:
            return None

        # Check cache first
        cache_key = f"term_translation_{system}_{code}_{self.target_language}"
        cached_translation = cache.get(cache_key)
        if cached_translation:
            return cached_translation

        try:
            # Find the concept in our MVC data
            concept = ValueSetConcept.objects.filter(
                code=code,
                code_system__icontains=system,  # Allow partial system matching
                status="active",
            ).first()

            if not concept:
                # Try alternative matching approaches
                concept = self._find_concept_by_alternative_matching(
                    code, system, original_display
                )

            if concept:
                # Look for translation
                translation_obj = ConceptTranslation.objects.filter(
                    concept=concept, language_code=self.target_language
                ).first()

                if translation_obj:
                    translation = {
                        "display": translation_obj.translated_display,
                        "definition": translation_obj.translated_definition,
                        "source": translation_obj.source,
                        "quality": translation_obj.translation_quality,
                        "original_display": concept.display,
                    }
                else:
                    # Use the concept's default display if no translation
                    translation = {
                        "display": concept.display,
                        "definition": concept.definition,
                        "source": "MVC_DEFAULT",
                        "quality": "official",
                        "original_display": concept.display,
                    }

                # Cache the result
                cache.set(cache_key, translation, self.cache_timeout)
                return translation

        except Exception as e:
            logger.warning(f"Error translating term {code} from {system}: {e}")

        return None

    def _find_concept_by_alternative_matching(
        self, code: str, system: str, original_display: str = None
    ) -> Optional["ValueSetConcept"]:
        """
        Try alternative approaches to find a concept when direct matching fails
        """
        # Try matching by OID if system looks like an OID
        if re.match(r"^[\d\.]+$", system):
            concept = ValueSetConcept.objects.filter(
                code=code, value_set__oid=system, status="active"
            ).first()
            if concept:
                return concept

        # Try matching by display text if provided
        if original_display:
            concept = ValueSetConcept.objects.filter(
                code=code, display__icontains=original_display, status="active"
            ).first()
            if concept:
                return concept

        # Try exact code match across all systems
        concept = ValueSetConcept.objects.filter(code=code, status="active").first()

        return concept

    def _extract_terminology_codes(self, document_content: str) -> List[Dict]:
        """
        Extract terminology codes from FHIR/CDA document content
        """
        terms = []

        # This is a simplified extraction - in practice, you'd use proper FHIR/CDA parsers
        # Look for common patterns in FHIR documents

        # FHIR coding patterns
        import json

        try:
            if document_content.strip().startswith("{"):
                # Assume JSON FHIR
                fhir_data = json.loads(document_content)
                terms.extend(self._extract_from_fhir_json(fhir_data))
        except json.JSONDecodeError:
            pass

        # XML patterns (CDA or FHIR XML)
        if "<" in document_content and ">" in document_content:
            terms.extend(self._extract_from_xml_content(document_content))

        return terms

    def _extract_from_fhir_json(
        self, fhir_data: Dict, terms: List[Dict] = None
    ) -> List[Dict]:
        """
        Recursively extract terminology from FHIR JSON
        """
        if terms is None:
            terms = []

        if isinstance(fhir_data, dict):
            # Look for coding elements
            if "coding" in fhir_data:
                for coding in fhir_data["coding"]:
                    if isinstance(coding, dict):
                        term = {
                            "code": coding.get("code"),
                            "system": coding.get("system"),
                            "display": coding.get("display"),
                        }
                        if term["code"] and term["system"]:
                            terms.append(term)

            # Look for code elements with system
            if "code" in fhir_data and "system" in fhir_data:
                term = {
                    "code": fhir_data["code"],
                    "system": fhir_data["system"],
                    "display": fhir_data.get("display"),
                }
                terms.append(term)

            # Recurse into nested objects
            for value in fhir_data.values():
                if isinstance(value, (dict, list)):
                    self._extract_from_fhir_json(value, terms)

        elif isinstance(fhir_data, list):
            for item in fhir_data:
                self._extract_from_fhir_json(item, terms)

        return terms

    def _extract_from_xml_content(self, xml_content: str) -> List[Dict]:
        """
        Extract terminology codes from XML content (CDA or FHIR XML)
        """
        terms = []

        # Simple regex patterns for common XML structures
        # In practice, you'd use proper XML parsing

        # Look for code attributes with codeSystem
        code_pattern = (
            r'code="([^"]+)"[^>]*codeSystem="([^"]+)"[^>]*(?:displayName="([^"]+)")?'
        )
        matches = re.findall(code_pattern, xml_content)

        for match in matches:
            terms.append(
                {
                    "code": match[0],
                    "system": match[1],
                    "display": match[2] if match[2] else None,
                }
            )

        return terms

    def _apply_translations_to_content(
        self, content: str, translation_map: Dict
    ) -> str:
        """
        Apply translations to document content

        This is a simplified approach - in practice, you'd need proper
        document structure preservation
        """
        enhanced_content = content

        for code, translation in translation_map.items():
            if translation.get("original_display") and translation.get("display"):
                # Replace display text with translated version
                original = translation["original_display"]
                translated = f"{translation['display']} ({original})"
                enhanced_content = enhanced_content.replace(original, translated)

        return enhanced_content

    def get_translation_summary(self, translation_result: Dict) -> Dict:
        """
        Generate a summary of translation results for UI display
        """
        return {
            "total_terms_found": len(translation_result["terminology_map"])
            + len(translation_result["untranslated_terms"]),
            "terms_translated": len(translation_result["terminology_map"]),
            "terms_untranslated": len(translation_result["untranslated_terms"]),
            "translation_coverage": (
                len(translation_result["terminology_map"])
                / (
                    len(translation_result["terminology_map"])
                    + len(translation_result["untranslated_terms"])
                )
                if (
                    len(translation_result["terminology_map"])
                    + len(translation_result["untranslated_terms"])
                )
                > 0
                else 0
            )
            * 100,
            "target_language": translation_result["language"],
            "source_language": translation_result.get("source_language", "en"),
        }


def get_available_translation_languages() -> List[Tuple[str, str]]:
    """
    Get list of available translation languages based on MVC data

    Returns:
        List of (language_code, language_name) tuples
    """
    from django.db import connection

    # Query distinct language codes from translations
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT language_code 
            FROM translation_services_concepttranslation 
            UNION 
            SELECT DISTINCT language_code 
            FROM translation_services_valuesettranslation
            ORDER BY language_code
        """
        )

        language_codes = [row[0] for row in cursor.fetchall()]

    # Map codes to names (you could extend this with a proper language mapping)
    language_map = {
        "en": "English",
        "de": "German (Deutsch)",
        "fr": "French (Français)",
        "it": "Italian (Italiano)",
        "es": "Spanish (Español)",
        "pt": "Portuguese (Português)",
        "nl": "Dutch (Nederlands)",
        "da": "Danish (Dansk)",
        "sv": "Swedish (Svenska)",
        "fi": "Finnish (Suomi)",
    }

    return [(code, language_map.get(code, code.upper())) for code in language_codes]


class TerminologyTranslatorCompat(TerminologyTranslator):
    """
    Compatibility wrapper for CDATranslationService
    Provides legacy method names while using CTS-based architecture
    """

    def translate_term(self, term: str, source_lang: str = "fr") -> str:
        """
        Compatibility method for legacy translate_term calls
        Returns the term as-is since proper CTS translation is document-level
        """
        return term

    def translate_text_block(self, text: str, source_lang: str = "fr") -> str:
        """
        Compatibility method for legacy translate_text_block calls
        Returns the text as-is since proper CTS translation is document-level
        """
        return text
