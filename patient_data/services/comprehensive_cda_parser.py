"""
Comprehensive CDA Parser
Combines Enhanced Clinical Parser and Non-Clinical Parser for complete CDA document processing.
Provides unified interface for extracting all CDA content: clinical codes, administrative data, demographics, etc.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .enhanced_cda_xml_parser import EnhancedCDAXMLParser
from .non_clinical_cda_parser import NonClinicalCDAParser

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveCDAResult:
    """Complete CDA parsing result with clinical and non-clinical data"""

    # Parsing status
    success: bool = True
    error: Optional[str] = None

    # Clinical data (from Enhanced parser)
    clinical_sections: List[Dict[str, Any]] = None
    sections_count: int = 0
    coded_sections_count: int = 0
    medical_terms_count: int = 0
    uses_coded_sections: bool = False
    translation_quality: str = "Basic"

    # Administrative data (from Non-Clinical parser)
    document_metadata: Any = None
    patient_demographics: Any = None
    healthcare_providers: List[Any] = None
    custodian_information: Any = None
    legal_authenticator: Any = None
    document_structure: Dict[str, Any] = None

    # Combined statistics
    parsing_completeness: float = 0.0
    data_richness_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering"""
        return {
            "success": self.success,
            "error": self.error,
            # Clinical data
            "sections": self.clinical_sections or [],
            "sections_count": self.sections_count,
            "coded_sections_count": self.coded_sections_count,
            "medical_terms_count": self.medical_terms_count,
            "uses_coded_sections": self.uses_coded_sections,
            "translation_quality": self.translation_quality,
            # Administrative data
            "document_metadata": self.document_metadata,
            "patient_identity": self._format_patient_identity(),
            "administrative_data": self._format_administrative_data(),
            "has_administrative_data": bool(self.document_metadata),
            # Enhanced metadata
            "healthcare_providers": self.healthcare_providers or [],
            "custodian_information": self.custodian_information,
            "legal_authenticator": self.legal_authenticator,
            "document_structure": self.document_structure or {},
            # Quality metrics
            "parsing_completeness": self.parsing_completeness,
            "data_richness_score": self.data_richness_score,
            "coded_sections_percentage": (
                self.coded_sections_count / max(self.sections_count, 1)
            )
            * 100,
        }

    def _format_patient_identity(self) -> Dict[str, Any]:
        """Format patient demographics for template compatibility"""
        if not self.patient_demographics:
            return {}

        return {
            "patient_id": self.patient_demographics.patient_id,
            "given_name": self.patient_demographics.given_name,
            "family_name": self.patient_demographics.family_name,
            "full_name": self.patient_demographics.full_name,
            "birth_date": self.patient_demographics.birth_date,
            "gender": self.patient_demographics.gender_display,
            "gender_code": self.patient_demographics.gender_code,
            "address": self.patient_demographics.formatted_address,
            "telecom": self.patient_demographics.telecom,
        }

    def _format_administrative_data(self) -> Dict[str, Any]:
        """Format administrative data for template compatibility"""
        admin_data = {}

        if self.document_metadata:
            admin_data.update(
                {
                    "document_id": self.document_metadata.document_id,
                    "title": self.document_metadata.title,
                    "creation_date": self.document_metadata.creation_date,
                    "document_type": self.document_metadata.document_type_display,
                    "confidentiality": self.document_metadata.confidentiality_display,
                    "language": self.document_metadata.language_code,
                }
            )

        if self.custodian_information:
            admin_data.update(
                {
                    "custodian_name": self.custodian_information.organization_name,
                    "custodian_id": self.custodian_information.organization_id,
                }
            )

        return admin_data


