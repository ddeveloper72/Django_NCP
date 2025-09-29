"""
Interoperable Healthcare Data Service
Unified service layer for extracting structured clinical data from both CDA and FHIR resources
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ResourceFormat(Enum):
    """Supported healthcare resource formats"""

    CDA_XML = "cda_xml"
    CDA_HTML = "cda_html"
    FHIR_JSON = "fhir_json"
    FHIR_XML = "fhir_xml"
    UNKNOWN = "unknown"


@dataclass
class PatientIdentity:
    """Unified patient identity structure for both CDA and FHIR"""

    patient_id: str
    url_patient_id: str
    given_name: str = ""
    family_name: str = ""
    birth_date: str = ""
    gender: str = ""
    identifiers: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.identifiers is None:
            self.identifiers = []


@dataclass
class ClinicalSection:
    """Unified clinical section structure for both CDA and FHIR"""

    section_id: str
    section_code: str
    title: str
    content: str = ""
    narrative_text: str = ""
    entries: List[Dict[str, Any]] = None
    has_entries: bool = False
    entry_count: int = 0
    has_structured_data: bool = False
    section_type: str = "general"  # allergies, medications, problems, etc.

    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        self.entry_count = len(self.entries)
        self.has_entries = self.entry_count > 0
        self.has_structured_data = self.has_entries


@dataclass
class StructuredPatientData:
    """Unified structured patient data for both CDA and FHIR"""

    patient_identity: PatientIdentity
    clinical_sections: List[ClinicalSection]
    structured_body: Dict[str, List[Dict]] = None
    document_info: Dict[str, Any] = None
    extraction_metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.structured_body is None:
            self.structured_body = {}
        if self.document_info is None:
            self.document_info = {}
        if self.extraction_metadata is None:
            self.extraction_metadata = {}


class HealthcareResourceExtractor(ABC):
    """Abstract base class for healthcare resource extractors"""

    @abstractmethod
    def extract_patient_data(
        self, resource_content: str
    ) -> Optional[StructuredPatientData]:
        """Extract structured patient data from healthcare resource"""
        pass

    @abstractmethod
    def detect_format(self, content: str) -> ResourceFormat:
        """Detect the format of healthcare resource content"""
        pass

    @abstractmethod
    def validate_resource(self, content: str) -> bool:
        """Validate that the resource is properly formatted"""
        pass


class CDAResourceExtractor(HealthcareResourceExtractor):
    """CDA resource extractor using existing CDA services"""

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        # Import existing CDA services
        from patient_data.services.cda_parser_service import CDAParserService
        from patient_data.services.cda_translation_service import CDATranslationService
        from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser

        self.cda_parser = CDAParserService()
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.translation_service = CDATranslationService(target_language)

    def extract_patient_data(
        self, resource_content: str
    ) -> Optional[StructuredPatientData]:
        """Extract structured patient data from CDA resource"""
        try:
            # Use existing CDA parser service
            cda_data = self.cda_parser.parse_cda_document(resource_content)

            if not cda_data:
                return None

            # Convert to unified format
            patient_identity = self._convert_patient_identity(
                cda_data.get("patient_info", {})
            )
            clinical_sections = self._convert_clinical_sections(
                cda_data.get("clinical_sections", [])
            )

            return StructuredPatientData(
                patient_identity=patient_identity,
                clinical_sections=clinical_sections,
                structured_body=cda_data.get("structured_body", {}),
                document_info=cda_data.get("document_info", {}),
                extraction_metadata={
                    "source_format": ResourceFormat.CDA_XML.value,
                    "extractor": "CDAResourceExtractor",
                    "target_language": self.target_language,
                    "services_used": ["CDAParserService"],
                },
            )

        except Exception as e:
            logger.error(f"Error extracting CDA patient data: {e}")
            return None

    def detect_format(self, content: str) -> ResourceFormat:
        """Detect CDA format"""
        if not content or not content.strip():
            return ResourceFormat.UNKNOWN

        content = content.strip()

        if content.startswith("<?xml") or "<ClinicalDocument" in content:
            return ResourceFormat.CDA_XML
        elif "<html" in content.lower() or "<body" in content.lower():
            return ResourceFormat.CDA_HTML
        else:
            return ResourceFormat.UNKNOWN

    def validate_resource(self, content: str) -> bool:
        """Validate CDA resource"""
        format_type = self.detect_format(content)
        return format_type in [ResourceFormat.CDA_XML, ResourceFormat.CDA_HTML]

    def _convert_patient_identity(self, patient_info: Dict) -> PatientIdentity:
        """Convert CDA patient info to unified PatientIdentity"""
        names = patient_info.get("names", [])
        primary_name = names[0] if names else {}

        identifiers = patient_info.get("identifiers", [])
        primary_id = (
            identifiers[0].get("extension", "unknown") if identifiers else "unknown"
        )

        return PatientIdentity(
            patient_id=primary_id,
            url_patient_id=primary_id,
            given_name=primary_name.get("given", ""),
            family_name=primary_name.get("family", ""),
            birth_date=patient_info.get("birth_date", ""),
            gender=patient_info.get("gender", ""),
            identifiers=identifiers,
        )

    def _convert_clinical_sections(
        self, clinical_sections: List
    ) -> List[ClinicalSection]:
        """Convert CDA clinical sections to unified format"""
        converted_sections = []

        for i, section in enumerate(clinical_sections):
            section_code = getattr(section, "code", f"section_{i}")
            title = getattr(section, "title", f"Section {i+1}")
            content = getattr(section, "content", "")
            narrative_text = getattr(section, "narrative_text", "")
            entries = getattr(section, "entries", [])

            converted_section = ClinicalSection(
                section_id=f"cda_section_{i}",
                section_code=section_code,
                title=title,
                content=content,
                narrative_text=narrative_text,
                entries=[
                    entry.__dict__ if hasattr(entry, "__dict__") else entry
                    for entry in entries
                ],
                section_type=self._determine_section_type(section_code, title),
            )
            converted_sections.append(converted_section)

        return converted_sections

    def _determine_section_type(self, section_code: str, title: str) -> str:
        """Determine section type from code or title"""
        section_mappings = {
            "48765-2": "allergies",
            "10160-0": "medications",
            "11450-4": "problems",
            "30954-2": "laboratory_results",
            "47519-4": "procedures",
            "11369-6": "immunizations",
            "29762-2": "social_history",
            "8716-3": "vital_signs",
        }

        return section_mappings.get(section_code, "general")


class FHIRResourceExtractor(HealthcareResourceExtractor):
    """FHIR resource extractor for future FHIR compatibility"""

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language

    def extract_patient_data(
        self, resource_content: str
    ) -> Optional[StructuredPatientData]:
        """Extract structured patient data from FHIR resource"""
        try:
            # Parse FHIR JSON/XML
            if resource_content.strip().startswith("{"):
                fhir_data = json.loads(resource_content)
            else:
                # TODO: Handle FHIR XML format
                logger.warning("FHIR XML format not yet implemented")
                return None

            # Convert FHIR bundle to unified format
            patient_identity = self._extract_fhir_patient_identity(fhir_data)
            clinical_sections = self._extract_fhir_clinical_sections(fhir_data)

            return StructuredPatientData(
                patient_identity=patient_identity,
                clinical_sections=clinical_sections,
                extraction_metadata={
                    "source_format": ResourceFormat.FHIR_JSON.value,
                    "extractor": "FHIRResourceExtractor",
                    "target_language": self.target_language,
                    "services_used": ["FHIRResourceExtractor"],
                },
            )

        except Exception as e:
            logger.error(f"Error extracting FHIR patient data: {e}")
            return None

    def detect_format(self, content: str) -> ResourceFormat:
        """Detect FHIR format"""
        if not content or not content.strip():
            return ResourceFormat.UNKNOWN

        content = content.strip()

        if content.startswith("{") and "resourceType" in content:
            return ResourceFormat.FHIR_JSON
        elif content.startswith("<?xml") and "http://hl7.org/fhir" in content:
            return ResourceFormat.FHIR_XML
        else:
            return ResourceFormat.UNKNOWN

    def validate_resource(self, content: str) -> bool:
        """Validate FHIR resource"""
        format_type = self.detect_format(content)
        return format_type in [ResourceFormat.FHIR_JSON, ResourceFormat.FHIR_XML]

    def _extract_fhir_patient_identity(self, fhir_data: Dict) -> PatientIdentity:
        """Extract patient identity from FHIR resource"""
        # Handle FHIR Patient resource or find Patient in Bundle
        patient_resource = None

        if fhir_data.get("resourceType") == "Patient":
            patient_resource = fhir_data
        elif fhir_data.get("resourceType") == "Bundle":
            # Find Patient resource in bundle entries
            entries = fhir_data.get("entry", [])
            for entry in entries:
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Patient":
                    patient_resource = resource
                    break

        if not patient_resource:
            return PatientIdentity(patient_id="unknown", url_patient_id="unknown")

        # Extract patient data from FHIR Patient resource
        names = patient_resource.get("name", [])
        primary_name = names[0] if names else {}

        identifiers = patient_resource.get("identifier", [])
        primary_id = (
            identifiers[0].get("value", "unknown") if identifiers else "unknown"
        )

        return PatientIdentity(
            patient_id=primary_id,
            url_patient_id=primary_id,
            given_name=" ".join(primary_name.get("given", [])),
            family_name=primary_name.get("family", ""),
            birth_date=patient_resource.get("birthDate", ""),
            gender=patient_resource.get("gender", ""),
            identifiers=[
                {"value": id_info.get("value", ""), "system": id_info.get("system", "")}
                for id_info in identifiers
            ],
        )

    def _extract_fhir_clinical_sections(self, fhir_data: Dict) -> List[ClinicalSection]:
        """Extract clinical sections from FHIR resource"""
        sections = []

        # Handle different FHIR resource types
        if fhir_data.get("resourceType") == "Bundle":
            entries = fhir_data.get("entry", [])

            for i, entry in enumerate(entries):
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType", "Unknown")

                if (
                    resource_type != "Patient"
                ):  # Skip Patient resource as it's handled separately
                    section = ClinicalSection(
                        section_id=f"fhir_section_{i}",
                        section_code=resource_type.lower(),
                        title=f"{resource_type} Resource",
                        content=json.dumps(resource, indent=2),
                        entries=[resource],
                        section_type=self._map_fhir_resource_to_section_type(
                            resource_type
                        ),
                    )
                    sections.append(section)

        return sections

    def _map_fhir_resource_to_section_type(self, resource_type: str) -> str:
        """Map FHIR resource types to clinical section types"""
        fhir_mappings = {
            "AllergyIntolerance": "allergies",
            "MedicationStatement": "medications",
            "MedicationRequest": "medications",
            "Condition": "problems",
            "Observation": "laboratory_results",
            "Procedure": "procedures",
            "Immunization": "immunizations",
            "DiagnosticReport": "laboratory_results",
        }

        return fhir_mappings.get(resource_type, "general")


class InteroperableHealthcareDataService:
    """Main service for handling both CDA and FHIR resources with unified output"""

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self.extractors = {
            ResourceFormat.CDA_XML: CDAResourceExtractor(target_language),
            ResourceFormat.CDA_HTML: CDAResourceExtractor(target_language),
            ResourceFormat.FHIR_JSON: FHIRResourceExtractor(target_language),
            ResourceFormat.FHIR_XML: FHIRResourceExtractor(target_language),
        }

    def extract_patient_data(
        self, resource_content: str
    ) -> Optional[StructuredPatientData]:
        """
        Extract structured patient data from any supported healthcare resource format

        Args:
            resource_content: Raw healthcare resource content (CDA XML/HTML or FHIR JSON/XML)

        Returns:
            StructuredPatientData object with unified format or None if extraction fails
        """
        if not resource_content:
            logger.warning("Empty resource content provided")
            return None

        # Detect resource format
        detected_format = self._detect_resource_format(resource_content)

        if detected_format == ResourceFormat.UNKNOWN:
            logger.warning("Unknown resource format detected")
            return None

        # Get appropriate extractor
        extractor = self.extractors.get(detected_format)
        if not extractor:
            logger.error(f"No extractor available for format: {detected_format}")
            return None

        # Extract structured data
        structured_data = extractor.extract_patient_data(resource_content)

        if structured_data:
            # Add service-level metadata
            structured_data.extraction_metadata.update(
                {
                    "detected_format": detected_format.value,
                    "interoperable_service": True,
                    "extraction_timestamp": "2025-09-25T20:30:00Z",
                }
            )

            logger.info(
                f"Successfully extracted patient data from {detected_format.value} resource"
            )
            logger.info(
                f"Found {len(structured_data.clinical_sections)} clinical sections"
            )

        return structured_data

    def _detect_resource_format(self, content: str) -> ResourceFormat:
        """Detect the format of healthcare resource content"""
        for format_type, extractor in self.extractors.items():
            if extractor.detect_format(content) == format_type:
                return format_type

        return ResourceFormat.UNKNOWN

    def validate_resource(self, content: str) -> bool:
        """Validate healthcare resource content"""
        detected_format = self._detect_resource_format(content)

        if detected_format == ResourceFormat.UNKNOWN:
            return False

        extractor = self.extractors.get(detected_format)
        return extractor.validate_resource(content) if extractor else False

    def get_supported_formats(self) -> List[str]:
        """Get list of supported resource formats"""
        return [format_type.value for format_type in self.extractors.keys()]
