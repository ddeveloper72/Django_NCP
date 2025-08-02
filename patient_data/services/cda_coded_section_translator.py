"""
CDA Section Code Translator
Maps HL7 CDA section codes to translated titles using standardized medical terminology
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CDACodedSectionTranslator:
    """
    Translates CDA section codes to localized section titles
    Uses HL7 Patient Summary section codes for consistent medical terminology
    """

    # HL7 Patient Summary section codes with multilingual translations
    SECTION_CODE_TRANSLATIONS = {
        # Allergies and Intolerances
        "48765-2": {
            "en": "Allergies and Adverse Reactions",
            "fr": "Allergies et Réactions Indésirables",
            "de": "Allergien und Unerwünschte Reaktionen",
            "es": "Alergias y Reacciones Adversas",
            "it": "Allergie e Reazioni Avverse",
            "nl": "Allergieën en Ongewenste Reacties",
            "pt": "Alergias e Reações Adversas",
            "description": "Known allergies, intolerances, and adverse drug reactions",
        },
        # History of Medication Use
        "10160-0": {
            "en": "History of Medication Use",
            "fr": "Historique Médicamenteux",
            "de": "Medikamentenanamnese",
            "es": "Historia de Uso de Medicamentos",
            "it": "Storia dell'Uso dei Farmaci",
            "nl": "Medicatiegeschiedenis",
            "pt": "Histórico de Uso de Medicamentos",
            "description": "Current and past medications, dosages, and treatment history",
        },
        # Problem List
        "11450-4": {
            "en": "Problem List",
            "fr": "Liste des Problèmes",
            "de": "Problemliste",
            "es": "Lista de Problemas",
            "it": "Elenco dei Problemi",
            "nl": "Probleemlijst",
            "pt": "Lista de Problemas",
            "description": "Active medical conditions, diagnoses, and health concerns",
        },
        # Relevant Diagnostic Tests and Laboratory Data
        "30954-2": {
            "en": "Relevant Diagnostic Tests and Laboratory Data",
            "fr": "Tests Diagnostiques et Données de Laboratoire Pertinents",
            "de": "Relevante Diagnostische Tests und Labordaten",
            "es": "Pruebas Diagnósticas y Datos de Laboratorio Relevantes",
            "it": "Test Diagnostici e Dati di Laboratorio Rilevanti",
            "nl": "Relevante Diagnostische Tests en Laboratoriumgegevens",
            "pt": "Testes Diagnósticos e Dados Laboratoriais Relevantes",
            "description": "Laboratory results, imaging studies, and diagnostic test results",
        },
        # History of Procedures
        "47519-4": {
            "en": "History of Procedures",
            "fr": "Historique des Procédures",
            "de": "Eingriffsanamnese",
            "es": "Historia de Procedimientos",
            "it": "Storia delle Procedure",
            "nl": "Geschiedenis van Procedures",
            "pt": "Histórico de Procedimentos",
            "description": "Surgical procedures, medical interventions, and treatments performed",
        },
        # History of Immunizations
        "11369-6": {
            "en": "Immunization History",
            "fr": "Historique des Vaccinations",
            "de": "Impfanamnese",
            "es": "Historia de Inmunizaciones",
            "it": "Storia delle Immunizzazioni",
            "nl": "Vaccinatiegeschiedenis",
            "pt": "Histórico de Imunizações",
            "description": "Vaccination records and immunization status",
        },
        # Vital Signs
        "8716-3": {
            "en": "Vital Signs",
            "fr": "Signes Vitaux",
            "de": "Vitalparameter",
            "es": "Signos Vitales",
            "it": "Segni Vitali",
            "nl": "Vitale Functies",
            "pt": "Sinais Vitais",
            "description": "Blood pressure, heart rate, temperature, respiratory rate, and other vital measurements",
        },
        # Social History
        "29762-2": {
            "en": "Social History",
            "fr": "Antécédents Sociaux",
            "de": "Sozialanamnese",
            "es": "Historia Social",
            "it": "Storia Sociale",
            "nl": "Sociale Anamnese",
            "pt": "História Social",
            "description": "Lifestyle factors, occupation, social determinants of health",
        },
        # Functional Status
        "47420-5": {
            "en": "Functional Status",
            "fr": "État Fonctionnel",
            "de": "Funktionsstatus",
            "es": "Estado Funcional",
            "it": "Stato Funzionale",
            "nl": "Functionele Status",
            "pt": "Estado Funcional",
            "description": "Physical function, mobility, activities of daily living",
        },
        # Advance Directives
        "42348-3": {
            "en": "Advance Directives",
            "fr": "Directives Anticipées",
            "de": "Patientenverfügungen",
            "es": "Directrices Anticipadas",
            "it": "Direttive Anticipate",
            "nl": "Wilsverklaringen",
            "pt": "Diretivas Antecipadas",
            "description": "Healthcare preferences, end-of-life decisions, and patient directives",
        },
        # Hospital Discharge Medications
        "10183-2": {
            "en": "Hospital Discharge Medications",
            "fr": "Médicaments de Sortie d'Hôpital",
            "de": "Entlassungsmedikation",
            "es": "Medicamentos al Alta Hospitalaria",
            "it": "Farmaci alla Dimissione Ospedaliera",
            "nl": "Ontslagmedicatie",
            "pt": "Medicamentos na Alta Hospitalar",
            "description": "Medications prescribed upon hospital discharge",
        },
        # History of Family Member Diseases
        "10157-6": {
            "en": "History of Family Member Diseases",
            "fr": "Antécédents Familiaux",
            "de": "Familienanamnese",
            "es": "Historia de Enfermedades Familiares",
            "it": "Storia delle Malattie dei Familiari",
            "nl": "Familieanamnese",
            "pt": "História de Doenças Familiares",
            "description": "Family medical history and genetic predispositions",
        },
        # History of Encounters
        "46240-8": {
            "en": "History of Encounters",
            "fr": "Historique des Rencontres",
            "de": "Kontaktanamnese",
            "es": "Historia de Encuentros",
            "it": "Storia degli Incontri",
            "nl": "Geschiedenis van Contacten",
            "pt": "Histórico de Encontros",
            "description": "Healthcare encounters, visits, and consultations",
        },
    }

    def __init__(self, target_language: str = "en"):
        """
        Initialize the coded section translator

        Args:
            target_language: Target language code (en, fr, de, es, it, nl, pt)
        """
        self.target_language = target_language
        self.supported_languages = ["en", "fr", "de", "es", "it", "nl", "pt"]

        if target_language not in self.supported_languages:
            logger.warning(
                f"Language {target_language} not supported, falling back to English"
            )
            self.target_language = "en"

    def translate_section_code(
        self, section_code: str, fallback_title: str = None
    ) -> Dict[str, str]:
        """
        Translate a section code to the target language

        Args:
            section_code: HL7 section code (e.g., "48765-2")
            fallback_title: Original title to use if code not found

        Returns:
            Dictionary with translated title and metadata
        """
        try:
            if section_code in self.SECTION_CODE_TRANSLATIONS:
                section_data = self.SECTION_CODE_TRANSLATIONS[section_code]

                return {
                    "translated_title": section_data.get(
                        self.target_language, section_data.get("en")
                    ),
                    "original_code": section_code,
                    "description": section_data.get("description", ""),
                    "is_coded": True,
                    "translation_quality": "high",
                    "source": "hl7_patient_summary_codes",
                }
            else:
                # Use fallback title if no coded translation available
                logger.info(
                    f"No coded translation found for section code: {section_code}"
                )
                return {
                    "translated_title": fallback_title
                    or f"Clinical Section ({section_code})",
                    "original_code": section_code,
                    "description": "Section not found in standard HL7 Patient Summary codes",
                    "is_coded": False,
                    "translation_quality": "low",
                    "source": "fallback",
                }

        except Exception as e:
            logger.error(f"Error translating section code {section_code}: {e}")
            return {
                "translated_title": fallback_title or "Clinical Section",
                "original_code": section_code,
                "description": "Translation error occurred",
                "is_coded": False,
                "translation_quality": "error",
                "source": "error",
            }

    def get_section_code_from_title(
        self, title: str, language: str = "en"
    ) -> Optional[str]:
        """
        Find section code by matching title text

        Args:
            title: Section title text
            language: Language of the title

        Returns:
            Section code if found, None otherwise
        """
        try:
            title_lower = title.lower().strip()

            for code, translations in self.SECTION_CODE_TRANSLATIONS.items():
                for lang, translated_title in translations.items():
                    if (
                        lang != "description"
                        and translated_title.lower() == title_lower
                    ):
                        return code

            return None

        except Exception as e:
            logger.error(f"Error finding section code for title '{title}': {e}")
            return None

    def get_all_section_translations(self) -> Dict[str, Dict]:
        """
        Get all available section translations for reference

        Returns:
            Complete mapping of section codes to translations
        """
        return self.SECTION_CODE_TRANSLATIONS.copy()

    def get_supported_languages(self) -> list:
        """
        Get list of supported language codes

        Returns:
            List of supported language codes
        """
        return self.supported_languages.copy()

    def validate_section_data(self, section_data: Dict) -> Dict[str, str]:
        """
        Validate and enhance section data with coded translations

        Args:
            section_data: Section data from CDA parser

        Returns:
            Enhanced section data with coded translations
        """
        try:
            # Extract section code from various possible locations
            section_code = None

            # Try different code extraction methods
            if "codes" in section_data and section_data["codes"]:
                for code_info in section_data["codes"]:
                    if code_info.get("type") == "section_code":
                        section_code = code_info.get("code")
                        break

            # If no section code found, try to derive from other data
            if not section_code and "code" in section_data:
                section_code = section_data["code"]

            # Get coded translation
            if section_code:
                translation_result = self.translate_section_code(
                    section_code,
                    section_data.get("title", section_data.get("original_title")),
                )

                # Enhance section data with coded translation
                section_data.update(
                    {
                        "coded_title": translation_result["translated_title"],
                        "section_code": section_code,
                        "section_description": translation_result["description"],
                        "is_coded_section": translation_result["is_coded"],
                        "translation_source": translation_result["source"],
                        "translation_quality": translation_result[
                            "translation_quality"
                        ],
                    }
                )

            return section_data

        except Exception as e:
            logger.error(f"Error validating section data: {e}")
            return section_data
