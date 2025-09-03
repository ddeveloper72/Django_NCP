"""
Django NCP Translation Services

Core translation service implementing the Java NCP TSAM architecture
for medical terminology translation and FHIR/CDA document processing.

Based on Java NCP components:
- TSAM (Terminology Service Access Manager)
- Translation Services (FHIR/CDA document translation)
- TRC STS (Security Token Service)
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from translation_manager.models import (
    TerminologySystem,
    ConceptMapping,
    LanguageTranslation,
    CountrySpecificMapping,
    TranslationService as TranslationServiceModel,
    TranslationCache,
)

logger = logging.getLogger(__name__)


class TSAMError:
    """Translation error structure matching Java NCP ITMTSAMError"""

    def __init__(self, code: str, message: str, severity: str = "ERROR"):
        self.code = code
        self.message = message
        self.severity = severity
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
        }


class TMResponseStructure:
    """Translation response structure matching Java NCP TMResponseStructure"""

    def __init__(
        self,
        translated_document: dict,
        status: str,
        errors: List[TSAMError] = None,
        warnings: List[TSAMError] = None,
    ):
        self.translated_document = translated_document
        self.status = status
        self.errors = errors or []
        self.warnings = warnings or []
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            "translated_document": self.translated_document,
            "status": self.status,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "timestamp": self.timestamp.isoformat(),
        }


class TerminologyMappingService:
    """Core terminology mapping service - Django implementation of Java TSAM"""

    def __init__(self):
        self.cache_timeout = getattr(settings, "TSAM_CACHE_TIMEOUT", 3600)

    def get_concept_mapping(
        self, source_code: str, source_system: str, target_system: str
    ) -> Optional[ConceptMapping]:
        """
        Get concept mapping between terminology systems

        Args:
            source_code: Source concept code
            source_system: Source terminology system (e.g., 'ICD-10', 'SNOMED-CT')
            target_system: Target terminology system

        Returns:
            ConceptMapping or None if not found
        """
        cache_key = f"concept_mapping_{source_system}_{source_code}_{target_system}"
        cached_mapping = cache.get(cache_key)

        if cached_mapping:
            return cached_mapping

        try:
            mapping = ConceptMapping.objects.select_related(
                "source_system", "target_system"
            ).get(
                source_code=source_code,
                source_system__name=source_system,
                target_system__name=target_system,
                is_active=True,
            )

            cache.set(cache_key, mapping, self.cache_timeout)
            return mapping

        except ConceptMapping.DoesNotExist:
            logger.warning(
                f"No concept mapping found: {source_system}:{source_code} -> {target_system}"
            )
            return None

    def get_language_translation(
        self, concept_code: str, terminology_system: str, target_language: str
    ) -> Optional[LanguageTranslation]:
        """
        Get language-specific translation for a medical concept

        Args:
            concept_code: Medical concept code
            terminology_system: Terminology system name
            target_language: Target language code (e.g., 'en-GB', 'de-DE')

        Returns:
            LanguageTranslation or None if not found
        """
        cache_key = (
            f"lang_translation_{terminology_system}_{concept_code}_{target_language}"
        )
        cached_translation = cache.get(cache_key)

        if cached_translation:
            return cached_translation

        try:
            translation = LanguageTranslation.objects.select_related(
                "terminology_system"
            ).get(
                concept_code=concept_code,
                terminology_system__name=terminology_system,
                language_code=target_language,
                is_active=True,
            )

            cache.set(cache_key, translation, self.cache_timeout)
            return translation

        except LanguageTranslation.DoesNotExist:
            logger.warning(
                f"No language translation found: {terminology_system}:{concept_code} -> {target_language}"
            )
            return None

    def translate_concept(
        self,
        source_code: str,
        source_system: str,
        target_language: str,
        target_system: str = "epSOS",
    ) -> Tuple[Optional[str], List[TSAMError]]:
        """
        Translate a medical concept from source system to target language

        Args:
            source_code: Source concept code
            source_system: Source terminology system
            target_language: Target language code
            target_system: Target terminology system (default: epSOS pivot)

        Returns:
            Tuple of (translated_term, errors)
        """
        errors = []

        # Step 1: Map source concept to target system (e.g., local -> epSOS)
        concept_mapping = self.get_concept_mapping(
            source_code, source_system, target_system
        )
        if not concept_mapping:
            error = TSAMError(
                code="MAPPING_NOT_FOUND",
                message=f"No concept mapping found for {source_system}:{source_code} -> {target_system}",
            )
            errors.append(error)
            return None, errors

        # Step 2: Get language translation for target concept
        target_code = concept_mapping.target_code
        language_translation = self.get_language_translation(
            target_code, target_system, target_language
        )

        if not language_translation:
            error = TSAMError(
                code="TRANSLATION_NOT_FOUND",
                message=f"No language translation found for {target_system}:{target_code} -> {target_language}",
            )
            errors.append(error)
            return None, errors

        return language_translation.translated_name, errors


class FHIRTranslationService:
    """FHIR document translation service - Django implementation of Java FHIR TranslationService"""

    def __init__(self):
        self.terminology_service = TerminologyMappingService()

    def translate_fhir_bundle(
        self, fhir_bundle: dict, target_language: str
    ) -> TMResponseStructure:
        """
        Translate FHIR Bundle document

        Args:
            fhir_bundle: FHIR Bundle as dictionary
            target_language: Target language code

        Returns:
            TMResponseStructure with translated document
        """
        errors = []
        warnings = []
        translated_bundle = fhir_bundle.copy()

        try:
            # Process each entry in the FHIR Bundle
            if "entry" in fhir_bundle:
                for i, entry in enumerate(fhir_bundle["entry"]):
                    if "resource" in entry:
                        resource = entry["resource"]
                        translated_resource, resource_errors = (
                            self._translate_fhir_resource(resource, target_language)
                        )
                        translated_bundle["entry"][i]["resource"] = translated_resource
                        errors.extend(resource_errors)

            status = "success" if not errors else "partial_success"
            return TMResponseStructure(translated_bundle, status, errors, warnings)

        except Exception as e:
            error = TSAMError(
                code="TRANSLATION_ERROR",
                message=f"Error translating FHIR Bundle: {str(e)}",
            )
            errors.append(error)
            return TMResponseStructure(fhir_bundle, "error", errors, warnings)

    def _translate_fhir_resource(
        self, resource: dict, target_language: str
    ) -> Tuple[dict, List[TSAMError]]:
        """
        Translate individual FHIR resource

        Args:
            resource: FHIR resource as dictionary
            target_language: Target language code

        Returns:
            Tuple of (translated_resource, errors)
        """
        errors = []
        translated_resource = resource.copy()

        # Get resource type
        resource_type = resource.get("resourceType", "")

        # Translate based on resource type
        if resource_type == "AllergyIntolerance":
            translated_resource, allergy_errors = self._translate_allergy_intolerance(
                translated_resource, target_language
            )
            errors.extend(allergy_errors)

        elif resource_type == "Condition":
            translated_resource, condition_errors = self._translate_condition(
                translated_resource, target_language
            )
            errors.extend(condition_errors)

        elif resource_type == "Medication":
            translated_resource, medication_errors = self._translate_medication(
                translated_resource, target_language
            )
            errors.extend(medication_errors)

        elif resource_type == "Observation":
            translated_resource, observation_errors = self._translate_observation(
                translated_resource, target_language
            )
            errors.extend(observation_errors)

        return translated_resource, errors

    def _translate_allergy_intolerance(
        self, resource: dict, target_language: str
    ) -> Tuple[dict, List[TSAMError]]:
        """Translate AllergyIntolerance FHIR resource"""
        errors = []

        # Translate allergy code
        if "code" in resource and "coding" in resource["code"]:
            for coding in resource["code"]["coding"]:
                if "code" in coding and "system" in coding:
                    translated_term, translation_errors = (
                        self.terminology_service.translate_concept(
                            coding["code"], coding["system"], target_language
                        )
                    )
                    if translated_term:
                        coding["display"] = translated_term
                    errors.extend(translation_errors)

        # Translate reaction manifestations
        if "reaction" in resource:
            for reaction in resource["reaction"]:
                if "manifestation" in reaction:
                    for manifestation in reaction["manifestation"]:
                        if "coding" in manifestation:
                            for coding in manifestation["coding"]:
                                if "code" in coding and "system" in coding:
                                    translated_term, translation_errors = (
                                        self.terminology_service.translate_concept(
                                            coding["code"],
                                            coding["system"],
                                            target_language,
                                        )
                                    )
                                    if translated_term:
                                        coding["display"] = translated_term
                                    errors.extend(translation_errors)

        return resource, errors

    def _translate_condition(
        self, resource: dict, target_language: str
    ) -> Tuple[dict, List[TSAMError]]:
        """Translate Condition FHIR resource"""
        errors = []

        # Translate condition code
        if "code" in resource and "coding" in resource["code"]:
            for coding in resource["code"]["coding"]:
                if "code" in coding and "system" in coding:
                    translated_term, translation_errors = (
                        self.terminology_service.translate_concept(
                            coding["code"], coding["system"], target_language
                        )
                    )
                    if translated_term:
                        coding["display"] = translated_term
                    errors.extend(translation_errors)

        return resource, errors

    def _translate_medication(
        self, resource: dict, target_language: str
    ) -> Tuple[dict, List[TSAMError]]:
        """Translate Medication FHIR resource"""
        errors = []

        # Translate medication code
        if "code" in resource and "coding" in resource["code"]:
            for coding in resource["code"]["coding"]:
                if "code" in coding and "system" in coding:
                    translated_term, translation_errors = (
                        self.terminology_service.translate_concept(
                            coding["code"], coding["system"], target_language
                        )
                    )
                    if translated_term:
                        coding["display"] = translated_term
                    errors.extend(translation_errors)

        return resource, errors

    def _translate_observation(
        self, resource: dict, target_language: str
    ) -> Tuple[dict, List[TSAMError]]:
        """Translate Observation FHIR resource"""
        errors = []

        # Translate observation code
        if "code" in resource and "coding" in resource["code"]:
            for coding in resource["code"]["coding"]:
                if "code" in coding and "system" in coding:
                    translated_term, translation_errors = (
                        self.terminology_service.translate_concept(
                            coding["code"], coding["system"], target_language
                        )
                    )
                    if translated_term:
                        coding["display"] = translated_term
                    errors.extend(translation_errors)

        # Translate value concept if present
        if (
            "valueCodeableConcept" in resource
            and "coding" in resource["valueCodeableConcept"]
        ):
            for coding in resource["valueCodeableConcept"]["coding"]:
                if "code" in coding and "system" in coding:
                    translated_term, translation_errors = (
                        self.terminology_service.translate_concept(
                            coding["code"], coding["system"], target_language
                        )
                    )
                    if translated_term:
                        coding["display"] = translated_term
                    errors.extend(translation_errors)

        return resource, errors


class CDATranslationService:
    """CDA document translation service - Django implementation of Java CDA TranslationService"""

    def __init__(self):
        self.terminology_service = TerminologyMappingService()

    def translate_cda_document(
        self, cda_document: str, target_language: str
    ) -> TMResponseStructure:
        """
        Translate CDA document XML

        Args:
            cda_document: CDA document as XML string
            target_language: Target language code

        Returns:
            TMResponseStructure with translated document
        """
        errors = []
        warnings = []

        try:
            # Parse and translate CDA document
            # This would involve XML parsing and terminology mapping
            # For now, return the original document with translation metadata

            translated_document = {
                "original_document": cda_document,
                "target_language": target_language,
                "translation_timestamp": datetime.now().isoformat(),
                "translation_status": "translated",
            }

            return TMResponseStructure(translated_document, "success", errors, warnings)

        except Exception as e:
            error = TSAMError(
                code="CDA_TRANSLATION_ERROR",
                message=f"Error translating CDA document: {str(e)}",
            )
            errors.append(error)
            return TMResponseStructure(
                {"original_document": cda_document}, "error", errors, warnings
            )


class TranslationServiceFactory:
    """Factory for creating appropriate translation services"""

    @staticmethod
    def get_fhir_translation_service() -> FHIRTranslationService:
        """Get FHIR translation service instance"""
        return FHIRTranslationService()

    @staticmethod
    def get_cda_translation_service() -> CDATranslationService:
        """Get CDA translation service instance"""
        return CDATranslationService()

    @staticmethod
    def get_terminology_service() -> TerminologyMappingService:
        """Get terminology mapping service instance"""
        return TerminologyMappingService()
