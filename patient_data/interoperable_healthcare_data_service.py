"""
Comprehensive Interoperable Healthcare Data Service
Handles CDA documents and FHIR resources with unified extraction and display
Includes headers, patient information, clinical sections, and metadata
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Import existing structured extraction services
from patient_data.services.cda_parser_service import CDAParserService
from patient_data.services.cda_translation_service import CDATranslationService
from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser

# Note: CDAJSONBundleParser import removed due to missing xmltodict dependency
from patient_data.translation_utils import (
    detect_document_language,
    get_template_translations,
)

logger = logging.getLogger(__name__)


class InteroperableHealthcareDataService:
    """
    Comprehensive service for handling both CDA documents and FHIR resources
    Provides unified data extraction and display capabilities
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        # Initialize existing extraction services
        self.cda_parser = CDAParserService()
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.translation_service = CDATranslationService(target_language)
        # Note: json_bundle_parser removed due to missing xmltodict dependency

    def extract_complete_healthcare_document(
        self, patient_id: str, resource_type: str = "cda"
    ) -> Optional[Dict[str, Any]]:
        """
        Extract complete healthcare document with all components:
        - Document headers and metadata
        - Patient demographics and extended information
        - Clinical sections with structured data
        - Supporting metadata and identifiers

        Args:
            patient_id: Patient identifier
            resource_type: 'cda' or 'fhir' (defaults to cda)

        Returns:
            Complete healthcare document structure or None
        """
        try:
            print(
                f"[HOSPITAL] Extracting complete healthcare document for patient {patient_id}"
            )

            if resource_type.lower() == "fhir":
                return self._extract_fhir_resource(patient_id)
            else:
                return self._extract_cda_document(patient_id)

        except Exception as e:
            logger.error(f"Failed to extract healthcare document: {e}")
            print(f"[ERROR] Extraction failed: {e}")
            return None

    def _extract_cda_document(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Extract complete CDA document with all components"""
        try:
            # Get CDA content
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                print(f"⚠️ No CDA content found for patient {patient_id}")
                return None

            # Parse document using existing services
            parsed_data = self.cda_parser.parse_cda_content(cda_content)
            if not parsed_data:
                print("⚠️ CDA parsing returned no data")
                return None

            print(f"[SUCCESS] CDA parsed successfully")

            # Extract document headers and metadata
            document_headers = self._extract_document_headers(cda_content, parsed_data)

            # Extract patient demographics and extended information
            patient_info = self._extract_patient_information(parsed_data)

            # Extract clinical sections with structured data
            clinical_sections = self._extract_clinical_sections(
                cda_content, parsed_data
            )

            # Extract supporting metadata
            document_metadata = self._extract_document_metadata(
                cda_content, parsed_data
            )

            # Combine into comprehensive structure
            complete_document = {
                "document_type": "CDA",
                "patient_id": patient_id,
                "extraction_timestamp": datetime.now().isoformat(),
                "document_headers": document_headers,
                "patient_information": patient_info,
                "clinical_sections": clinical_sections,
                "document_metadata": document_metadata,
                "language": detect_document_language(cda_content),
                "translations": get_template_translations(self.target_language),
            }

            print(
                f"[LIST] Complete CDA document extracted with {len(clinical_sections)} clinical sections"
            )
            return complete_document

        except Exception as e:
            logger.error(f"CDA extraction failed: {e}")
            print(f"[ERROR] CDA extraction error: {e}")
            return None

    def _extract_fhir_resource(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Extract FHIR resource (placeholder for future implementation)"""
        print(
            f"[SYNC] FHIR resource extraction for patient {patient_id} - Implementation pending"
        )

        # Placeholder structure for FHIR compatibility
        fhir_structure = {
            "document_type": "FHIR",
            "patient_id": patient_id,
            "extraction_timestamp": datetime.now().isoformat(),
            "resource_type": "Bundle",
            "status": "pending_implementation",
            "message": "FHIR resource extraction will be implemented in next phase",
        }

        return fhir_structure

    def _extract_document_headers(
        self, cda_content: str, parsed_data: Dict
    ) -> Dict[str, Any]:
        """Extract document headers and identifiers"""
        try:
            headers = {
                "document_title": parsed_data.get("title", "Clinical Document"),
                "document_id": parsed_data.get("id"),
                "version": parsed_data.get("version"),
                "creation_time": parsed_data.get("effectiveTime"),
                "confidentiality_code": parsed_data.get("confidentialityCode"),
                "language_code": parsed_data.get("languageCode"),
                "author": self._extract_author_info(parsed_data),
                "custodian": self._extract_custodian_info(parsed_data),
                "legal_authenticator": self._extract_legal_authenticator(parsed_data),
            }

            print(f"📄 Document headers extracted: {headers.get('document_title')}")
            return headers

        except Exception as e:
            logger.error(f"Header extraction failed: {e}")
            return {}

    def _extract_patient_information(self, parsed_data: Dict) -> Dict[str, Any]:
        """Extract comprehensive patient demographics and extended information"""
        try:
            patient_data = parsed_data.get("patient", {})

            patient_info = {
                "demographics": {
                    "name": patient_data.get("name"),
                    "patient_id": patient_data.get("id"),
                    "birth_date": patient_data.get("birthTime"),
                    "gender": patient_data.get("administrativeGenderCode"),
                    "marital_status": patient_data.get("maritalStatusCode"),
                },
                "contact_information": {
                    "addresses": patient_data.get("addresses", []),
                    "telecom": patient_data.get("telecom", []),
                },
                "identifiers": patient_data.get("identifiers", []),
                "guardian_information": patient_data.get("guardian"),
                "provider_organization": patient_data.get("providerOrganization"),
                "language_communication": patient_data.get("languageCommunication", []),
            }

            print(
                f"👤 Patient information extracted for: {patient_info['demographics'].get('name')}"
            )
            return patient_info

        except Exception as e:
            logger.error(f"Patient information extraction failed: {e}")
            return {}

    def _extract_clinical_sections(
        self, cda_content: str, parsed_data: Dict
    ) -> List[Dict[str, Any]]:
        """Extract clinical sections with structured entries and coded data"""
        try:
            # Use enhanced parser for structured clinical sections
            clinical_data = self.enhanced_parser.extract_clinical_sections(cda_content)

            sections = []
            if clinical_data and "sections" in clinical_data:
                for section in clinical_data["sections"]:
                    processed_section = {
                        "section_code": section.get("code"),
                        "section_title": section.get("title"),
                        "section_text": section.get("text"),
                        "entries": self._process_section_entries(
                            section.get("entries", [])
                        ),
                        "template_id": section.get("templateId"),
                        "language": section.get("language", self.target_language),
                    }
                    sections.append(processed_section)

            print(f"[HOSPITAL] Clinical sections extracted: {len(sections)} sections")
            for section in sections:
                entries_count = len(section.get("entries", []))
                print(
                    f"  - {section.get('section_title', 'Unknown')}: {entries_count} entries"
                )

            return sections

        except Exception as e:
            logger.error(f"Clinical sections extraction failed: {e}")
            return []

    def _process_section_entries(self, entries: List[Dict]) -> List[Dict[str, Any]]:
        """Process clinical entries with proper code/value separation"""
        processed_entries = []

        for entry in entries:
            processed_entry = {
                "entry_type": entry.get("typeCode"),
                "clinical_statement": {
                    "code": entry.get("code"),
                    "display_name": entry.get("displayName"),
                    "value": entry.get("value"),
                    "unit": entry.get("unit"),
                    "interpretation": entry.get("interpretation"),
                },
                "effective_time": entry.get("effectiveTime"),
                "status": entry.get("statusCode"),
                "participants": entry.get("participants", []),
                "translations": entry.get("translations", []),
            }
            processed_entries.append(processed_entry)

        return processed_entries

    def _extract_document_metadata(
        self, cda_content: str, parsed_data: Dict
    ) -> Dict[str, Any]:
        """Extract supporting document metadata and context"""
        try:
            metadata = {
                "document_class": parsed_data.get("classCode"),
                "mood_code": parsed_data.get("moodCode"),
                "realm_code": parsed_data.get("realmCode"),
                "type_id": parsed_data.get("typeId"),
                "template_ids": parsed_data.get("templateId", []),
                "set_id": parsed_data.get("setId"),
                "version_number": parsed_data.get("versionNumber"),
                "copy_time": parsed_data.get("copyTime"),
                "related_documents": parsed_data.get("relatedDocument", []),
                "encompassing_encounter": parsed_data.get("componentOf", {}).get(
                    "encompassingEncounter"
                ),
            }

            print(f"[CHART] Document metadata extracted")
            return metadata

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}

    def _extract_author_info(self, parsed_data: Dict) -> Optional[Dict]:
        """Extract document author information"""
        try:
            authors = parsed_data.get("author", [])
            if authors:
                # Return first author (can be extended for multiple authors)
                author = authors[0] if isinstance(authors, list) else authors
                return {
                    "name": author.get("assignedAuthor", {})
                    .get("assignedPerson", {})
                    .get("name"),
                    "id": author.get("assignedAuthor", {}).get("id"),
                    "time": author.get("time"),
                    "organization": author.get("assignedAuthor", {}).get(
                        "representedOrganization"
                    ),
                }
        except Exception:
            pass
        return None

    def _extract_custodian_info(self, parsed_data: Dict) -> Optional[Dict]:
        """Extract document custodian information"""
        try:
            custodian = parsed_data.get("custodian", {})
            if custodian:
                return {
                    "organization": custodian.get("assignedCustodian", {}).get(
                        "representedCustodianOrganization"
                    ),
                    "id": custodian.get("assignedCustodian", {})
                    .get("representedCustodianOrganization", {})
                    .get("id"),
                }
        except Exception:
            pass
        return None

    def _extract_legal_authenticator(self, parsed_data: Dict) -> Optional[Dict]:
        """Extract legal authenticator information"""
        try:
            authenticator = parsed_data.get("legalAuthenticator", {})
            if authenticator:
                return {
                    "name": authenticator.get("assignedEntity", {})
                    .get("assignedPerson", {})
                    .get("name"),
                    "id": authenticator.get("assignedEntity", {}).get("id"),
                    "time": authenticator.get("time"),
                    "signature_code": authenticator.get("signatureCode"),
                }
        except Exception:
            pass
        return None

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get CDA content from Django sessions"""
        try:
            # Search sessions for patient CDA data
            sessions = Session.objects.all()

            for session in sessions:
                try:
                    session_data = session.get_decoded()
                    if "cda_data" in session_data:
                        cda_data = session_data["cda_data"]

                        # Check if this session contains our patient
                        if self._session_contains_patient(cda_data, patient_id):
                            cda_content = cda_data.get("L3_xml_content")
                            if cda_content:
                                print(f"[SUCCESS] Found CDA content for patient {patient_id}")
                                return cda_content

                except Exception as e:
                    continue

            print(f"⚠️ No CDA content found for patient {patient_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve CDA content: {e}")
            return None

    def _session_contains_patient(self, cda_data: Dict, patient_id: str) -> bool:
        """Check if session contains the requested patient"""
        try:
            # Check patient_summaries
            if "patient_summaries" in cda_data:
                for summary in cda_data["patient_summaries"]:
                    if summary.get("id") == patient_id:
                        return True

            # Check current_patient
            if "current_patient" in cda_data:
                if cda_data["current_patient"].get("id") == patient_id:
                    return True

            return False

        except Exception:
            return False


@method_decorator(csrf_exempt, name="dispatch")
class InteroperableHealthcareDataView(View):
    """
    Django view providing interoperable healthcare data access
    Supports both CDA and FHIR resources through unified service
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.healthcare_service = InteroperableHealthcareDataService()

    def get(self, request, patient_id: str, resource_type: str = "cda"):
        """
        GET endpoint for healthcare document retrieval

        Args:
            patient_id: Patient identifier
            resource_type: 'cda' or 'fhir' (optional, defaults to 'cda')
        """
        try:
            print(
                f"[SEARCH] Healthcare data request: Patient {patient_id}, Type: {resource_type}"
            )

            # Extract complete healthcare document
            document_data = (
                self.healthcare_service.extract_complete_healthcare_document(
                    patient_id, resource_type
                )
            )

            if not document_data:
                return JsonResponse(
                    {
                        "error": f"No {resource_type.upper()} document found for patient {patient_id}",
                        "patient_id": patient_id,
                        "resource_type": resource_type,
                    },
                    status=404,
                )

            # Determine response format based on request
            format_type = request.GET.get("format", "html")

            if format_type == "json":
                return JsonResponse(document_data, safe=False)
            else:
                # Render HTML template with complete document data
                return render(
                    request,
                    "patient_data/interoperable_healthcare_document.html",
                    {
                        "document": document_data,
                        "patient_id": patient_id,
                        "resource_type": resource_type,
                    },
                )

        except Exception as e:
            logger.error(f"Healthcare data view error: {e}")
            return JsonResponse(
                {"error": "Internal server error", "message": str(e)}, status=500
            )

    def post(self, request, patient_id: str, resource_type: str = "cda"):
        """
        POST endpoint for healthcare document processing
        (Future implementation for document updates/transformations)
        """
        return JsonResponse(
            {
                "message": "POST operations for healthcare documents - Implementation pending",
                "patient_id": patient_id,
                "resource_type": resource_type,
            },
            status=501,
        )


# Utility function for direct service access
def get_complete_healthcare_document(
    patient_id: str, resource_type: str = "cda", language: str = "en"
) -> Optional[Dict[str, Any]]:
    """
    Utility function for direct access to complete healthcare document extraction

    Args:
        patient_id: Patient identifier
        resource_type: 'cda' or 'fhir'
        language: Target language for translations

    Returns:
        Complete healthcare document structure
    """
    service = InteroperableHealthcareDataService(target_language=language)
    return service.extract_complete_healthcare_document(patient_id, resource_type)


# Service factory for different healthcare standards
class HealthcareServiceFactory:
    """Factory for creating healthcare data services"""

    @staticmethod
    def create_service(
        standard: str, language: str = "en"
    ) -> InteroperableHealthcareDataService:
        """
        Create healthcare service for specific standard

        Args:
            standard: 'cda', 'fhir', 'hl7v2', etc.
            language: Target language

        Returns:
            Configured healthcare service
        """
        # Currently supports CDA, with FHIR planned
        return InteroperableHealthcareDataService(target_language=language)
