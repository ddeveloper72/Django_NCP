"""
Translation Utilities for CDA Template Internationalization
Provides translation utilities for dynamic template rendering
"""

from django.utils.translation import gettext as _
from typing import Dict, Any


class TemplateTranslationService:
    """Service for providing template translations based on source document language"""

    def __init__(self, source_language: str = "en", target_language: str = "en"):
        self.source_language = source_language
        self.target_language = target_language

        # Import EU UI translations for basic terms
        from patient_data.services.eu_ui_translations import eu_ui_translations

        self.ui_translations = eu_ui_translations

    def get_section_translations(self) -> Dict[str, str]:
        """Get translated section headers and labels"""

        # Base translations - these should come from CTS/translation service
        translations = {
            # Main Headers
            "clinical_sections": _("Clinical Sections"),
            "medical_terms": _("Medical Terms"),
            "translation_quality": _("Translation Quality"),
            "standards_compliance": _("Standards Compliance"),
            "hl7_coded_sections": _("HL7 Coded Sections"),
            # Patient Information
            "patient_details": _("Patient Details"),
            "patient_information": _("Patient Information"),
            "patient_name": _("Patient Name"),
            "european_patient_summary": _("European Patient Summary"),
            # Administrative Section
            "other_contacts": _("Other Contacts"),
            "address": _("Address"),
            "name": _("Name"),
            "telecom": _("Contact"),
            # Safety and Medical Alerts
            "safety_alerts": _("SAFETY ALERTS"),
            "known_allergies": _("Known Allergies"),
            "medical_alerts": _("Medical Alerts"),
            "no_cda_identifiers": _("No CDA identifiers available"),
            # Clinical Content
            "enhanced_medical_translation": _(
                "Enhanced medical translation with {count} verified medical terms"
            ),
            "coded_sections_info": _("{coded} of {total} clinical sections"),
            "professional_terminology": _(
                "Coded Sections: Professional medical terminology"
            ),
            "machine_translated": _("Free Text: Machine translated content"),
            # Navigation
            "back_to_patient_details": _("Back to Patient Details"),
            # Document Info
            "source_document": _(
                "Source: {country} • Document: Patient Summary ({type})"
            ),
            "document_confidence": _("Match Confidence: {confidence}%"),
            # Additional UI labels - now using EU translation library
            "patient_summary": _("Patient Summary"),
            "name": self.ui_translations.get_translation("name", self.target_language),
            "address": self.ui_translations.get_translation(
                "address", self.target_language
            ),
            "email": self.ui_translations.get_translation(
                "email", self.target_language
            ),
            "phone": self.ui_translations.get_translation(
                "phone", self.target_language
            ),
            "contact": self.ui_translations.get_translation(
                "contact", self.target_language
            ),
            "organization": self.ui_translations.get_translation(
                "organization", self.target_language
            ),
            "information": self.ui_translations.get_translation(
                "information", self.target_language
            ),
            "details": self.ui_translations.get_translation(
                "details", self.target_language
            ),
        }

        return translations

    def get_medical_section_translations(self) -> Dict[str, str]:
        """Get medical section specific translations"""
        return {
            "allergies": _("Allergies and Intolerances"),
            "medications": _("Medication Summary"),
            "medical_devices": _("Medical Devices"),
            "immunizations": _("Immunizations"),
            "surgeries": _("Surgical Procedures"),
            "problems": _("Problem List"),
            "vital_signs": _("Vital Signs"),
            "social_history": _("Social History"),
        }

    def get_button_translations(self) -> Dict[str, str]:
        """Get button and interactive element translations"""
        return {
            "translated_coded": _("Translated coded"),
            "original_narrative": _("Original narrative"),
            "show_original": _("Show Original"),
            "show_translation": _("Show Translation"),
            "download_pdf": _("Download PDF"),
            "print_document": _("Print Document"),
        }


def get_template_translations(
    source_language: str = "en", target_language: str = "en"
) -> Dict[str, Any]:
    """
    Get all template translations for CDA document display

    Args:
        source_language: Language of the source CDA document (detected from document)
        target_language: Target language for display (user preference)

    Returns:
        Dictionary of translated strings for template use
    """
    service = TemplateTranslationService(source_language, target_language)

    translations = {}
    translations.update(service.get_section_translations())
    translations.update(service.get_medical_section_translations())
    translations.update(service.get_button_translations())

    return translations


def detect_document_language(cda_content: str) -> str:
    """
    Detect the source language of a CDA document using CTS-based approach

    Args:
        cda_content: Raw CDA XML content

    Returns:
        ISO language code (e.g., 'fr', 'de', 'lv', 'en')
    """
    # Use the dedicated CTS-compliant language detection service
    from patient_data.services.eu_language_detection_service import detect_cda_language

    return detect_cda_language(cda_content)