class ComprehensiveCDAParser:
    """
    Comprehensive CDA Parser that combines clinical and non-clinical extraction
    Provides complete CDA document processing with unified result structure
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self.clinical_parser = EnhancedCDAXMLParser()
        self.non_clinical_parser = NonClinicalCDAParser()

        logger.info(
            f"Comprehensive CDA Parser initialized for target language: {target_language}"
        )

    def parse_cda_content(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse CDA content comprehensively using both clinical and non-clinical parsers

        Args:
            xml_content: Raw CDA XML content

        Returns:
            Unified dictionary with complete CDA data
        """
        try:
            logger.info(
                f"Starting comprehensive CDA parsing (content length: {len(xml_content)})"
            )

            # Parse clinical data
            clinical_result = self.clinical_parser.parse_cda_content(xml_content)
            logger.info("Clinical parsing completed")

            # Parse non-clinical data
            non_clinical_result = self.non_clinical_parser.parse_cda_content(
                xml_content
            )
            logger.info("Non-clinical parsing completed")

            # Combine results
            comprehensive_result = self._merge_parsing_results(
                clinical_result, non_clinical_result
            )

            # Calculate quality metrics
            self._calculate_quality_metrics(comprehensive_result)

            logger.info(
                f"Comprehensive parsing complete: "
                f"{comprehensive_result.sections_count} sections, "
                f"{comprehensive_result.medical_terms_count} codes, "
                f"{comprehensive_result.parsing_completeness:.1f}% complete"
            )

            return comprehensive_result.to_dict()

        except Exception as e:
            logger.error(f"Comprehensive CDA parsing failed: {str(e)}")
            return self._create_error_result(str(e))

    def _merge_parsing_results(
        self, clinical_result: Dict[str, Any], non_clinical_result: Dict[str, Any]
    ) -> ComprehensiveCDAResult:
        """Merge clinical and non-clinical parsing results"""

        result = ComprehensiveCDAResult()

        # Check if both parsers succeeded
        clinical_success = clinical_result.get("success", False)
        non_clinical_success = non_clinical_result.get("success", False)

        result.success = clinical_success and non_clinical_success

        if not result.success:
            errors = []
            if not clinical_success:
                errors.append(
                    f"Clinical: {clinical_result.get('error', 'Unknown error')}"
                )
            if not non_clinical_success:
                errors.append(
                    f"Non-clinical: {non_clinical_result.get('error', 'Unknown error')}"
                )
            result.error = "; ".join(errors)

        # Merge clinical data
        if clinical_success:
            result.clinical_sections = clinical_result.get("sections", [])
            result.sections_count = clinical_result.get("sections_count", 0)
            result.coded_sections_count = clinical_result.get("coded_sections_count", 0)
            result.medical_terms_count = clinical_result.get("medical_terms_count", 0)
            result.uses_coded_sections = clinical_result.get(
                "uses_coded_sections", False
            )
            result.translation_quality = clinical_result.get(
                "translation_quality", "Basic"
            )

        # Merge non-clinical data
        if non_clinical_success:
            result.document_metadata = non_clinical_result.get("document_metadata")
            result.patient_demographics = non_clinical_result.get(
                "patient_demographics"
            )
            result.healthcare_providers = non_clinical_result.get(
                "healthcare_providers", []
            )
            result.custodian_information = non_clinical_result.get(
                "custodian_information"
            )
            result.legal_authenticator = non_clinical_result.get("legal_authenticator")
            result.document_structure = non_clinical_result.get(
                "document_structure", {}
            )

        return result

    def _calculate_quality_metrics(self, result: ComprehensiveCDAResult):
        """Calculate parsing completeness and data richness scores"""

        # Data richness components (each worth points)
        richness_score = 0

        # Clinical data richness (40 points max)
        if result.sections_count > 0:
            richness_score += min(
                result.sections_count * 2, 20
            )  # Up to 20 points for sections
        if result.medical_terms_count > 0:
            richness_score += min(
                result.medical_terms_count // 5, 20
            )  # Up to 20 points for codes

        # Administrative data richness (60 points max)
        if result.document_metadata and result.document_metadata.title:
            richness_score += 10  # Document metadata
        if result.patient_demographics and result.patient_demographics.full_name:
            richness_score += 15  # Patient demographics
        if result.healthcare_providers:
            richness_score += min(
                len(result.healthcare_providers) * 5, 15
            )  # Healthcare providers
        if (
            result.custodian_information
            and result.custodian_information.organization_name
        ):
            richness_score += 10  # Custodian info
        if result.legal_authenticator and result.legal_authenticator.full_name:
            richness_score += 10  # Legal authenticator

        result.data_richness_score = min(richness_score, 100)

        # Parsing completeness (percentage)
        completeness_factors = [
            result.sections_count > 0,  # Has clinical sections
            result.medical_terms_count > 0,  # Has clinical codes
            bool(result.document_metadata),  # Has document metadata
            bool(result.patient_demographics),  # Has patient data
            len(result.healthcare_providers) > 0,  # Has providers
        ]

        result.parsing_completeness = (
            sum(completeness_factors) / len(completeness_factors)
        ) * 100

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result in expected format"""
        error_result = ComprehensiveCDAResult()
        error_result.success = False
        error_result.error = error_message
        return error_result.to_dict()

    def get_parser_capabilities(self) -> Dict[str, List[str]]:
        """Get information about parser capabilities"""
        return {
            "clinical_capabilities": [
                "Clinical sections extraction",
                "SNOMED-CT codes",
                "LOINC codes",
                "ICD-10 codes",
                "ATC medication codes",
                "Multi-country CDA variations",
                "Coded entry relationships",
            ],
            "non_clinical_capabilities": [
                "Document metadata",
                "Patient demographics",
                "Healthcare provider information",
                "Custodian details",
                "Legal authenticator data",
                "Document structure analysis",
                "Administrative classifications",
            ],
            "output_formats": [
                "Django template compatible",
                "JSON serializable",
                "Quality metrics included",
                "Error handling integrated",
            ],
        }
