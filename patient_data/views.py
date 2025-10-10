"""
Patient Data Views
EU NCP Portal Patient Search and Document Retrieval

IMPORTANT - Patient Identifier Management:
- URL session_id (e.g., 549316): Temporary session identifier, safe for logging
- CDA patient_id (e.g., aGVhbHRoY2FyZUlkMTIz): Real patient identifier from healthcare system, PHI-protected
- Database IDs: Internal Django model primary keys, not exposed to users

URL Structure: /patients/cda/{session_id}/{cda_type}/
Example: /patients/cda/549316/L3/ where 549316 is the temporary session ID
"""

import base64
import html
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from xhtml2pdf import pisa

from ncp_gateway.models import Patient  # Add import for NCP gateway Patient model

from .forms import PatientDataForm
from .models import PatientData
from .services import EUPatientSearchService, PatientCredentials
from .services.clinical_pdf_service import ClinicalDocumentPDFService
from .services.fhir_agent_service import FHIRAgentService
from .services.section_processors import PatientSectionProcessor
from .services.terminology_service import CentralTerminologyService
from .services.history_of_past_illness_extractor import HistoryOfPastIllnessExtractor
from .services.immunizations_extractor import ImmunizationsExtractor
from .services.pregnancy_history_extractor import PregnancyHistoryExtractor
from .services.social_history_extractor import SocialHistoryExtractor
from .services.physical_findings_extractor import PhysicalFindingsExtractor
from .services.coded_results_extractor import CodedResultsExtractor

logger = logging.getLogger(__name__)


# Mandatory Clinical Sections (always displayed even if empty)
MANDATORY_CLINICAL_SECTIONS = {
    "48765-2": {
        "code": "48765-2",
        "title": "Allergies and adverse reactions Document",
        "display_name": "Allergies and adverse reactions",
        "icon": "fa-solid fa-exclamation-triangle",
        "empty_message": "No known allergies or adverse reactions documented."
    },
    "30954-2": {
        "code": "30954-2", 
        "title": "Relevant diagnostic tests/laboratory data Narrative",
        "display_name": "Relevant diagnostic tests/laboratory data",
        "icon": "fa-solid fa-flask",
        "empty_message": "No diagnostic tests or laboratory data available."
    },
    "11450-4": {
        "code": "11450-4",
        "title": "Problem list - Reported", 
        "display_name": "Problem list",
        "icon": "fa-solid fa-list-ul",
        "empty_message": "No active problems reported."
    },
    "10160-0": {
        "code": "10160-0",
        "title": "History of Medication use Narrative",
        "display_name": "History of Medication use", 
        "icon": "fa-solid fa-pills",
        "empty_message": "No medication history documented."
    },
    "46264-8": {
        "code": "46264-8",
        "title": "History of medical device use",
        "display_name": "History of medical device use",
        "icon": "fa-solid fa-heartbeat", 
        "empty_message": "No medical device usage documented."
    },
    "47519-4": {
        "code": "47519-4",
        "title": "History of Procedures Document",
        "display_name": "History of Procedures",
        "icon": "fa-solid fa-user-md",
        "empty_message": "No procedures documented."
    }
}


def ensure_mandatory_sections(clinical_arrays: dict) -> dict:
    """
    Ensure all mandatory clinical sections are present, adding empty sections with 
    appropriate messaging when they don't exist in the CDA.
    
    Args:
        clinical_arrays: Dictionary of clinical section arrays
        
    Returns:
        Enhanced clinical_arrays with mandatory sections guaranteed to be present
    """
    # Mapping from our internal names to LOINC codes
    section_mapping = {
        "allergies": "48765-2",
        "results": "30954-2", 
        "problems": "11450-4",
        "medications": "10160-0",
        "medical_devices": "46264-8",  # This might need adjustment based on actual data structure
        "procedures": "47519-4"
    }
    
    for section_name, loinc_code in section_mapping.items():
        if section_name not in clinical_arrays or not clinical_arrays[section_name]:
            # Create empty section with mandatory messaging
            mandatory_info = MANDATORY_CLINICAL_SECTIONS[loinc_code]
            empty_section = {
                "is_mandatory": True,
                "is_empty": True,
                "section_code": loinc_code,
                "display_name": mandatory_info["display_name"], 
                "title": mandatory_info["title"],
                "icon": mandatory_info["icon"],
                "empty_message": mandatory_info["empty_message"],
                "entries": [],
                "clinical_table": None
            }
            clinical_arrays[section_name] = [empty_section]
            logger.info(f"Added mandatory empty section: {mandatory_info['display_name']}")
    
    return clinical_arrays


def detect_extended_clinical_sections(comprehensive_data: dict) -> dict:
    """
    Detect extended clinical sections available in CDA document beyond mandatory 5 sections.
    
    Args:
        comprehensive_data: Processed CDA data from comprehensive clinical service
        
    Returns:
        Dictionary with extended section arrays for template rendering
    """
    extended_sections = {
        "history_of_past_illness": [],
        "immunizations": [],
        "pregnancy_history": [],
        "social_history": [],
        "physical_findings": [],
        "coded_results": {"blood_group": [], "diagnostic_results": []},
        "laboratory_results": [],
        "advance_directives": [],
        "additional_sections": []
    }
    
    # LOINC code mappings for extended sections
    extended_section_mapping = {
        "11369-6": "immunizations",  # History of Immunizations
        "29762-2": "social_history",  # Social History
        "8716-3": "vital_signs",     # Vital Signs (could be extended)
        "47420-5": "functional_status",  # Functional Status
        "42348-3": "advance_directives",  # Advance Directives
        "11348-0": "history_of_past_illness",  # History of Past Illness (corrected LOINC code)
        "10162-6": "pregnancy_history",  # History of pregnancies
        "30954-2": "laboratory_results",  # Relevant diagnostic tests
        "18748-4": "coded_results",  # Diagnostic imaging report
        "34530-6": "coded_results",  # ABO/Rh blood group panel
        "883-9": "coded_results",    # ABO blood group
        "882-1": "coded_results",    # Rh blood group
        "18725-2": "coded_results",  # Microbiology studies
        "11502-2": "coded_results",  # Laboratory report
    }
    
    if not comprehensive_data or not isinstance(comprehensive_data, dict):
        return extended_sections
    
    # Check if we have sections data
    sections = comprehensive_data.get("sections", [])
    if not sections:
        return extended_sections
    
    logger.info(f"[EXTENDED SECTIONS] Processing {len(sections)} sections for extended detection")
    
    # Process each section and categorize
    for section in sections:
        section_code = section.get("section_code", "")
        section_title = section.get("display_name", section.get("title", "")).lower()
        entries = section.get("entries", [])
        
        # Map by LOINC code first
        mapped_category = extended_section_mapping.get(section_code)
        if mapped_category and mapped_category in extended_sections:
            if entries:  # Only add if has actual data
                extended_sections[mapped_category].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped {section_code} to {mapped_category} with {len(entries)} entries")
            continue
        
        # Map by title keywords for sections without standard LOINC codes
        if any(keyword in section_title for keyword in ["immuniz", "vaccin", "immun"]):
            if entries:
                extended_sections["immunizations"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to immunizations by keyword")
        elif any(keyword in section_title for keyword in ["social", "tobacco", "alcohol", "smoking"]):
            if entries:
                extended_sections["social_history"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to social_history by keyword")
        elif any(keyword in section_title for keyword in ["pregnan", "pregnancy", "obstetric"]):
            if entries:
                extended_sections["pregnancy_history"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to pregnancy_history by keyword")
        elif any(keyword in section_title for keyword in ["past illness", "history of present", "medical history"]):
            if entries:
                extended_sections["history_of_past_illness"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to history_of_past_illness by keyword")
        elif any(keyword in section_title for keyword in ["laboratory", "lab result", "diagnostic test"]):
            if entries:
                extended_sections["laboratory_results"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to laboratory_results by keyword")
        elif any(keyword in section_title for keyword in ["advance directive", "living will", "healthcare proxy"]):
            if entries:
                extended_sections["advance_directives"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Mapped '{section_title}' to advance_directives by keyword")
        else:
            # Any other section with data goes to additional_sections
            if entries:
                extended_sections["additional_sections"].append(section)
                logger.info(f"[EXTENDED SECTIONS] Added '{section_title}' to additional_sections")
    
    # Log summary
    total_extended = sum(len(sections) for sections in extended_sections.values())
    logger.info(f"[EXTENDED SECTIONS] Detected {total_extended} extended sections total")
    
    return extended_sections


def has_meaningful_administrative_data(admin_data):
    """
    Check if administrative data contains meaningful content.
    Returns True if the structure exists, even if fields are empty,
    to allow template to render placeholder content.
    """
    if not admin_data or not isinstance(admin_data, dict):
        return False

    # Check if we have the main structure with expected keys
    expected_keys = [
        "document_creation_date",
        "document_last_update_date",
        "document_version_number",
        "patient_contact_info",
        "author_hcp",
        "legal_authenticator",
        "custodian_organization",
        "preferred_hcp",
        "guardian",
        "other_contacts",
    ]

    # If we have most of the expected structure, consider it meaningful
    # This allows templates to render even with empty/None values
    present_keys = sum(1 for key in expected_keys if key in admin_data)
    if present_keys >= 6:  # If at least 6 out of 10 keys are present
        return True

    # Original detailed checks for actual content (fallback)
    if (
        admin_data.get("document_creation_date")
        or admin_data.get("document_last_update_date")
        or admin_data.get("document_version_number")
    ):
        return True

    contact_info = admin_data.get("patient_contact_info", {})
    if contact_info.get("addresses") or contact_info.get("telecoms"):
        return True

    author_hcp = admin_data.get("author_hcp", {})
    if author_hcp.get("family_name") or (
        author_hcp.get("organization", {}).get("name")
    ):
        return True

    legal_auth = admin_data.get("legal_authenticator", {})
    if legal_auth.get("family_name") or (
        legal_auth.get("organization", {}).get("name")
    ):
        return True

    custodian = admin_data.get("custodian_organization", {})
    if custodian.get("name"):
        return True

    preferred_hcp = admin_data.get("preferred_hcp", {})
    if preferred_hcp.get("name"):
        return True

    guardian = admin_data.get("guardian", {})
    if guardian.get("family_name"):
        return True

    other_contacts = admin_data.get("other_contacts", [])
    if other_contacts and len(other_contacts) > 0:
        return True

    return False


# REFACTOR: Data processing functions (moved from template for proper MVC separation)
def prepare_enhanced_section_data(sections, service_processed=False):
    """
    Pre-process sections for template display
    Handles all value set lookups and field processing in Python
    Creates clinical-grade table structures for medical data display

    Args:
        sections: Raw sections from enhanced CDA processor or CDADisplayService
        service_processed: Boolean indicating if sections are already processed by CDADisplayService

    Returns:
        dict: Processed sections ready for clinical table display
    """
    if not sections:
        return []

    processed_sections = []

    for section in sections:
        # Handle different title formats
        section_title = section.get("title", "Unknown Section")
        if isinstance(section_title, dict):
            # If title is a dict with translated/original keys
            section_title = (
                section_title.get("translated")
                or section_title.get("original")
                or section_title.get("coded")
                or "Unknown Section"
            )
        elif isinstance(section_title, str):
            # If title is already a string, use it
            section_title = section_title
        else:
            section_title = "Unknown Section"

        processed_section = {
            "title": section_title,
            "type": section.get("type", "unknown"),
            "section_code": section.get("section_code", ""),
            "entries": [],
            "has_entries": False,
            "medical_terminology_count": 0,
            "coded_entries_count": 0,
            "clinical_table": None,  # New: structured table for clinical display
            "structured_data": section.get(
                "structured_data"
            ),  # Preserve original clinical data from NCPeH-A
            "content": section.get("content"),  # Preserve raw XML content as fallback
        }

        # If sections are already processed by CDADisplayService, use optimized path
        if service_processed:
            # CDADisplayService already provides optimized section data
            processed_section.update(
                {
                    "entries": section.get("entries", []),
                    "has_entries": section.get("has_entries", False),
                    "medical_terminology_count": section.get(
                        "medical_terminology_count", 0
                    ),
                    "coded_entries_count": section.get("coded_entries_count", 0),
                    "clinical_table": section.get("clinical_table"),
                }
            )
            logger.info(
                f"Section '{section_title}': Using CDADisplayService processed data"
            )
        else:
            # Legacy processing path for non-service processed sections
            # Process entries with proper field lookups
            entries_data = None
            entry_count = 0

            # Check multiple possible entry data sources (Enhanced CDA Processor uses 'structured_data')
            structured_data = section.get("structured_data")
            if structured_data is not None and len(structured_data) > 0:
                entries_data = section.get("structured_data", [])
                entry_count = len(entries_data)
                logger.info(
                    f"Section '{section_title}': Found {entry_count} entries in structured_data"
                )
            elif section.get("table_data"):
                entries_data = section.get("table_data", [])
                entry_count = len(entries_data)
                logger.info(
                    f"Section '{section_title}': Found {entry_count} entries in table_data"
                )
            elif section.get("entries"):
                entries_data = section.get("entries", [])
                entry_count = len(entries_data)
                logger.info(
                    f"Section '{section_title}': Found {entry_count} entries in entries"
                )
            elif section.get("content") and isinstance(section.get("content"), list):
                entries_data = section.get("content", [])
                entry_count = len(entries_data)
                logger.info(
                    f"Section '{section_title}': Found {entry_count} entries in content"
                )
            else:
                # No entries found
                entries_data = None
                entry_count = 0

            if entries_data:
                for entry in entries_data:
                    processed_entry = process_entry_for_display(
                        entry,
                        section.get("section_code", ""),
                        service_processed=service_processed,
                    )
                    processed_section["entries"].append(processed_entry)

                    # Update metrics
                    if processed_entry.get("has_medical_terminology"):
                        processed_section["medical_terminology_count"] += 1
                    if processed_entry.get("is_coded"):
                        processed_section["coded_entries_count"] += 1

                # Create clinical table structure for medical display
                processed_section["clinical_table"] = create_clinical_table(
                    entries_data,
                    section.get("section_code", ""),
                    section_title,
                    service_processed=service_processed,
                )

            processed_section["has_entries"] = len(
                processed_section["entries"]
            ) > 0 or (
                processed_section["structured_data"]
                and len(processed_section["structured_data"]) > 0
            )

        processed_sections.append(processed_section)

    return processed_sections


def create_clinical_table(
    entries_data, section_code, section_title, service_processed=False
):
    """
    Create a clinical-grade table structure for medical data display

    Args:
        entries_data: List of raw entries from enhanced CDA processor or CDADisplayService
        section_code: LOINC section code for specialized processing
        section_title: Human-readable section title
        service_processed: Boolean indicating if data is already processed by service

    Returns:
        dict: Clinical table with headers, rows, and metadata for professional display
    """
    if not entries_data:
        return None

    # If service has already provided a clinical table, use it directly
    if service_processed and isinstance(entries_data, list) and len(entries_data) > 0:
        first_entry = entries_data[0]
        if isinstance(first_entry, dict) and first_entry.get("clinical_table"):
            logger.info(
                f"Using service-provided clinical table for section {section_title}"
            )
            return first_entry.get("clinical_table")

    # Define clinical table structures by section type
    table_config = {
        "47519-4": {  # Procedures
            "headers": [
                {"key": "procedure", "label": "Procedure", "primary": True},
                {"key": "date", "label": "Date Performed", "type": "date"},
                {"key": "status", "label": "Status", "type": "status"},
                {"key": "provider", "label": "Healthcare Provider"},
                {"key": "codes", "label": "Medical Codes", "type": "codes"},
            ],
            "title": "Clinical Procedures",
            "icon": "fas fa-procedures",
        },
        "11450-4": {  # Problems/Conditions
            "headers": [
                {"key": "section_title", "label": "Section Title"},
                {"key": "problem", "label": "Problem", "primary": True},
                {"key": "problem_id", "label": "Problem ID", "type": "codes"},
                {"key": "onset_date", "label": "Onset Date", "type": "date"},
                {
                    "key": "diagnosis_assertion_status",
                    "label": "Diagnosis Assertion Status",
                    "type": "status",
                },
                {
                    "key": "health_professional",
                    "label": "Related Health Professional Name",
                },
                {
                    "key": "external_resource",
                    "label": "Related External Resource",
                    "type": "reference",
                },
            ],
            "title": "Current Problems / Diagnosis",
            "icon": "fas fa-stethoscope",
        },
        "48765-2": {  # Allergies
            "headers": [
                {"key": "code", "label": "Code", "type": "code"},
                {"key": "reaction_type", "label": "Reaction Type", "primary": True, "type": "reaction"},
                {"key": "manifestation", "label": "Clinical Manifestation", "type": "reaction"},
                {"key": "agent", "label": "Agent", "type": "allergen"},
                {"key": "time", "label": "Time", "type": "date"},
                {"key": "severity", "label": "Severity", "type": "severity"},
                {"key": "criticality", "label": "Criticality", "type": "severity"},
                {"key": "status", "label": "Status", "type": "status"},
                {"key": "certainty", "label": "Certainty", "type": "status"},
            ],
            "title": "Allergies & Adverse Reactions",
            "icon": "fas fa-exclamation-triangle",
        },
        "10160-0": {  # Medications
            "headers": [
                {"key": "medication", "label": "Medication", "primary": True},
                {"key": "dosage", "label": "Dosage & Strength"},
                {"key": "frequency", "label": "Frequency"},
                {"key": "status", "label": "Status", "type": "status"},
                {"key": "start_date", "label": "Start Date", "type": "date"},
            ],
            "title": "Current & Past Medications",
            "icon": "fas fa-pills",
        },
        "46264-8": {  # Medical Devices
            "headers": [
                {"key": "Device Type", "label": "Device Type", "primary": True, "type": "device"},
                {"key": "Device ID", "label": "Device ID", "type": "device"},
                {"key": "Implant Date", "label": "Implant Date", "type": "date"},
            ],
            "title": "Medical Devices & Implants",
            "icon": "fas fa-microchip",
        },
        "default": {  # Generic clinical data
            "headers": [
                {"key": "item", "label": "Clinical Item", "primary": True},
                {"key": "value", "label": "Value/Description"},
                {"key": "date", "label": "Date", "type": "date"},
                {"key": "status", "label": "Status", "type": "status"},
                {"key": "codes", "label": "Medical Codes", "type": "codes"},
            ],
            "title": "Clinical Information",
            "icon": "fas fa-clipboard-list",
        },
    }

    # Get configuration for this section type
    config = table_config.get(section_code, table_config["default"])

    # Process each entry into table rows
    table_rows = []
    for entry in entries_data:
        row = extract_clinical_row_data(entry, config["headers"], section_code)
        if row:
            table_rows.append(row)

    # Create clinical table structure
    clinical_table = {
        "title": config["title"],
        "icon": config["icon"],
        "section_code": section_code,
        "headers": config["headers"],
        "rows": table_rows,
        "entry_count": len(table_rows),
        "has_coded_entries": any(row.get("has_medical_codes") for row in table_rows),
        "medical_terminology_coverage": calculate_terminology_coverage(table_rows),
    }

    return clinical_table


def extract_clinical_row_data(entry, headers, section_code):
    """
    Extract clinical data from entry fields based on table configuration

    Args:
        entry: Single entry from enhanced CDA processor
        headers: Table header configuration
        section_code: Section code for specialized extraction

    Returns:
        dict: Row data structured for clinical table display
    """
    row = {
        "has_medical_codes": False,
        "terminology_quality": "basic",
        "entry_id": entry.get("id", "unknown"),
        "data": {},
    }

    fields = entry.get("fields", {})

    # Extract data for each configured column
    for header in headers:
        key = header["key"]
        header_type = header.get("type", "text")

        if key == "procedure" and section_code == "47519-4":
            # Extract procedure information using comprehensive field names
            procedure_data = extract_field_value(
                fields,
                [
                    "Procedure DisplayName",
                    "Procedure OriginalText",
                    "Procedure Code",
                    "Procedure",
                ],
            )

            # Extract specific procedure codes for medical codes column
            procedure_codes = []

            # Look for original procedure_code field from CDA processor
            for field_name, field_data in fields.items():
                # Check if this field contains original procedure_code from _extract_procedure_data
                if isinstance(field_data, dict) and "procedure_code" in str(field_data):
                    pass

                # Check for the raw data structure from CDA processor
                if (
                    field_name.lower() == "procedure_code"
                    or "procedure_code" in field_name.lower()
                ):
                    pass

            # Check for procedure code fields
            for field_name, field_data in fields.items():
                if "Procedure Code" in field_name and isinstance(field_data, dict):
                    if field_data.get("value"):
                        procedure_codes.append(
                            {
                                "code": field_data.get("value"),
                                "system": get_code_system_name(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                                "display": "",  # No display to avoid duplication
                                "field": field_name,
                                "badge": get_code_system_badge(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                            }
                        )
                elif (
                    "code" in field_name.lower()
                    and isinstance(field_data, dict)
                    and field_data.get("value")
                ):
                    procedure_codes.append(
                        {
                            "code": field_data.get("value"),
                            "system": get_code_system_name(
                                field_data.get("codeSystem", "Unknown")
                            ),
                            "display": "",  # No display to avoid duplication
                            "field": field_name,
                            "badge": get_code_system_badge(
                                field_data.get("codeSystem", "Unknown")
                            ),
                        }
                    )

            row["data"][key] = {
                "value": procedure_data.get("display_value", "Unknown Procedure"),
                "codes": procedure_codes or procedure_data.get("codes", []),
                "has_terminology": procedure_data.get("has_terminology", False)
                or len(procedure_codes) > 0,
            }

            # Use Central Terminology Service to extract additional codes if none found
            if len(procedure_codes) == 0:
                terminology_service = CentralTerminologyService()

                extracted_codes = terminology_service.extract_procedure_terminology(
                    fields
                )
                if extracted_codes["codes"]:
                    row["data"][key]["codes"] = extracted_codes["codes"]
                    row["data"][key]["has_terminology"] = True
                    logger.info(
                        f"[SUCCESS] TERMINOLOGY SERVICE: Added {len(extracted_codes['codes'])} procedure codes from CDA data"
                    )

        elif key == "provider" and section_code == "47519-4":
            # Extract healthcare provider information
            provider_parts = []

            # Try to get provider name
            provider_name = extract_field_value(
                fields, ["Healthcare Provider Name", "Provider Name", "Physician"]
            )
            if (
                provider_name.get("display_value")
                and provider_name["display_value"] != "Not specified"
            ):
                provider_parts.append(provider_name["display_value"])

            # Try to get provider organization
            provider_org = extract_field_value(
                fields,
                [
                    "Healthcare Provider Organization",
                    "Provider Organization",
                    "Hospital",
                ],
            )
            if (
                provider_org.get("display_value")
                and provider_org["display_value"] != "Not specified"
            ):
                provider_parts.append(f"({provider_org['display_value']})")

            provider_value = (
                " ".join(provider_parts) if provider_parts else "Not specified"
            )
            row["data"][key] = {
                "value": provider_value,
                "has_terminology": any(
                    [
                        provider_name.get("has_terminology"),
                        provider_org.get("has_terminology"),
                    ]
                ),
            }

        elif key == "section_title" and section_code == "11450-4":
            # Extract section title - Maps to JSON: "section/code[@code='11450-4']/@displayName"
            section_title_data = extract_field_value(
                fields,
                [
                    "Section Title",
                    "Section DisplayName",
                    "Code DisplayName",
                    "Title",
                    "Display Name",
                    "Section Name",
                ],
            )
            row["data"][key] = {
                "value": section_title_data.get(
                    "display_value", "Current Problems / Diagnosis"
                ),
                "has_terminology": section_title_data.get("has_terminology", False),
            }

        elif key == "problem" and section_code == "11450-4":
            # Extract problem information using Central Terminology Service
            # No hardcoded medical conditions - extract from CDA document

            # Use Central Terminology Service to extract condition terminology
            terminology_service = CentralTerminologyService()
            condition_terminology = terminology_service.extract_condition_terminology(
                fields
            )

            # Use extracted terminology or fallback to standard field extraction
            if (
                condition_terminology["has_terminology"]
                and condition_terminology["display_value"] != "Unknown Problem"
            ):
                problem_value = condition_terminology["display_value"]
                has_terminology = True
            else:
                # Standard field extraction as fallback
                problem_data = extract_field_value(
                    fields,
                    [
                        "Value DisplayName",
                        "Problem DisplayName",
                        "Observation Value DisplayName",
                        "DisplayName",
                        "Problem Description",
                        "Condition Name",
                        "Problem",
                        "Value Display Name",
                        "Display Name",
                        "Condition",
                        "Disease",
                        "Diagnosis",
                        "Clinical Finding",
                        "Medical Problem",
                    ],
                )
                problem_value = problem_data.get("display_value", "Unknown Problem")
                has_terminology = problem_value != "Unknown Problem"

            row["data"][key] = {
                "value": problem_value,
                "codes": condition_terminology.get("codes", []),
                "has_terminology": has_terminology,
            }

        elif key == "problem_id" and section_code == "11450-4":
            # Extract problem ID information - New column for JSON mapping
            # Maps to "Problem ID" field in JSON: "entry/act/.../observation/.../value/@code"
            problem_id_data = extract_field_value(
                fields, ["Problem Code", "Value Code", "Problem ID", "Code"]
            )

            # Extract specific problem codes for medical codes column
            problem_codes = []

            # Check for problem code fields - Look specifically for the medical codes we saw in XML
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict) and field_data.get("value"):
                    field_value = str(field_data.get("value"))

                    # Check if this looks like a medical code (SNOMED CT codes are typically 6-18 digits)
                    if field_value.isdigit() and len(field_value) >= 6:
                        logger.info(
                            f"[TARGET] Found medical code: {field_value} in field {field_name}"
                        )

                        # Create a code entry for this
                        problem_codes.append(
                            {
                                "code": field_value,
                                "system": get_code_system_name(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )  # Default to SNOMED CT
                                ),
                                "display": "",
                                "field": field_name,
                                "badge": get_code_system_badge(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                            }
                        )

                # Also check traditional field patterns
                elif "Problem Code" in field_name and isinstance(field_data, dict):
                    if field_data.get("value"):
                        problem_codes.append(
                            {
                                "code": field_data.get("value"),
                                "system": get_code_system_name(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                                "display": "",
                                "field": field_name,
                                "badge": get_code_system_badge(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                            }
                        )

            # Apply our enhanced 3-tier strategy for diabetes recognition (and other conditions)
            if len(problem_codes) == 0:
                # Get the problem display name to check for condition patterns
                problem_display_data = extract_field_value(
                    fields,
                    [
                        "Problem DisplayName",
                        "Problem",
                        "Condition",
                        "Value DisplayName",
                    ],
                )
                problem_display = problem_display_data.get("display_value", "").lower()

                # Use Central Terminology Service to extract codes from CDA fields
                terminology_service = CentralTerminologyService()

                extracted_codes = terminology_service.extract_medical_codes_from_fields(
                    fields
                )
                if extracted_codes:
                    problem_codes = extracted_codes
                    logger.info(
                        f"[TARGET] TERMINOLOGY SERVICE: Found {len(problem_codes)} medical codes from CDA data"
                    )
                else:
                    logger.info(
                        "[INFO] TERMINOLOGY SERVICE: No medical codes found in CDA fields"
                    )

            row["data"][key] = {
                "value": problem_codes[0]["code"] if problem_codes else "No Code",
                "codes": problem_codes,
                "has_terminology": len(problem_codes) > 0,
                "type": "codes",
            }

        elif key == "diagnosis_assertion_status" and section_code == "11450-4":
            # Extract diagnosis assertion status - New column for JSON mapping
            # Maps to "Diagnosis Assertion Status" field in JSON: "entry/act/.../observation/.../value"
            assertion_data = extract_field_value(
                fields,
                [
                    "Diagnosis Assertion Status",
                    "Assertion Status",
                    "Status",
                    "Diagnosis Status",
                ],
            )
            row["data"][key] = {
                "value": assertion_data.get("display_value", "Not specified"),
                "type": "status",
                "css_class": get_status_css_class(
                    assertion_data.get("display_value", "")
                ),
            }

        elif key == "health_professional" and section_code == "11450-4":
            # Extract related health professional name - New column for JSON mapping
            # Maps to "Related Health Professional Name" field in JSON: "entry/act/.../assignedEntity/assignedPerson/name"
            professional_data = extract_field_value(
                fields,
                [
                    "Related Health Professional Name",
                    "Health Professional Name",
                    "Healthcare Provider Name",
                    "Assigned Person Name",
                    "Provider Name",
                    "Physician Name",
                ],
            )
            row["data"][key] = {
                "value": professional_data.get("display_value", "Not specified"),
                "has_terminology": professional_data.get("has_terminology", False),
            }

        elif key == "external_resource" and section_code == "11450-4":
            # Extract related external resource - New column for JSON mapping
            # Maps to "Related External Resource" field in JSON: "entry/act/.../reference/@value"
            resource_data = extract_field_value(
                fields,
                [
                    "Related External Resource",
                    "External Resource",
                    "Reference Value",
                    "Reference",
                    "External Reference",
                ],
            )
            row["data"][key] = {
                "value": resource_data.get("display_value", "Not specified"),
                "type": "reference",
                "has_terminology": resource_data.get("has_terminology", False),
            }

        elif key == "allergen" and section_code == "48765-2":
            # Extract allergen information
            allergen_data = extract_field_value(
                fields, ["Allergen DisplayName", "Allergen Code", "Allergen"]
            )
            row["data"][key] = {
                "value": allergen_data.get("display_value", "Unknown Allergen"),
                "codes": allergen_data.get("codes", []),
                "has_terminology": allergen_data.get("has_terminology", False),
            }

        elif key == "medication" and section_code == "10160-0":
            # Extract medication information using comprehensive field names
            medication_data = extract_field_value(
                fields,
                [
                    "Medication Name",
                    "Medication DisplayName",
                    "Medication Description",
                    "Medication Code",
                    "Medication",
                ],
            )
            row["data"][key] = {
                "value": medication_data.get("display_value", "Unknown Medication"),
                "codes": medication_data.get("codes", []),
                "has_terminology": medication_data.get("has_terminology", False),
            }

        elif key == "dosage" and section_code == "10160-0":
            # Extract dosage information from comprehensive fields
            dosage_parts = []

            # Try to get strength information
            strength_data = extract_field_value(
                fields, ["Strength Value", "Strength", "Dosage"]
            )
            if (
                strength_data.get("display_value")
                and strength_data["display_value"] != "Not specified"
            ):
                dosage_parts.append(strength_data["display_value"])

            # Try to get strength unit
            unit_data = extract_field_value(
                fields, ["Strength Unit", "Unit", "Dosage Unit"]
            )
            if (
                unit_data.get("display_value")
                and unit_data["display_value"] != "Not specified"
            ):
                if dosage_parts:
                    dosage_parts[-1] += f" {unit_data['display_value']}"
                else:
                    dosage_parts.append(unit_data["display_value"])

            # Try to get dose form
            form_data = extract_field_value(
                fields, ["Dose Form Name", "Form", "Dosage Form"]
            )
            if (
                form_data.get("display_value")
                and form_data["display_value"] != "Not specified"
            ):
                dosage_parts.append(form_data["display_value"])

            dosage_value = " - ".join(dosage_parts) if dosage_parts else "Not specified"
            row["data"][key] = {
                "value": dosage_value,
                "has_terminology": any(
                    [
                        strength_data.get("has_terminology"),
                        unit_data.get("has_terminology"),
                        form_data.get("has_terminology"),
                    ]
                ),
            }

        elif key == "frequency" and section_code == "10160-0":
            # Extract frequency information from comprehensive fields
            frequency_parts = []

            # Try to get frequency period value and unit
            period_value = extract_field_value(
                fields, ["Frequency Period Value", "Period Value", "Frequency"]
            )
            if (
                period_value.get("display_value")
                and period_value["display_value"] != "Not specified"
            ):
                frequency_parts.append(period_value["display_value"])

            period_unit = extract_field_value(
                fields, ["Frequency Period Unit", "Period Unit", "Frequency Unit"]
            )
            if (
                period_unit.get("display_value")
                and period_unit["display_value"] != "Not specified"
            ):
                if frequency_parts:
                    frequency_parts[-1] += f" {period_unit['display_value']}"
                else:
                    frequency_parts.append(period_unit["display_value"])

            # Fallback to general frequency fields
            if not frequency_parts:
                frequency_data = extract_field_value(
                    fields, ["Schedule", "Timing", "Dosing Frequency"]
                )
                if frequency_data.get("display_value") != "Not specified":
                    frequency_parts.append(frequency_data["display_value"])

            frequency_value = (
                " ".join(frequency_parts) if frequency_parts else "Not specified"
            )
            row["data"][key] = {
                "value": frequency_value,
                "has_terminology": any(
                    [
                        period_value.get("has_terminology"),
                        period_unit.get("has_terminology"),
                    ]
                ),
            }

        elif key == "status":
            # Extract status information - enhanced for different section types
            status_fields = ["Status", "Statut", "State"]

            # Add comprehensive status fields based on section type
            if section_code == "10160-0":  # Medications
                status_fields = [
                    "Status Code",
                    "statusCode",
                    "Treatment Status",
                ] + status_fields
            elif section_code == "47519-4":  # Procedures
                status_fields = [
                    "Procedure Status",
                    "Procedure Status Code",
                    "Status Code",
                ] + status_fields
            elif section_code == "48765-2":  # Allergies
                status_fields = ["Allergy Status", "Status Code"] + status_fields
            elif section_code == "11450-4":  # Problems
                status_fields = ["Problem Status", "Status Code"] + status_fields

            status_data = extract_field_value(fields, status_fields)
            row["data"][key] = {
                "value": status_data.get("display_value", "Unknown"),
                "type": "status",
                "css_class": get_status_css_class(status_data.get("display_value", "")),
            }

        elif key == "severity":
            # Extract severity information
            severity_data = extract_field_value(fields, ["Severity", "Sévérité"])
            row["data"][key] = {
                "value": severity_data.get("display_value", "Not specified"),
                "type": "severity",
                "css_class": get_severity_css_class(
                    severity_data.get("display_value", "")
                ),
            }

        elif header_type == "date":
            # Extract date information - enhanced for different clinical contexts
            date_fields = [key.title(), f"{key.replace('_', ' ').title()}", "Date"]

            # Add specific date field mappings based on section type
            if section_code == "10160-0":  # Medications
                if key == "start_date":
                    date_fields.extend(
                        [
                            "Treatment Start Date",
                            "Start Date",
                            "Effective Time Low",
                            "Begin Date",
                            "Début",
                        ]
                    )
                elif key == "end_date":
                    date_fields.extend(
                        [
                            "Treatment End Date",
                            "End Date",
                            "Effective Time High",
                            "Stop Date",
                            "Fin",
                        ]
                    )
                else:
                    date_fields.extend(
                        [
                            "Treatment Start Date",
                            "Effective Time",
                            "Medication Date",
                            "Date de médication",
                        ]
                    )
            elif section_code == "47519-4":  # Procedures
                if key == "date" or key == "date_performed":
                    date_fields = [
                        "Procedure Date",
                        "Procedure Start Date",
                        "Procedure End Date",
                        "Effective Time",
                        "Date Performed",
                        "Performed Date",
                    ] + date_fields
                elif key == "start_date":
                    date_fields.extend(
                        ["Procedure Start Date", "Start Date", "Begin Date"]
                    )
                elif key == "end_date":
                    date_fields.extend(
                        ["Procedure End Date", "End Date", "Completion Date"]
                    )
            elif section_code == "48765-2":  # Allergies
                if key == "onset_date":
                    date_fields.extend(
                        [
                            "Allergy Onset Date",
                            "Onset Date",
                            "First Noted",
                            "Reaction Date",
                        ]
                    )
            elif section_code == "11450-4":  # Problems
                if key == "onset_date":
                    date_fields.extend(
                        ["Problem Onset Date", "Onset Date", "Diagnosis Date"]
                    )

            date_data = extract_field_value(fields, date_fields)
            row["data"][key] = {
                "value": date_data.get("display_value", "Not specified"),
                "type": "date",
                "formatted": format_clinical_date(date_data.get("display_value", "")),
            }

        elif key == "codes":
            # [TARGET] SOLUTION: Extract original procedure codes directly from CDA before translation
            original_codes = []

            logger.info(
                f"[INFO] CODES COLUMN: Analyzing {len(fields)} fields for original procedure codes"
            )

            # Strategy 1: Look for fields that contain procedure_code from _extract_procedure_data
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict):
                    logger.info(f"[INFO] Field '{field_name}': {field_data}")

                    # Check for the original procedure_code field (from CDA processor)
                    if field_data.get("procedure_code"):
                        logger.info(
                            f"[TARGET] FOUND original procedure_code: {field_data['procedure_code']}"
                        )
                        original_codes.append(
                            {
                                "code": field_data["procedure_code"],
                                "system": field_data.get("code_system", "SNOMED CT"),
                                "display": "",
                                "field": field_name,
                                "badge": get_code_system_badge(
                                    "2.16.840.1.113883.6.96"
                                ),
                            }
                        )

                    # Check for any field with a "code" property that's numeric
                    elif (
                        field_data.get("code")
                        and str(field_data["code"]).isdigit()
                        and len(str(field_data["code"])) >= 6
                    ):
                        logger.info(
                            f"[TARGET] FOUND numeric code: {field_data['code']}"
                        )
                        original_codes.append(
                            {
                                "code": str(field_data["code"]),
                                "system": get_code_system_name(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                                "display": "",
                                "field": field_name,
                                "badge": get_code_system_badge(
                                    field_data.get(
                                        "codeSystem", "2.16.840.1.113883.6.96"
                                    )
                                ),
                            }
                        )

            # Strategy 2: If no original codes found, search for numeric patterns in any field values
            if not original_codes:
                import re

                logger.info(
                    "[INFO] No direct codes found, searching for numeric patterns..."
                )
                for field_name, field_data in fields.items():
                    if isinstance(field_data, dict) and field_data.get("value"):
                        value_str = str(field_data["value"])
                        # Look for SNOMED CT style codes (typically 6-18 digits)
                        numeric_codes = re.findall(r"\b\d{6,18}\b", value_str)
                        for code in numeric_codes:
                            logger.info(
                                f"[TARGET] EXTRACTED numeric pattern: {code} from field {field_name}"
                            )
                            original_codes.append(
                                {
                                    "code": code,
                                    "system": "SNOMED CT",
                                    "display": "",
                                    "field": f"{field_name}_pattern",
                                    "badge": get_code_system_badge(
                                        "2.16.840.1.113883.6.96"
                                    ),
                                }
                            )

            # Strategy 3: Use Central Terminology Service for code extraction
            if not original_codes:
                terminology_service = CentralTerminologyService()

                logger.info(
                    "[INFO] TERMINOLOGY SERVICE: Extracting codes from CDA fields..."
                )
                original_codes = terminology_service.extract_medical_codes_from_fields(
                    fields
                )

                if original_codes:
                    logger.info(
                        f"[SUCCESS] TERMINOLOGY SERVICE: Found {len(original_codes)} codes from CDA data"
                    )
                else:
                    logger.info(
                        "ℹ️ TERMINOLOGY SERVICE: No medical codes found in CDA fields - this is normal for some entries"
                    )

            logger.info(
                f"[SUCCESS] CODES RESULT: Found {len(original_codes)} original codes"
            )
            for code in original_codes:
                logger.info(
                    f"  [LIST] {code['code']} ({code['system']}) from {code['field']}"
                )

            row["data"][key] = {
                "codes": original_codes,
                "count": len(original_codes),
                "has_codes": len(original_codes) > 0,
            }

        elif key == "Device Type" and section_code == "46264-8":
            # Special handling for Device Type to preserve device_code
            device_type_data = extract_field_value(fields, [key, "Device Type", "Type"])
            row["data"][key] = {
                "value": device_type_data.get("display_value", "Not specified"),
                "has_terminology": device_type_data.get("has_terminology", False),
                "device_code": device_type_data.get("device_code", ""),  # Preserve device code
            }

        else:
            # Generic field extraction
            generic_data = extract_field_value(fields, [key.title(), key])
            row["data"][key] = {
                "value": generic_data.get("display_value", "Not specified"),
                "has_terminology": generic_data.get("has_terminology", False),
            }

        # Update row-level terminology tracking
        if row["data"][key].get("has_terminology") or row["data"][key].get("codes"):
            row["has_medical_codes"] = True
            row["terminology_quality"] = "enhanced"

    return row


def extract_field_value(fields, field_patterns):
    """
    Extract value from fields using multiple possible field name patterns

    Args:
        fields: Dictionary of field data from entry
        field_patterns: List of possible field names to check

    Returns:
        dict: Extracted value with metadata
    """
    result = {
        "display_value": "Not specified",
        "original_value": None,
        "has_terminology": False,
        "codes": [],
        "device_code": "",  # Add device_code to result
        "code_system": "",  # Add code_system to result
    }

    for pattern in field_patterns:
        if pattern in fields:
            field_data = fields[pattern]

            if isinstance(field_data, dict):
                # Structured field with value set information
                display_value = (
                    field_data.get("value")
                    or field_data.get("display_name")
                    or field_data.get("displayName")
                )

                if display_value and display_value not in ["Unknown", "Not specified"]:
                    result["display_value"] = display_value
                    result["original_value"] = field_data.get("original_value")
                    result["has_terminology"] = field_data.get("has_valueset", False)
                    
                    # Preserve device_code and code_system for medical devices
                    result["device_code"] = field_data.get("device_code", "")
                    result["code_system"] = field_data.get("code_system", "")

                    # Extract codes if available
                    if field_data.get("code"):
                        result["codes"].append(
                            {
                                "code": field_data.get("code"),
                                "system": field_data.get("codeSystem", "Unknown"),
                                "display": display_value,
                            }
                        )

                    # Handle procedure codes with direct value field containing the code
                    elif (
                        "Code" in pattern
                        and field_data.get("value")
                        and pattern != "Procedure DisplayName"
                    ):
                        # This handles cases where the code is directly in the value field
                        result["codes"].append(
                            {
                                "code": field_data.get("value"),
                                "system": field_data.get("codeSystem", "SNOMED CT"),
                                "display": field_data.get(
                                    "display_name", display_value
                                ),
                            }
                        )

                    break

            elif isinstance(field_data, str) and field_data not in [
                "Unknown",
                "Not specified",
                "",
            ]:
                result["display_value"] = field_data
                break

    return result


def extract_all_medical_codes(fields):
    """
    Extract all medical codes from entry fields with enhanced procedure code support

    Args:
        fields: Dictionary of field data

    Returns:
        list: List of medical code dictionaries
    """
    codes = []

    for field_name, field_data in fields.items():
        if isinstance(field_data, dict):
            # Check for direct code property
            if field_data.get("code"):
                codes.append(
                    {
                        "code": field_data.get("code"),
                        "system": get_code_system_name(
                            field_data.get("codeSystem", "Unknown")
                        ),
                        "display": "",  # No display to avoid duplication
                        "field": field_name,
                        "badge": get_code_system_badge(
                            field_data.get("codeSystem", "Unknown")
                        ),
                    }
                )

            # Enhanced extraction for procedure codes specifically
            elif "Procedure Code" in field_name and field_data.get("value"):
                # Handle both simple values and complex structures with translations
                field_value = field_data.get("value")

                if isinstance(field_value, dict) and field_value.get("original_code"):
                    # New structure with preserved original code
                    codes.append(
                        {
                            "code": field_value.get(
                                "original_code"
                            ),  # Use original numeric code
                            "system": get_code_system_name(
                                field_value.get("codeSystem", "2.16.840.1.113883.6.96")
                            ),
                            "display": "",  # Minimal display - no duplication
                            "field": field_name,
                            "badge": get_code_system_badge(
                                field_value.get("codeSystem", "2.16.840.1.113883.6.96")
                            ),
                        }
                    )
                elif field_value:
                    # Fallback for simple string values
                    codes.append(
                        {
                            "code": field_value,
                            "system": get_code_system_name(
                                field_data.get("codeSystem", "2.16.840.1.113883.6.96")
                            ),
                            "display": "",  # No display to avoid duplication
                            "field": field_name,
                            "badge": get_code_system_badge(
                                field_data.get("codeSystem", "2.16.840.1.113883.6.96")
                            ),
                        }
                    )
                    logger.info(
                        f"[SUCCESS] ADDED SIMPLE PROCEDURE CODE: {field_value} from {field_name}"
                    )

            # Check for nested code structures (common in CDA)
            elif isinstance(field_data.get("value"), dict) and field_data["value"].get(
                "code"
            ):
                nested_code = field_data["value"]
                codes.append(
                    {
                        "code": nested_code.get("code"),
                        "system": get_code_system_name(
                            nested_code.get("codeSystem", "Unknown")
                        ),
                        "display": "",  # No display to avoid duplication
                        "field": field_name,
                        "badge": get_code_system_badge(
                            nested_code.get("codeSystem", "Unknown")
                        ),
                    }
                )

    return codes


def get_code_system_name(oid_or_name):
    """
    Convert OID or system identifier to readable name
    Comprehensive mapping for international code systems

    Args:
        oid_or_name: OID string or system name

    Returns:
        str: Human-readable system name
    """
    system_mapping = {
        # International Standards
        "2.16.840.1.113883.6.96": "SNOMED CT",
        "2.16.840.1.113883.6.1": "LOINC",
        "2.16.840.1.113883.6.88": "RxNorm",
        "2.16.840.1.113883.6.3": "ICD-10-CM",
        "2.16.840.1.113883.6.4": "ICD-10-PCS",
        "2.16.840.1.113883.6.103": "ICD-9-CM",
        "2.16.840.1.113883.6.104": "ICD-9-PCS",
        "2.16.840.1.113883.5.83": "UCUM",
        "2.16.840.1.113883.6.73": "ATC",
        # European/WHO Standards
        "2.16.840.1.113883.6.14": "ICD-10-WHO",
        "1.2.250.1.213.1.1.4.1": "CIM-10-FR",  # French ICD-10
        "2.16.840.1.113883.3.989.12.2": "EDQM",  # European standards
        "2.16.840.1.113883.6.259": "ISO 11238",  # Substance codes
        # Already readable names
        "SNOMED CT": "SNOMED CT",
        "LOINC": "LOINC",
        "RxNorm": "RxNorm",
        "ICD-10": "ICD-10",
        "ICD-9": "ICD-9",
        "UCUM": "UCUM",
        "ATC": "ATC",
        "EDQM": "EDQM",
    }

    return system_mapping.get(oid_or_name, f"Code System ({oid_or_name})")


def get_code_system_badge(oid_or_name):
    """
    Get CSS badge class for code system with expanded international support

    Args:
        oid_or_name: OID string or system name

    Returns:
        str: CSS badge class
    """
    badge_mapping = {
        # International Standards - Primary colors
        "2.16.840.1.113883.6.96": "badge bg-primary",  # SNOMED CT - Blue
        "2.16.840.1.113883.6.1": "badge bg-success",  # LOINC - Green
        "2.16.840.1.113883.6.88": "badge bg-warning",  # RxNorm - Orange
        "2.16.840.1.113883.6.3": "badge bg-danger",  # ICD-10-CM - Red
        "2.16.840.1.113883.6.4": "badge bg-danger",  # ICD-10-PCS - Red
        "2.16.840.1.113883.6.103": "badge bg-secondary",  # ICD-9-CM - Gray
        "2.16.840.1.113883.6.104": "badge bg-secondary",  # ICD-9-PCS - Gray
        "2.16.840.1.113883.5.83": "badge bg-info",  # UCUM - Light blue
        "2.16.840.1.113883.6.73": "badge bg-dark",  # ATC - Dark
        # European/WHO Standards
        "2.16.840.1.113883.6.14": "badge bg-danger",  # ICD-10-WHO - Red
        "1.2.250.1.213.1.1.4.1": "badge bg-danger",  # French ICD-10 - Red
        "2.16.840.1.113883.3.989.12.2": "badge bg-info",  # EDQM - Light blue
        "2.16.840.1.113883.6.259": "badge bg-secondary",  # ISO 11238 - Gray
        # Readable names
        "SNOMED CT": "badge bg-primary",
        "LOINC": "badge bg-success",
        "RxNorm": "badge bg-warning",
        "ICD-10": "badge bg-danger",
        "ICD-9": "badge bg-secondary",
        "UCUM": "badge bg-info",
        "ATC": "badge bg-dark",
        "EDQM": "badge bg-info",
    }

    return badge_mapping.get(oid_or_name, "badge bg-outline-secondary")


def get_status_css_class(status_value):
    """Get CSS class for status display"""
    status_lower = status_value.lower()
    if "active" in status_lower:
        return "badge bg-success"
    elif "inactive" in status_lower or "resolved" in status_lower:
        return "badge bg-secondary"
    elif "pending" in status_lower:
        return "badge bg-warning"
    else:
        return "badge bg-info"


def get_severity_css_class(severity_value):
    """Get CSS class for severity display"""
    severity_lower = severity_value.lower()
    if "severe" in severity_lower or "high" in severity_lower:
        return "badge bg-danger"
    elif "moderate" in severity_lower or "medium" in severity_lower:
        return "badge bg-warning"
    elif "mild" in severity_lower or "low" in severity_lower:
        return "badge bg-info"
    else:
        return "badge bg-secondary"


def format_clinical_date(date_string):
    """Format date for clinical display with timezone support"""
    if not date_string or date_string in ["Not specified", "Unknown"]:
        return "Not recorded"

    # Handle Malta timezone-aware formats first
    try:
        # Check for Malta-style timezone format: YYYYMMDDHHMMSS+ZZZZ
        if "+" in date_string or (date_string.count("-") > 2):
            # Extract timezone if present
            timezone_info = ""
            core_datetime = date_string

            for i, char in enumerate(date_string):
                if char in ["+", "-"] and i >= 8:
                    core_datetime = date_string[:i]
                    timezone_info = date_string[i:]
                    break

            # Parse core datetime (YYYYMMDDHHMMSS or YYYYMMDD)
            if len(core_datetime) >= 8:
                year = core_datetime[:4]
                month = core_datetime[4:6]
                day = core_datetime[6:8]

                # Create formatted date
                from datetime import datetime

                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    formatted_date = date_obj.strftime("%B %d, %Y")

                    # Add time if present
                    if len(core_datetime) >= 14:
                        hour = core_datetime[8:10]
                        minute = core_datetime[10:12]
                        formatted_date += f" at {hour}:{minute}"

                    # Add timezone info if present
                    if timezone_info:
                        if timezone_info == "+0000":
                            formatted_date += " (UTC)"
                        else:
                            formatted_date += f" (UTC{timezone_info})"

                    return formatted_date
                except ValueError:
                    pass
    except:
        pass

    # Basic date formatting for standard formats
    try:
        from datetime import datetime

        # Try to parse common date formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
            try:
                date_obj = datetime.strptime(date_string, fmt)
                return date_obj.strftime("%B %d, %Y")
            except ValueError:
                continue
    except:
        pass

    return date_string


def calculate_terminology_coverage(table_rows):
    """Calculate percentage of entries with medical terminology"""
    if not table_rows:
        return 0

    coded_count = sum(1 for row in table_rows if row.get("has_medical_codes"))
    return round((coded_count / len(table_rows)) * 100, 1)


def process_entry_for_display(entry, section_code, service_processed=False):
    """
    Process a single entry for template display
    Handles all field lookups and terminology resolution in Python

    Args:
        entry: Raw entry from CDA processor or CDADisplayService
        section_code: Section code for specialized processing
        service_processed: Boolean indicating if entry is already processed by service

    Returns:
        dict: Processed entry with resolved terminology and display fields
    """
    # If already processed by service, return with minimal additional processing
    if service_processed and isinstance(entry, dict) and entry.get("display_fields"):
        # Entry is already processed by CDADisplayService - use optimized path
        return {
            "original_entry": entry.get("original_entry", entry),
            "display_fields": entry.get("display_fields", {}),
            "has_medical_terminology": entry.get("has_medical_terminology", False),
            "is_coded": entry.get("is_coded", False),
            "display_name": entry.get("display_name", "Unknown Item"),
            "additional_info": entry.get("additional_info", {}),
        }

    # Legacy processing path for non-service processed entries
    processed_entry = {
        "original_entry": entry,
        "display_fields": {},
        "has_medical_terminology": False,
        "is_coded": False,
        "display_name": "Unknown Item",
        "additional_info": {},
    }

    fields = entry.get("fields", {})

    # Handle different section types with specialized processing
    if section_code == "48765-2":  # Allergies
        processed_entry.update(process_allergy_entry(fields))
    elif section_code == "10160-0":  # Medications
        processed_entry.update(process_medication_entry(fields))
    elif section_code == "11450-4":  # Problems
        processed_entry.update(process_problem_entry(fields))
    else:
        processed_entry.update(process_generic_entry(fields))

    return processed_entry


def process_allergy_entry(fields):
    """Process allergy-specific fields with proper terminology lookup"""
    result = {
        "display_name": "Unknown Allergen",
        "reaction": "Unknown Reaction",
        "severity": "Unknown Severity",
        "status": "Active",
        "has_medical_terminology": False,
        "original_value": None,
    }

    # Try multiple field name patterns for allergen (handles multilingual field names)
    allergen_patterns = ["Allergen DisplayName", "Allergen Code", "Allergène"]
    for pattern in allergen_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                # Check if this field has value set information
                if field_data.get("has_valueset"):
                    result["has_medical_terminology"] = True
                    result["original_value"] = field_data.get("original_value")

                display_name = field_data.get("value") or field_data.get("display_name")
                if display_name and display_name not in ["Unknown", "Unknown Allergen"]:
                    result["display_name"] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in [
                "Unknown",
                "Unknown Allergen",
            ]:
                result["display_name"] = field_data
                break

    # Process reaction information
    reaction_patterns = ["Reaction DisplayName", "Reaction Code", "Réaction"]
    for pattern in reaction_patterns:
        if pattern in fields:
            reaction_data = fields[pattern]
            if isinstance(reaction_data, dict):
                if reaction_data.get("has_valueset"):
                    result["has_medical_terminology"] = True

                reaction_name = reaction_data.get("value") or reaction_data.get(
                    "display_name"
                )
                if reaction_name and reaction_name not in [
                    "Unknown",
                    "Unknown Reaction",
                ]:
                    result["reaction"] = reaction_name
                    break
            elif isinstance(reaction_data, str) and reaction_data not in [
                "Unknown",
                "Unknown Reaction",
            ]:
                result["reaction"] = reaction_data
                break

    # Process severity
    severity_patterns = ["Severity", "Sévérité"]
    for pattern in severity_patterns:
        if pattern in fields:
            severity_data = fields[pattern]
            if isinstance(severity_data, dict):
                severity_value = severity_data.get("value") or severity_data.get(
                    "display_name"
                )
                if severity_value and severity_value != "Unknown":
                    result["severity"] = severity_value
                    break
            elif isinstance(severity_data, str) and severity_data != "Unknown":
                result["severity"] = severity_data
                break

    # Process status
    status_patterns = ["Status", "Statut"]
    for pattern in status_patterns:
        if pattern in fields:
            status_data = fields[pattern]
            if isinstance(status_data, dict):
                status_value = status_data.get("value") or status_data.get(
                    "display_name"
                )
                if status_value:
                    result["status"] = status_value
                    break
            elif isinstance(status_data, str):
                result["status"] = status_data
                break

    return result


def process_medication_entry(fields):
    """Process medication-specific fields with proper terminology lookup"""
    result = {
        "display_name": "Unknown Medication",
        "dosage": "Not specified",
        "frequency": "Not specified",
        "status": "Active",
        "has_medical_terminology": False,
        "original_value": None,
    }

    # Try multiple field name patterns for medication
    medication_patterns = ["Medication DisplayName", "Medication Code", "Médicament"]
    for pattern in medication_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get("has_valueset"):
                    result["has_medical_terminology"] = True
                    result["original_value"] = field_data.get("original_value")

                display_name = field_data.get("value") or field_data.get("display_name")
                if display_name and display_name not in [
                    "Unknown",
                    "Unknown Medication",
                ]:
                    result["display_name"] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in [
                "Unknown",
                "Unknown Medication",
            ]:
                result["display_name"] = field_data
                break

    # Process dosage
    if "Dosage" in fields:
        dosage_data = fields["Dosage"]
        if isinstance(dosage_data, dict):
            dosage_value = dosage_data.get("value") or dosage_data.get("display_name")
            if dosage_value:
                result["dosage"] = dosage_value
        elif isinstance(dosage_data, str):
            result["dosage"] = dosage_data

    # Process frequency
    frequency_patterns = ["Frequency", "Fréquence"]
    for pattern in frequency_patterns:
        if pattern in fields:
            frequency_data = fields[pattern]
            if isinstance(frequency_data, dict):
                frequency_value = frequency_data.get("value") or frequency_data.get(
                    "display_name"
                )
                if frequency_value:
                    result["frequency"] = frequency_value
                    break
            elif isinstance(frequency_data, str):
                result["frequency"] = frequency_data
                break

    # Process status
    status_patterns = ["Status", "Statut"]
    for pattern in status_patterns:
        if pattern in fields:
            status_data = fields[pattern]
            if isinstance(status_data, dict):
                status_value = status_data.get("value") or status_data.get(
                    "display_name"
                )
                if status_value:
                    result["status"] = status_value
                    break
            elif isinstance(status_data, str):
                result["status"] = status_data
                break

    return result


def process_problem_entry(fields):
    """Process problem/condition-specific fields with proper terminology lookup
    Updated to match JSON mapping structure for "Current Problems / Diagnosis" section
    """
    result = {
        "display_name": "Unknown Problem",
        "problem_id": "No Code",
        "onset_date": "Not specified",
        "diagnosis_assertion_status": "Not specified",
        "health_professional": "Not specified",
        "external_resource": "Not specified",
        "has_medical_terminology": False,
        "original_value": None,
    }

    # Try field patterns matching JSON XPath mappings
    # "Problem" -> "entry/act/.../observation/.../value/@displayName"
    problem_patterns = [
        "Problem DisplayName",
        "Problem",
        "Value DisplayName",
        "Condition",
        "Diagnosis Name",
        "Problème",
    ]
    for pattern in problem_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get("has_valueset"):
                    result["has_medical_terminology"] = True
                    result["original_value"] = field_data.get("original_value")

                display_name = field_data.get("value") or field_data.get("display_name")
                if display_name and display_name not in ["Unknown", "Unknown Problem"]:
                    result["display_name"] = display_name
                    break
            elif isinstance(field_data, str) and field_data not in [
                "Unknown",
                "Unknown Problem",
            ]:
                result["display_name"] = field_data
                break

    # "Problem ID" -> "entry/act/.../observation/.../value/@code"
    problem_id_patterns = [
        "Problem Code",
        "Problem ID",
        "Value Code",
        "Code",
        "Condition Code",
        "Diagnosis Code",
    ]
    for pattern in problem_id_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                code_value = field_data.get("value") or field_data.get("display_name")
                if code_value and code_value != "No Code":
                    result["problem_id"] = code_value
                    result["has_medical_terminology"] = True
                    break
            elif isinstance(field_data, str) and field_data != "No Code":
                result["problem_id"] = field_data
                break

    # "Onset Date" -> "entry/act/.../effectiveTime/low/@value"
    onset_patterns = [
        "Onset Date",
        "Effective Time Low",
        "Start Date",
        "Date",
        "Problem Date",
        "Date de diagnostic",
    ]
    for pattern in onset_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                date_value = field_data.get("value") or field_data.get("display_name")
                if date_value and date_value != "Not specified":
                    result["onset_date"] = date_value
                    break
            elif isinstance(field_data, str) and field_data != "Not specified":
                result["onset_date"] = field_data
                break

    # "Diagnosis Assertion Status" -> "entry/act/.../observation/.../value"
    assertion_patterns = [
        "Diagnosis Assertion Status",
        "Assertion Status",
        "Problem Status",
        "Status",
        "Diagnosis Status",
        "Statut du diagnostic",
    ]
    for pattern in assertion_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                status_value = field_data.get("value") or field_data.get("display_name")
                if status_value and status_value != "Not specified":
                    result["diagnosis_assertion_status"] = status_value
                    break
            elif isinstance(field_data, str) and field_data != "Not specified":
                result["diagnosis_assertion_status"] = field_data
                break

    # "Related Health Professional Name" -> "entry/act/.../assignedEntity/assignedPerson/name"
    professional_patterns = [
        "Related Health Professional Name",
        "Health Professional Name",
        "Healthcare Provider Name",
        "Assigned Person Name",
        "Provider Name",
        "Physician Name",
        "Médecin",
    ]
    for pattern in professional_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                name_value = field_data.get("value") or field_data.get("display_name")
                if name_value and name_value != "Not specified":
                    result["health_professional"] = name_value
                    break
            elif isinstance(field_data, str) and field_data != "Not specified":
                result["health_professional"] = field_data
                break

    # "Related External Resource" -> "entry/act/.../reference/@value"
    resource_patterns = [
        "Related External Resource",
        "External Resource",
        "Reference Value",
        "Reference",
        "External Reference",
        "Ressource externe",
    ]
    for pattern in resource_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                resource_value = field_data.get("value") or field_data.get(
                    "display_name"
                )
                if resource_value and resource_value != "Not specified":
                    result["external_resource"] = resource_value
                    break
            elif isinstance(field_data, str) and resource_value != "Not specified":
                result["external_resource"] = field_data
                break

    return result


def process_generic_entry(fields):
    """Process generic entry fields with basic terminology lookup"""
    result = {
        "display_name": "Unknown Item",
        "has_medical_terminology": False,
        "field_data": [],
    }

    # Try common field patterns
    common_patterns = ["DisplayName", "Name", "Title", "Description", "Value"]

    for pattern in common_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get("has_valueset"):
                    result["has_medical_terminology"] = True

                display_name = field_data.get("value") or field_data.get("display_name")
                if display_name and display_name != "Unknown":
                    result["display_name"] = display_name
                    break
            elif isinstance(field_data, str) and field_data != "Unknown":
                result["display_name"] = field_data
                break

    # Collect first 4 fields for generic display
    field_count = 0
    for field_name, field_info in fields.items():
        if field_count >= 4:
            break

        field_value = "Unknown"
        has_valueset = False
        original_value = None

        if isinstance(field_info, dict):
            field_value = (
                field_info.get("value") or field_info.get("display_name") or "Unknown"
            )
            has_valueset = field_info.get("has_valueset", False)
            original_value = field_info.get("original_value")
        elif isinstance(field_info, str):
            field_value = field_info

        result["field_data"].append(
            {
                "name": field_name,
                "value": field_value,
                "has_valueset": has_valueset,
                "original_value": original_value,
            }
        )

        field_count += 1

    return result


def patient_data_view(request):
    """View for patient data form submission and display"""

    if request.method == "POST":
        form = PatientDataForm(request.POST)
        if form.is_valid():
            # Extract the NCP query parameters
            country_code = form.cleaned_data["country_code"]
            patient_id = form.cleaned_data["patient_id"]
            
            # Extract development flags
            use_local_cda = form.cleaned_data.get("use_local_cda", True)
            use_hapi_fhir = form.cleaned_data.get("use_hapi_fhir", True)

            # Log the NCP query with development options
            logger.info(
                "NCP Document Query: Patient ID %s from %s (CDA: %s, FHIR: %s)",
                patient_id,
                country_code,
                use_local_cda,
                use_hapi_fhir,
            )

            # Create search credentials for NCP-to-NCP query
            credentials = PatientCredentials(
                country_code=country_code,
                patient_id=patient_id,
            )

            # Search for matching documents with development options
            search_service = EUPatientSearchService()
            matches = search_service.search_patient(credentials, use_local_cda, use_hapi_fhir)

            if matches:
                # Get the first (best) match
                match = matches[0]

                # Create a PatientSession record for the new session management system
                import uuid
                from datetime import timedelta

                from .models import PatientSession

                # Generate a unique session ID
                session_id = str(uuid.uuid4().int)[:10]  # 10-digit session ID

                # Prepare patient data for secure storage
                patient_session_data = {
                    "file_path": match.file_path or "FHIR_BUNDLE",  # Handle None file_path for FHIR
                    "country_code": match.country_code,
                    "confidence_score": match.confidence_score,
                    "patient_data": match.patient_data,
                    "cda_content": match.cda_content,
                    # Enhanced L1/L3 CDA support
                    "l1_cda_content": match.l1_cda_content,
                    "l3_cda_content": match.l3_cda_content,
                    "l1_cda_path": match.l1_cda_path,
                    "l3_cda_path": match.l3_cda_path,
                    "preferred_cda_type": match.preferred_cda_type,
                    "has_l1": match.has_l1_cda(),
                    "has_l3": match.has_l3_cda(),
                    # Enhanced multiple document support
                    "l1_documents": match.l1_documents or [],
                    "l3_documents": match.l3_documents or [],
                    "selected_l1_index": match.selected_l1_index,
                    "selected_l3_index": match.selected_l3_index,
                    "document_summary": match.get_document_summary(),
                    "available_document_types": match.get_available_document_types(),
                    # FHIR integration - detect source type
                    "data_source": match.patient_data.get("source", "CDA"),  # "CDA" or "FHIR"
                    "is_fhir_source": match.patient_data.get("source") == "FHIR",
                    "fhir_bundle": match.patient_data.get("fhir_bundle") if match.patient_data.get("source") == "FHIR" else None,
                    "clinical_sections": match.patient_data.get("clinical_sections", []),
                    "fhir_patient_id": match.patient_data.get("fhir_patient_id") if match.patient_data.get("source") == "FHIR" else None,
                }

                # Create PatientSession for secure session management
                patient_session = PatientSession.objects.create(
                    session_id=session_id,
                    user=request.user,
                    country_code=country_code,
                    search_criteria_hash=hash(f"{country_code}_{patient_id}"),
                    status="active",
                    expires_at=timezone.now() + timedelta(hours=8),
                    client_ip=request.META.get("REMOTE_ADDR", ""),
                    last_action="patient_search_successful",
                    encryption_key_version=1,  # Set default encryption version
                )

                # Encrypt and store patient data
                patient_session.encrypt_patient_data(patient_session_data)

                # Also keep traditional session storage for backward compatibility
                request.session[f"patient_match_{session_id}"] = patient_session_data

                # Add success message
                messages.success(
                    request,
                    f"Patient documents found with {match.confidence_score*100:.1f}% confidence in {match.country_code} NCP!",
                )

                # Redirect to patient details view with the session ID
                return redirect("patient_data:patient_details", patient_id=session_id)
            else:
                # No match found
                messages.warning(
                    request,
                    f"No patient documents found for ID '{patient_id}' in {country_code} NCP.",
                )
        else:
            # Form has errors
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request - check for URL parameters to pre-fill form
        initial_data = {}

        # Check for session-based pre-fill data first (from smart search)
        session_prefill = request.session.pop("prefill_search_form", None)
        if session_prefill:
            initial_data.update(session_prefill)
            logger.info(f"Pre-filling form from session data: {session_prefill}")

        # Check for country and patient_id parameters from test patient links
        country_param = request.GET.get("country")
        patient_id_param = request.GET.get("patient_id")

        if country_param and patient_id_param:
            initial_data["country_code"] = country_param
            initial_data["patient_id"] = patient_id_param
            logger.info(
                f"Pre-filling form with country={country_param}, patient_id={patient_id_param}"
            )

            # Auto-trigger search if both parameters are provided
            # This makes "Test NCP Query" buttons work seamlessly
            auto_search = request.GET.get("auto_search", "true")
            if auto_search.lower() == "true":
                # Create form with the data and validate it
                form = PatientDataForm(initial_data)
                if form.is_valid():
                    # Create search credentials for NCP-to-NCP query
                    credentials = PatientCredentials(
                        country_code=country_param,
                        patient_id=patient_id_param,
                    )

                    # Search for matching CDA documents
                    search_service = EUPatientSearchService()
                    matches = search_service.search_patient(credentials)

                    if matches:
                        # Get the first (best) match
                        match = matches[0]

                        # Create a temporary PatientData record for session storage
                        from .models import PatientData

                        temp_patient = PatientData(
                            given_name=match.given_name,
                            family_name=match.family_name,
                            birth_date=match.birth_date,
                            gender=match.gender,
                        )
                        # Use the original patient_id_param as the ID for consistency
                        temp_patient.id = patient_id_param

                        # Store the match information in session for patient details view
                        session_key = f"patient_match_{patient_id_param}"
                        request.session[session_key] = {
                            "patient_data": match.patient_data,
                            "match_score": match.match_score,
                            "confidence_score": match.confidence_score,
                            "l1_cda_content": match.l1_cda_content,
                            "l3_cda_content": match.l3_cda_content,
                            "l1_cda_path": match.l1_cda_path,
                            "l3_cda_path": match.l3_cda_path,
                            "available_documents": match.available_documents,
                            "file_path": getattr(match, "file_path", ""),
                        }

                        # Success message with match information
                        messages.success(
                            request,
                            f"Found patient: {match.given_name} {match.family_name} (ID: {match.patient_id}) "
                            f"from {match.country_code} NCP. Confidence: {match.confidence_score:.1%}",
                        )

                        # Redirect to patient details using the original patient ID
                        return redirect(
                            "patient_data:patient_details", patient_id=patient_id_param
                        )
                    else:
                        # No match found
                        messages.warning(
                            request,
                            f"No patient documents found for ID '{patient_id_param}' in {country_param} NCP.",
                        )

        form = PatientDataForm(initial=initial_data)

    return render(request, "patient_data/patient_form.html", {"form": form})


def direct_patient_view(request, patient_id):
    """
    Direct patient access from admin console - bypasses session middleware
    Supports both:
    1. Database primary keys (from admin console View Details buttons)
    2. Actual patient identifiers (from CDA files)
    """
    import logging

    from django.http import HttpResponse

    try:
        logger = logging.getLogger(__name__)

        # Simple test response first
        if patient_id == "test":
            return HttpResponse("Direct patient view is working!")

        # STEP 1: Check if patient_id is a database primary key (from admin console)
        # This simulates using database records as signposts for automated search
        target_patient_identifier = None
        target_country_code = None
        database_record = None

        try:
            # Try to find database record by primary key
            from .models import PatientData, PatientIdentifier

            # Check if patient_id looks like a database primary key (numeric)
            if patient_id.isdigit():
                try:
                    patient_data = PatientData.objects.get(pk=int(patient_id))
                    patient_identifier = patient_data.patient_identifier
                    target_patient_identifier = patient_identifier.patient_id
                    raw_country = patient_identifier.home_member_state

                    # Normalize country code (extract 2-letter code if it's in format "Country (XX)")
                    if "(" in raw_country and ")" in raw_country:
                        # Extract code from "Ireland (IE)" -> "IE"
                        target_country_code = raw_country.split("(")[1].split(")")[0]
                    else:
                        target_country_code = raw_country

                except PatientData.DoesNotExist:
                    # Continue with original logic - maybe it's a real patient ID
                    pass

        except Exception as db_error:
            # Continue with original logic
            pass

        # STEP 2: Search CDA file system
        from .services.cda_document_index import get_cda_indexer

        indexer = get_cda_indexer()
        all_patients = indexer.get_all_patients()

        # STEP 3: Find the patient by identifier (use database info if available)
        search_patient_id = target_patient_identifier or patient_id
        search_country_code = target_country_code

        target_patient = None

        # First try: if we have database info, search by those identifiers
        if target_patient_identifier and target_country_code:
            for patient in all_patients:
                if (
                    patient["patient_id"] == target_patient_identifier
                    and patient["country_code"] == target_country_code
                ):
                    target_patient = patient
                    break

        # Second try: search by the original patient_id (for backwards compatibility)
        if not target_patient:
            for patient in all_patients:
                if patient["patient_id"] == patient_id:
                    target_patient = patient
                    break

        if not target_patient:
            if target_patient_identifier:
                messages.error(
                    request,
                    f"Patient {target_patient_identifier} from {target_country_code} not found in CDA files. The database record exists but the CDA document may not be available.",
                )
            else:
                messages.error(request, f"Patient {patient_id} not found in test data.")
            return redirect("patient_data:patient_data_form")

        # Create credentials for search (same pattern as existing working code)
        credentials = PatientCredentials(
            country_code=target_patient["country_code"],
            patient_id=target_patient["patient_id"],
        )

        # STEP 4: Execute automated search (simulating NCP-to-NCP communication)
        if database_record:
            print(
                f"DEBUG: [ROCKET] AUTOMATED SEARCH: Simulating query to {target_patient['country_code']} NCP for patient {target_patient['patient_id']}"
            )
            print(
                f"DEBUG: 🌐 In production: This would be an API call to {target_patient['country_code']} National Contact Point"
            )

        search_service = EUPatientSearchService()
        matches = search_service.search_patient(credentials)

        if not matches:
            error_msg = f"No CDA documents found for patient {target_patient_identifier or patient_id}"
            if database_record:
                error_msg += f" in {target_country_code} NCP. The database signpost exists but no corresponding CDA files were found."
            messages.error(request, error_msg)
            return redirect("patient_data:patient_data_form")

        # Get the first (best) match
        match = matches[0]

        if database_record:
            messages.success(
                request,
                f"[ROCKET] Automated search completed! Found CDA documents via {target_country_code} NCP simulation.",
            )

        # Build patient data similar to patient_details_view
        patient_data = {
            "name": f"{target_patient['given_name']} {target_patient['family_name']}",
            "given_name": target_patient["given_name"],
            "family_name": target_patient["family_name"],
            "birth_date": target_patient.get("birth_date", ""),
            "gender": target_patient.get("gender", ""),
            "primary_patient_id": target_patient["patient_id"],
            "secondary_patient_id": "",
            "patient_identifiers": [],
            "address": {},
            "contact_info": {},
        }

        # Process CDA content for display
        from .document_services import CDAProcessor

        processor = CDAProcessor()
        cda_data = processor.parse_cda_document(match.cda_content)

        # Extract patient information from the parsed data
        patient_summary = cda_data.get("patient", {})

        # Get country display name
        from .forms import COUNTRY_CHOICES

        country_display = next(
            (
                name
                for code, name in COUNTRY_CHOICES
                if code == target_patient["country_code"]
            ),
            target_patient["country_code"],
        )

        # STEP 5: Create secure session and redirect (instead of direct rendering)

        import uuid
        from datetime import timedelta

        from django.utils import timezone

        from .models import PatientSession

        # Generate a unique session ID (same pattern as normal search)
        session_id = str(uuid.uuid4().int)[:10]  # 10-digit session ID

        # Prepare patient data for secure storage (same format as normal search)
        patient_session_data = {
            "file_path": match.file_path,
            "country_code": target_patient["country_code"],
            "confidence_score": 1.0,  # 100% confidence for direct access
            "patient_data": patient_data,
            "cda_content": match.cda_content,
            # Enhanced L1/L3 CDA support
            "l1_cda_content": getattr(match, "l1_cda_content", None),
            "l3_cda_content": getattr(match, "l3_cda_content", None),
            "l1_cda_path": getattr(match, "l1_cda_path", None),
            "l3_cda_path": getattr(match, "l3_cda_path", None),
            "preferred_cda_type": "L3",
            "has_l1": getattr(match, "has_l1", False),
            "has_l3": getattr(match, "has_l3", True),
            # Enhanced multiple document support
            "l1_documents": getattr(match, "l1_documents", []),
            "l3_documents": getattr(match, "l3_documents", []),
            "selected_l1_index": 0,
            "selected_l3_index": 0,
            "document_summary": {},
            "available_document_types": ["L3"],
            # Automation context
            "automated_search": database_record is not None,
            "original_database_id": patient_id if database_record else None,
        }

        # Create PatientSession for secure session management
        try:
            patient_session = PatientSession.objects.create(
                session_id=session_id,
                user=request.user,
                country_code=target_patient["country_code"],
                search_criteria_hash=hash(
                    f"{target_patient['country_code']}_{target_patient['patient_id']}"
                ),
                status="active",
                expires_at=timezone.now() + timedelta(hours=8),
                client_ip=request.META.get("REMOTE_ADDR", ""),
                last_action=(
                    "automated_admin_search"
                    if database_record
                    else "direct_patient_access"
                ),
                encryption_key_version=1,
            )

            # Encrypt and store patient data
            patient_session.encrypt_patient_data(patient_session_data)
        except Exception as session_error:
            # Continue with traditional session storage
            pass

        # Store in traditional session for backward compatibility
        request.session[f"patient_match_{session_id}"] = patient_session_data

        # Add appropriate success message
        if database_record:
            success_message = f"[ROCKET] Automated search via database signpost completed! Retrieved CDA documents from {target_patient['country_code']} NCP with 100% confidence."
        else:
            success_message = f"Patient documents found with 100.0% confidence in {target_patient['country_code']} NCP!"

        messages.success(request, success_message)

        # Redirect to secure patient details view (same as normal search flow)
        return redirect("patient_data:patient_details", patient_id=session_id)

    except Exception as e:
        import traceback

        try:
            messages.error(request, f"Error accessing patient data: {str(e)}")
        except:
            pass
        return redirect("patient_data:patient_data_form")


def _get_display_filename(match_data):
    """Helper function to get appropriate display filename for different data sources"""
    data_source = match_data.get("data_source", "CDA")
    
    if data_source == "FHIR":
        # For FHIR sources, show FHIR patient ID or bundle info
        fhir_patient_id = match_data.get("fhir_patient_id")
        if fhir_patient_id:
            return f"FHIR Patient {fhir_patient_id}"
        return "FHIR Patient Summary Bundle"
    else:
        # For CDA sources, show file basename if available
        file_path = match_data.get("file_path")
        if file_path and file_path != "FHIR_BUNDLE":
            return os.path.basename(file_path)
        return "CDA Document"


def patient_details_view(request, patient_id):
    """
    View for displaying patient details and CDA documents

    IDENTIFIER NOTE:
    - patient_id parameter: Session ID from URL (e.g., 549316 or UUID-based)
    - This is NOT the actual patient identifier from the CDA document
    - Real patient IDs from CDA are larger numbers (e.g., aGVhbHRoY2FyZUlkMTIz)
    - Session IDs are safe for logging, real patient IDs must be protected
    """

    # First check for PatientSession record (new session management)
    from .models import PatientSession

    patient_session = None
    match_data = None

    try:
        patient_session = PatientSession.objects.get_active_session(patient_id)
        if patient_session:
            # Get patient data from the secure session
            match_data = patient_session.get_patient_data()
            logger.info(f"Found PatientSession record for session {patient_id}")
        else:
            logger.info(f"No active PatientSession found for session {patient_id}")
    except Exception as e:
        logger.warning(f"Error retrieving PatientSession for {patient_id}: {e}")

    # Fallback to traditional session storage if no PatientSession found
    if not match_data:
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)
        if match_data:
            logger.info(f"Found traditional session data for patient {patient_id}")

    # If no session data found, this might be direct access from admin console
    # Try to find the patient in the test data index and perform a search
    if not match_data:
        logger.info(
            f"No session data found for patient {patient_id}, attempting direct lookup"
        )
        try:
            from .services import EUPatientSearchService, PatientCredentials
            from .services.cda_document_index import get_cda_indexer

            indexer = get_cda_indexer()
            all_patients = indexer.get_all_patients()

            # Find the patient by patient_id
            target_patient = None
            for patient in all_patients:
                if patient["patient_id"] == patient_id:
                    target_patient = patient
                    break

            if target_patient:
                logger.info(
                    f"Found patient {patient_id} in index: {target_patient['given_name']} {target_patient['family_name']}"
                )

                # Create credentials for search
                credentials = PatientCredentials(
                    given_name=target_patient["given_name"],
                    family_name=target_patient["family_name"],
                    birth_date=target_patient.get("birth_date", ""),
                    country_code=target_patient["country_code"],
                )

                # Perform the search
                search_service = EUPatientSearchService()
                search_result = search_service.search_patient(credentials)

                if search_result:
                    logger.info(f"Direct search successful for patient {patient_id}")

                    # Store in session for future access
                    match_data = {
                        "patient_data": {
                            "name": f"{target_patient['given_name']} {target_patient['family_name']}",
                            "given_name": target_patient["given_name"],
                            "family_name": target_patient["family_name"],
                            "birth_date": target_patient.get("birth_date", ""),
                            "gender": target_patient.get("gender", ""),
                        },
                        "cda_content": search_result.cda_content,
                        "file_path": search_result.file_path,
                        "confidence_score": search_result.confidence_score,
                        "country_code": target_patient["country_code"],
                        "preferred_cda_type": "L3",
                        "has_l1": search_result.has_l1,
                        "has_l3": search_result.has_l3,
                    }

                    # Store in session
                    session_key = f"patient_match_{patient_id}"
                    request.session[session_key] = match_data

                    messages.success(
                        request,
                        f"Patient documents found with 100.0% confidence in {target_patient['country_code']} NCP!",
                    )
                else:
                    logger.warning(f"Direct search failed for patient {patient_id}")
            else:
                logger.warning(f"Patient {patient_id} not found in test data index")

        except Exception as e:
            logger.error(f"Error during direct patient lookup for {patient_id}: {e}")

    # Check if this is an NCP query result (session data exists but no DB record)
    if (
        match_data
        and not PatientData.objects.filter(
            patient_identifier__patient_id=patient_id
        ).exists()
    ):
        # This is an NCP query result - create temp patient from session data
        patient_info = match_data["patient_data"]

        # Create a temporary patient object (not saved to DB)
        # Convert birth_date string to proper date object for template formatting
        birth_date_value = patient_info.get("birth_date")
        if birth_date_value and isinstance(birth_date_value, str):
            try:
                from datetime import datetime

                birth_date_value = datetime.strptime(
                    birth_date_value, "%Y-%m-%d"
                ).date()
            except (ValueError, TypeError):
                birth_date_value = None

        patient_data = PatientData(
            id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=birth_date_value,
            gender=patient_info.get("gender", ""),
        )

        # Set access_timestamp for session-based patients to current time
        # This ensures the "Submitted" field shows a proper timestamp
        from django.utils import timezone

        patient_data.access_timestamp = timezone.now()

        logger.info(
            f"Created temporary patient object: {patient_data.given_name} {patient_data.family_name} for NCP query result: {patient_id}"
        )
    else:
        # Standard database lookup
        try:
            patient_data = PatientData.objects.filter(
                patient_identifier__patient_id=patient_id
            ).first()
            if not patient_data:
                raise PatientData.DoesNotExist
        except PatientData.DoesNotExist:
            messages.error(request, "Patient data not found.")
            return redirect("patient_data:patient_data_form")

    # Log session data status
    if match_data:
        logger.info("Found session data for patient %s", patient_id)
    else:
        logger.warning("No session data found for patient %s", patient_id)

    context = {
        "patient_data": patient_data,
        "patient_id": patient_id,  # Add patient_id for correct URL generation
        "has_cda_match": match_data is not None,
    }

    if match_data:
        # Build patient summary directly from match data

        # Check if patient identifiers are missing from session data (backwards compatibility)
        patient_data_dict = match_data["patient_data"]
        if not patient_data_dict.get(
            "primary_patient_id"
        ) and not patient_data_dict.get("secondary_patient_id"):
            logger.info(
                "Patient identifiers missing from session data, re-extracting..."
            )
            try:
                # Re-extract patient identifiers from CDA content
                import xml.etree.ElementTree as ET

                root = ET.fromstring(match_data["cda_content"])
                namespaces = {
                    "hl7": "urn:hl7-org:v3",
                    "ext": "urn:hl7-EE-DL-Ext:v1",
                }

                # Find patient role
                patient_role = root.find(".//hl7:patientRole", namespaces)
                if patient_role is not None:
                    # Extract patient IDs
                    id_elements = patient_role.findall("hl7:id", namespaces)
                    primary_patient_id = ""
                    secondary_patient_id = ""
                    patient_identifiers = []

                    for idx, id_elem in enumerate(id_elements):
                        extension = id_elem.get("extension", "")
                        root_attr = id_elem.get("root", "")
                        assigning_authority = id_elem.get("assigningAuthorityName", "")
                        displayable = id_elem.get("displayable", "")

                        if extension:
                            identifier_info = {
                                "extension": extension,
                                "root": root_attr,
                                "assigningAuthorityName": assigning_authority,
                                "displayable": displayable,
                                "type": "primary" if idx == 0 else "secondary",
                            }
                            patient_identifiers.append(identifier_info)

                            if idx == 0:
                                primary_patient_id = extension
                            elif idx == 1:
                                secondary_patient_id = extension

                    # Update the patient data with extracted identifiers
                    patient_data_dict["primary_patient_id"] = primary_patient_id
                    patient_data_dict["secondary_patient_id"] = secondary_patient_id
                    patient_data_dict["patient_identifiers"] = patient_identifiers

                    # Update the session data
                    match_data["patient_data"] = patient_data_dict
                    request.session[session_key] = match_data

                    logger.info(
                        f"Re-extracted identifiers: primary={primary_patient_id}, secondary={secondary_patient_id}"
                    )
            except Exception as e:
                logger.error(f"Error re-extracting patient identifiers: {e}")

        # Build patient summary directly from match data with terminology enhancement
        patient_summary = {
            "patient_name": match_data["patient_data"].get("name", "Unknown"),
            "birth_date": match_data["patient_data"].get("birth_date", "Unknown"),
            "gender": match_data["patient_data"].get("gender", "Unknown"),
            "primary_patient_id": match_data["patient_data"].get(
                "primary_patient_id", ""
            ),
            "secondary_patient_id": match_data["patient_data"].get(
                "secondary_patient_id", ""
            ),
            "patient_identifiers": match_data["patient_data"].get(
                "patient_identifiers", []
            ),
            "address": match_data["patient_data"].get("address", {}),
            "contact_info": match_data["patient_data"].get("contact_info", {}),
            "cda_type": match_data.get("preferred_cda_type", "L3"),
            "file_path": match_data.get("file_path"),  # Use .get() to handle None values
            "confidence_score": match_data["confidence_score"],
            "data_source": match_data["patient_data"].get("source", "CDA"),  # Track data source
        }

        # Enhance patient summary with terminology processing if CDA content available
        if match_data.get("cda_content"):
            try:
                terminology_service = CentralTerminologyService()
                enhanced_summary = terminology_service.enhance_patient_summary(
                    patient_summary, match_data["cda_content"]
                )
                if enhanced_summary:
                    patient_summary.update(enhanced_summary)
                    logger.info(
                        "[SUCCESS] Enhanced patient summary with terminology processing"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to enhance patient summary with terminology: {e}"
                )
                # Continue with basic summary if enhancement fails

        # Get country display name
        from .forms import COUNTRY_CHOICES

        country_display = next(
            (
                name
                for code, name in COUNTRY_CHOICES
                if code == match_data["country_code"]
            ),
            match_data["country_code"],
        )

        # Extract clinical arrays for Clinical Information tab
        clinical_arrays = {
            "medications": [],
            "allergies": [],
            "problems": [],
            "procedures": [],
            "vital_signs": [],
            "results": [],
            "immunizations": [],
        }
        
        try:
            # Import and use the comprehensive clinical data service
            from .services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
            
            comprehensive_service = ComprehensiveClinicalDataService()
            cda_content = match_data.get("cda_content")
            
            if cda_content:
                logger.info(f"[PATIENT_DETAILS] Extracting clinical arrays for patient {patient_id}")
                
                # Extract comprehensive data
                comprehensive_data = comprehensive_service.extract_comprehensive_clinical_data(
                    cda_content, match_data["country_code"]
                )
                
                if comprehensive_data and isinstance(comprehensive_data, dict):
                    clinical_arrays = comprehensive_service.get_clinical_arrays_for_display(
                        comprehensive_data
                    )
                    logger.info(
                        f"[PATIENT_DETAILS] Clinical arrays extracted: problems={len(clinical_arrays['problems'])}, allergies={len(clinical_arrays['allergies'])}, medications={len(clinical_arrays['medications'])}"
                    )
                    
                    # ENHANCED: Integrate Enhanced CDA Helper for 9-column allergies format
                    try:
                        from .cda_display_data_helper import CDADisplayDataHelper
                        
                        logger.info("[ENHANCED ALLERGIES] Starting Enhanced CDA Helper integration")
                        display_helper = CDADisplayDataHelper()
                        clinical_sections = display_helper.extract_clinical_sections(cda_content)
                        logger.info(f"[ENHANCED ALLERGIES] Extracted {len(clinical_sections)} clinical sections")
                        
                        # Find allergies section with clinical_table structure
                        allergies_with_clinical_table = []
                        for section in clinical_sections:
                            section_name = section.get("display_name", "").lower()
                            logger.info(f"[ENHANCED ALLERGIES] Processing section: {section.get('display_name', 'Unknown')}")
                            if any(keyword in section_name for keyword in ["allerg", "adverse", "reaction", "intolerance"]):
                                logger.info(f"[ENHANCED ALLERGIES] Found allergies section: {section.get('display_name')}")
                                if section.get("clinical_table"):
                                    logger.info(f"[ENHANCED ALLERGIES] Found enhanced allergies section: {section.get('display_name')}")
                                    # Convert clinical_table structure to allergy objects with clinical_table
                                    enhanced_allergy = {
                                        "clinical_table": section["clinical_table"],
                                        "allergen": {"name": "Enhanced Allergies", "code": {"code": "Enhanced"}},
                                        "section_name": section.get("display_name", ""),
                                        "is_enhanced": True
                                    }
                                    allergies_with_clinical_table.append(enhanced_allergy)
                                    logger.info(f"[ENHANCED ALLERGIES] Clinical table has {len(section['clinical_table'].get('headers', []))} headers and {len(section['clinical_table'].get('rows', []))} rows")
                                else:
                                    logger.info(f"[ENHANCED ALLERGIES] Section {section.get('display_name')} has no clinical_table")
                        
                        # Replace allergies with enhanced version if available
                        if allergies_with_clinical_table:
                            logger.info(f"[ENHANCED ALLERGIES] Replacing {len(clinical_arrays['allergies'])} standard allergies with {len(allergies_with_clinical_table)} enhanced allergies")
                            clinical_arrays["allergies"] = allergies_with_clinical_table
                        else:
                            logger.info("[ENHANCED ALLERGIES] No enhanced allergies found, keeping standard format")
                            
                    except Exception as e:
                        logger.warning(f"[ENHANCED ALLERGIES] Enhanced CDA Helper integration failed: {e}")
                        import traceback
                        logger.warning(f"[ENHANCED ALLERGIES] Full traceback: {traceback.format_exc()}")
                        # Keep standard allergies on error
                        
                else:
                    logger.info(f"[PATIENT_DETAILS] No comprehensive data extracted for patient {patient_id}")
            else:
                logger.info(f"[PATIENT_DETAILS] No CDA content available for patient {patient_id}")
                
        except Exception as e:
            logger.warning(f"[PATIENT_DETAILS] Failed to extract clinical arrays: {e}")
            # Keep default empty arrays

        context.update(
            {
                "patient_summary": patient_summary,
                "match_confidence": round(match_data["confidence_score"] * 100, 1),
                "source_country": match_data["country_code"],
                "source_country_display": country_display,
                "cda_file_name": _get_display_filename(match_data),
                # L1/L3 CDA availability information
                "l1_available": match_data.get("has_l1", False),
                "l3_available": match_data.get("has_l3", False),
                "preferred_cda_type": match_data.get("preferred_cda_type", "L3"),
                # Enhanced multiple document support
                "l1_documents": match_data.get("l1_documents", []),
                "l3_documents": match_data.get("l3_documents", []),
                "document_summary": match_data.get("document_summary", {}),
                "available_document_types": match_data.get(
                    "available_document_types", []
                ),
                "selected_l1_index": match_data.get("selected_l1_index", 0),
                "selected_l3_index": match_data.get("selected_l3_index", 0),
            }
        )

        # Add clinical arrays to context if available (unpack for template compatibility)
        if clinical_arrays:
            context.update(
                {
                    "medications": clinical_arrays["medications"],
                    "allergies": clinical_arrays["allergies"],
                    "problems": clinical_arrays["problems"],
                    "procedures": clinical_arrays["procedures"],
                    "vital_signs": clinical_arrays["vital_signs"],
                    "results": clinical_arrays["results"],
                    "immunizations": clinical_arrays["immunizations"],
                    "coded_results": {"blood_group": [], "diagnostic_results": []},  # Initialize for template compatibility
                }
            )
            total_clinical_items = sum(
                len(arr) for arr in clinical_arrays.values()
            )
            logger.info(
                f"[PATIENT_DETAILS] Added {total_clinical_items} clinical array items to context for patient {patient_id}"
            )
        else:
            # Ensure clinical arrays exist even if empty for template compatibility
            context.update(
                {
                    "medications": [],
                    "allergies": [],
                    "problems": [],
                    "procedures": [],
                    "vital_signs": [],
                    "results": [],
                    "immunizations": [],
                    "coded_results": {"blood_group": [], "diagnostic_results": []},  # Initialize for template compatibility
                }
            )
            logger.info(f"[PATIENT_DETAILS] Added empty clinical arrays to context for patient {patient_id}")

        return render(request, "patient_data/patient_details.html", context)
    else:
        # Session data is missing - provide fallback with clear message
        logger.warning(
            "Session data lost for patient %s, showing basic patient info only",
            patient_id,
        )

        # Add a helpful message to the user
        messages.warning(
            request,
            "Patient search data has expired. Please search again to view CDA documents and detailed information.",
        )

        # Provide basic context without CDA match data
        context.update(
            {
                "session_expired": True,
                "show_search_again_message": True,
                "session_error": "Patient search data has expired. Please search again to view CDA documents and detailed information.",
                "coded_results": {"blood_group": [], "diagnostic_results": []},  # Initialize for template compatibility
            }
        )

        return render(request, "patient_data/patient_details.html", context)


def _enhance_extended_data_for_templates(context):
    """
    Enhanced data processing for templates - Move complex logic from templates to views.

    This function processes the extended_data to:
    1. Format addresses and telecoms with proper field mapping
    2. Identify preferred communication methods
    3. Format datetime fields
    4. Create template-ready data structures
    5. Calculate counts and flags for UI components

    Args:
        context: The view context dictionary

    Returns:
        Enhanced context with processed data ready for simple template consumption
    """
    try:
        extended_data = context.get("extended_data", {})
        if not extended_data or not extended_data.get("has_meaningful_data"):
            return context

        logger.info("[TOOL] Enhanced data processing started")

        # 1. Process Contact Information
        contact_info = extended_data.get("contact_information", {})

        # Address processing - map field names for template compatibility
        processed_addresses = []
        for addr in contact_info.get("addresses", []):
            processed_addr = {
                "street_address_line": addr.get(
                    "street", ""
                ),  # Map street -> street_address_line
                "city": addr.get("city", ""),
                "postal_code": addr.get("postal_code", ""),
                "state": addr.get("state", ""),
                "country": addr.get("country", ""),
                "use": addr.get("use", ""),
                "use_label": addr.get("use_label", ""),
                # Pre-formatted full address for simple template use
                "formatted_address": _format_address_display(addr),
            }
            processed_addresses.append(processed_addr)

        # Telecom processing - identify preferred methods and format
        processed_telecoms = []
        primary_phone = None
        primary_email = None

        for telecom in contact_info.get("telecoms", []):
            processed_telecom = {
                "value": telecom.get("value", ""),
                "use": telecom.get("use", ""),
                "use_label": telecom.get("use_label", "Contact"),
                "system": telecom.get("system", "phone"),
                # Pre-determine icon for template
                "icon_class": _get_telecom_icon(telecom),
                # Pre-format for display
                "display_value": _format_telecom_display(telecom),
                "is_primary": telecom.get("use") == "HP",  # Home/Primary flag
            }
            processed_telecoms.append(processed_telecom)

            # Identify primary contacts for quick access
            if telecom.get("use") == "HP" and telecom.get("system") == "phone":
                primary_phone = processed_telecom
            elif telecom.get("system") == "email" and not primary_email:
                primary_email = processed_telecom

        # Update contact information with processed data
        enhanced_contact_info = {
            "addresses": processed_addresses,
            "telecoms": processed_telecoms,
            "total_items": len(processed_addresses) + len(processed_telecoms),
            "has_addresses": len(processed_addresses) > 0,
            "has_telecoms": len(processed_telecoms) > 0,
            "primary_phone": primary_phone,
            "primary_email": primary_email,
            "has_primary_contact": primary_phone is not None
            or primary_email is not None,
        }

        # 2. Process Navigation Tabs with enhanced counts
        navigation_tabs = []
        for tab in extended_data.get("navigation_tabs", []):
            enhanced_tab = dict(tab)  # Copy original tab data

            # Update counts based on processed data
            if tab.get("id") == "contact_details":
                enhanced_tab["count"] = enhanced_contact_info["total_items"]
            elif tab.get("id") == "contact":
                enhanced_tab["count"] = enhanced_contact_info["total_items"]

            navigation_tabs.append(enhanced_tab)

        # 3. Update extended_data with enhanced information
        enhanced_extended_data = dict(extended_data)
        enhanced_extended_data["contact_information"] = enhanced_contact_info
        enhanced_extended_data["navigation_tabs"] = navigation_tabs

        # 4. Add convenience flags for templates
        enhanced_extended_data["has_any_contact_data"] = (
            enhanced_contact_info["total_items"] > 0
        )
        enhanced_extended_data["contact_summary"] = {
            "total_addresses": len(processed_addresses),
            "total_telecoms": len(processed_telecoms),
            "has_primary_phone": primary_phone is not None,
            "has_primary_email": primary_email is not None,
        }

        context["extended_data"] = enhanced_extended_data

        logger.info(
            f"[SUCCESS] Enhanced data processing complete - {enhanced_contact_info['total_items']} contact items processed"
        )
        logger.info(
            f"   Addresses: {len(processed_addresses)}, Telecoms: {len(processed_telecoms)}"
        )
        if primary_phone:
            logger.info(f"   Primary phone: {primary_phone['display_value']}")

        return context

    except Exception as e:
        logger.error(f"[ERROR] Error in enhanced data processing: {e}")
        # Return original context if enhancement fails
        return context


def _format_address_display(addr):
    """Format address for display with proper line breaks and spacing."""
    parts = []
    if addr.get("street"):
        parts.append(addr["street"])

    city_line = []
    if addr.get("city"):
        city_line.append(addr["city"])
    if addr.get("postal_code"):
        city_line.append(addr["postal_code"])

    if city_line:
        parts.append(", ".join(city_line))

    if addr.get("state"):
        parts.append(addr["state"])
    if addr.get("country"):
        parts.append(addr["country"])

    return "<br>".join(parts) if parts else "Address not available"


def _get_telecom_icon(telecom):
    """Determine appropriate icon for telecom type."""
    system = telecom.get("system", "").lower()
    if "email" in system:
        return "fas fa-envelope"
    elif "phone" in system or "tel" in telecom.get("value", "").lower():
        return "fas fa-phone"
    elif "fax" in system:
        return "fas fa-fax"
    else:
        return "fas fa-address-card"


def _format_telecom_display(telecom):
    """Format telecom value for display."""
    value = telecom.get("value", "")
    use_label = telecom.get("use_label", "")

    # Clean up phone numbers
    if "tel:" in value:
        value = value.replace("tel:", "")

    # Add use label if available
    if use_label and use_label != "Contact":
        return f"{value} ({use_label})"
    else:
        return value


def patient_cda_view(request, session_id, cda_type=None):
    """View for displaying CDA document with structured clinical data extraction

    ARCHITECTURE: Three-tier ID system implementation
    - session_id: URL parameter for privacy-compliant navigation (from URL)
    - patient_id: Healthcare/government identifier (from CDA XML document)
    - database_id: Internal database primary key (auto-generated)

    Args:
        session_id: Session identifier from URL for privacy-compliant routing
        cda_type: Optional CDA type ('L1' or 'L3'). If None, defaults to L3 preference.
    """
    print(f"🚀 [START] patient_cda_view called: session_id={session_id}, cda_type={cda_type}")
    print(f"🔑 [SESSION] Current request.session.session_key: {request.session.session_key}")
    print(f"🔑 [SESSION] Current request.session keys: {list(request.session.keys())}")
    print("🔥🔥🔥 [CRITICAL] PATIENT_CDA_VIEW FUNCTION DEFINITELY REACHED!")
    print("🔥🔥🔥 [CRITICAL] THIS SHOULD DEFINITELY APPEAR IN LOGS!")
    
    # Check if Diana's session data is in current session
    target_key = f"patient_match_{session_id}"
    print(f"🔍 [SESSION] Looking for key: {target_key}")
    print(f"🔍 [SESSION] Key exists in current session: {target_key in request.session}")
    
    # CRITICAL FIX: If not in current session, search all database sessions
    if target_key not in request.session:
        print(f"🔧 [FIX] Session data not in current request.session, searching database...")
        from django.contrib.sessions.models import Session
        
        for db_session in Session.objects.all():
            try:
                session_data = db_session.get_decoded()
                if target_key in session_data:
                    print(f"✅ [FIX] FOUND {target_key} in database session {db_session.session_key[:10]}...")
                    # Copy the data to current request session
                    request.session[target_key] = session_data[target_key]
                    request.session.save()
                    print(f"✅ [FIX] Copied session data to current request session")
                    break
            except:
                continue
    
    from django.http import HttpResponse

    from .ui_labels import get_ui_labels

    def make_serializable(obj):
        """Recursively convert objects to JSON-serializable format"""
        if hasattr(obj, "__dict__"):
            # Convert custom objects to dictionaries
            return {key: make_serializable(value) for key, value in vars(obj).items()}
        elif isinstance(obj, dict):
            return {key: make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(item) for item in obj]
        else:
            return obj

    def _check_actual_cda_availability(session_id, cda_type):
        """Check if CDA document is actually available when session data is missing"""
        try:
            from django.contrib.sessions.models import Session

            logger.info(
                f"[HELPER] Checking actual CDA availability for {session_id}/{cda_type}"
            )

            # Search for session data directly
            session_key = f"patient_match_{session_id}"
            all_sessions = Session.objects.all()

            logger.info(f"[HELPER] Found {all_sessions.count()} total sessions")

            for i, db_session in enumerate(all_sessions):
                try:
                    session_data = db_session.get_decoded()
                    if session_key in session_data:
                        match_data = session_data[session_key]

                        logger.info(
                            f"[HELPER] Found session data for {session_id} in session {i}"
                        )
                        logger.info(
                            f"[HELPER] Match data keys: {list(match_data.keys())}"
                        )

                        # Check for the specific CDA type content
                        if cda_type.upper() == "L3":
                            cda_content = match_data.get("l3_cda_content")
                        elif cda_type.upper() == "L1":
                            cda_content = match_data.get("l1_cda_content")
                        else:
                            cda_content = match_data.get("cda_content")

                        content_length = len(cda_content) if cda_content else 0
                        logger.info(
                            f"[HELPER] {cda_type} content length: {content_length}"
                        )

                        # If we found content, the CDA type is available
                        is_available = bool(cda_content and len(cda_content) > 100)

                        logger.info(
                            f"[HELPER] Direct CDA availability check for {session_id}/{cda_type}: {is_available} (content: {content_length} chars)"
                        )
                        return is_available

                except Exception as e:
                    logger.warning(f"[HELPER] Error processing session {i}: {e}")
                    continue  # Skip corrupted sessions

            logger.warning(
                f"[HELPER] No session data found for direct CDA availability check: {session_id}/{cda_type}"
            )
            return False

        except Exception as e:
            logger.warning(
                f"[HELPER] Failed to check actual CDA availability for {session_id}/{cda_type}: {e}"
            )
            return False

    logger.info(f"PATIENT_CDA_VIEW CALLED for session_id: {session_id}")

    # IMMEDIATE TEST: Check if our code is reachable
    logger.info(
        f"[DEBUG] COMPREHENSIVE SERVICE TEST - Code is reachable for session {session_id}"
    )

    # Try FHIR Agent Service first for unified data extraction
    fhir_service = FHIRAgentService()
    
    # First, try to get FHIR bundle content from session
    fhir_bundle_content = fhir_service.get_fhir_bundle_from_session(session_id)
    
    if fhir_bundle_content:
        logger.info(f"[FHIR] Found FHIR bundle content for session {session_id}")
        fhir_data = fhir_service.extract_patient_context_data(fhir_bundle_content, session_id)
    else:
        logger.info(f"[FHIR] No FHIR bundle content found for session {session_id}")
        fhir_data = None
    
    logger.info(f"[FHIR] Attempted FHIR processing for session {session_id}, success: {fhir_data is not None and not fhir_data.get('error')}")
    
    # If FHIR processing was successful, use FHIR data for context
    if fhir_data and not fhir_data.get('error'):
        logger.info(f"[FHIR] Using FHIR data for session {session_id}")
        
        # Extract data components from FHIR response
        admin_data = fhir_data.get('administrative_data', {})
        clinical_arrays = fhir_data.get('clinical_arrays', {})
        patient_data = fhir_data.get('patient_data', {})
        patient_information = fhir_data.get('patient_information', {})
        
        # Use patient_information if available, otherwise patient_data
        patient_demographics = patient_information if patient_information else patient_data
        
        # Extract country from patient address
        def extract_country_from_address(patient_data):
            """Extract country code from patient address data"""
            addresses = patient_data.get('address', [])
            if addresses and isinstance(addresses, list) and len(addresses) > 0:
                return addresses[0].get('country', 'Unknown')
            return 'Unknown'
        
        # Extract primary patient identifier
        def extract_primary_patient_id(patient_data):
            """Extract primary patient identifier from FHIR identifiers"""
            identifiers = patient_data.get('identifier', [])
            if identifiers and isinstance(identifiers, list) and len(identifiers) > 0:
                return identifiers[0].get('value', 'Unknown')
            return patient_data.get('id', 'Unknown')  # Fallback to resource ID
        
        # Build context using FHIR data with proper template structure
        context = {
            'session_id': session_id,
            'patient_data': patient_demographics,
            'patient_identity': {
                'patient_id': extract_primary_patient_id(patient_demographics),
                'session_id': session_id,
                'given_name': patient_demographics.get('given_name', 'Unknown'),
                'family_name': patient_demographics.get('family_name', 'Patient'),
                'full_name': f"{patient_demographics.get('given_name', 'Unknown')} {patient_demographics.get('family_name', 'Patient')}",
                'birth_date': patient_demographics.get('birth_date', 'Unknown'),
                'gender': patient_demographics.get('gender', 'Unknown'),
                'patient_identifiers': patient_demographics.get('identifier', []),
                'primary_patient_id': extract_primary_patient_id(patient_demographics),
                'secondary_patient_id': None,
            },
            'admin_data': admin_data,
            'clinical_arrays': clinical_arrays,
            'fhir_processing': True,
            'data_source': 'FHIR',
            'source_country': extract_country_from_address(patient_demographics),
            'source_language': 'en',  # TODO: Extract from FHIR bundle if available
            'translation_quality': 'High',  # FHIR has structured data
            'patient_summary': {
                'data_source': 'FHIR',
                'file_path': 'FHIR_BUNDLE',
                'confidence_score': 0.95,
            },
            'has_administrative_data': bool(admin_data),
            'has_clinical_data': bool(clinical_arrays),
        }
        
        # Add clinical arrays to context for template compatibility
        if clinical_arrays:
            context.update({
                "medications": clinical_arrays.get("medications", []),
                "allergies": clinical_arrays.get("allergies", []),
                "problems": clinical_arrays.get("problems", []),
                "procedures": clinical_arrays.get("procedures", []),
                "vital_signs": clinical_arrays.get("vital_signs", []),
                "results": clinical_arrays.get("results", []),
                "immunizations": clinical_arrays.get("immunizations", []),
                "coded_results": {"blood_group": [], "diagnostic_results": []},
            })
        
        logger.info(f"[FHIR] Context built using FHIR data for session {session_id}")
        logger.info(f"[FHIR] Patient identity: {context['patient_identity']['given_name']} {context['patient_identity']['family_name']}")
        logger.info(f"[FHIR] Patient ID: {context['patient_identity']['patient_id']}")
        logger.info(f"[FHIR] Source Country: {context['source_country']}")
        logger.info(f"[FHIR] Available identifiers: {patient_demographics.get('identifier', [])}")
        logger.info(f"[FHIR] Available addresses: {patient_demographics.get('address', [])}")
        
        # Render template with FHIR data
        return render(request, "patient_data/enhanced_patient_cda.html", context)

    try:
        # Import the unified CDA display service
        from .services.cda_display_service import CDADisplayService

        # Initialize the display service with appropriate settings
        display_service = CDADisplayService(
            target_language="en", country_code=None  # Will be set based on session data
        )

        # Check if this is a database patient (from NCP gateway) or session patient
        try:
            patient_data = PatientData.objects.get(id=session_id)
            logger.info(
                f"Found NCP database patient: {patient_data.given_name} {patient_data.family_name}"
            )

            # Try to extract clinical data from structured CDA using unified service
            clinical_data = display_service.extract_patient_clinical_data(session_id)

            # Initialize administrative data and clinical arrays variables
            admin_data = None
            clinical_arrays = None
            comprehensive_data = None

            # ALWAYS run Comprehensive Clinical Data Service for administrative data and clinical arrays
            logger.info(
                f"Running Comprehensive Clinical Data Service for administrative data and clinical arrays for session {session_id}"
            )
            try:
                from .services.comprehensive_clinical_data_service import (
                    ComprehensiveClinicalDataService,
                )

                # Get CDA content for comprehensive parsing
                cda_content = display_service._get_cda_content_from_session(session_id)
                logger.info(
                    f"[DEBUG] Got CDA content length: {len(cda_content) if cda_content else 0}"
                )

                comprehensive_service = ComprehensiveClinicalDataService()

                if cda_content:
                    logger.info(
                        f"[DEBUG] Created comprehensive service, extracting data..."
                    )

                    comprehensive_data = (
                        comprehensive_service.extract_comprehensive_clinical_data(
                            cda_content
                        )
                    )
                    logger.info(
                        f"[DEBUG] Comprehensive data extracted: {bool(comprehensive_data)}"
                    )

                    # Extract administrative data for template context
                    admin_data = (
                        comprehensive_service.get_administrative_data_for_display(
                            comprehensive_data
                        )
                    )
                    logger.info(
                        f"[ADMIN SERVICE] Administrative data extracted for session {session_id}: patient={admin_data['patient_identity'].get('full_name', 'Unknown')}, document={admin_data['document_metadata'].get('document_title', 'Unknown')}"
                    )

                    # Extract clinical arrays for Clinical Information tab
                    if comprehensive_data and isinstance(comprehensive_data, dict):
                        clinical_arrays = (
                            comprehensive_service.get_clinical_arrays_for_display(
                                comprehensive_data
                            )
                        )
                        logger.info(
                            f"[CLINICAL SERVICE] Clinical arrays extracted: med={len(clinical_arrays['medications'])}, all={len(clinical_arrays['allergies'])}, prob={len(clinical_arrays['problems'])}, proc={len(clinical_arrays['procedures'])}, vs={len(clinical_arrays['vital_signs'])}"
                        )
                    else:
                        logger.info(
                            f"[CLINICAL SERVICE] No comprehensive data available, using empty clinical arrays"
                        )
                        clinical_arrays = {
                            "medications": [],
                            "allergies": [],
                            "problems": [],
                            "procedures": [],
                            "vital_signs": [],
                            "results": [],
                            "immunizations": [],
                            "medical_devices": [],
                        }

                else:
                    logger.warning(
                        f"[DEBUG] No CDA content available for session {session_id}, using empty clinical arrays"
                    )
                    # Initialize empty clinical arrays for sessions without CDA content
                    clinical_arrays = {
                        "medications": [],
                        "allergies": [],
                        "problems": [],
                        "procedures": [],
                        "vital_signs": [],
                        "results": [],
                        "immunizations": [],
                        "medical_devices": [],
                    }

                # If main clinical data extraction failed, use comprehensive service sections
                if not clinical_data or not clinical_data.get("sections"):
                    logger.info(
                        f"Main clinical data extraction returned empty, checking comprehensive data"
                    )
                    if comprehensive_data and comprehensive_data.get("sections"):
                        logger.info(
                            f"Comprehensive service found {len(comprehensive_data['sections'])} sections"
                        )
                        # Convert comprehensive service sections to expected format
                        if not clinical_data:
                            clinical_data = {"sections": []}
                        clinical_data["sections"] = comprehensive_data["sections"]

            except Exception as e:
                logger.warning(f"Comprehensive service execution failed: {e}")
                import traceback

                logger.warning(f"Traceback: {traceback.format_exc()}")
                # Initialize empty clinical arrays on error
                if clinical_arrays is None:
                    clinical_arrays = {
                        "medications": [],
                        "allergies": [],
                        "problems": [],
                        "procedures": [],
                        "vital_signs": [],
                        "results": [],
                        "immunizations": [],
                        "medical_devices": [],
                    }

            if clinical_data:
                # Structured CDA found - create enhanced context with both new and existing data
                logger.info(
                    f"Successfully extracted clinical data for session {session_id}"
                )

                # Convert our structured clinical data to the existing template format
                processed_sections = []
                for section in clinical_data["sections"]:
                    # Handle both ClinicalSection dataclass and PatientSummarySection objects
                    if hasattr(section, "display_name"):
                        # ClinicalSection dataclass object
                        section_title = section.display_name
                        entry_count = (
                            section.entry_count
                            if hasattr(section, "entry_count")
                            else 0
                        )
                        section_entries = (
                            section.entries if hasattr(section, "entries") else []
                        )
                    else:
                        # PatientSummarySection or dict from enhanced parser
                        section_title = str(
                            section.get(
                                "title", section.get("display_name", "Unknown Section")
                            )
                        )
                        section_entries = section.get("entries", [])
                        entry_count = len(section_entries)

                    processed_section = {
                        "title": section_title,
                        "medical_terminology_count": 0,
                        "has_entries": entry_count > 0,
                        "entries": [],
                    }

                    # Convert each entry
                    for entry in section_entries:
                        # Handle both ClinicalEntry dataclass and enhanced parser entry formats
                        if hasattr(entry, "primary_code"):
                            # ClinicalEntry dataclass object
                            processed_entry = {
                                "display_name": "Unknown Item",
                                "has_medical_terminology": False,
                                "status": entry.status or "Unknown",
                            }

                            # Set display name from primary code or entry type
                            if entry.primary_code and entry.primary_code.display:
                                processed_entry["display_name"] = (
                                    entry.primary_code.display
                                )
                                if entry.primary_code.code:
                                    processed_entry["has_medical_terminology"] = True
                                    processed_section["medical_terminology_count"] += 1
                            elif (
                                entry.values
                                and len(entry.values) > 0
                                and entry.values[0].display
                            ):
                                processed_entry["display_name"] = entry.values[
                                    0
                                ].display
                            else:
                                processed_entry["display_name"] = (
                                    f"Unknown {entry.entry_type.title()}"
                                )

                            # Add section-specific fields based on section type
                            if (
                                hasattr(section, "section_type")
                                and section.section_type
                                == "ALLERGIES AND ADVERSE REACTIONS"
                            ):
                                if entry.participants:
                                    processed_entry["reaction"] = ", ".join(
                                        entry.participants
                                    )
                                if entry.values:
                                    reactions = [
                                        v.display
                                        for v in entry.values
                                        if v.display and "nausea" in v.display.lower()
                                    ]
                                    if reactions:
                                        processed_entry["reaction"] = ", ".join(
                                            reactions
                                        )

                            elif (
                                hasattr(section, "section_type")
                                and section.section_type == "MEDICATIONS"
                            ):
                                if entry.values:
                                    dosages = [
                                        v.display for v in entry.values if v.display
                                    ]
                                    if dosages:
                                        processed_entry["dosage"] = ", ".join(dosages)

                        else:
                            # Enhanced parser entry (dict format) - create basic entry
                            processed_entry = {
                                "display_name": str(
                                    entry.get(
                                        "display_name",
                                        entry.get("title", "Clinical Entry"),
                                    )
                                ),
                                "has_medical_terminology": bool(entry.get("codes", [])),
                                "status": entry.get("status", "Unknown"),
                            }

                        processed_section["entries"].append(processed_entry)

                    processed_sections.append(processed_section)

                # Calculate totals for the existing template
                total_medical_terms = sum(
                    section["medical_terminology_count"]
                    for section in processed_sections
                )
                coded_sections_count = len(
                    [
                        s
                        for s in processed_sections
                        if s["medical_terminology_count"] > 0
                    ]
                )
                coded_sections_percentage = (
                    (coded_sections_count / len(processed_sections) * 100)
                    if processed_sections
                    else 0
                )

                # Create context compatible with existing template
                context = {
                    "patient_identity": {
                        "given_name": patient_data.first_name,
                        "family_name": patient_data.last_name,
                        "birth_date": (
                            str(patient_data.birth_date)
                            if patient_data.birth_date
                            else "Unknown"
                        ),
                        "gender": patient_data.gender or "Unknown",
                        "patient_id": str(session_id),
                    },
                    "source_country": (
                        str(patient_data.country_of_origin)
                        if patient_data.country_of_origin
                        else "Unknown"
                    ),
                    "cda_type": "L3",
                    "translation_quality": "High (Structured)",
                    "has_l1_cda": False,
                    "has_l3_cda": True,
                    "processed_sections": processed_sections,
                    "enhanced_allergies": match_data.get(
                        "enhanced_allergies", []
                    ),  # Add enhanced allergies directly
                    "sections_count": len(clinical_data["sections"]),
                    "medical_terms_count": total_medical_terms,
                    "coded_sections_count": coded_sections_count,
                    "coded_sections_percentage": coded_sections_percentage,
                    "uses_coded_sections": coded_sections_count > 0,
                    "clinical_data": clinical_data,  # Also provide the raw structured data
                }

                # Add administrative data to context if available
                if admin_data:
                    logger.info(
                        f"[ADMIN DATA DEBUG] admin_data keys: {admin_data.keys()}"
                    )
                    if "patient_identity" in admin_data:
                        patient_identity_data = admin_data["patient_identity"]
                        logger.info(
                            f"[ADMIN DATA DEBUG] patient_identity keys: {patient_identity_data.keys()}"
                        )
                        logger.info(
                            f"[ADMIN DATA DEBUG] patient_identifiers present: {'patient_identifiers' in patient_identity_data}"
                        )
                        if "patient_identifiers" in patient_identity_data:
                            identifiers = patient_identity_data["patient_identifiers"]
                            logger.info(
                                f"[ADMIN DATA DEBUG] patient_identifiers length: {len(identifiers) if identifiers else 0}"
                            )
                            if identifiers:
                                logger.info(
                                    f"[ADMIN DATA DEBUG] first identifier: {identifiers[0]}"
                                )

                    # ENHANCED MERGE: Properly merge patient_identity instead of overriding
                    logger.info(
                        f"[DATABASE MERGE DEBUG] Before merge - context patient_identity: {context['patient_identity'].keys()}"
                    )

                    # Preserve the existing patient_identity and merge with admin_data
                    existing_patient_identity = context["patient_identity"].copy()
                    admin_patient_identity = admin_data.get("patient_identity", {})

                    # Merge admin patient identity into existing, preserving all fields
                    merged_patient_identity = existing_patient_identity.copy()
                    merged_patient_identity.update(admin_patient_identity)

                    # Ensure patient_identifiers from admin_data is preserved
                    if "patient_identifiers" in admin_patient_identity:
                        merged_patient_identity["patient_identifiers"] = (
                            admin_patient_identity["patient_identifiers"]
                        )
                        logger.info(
                            f"[DATABASE MERGE DEBUG] Preserved patient_identifiers from admin_data: {len(admin_patient_identity['patient_identifiers'])}"
                        )

                    logger.info(
                        f"[DATABASE MERGE DEBUG] After merge - merged patient_identity has patient_identifiers: {'patient_identifiers' in merged_patient_identity}"
                    )

                    context.update(
                        {
                            "administrative_data": admin_data["document_metadata"],
                            "contact_data": admin_data["contact_data"],
                            "patient_identity": merged_patient_identity,  # Use merged identity instead of override
                            "healthcare_data": admin_data["healthcare_provider_data"],
                            "has_administrative_data": bool(
                                admin_data["document_metadata"]
                                or admin_data["patient_identity"]
                            ),
                        }
                    )
                    logger.info(
                        f"[ADMIN DATA DEBUG] After context update - patient_identity has patient_identifiers: {'patient_identifiers' in context['patient_identity']}"
                    )
                    if "patient_identifiers" in context["patient_identity"]:
                        identifiers = context["patient_identity"]["patient_identifiers"]
                        logger.info(
                            f"[ADMIN DATA DEBUG] Final patient_identifiers count: {len(identifiers)}"
                        )
                        if identifiers:
                            logger.info(
                                f"[ADMIN DATA DEBUG] Final first identifier root: {identifiers[0].get('root', 'NO ROOT')}"
                            )
                    logger.info(
                        f"[ADMIN SERVICE] Added comprehensive administrative data to context for session {session_id}"
                    )
                else:
                    # Ensure template variables exist even if no admin data
                    context.update(
                        {
                            "administrative_data": {},
                            "contact_data": {},
                            "healthcare_data": {},
                            "has_administrative_data": False,
                        }
                    )
                    logger.info(
                        f"[ADMIN SERVICE] No administrative data available for session {session_id}"
                    )

                # Add clinical arrays to context if available
                if clinical_arrays:
                    context.update(
                        {
                            "medications": clinical_arrays["medications"],
                            "allergies": clinical_arrays["allergies"],
                            "problems": clinical_arrays["problems"],
                            "procedures": clinical_arrays["procedures"],
                            "vital_signs": clinical_arrays["vital_signs"],
                            "results": clinical_arrays["results"],
                            "immunizations": clinical_arrays["immunizations"],
                            "coded_results": {"blood_group": [], "diagnostic_results": []},
                        }
                    )
                    total_clinical_items = sum(
                        len(arr) for arr in clinical_arrays.values()
                    )
                    logger.info(
                        f"[CLINICAL SERVICE] Added {total_clinical_items} clinical array items to context for session {session_id}"
                    )
                else:
                    # Ensure clinical arrays exist even if empty
                    context.update(
                        {
                            "medications": [],
                            "allergies": [],
                            "problems": [],
                            "procedures": [],
                            "vital_signs": [],
                            "results": [],
                            "immunizations": [],
                            "coded_results": {"blood_group": [], "diagnostic_results": []},
                        }
                    )
                    logger.info(
                        f"[CLINICAL SERVICE] No clinical arrays available for session {session_id}"
                    )

                # TEMPORARILY DISABLED: Early return prevents extended header extraction
                # TODO: Move extended header extraction before this point
                # return render(
                #     request,
                #     "patient_data/enhanced_patient_cda.html",
                #     context,
                #     using="jinja2",
                # )
            else:
                # Fall back to existing logic for non-structured CDAs
                logger.info(
                    f"No structured clinical data available for session {session_id}, using fallback"
                )

        except (PatientData.DoesNotExist, ValueError, ValidationError) as e:
            # This is a session-based patient from EU search or invalid UUID format
            logger.info(
                f"Session-based patient {session_id}, checking session data (reason: {type(e).__name__})"
            )

        # 2. GET PATIENT DATA FROM SESSION OR DATABASE (Using robust session search)
        from .services.session_data_service import SessionDataService

        # Use comprehensive session search (same as debug clinical view)
        match_data, debug_info = SessionDataService.get_patient_data(
            request, session_id
        )

        if not match_data:
            # No patient data found anywhere - return detailed error page
            logger.error(f"ERROR: No patient data found for session {session_id}")
            logger.error(f"Session search details:\n{debug_info}")

            error_context = SessionDataService.create_session_not_found_context(
                session_id, debug_info, request
            )
            return render(request, "patient_data/error.html", error_context)

        # EXTRACT PATIENT GOVERNMENT ID FROM SESSION TOKEN
        # Session stores patient_id (aGVhbHRoY2FyZUlkMTIz) mapped to session_id (418650)
        patient_government_id = None
        if match_data and "patient_data" in match_data:
            # Try to get the real patient government ID from session data
            patient_government_id = (
                match_data["patient_data"].get("primary_patient_id")
                or match_data["patient_data"].get("patient_id")
                or match_data["patient_data"].get("government_id")
            )

        if not patient_government_id:
            # Fallback: use session_id if no government ID found
            patient_government_id = session_id
            logger.info(
                f"[WARNING] No government ID in session, using session_id as fallback: {patient_government_id}"
            )

        # Check if this is an NCP query result (session data exists but no DB record)
        try:
            db_patient_exists = PatientData.objects.filter(id=session_id).exists()
        except (ValueError, TypeError):
            # Non-numeric session IDs (like Malta's 9999002M) can't exist in DB
            db_patient_exists = False

        if match_data and not db_patient_exists:
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=session_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for CDA display: session_id={session_id}, government_id={patient_government_id}"
            )
        else:
            # Standard database lookup
            try:
                # Try database lookup only for numeric IDs
                if session_id.isdigit():
                    patient_data = PatientData.objects.get(id=session_id)
                    logger.info(
                        f"Found database patient: {patient_data.given_name} {patient_data.family_name}"
                    )
                else:
                    # Non-numeric session IDs (like Malta 9999002M) are session-only
                    logger.info(
                        f"Non-numeric session ID {session_id}, skipping database lookup"
                    )
                    patient_data = None
            except PatientData.DoesNotExist:
                logger.warning(f"Session {session_id} not found in database")
                # Don't redirect immediately - check for session data first
                patient_data = None

            # For database patients, session data should already be found by SessionDataService
            # If not, create minimal session data to allow viewing
            session_key = f"patient_match_{session_id}"
            if not request.session.get(session_key) and patient_data is not None:
                logger.info(
                    f"Creating session data for database patient {session_id} with raw_patient_summary"
                )

                # Check if patient has raw CDA content in database
                cda_content = (
                    patient_data.raw_patient_summary
                    if hasattr(patient_data, "raw_patient_summary")
                    else None
                )
                has_cda_content = bool(cda_content and len(cda_content.strip()) > 100)

                logger.info(
                    f"Database patient {session_id} has CDA content: {has_cda_content} (length: {len(cda_content) if cda_content else 0})"
                )

                # Create match data for database patients with CDA content
                match_data = {
                    "file_path": f"database_patient_{session_id}.xml",
                    "country_code": "TEST",
                    "confidence_score": 1.0,
                    "patient_data": {
                        "given_name": patient_data.given_name,
                        "family_name": patient_data.family_name,
                        "birth_date": (
                            str(patient_data.birth_date)
                            if patient_data.birth_date
                            else ""
                        ),
                        "gender": patient_data.gender,
                    },
                    "cda_content": cda_content if has_cda_content else None,
                    "l1_cda_content": cda_content if has_cda_content else None,
                    "l3_cda_content": cda_content if has_cda_content else None,
                    "l1_cda_path": (
                        f"database_patient_{session_id}_L1.xml"
                        if has_cda_content
                        else None
                    ),
                    "l3_cda_path": (
                        f"database_patient_{session_id}_L3.xml"
                        if has_cda_content
                        else None
                    ),
                    "preferred_cda_type": "L3",
                    "has_l1": has_cda_content,
                    "has_l3": has_cda_content,
                }
                # Store in session for this request
                request.session[session_key] = match_data

        # Initialize Enhanced CDA Processor with JSON Field Mapping enhancement (hybrid approach)
        from .services.enhanced_cda_field_mapper import EnhancedCDAFieldMapper
        from .services.enhanced_cda_processor import EnhancedCDAProcessor
        from .services.patient_search_service import PatientMatch
        from .translation_utils import (
            detect_document_language,
            get_template_translations,
        )

        # Determine source language from country code with enhanced mapping
        source_language = "fr"  # Default to French
        country_code = match_data.get("country_code", "").upper()

        # Enhanced country-to-language mapping for all EU NCP countries
        country_language_map = {
            # Western Europe
            "BE": "nl",  # Belgium (Dutch/Flemish primary, French secondary)
            "DE": "de",  # Germany
            "FR": "fr",  # France
            "IE": "en",  # Ireland (English)
            "LU": "fr",  # Luxembourg (French primary, German/Luxembourgish secondary)
            "NL": "nl",  # Netherlands
            "AT": "de",  # Austria (German)
            # Southern Europe
            "ES": "es",  # Spain
            "IT": "it",  # Italy
            "PT": "pt",  # Portugal
            "GR": "el",  # Greece (Greek)
            "CY": "el",  # Cyprus (Greek primary, Turkish secondary)
            "MT": "en",  # Malta (English and Maltese)
            # Central/Eastern Europe
            "PL": "pl",  # Poland
            "CZ": "cs",  # Czech Republic (Czech)
            "SK": "sk",  # Slovakia (Slovak)
            "HU": "hu",  # Hungary (Hungarian)
            "SI": "sl",  # Slovenia (Slovenian)
            "HR": "hr",  # Croatia (Croatian)
            "RO": "ro",  # Romania (Romanian)
            "BG": "bg",  # Bulgaria (Bulgarian)
            # Baltic States
            "LT": "lt",  # Lithuania (Lithuanian)
            "LV": "lv",  # Latvia (Latvian)
            "EE": "et",  # Estonia (Estonian)
            # Nordic Countries
            "DK": "da",  # Denmark (Danish)
            "FI": "fi",  # Finland (Finnish)
            "SE": "sv",  # Sweden (Swedish)
            # Special codes
            "EU": "en",  # European Union documents (English)
            "CH": "de",  # Switzerland (German primary, but multilingual)
        }

        if country_code in country_language_map:
            source_language = country_language_map[country_code]

        # Create TWO processors for dual language support
        # 1. Original language processor - preserves source language content
        original_processor = EnhancedCDAProcessor(
            target_language=source_language, country_code=country_code
        )
        # 2. Translation processor - translates to English
        translation_processor = EnhancedCDAProcessor(
            target_language="en", country_code=country_code
        )

        # Shared field mapper
        field_mapper = EnhancedCDAFieldMapper()

        # Reconstruct PatientMatch object from session data for translation service
        # This provides the translation service with the proper search result context
        patient_info = match_data.get("patient_data", {})
        search_result = PatientMatch(
            patient_id=patient_government_id,
            given_name=patient_info.get(
                "given_name", patient_data.given_name if patient_data else "Unknown"
            ),
            family_name=patient_info.get(
                "family_name", patient_data.family_name if patient_data else "Patient"
            ),
            birth_date=patient_info.get(
                "birth_date",
                (
                    str(patient_data.birth_date)
                    if patient_data and patient_data.birth_date
                    else ""
                ),
            ),
            gender=patient_info.get(
                "gender", patient_data.gender if patient_data else ""
            ),
            country_code=country_code,
            confidence_score=match_data.get("confidence_score", 0.95),
            file_path=match_data.get("file_path"),
            l1_cda_content=match_data.get("l1_cda_content"),
            l3_cda_content=match_data.get("l3_cda_content"),
            l1_cda_path=match_data.get("l1_cda_path"),
            l3_cda_path=match_data.get("l3_cda_path"),
            cda_content=match_data.get("cda_content"),
            patient_data=patient_info,
            preferred_cda_type=cda_type or "L3",  # Use requested type or default to L3
            # Include document arrays and selected indices for proper CDA selection
            l1_documents=match_data.get("l1_documents", []),
            l3_documents=match_data.get("l3_documents", []),
            selected_l1_index=match_data.get("selected_l1_index", 0),
            selected_l3_index=match_data.get("selected_l3_index", 0),
        )

        # Use CDADisplayService for comprehensive CDA processing
        # This handles dual language, Malta enhancements, administrative data, and all section processing
        cda_display_service = CDADisplayService()

        # Get the appropriate CDA content for processing (respecting requested type)
        # ENHANCED: Search for CDA content by patient government ID across all sessions
        cda_content, actual_cda_type = search_result.get_rendering_cda(cda_type)

        # IMPLEMENT GOVERNMENT ID-BASED CDA LOOKUP
        # Search all session data for CDA documents matching the patient government ID
        if patient_government_id and patient_government_id != session_id:
            logger.info(
                f"[INFO] Searching for additional CDA content by government ID: {patient_government_id}"
            )

            # Search all session keys for this patient government ID
            additional_cda_found = False
            for session_key, session_value in request.session.items():
                if session_key.startswith("patient_match_") and isinstance(
                    session_value, dict
                ):
                    session_patient_data = session_value.get("patient_data", {})
                    session_gov_id = (
                        session_patient_data.get("primary_patient_id")
                        or session_patient_data.get("patient_id")
                        or session_patient_data.get("government_id")
                    )

                    # If we find a session with matching government ID but different session
                    if (
                        session_gov_id == patient_government_id
                        and session_key != f"patient_match_{session_id}"
                    ):
                        logger.info(
                            f"[LIST] Found additional CDA data in session: {session_key}"
                        )

                        # Get CDA content from this session
                        additional_l3_content = session_value.get("l3_cda_content")
                        additional_l1_content = session_value.get("l1_cda_content")

                        # Use the most recent or complete CDA content available
                        if additional_l3_content and len(
                            additional_l3_content.strip()
                        ) > len(cda_content.strip() if cda_content else ""):
                            logger.info(
                                f"[SYNC] Using more complete L3 CDA from {session_key}"
                            )
                            cda_content = additional_l3_content
                            actual_cda_type = "L3"
                            additional_cda_found = True
                        elif additional_l1_content and not cda_content:
                            logger.info(f"[SYNC] Using L1 CDA from {session_key}")
                            cda_content = additional_l1_content
                            actual_cda_type = "L1"
                            additional_cda_found = True

            if additional_cda_found:
                logger.info(
                    f"[SUCCESS] Successfully aggregated CDA content for government ID: {patient_government_id}"
                )
            else:
                logger.info(
                    f"ℹ️ No additional CDA content found for government ID: {patient_government_id}"
                )

        # Process CDA content using CDADisplayService for comprehensive processing
        translation_result = {"sections": []}
        sections_count = 0
        medical_terms_count = 0
        coded_sections_count = 0
        coded_sections_percentage = 0
        uses_coded_sections = False
        translation_quality = "Basic"
        extended_header_data = {}

        # DEBUG: Check CDA content before condition
        print(f"💥 [DEBUG] Pre-condition check:")
        print(f"💥 [DEBUG] cda_content exists: {cda_content is not None}")
        print(f"💥 [DEBUG] cda_content length: {len(cda_content) if cda_content else 0}")
        print(f"💥 [DEBUG] cda_content contains 'No CDA': {'<!-- No CDA content available -->' in cda_content if cda_content else False}")
        print(f"💥 [DEBUG] cda_content.strip() length: {len(cda_content.strip()) if cda_content else 0}")
        
        if (
            cda_content
            and cda_content.strip()
            and "<!-- No CDA content available -->" not in cda_content
        ):
            print(f"🎯 [DEBUG] CDA CONTENT CONDITION PASSED - Processing CDA...")
            print(f"🎯 [DEBUG] CDA Content length: {len(cda_content)}")
            print(f"🎯 [DEBUG] First 200 chars: {cda_content[:200] if cda_content else 'None'}")
            
            try:
                logger.info(
                    f"Processing {actual_cda_type} CDA content with CDADisplayService (length: {len(cda_content)}, session: {session_id}, government_id: {patient_government_id})"
                )

                # Use CDADisplayService for comprehensive processing
                # This handles dual language, Malta enhancements, administrative data, and all section processing
                processing_result = cda_display_service.extract_patient_clinical_data(
                    session_id=session_id,
                    cda_content=cda_content,
                )

                print(f"🌟 [DEBUG] CDADisplayService result: {processing_result.get('success', False) if processing_result else 'None'}")
                print(f"🌟 [DEBUG] Processing result keys: {list(processing_result.keys()) if processing_result else 'None'}")
                print(f"🌟 [DEBUG] Processing result type: {type(processing_result)}")
                print(f"🌟 [DEBUG] Processing result success value: {repr(processing_result.get('success'))}")

                if processing_result.get("success"):
                    print("✅ [DEBUG] SUCCESS CONDITION MET - Entering enhanced processing block...")
                    print(f"🔍 [DEBUG] Processing result sections: {len(processing_result.get('sections', []))}")
                    print(f"🔍 [DEBUG] Processing result keys: {list(processing_result.keys())}")
                    
                    # Use the comprehensive result from CDADisplayService
                    translation_result = processing_result

                    # Extract metrics from service result
                    sections_count = processing_result.get("sections_count", 0)
                    coded_sections_count = processing_result.get(
                        "coded_sections_count", 0
                    )
                    medical_terms_count = processing_result.get(
                        "medical_terms_count", 0
                    )
                    coded_sections_percentage = processing_result.get(
                        "coded_sections_percentage", 0
                    )
                    uses_coded_sections = processing_result.get(
                        "uses_coded_sections", False
                    )
                    translation_quality = processing_result.get(
                        "translation_quality", "Basic"
                    )

                    # Get extended header data from service result
                    extended_header_data = processing_result.get(
                        "administrative_data", {}
                    )

                    logger.info(
                        f"[SUCCESS] CDADisplayService processing successful: {sections_count} sections, "
                        f"{coded_sections_count} coded sections ({coded_sections_percentage}%), "
                        f"{medical_terms_count} medical terms"
                    )

                    # ENHANCED: Process allergies section with Enhanced CDA Processor for 9-column structure
                    print("🚀 [DEBUG] About to enter Enhanced CDA Processor block...")
                    print(f"🚀 [DEBUG] actual_cda_type: {actual_cda_type}")
                    print(f"🚀 [DEBUG] source_language: {source_language}")
                    print(f"🚀 [DEBUG] country_code: {country_code}")
                    
                    try:
                        print("🔥 [DEBUG] ENHANCED CDA PROCESSOR BLOCK REACHED!")
                        print(f"🔥 [DEBUG] Session: {session_id}, CDA Type: {actual_cda_type}")
                        print(f"🔥 [DEBUG] CDA Content length: {len(cda_content) if cda_content else 0}")
                        print(f"🔥 [DEBUG] Contains 48765-2? {'48765-2' in cda_content if cda_content else False}")
                        
                        logger.info("[ENHANCED] Invoking Enhanced CDA Processor for allergies extraction")
                        
                        # Process with Enhanced CDA Processor to extract structured allergies data
                        enhanced_processor = EnhancedCDAProcessor(
                            target_language=source_language, 
                            country_code=country_code
                        )
                        
                        # Extract allergies section specifically (code 48765-2) using XML processing
                        enhanced_allergies_data = []
                        
                        if cda_content and '48765-2' in cda_content:
                            print("🔥 [DEBUG] CDA CONTENT CONDITION MET - Processing allergies...")
                            # Parse XML to extract allergies section
                            try:
                                import xml.etree.ElementTree as ET
                                root = ET.fromstring(cda_content)
                                
                                # Find allergies section (code 48765-2) using manual filtering
                                # ElementTree XPath predicates are unreliable, so we find sections first then filter
                                all_sections = root.findall(".//{urn:hl7-org:v3}section")
                                allergies_sections = []
                                
                                for section in all_sections:
                                    code_elem = section.find('{urn:hl7-org:v3}code')
                                    if code_elem is not None and code_elem.get('code') == '48765-2':
                                        allergies_sections.append(section)
                                        print(f"🎯 [DEBUG] Found allergies section with code 48765-2")
                                
                                # Define namespaces for entry processing
                                namespaces = {
                                    'hl7': 'urn:hl7-org:v3',
                                    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
                                }
                                
                                for section in allergies_sections:
                                    # Extract entries from allergies section
                                    entries = section.findall("{urn:hl7-org:v3}entry")
                                    
                                    for entry in entries:
                                        # Extract observation data for each allergy
                                        obs_data = enhanced_processor._extract_observation_data(entry, namespaces)
                                        if obs_data:
                                            enhanced_allergies_data.append(obs_data)
                                
                                logger.info(f"[ENHANCED] Extracted {len(enhanced_allergies_data)} allergies from XML processing")
                                
                            except ET.ParseError:
                                logger.warning("[ENHANCED] CDA content is not valid XML, trying HTML processing")
                                # Fall back to HTML processing if XML parsing fails
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(cda_content, 'html.parser')
                                
                                # Look for allergies section in HTML
                                allergies_divs = soup.find_all('div', string=re.compile(r'48765-2|Allergies|allergies'))
                                for div in allergies_divs:
                                    # Extract table data if present
                                    table = div.find_next('table')
                                    if table:
                                        rows = table.find_all('tr')[1:]  # Skip header
                                        for row in rows:
                                            cells = row.find_all(['td', 'th'])
                                            if len(cells) >= 2:
                                                # Basic allergy extraction from HTML table
                                                allergy_data = {
                                                    'allergy_type': 'Drug Allergy',
                                                    'causative_agent': cells[0].get_text(strip=True) if cells[0] else 'Unknown',
                                                    'manifestation': cells[1].get_text(strip=True) if len(cells) > 1 else 'Unknown reaction',
                                                    'severity': 'moderate',
                                                    'status': 'active',
                                                    'recorded_date': '',
                                                    'onset_date': '',
                                                    'allergy_code': '',
                                                    'agent_code': '',
                                                    'manifestation_code': '',
                                                    'notes': ''
                                                }
                                                enhanced_allergies_data.append(allergy_data)
                        
                        if enhanced_allergies_data and len(enhanced_allergies_data) > 0:
                            logger.info(f"[ENHANCED] Successfully extracted {len(enhanced_allergies_data)} enhanced allergies")
                            
                            # Store enhanced allergies data in session for template access
                            request.session[f'enhanced_allergies_data_{session_id}'] = {
                                'structured_entries': enhanced_allergies_data,
                                'extraction_timestamp': str(timezone.now()),
                                'source_language': source_language,
                                'country_code': country_code
                            }
                            
                            logger.info(f"[ENHANCED] Stored enhanced allergies data in session key: enhanced_allergies_data_{session_id}")
                        else:
                            logger.info("[ENHANCED] No enhanced allergies data extracted")
                            
                    except Exception as e:
                        logger.error(f"[ERROR] Enhanced CDA Processor allergies extraction failed: {str(e)}")

                    # Extract processed sections for Clinical Information tab
                    processed_sections = []
                    raw_sections = processing_result.get("sections", [])

                    logger.info(
                        f"[DEBUG] Converting {len(raw_sections)} raw sections to processed_sections"
                    )

                    for section in raw_sections:
                        # Convert each section to the format expected by the Clinical Information template
                        if hasattr(section, "display_name"):
                            # ClinicalSection dataclass object
                            section_title = section.display_name
                            entries = getattr(section, "entries", [])
                        else:
                            # Dictionary format from enhanced processor
                            section_title = section.get(
                                "title", section.get("display_name", "Unknown Section")
                            )
                            entries = section.get("entries", [])

                        processed_section = {
                            "title": section_title,
                            "has_entries": len(entries) > 0,
                            "entries": [],
                            "medical_terminology_count": 0,
                        }

                        # Check if this is an allergies section and we have enhanced allergies data
                        # DEBUG: Log enhanced allergies processing
                        enhanced_allergies = match_data.get("enhanced_allergies", [])
                        print(
                            f"[DEBUG] Enhanced allergies in match_data: {len(enhanced_allergies)} items"
                        )
                        
                        # ALSO check session for enhanced allergies data (session-based storage)
                        if not enhanced_allergies:
                            # Check for session-specific enhanced allergies data first
                            enhanced_key = f'enhanced_allergies_data_{session_id}'
                            if enhanced_key in request.session:
                                session_allergies = request.session[enhanced_key]
                                structured_entries = session_allergies.get('structured_entries', [])
                                if structured_entries:
                                    # Convert structured_entries format to old format for compatibility
                                    enhanced_allergies = []
                                    for entry in structured_entries:
                                        # Convert new format to old format expected by view
                                        converted_entry = {
                                            'substance': entry.get('causative_agent', 'Unknown'),
                                            'code': entry.get('allergy_code', '').split(':')[-1] if ':' in entry.get('allergy_code', '') else entry.get('allergy_code', ''),
                                            'coding_system': entry.get('allergy_code', '').split(':')[0] if ':' in entry.get('allergy_code', '') else 'SNOMED-CT',
                                            'agent_code': entry.get('agent_code', '').split(':')[-1] if ':' in entry.get('agent_code', '') else entry.get('agent_code', ''),
                                            'manifestation': [entry.get('manifestation', 'Unknown reaction')],
                                            'manifestation_codes': [entry.get('manifestation_code', '').split(':')[-1] if ':' in entry.get('manifestation_code', '') else entry.get('manifestation_code', '')],
                                            'severity': entry.get('severity', 'unknown'),
                                            'status': entry.get('status', 'active'),
                                            'onset_date': entry.get('onset_date', ''),
                                            'end_date': entry.get('end_date', ''),
                                            'certainty': 'confirmed',  # Default from enhanced data
                                        }
                                        enhanced_allergies.append(converted_entry)
                                    print(f"[DEBUG] Converted {len(enhanced_allergies)} enhanced allergies from session key: {enhanced_key}")
                            
                            # Fallback: check general session keys for enhanced allergies data
                            if not enhanced_allergies:
                                for session_key, session_value in request.session.items():
                                    if 'enhanced_allergies_data' in session_key and isinstance(session_value, dict):
                                        structured_entries = session_value.get('structured_entries', [])
                                        if structured_entries:
                                            # Convert structured_entries format to old format for compatibility
                                            enhanced_allergies = []
                                            for entry in structured_entries:
                                                # Convert new format to old format expected by view
                                                converted_entry = {
                                                    'substance': entry.get('causative_agent', 'Unknown'),
                                                    'code': entry.get('allergy_code', '').split(':')[-1] if ':' in entry.get('allergy_code', '') else entry.get('allergy_code', ''),
                                                    'coding_system': entry.get('allergy_code', '').split(':')[0] if ':' in entry.get('allergy_code', '') else 'SNOMED-CT',
                                                    'agent_code': entry.get('agent_code', '').split(':')[-1] if ':' in entry.get('agent_code', '') else entry.get('agent_code', ''),
                                                    'manifestation': [entry.get('manifestation', 'Unknown reaction')],
                                                    'manifestation_codes': [entry.get('manifestation_code', '').split(':')[-1] if ':' in entry.get('manifestation_code', '') else entry.get('manifestation_code', '')],
                                                    'severity': entry.get('severity', 'unknown'),
                                                    'status': entry.get('status', 'active'),
                                                    'onset_date': entry.get('onset_date', ''),
                                                    'end_date': entry.get('end_date', ''),
                                                    'certainty': 'confirmed',  # Default from enhanced data
                                                }
                                                enhanced_allergies.append(converted_entry)
                                            print(f"[DEBUG] Converted {len(enhanced_allergies)} enhanced allergies from session key: {session_key}")
                                            break

                        is_allergies_section = any(
                            keyword in str(section_title).lower()
                            for keyword in ["allerg", "adverse", "reaction"]
                        )
                        print(
                            f"[DEBUG] Section '{section_title}' is_allergies_section: {is_allergies_section}"
                        )

                        if is_allergies_section and enhanced_allergies:
                            print(
                                f"[DEBUG] TRIGGERING enhanced allergies logic for {section_title}"
                            )
                        is_allergies_section = any(
                            keyword in str(section_title).lower()
                            for keyword in ["allerg", "adverse", "reaction"]
                        )

                        if is_allergies_section and enhanced_allergies:
                            logger.info(
                                f"[ENHANCED] Found {len(enhanced_allergies)} enhanced allergies for section: {section_title}"
                            )

                            # Create 8-column clinical table structure for allergies (removed generic code column)
                            processed_section["clinical_table"] = {
                                "headers": [
                                    {"key": "reaction_type", "label": "Reaction Type", "primary": True, "type": "reaction"},
                                    {"key": "manifestation", "label": "Clinical Manifestation", "type": "reaction"},
                                    {"key": "agent", "label": "Agent", "type": "allergen"},
                                    {"key": "time", "label": "Time", "type": "date"},
                                    {"key": "severity", "label": "Severity", "type": "severity"},
                                    {"key": "criticality", "label": "Criticality", "type": "severity"},
                                    {"key": "status", "label": "Status", "type": "status"},
                                    {"key": "certainty", "label": "Certainty", "type": "status"},
                                ],
                                "rows": []
                            }

                            # Convert enhanced allergies to clinical table rows
                            for allergy in enhanced_allergies:
                                row = {
                                    "data": {
                                        "reaction_type": {"value": "Propensity to adverse reaction", "display_value": "Propensity to adverse reaction"},
                                        "manifestation": {"value": ", ".join(allergy.get("manifestation", ["Unknown"])), "display_value": ", ".join(allergy.get("manifestation", ["Unknown"]))},
                                        "agent": {"value": allergy.get("substance", "Unknown"), "display_value": allergy.get("substance", "Unknown")},
                                        "time": {"value": allergy.get("onset_date", "Unknown"), "display_value": allergy.get("onset_date", "Unknown")},
                                        "severity": {"value": allergy.get("severity", "unknown"), "display_value": allergy.get("severity", "unknown").title()},
                                        "criticality": {"value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low", "display_value": "High" if allergy.get("severity", "").lower() == "severe" else "Medium" if allergy.get("severity", "").lower() == "moderate" else "Low"},
                                        "status": {"value": allergy.get("status", "active"), "display_value": allergy.get("status", "active").title()},
                                        "certainty": {"value": allergy.get("certainty", "confirmed"), "display_value": allergy.get("certainty", "confirmed").title()},
                                    },
                                    "has_medical_codes": bool(allergy.get("manifestation_code") or allergy.get("agent_code"))
                                }
                                processed_section["clinical_table"]["rows"].append(row)

                            # Also create legacy entries for backward compatibility
                            for allergy in enhanced_allergies:
                                enhanced_entry = {
                                    "display_name": allergy.get(
                                        "substance", "Unknown Allergen"
                                    ),
                                    "has_medical_terminology": True,
                                    "status": allergy.get("status", "active").title(),
                                    "severity": allergy.get(
                                        "severity", "unknown"
                                    ).title(),
                                    "reaction": ", ".join(
                                        allergy.get("manifestation", [])
                                    ),
                                    "onset_date": allergy.get("onset_date", "Unknown"),
                                    "last_occurrence": allergy.get(
                                        "last_occurrence", "Unknown"
                                    ),
                                    "coding_system": allergy.get("coding_system", ""),
                                    "code": allergy.get("code", ""),
                                    "ps_guidelines_compliant": allergy.get(
                                        "ps_guidelines_compliant", False
                                    ),
                                    "enhanced_data": True,  # Flag to identify enhanced entries
                                    # Add clinical codes for manifestation and agent
                                    "manifestation_code": allergy.get("manifestation_code", ""),
                                    "manifestation_display": allergy.get("manifestation_display", ""),
                                    "agent_code": allergy.get("agent_code", ""),
                                    "agent_display": allergy.get("agent_display", ""),
                                    # Add code systems if available
                                    "manifestation_code_system": allergy.get("manifestation_code_system", ""),
                                    "agent_code_system": allergy.get("agent_code_system", ""),
                                }
                                processed_section["entries"].append(enhanced_entry)
                                processed_section["medical_terminology_count"] += 1

                            # Set flags for template
                            processed_section["structured_entries"] = processed_section["entries"].copy()
                            processed_section["has_entries"] = True
                            processed_section["enhanced_data"] = True

                            logger.info(
                                f"[ENHANCED] Created 9-column allergies clinical table with {len(enhanced_allergies)} enhanced entries for {section_title}"
                            )
                        else:
                            # Convert original CDA entries
                            for entry in entries:
                                if hasattr(entry, "primary_code"):
                                    # ClinicalEntry dataclass
                                    display_name = (
                                        entry.primary_code.display
                                        if entry.primary_code
                                        else "Unknown Item"
                                    )
                                    has_terminology = bool(
                                        entry.primary_code and entry.primary_code.code
                                    )
                                else:
                                    # Dictionary format
                                    display_name = entry.get(
                                        "display_name",
                                        entry.get("name", "Unknown Item"),
                                    )
                                    has_terminology = bool(entry.get("code"))

                                processed_entry = {
                                    "display_name": display_name,
                                    "has_medical_terminology": has_terminology,
                                    "status": getattr(
                                        entry, "status", entry.get("status", "Active")
                                    ),
                                }

                                processed_section["entries"].append(processed_entry)

                                if has_terminology:
                                    processed_section["medical_terminology_count"] += 1

                        processed_sections.append(processed_section)

                    logger.info(
                        f"[DEBUG] Created {len(processed_sections)} processed sections for Clinical Information tab"
                    )

                else:
                    logger.error(f"[ERROR] CDADisplayService processing failed")
                    translation_result = {"sections": [], "success": False}
                    processed_sections = []  # Initialize empty for failed processing

            except Exception as e:
                logger.error(
                    f"Error processing CDA content with CDADisplayService: {e}"
                )
                translation_result = {"sections": [], "success": False}
                processed_sections = []  # Initialize empty for exception case
        else:
            print(f"❌ [DEBUG] CDA CONTENT CONDITION FAILED!")
            print(f"❌ [DEBUG] cda_content exists: {bool(cda_content)}")
            print(f"❌ [DEBUG] cda_content length: {len(cda_content) if cda_content else 0}")
            print(f"❌ [DEBUG] cda_content stripped: {bool(cda_content.strip()) if cda_content else False}")
            print(f"❌ [DEBUG] Contains 'No CDA content': {'<!-- No CDA content available -->' in cda_content if cda_content else False}")
            
            logger.warning("No valid CDA content available for processing")
            translation_result = {"sections": [], "success": False}
            processed_sections = []  # Initialize empty for no CDA content case

        # Initialize variables that might not be set if processing fails
        if "enhanced_processing_result" not in locals():
            enhanced_processing_result = {"success": False, "sections": []}
        if "extended_header_data" not in locals():
            extended_header_data = {}

        # Check for embedded PDFs in L1 CDA documents
        embedded_pdfs = []
        has_embedded_pdfs = False
        if cda_content and actual_cda_type == "L1":
            try:
                pdf_service = ClinicalDocumentPDFService()
                embedded_pdfs = pdf_service.extract_all_pdfs_from_xml(cda_content)
                has_embedded_pdfs = len(embedded_pdfs) > 0
                if has_embedded_pdfs:
                    logger.info(
                        f"[INFO] Found {len(embedded_pdfs)} embedded PDFs in L1 CDA document"
                    )
                    for i, pdf_info in enumerate(embedded_pdfs):
                        logger.info(
                            f"  PDF {i+1}: {pdf_info.get('filename', 'Unnamed')} ({pdf_info.get('size', 0)} bytes)"
                        )
                else:
                    logger.info("[INFO] No embedded PDFs found in L1 CDA document")
            except Exception as pdf_error:
                logger.warning(f"Failed to check for embedded PDFs: {pdf_error}")

        # Build complete context for Enhanced CDA Display
        context = {
            "session_id": session_id,  # Session ID for URL routing
            "patient_identity": {
                "patient_id": patient_government_id,  # Display the government ID
                "session_id": session_id,  # Keep session ID for URL routing
                "given_name": (
                    patient_data.given_name
                    if patient_data
                    else patient_info.get("given_name", "Unknown")
                ),
                "family_name": (
                    patient_data.family_name
                    if patient_data
                    else patient_info.get("family_name", "Patient")
                ),
                "birth_date": (
                    patient_data.birth_date
                    if patient_data
                    else patient_info.get("birth_date", "Unknown")
                ),
                "gender": (
                    patient_data.gender
                    if patient_data
                    else patient_info.get("gender", "Unknown")
                ),
                "patient_identifiers": [],
                "primary_patient_id": patient_government_id,
                "secondary_patient_id": None,
            },
            "source_country": match_data.get("country_code", "Unknown"),
            "source_language": source_language,
            "cda_type": actual_cda_type,
        }

        # DEBUG: Check session state before building has_l3_cda logic
        session_has_match = f"patient_match_{session_id}" in request.session
        session_has_extended = f"patient_extended_data_{session_id}" in request.session
        search_result_has_l3 = search_result.has_l3_cda() if search_result else None

        logger.info(f"[DEBUG] L3 Button Logic Debug for session {session_id}:")
        logger.info(f"[DEBUG] - Session has patient_match: {session_has_match}")
        logger.info(f"[DEBUG] - Session has extended data: {session_has_extended}")
        logger.info(f"[DEBUG] - Search result exists: {search_result is not None}")
        logger.info(f"[DEBUG] - Search result has_l3_cda: {search_result_has_l3}")

        # Prioritize session extended data over search result for L1/L3 flags
        context.update(
            {
                "has_l1_cda": (
                    request.session.get(f"patient_match_{session_id}", {}).get("has_l1")
                    if f"patient_match_{session_id}" in request.session
                    else (
                        request.session.get(
                            f"patient_extended_data_{session_id}", {}
                        ).get("has_l1_cda")
                        if f"patient_extended_data_{session_id}" in request.session
                        else (
                            search_result.has_l1_cda()
                            if search_result
                            else _check_actual_cda_availability(session_id, "L1")
                        )
                    )
                ),
                "has_l3_cda": (
                    request.session.get(f"patient_match_{session_id}", {}).get("has_l3")
                    if f"patient_match_{session_id}" in request.session
                    else (
                        request.session.get(
                            f"patient_extended_data_{session_id}", {}
                        ).get("has_l3_cda")
                        if f"patient_extended_data_{session_id}" in request.session
                        else (
                            search_result.has_l3_cda()
                            if search_result
                            else _check_actual_cda_availability(session_id, "L3")
                        )
                    )
                ),
            }
        )

        logger.info(f"[DEBUG] Final context has_l3_cda: {context.get('has_l3_cda')}")
        logger.info(
            f"[DEBUG] L3 Button should be: {'ENABLED' if context.get('has_l3_cda') else 'DISABLED'}"
        )
        logger.info(
            f"[DEBUG] Processed sections count: {len(processed_sections) if 'processed_sections' in locals() else 'NOT_DEFINED'}"
        )
        logger.info(
            f"[DEBUG] Clinical Info tab should be: {'ENABLED' if len(processed_sections) > 0 else 'DISABLED'}"
        )

        context.update(
            {
                "confidence": int(match_data.get("confidence_score", 0.95) * 100),
                "file_name": match_data.get("file_path", "unknown.xml"),
                "translation_quality": translation_quality,
                "sections_count": sections_count,
                "processed_sections": processed_sections,  # Add processed sections for Clinical Information tab
                "enhanced_allergies": match_data.get(
                    "enhanced_allergies", []
                ),  # Add enhanced allergies directly
                "medical_terms_count": medical_terms_count,
                "coded_sections_count": coded_sections_count,
                "coded_sections_percentage": coded_sections_percentage,
                "uses_coded_sections": uses_coded_sections,
                "translation_result": translation_result,
                "safety_alerts": [],
                "allergy_alerts": [],
                "has_safety_alerts": False,
                # Add patient_summary for FHIR badge template compatibility
                "patient_summary": {
                    "data_source": match_data.get("patient_data", {}).get("source", "CDA"),
                    "file_path": match_data.get("file_path"),
                    "confidence_score": match_data.get("confidence_score", 0.95),
                },
                # Add session_id and cda_file_name for FHIR badge template compatibility
                "session_id": session_id,
                "cda_file_name": match_data.get("file_path", "unknown.xml"),
                "administrative_data": {
                    "document_creation_date": None,
                    "document_last_update_date": None,
                    "document_version_number": None,
                    "patient_contact_info": {"addresses": [], "telecoms": []},
                    "author_hcp": {"family_name": None, "organization": {"name": None}},
                    "legal_authenticator": {
                        "family_name": None,
                        "organization": {"name": None},
                    },
                    "custodian_organization": {"name": None},
                    "preferred_hcp": {"name": None},
                    "guardian": {"family_name": None},
                    "other_contacts": [],
                },
                "has_administrative_data": False,
                # PDF content information for L1 CDAs
                "embedded_pdfs": embedded_pdfs,
                "has_embedded_pdfs": has_embedded_pdfs,
                "is_pdf_only_cda": has_embedded_pdfs
                and len(enhanced_processing_result.get("sections", [])) == 0,
            }
        )

        # CLINICAL ARRAYS EXTRACTION: Add clinical arrays for Clinical Information tab (Session-based patient path)
        # Only execute this fallback if medications weren't already extracted by comprehensive processing
        try:
            # Get the raw CDA content from the search result based on the requested type
            raw_cda_content = None
            if actual_cda_type == "L3":
                raw_cda_content = search_result.l3_cda_content
            elif actual_cda_type == "L1":
                raw_cda_content = search_result.l1_cda_content
            else:
                # Fallback to any available content
                raw_cda_content = search_result.l3_cda_content or search_result.l1_cda_content or search_result.cda_content
            
            if raw_cda_content and raw_cda_content.strip() and not context.get("medications"):
                logger.info(
                    f"[CLINICAL ARRAYS SESSION] Extracting clinical arrays for session {session_id} using ComprehensiveClinicalDataService (fallback path)"
                )
                from .services.comprehensive_clinical_data_service import (
                    ComprehensiveClinicalDataService,
                )

                # Use the comprehensive service directly with raw CDA content
                comprehensive_service = ComprehensiveClinicalDataService()
                comprehensive_data = comprehensive_service.extract_comprehensive_clinical_data(
                    raw_cda_content, country_code
                )
                
                if comprehensive_data and isinstance(comprehensive_data, dict):
                    clinical_arrays = comprehensive_service.get_clinical_arrays_for_display(
                        comprehensive_data
                    )

                    # ENHANCED: Integrate Enhanced CDA Helper for 9-column allergies format
                    try:
                        from .cda_display_data_helper import CDADisplayDataHelper
                        
                        logger.info("[ENHANCED ALLERGIES CDA_VIEW] Starting Enhanced CDA Helper integration")
                        display_helper = CDADisplayDataHelper()
                        clinical_sections = display_helper.extract_clinical_sections(raw_cda_content)
                        logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Extracted {len(clinical_sections)} clinical sections")
                        
                        # Find allergies section with clinical_table structure
                        allergies_with_clinical_table = []
                        for section in clinical_sections:
                            section_name = section.get("display_name", "").lower()
                            logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Processing section: {section.get('display_name', 'Unknown')}")
                            if any(keyword in section_name for keyword in ["allerg", "adverse", "reaction", "intolerance"]):
                                logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Found allergies section: {section.get('display_name')}")
                                if section.get("clinical_table"):
                                    logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Found enhanced allergies section: {section.get('display_name')}")
                                    # Convert clinical_table structure to allergy objects with clinical_table
                                    enhanced_allergy = {
                                        "clinical_table": section["clinical_table"],
                                        "allergen": {"name": "Enhanced Allergies", "code": {"code": "Enhanced"}},
                                        "section_name": section.get("display_name", ""),
                                        "is_enhanced": True
                                    }
                                    allergies_with_clinical_table.append(enhanced_allergy)
                                    logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Clinical table has {len(section['clinical_table'].get('headers', []))} headers and {len(section['clinical_table'].get('rows', []))} rows")
                                else:
                                    logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Section {section.get('display_name')} has no clinical_table")
                        
                        # Replace allergies with enhanced version if available
                        if allergies_with_clinical_table:
                            logger.info(f"[ENHANCED ALLERGIES CDA_VIEW] Replacing {len(clinical_arrays['allergies'])} standard allergies with {len(allergies_with_clinical_table)} enhanced allergies")
                            clinical_arrays["allergies"] = allergies_with_clinical_table
                        else:
                            logger.info("[ENHANCED ALLERGIES CDA_VIEW] No enhanced allergies found, keeping standard format")

                        # ENHANCED: Process procedures using the same clinical_sections data
                        logger.info("[ENHANCED PROCEDURES CDA_VIEW] Starting Enhanced CDA Helper integration for procedures")
                        
                        # Find procedures section with clinical_table structure from existing clinical_sections
                        procedures_with_clinical_table = []
                        for section in clinical_sections:
                            section_name = section.get("display_name", "").lower()
                            logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Processing section: {section.get('display_name', 'Unknown')}")
                            if any(keyword in section_name for keyword in ["procedure", "surgery", "surgical", "intervention"]):
                                logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Found procedures section: {section.get('display_name')}")
                                if section.get("clinical_table"):
                                    logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Found enhanced procedures section: {section.get('display_name')}")
                                    # Convert clinical_table structure to procedure objects with clinical_table
                                    enhanced_procedure = {
                                        "clinical_table": section["clinical_table"],
                                        "procedure": {"name": "Enhanced Procedures", "code": {"code": "Enhanced"}},
                                        "section_name": section.get("display_name", ""),
                                        "is_enhanced": True
                                    }
                                    procedures_with_clinical_table.append(enhanced_procedure)
                                    logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Clinical table has {len(section['clinical_table'].get('headers', []))} headers and {len(section['clinical_table'].get('rows', []))} rows")
                                else:
                                    logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Section {section.get('display_name')} has no clinical_table")
                        
                        # Replace procedures with enhanced version if available
                        if procedures_with_clinical_table:
                            logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Replacing {len(clinical_arrays['procedures'])} standard procedures with {len(procedures_with_clinical_table)} enhanced procedures")
                            clinical_arrays["procedures"] = procedures_with_clinical_table
                            # Also store enhanced procedures for template access
                            context["enhanced_procedures"] = procedures_with_clinical_table
                            logger.info(f"[ENHANCED PROCEDURES CDA_VIEW] Added {len(procedures_with_clinical_table)} enhanced procedures to context")
                        else:
                            logger.info("[ENHANCED PROCEDURES CDA_VIEW] No enhanced procedures found, keeping standard format")
                            context["enhanced_procedures"] = []

                        # ENHANCED: Process medical devices sections with clinical_table structure
                        medical_devices_with_clinical_table = []
                        for section in clinical_sections:
                            section_name = section.get("section_name", "").lower()
                            display_name = section.get("display_name", "").lower()
                            
                            # Check if this is a medical devices section
                            is_medical_devices_section = (
                                section_name in ["medical_devices", "medical_device"] or
                                "medical device" in display_name or
                                "device" in display_name or
                                section.get("section_code") == "46264-8"
                            )
                            
                            if is_medical_devices_section and section.get("clinical_table"):
                                logger.info(f"[ENHANCED MEDICAL DEVICES CDA_VIEW] Found medical devices section: {section.get('display_name')}")
                                if section["clinical_table"].get("headers") and section["clinical_table"].get("rows"):
                                    # Convert clinical_table structure to device objects with clinical_table
                                    enhanced_device = {
                                        "clinical_table": section["clinical_table"],
                                        "device": {"name": "Enhanced Medical Devices", "code": {"code": "Enhanced"}},
                                        "section_name": section.get("display_name", ""),
                                        "is_enhanced": True
                                    }
                                    medical_devices_with_clinical_table.append(enhanced_device)
                                    logger.info(f"[ENHANCED MEDICAL DEVICES CDA_VIEW] Clinical table has {len(section['clinical_table'].get('headers', []))} headers and {len(section['clinical_table'].get('rows', []))} rows")
                                else:
                                    logger.info(f"[ENHANCED MEDICAL DEVICES CDA_VIEW] Section {section.get('display_name')} has no clinical_table")
                        
                        # Ensure medical_devices key exists in clinical_arrays
                        if "medical_devices" not in clinical_arrays:
                            clinical_arrays["medical_devices"] = []
                        
                        # Replace medical devices with enhanced version if available
                        if medical_devices_with_clinical_table:
                            logger.info(f"[ENHANCED MEDICAL DEVICES CDA_VIEW] Replacing {len(clinical_arrays['medical_devices'])} standard devices with {len(medical_devices_with_clinical_table)} enhanced devices")
                            clinical_arrays["medical_devices"] = medical_devices_with_clinical_table
                            # Also store enhanced medical devices for template access
                            context["enhanced_medical_devices"] = medical_devices_with_clinical_table
                            logger.info(f"[ENHANCED MEDICAL DEVICES CDA_VIEW] Added {len(medical_devices_with_clinical_table)} enhanced medical devices to context")
                        else:
                            logger.info("[ENHANCED MEDICAL DEVICES CDA_VIEW] No enhanced medical devices found, keeping standard format")
                            context["enhanced_medical_devices"] = []
                            
                    except Exception as e:
                        logger.warning(f"[ENHANCED CDA_VIEW] Enhanced CDA Helper integration failed: {e}")
                        import traceback
                        logger.warning(f"[ENHANCED CDA_VIEW] Full traceback: {traceback.format_exc()}")
                        # Keep standard data on error

                if clinical_arrays:
                    # Ensure mandatory sections are present even if empty
                    clinical_arrays = ensure_mandatory_sections(clinical_arrays)
                    
                    # Add clinical arrays to context for Clinical Information tab
                    context.update(
                        {
                            "medications": clinical_arrays["medications"],
                            "allergies": clinical_arrays["allergies"],
                            "problems": clinical_arrays["problems"],
                            "procedures": clinical_arrays["procedures"],
                            "vital_signs": clinical_arrays["vital_signs"],
                            "results": clinical_arrays["results"],
                            "immunizations": clinical_arrays["immunizations"],
                            "medical_devices": clinical_arrays["medical_devices"],
                        }
                    )
                    total_clinical_items = sum(
                        len(arr) for arr in clinical_arrays.values()
                    )
                    logger.info(
                        f"[CLINICAL ARRAYS SESSION] Added {total_clinical_items} clinical array items to context: med={len(clinical_arrays['medications'])}, all={len(clinical_arrays['allergies'])}, prob={len(clinical_arrays['problems'])}, proc={len(clinical_arrays['procedures'])}, vs={len(clinical_arrays['vital_signs'])}"
                    )
                    
                    # EXTENDED CLINICAL SECTIONS DETECTION (when clinical arrays exist)
                    try:
                        if 'comprehensive_data' in locals() and comprehensive_data:
                            extended_sections = detect_extended_clinical_sections(comprehensive_data)
                        else:
                            # Initialize empty extended sections if no comprehensive_data
                            extended_sections = {
                                "history_of_past_illness": [],
                                "immunizations": [],
                                "pregnancy_history": [],
                                "social_history": [],
                                "physical_findings": [],
                                "coded_results": {"blood_group": [], "diagnostic_results": []},
                                "laboratory_results": [],
                                "advance_directives": [],
                                "additional_sections": []
                            }
                            
                        # HISTORY OF PAST ILLNESS SPECIALIZED EXTRACTION
                        # This runs regardless of comprehensive_data status if we have raw CDA content
                        try:
                            if raw_cda_content:
                                logger.info("[HISTORY OF PAST ILLNESS] Starting specialized extraction from raw CDA content")
                                history_extractor = HistoryOfPastIllnessExtractor()
                                history_entries = history_extractor.extract_history_of_past_illness(raw_cda_content)
                                
                                if history_entries:
                                    # Override the history_of_past_illness with structured data
                                    extended_sections["history_of_past_illness"] = history_entries
                                    logger.info(f"[HISTORY OF PAST ILLNESS] Successfully extracted {len(history_entries)} structured entries")
                                else:
                                    logger.info("[HISTORY OF PAST ILLNESS] No history entries found in CDA document")
                            else:
                                logger.warning("[HISTORY OF PAST ILLNESS] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[HISTORY OF PAST ILLNESS] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # IMMUNIZATIONS SPECIALIZED EXTRACTION
                        # This runs regardless of comprehensive_data status if we have raw CDA content
                        try:
                            if raw_cda_content:
                                logger.info("[IMMUNIZATIONS] Starting specialized extraction from raw CDA content")
                                immunizations_extractor = ImmunizationsExtractor()
                                immunization_entries = immunizations_extractor.extract_immunizations(raw_cda_content)
                                
                                if immunization_entries:
                                    # Override the immunizations with structured data
                                    extended_sections["immunizations"] = immunization_entries
                                    logger.info(f"[IMMUNIZATIONS] Successfully extracted {len(immunization_entries)} structured entries")
                                else:
                                    logger.info("[IMMUNIZATIONS] No immunization entries found in CDA document")
                            else:
                                logger.warning("[IMMUNIZATIONS] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[IMMUNIZATIONS] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # PREGNANCY HISTORY SPECIALIZED EXTRACTION (PATH 1)
                        # This runs regardless of comprehensive_data status if we have raw CDA content
                        try:
                            if raw_cda_content:
                                logger.info("[PREGNANCY HISTORY PATH1] Starting specialized extraction from raw CDA content")
                                pregnancy_extractor = PregnancyHistoryExtractor()
                                pregnancy_data = pregnancy_extractor.extract_pregnancy_history(raw_cda_content)
                                
                                logger.info(f"[PREGNANCY HISTORY PATH1] Extraction result: {pregnancy_data}")
                                if pregnancy_data:
                                    logger.info(f"[PREGNANCY HISTORY PATH1] Current pregnancy: {pregnancy_data.current_pregnancy}")
                                    logger.info(f"[PREGNANCY HISTORY PATH1] Previous pregnancies: {len(pregnancy_data.previous_pregnancies) if pregnancy_data.previous_pregnancies else 0}")
                                    logger.info(f"[PREGNANCY HISTORY PATH1] Pregnancy overview: {len(pregnancy_data.pregnancy_overview) if pregnancy_data.pregnancy_overview else 0}")
                                
                                if pregnancy_data and (pregnancy_data.current_pregnancy or pregnancy_data.previous_pregnancies or pregnancy_data.pregnancy_overview):
                                    # Add structured pregnancy data to extended sections
                                    extended_sections["pregnancy_history"] = pregnancy_data
                                    logger.info(f"[PREGNANCY HISTORY PATH1] Successfully extracted comprehensive pregnancy data - ADDED TO CONTEXT")
                                else:
                                    logger.info("[PREGNANCY HISTORY PATH1] No pregnancy history found in CDA document")
                            else:
                                logger.warning("[PREGNANCY HISTORY PATH1] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[PREGNANCY HISTORY PATH1] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # SOCIAL HISTORY SPECIALIZED EXTRACTION (PATH 1)
                        # This runs regardless of comprehensive_data status if we have raw CDA content
                        try:
                            if raw_cda_content:
                                logger.info("[SOCIAL HISTORY PATH1] Starting specialized extraction from raw CDA content")
                                social_history_extractor = SocialHistoryExtractor()
                                social_history_entries = social_history_extractor.extract_social_history(raw_cda_content)
                                
                                if social_history_entries:
                                    extended_sections["social_history"] = social_history_entries
                                    logger.info(f"[SOCIAL HISTORY PATH1] Successfully extracted {len(social_history_entries)} entries - ADDED TO CONTEXT")
                                else:
                                    logger.info("[SOCIAL HISTORY PATH1] No social history entries found in CDA document")
                            else:
                                logger.warning("[SOCIAL HISTORY PATH1] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[SOCIAL HISTORY PATH1] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # PHYSICAL FINDINGS SPECIALIZED EXTRACTION (PATH 1)
                        # This runs regardless of comprehensive_data status if we have raw CDA content
                        try:
                            if raw_cda_content:
                                logger.info("[PHYSICAL FINDINGS PATH1] Starting specialized extraction from raw CDA content")
                                physical_findings_extractor = PhysicalFindingsExtractor()
                                physical_findings_entries = physical_findings_extractor.extract_physical_findings(raw_cda_content)
                                
                                if physical_findings_entries:
                                    extended_sections["physical_findings"] = physical_findings_entries
                                    logger.info(f"[PHYSICAL FINDINGS PATH1] Successfully extracted {len(physical_findings_entries)} entries - ADDED TO CONTEXT")
                                else:
                                    logger.info("[PHYSICAL FINDINGS PATH1] No physical findings entries found in CDA document")
                            else:
                                logger.warning("[PHYSICAL FINDINGS PATH1] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[PHYSICAL FINDINGS PATH1] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # CODED RESULTS SPECIALIZED EXTRACTION (PATH 1)
                        # This extracts both blood group and diagnostic results
                        try:
                            if raw_cda_content:
                                logger.info("[CODED RESULTS PATH1] Starting specialized extraction from raw CDA content")
                                coded_results_extractor = CodedResultsExtractor()
                                coded_results_data = coded_results_extractor.extract_coded_results(raw_cda_content)
                                
                                if coded_results_data and (coded_results_data.get('blood_group') or coded_results_data.get('diagnostic_results')):
                                    extended_sections["coded_results"] = coded_results_data
                                    blood_group_count = len(coded_results_data.get('blood_group', []))
                                    diagnostic_count = len(coded_results_data.get('diagnostic_results', []))
                                    logger.info(f"[CODED RESULTS PATH1] Successfully extracted {blood_group_count} blood group + {diagnostic_count} diagnostic results - ADDED TO CONTEXT")
                                else:
                                    logger.info("[CODED RESULTS PATH1] No coded results found in CDA document")
                            else:
                                logger.warning("[CODED RESULTS PATH1] No raw CDA content available for extraction")
                                        
                        except Exception as e:
                            logger.warning(f"[CODED RESULTS PATH1] Extraction failed: {e}")
                            # Keep existing detection if specialized extraction fails
                        
                        # UPDATE CONTEXT WITH EXTENDED SECTIONS (including History of Past Illness)
                        context.update(extended_sections)
                        
                        total_extended = sum(len(sections) for sections in extended_sections.values())
                        logger.info(f"[EXTENDED SECTIONS] Added {total_extended} extended clinical sections to context")
                    except Exception as e:
                        logger.warning(f"[EXTENDED SECTIONS] Failed to detect extended sections: {e}")
                        
                else:
                    # Create empty clinical arrays and ensure mandatory sections
                    clinical_arrays = {
                        "medications": [],
                        "allergies": [],
                        "problems": [],
                        "procedures": [],
                        "vital_signs": [],
                        "results": [],
                        "immunizations": [],
                        "medical_devices": [],
                    }
                    clinical_arrays = ensure_mandatory_sections(clinical_arrays)
                    
                    # Update context with mandatory sections
                    context.update(
                        {
                            "medications": clinical_arrays["medications"],
                            "allergies": clinical_arrays["allergies"],
                            "problems": clinical_arrays["problems"],
                            "procedures": clinical_arrays["procedures"],
                            "vital_signs": clinical_arrays["vital_signs"],
                            "results": clinical_arrays["results"],
                            "immunizations": clinical_arrays["immunizations"],
                            "medical_devices": clinical_arrays["medical_devices"],
                        }
                    )
                    logger.info(
                        f"[CLINICAL ARRAYS SESSION] No clinical arrays extracted for session {session_id}"
                    )
            elif context.get("medications"):
                logger.info(
                    f"[CLINICAL ARRAYS SESSION] Skipping fallback extraction for session {session_id} - medications already extracted by comprehensive processing with {len(context.get('medications', []))} items"
                )

            # EXTENDED CLINICAL SECTIONS DETECTION
            # Detect and add extended clinical sections to context after mandatory sections are processed
            try:
                # Initialize extended_sections for both paths with all required keys
                extended_sections = {
                    "coded_results": {"blood_group": [], "diagnostic_results": []}
                }
                
                # PATH 1: Get comprehensive data from earlier processing (available in locals)
                has_comprehensive_data = 'comprehensive_data' in locals() and comprehensive_data
                # PATH 2: Check if we can do specialized extractions (when medications already exist)
                can_do_specialized_extractions = context.get("medications")
                
                if has_comprehensive_data:
                    # PATH 1: Use comprehensive data detection 
                    logger.info("[EXTENDED SECTIONS] Using comprehensive data detection (PATH 1)")
                    extended_sections = detect_extended_clinical_sections(comprehensive_data)
                    
                    # PRESERVE SPECIALIZED EXTRACTIONS: Don't override if already populated by specialized extractors
                    existing_history = context.get("history_of_past_illness", [])
                    if existing_history:
                        logger.info(f"[EXTENDED SECTIONS] Preserving existing History of Past Illness data ({len(existing_history)} entries)")
                        extended_sections["history_of_past_illness"] = existing_history
                    
                    # PATH 1 completed - context will be set after all paths
                
                elif can_do_specialized_extractions:
                    # PATH 2: Do specialized extractions when medications already exist
                    logger.info("[EXTENDED SECTIONS] Running specialized extractions (PATH 2)")
                    
                    # PRESERVE SPECIALIZED EXTRACTIONS: Don't override if already populated by specialized extractors
                    existing_history = context.get("history_of_past_illness", [])
                    if existing_history:
                        logger.info(f"[EXTENDED SECTIONS] Preserving existing History of Past Illness data ({len(existing_history)} entries)")
                        extended_sections["history_of_past_illness"] = existing_history
                    
                    # IMMUNIZATIONS SPECIALIZED EXTRACTION (Path 2 - when medications already exist)
                    # This runs when the clinical arrays block was skipped due to existing medications
                    try:
                        # Get the raw CDA content for immunizations extraction
                        raw_cda_content = None
                        if actual_cda_type == "L3":
                            raw_cda_content = search_result.l3_cda_content
                        elif actual_cda_type == "L1":
                            raw_cda_content = search_result.l1_cda_content
                        else:
                            raw_cda_content = search_result.l3_cda_content or search_result.l1_cda_content or search_result.cda_content
                            
                        if raw_cda_content:
                            logger.info("[IMMUNIZATIONS PATH2] Starting specialized extraction from raw CDA content")
                            from .services.immunizations_extractor import ImmunizationsExtractor
                            immunizations_extractor = ImmunizationsExtractor()
                            immunization_entries = immunizations_extractor.extract_immunizations(raw_cda_content)
                            
                            if immunization_entries:
                                # Override the immunizations with structured data
                                extended_sections["immunizations"] = immunization_entries
                                logger.info(f"[IMMUNIZATIONS PATH2] Successfully extracted {len(immunization_entries)} structured entries")
                            else:
                                logger.info("[IMMUNIZATIONS PATH2] No immunization entries found in CDA document")
                        else:
                            logger.warning("[IMMUNIZATIONS PATH2] No raw CDA content available for extraction")
                    except Exception as e:
                        logger.warning(f"[IMMUNIZATIONS PATH2] Extraction failed: {e}")
                        # Keep existing detection if specialized extraction fails
                    
                    # PREGNANCY HISTORY SPECIALIZED EXTRACTION (Path 2 - when medications already exist)
                    # This runs when the clinical arrays block was skipped due to existing medications
                    try:
                        if raw_cda_content:
                            logger.info("[PREGNANCY HISTORY PATH2] Starting specialized extraction from raw CDA content")
                            pregnancy_extractor = PregnancyHistoryExtractor()
                            pregnancy_data = pregnancy_extractor.extract_pregnancy_history(raw_cda_content)
                            
                            if pregnancy_data and (pregnancy_data.current_pregnancy or pregnancy_data.previous_pregnancies or pregnancy_data.pregnancy_overview):
                                # Add structured pregnancy data to extended sections
                                extended_sections["pregnancy_history"] = pregnancy_data
                                logger.info(f"[PREGNANCY HISTORY PATH2] Successfully extracted comprehensive pregnancy data")
                            else:
                                logger.info("[PREGNANCY HISTORY PATH2] No pregnancy history found in CDA document")
                        else:
                            logger.warning("[PREGNANCY HISTORY PATH2] No raw CDA content available for extraction")
                    except Exception as e:
                        logger.warning(f"[PREGNANCY HISTORY PATH2] Extraction failed: {e}")
                        # Keep existing detection if specialized extraction fails
                    
                    # SOCIAL HISTORY SPECIALIZED EXTRACTION (PATH 2)
                    try:
                        if raw_cda_content:
                            logger.info("[SOCIAL HISTORY PATH2] Starting specialized extraction from raw CDA content")
                            social_history_extractor = SocialHistoryExtractor()
                            social_history_entries = social_history_extractor.extract_social_history(raw_cda_content)
                            
                            if social_history_entries:
                                extended_sections["social_history"] = social_history_entries
                                logger.info(f"[SOCIAL HISTORY PATH2] Successfully extracted {len(social_history_entries)} entries")
                            else:
                                logger.info("[SOCIAL HISTORY PATH2] No social history entries found in CDA document")
                        else:
                            logger.warning("[SOCIAL HISTORY PATH2] No raw CDA content available for extraction")
                    except Exception as e:
                        logger.warning(f"[SOCIAL HISTORY PATH2] Extraction failed: {e}")
                    
                    # PHYSICAL FINDINGS SPECIALIZED EXTRACTION (PATH 2)
                    try:
                        if raw_cda_content:
                            logger.info("[PHYSICAL FINDINGS PATH2] Starting specialized extraction from raw CDA content")
                            physical_findings_extractor = PhysicalFindingsExtractor()
                            physical_findings_entries = physical_findings_extractor.extract_physical_findings(raw_cda_content)
                            
                            if physical_findings_entries:
                                extended_sections["physical_findings"] = physical_findings_entries
                                logger.info(f"[PHYSICAL FINDINGS PATH2] Successfully extracted {len(physical_findings_entries)} entries")
                            else:
                                logger.info("[PHYSICAL FINDINGS PATH2] No physical findings entries found in CDA document")
                        else:
                            logger.warning("[PHYSICAL FINDINGS PATH2] No raw CDA content available for extraction")
                    except Exception as e:
                        logger.warning(f"[PHYSICAL FINDINGS PATH2] Extraction failed: {e}")
                        # Keep existing detection if specialized extraction fails
                    
                    # CODED RESULTS SPECIALIZED EXTRACTION (PATH 2)
                    try:
                        if raw_cda_content:
                            logger.info("[CODED RESULTS PATH2] Starting specialized extraction from raw CDA content")
                            coded_results_extractor = CodedResultsExtractor()
                            coded_results_data = coded_results_extractor.extract_coded_results(raw_cda_content)
                            
                            if coded_results_data and (coded_results_data.get('blood_group') or coded_results_data.get('diagnostic_results')):
                                extended_sections["coded_results"] = coded_results_data
                                blood_group_count = len(coded_results_data.get('blood_group', []))
                                diagnostic_count = len(coded_results_data.get('diagnostic_results', []))
                                logger.info(f"[CODED RESULTS PATH2] Successfully extracted {blood_group_count} blood group + {diagnostic_count} diagnostic results")
                            else:
                                logger.info("[CODED RESULTS PATH2] No coded results found in CDA document")
                        else:
                            logger.warning("[CODED RESULTS PATH2] No raw CDA content available for extraction")
                    except Exception as e:
                        logger.warning(f"[CODED RESULTS PATH2] Extraction failed: {e}")
                        # Keep existing detection if specialized extraction fails
                
                    context["extended_sections"] = extended_sections
                    
                    # Extract individual sections for template compatibility
                    context["history_of_past_illness"] = extended_sections.get("history_of_past_illness", [])
                    context["immunizations"] = extended_sections.get("immunizations", [])
                    context["pregnancy_history"] = extended_sections.get("pregnancy_history")
                    context["social_history"] = extended_sections.get("social_history", [])
                    context["physical_findings"] = extended_sections.get("physical_findings", [])
                    context["coded_results"] = extended_sections.get("coded_results", {"blood_group": [], "diagnostic_results": []})
                    context["laboratory_results"] = extended_sections.get("laboratory_results", [])
                    context["advance_directives"] = extended_sections.get("advance_directives", [])
                    context["additional_sections"] = extended_sections.get("additional_sections", [])
                    
                    # Calculate total properly, handling both lists and single objects
                    total_extended = 0
                    for section_name, sections in extended_sections.items():
                        if isinstance(sections, list):
                            total_extended += len(sections)
                        elif sections:  # Single object like PregnancyHistoryData
                            total_extended += 1
                    logger.info(f"[EXTENDED SECTIONS] Added {total_extended} extended clinical sections to context")
                    
                    # Log details of extended sections found
                    for section_name, sections in extended_sections.items():
                        if sections:
                            logger.info(f"[EXTENDED SECTIONS] {section_name}: {len(sections)} sections")
                
                else:
                    # Add empty extended sections for template compatibility
                    # PRESERVE SPECIALIZED EXTRACTIONS: Don't override if already populated
                    # Check both context and extended_sections for existing data
                    existing_social_history = []
                    if extended_sections.get("social_history"):
                        existing_social_history = extended_sections["social_history"]
                        logger.info(f"[EXTENDED SECTIONS] Preserving {len(existing_social_history)} social history entries from specialized extraction")
                    elif context.get("social_history"):
                        existing_social_history = context.get("social_history", [])
                    
                    empty_sections = {
                        "history_of_past_illness": context.get("history_of_past_illness", []),  # Preserve existing
                        "immunizations": context.get("immunizations", []),  # Don't override if already exists
                        "pregnancy_history": context.get("pregnancy_history", []),  # Preserve existing
                        "social_history": existing_social_history,  # Preserve from extended_sections or context
                        "physical_findings": context.get("physical_findings", []),  # Preserve existing
                        "coded_results": context.get("coded_results", {"blood_group": [], "diagnostic_results": []}),  # Preserve existing
                        "laboratory_results": [],
                        "advance_directives": [],
                        "additional_sections": []
                    }
                    context.update(empty_sections)
                    
                    # Log what we preserved
                    preserved_history = len(context.get("history_of_past_illness", []))
                    if preserved_history > 0:
                        logger.info(f"[EXTENDED SECTIONS] No comprehensive data available, but preserved {preserved_history} History of Past Illness entries from specialized extraction")
                    else:
                        logger.info("[EXTENDED SECTIONS] No comprehensive data available, added empty extended sections")
                    
            except Exception as e:
                logger.warning(f"[EXTENDED SECTIONS] Failed to detect extended sections: {e}")
                # Add empty extended sections on error but preserve specialized extractions
                context.update({
                    "history_of_past_illness": context.get("history_of_past_illness", []),  # Preserve existing
                    "immunizations": context.get("immunizations", []),
                    "pregnancy_history": context.get("pregnancy_history", []),  # Preserve existing
                    "social_history": [],
                    "physical_findings": context.get("physical_findings", []),  # Preserve existing
                    "coded_results": context.get("coded_results", {}),  # Preserve existing
                    "laboratory_results": [],
                    "advance_directives": [],
                    "additional_sections": []
                })

        except Exception as e:
            logger.warning(f"[CLINICAL ARRAYS SESSION] Clinical arrays extraction failed: {e}")
            # Ensure clinical arrays exist even if extraction fails
            context.update(
                {
                    "medications": [],
                    "allergies": [],
                    "problems": [],
                    "procedures": [],
                    "vital_signs": [],
                    "results": [],
                    "immunizations": [],
                    "history_of_past_illness": [],
                    "pregnancy_history": [],
                    "social_history": [],
                    "physical_findings": [],
                    "coded_results": {},
                    "laboratory_results": [],
                    "advance_directives": [],
                    "additional_sections": []
                }
            )

        # Extract enhanced data from CDADisplayService result
        enhanced_processing_result = translation_result
        enhanced_patient_identity = enhanced_processing_result.get(
            "patient_identity", {}
        )
        enhanced_admin_data = enhanced_processing_result.get("administrative_data", {})

        # Update patient identity with enhanced data while preserving patient_id for routing
        if enhanced_patient_identity:
            logger.info(
                f"[ENHANCED MERGE DEBUG] Before merge - patient_identity has patient_identifiers: {'patient_identifiers' in context['patient_identity']}"
            )
            if "patient_identifiers" in context["patient_identity"]:
                logger.info(
                    f"[ENHANCED MERGE DEBUG] Before merge - patient_identifiers: {context['patient_identity']['patient_identifiers']}"
                )

            logger.info(
                f"[ENHANCED MERGE DEBUG] enhanced_patient_identity keys: {enhanced_patient_identity.keys()}"
            )
            logger.info(
                f"[ENHANCED MERGE DEBUG] enhanced_patient_identity has patient_identifiers: {'patient_identifiers' in enhanced_patient_identity}"
            )

            url_patient_id = context["patient_identity"][
                "patient_id"
            ]  # Keep for URL routing
            xml_patient_id = enhanced_patient_identity.get(
                "patient_id"
            )  # From XML document

            # Preserve patient_identifiers before updating
            existing_patient_identifiers = context["patient_identity"].get(
                "patient_identifiers", []
            )
            logger.info(
                f"[ENHANCED MERGE DEBUG] Preserving {len(existing_patient_identifiers)} patient identifiers before merge"
            )

            # Store the enhanced data temporarily to check for patient_identifiers
            enhanced_has_valid_identifiers = (
                enhanced_patient_identity.get("patient_identifiers")
                and len(enhanced_patient_identity.get("patient_identifiers", [])) > 0
            )
            logger.info(
                f"[ENHANCED MERGE DEBUG] Enhanced data has valid patient_identifiers: {enhanced_has_valid_identifiers}"
            )

            context["patient_identity"].update(enhanced_patient_identity)

            logger.info(
                f"[ENHANCED MERGE DEBUG] After merge - patient_identity has patient_identifiers: {'patient_identifiers' in context['patient_identity']}"
            )
            current_identifiers = context["patient_identity"].get(
                "patient_identifiers", []
            )
            logger.info(
                f"[ENHANCED MERGE DEBUG] After merge - patient_identifiers length: {len(current_identifiers) if current_identifiers else 0}"
            )

            # Always restore existing patient_identifiers if they exist and the merged data doesn't have valid ones
            if existing_patient_identifiers and (
                not context["patient_identity"].get("patient_identifiers")
                or len(context["patient_identity"].get("patient_identifiers", [])) == 0
            ):
                context["patient_identity"][
                    "patient_identifiers"
                ] = existing_patient_identifiers
                logger.info(
                    f"[PATIENT IDENTITY] Restored {len(existing_patient_identifiers)} patient identifiers after merge overwrote them"
                )
            elif existing_patient_identifiers and not enhanced_has_valid_identifiers:
                # Enhanced data had empty/invalid patient_identifiers, so preserve the original
                context["patient_identity"][
                    "patient_identifiers"
                ] = existing_patient_identifiers
                logger.info(
                    f"[PATIENT IDENTITY] Preserved {len(existing_patient_identifiers)} patient identifiers over empty enhanced data"
                )
            elif context["patient_identity"].get("patient_identifiers"):
                logger.info(
                    f"[ENHANCED MERGE DEBUG] patient_identifiers already present after merge: {len(context['patient_identity']['patient_identifiers'])}"
                )
            else:
                logger.info(
                    f"[ENHANCED MERGE DEBUG] No patient_identifiers to preserve and none in enhanced data"
                )

            # Use XML patient ID for display, session ID for routing
            if xml_patient_id:
                context["patient_identity"][
                    "patient_id"
                ] = xml_patient_id  # Display the XML patient ID
                context["patient_identity"][
                    "url_patient_id"
                ] = url_patient_id  # Keep session ID for navigation
            else:
                context["patient_identity"][
                    "patient_id"
                ] = url_patient_id  # Ensure session ID is preserved

        # Update administrative data with enhanced data
        if enhanced_admin_data:
            # Ensure administrative data is JSON serializable
            context["administrative_data"] = make_serializable(enhanced_admin_data)
            # Use our helper function to properly detect meaningful content
            context["has_administrative_data"] = has_meaningful_administrative_data(
                enhanced_admin_data
            )
        else:
            context["administrative_data"] = {}
            context["has_administrative_data"] = False

        # Add single language flag to context
        context["is_single_language"] = enhanced_processing_result.get(
            "is_single_language", False
        )

        # Add template translations for dynamic UI text
        detected_source_language = enhanced_processing_result.get(
            "source_language", "en"
        )
        template_translations = get_template_translations(
            source_language=detected_source_language, target_language="en"
        )
        context["template_translations"] = template_translations
        context["detected_source_language"] = detected_source_language

        logger.info(
            f"Added template translations for {detected_source_language} → en with {len(template_translations)} strings"
        )

        # CLINICAL ARRAYS: Context already added by comprehensive clinical data service earlier in view
        # (Duplicate extraction removed to prevent overriding working clinical arrays)

        # NEW: Use CDA Display Data Helper to extract comprehensive extended patient data
        try:
            from .cda_display_data_helper import CDADisplayDataHelper

            logger.info(
                "[INFO] Extracting extended patient data using CDA Display Data Helper..."
            )
            display_helper = CDADisplayDataHelper()

            # Extract extended patient data if we have CDA content
            enhanced_extended_data = None
            if cda_content and cda_content.strip():
                enhanced_extended_data = display_helper.extract_extended_patient_data(
                    cda_content
                )

            if enhanced_extended_data:
                # Use the enhanced extraction result
                context["patient_extended_data"] = enhanced_extended_data
                # Also add administrative_data to context for template compatibility
                context["administrative_data"] = enhanced_extended_data.get(
                    "administrative_data", {}
                )
                # Add template-expected variables for compatibility (using standardized keys)
                context["contact_data"] = enhanced_extended_data.get("contact_data", {})
                context["contact_info"] = enhanced_extended_data.get(
                    "contact_data", {}
                )  # Template compatibility

                # Enhanced CDA Parser healthcare data override (always prefer fresh extraction)
                enhanced_healthcare_data = {}
                admin_data = enhanced_extended_data.get("administrative_data", {})

                # Use Enhanced CDA Parser logic for healthcare data mapping
                if (
                    admin_data.get("author_hcp")
                    or admin_data.get("author_information")
                    or admin_data.get("custodian_organization")
                    or admin_data.get("legal_authenticator")
                ):
                    # Map author information - prefer single author_hcp, fallback to first author_information
                    if admin_data.get("author_hcp"):
                        enhanced_healthcare_data["author_hcp"] = admin_data.get(
                            "author_hcp"
                        )
                    elif admin_data.get("author_information"):
                        author_info_list = admin_data.get("author_information")
                        if (
                            isinstance(author_info_list, list)
                            and len(author_info_list) > 0
                        ):
                            # Take the first author and flatten person info to top level
                            first_author = author_info_list[0]
                            if (
                                isinstance(first_author, dict)
                                and "person" in first_author
                            ):
                                # Flatten person info to top level for template compatibility
                                enhanced_healthcare_data["author_hcp"] = {
                                    "family_name": first_author["person"].get(
                                        "family_name"
                                    ),
                                    "given_name": first_author["person"].get(
                                        "given_name"
                                    ),
                                    "full_name": first_author["person"].get(
                                        "full_name"
                                    ),
                                    "title": first_author["person"].get("title"),
                                    "role": first_author["person"].get("role"),
                                    "organization": first_author.get(
                                        "organization", {}
                                    ),
                                }
                            else:
                                enhanced_healthcare_data["author_hcp"] = first_author
                        else:
                            enhanced_healthcare_data["author_hcp"] = author_info_list

                    # Map organization - prefer custodian_organization, fallback to organization
                    if admin_data.get("custodian_organization"):
                        enhanced_healthcare_data["organization"] = admin_data.get(
                            "custodian_organization"
                        )
                    elif admin_data.get("organization"):
                        enhanced_healthcare_data["organization"] = admin_data.get(
                            "organization"
                        )

                    # Map legal authenticator
                    if admin_data.get("legal_authenticator"):
                        enhanced_healthcare_data["legal_authenticator"] = (
                            admin_data.get("legal_authenticator")
                        )

                    logger.info(
                        f"[SUCCESS] Enhanced healthcare_data mapping: {list(enhanced_healthcare_data.keys())}"
                    )
                    logger.info(
                        f"[DEBUG] Enhanced Author HCP: {enhanced_healthcare_data.get('author_hcp', {}).get('full_name', 'None')}"
                    )
                    logger.info(
                        f"[DEBUG] Enhanced Organization: {enhanced_healthcare_data.get('organization', {}).get('name', 'None')}"
                    )

                # Use enhanced healthcare data if available, otherwise fallback to original
                context["healthcare_data"] = (
                    enhanced_healthcare_data
                    if enhanced_healthcare_data
                    else enhanced_extended_data.get("healthcare_data", {})
                )
                # Store patient-specific extended data in session
                request.session[f"patient_extended_data_{session_id}"] = (
                    enhanced_extended_data
                )
                logger.info(
                    f"[SUCCESS] Successfully extracted enhanced extended patient data for session {session_id}"
                )
                logger.info(
                    f"   - Administrative data: {'Yes' if enhanced_extended_data.get('administrative_data') else 'No'}"
                )
                logger.info(
                    f"   - Contact information: {'Yes' if enhanced_extended_data.get('contact_data') else 'No'}"
                )
                logger.info(
                    f"   - Healthcare providers: {'Yes' if enhanced_extended_data.get('healthcare_data') else 'No'}"
                )
                logger.info(
                    f"   - Document details: {'Yes' if enhanced_extended_data.get('document_details') else 'No'}"
                )
            else:
                # Fallback to existing extraction method
                logger.info(
                    "[WARNING] Enhanced extraction failed, falling back to existing method..."
                )

                if extended_header_data:
                    context["patient_extended_data"] = extended_header_data
                    context["administrative_data"] = (
                        extended_header_data  # Template compatibility
                    )
                    context["contact_data"] = {}  # Empty for template compatibility
                    context["contact_info"] = {}  # Template compatibility
                    context["healthcare_data"] = {}  # Empty for template compatibility
                    context["coded_results"] = {"blood_group": [], "diagnostic_results": []}  # Empty for template compatibility
                    request.session[f"patient_extended_data_{session_id}"] = (
                        extended_header_data
                    )
                    logger.info(
                        f"[LIST] Using fallback extended header data for session {session_id}"
                    )
                else:
                    context["patient_extended_data"] = None
                    context["administrative_data"] = {}  # Empty dict for template
                    context["contact_data"] = {}  # Empty for template compatibility
                    context["contact_info"] = {}  # Template compatibility
                    context["healthcare_data"] = {}  # Empty for template compatibility
                    context["coded_results"] = {"blood_group": [], "diagnostic_results": []}  # Empty for template compatibility
                    logger.warning(
                        "[ERROR] No extended patient data available from any extraction method"
                    )

        except Exception as helper_error:
            logger.error(f"[ERROR] CDA Display Data Helper failed: {helper_error}")

            # Fallback to original method
            if extended_header_data:
                context["patient_extended_data"] = extended_header_data
                context["administrative_data"] = (
                    extended_header_data  # Template compatibility
                )
                context["contact_data"] = {}  # Empty for template compatibility
                context["contact_info"] = {}  # Template compatibility
                context["healthcare_data"] = {}  # Empty for template compatibility
                context["coded_results"] = {"blood_group": [], "diagnostic_results": []}  # Empty for template compatibility
                request.session[f"patient_extended_data_{session_id}"] = (
                    extended_header_data
                )
                logger.info("[LIST] Using original extended header data as fallback")
            else:
                context["patient_extended_data"] = None
                context["administrative_data"] = {}  # Empty dict for template
                context["contact_data"] = {}  # Empty for template compatibility
                context["healthcare_data"] = {}  # Empty for template compatibility
                context["coded_results"] = {"blood_group": [], "diagnostic_results": []}  # Empty for template compatibility
                logger.warning("[ERROR] No extended header data available for fallback")

        # [DEBUG] Social History Template Context Debug
        logger.info(f"🔍 [TEMPLATE DEBUG] About to render template with context...")
        logger.info(f"🔍 [TEMPLATE DEBUG] Context has 'social_history' key: {'social_history' in context}")
        if 'social_history' in context:
            social_hist = context['social_history']
            logger.info(f"🔍 [TEMPLATE DEBUG] social_history type: {type(social_hist)}")
            logger.info(f"🔍 [TEMPLATE DEBUG] social_history length: {len(social_hist) if hasattr(social_hist, '__len__') else 'N/A'}")
            logger.info(f"🔍 [TEMPLATE DEBUG] social_history content: {social_hist}")
            if social_hist and len(social_hist) > 0:
                logger.info("✅ [TEMPLATE DEBUG] Template condition SHOULD evaluate to TRUE")
            else:
                logger.info("❌ [TEMPLATE DEBUG] Template condition will evaluate to FALSE")
        
        if 'extended_sections' in context:
            ext_sections = context['extended_sections']
            logger.info(f"🔍 [TEMPLATE DEBUG] extended_sections type: {type(ext_sections)}")
            if hasattr(ext_sections, 'get'):
                ext_social = ext_sections.get('social_history', [])
                logger.info(f"🔍 [TEMPLATE DEBUG] extended_sections.social_history: {ext_social}")

        # Prepare template context - use enhanced template with proper content
        return render(request, "patient_data/enhanced_patient_cda.html", context)

    except Exception as e:
        logger.error(f"Error in patient_cda_view: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Re-raise the exception to see the full Django debug page
        raise e


@login_required
@require_http_methods(["POST"])
def cda_translation_toggle(request, patient_id):
    """AJAX endpoint for toggling CDA translation sections"""
    try:
        data = json.loads(request.body)
        section_id = data.get("section_id")
        show_translation = data.get("show_translation", True)
        target_language = data.get("target_language", "en")

        # Placeholder implementation
        return JsonResponse(
            {
                "success": True,
                "message": "Function temporarily disabled during refactoring",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cda_translation_toggle(request, patient_id):
    """AJAX endpoint for toggling CDA translation sections"""
    try:
        data = json.loads(request.body)
        section_id = data.get("section_id")
        show_translation = data.get("show_translation", True)
        target_language = data.get("target_language", "en")

        # Placeholder implementation
        return JsonResponse(
            {
                "success": True,
                "message": "Function temporarily disabled during refactoring",
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cda_translation_toggle(request, patient_id):
    """AJAX endpoint for toggling CDA translation sections"""
    try:
        data = json.loads(request.body)
        section_id = data.get("section_id")
        show_translation = data.get("show_translation", True)
        target_language = data.get("target_language", "en")

        # Get patient data and CDA content
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            return JsonResponse({"error": "No CDA document found"}, status=404)

        # Initialize translation manager
        from .services.cda_translation_manager import CDATranslationManager

        translation_manager = CDATranslationManager(target_language=target_language)

        # Process the specific section if section_id provided
        if section_id:
            # Get section-specific translation
            cda_content = match_data.get("l3_cda_content") or match_data.get(
                "cda_content", ""
            )
            translation_data = translation_manager.process_cda_for_viewer(cda_content)

            # Find the specific section
            section_data = None
            for section in translation_data.get("clinical_sections", []):
                if section["id"] == section_id:
                    section_data = section
                    break

            if section_data:
                return JsonResponse(
                    {
                        "success": True,
                        "section": section_data,
                        "show_translation": show_translation,
                    }
                )
            else:
                return JsonResponse({"error": "Section not found"}, status=404)

        # Return general translation status
        return JsonResponse(
            {
                "success": True,
                "translation_status": translation_manager.get_translation_status(),
            }
        )

    except PatientData.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)
    except Exception as e:
        logger.error(f"Error in CDA translation toggle: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def download_cda_xml(request, patient_id):
    """Download CDA document as XML file - prefers L1 for better PDF structure"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # For PDF/ORCD extraction, prefer L1 documents as they have better structure
        # Reconstruct PatientMatch to get the appropriate content
        from .services.patient_search_service import PatientMatch

        # Get patient info
        patient_info = match_data.get("patient_data", {})

        # Reconstruct PatientMatch object to use proper content selection
        search_result = PatientMatch(
            patient_id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=patient_info.get("birth_date", ""),
            gender=patient_info.get("gender", ""),
            country_code=match_data.get("country_code", ""),
            confidence_score=match_data.get("confidence_score", 0.95),
            file_path=match_data.get("file_path"),
            l1_cda_content=match_data.get("l1_cda_content"),
            l3_cda_content=match_data.get("l3_cda_content"),
            l1_cda_path=match_data.get("l1_cda_path"),
            l3_cda_path=match_data.get("l3_cda_path"),
            cda_content=match_data.get("cda_content"),
            patient_data=patient_info,
            # Include document arrays and selected indices
            l1_documents=match_data.get("l1_documents", []),
            l3_documents=match_data.get("l3_documents", []),
            selected_l1_index=match_data.get("selected_l1_index", 0),
            selected_l3_index=match_data.get("selected_l3_index", 0),
        )

        # Get ORCD content (prefers L1 for PDF generation)
        orcd_content = search_result.get_orcd_cda()

        if not orcd_content:
            messages.error(request, "No CDA content available for download.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Determine the document type being downloaded
        document_type = "L1" if search_result.l1_cda_content else "L3"

        # Return the XML content for download
        response = HttpResponse(orcd_content, content_type="application/xml")
        response["Content-Disposition"] = (
            f'attachment; filename="patient_cda_{patient_id}_{document_type}.xml"'
        )

        return response

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_cda_html(request, patient_id):
    """Download CDA document as HTML transcoded view"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Return the HTML content for download
        # The CDA content should already be in HTML format from the L3 transformation
        response = HttpResponse(match_data["cda_content"], content_type="text/html")
        response["Content-Disposition"] = (
            f'attachment; filename="patient_cda_{patient_id}.html"'
        )

        return response

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_cda_pdf(request, patient_id):
    """Download the rendered CDA document as self-contained HTML with collapsible sections"""

    logger.info(f"CDA HTML download requested for patient {patient_id}")

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(f"Created temporary patient object for CDA HTML: {patient_id}")
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
                logger.info(
                    f"Found patient_data: {patient_data.given_name} {patient_data.family_name}"
                )
            except PatientData.DoesNotExist:
                logger.error(f"Patient data not found for ID: {patient_id}")
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        if not match_data:
            logger.error("No match_data found in session")
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Get the enhanced CDA processor to render the structured view
        from .services.enhanced_cda_processor import EnhancedCDAProcessor

        # Process the CDA content to get structured sections
        processor = EnhancedCDAProcessor()

        # Use L3 content if available, otherwise fall back to main content
        cda_content = match_data.get("l3_cda_content") or match_data.get(
            "cda_content", ""
        )

        if not cda_content:
            messages.error(request, "No CDA content available for processing.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Process the CDA content
        processed_data = processor.process_clinical_sections(cda_content)

        logger.info(
            f"Processed CDA into {processed_data.get('sections_count', 0)} sections"
        )

        # Extract sections from the processed data
        if not processed_data.get("success", False):
            messages.error(
                request,
                f"Error processing CDA: {processed_data.get('error', 'Unknown error')}",
            )
            return redirect("patient_data:patient_details", patient_id=patient_id)

        processed_sections = processed_data.get("sections", [])

        # Generate self-contained HTML from the structured sections
        return generate_structured_cda_html(
            request, patient_id, patient_data, match_data, processed_sections
        )

    except Exception as e:
        logger.error(f"Error in download_cda_pdf: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating CDA HTML document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def transform_entries_for_interactive_tables(entries, section_title):
    """Transform entries from CDA processor format to interactive table format"""
    if not entries:
        return []

    transformed = []

    for entry in entries:
        # Handle different entry formats from Enhanced CDA Processor

        # Format 1: Entry with fields structure (from generic XML parsing)
        fields = entry.get("fields", {})
        entry_text = entry.get("text", "")

        # Format 2: Direct field data (from country-specific or table extraction)
        if not fields and isinstance(entry, dict):
            # Convert direct entry to fields format
            fields = {
                k: {"value": v}
                for k, v in entry.items()
                if k not in ["text", "id", "entry_type"]
            }
            if not entry_text:
                entry_text = entry.get("text", entry.get("description", ""))

        if "medication" in section_title.lower():
            # Transform for medication table
            transformed_entry = {
                "Medication": extract_field_value_simple(
                    fields,
                    [
                        "Medication Name",
                        "Medication",
                        "Drug Name",
                        "medication_name",
                        "name",
                    ],
                )
                or entry_text,
                "Dosage & Strength": extract_field_value_simple(
                    fields, ["Dosage", "Strength", "Dose", "dose", "dosage"]
                ),
                "Frequency": extract_field_value_simple(
                    fields, ["Frequency", "Administration Frequency", "frequency"]
                ),
                "Status": extract_field_value_simple(
                    fields, ["Status", "Medication Status", "status"]
                )
                or "Active",
                "Start Date": extract_field_value_simple(
                    fields, ["Start Date", "Effective Date", "start_date", "date"]
                ),
                "Codes": extract_codes_simple(fields),
            }
        elif "allergi" in section_title.lower() or "adverse" in section_title.lower():
            # Transform for allergy table
            transformed_entry = {
                "Allergen": extract_field_value_simple(
                    fields, ["Allergen", "Agent", "Substance", "allergen", "agent"]
                )
                or entry_text,
                "Reaction": extract_field_value_simple(
                    fields, ["Reaction", "Manifestation", "reaction"]
                ),
                "Severity": extract_field_value_simple(
                    fields, ["Severity", "Criticality", "severity"]
                ),
                "Status": extract_field_value_simple(fields, ["Status", "status"])
                or "Active",
                "First Noted": extract_field_value_simple(
                    fields, ["Onset Date", "First Noted", "Date", "date", "onset_date"]
                ),
                "Codes": extract_codes_simple(fields),
            }
        elif "procedure" in section_title.lower():
            # Transform for procedure table
            transformed_entry = {
                "Procedure": extract_field_value_simple(
                    fields, ["Procedure", "Procedure Name", "procedure_name", "name"]
                )
                or entry_text,
                "Date Performed": extract_field_value_simple(
                    fields,
                    [
                        "Date Performed",
                        "Procedure Date",
                        "Date",
                        "date",
                        "performed_date",
                    ],
                ),
                "Status": extract_field_value_simple(fields, ["Status", "status"])
                or "Completed",
                "Healthcare Provider": extract_field_value_simple(
                    fields, ["Provider", "Performer", "Healthcare Provider", "provider"]
                ),
                "Medical Codes": extract_codes_simple(fields),
            }
        elif "problem" in section_title.lower() or "diagnosis" in section_title.lower():
            # Transform for problem table
            transformed_entry = {
                "Problem": extract_field_value_simple(
                    fields,
                    [
                        "Problem",
                        "Diagnosis",
                        "Condition",
                        "problem",
                        "diagnosis",
                        "condition",
                    ],
                )
                or entry_text,
                "Status": extract_field_value_simple(fields, ["Status", "status"])
                or "Active",
                "Onset Date": extract_field_value_simple(
                    fields, ["Onset Date", "Date", "onset_date", "date"]
                ),
                "Notes": extract_field_value_simple(
                    fields, ["Notes", "Comment", "notes", "comment"]
                ),
                "Codes": extract_codes_simple(fields),
            }
        elif "immuniz" in section_title.lower() or "vaccin" in section_title.lower():
            # Transform for immunization table
            transformed_entry = {
                "Vaccine": extract_field_value_simple(
                    fields, ["Vaccine", "Immunization", "vaccine_name", "name"]
                )
                or entry_text,
                "Date Given": extract_field_value_simple(
                    fields, ["Date Given", "Administration Date", "Date", "date"]
                ),
                "Dose": extract_field_value_simple(
                    fields, ["Dose", "Dose Number", "dose"]
                ),
                "Status": extract_field_value_simple(fields, ["Status", "status"])
                or "Completed",
                "Codes": extract_codes_simple(fields),
            }
        elif "device" in section_title.lower():
            # Transform for medical device table
            transformed_entry = {
                "Device": extract_field_value_simple(
                    fields,
                    ["Device", "Device Name", "Medical Device", "device_name", "name"],
                )
                or entry_text,
                "Type": extract_field_value_simple(
                    fields, ["Type", "Device Type", "type"]
                ),
                "Status": extract_field_value_simple(fields, ["Status", "status"])
                or "Active",
                "Implant Date": extract_field_value_simple(
                    fields, ["Implant Date", "Date", "implant_date", "date"]
                ),
                "Codes": extract_codes_simple(fields),
            }
        else:
            # Generic transformation
            transformed_entry = {}
            # Add all available fields
            for field_name, field_data in fields.items():
                if isinstance(field_data, dict):
                    value = field_data.get(
                        "value", field_data.get("displayName", str(field_data))
                    )
                else:
                    value = str(field_data)

                # Clean up field name for display
                clean_field_name = field_name.replace("_", " ").title()
                transformed_entry[clean_field_name] = value

            # Add text content if available
            if entry_text and "Text Content" not in transformed_entry:
                transformed_entry["Content"] = entry_text

        if transformed_entry:
            transformed.append(transformed_entry)

    return transformed


def extract_field_value_simple(fields, field_patterns):
    """Extract value from fields using field patterns"""
    for pattern in field_patterns:
        for field_name, field_data in fields.items():
            if pattern.lower() in field_name.lower():
                if isinstance(field_data, dict):
                    return field_data.get("value", field_data.get("displayName", ""))
                else:
                    return str(field_data)
    return "Not specified"


def extract_codes_simple(fields):
    """Extract medical codes from fields"""
    codes = []
    for field_name, field_data in fields.items():
        if "code" in field_name.lower():
            if isinstance(field_data, dict):
                code_value = field_data.get("code", field_data.get("value", ""))
                if code_value:
                    codes.append(str(code_value))
            elif field_data:
                codes.append(str(field_data))
    return ", ".join(codes) if codes else ""


def generate_structured_cda_html(
    request, patient_id, patient_data, match_data, processed_sections
):
    """Generate self-contained HTML from structured CDA sections with collapsible functionality"""

    logger.info("Generating structured CDA HTML with collapsible sections")

    try:
        # Get patient info
        patient_info = match_data.get("patient_data", {})

        # Build the structured HTML content with collapsible sections
        sections_html = ""

        logger.info(
            f"Processing {len(processed_sections)} sections for HTML generation"
        )

        for i, section in enumerate(processed_sections):
            section_title = section.get("title", "Unknown Section")

            # Handle different section data formats from Enhanced CDA Processor
            section_entries = []

            # Check if section has structured_data (the new format)
            if "structured_data" in section and section["structured_data"]:
                section_entries = section["structured_data"]
            # Check if section has table_rows (alternative format)
            elif "table_rows" in section and section["table_rows"]:
                section_entries = section["table_rows"]
            # Check if section has table_data (country-specific format)
            elif "table_data" in section and section["table_data"]:
                section_entries = section["table_data"]
            # Fallback to entries field
            elif "entries" in section:
                section_entries = section["entries"]

            # Handle title format - could be string or dict
            if isinstance(section_title, dict):
                section_title = section_title.get(
                    "translated",
                    section_title.get(
                        "coded", section_title.get("original", "Unknown Section")
                    ),
                )

            section_code = section.get("code", section.get("section_code", ""))
            original_content = section.get("original_content", "")

            logger.info(
                f"Section {i}: '{section_title}' with {len(section_entries)} entries"
            )

            if section_entries:
                logger.info(f"First entry structure: {section_entries[0]}")

            if not section_entries:
                logger.info(f"Skipping empty section: {section_title}")
                continue

            # Transform entries to the format expected by interactive tables
            transformed_entries = transform_entries_for_interactive_tables(
                section_entries, section_title
            )

            if not transformed_entries:
                logger.info(f"No transformed entries for section: {section_title}")
                continue

            section_id = f"section_{i}"

            sections_html += f"""
            <div class="clinical-section" id="{section_id}">
                <div class="section-header" onclick="toggleSection('{section_id}')">
                    <h2 class="section-title">
                        <span class="toggle-icon">▼</span>
                        {section_title}
                        <small class="section-info">({len(section_entries)} entries)</small>
                    </h2>
                </div>

                <div class="section-content expanded" id="{section_id}_content">
                    <div class="section-tabs">
                        <button class="tab-button active" onclick="showTab('{section_id}', 'structured')">
                            [DATA] Structured View
                        </button>
                        <button class="tab-button" onclick="showTab('{section_id}', 'original')">
                            📄 Original Content
                        </button>
                    </div>

                    <div id="{section_id}_structured" class="tab-content active">
            """

            # Handle different section types based on title
            if "medication" in section_title.lower():
                sections_html += generate_medication_table_html_interactive(
                    transformed_entries
                )
            elif (
                "allergi" in section_title.lower() or "adverse" in section_title.lower()
            ):
                sections_html += generate_allergy_table_html_interactive(
                    transformed_entries
                )
            elif "procedure" in section_title.lower():
                sections_html += generate_procedure_table_html_interactive(
                    transformed_entries
                )
            elif (
                "problem" in section_title.lower()
                or "diagnosis" in section_title.lower()
            ):
                sections_html += generate_problem_table_html_interactive(
                    transformed_entries
                )
            else:
                # Generic table for other sections
                sections_html += generate_generic_table_html_interactive(
                    transformed_entries
                )

            sections_html += f"""
                    </div>

                    <div id="{section_id}_original" class="tab-content">
                        <div class="original-content">
                            <h4>Original CDA Content (Code: {section_code})</h4>
                            <pre class="xml-content">{html.escape(original_content[:2000]) if original_content else "No original content available"}</pre>
                        </div>
                    </div>
                </div>
            </div>
            """

        # Handle patient data format - could be dict or object
        if isinstance(patient_data, dict):
            patient_given_name = (
                patient_data.get("name", "Unknown").split()[0]
                if patient_data.get("name")
                else "Unknown"
            )
            patient_family_name = (
                patient_data.get("name", "Unknown").split()[-1]
                if patient_data.get("name")
                and len(patient_data.get("name", "").split()) > 1
                else ""
            )
        else:
            patient_given_name = getattr(patient_data, "given_name", "Unknown")
            patient_family_name = getattr(patient_data, "family_name", "")

        # Create the complete self-contained HTML document
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clinical Document - {patient_given_name} {patient_family_name}</title>
    <style>
        /* Self-contained CSS for clinical document */
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}

        .document-container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}

        .patient-header {{
            background: linear-gradient(135deg, #4a90e2, #357abd);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .patient-header h1 {{
            font-size: 2.5em;
            margin-bottom: 15px;
            font-weight: 300;
        }}

        .patient-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .info-card {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #fff;
        }}

        .clinical-section {{
            border-bottom: 1px solid #e9ecef;
        }}

        .section-header {{
            background: #f8f9fa;
            padding: 20px;
            cursor: pointer;
            transition: background-color 0.3s;
            border-left: 4px solid #4a90e2;
        }}

        .section-header:hover {{
            background: #e9ecef;
        }}

        .section-title {{
            display: flex;
            align-items: center;
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
        }}

        .toggle-icon {{
            margin-right: 12px;
            transition: transform 0.3s;
            font-size: 0.8em;
        }}

        .section-header.collapsed .toggle-icon {{
            transform: rotate(-90deg);
        }}

        .section-info {{
            margin-left: auto;
            font-size: 0.9em;
            color: #6c757d;
            font-weight: 400;
        }}

        .section-content {{
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.3s ease-in-out;
        }}

        .section-content.collapsed {{
            max-height: 0;
        }}

        .section-tabs {{
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }}

        .tab-button {{
            background: none;
            border: none;
            padding: 15px 25px;
            cursor: pointer;
            font-size: 1em;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }}

        .tab-button:hover {{
            background: #e9ecef;
            color: #495057;
        }}

        .tab-button.active {{
            color: #4a90e2;
            border-bottom-color: #4a90e2;
            background: white;
        }}

        .tab-content {{
            display: none;
            padding: 25px;
        }}

        .tab-content.active {{
            display: block;
        }}

        .clinical-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .clinical-table th {{
            background: #4a90e2;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .clinical-table td {{
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            vertical-align: top;
        }}

        .clinical-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .clinical-table tr:hover {{
            background: #e3f2fd;
        }}

        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-active {{
            background: #d4edda;
            color: #155724;
        }}

        .status-completed {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .status-inactive {{
            background: #f8d7da;
            color: #721c24;
        }}

        .medical-code {{
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            color: #495057;
            cursor: help;
            margin: 2px;
            display: inline-block;
        }}

        .medical-code:hover {{
            background: #4a90e2;
            color: white;
        }}

        .original-content {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
        }}

        .xml-content {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.4;
            margin-top: 10px;
        }}

        .document-footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 1px solid #dee2e6;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .document-container {{
                box-shadow: none;
                border-radius: 0;
            }}
            .section-content {{
                max-height: none !important;
            }}
            .tab-content {{
                display: block !important;
            }}
        }}

        @media (max-width: 768px) {{
            .patient-info {{
                grid-template-columns: 1fr;
            }}
            .clinical-table {{
                font-size: 0.9em;
            }}
            .clinical-table th,
            .clinical-table td {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="patient-header">
            <h1>👤 {patient_given_name} {patient_family_name}</h1>

            <div class="patient-info">
                <div class="info-card">
                    <strong>Birth Date:</strong> {patient_data.get('dob') if isinstance(patient_data, dict) else getattr(patient_data, 'birth_date', None) or 'Not specified'}
                </div>
                <div class="info-card">
                    <strong>Gender:</strong> {patient_data.get('gender') if isinstance(patient_data, dict) else getattr(patient_data, 'gender', None) or 'Not specified'}
                </div>
                <div class="info-card">
                    <strong>Patient ID:</strong> {patient_id}
                </div>
                <div class="info-card">
                    <strong>Source Country:</strong> {patient_info.get('source_country', 'Unknown')}
                </div>
            </div>
        </div>

        <div class="document-body">
            {sections_html}
        </div>

        <div class="document-footer">
            <p><strong>Generated:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M')} |
            <strong>Source:</strong> EU NCP Portal |
            <strong>Document Type:</strong> L3 CDA with Structured Clinical Content</p>
        </div>
    </div>

    <script>
        // Self-contained JavaScript for interactivity
        function toggleSection(sectionId) {{
            const content = document.getElementById(sectionId + '_content');
            const header = document.querySelector('#' + sectionId + ' .section-header');

            if (content.classList.contains('collapsed')) {{
                content.classList.remove('collapsed');
                header.classList.remove('collapsed');
            }} else {{
                content.classList.add('collapsed');
                header.classList.add('collapsed');
            }}
        }}

        function showTab(sectionId, tabType) {{
            // Hide all tab contents for this section
            const structuredTab = document.getElementById(sectionId + '_structured');
            const originalTab = document.getElementById(sectionId + '_original');
            const buttons = document.querySelectorAll('#' + sectionId + ' .tab-button');

            structuredTab.classList.remove('active');
            originalTab.classList.remove('active');
            buttons.forEach(btn => btn.classList.remove('active'));

            // Show selected tab
            if (tabType === 'structured') {{
                structuredTab.classList.add('active');
                buttons[0].classList.add('active');
            }} else {{
                originalTab.classList.add('active');
                buttons[1].classList.add('active');
            }}
        }}

        // Add tooltips for medical codes
        document.addEventListener('DOMContentLoaded', function() {{
            const codes = document.querySelectorAll('.medical-code');
            codes.forEach(code => {{
                code.addEventListener('mouseenter', function() {{
                    // Future: Add tooltip with code description
                }});
            }});
        }});
    </script>
</body>
</html>"""

        logger.info(f"HTML content length: {len(html_content)} characters")

        # Create the HTTP response with HTML content
        response = HttpResponse(html_content, content_type="text/html")
        response["Content-Disposition"] = (
            f'attachment; filename="clinical_document_{patient_given_name}_{patient_family_name}_{patient_id}.html"'
        )

        logger.info(f"Generated structured CDA HTML for patient {patient_id}")

        return response

    except Exception as e:
        logger.error(f"Error in generate_structured_cda_html: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        # Only try to add messages if request has session middleware
        if hasattr(request, "_messages"):
            messages.error(request, "Error generating CDA HTML document.")
            return redirect("patient_data:patient_details", patient_id=patient_id)
        else:
            # For testing environments, return the error as HTML
            return f"<html><body><h1>Error generating CDA HTML</h1><p>{e}</p></body></html>"
    """Generate PDF from structured CDA sections (like the rendered view in the browser)"""

    logger.info("Generating structured CDA PDF")

    try:
        # Get patient info
        patient_info = match_data.get("patient_data", {})

        # Build the structured HTML content for PDF
        sections_html = ""

        for section in processed_sections:
            section_title = section.get("title", "Unknown Section")
            section_entries = section.get("entries", [])

            if not section_entries:
                continue

            sections_html += f'<div class="clinical-section">'
            sections_html += f'<h2 class="section-title">{section_title}</h2>'

            # Handle different section types based on title
            if "medication" in section_title.lower():
                sections_html += generate_medication_table_html(section_entries)
            elif (
                "allergi" in section_title.lower() or "adverse" in section_title.lower()
            ):
                sections_html += generate_allergy_table_html(section_entries)
            elif "procedure" in section_title.lower():
                sections_html += generate_procedure_table_html(section_entries)
            elif (
                "problem" in section_title.lower()
                or "diagnosis" in section_title.lower()
            ):
                sections_html += generate_problem_table_html(section_entries)
            else:
                # Generic table for other sections
                sections_html += generate_generic_table_html(section_entries)

            sections_html += "</div>"

        # Create the complete HTML document for PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Clinical Document - {patient_data.given_name} {patient_data.family_name}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 1.5cm;
                }}

                body {{
                    font-family: Arial, sans-serif;
                    font-size: 9pt;
                    line-height: 1.3;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}

                .patient-header {{
                    background-color: #4a90e2;
                    color: white;
                    padding: 15px;
                    margin-bottom: 20px;
                }}

                .patient-header h1 {{
                    margin: 0;
                    font-size: 18pt;
                }}

                .patient-info {{
                    display: flex;
                    justify-content: space-between;
                    margin-top: 10px;
                    font-size: 10pt;
                }}

                .clinical-section {{
                    margin-bottom: 25px;
                    page-break-inside: avoid;
                }}

                .section-title {{
                    background-color: #f8f9fa;
                    padding: 10px;
                    margin: 0 0 15px 0;
                    font-size: 14pt;
                    color: #2c3e50;
                    border-left: 4px solid #4a90e2;
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                    font-size: 8pt;
                }}

                th {{
                    background-color: #e8f4f8;
                    padding: 8px 6px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid #ddd;
                    font-size: 8pt;
                }}

                td {{
                    padding: 6px;
                    border: 1px solid #ddd;
                    vertical-align: top;
                }}

                .status-active {{
                    background-color: #d4edda;
                    color: #155724;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                }}

                .status-completed {{
                    background-color: #cce5ff;
                    color: #004085;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 7pt;
                }}

                .medical-code {{
                    background-color: #e9ecef;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 7pt;
                    margin: 1px;
                }}

                .footer {{
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #ddd;
                    font-size: 8pt;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="patient-header">
                <h1>👤 {patient_data.given_name} {patient_data.family_name}</h1>
                <div class="patient-info">
                    <div>
                        <strong>Birth Date:</strong> {patient_info.get('birth_date', 'Not specified')}<br>
                        <strong>Gender:</strong> {patient_info.get('gender', 'Not specified')}
                    </div>
                    <div>
                        <strong>Source Country:</strong> {match_data.get('country_code', 'Unknown')}<br>
                        <strong>Patient ID:</strong> {patient_info.get('primary_patient_id', 'Not specified')}
                    </div>
                </div>
            </div>

            {sections_html}

            <div class="footer">
                <p><strong>Generated:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M')} | <strong>Source:</strong> EU NCP Portal | <strong>Document Type:</strong> L3 CDA with Structured Clinical Content</p>
            </div>
        </body>
        </html>
        """

        # Generate PDF using xhtml2pdf
        logger.info("Starting structured CDA PDF generation")
        logger.info(f"HTML content length: {len(html_content)} characters")

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)

        logger.info(f"PDF generation completed. Errors: {pdf.err}")

        if not pdf.err:
            pdf_bytes = result.getvalue()
            result.close()

            logger.info(
                f"Structured CDA PDF generated successfully. Size: {len(pdf_bytes)} bytes"
            )

            # Create filename
            filename = f"{patient_data.given_name}_{patient_data.family_name}_Clinical_Document.pdf"

            # Return PDF response for preview
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            # Remove Content-Disposition to show in browser instead of downloading
            # response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                f"Generated structured CDA PDF preview for patient {patient_id}"
            )
            return response
        else:
            logger.error(f"Error generating structured CDA PDF: {pdf.err}")
            messages.error(request, "Error generating PDF document.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

    except Exception as e:
        logger.error(f"Error in generate_structured_cda_pdf: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating PDF document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def generate_medication_table_html(entries):
    """Generate HTML table for medication entries"""
    html = """
    <table>
        <thead>
            <tr>
                <th>Medication</th>
                <th>Dosage & Strength</th>
                <th>Frequency</th>
                <th>Status</th>
                <th>Start Date</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        fields = entry.get("fields", {})
        medication_name = fields.get("Medication Name", {}).get(
            "value", "Not specified"
        )
        dosage = fields.get("Dosage & Strength", {}).get(
            "value", "Concentrate for solution for injection"
        )
        frequency = fields.get("Frequency", {}).get("value", "1 day")
        status = fields.get("Status", {}).get("value", "Active")
        start_date = fields.get("Start Date", {}).get("value", "")

        status_class = "status-active" if status.lower() == "active" else ""

        html += f"""
        <tr>
            <td>{medication_name}</td>
            <td>{dosage}</td>
            <td>{frequency}</td>
            <td><span class="{status_class}">{status}</span></td>
            <td>{start_date}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_allergy_table_html(entries):
    """Generate HTML table for allergy entries"""
    html = """
    <table>
        <thead>
            <tr>
                <th>Allergen</th>
                <th>Reaction</th>
                <th>Severity</th>
                <th>Status</th>
                <th>First Noted</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        fields = entry.get("fields", {})
        allergen = fields.get("Allergen", {}).get("value", "Not specified")
        reaction = fields.get("Reaction", {}).get("value", "Not specified")
        severity = fields.get("Severity", {}).get("value", "Not specified")
        status = fields.get("Status", {}).get("value", "Not specified")
        first_noted = fields.get("First Noted", {}).get("value", "Not recorded")

        html += f"""
        <tr>
            <td>{allergen}</td>
            <td>{reaction}</td>
            <td>{severity}</td>
            <td>{status}</td>
            <td>{first_noted}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_procedure_table_html(entries):
    """Generate HTML table for procedure entries"""
    html = """
    <table>
        <thead>
            <tr>
                <th>Procedure</th>
                <th>Date Performed</th>
                <th>Status</th>
                <th>Healthcare Provider</th>
                <th>Medical Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        fields = entry.get("fields", {})
        procedure = fields.get("Procedure", {}).get("value", "Not specified")
        date_performed = fields.get("Date Performed", {}).get("value", "")
        status = fields.get("Status", {}).get("value", "Completed")
        provider = fields.get("Healthcare Provider", {}).get("value", "Not specified")

        # Handle medical codes
        codes_html = ""
        medical_codes = fields.get("Medical Codes", {})
        if isinstance(medical_codes, dict):
            for code_type, code_value in medical_codes.items():
                if code_value:
                    codes_html += f'<span class="medical-code">{code_value}</span> '

        status_class = "status-completed" if status.lower() == "completed" else ""

        html += f"""
        <tr>
            <td>{procedure}</td>
            <td>{date_performed}</td>
            <td><span class="{status_class}">{status}</span></td>
            <td>{provider}</td>
            <td>{codes_html}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_problem_table_html(entries):
    """Generate HTML table for problem/diagnosis entries"""
    html = """
    <table>
        <thead>
            <tr>
                <th>Problem/Diagnosis</th>
                <th>Status</th>
                <th>Date Onset</th>
                <th>Medical Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        fields = entry.get("fields", {})
        problem = fields.get("Problem", {}).get(
            "value", entry.get("text", "Not specified")
        )
        status = fields.get("Status", {}).get("value", "Active")
        date_onset = fields.get("Date Onset", {}).get("value", "")

        # Handle medical codes
        codes_html = ""
        medical_codes = fields.get("Medical Codes", {})
        if isinstance(medical_codes, dict):
            for code_type, code_value in medical_codes.items():
                if code_value:
                    codes_html += f'<span class="medical-code">{code_value}</span> '

        status_class = "status-active" if status.lower() == "active" else ""

        html += f"""
        <tr>
            <td>{problem}</td>
            <td><span class="{status_class}">{status}</span></td>
            <td>{date_onset}</td>
            <td>{codes_html}</td>
        </tr>
        """

    html += "</tbody></table>"
    return html


def generate_generic_table_html(entries):
    """Generate HTML table for generic entries"""
    if not entries:
        return "<p>No entries found in this section.</p>"

    # Get all unique field names for table headers
    all_fields = set()
    for entry in entries:
        if "fields" in entry:
            all_fields.update(entry["fields"].keys())

    if not all_fields:
        return "<p>No structured data available for this section.</p>"

    html = "<table><thead><tr>"
    for field in sorted(all_fields):
        html += f"<th>{field}</th>"
    html += "</tr></thead><tbody>"

    for entry in entries:
        html += "<tr>"
        fields = entry.get("fields", {})
        for field in sorted(all_fields):
            value = fields.get(field, {}).get("value", "")
            html += f"<td>{value}</td>"
        html += "</tr>"

    html += "</tbody></table>"
    return html


def download_patient_summary_pdf(request, patient_id):
    """Download Patient Summary as PDF - checks for embedded PDF in CDA first, falls back to HTML->PDF"""

    logger.info(f"PDF download requested for patient {patient_id}")

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for PDF download: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
                logger.info(
                    f"Found patient_data: {patient_data.given_name} {patient_data.family_name}"
                )
            except PatientData.DoesNotExist:
                logger.error(f"Patient data not found for ID: {patient_id}")
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        logger.info(f"Match data exists: {match_data is not None}")

        if not match_data:
            logger.error("No match_data found in session")
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # First, try to extract embedded PDF from CDA content (like your Flask app)
        logger.info("Attempting to extract embedded PDF from CDA content")

        # Check all available CDA content sources
        cda_sources = [
            ("L1", match_data.get("l1_cda_content")),
            ("L3", match_data.get("l3_cda_content")),
            ("original", match_data.get("cda_content")),
        ]

        for source_type, cda_content in cda_sources:
            if cda_content:
                logger.info(f"Checking {source_type} CDA content for embedded PDF")

                # Look for base64 PDF content (similar to your Flask app)
                import base64

                # Convert to bytes if it's a string
                if isinstance(cda_content, str):
                    cda_bytes = cda_content.encode("utf-8")
                else:
                    cda_bytes = cda_content

                # Look for base64 PDF patterns
                pdf_patterns = [
                    b'<text mediaType="application/pdf" representation="B64">',
                    b'<text mediatype="application/pdf" representation="B64">',
                    b'mediaType="application/pdf"',
                    b'mediatype="application/pdf"',
                ]

                for pattern in pdf_patterns:
                    start_index = cda_bytes.find(pattern)
                    if start_index != -1:
                        logger.info(
                            f"Found PDF pattern in {source_type} CDA: {pattern.decode('utf-8', errors='ignore')}"
                        )

                        # Find the content between tags
                        tag_end = cda_bytes.find(b">", start_index) + 1
                        end_tag = cda_bytes.find(b"</text>", tag_end)

                        if end_tag != -1:
                            # Extract base64 content
                            base64_content = cda_bytes[tag_end:end_tag].strip()

                            try:
                                # Decode base64 to get PDF bytes
                                pdf_bytes = base64.b64decode(base64_content)

                                # Verify it's a valid PDF
                                if pdf_bytes.startswith(b"%PDF"):
                                    logger.info(
                                        f"Successfully extracted PDF from {source_type} CDA. Size: {len(pdf_bytes)} bytes"
                                    )

                                    # Create filename
                                    filename = f"{patient_data.given_name}_{patient_data.family_name}_Patient_Summary.pdf"

                                    # Return PDF response for preview (not attachment)
                                    response = HttpResponse(
                                        pdf_bytes, content_type="application/pdf"
                                    )
                                    # Remove Content-Disposition to show in browser instead of downloading
                                    # response["Content-Disposition"] = f'attachment; filename="{filename}"'

                                    logger.info(
                                        f"Generated patient summary PDF preview for patient {patient_id}"
                                    )
                                    return response

                            except Exception as e:
                                logger.warning(
                                    f"Failed to decode base64 PDF from {source_type}: {e}"
                                )
                                continue

        logger.info("No embedded PDF found, falling back to HTML->PDF generation")

        # Fallback: Generate PDF from HTML content (existing logic)
        return generate_pdf_from_html(request, patient_id, patient_data, match_data)

    except Exception as e:
        logger.error(f"Unexpected error in download_patient_summary_pdf: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating PDF document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def generate_pdf_from_html(request, patient_id, patient_data, match_data):
    """Generate PDF from HTML content using xhtml2pdf"""

    logger.info("Generating PDF from HTML content using xhtml2pdf")

    try:
        # Get patient summary using the same logic as the details view
        search_service = EUPatientSearchService()

        # Reconstruct match object for summary
        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class SimplePatientResult:
            """Simple patient result for views"""

            file_path: str
            country_code: str
            confidence_score: float
            patient_data: Dict
            cda_content: str

        # Extract required fields from patient_data or use defaults
        patient_info = match_data.get("patient_data", {})

        match = SimplePatientResult(
            file_path=match_data["file_path"],
            country_code=match_data["country_code"],
            confidence_score=match_data["confidence_score"],
            patient_data=match_data["patient_data"],
            cda_content=match_data["cda_content"],
        )

        patient_summary = search_service.get_patient_summary(match)

        logger.info(f"Patient summary retrieved: {patient_summary is not None}")
        if patient_summary:
            logger.info(
                f"Patient summary keys: {list(patient_summary.keys()) if isinstance(patient_summary, dict) else type(patient_summary)}"
            )

        if not patient_summary:
            logger.error("No patient summary content available")
            # Create a basic summary from available data
            patient_summary = {
                "patient_name": f"{patient_data.given_name} {patient_data.family_name}",
                "birth_date": (
                    str(patient_data.birth_date)
                    if patient_data.birth_date
                    else "Not specified"
                ),
                "gender": patient_data.gender or "Not specified",
                "primary_patient_id": patient_info.get(
                    "primary_patient_id", "Not specified"
                ),
                "secondary_patient_id": patient_info.get("secondary_patient_id", ""),
                "cda_content": match_data.get("cda_content", ""),
            }

        # Get the CDA content from patient summary
        cda_content = patient_summary.get("cda_content", "")

        # If we have L3 content (HTML), prefer that
        l3_cda_content = match_data.get("l3_cda_content")
        if l3_cda_content:
            cda_content = l3_cda_content

        # Clean up and structure the content for PDF
        sections_html = ""
        if cda_content:
            # Clean up the CDA content for better PDF display
            import re
            from html import unescape

            # Remove XML declaration and root elements if present
            clean_content = re.sub(r"<\?xml[^>]*\?>", "", cda_content)
            clean_content = re.sub(r"<ClinicalDocument[^>]*>", "", clean_content)
            clean_content = re.sub(r"</ClinicalDocument>", "", clean_content)
            clean_content = re.sub(r"<component[^>]*>", "", clean_content)
            clean_content = re.sub(r"</component>", "", clean_content)
            clean_content = re.sub(r"<structuredBody[^>]*>", "", clean_content)
            clean_content = re.sub(r"</structuredBody>", "", clean_content)

            # Unescape HTML entities
            clean_content = unescape(clean_content)

            # If it's mostly tables and structured content, use it as-is
            sections_html = f"""
            <div class="section">
                <h2>Patient Summary Content</h2>
                <div class="content">
                    {clean_content}
                </div>
            </div>
            """
        else:
            sections_html = """
            <div class="section">
                <p>No detailed patient summary content available.</p>
            </div>
            """

        # Prepare HTML content with proper structure and inline CSS
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Patient Summary - {patient_data.given_name} {patient_data.family_name}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}

                body {{
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    line-height: 1.4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}

                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }}

                h1 {{ font-size: 16pt; }}
                h2 {{ font-size: 14pt; }}
                h3 {{ font-size: 12pt; }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                }}

                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }}

                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                    color: #2c3e50;
                }}

                .patient-header {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}

                .section {{
                    margin-bottom: 20px;
                }}

                ul {{
                    padding-left: 20px;
                }}

                li {{
                    margin-bottom: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="patient-header">
                <h1>Patient Summary</h1>
                <p><strong>Patient:</strong> {patient_summary.get('patient_name', 'Unknown')}</p>
                <p><strong>Date of Birth:</strong> {patient_summary.get('birth_date', 'Not specified')}</p>
                <p><strong>Gender:</strong> {patient_summary.get('gender', 'Not specified')}</p>
                <p><strong>Primary Patient ID:</strong> {patient_summary.get('primary_patient_id', 'Not specified')}</p>
                {f'<p><strong>Secondary Patient ID:</strong> {patient_summary.get("secondary_patient_id")}</p>' if patient_summary.get('secondary_patient_id') else ''}
                <p><strong>Generated:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div class="content">
                {sections_html}
            </div>
        </body>
        </html>
        """

        # Generate PDF using xhtml2pdf
        logger.info("Starting PDF generation with xhtml2pdf")
        logger.info(f"HTML content length: {len(html_content)} characters")

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)

        logger.info(f"PDF generation completed. Errors: {pdf.err}")

        if not pdf.err:
            pdf_bytes = result.getvalue()
            result.close()

            logger.info(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")

            # Create filename
            filename = f"{patient_data.given_name}_{patient_data.family_name}_Patient_Summary.pdf"

            # Return PDF response for preview (not attachment)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            # Remove Content-Disposition to show in browser instead of downloading
            # response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                f"Generated patient summary PDF preview for patient {patient_id}"
            )
            return response
        else:
            logger.error(f"Error generating PDF: {pdf.err}")
            messages.error(request, "Error generating PDF document.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

    except Exception as e:
        logger.error(f"Error in generate_pdf_from_html: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating PDF document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def download_patient_summary_pdf_file(request, patient_id):
    """Download Patient Summary as PDF file (force download, not preview)"""

    logger.info(f"PDF file download requested for patient {patient_id}")

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for PDF file download: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
                logger.info(
                    f"Found patient_data: {patient_data.given_name} {patient_data.family_name}"
                )
            except PatientData.DoesNotExist:
                logger.error(f"Patient data not found for ID: {patient_id}")
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        logger.info(f"Match data exists: {match_data is not None}")

        if not match_data:
            logger.error("No match_data found in session")
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # First, try to extract embedded PDF from CDA content (like your Flask app)
        logger.info("Attempting to extract embedded PDF from CDA content")

        # Check all available CDA content sources
        cda_sources = [
            ("L1", match_data.get("l1_cda_content")),
            ("L3", match_data.get("l3_cda_content")),
            ("original", match_data.get("cda_content")),
        ]

        for source_type, cda_content in cda_sources:
            if cda_content:
                logger.info(f"Checking {source_type} CDA content for embedded PDF")

                # Look for base64 PDF content (similar to your Flask app)
                import base64

                # Convert to bytes if it's a string
                if isinstance(cda_content, str):
                    cda_bytes = cda_content.encode("utf-8")
                else:
                    cda_bytes = cda_content

                # Look for base64 PDF patterns
                pdf_patterns = [
                    b'<text mediaType="application/pdf" representation="B64">',
                    b'<text mediatype="application/pdf" representation="B64">',
                    b'mediaType="application/pdf"',
                    b'mediatype="application/pdf"',
                ]

                for pattern in pdf_patterns:
                    start_index = cda_bytes.find(pattern)
                    if start_index != -1:
                        logger.info(
                            f"Found PDF pattern in {source_type} CDA: {pattern.decode('utf-8', errors='ignore')}"
                        )

                        # Find the content between tags
                        tag_end = cda_bytes.find(b">", start_index) + 1
                        end_tag = cda_bytes.find(b"</text>", tag_end)

                        if end_tag != -1:
                            # Extract base64 content
                            base64_content = cda_bytes[tag_end:end_tag].strip()

                            try:
                                # Decode base64 to get PDF bytes
                                pdf_bytes = base64.b64decode(base64_content)

                                # Verify it's a valid PDF
                                if pdf_bytes.startswith(b"%PDF"):
                                    logger.info(
                                        f"Successfully extracted PDF from {source_type} CDA. Size: {len(pdf_bytes)} bytes"
                                    )

                                    # Create filename
                                    filename = f"{patient_data.given_name}_{patient_data.family_name}_Patient_Summary.pdf"

                                    # Return PDF response for download (with attachment)
                                    response = HttpResponse(
                                        pdf_bytes, content_type="application/pdf"
                                    )
                                    response["Content-Disposition"] = (
                                        f'attachment; filename="{filename}"'
                                    )

                                    logger.info(
                                        f"Generated patient summary PDF file download for patient {patient_id}"
                                    )
                                    return response

                            except Exception as e:
                                logger.warning(
                                    f"Failed to decode base64 PDF from {source_type}: {e}"
                                )
                                continue

        logger.info(
            "No embedded PDF found, falling back to HTML->PDF generation for file download"
        )

        # Fallback: Generate PDF from HTML content for download
        return generate_pdf_file_from_html(
            request, patient_id, patient_data, match_data
        )

    except Exception as e:
        logger.error(f"Unexpected error in download_patient_summary_pdf_file: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating PDF document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def generate_pdf_file_from_html(request, patient_id, patient_data, match_data):
    """Generate PDF file (for download) from HTML content using xhtml2pdf"""

    logger.info("Generating PDF file from HTML content using xhtml2pdf")

    try:
        # Get patient summary using the same logic as the preview function
        search_service = EUPatientSearchService()

        # Reconstruct match object for summary
        from dataclasses import dataclass
        from typing import Dict

        @dataclass
        class SimplePatientResult:
            """Simple patient result for views"""

            file_path: str
            country_code: str
            confidence_score: float
            patient_data: Dict
            cda_content: str

        # Extract required fields from patient_data or use defaults
        patient_info = match_data.get("patient_data", {})

        match = SimplePatientResult(
            file_path=match_data["file_path"],
            country_code=match_data["country_code"],
            confidence_score=match_data["confidence_score"],
            patient_data=match_data["patient_data"],
            cda_content=match_data["cda_content"],
        )

        patient_summary = search_service.get_patient_summary(match)

        logger.info(f"Patient summary retrieved: {patient_summary is not None}")
        if patient_summary:
            logger.info(
                f"Patient summary keys: {list(patient_summary.keys()) if isinstance(patient_summary, dict) else type(patient_summary)}"
            )

        if not patient_summary:
            logger.error("No patient summary content available")
            # Create a basic summary from available data
            patient_summary = {
                "patient_name": f"{patient_data.given_name} {patient_data.family_name}",
                "birth_date": (
                    str(patient_data.birth_date)
                    if patient_data.birth_date
                    else "Not specified"
                ),
                "gender": patient_data.gender or "Not specified",
                "primary_patient_id": patient_info.get(
                    "primary_patient_id", "Not specified"
                ),
                "secondary_patient_id": patient_info.get("secondary_patient_id", ""),
                "cda_content": match_data.get("cda_content", ""),
            }

        # Get the CDA content from patient summary
        cda_content = patient_summary.get("cda_content", "")

        # If we have L3 content (HTML), prefer that
        l3_cda_content = match_data.get("l3_cda_content")
        if l3_cda_content:
            cda_content = l3_cda_content

        # Clean up and structure the content for PDF
        sections_html = ""
        if cda_content:
            # Clean up the CDA content for better PDF display
            import re
            from html import unescape

            # Remove XML declaration and root elements if present
            clean_content = re.sub(r"<\?xml[^>]*\?>", "", cda_content)
            clean_content = re.sub(r"<ClinicalDocument[^>]*>", "", clean_content)
            clean_content = re.sub(r"</ClinicalDocument>", "", clean_content)
            clean_content = re.sub(r"<component[^>]*>", "", clean_content)
            clean_content = re.sub(r"</component>", "", clean_content)
            clean_content = re.sub(r"<structuredBody[^>]*>", "", clean_content)
            clean_content = re.sub(r"</structuredBody>", "", clean_content)

            # Unescape HTML entities
            clean_content = unescape(clean_content)

            # If it's mostly tables and structured content, use it as-is
            sections_html = f"""
            <div class="section">
                <h2>Patient Summary Content</h2>
                <div class="content">
                    {clean_content}
                </div>
            </div>
            """
        else:
            sections_html = """
            <div class="section">
                <p>No detailed patient summary content available.</p>
            </div>
            """

        # Prepare HTML content with proper structure and inline CSS
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Patient Summary - {patient_data.given_name} {patient_data.family_name}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}

                body {{
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    line-height: 1.4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }}

                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                }}

                h1 {{ font-size: 16pt; }}
                h2 {{ font-size: 14pt; }}
                h3 {{ font-size: 12pt; }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 1em 0;
                }}

                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }}

                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                    color: #2c3e50;
                }}

                .patient-header {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}

                .section {{
                    margin-bottom: 20px;
                }}

                ul {{
                    padding-left: 20px;
                }}

                li {{
                    margin-bottom: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="patient-header">
                <h1>Patient Summary</h1>
                <p><strong>Patient:</strong> {patient_summary.get('patient_name', 'Unknown')}</p>
                <p><strong>Date of Birth:</strong> {patient_summary.get('birth_date', 'Not specified')}</p>
                <p><strong>Gender:</strong> {patient_summary.get('gender', 'Not specified')}</p>
                <p><strong>Primary Patient ID:</strong> {patient_summary.get('primary_patient_id', 'Not specified')}</p>
                {f'<p><strong>Secondary Patient ID:</strong> {patient_summary.get("secondary_patient_id")}</p>' if patient_summary.get('secondary_patient_id') else ''}
                <p><strong>Generated:</strong> {timezone.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>

            <div class="content">
                {sections_html}
            </div>
        </body>
        </html>
        """

        # Generate PDF using xhtml2pdf
        logger.info("Starting PDF file generation with xhtml2pdf")
        logger.info(f"HTML content length: {len(html_content)} characters")

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)

        logger.info(f"PDF file generation completed. Errors: {pdf.err}")

        if not pdf.err:
            pdf_bytes = result.getvalue()
            result.close()

            logger.info(
                f"PDF file generated successfully. Size: {len(pdf_bytes)} bytes"
            )

            # Create filename
            filename = f"{patient_data.given_name}_{patient_data.family_name}_Patient_Summary.pdf"

            # Return PDF response for download (with attachment)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            logger.info(
                f"Generated patient summary PDF file download for patient {patient_id}"
            )
            return response
        else:
            logger.error(f"Error generating PDF file: {pdf.err}")
            messages.error(request, "Error generating PDF document.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

    except Exception as e:
        logger.error(f"Error in generate_pdf_file_from_html: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        messages.error(request, "Error generating PDF document.")
        return redirect("patient_data:patient_details", patient_id=patient_id)


def patient_orcd_view(request, patient_id):
    """View for displaying ORCD (Original Clinical Document) PDF preview"""

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD display: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Initialize PDF service
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD, we prefer L1 CDA as it typically contains the embedded PDF
        # Fall back to L3 CDA if L1 is not available
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")

        # Try L1 first for ORCD extraction
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        pdf_attachments = []
        orcd_available = False

        if orcd_cda_content:
            try:
                logger.info(
                    f"Attempting ORCD PDF extraction from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
                )
                pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)
                orcd_available = len(pdf_attachments) > 0
                logger.info(
                    f"ORCD extraction from {cda_type_used} CDA: {len(pdf_attachments)} PDFs found"
                )

                # Log more details about the extracted PDFs
                for i, pdf_info in enumerate(pdf_attachments):
                    logger.info(
                        f"PDF {i}: {pdf_info['filename']} ({pdf_info['size']} bytes, media_type: {pdf_info.get('media_type', 'unknown')})"
                    )

            except Exception as e:
                logger.error(f"Error extracting PDFs from {cda_type_used} CDA: {e}")
                import traceback

                logger.error(traceback.format_exc())

        context = {
            "patient_data": patient_data,
            "source_country": match_data["country_code"],
            "confidence": round(match_data["confidence_score"] * 100, 1),
            "file_name": os.path.basename(
                match_data.get("l1_cda_path") or match_data.get("file_path", "")
            ),
            "orcd_available": orcd_available,
            "pdf_attachments": pdf_attachments,
            "cda_type_used": cda_type_used,
            "l1_available": bool(l1_cda_content),
            "l3_available": bool(l3_cda_content),
        }

        return render(request, "patient_data/patient_orcd.html", context)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def download_orcd_pdf(request, patient_id, attachment_index=0):
    """Download ORCD PDF attachment"""

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD download: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                messages.error(request, "Patient data not found.")
                return redirect("patient_data:patient_data_form")

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        if not match_data:
            messages.error(request, "No CDA document found for this patient.")
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD download, prefer L1 CDA
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        if not orcd_cda_content:
            messages.error(request, "No CDA content available.")
            return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

        try:
            logger.info(
                f"Attempting ORCD PDF download from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
            )
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                messages.error(
                    request, f"PDF attachment not found in {cda_type_used} CDA."
                )
                return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

            # Get the requested PDF attachment
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]
            filename = f"{patient_data.given_name}_{patient_data.family_name}_ORCD_{cda_type_used}.pdf"

            logger.info(
                f"Downloaded ORCD PDF from {cda_type_used} CDA for patient {patient_id} ({len(pdf_data)} bytes)"
            )

            # Return PDF response
            return pdf_service.get_pdf_response(
                pdf_data, filename, disposition="attachment"
            )

        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            import traceback

            logger.error(traceback.format_exc())
            messages.error(request, "Error extracting PDF from document.")
            return redirect("patient_data:patient_orcd_view", patient_id=patient_id)

    except PatientData.DoesNotExist:
        messages.error(request, "Patient data not found.")
        return redirect("patient_data:patient_data_form")


def view_orcd_pdf(request, patient_id, attachment_index=0):
    """View ORCD PDF inline for fullscreen preview"""

    try:
        # Check if this is an NCP query result (session data exists but no DB record)
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if match_data and not PatientData.objects.filter(id=patient_id).exists():
            # This is an NCP query result - create temp patient from session data
            patient_info = match_data["patient_data"]

            # Create a temporary patient object (not saved to DB)
            patient_data = PatientData(
                id=patient_id,
                given_name=patient_info.get("given_name", "Unknown"),
                family_name=patient_info.get("family_name", "Patient"),
                birth_date=patient_info.get("birth_date") or None,
                gender=patient_info.get("gender", ""),
            )

            logger.info(
                f"Created temporary patient object for ORCD inline view: {patient_id}"
            )
        else:
            # Standard database lookup
            try:
                patient_data = PatientData.objects.get(id=patient_id)
            except PatientData.DoesNotExist:
                return HttpResponse(
                    "<html><body><h1>Patient not found</h1><p>Please return to the patient data form.</p></body></html>",
                    status=404,
                )

            # Get CDA match from session for database patients
            if not match_data:
                match_data = request.session.get(session_key)

        if not match_data:
            return HttpResponse(
                "<html><body><h1>No CDA document found</h1><p>Please return to the patient details page.</p></body></html>",
                status=404,
            )

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()

        # For ORCD viewing, prefer L1 CDA
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )
        cda_type_used = (
            "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
        )

        if not orcd_cda_content:
            return HttpResponse(
                "<html><body><h1>No CDA content available</h1><p>No document content could be retrieved.</p></body></html>",
                status=404,
            )

        try:
            logger.info(
                f"Attempting ORCD PDF inline viewing from {cda_type_used} CDA (content length: {len(orcd_cda_content)})"
            )
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                return HttpResponse(
                    f"<html><body><h1>PDF not found</h1><p>PDF attachment not found in {cda_type_used} CDA.</p></body></html>",
                    status=404,
                )

            # Get the requested PDF attachment
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]
            filename = f"{patient_data.given_name}_{patient_data.family_name}_ORCD_{cda_type_used}.pdf"

            logger.info(
                f"Viewing ORCD PDF inline from {cda_type_used} CDA for patient {patient_id} ({len(pdf_data)} bytes)"
            )

            # Return PDF response for inline viewing with enhanced headers
            response = pdf_service.get_pdf_response(
                pdf_data, filename, disposition="inline"
            )

            # Add headers to help with PDF display
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "SAMEORIGIN"

            return response

        except Exception as e:
            logger.error(f"Error viewing PDF: {e}")
            return HttpResponse(
                f"<html><body><h1>Error loading PDF</h1><p>Error extracting PDF from document: {e}</p></body></html>",
                status=500,
            )

    except PatientData.DoesNotExist:
        return HttpResponse(
            "<html><body><h1>Patient not found</h1><p>Patient data not found.</p></body></html>",
            status=404,
        )


def debug_orcd_pdf(request, patient_id):
    """Debug ORCD PDF extraction and display"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        debug_info = []
        debug_info.append(f"<h2>PDF Debug Information for Patient {patient_id}</h2>")
        debug_info.append(
            f"<p><strong>Patient:</strong> {patient_data.given_name} {patient_data.family_name}</p>"
        )

        if not match_data:
            debug_info.append(
                "<p><strong>Error:</strong> No CDA document found in session</p>"
            )
        else:
            debug_info.append("<p><strong>Session data found:</strong> ✓</p>")

            # Check CDA content
            l1_cda_content = match_data.get("l1_cda_content")
            l3_cda_content = match_data.get("l3_cda_content")
            debug_info.append(
                f"<p><strong>L1 CDA Available:</strong> {'✓' if l1_cda_content else '✗'}</p>"
            )
            debug_info.append(
                f"<p><strong>L3 CDA Available:</strong> {'✓' if l3_cda_content else '✗'}</p>"
            )

            if l1_cda_content:
                debug_info.append(
                    f"<p><strong>L1 CDA Length:</strong> {len(l1_cda_content)} characters</p>"
                )
            if l3_cda_content:
                debug_info.append(
                    f"<p><strong>L3 CDA Length:</strong> {len(l3_cda_content)} characters</p>"
                )

            # Test PDF extraction
            pdf_service = ClinicalDocumentPDFService()
            orcd_cda_content = l1_cda_content or l3_cda_content or ""
            cda_type_used = (
                "L1" if l1_cda_content else ("L3" if l3_cda_content else "Unknown")
            )

            if orcd_cda_content:
                try:
                    pdf_attachments = pdf_service.extract_pdfs_from_xml(
                        orcd_cda_content
                    )
                    debug_info.append(
                        f"<p><strong>PDF Attachments Found:</strong> {len(pdf_attachments)}</p>"
                    )
                    debug_info.append(
                        f"<p><strong>CDA Type Used:</strong> {cda_type_used}</p>"
                    )

                    for i, pdf in enumerate(pdf_attachments):
                        debug_info.append(f"<p><strong>PDF {i + 1}:</strong></p>")
                        debug_info.append(f"<ul>")
                        debug_info.append(f"  <li>Size: {pdf['size']} bytes</li>")
                        debug_info.append(f"  <li>Filename: {pdf['filename']}</li>")
                        debug_info.append(
                            f"  <li>Valid PDF header: {'✓' if pdf['data'].startswith(b'%PDF') else '✗'}</li>"
                        )
                        debug_info.append(
                            f"  <li>First 100 bytes: {pdf['data'][:100]}</li>"
                        )
                        debug_info.append(f"</ul>")

                        # Create download link for this PDF
                        debug_info.append(
                            f"<p><a href='/patients/orcd/{patient_id}/download/{i}/' target='_blank'>Download PDF {i + 1}</a></p>"
                        )
                        debug_info.append(
                            f"<p><a href='/patients/orcd/{patient_id}/view/' target='_blank'>View PDF {i + 1} Inline</a></p>"
                        )

                except Exception as e:
                    debug_info.append(
                        f"<p><strong>PDF Extraction Error:</strong> {str(e)}</p>"
                    )
            else:
                debug_info.append(
                    "<p><strong>Error:</strong> No CDA content available</p>"
                )

        debug_info.append("<hr>")
        debug_info.append(
            f"<p><a href='/patients/{patient_id}/details/'>← Back to Patient Details</a></p>"
        )
        debug_info.append(
            f"<p><a href='/patients/{patient_id}/orcd/'>← Back to ORCD Viewer</a></p>"
        )

        html_content = f"""
        <html>
        <head>
            <title>ORCD PDF Debug - {patient_data.given_name} {patient_data.family_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h2 {{ color: #2c3e50; }}
                p {{ margin: 10px 0; }}
                ul {{ margin: 10px 0; }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            {''.join(debug_info)}
        </body>
        </html>
        """

        return HttpResponse(html_content)

    except PatientData.DoesNotExist:
        return HttpResponse(
            "<html><body><h1>Patient not found</h1><p>Patient data not found.</p></body></html>",
            status=404,
        )
    except Exception as e:
        return HttpResponse(
            f"<html><body><h1>Debug Error</h1><p>Error during debug: {str(e)}</p></body></html>",
            status=500,
        )


def orcd_pdf_base64(request, patient_id, attachment_index=0):
    """Return ORCD PDF as base64 data URL for direct embedding"""

    try:
        patient_data = PatientData.objects.get(id=patient_id)
        match_data = request.session.get(f"patient_match_{patient_id}")

        if not match_data:
            return HttpResponse("No CDA document found", status=404)

        # Initialize PDF service and extract PDFs
        pdf_service = ClinicalDocumentPDFService()
        l1_cda_content = match_data.get("l1_cda_content")
        l3_cda_content = match_data.get("l3_cda_content")
        orcd_cda_content = (
            l1_cda_content or l3_cda_content or match_data.get("cda_content", "")
        )

        if not orcd_cda_content:
            return HttpResponse("No CDA content available", status=404)

        try:
            pdf_attachments = pdf_service.extract_pdfs_from_xml(orcd_cda_content)

            if not pdf_attachments or attachment_index >= len(pdf_attachments):
                return HttpResponse("PDF attachment not found", status=404)

            # Get the PDF data
            pdf_attachment = pdf_attachments[attachment_index]
            pdf_data = pdf_attachment["data"]

            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

            # Create HTML page with embedded PDF using data URL
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>ORCD PDF - {patient_data.given_name} {patient_data.family_name}</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 20px;
                        font-family: Arial, sans-serif;
                        background: #f5f5f5;
                    }}
                    .pdf-container {{
                        background: white;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .pdf-header {{
                        margin-bottom: 20px;
                        padding-bottom: 15px;
                        border-bottom: 1px solid #eee;
                    }}
                    .pdf-viewer {{
                        width: 100%;
                        height: 800px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                    }}
                    .fallback {{
                        text-align: center;
                        padding: 40px;
                        background: #f8f9fa;
                        border-radius: 4px;
                        border: 2px dashed #dee2e6;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 8px 16px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 5px;
                    }}
                    .btn:hover {{
                        background: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="pdf-container">
                    <div class="pdf-header">
                        <h2>ORCD PDF Document</h2>
                        <p><strong>Patient:</strong> {patient_data.given_name} {patient_data.family_name}</p>
                        <p><strong>Document Size:</strong> {len(pdf_data):,} bytes</p>
                        <a href="javascript:history.back()" class="btn">← Back</a>
                        <a href="/patients/orcd/{patient_id}/download/" class="btn">Download PDF</a>
                    </div>

                    <!-- Primary: Object with data URL -->
                    <object
                        class="pdf-viewer"
                        data="data:application/pdf;base64,{pdf_base64}"
                        type="application/pdf">

                        <!-- Fallback: Embed with data URL -->
                        <embed
                            src="data:application/pdf;base64,{pdf_base64}"
                            type="application/pdf"
                            width="100%"
                            height="800px" />

                        <!-- Final fallback -->
                        <div class="fallback">
                            <h3>PDF Preview Not Available</h3>
                            <p>Your browser doesn't support inline PDF viewing.</p>
                            <a href="/patients/orcd/{patient_id}/download/" class="btn">Download PDF Instead</a>
                        </div>
                    </object>
                </div>

                <script>
                    // Try to detect if PDF loaded successfully
                    setTimeout(function() {{
                        console.log('PDF data URL length: {len(pdf_base64)} characters');
                        console.log('PDF starts with valid header: {str(pdf_data.startswith(b"%PDF")).lower()}');
                    }}, 1000);
                </script>
            </body>
            </html>
            """

            return HttpResponse(html_content)

        except Exception as e:
            logger.error(f"Error creating base64 PDF: {e}")
            return HttpResponse(f"Error processing PDF: {str(e)}", status=500)

    except PatientData.DoesNotExist:
        return HttpResponse("Patient not found", status=404)


# ========================================
# Legacy Views (Minimal Implementation)
# ========================================


@login_required
def patient_search_view(request):
    """Legacy patient search view - redirect to new form"""
    return redirect("patient_data:patient_data_form")


@login_required
def patient_search_results(request):
    """Legacy patient search results view"""
    return render(
        request,
        "patient_data/search_results.html",
        {"message": "Please use the new patient search form."},
    )


def generate_dynamic_ps_sections(sections):
    """
    Generate dynamic PS Display Guidelines sections with enhanced table rendering

    This function creates structured sections that combine:
    - Original language content
    - Code-based translations
    - PS Guidelines compliant tables
    - Interactive comparison views
    """

    enhanced_sections = []

    for section in sections:
        # Create base enhanced section
        enhanced_section = section.copy()

        # Generate dynamic subsections based on content type
        subsections = []

        # 1. Original Content Subsection
        if section.get("content", {}).get("original"):
            subsections.append(
                {
                    "type": "original_content",
                    "title": f"Original Content ({section.get('source_language', 'fr').upper()})",
                    "icon": "fas fa-flag",
                    "content": section["content"]["original"],
                    "priority": 1,
                }
            )

        # 2. PS Guidelines Table Subsection (Priority!)
        if section.get("ps_table_html"):
            # Determine section type for better labeling
            section_code = section.get("section_code", "")
            section_type_names = {
                "10160-0": "Medication History",
                "48765-2": "Allergies & Adverse Reactions",
                "11450-4": "Problem List",
                "47519-4": "Procedures History",
                "30954-2": "Laboratory Results",
                "10157-6": "Immunization History",
                "18776-5": "Treatment Plan",
            }

            ps_section_name = section_type_names.get(
                section_code, "Clinical Information"
            )

            subsections.append(
                {
                    "type": "ps_guidelines_table",
                    "title": f"PS Guidelines Standardized Table - {ps_section_name}",
                    "icon": "fas fa-table",
                    "content": section["ps_table_html"],
                    "section_code": section_code,
                    "priority": 0,  # Highest priority
                    "compliance_note": "This table follows EU Patient Summary Display Guidelines for interoperability",
                }
            )

        # 3. Code-based Translation Subsection
        if section.get("is_coded_section") and section.get("title", {}).get("coded"):
            subsections.append(
                {
                    "type": "coded_translation",
                    "title": "Code-based Medical Translation",
                    "icon": "fas fa-code",
                    "content": section["content"].get("translated", ""),
                    "coded_title": section["title"]["coded"],
                    "section_code": section.get("section_code", ""),
                    "priority": 2,
                }
            )

        # 4. Free-text Translation Subsection
        elif section.get("content", {}).get("translated"):
            subsections.append(
                {
                    "type": "free_text_translation",
                    "title": "Free-text Translation",
                    "icon": "fas fa-language",
                    "content": section["content"]["translated"],
                    "priority": 3,
                }
            )

        # 5. Original Tables Comparison (if different from PS Guidelines)
        if section.get("original_tables") and section.get("ps_table_html"):
            subsections.append(
                {
                    "type": "original_tables",
                    "title": "Original Document Tables (Comparison)",
                    "icon": "fas fa-table",
                    "content": section["original_tables"],
                    "priority": 4,
                    "note": "These are the original tables as they appeared in the source document",
                }
            )

        # Sort subsections by priority (PS Guidelines tables first)
        subsections.sort(key=lambda x: x.get("priority", 99))

        # Add subsections to enhanced section
        enhanced_section["subsections"] = subsections
        enhanced_section["has_subsections"] = len(subsections) > 0
        enhanced_section["subsection_count"] = len(subsections)

        # Add section-level metadata for better organization
        enhanced_section["section_metadata"] = {
            "has_ps_table": bool(section.get("ps_table_html")),
            "has_coded_translation": section.get("is_coded_section", False),
            "has_original_content": bool(section.get("content", {}).get("original")),
            "clinical_importance": _get_clinical_importance(
                section.get("section_code", "")
            ),
            "display_priority": _get_display_priority(section.get("section_code", "")),
        }

        enhanced_sections.append(enhanced_section)

    # Sort sections by clinical importance (medications, allergies, problems first)
    enhanced_sections.sort(key=lambda x: x["section_metadata"]["display_priority"])

    return enhanced_sections


def _get_clinical_importance(section_code):
    """Determine clinical importance level for section ordering"""
    high_importance_codes = [
        "10160-0",
        "48765-2",
        "11450-4",
    ]  # Medications, Allergies, Problems
    medium_importance_codes = [
        "47519-4",
        "30954-2",
        "10157-6",
    ]  # Procedures, Labs, Immunizations

    if section_code in high_importance_codes:
        return "high"
    elif section_code in medium_importance_codes:
        return "medium"
    else:
        return "low"


def _get_display_priority(section_code):
    """Get numeric display priority (lower = displayed first)"""
    priority_map = {
        "10160-0": 1,  # Medication History (most critical)
        "48765-2": 2,  # Allergies (safety critical)
        "11450-4": 3,  # Problems/Conditions
        "47519-4": 4,  # Procedures
        "30954-2": 5,  # Laboratory Results
        "10157-6": 6,  # Immunizations
        "18776-5": 7,  # Treatment Plan
    }
    return priority_map.get(section_code, 99)  # Unknown sections go last


def enhanced_cda_display(request):
    """
    Enhanced CDA Display endpoint for multi-European language processing
    Handles both GET (render template) and POST (AJAX processing) requests
    """

    import json

    from .services.enhanced_cda_processor import EnhancedCDAProcessor
    from .translation_utils import detect_document_language
    from .ui_labels import get_ui_labels

    if request.method == "POST":
        try:
            # AJAX request for CDA processing
            cda_content = request.POST.get("cda_content", "")
            source_language = request.POST.get("source_language", "")
            target_language = request.POST.get("target_language", "en")
            country_code = request.POST.get("country_code", "").upper()

            if not cda_content.strip():
                return JsonResponse(
                    {"success": False, "error": "No CDA content provided"}
                )

            # Enhanced multi-European language detection
            detected_source_language = None

            # Method 1: Use provided source_language if valid
            supported_languages = [
                "de",
                "it",
                "es",
                "pt",
                "lv",
                "lt",
                "et",
                "en",
                "fr",
                "nl",
                "el",
                "mt",
                "cs",
                "sk",
                "hu",
                "sl",
                "hr",
                "ro",
                "bg",
                "da",
                "fi",
                "sv",
                "pl",
            ]

            if source_language and source_language in supported_languages:
                detected_source_language = source_language
                logger.info(f"Using provided source language: {source_language}")

            # Method 2: Derive from country code if provided
            elif country_code:
                country_language_map = {
                    # Western Europe
                    "BE": "nl",  # Belgium (Dutch/Flemish primary, French secondary)
                    "DE": "de",  # Germany
                    "FR": "fr",  # France
                    "IE": "en",  # Ireland (English)
                    "LU": "fr",  # Luxembourg (French primary, German/Luxembourgish secondary)
                    "NL": "nl",  # Netherlands
                    "AT": "de",  # Austria (German)
                    # Southern Europe
                    "ES": "es",  # Spain
                    "IT": "it",  # Italy
                    "PT": "pt",  # Portugal
                    "GR": "el",  # Greece (Greek)
                    "CY": "el",  # Cyprus (Greek primary, Turkish secondary)
                    "MT": "en",  # Malta (English and Maltese)
                    # Central/Eastern Europe
                    "PL": "pl",  # Poland
                    "CZ": "cs",  # Czech Republic (Czech)
                    "SK": "sk",  # Slovakia (Slovak)
                    "HU": "hu",  # Hungary (Hungarian)
                    "SI": "sl",  # Slovenia (Slovenian)
                    "HR": "hr",  # Croatia (Croatian)
                    "RO": "ro",  # Romania (Romanian)
                    "BG": "bg",  # Bulgaria (Bulgarian)
                    # Baltic States
                    "LT": "lt",  # Lithuania (Lithuanian)
                    "LV": "lv",  # Latvia (Latvian)
                    "EE": "et",  # Estonia (Estonian)
                    # Nordic Countries
                    "DK": "da",  # Denmark (Danish)
                    "FI": "fi",  # Finland (Finnish)
                    "SE": "sv",  # Sweden (Swedish)
                    # Special codes
                    "EU": "en",  # European Union documents (English)
                    "CH": "de",  # Switzerland (German primary, but multilingual)
                }

                if country_code in country_language_map:
                    detected_source_language = country_language_map[country_code]
                    logger.info(
                        f"Derived source language from country {country_code}: {detected_source_language}"
                    )

            # Method 3: Auto-detect from CDA content
            if not detected_source_language:
                detected_source_language = detect_document_language(cda_content)
                logger.info(
                    f"Auto-detected source language from content: {detected_source_language}"
                )

            # Method 4: Ultimate fallback to French (for backwards compatibility)
            if not detected_source_language:
                detected_source_language = "fr"
                logger.warning(
                    "Could not detect source language, falling back to French"
                )

            # Initialize Enhanced CDA Processor with JSON Field Mapping
            processor = EnhancedCDAProcessor(target_language=target_language)

            # Process CDA content with comprehensive field mapping
            result = processor.process_clinical_sections(
                cda_content=cda_content, source_language=detected_source_language
            )

            # Apply Malta-specific enhancements if this is a Malta document
            if country_code == "MT" or "malta" in cda_content.lower():
                try:
                    from .services.malta_cda_enhancer import MaltaCDAEnhancer

                    malta_enhancer = MaltaCDAEnhancer()

                    if result.get("success") and result.get("sections"):
                        logger.info("Applying Malta CDA enhancements...")

                        # Enhance sections with Malta-specific processing
                        enhanced_sections = malta_enhancer.enhance_cda_sections(
                            result["sections"], cda_content
                        )

                        # Fix empty clinical sections
                        enhanced_sections = malta_enhancer.fix_empty_clinical_sections(
                            enhanced_sections
                        )

                        result["sections"] = enhanced_sections
                        result["malta_enhanced"] = True

                        logger.info(
                            f"Malta enhancements applied to {len(enhanced_sections)} sections"
                        )

                except Exception as e:
                    logger.error(f"Malta enhancement failed: {e}")
                    # Continue with original result if enhancement fails

            # Add language detection info to result
            result["detected_source_language"] = detected_source_language
            result["language_detection_method"] = (
                "provided"
                if source_language
                else (
                    "country_code"
                    if country_code
                    else (
                        "auto_detected"
                        if detected_source_language != "fr"
                        else "fallback"
                    )
                )
            )

            logger.info(
                f"Enhanced CDA processing result: success={result.get('success')}, "
                f"sections={result.get('sections_count', 0)}, "
                f"source_lang={detected_source_language}, target_lang={target_language}"
            )

            return JsonResponse(result)

        except Exception as e:
            logger.error(f"Error in enhanced CDA display AJAX processing: {e}")
            return JsonResponse({"success": False, "error": str(e)})

    else:
        # GET request - render template with multi-language support info
        supported_languages = {
            "de": "German (Deutschland, Österreich, Schweiz)",
            "it": "Italian (Italia, San Marino, Vaticano)",
            "es": "Spanish (España, Andorra)",
            "pt": "Portuguese (Portugal)",
            "lv": "Latvian (Latvija)",
            "lt": "Lithuanian (Lietuva)",
            "et": "Estonian (Eesti)",
            "en": "English (Malta, Ireland)",
            "fr": "French (France, Luxembourg)",
            "nl": "Dutch (Nederland, België)",
            "el": "Greek (Ελλάδα)",
        }

        context = {
            "page_title": "Enhanced CDA Display Tool",
            "description": "Multi-European Language CDA Document Processor with CTS Compliance",
            "supported_languages": supported_languages,
            "default_target_language": "en",
            "ui_labels": get_ui_labels("en"),  # Add dynamic UI labels
        }

        return render(request, "patient_data/enhanced_cda_display.html", context)


def _create_dual_language_sections(original_result, translated_result, source_language):
    """
    Create dual language sections by combining original and translated processing results

    Args:
        original_result: Processing result with source language content
        translated_result: Processing result with English translation
        source_language: Source language code (pt, fr, de, etc.)

    Returns:
        Combined result with dual language sections
    """
    if not original_result.get("success") or not translated_result.get("success"):
        logger.warning(
            "One or both processing results failed, falling back to single language"
        )
        return (
            translated_result if translated_result.get("success") else original_result
        )

    # Start with the translated result structure
    dual_result = dict(translated_result)

    original_sections = original_result.get("sections", [])
    translated_sections = translated_result.get("sections", [])

    # Create dual language sections
    dual_sections = []

    for i, translated_section in enumerate(translated_sections):
        # Find corresponding original section
        original_section = None
        if i < len(original_sections):
            original_section = original_sections[i]

        # Create dual language section (simplified implementation)
        dual_section = dict(translated_section)
        if original_section:
            dual_section["original"] = original_section

        dual_sections.append(dual_section)

    # Update the result with dual language sections
    dual_result["sections"] = dual_sections

    return dual_result


# Enhanced CDA Document Display View


from django.views import View


def _create_dual_language_sections(original_result, translated_result, source_language):
    """
    Create dual language sections by combining original and translated processing results

    Args:
        original_result: Processing result with source language content
        translated_result: Processing result with English translation
        source_language: Source language code (pt, fr, de, etc.)

    Returns:
        Combined result with dual language sections
    """
    if not original_result.get("success") or not translated_result.get("success"):
        logger.warning(
            "One or both processing results failed, falling back to single language"
        )
        return (
            translated_result if translated_result.get("success") else original_result
        )

    # Start with the translated result structure
    dual_result = dict(translated_result)

    original_sections = original_result.get("sections", [])
    translated_sections = translated_result.get("sections", [])

    # Create dual language sections
    dual_sections = []

    for i, translated_section in enumerate(translated_sections):
        # Find corresponding original section
        original_section = None
        if i < len(original_sections):
            original_section = original_sections[i]

        # Create dual language section
        dual_section = dict(translated_section)

        # Preserve original content structure while adding dual language content
        original_content = (
            original_section.get("content", "") if original_section else ""
        )
        translated_content = translated_section.get("content", "")

        # Handle content that might be a dict (with medical_terms) or string
        if isinstance(translated_content, dict):
            # Keep all the metadata from translated content
            dual_section["content"] = dict(translated_content)
            dual_section["content"]["translated"] = translated_content.get(
                "content", str(translated_content)
            )
            dual_section["content"]["original"] = (
                original_content.get("content", str(original_content))
                if isinstance(original_content, dict)
                else str(original_content)
            )
        else:
            # Simple string content
            dual_section["content"] = {
                "translated": str(translated_content),
                "original": str(original_content),
                "medical_terms": 0,  # Default for compatibility
            }

        # Add source language info
        dual_section["source_language"] = source_language
        dual_section["has_dual_language"] = True

        # Handle PS table content for both languages if available
        if translated_section.get("has_ps_table"):
            dual_section["ps_table_html"] = translated_section.get("ps_table_html", "")
            if original_section and original_section.get("has_ps_table"):
                dual_section["ps_table_html_original"] = original_section.get(
                    "ps_table_html", ""
                )
            else:
                dual_section["ps_table_html_original"] = ""

        dual_sections.append(dual_section)

    # Update the result with dual language sections
    dual_result["sections"] = dual_sections
    dual_result["dual_language_active"] = True
    dual_result["source_language"] = source_language

    # Ensure medical_terms_count is preserved for template compatibility
    if "medical_terms_count" not in dual_result:
        dual_result["medical_terms_count"] = translated_result.get(
            "medical_terms_count", 0
        )

    logger.info(
        f"Created {len(dual_sections)} dual language sections ({source_language} | en)"
    )

    return dual_result


@require_http_methods(["POST"])
def upload_cda_document(request):
    """Handle CDA document upload and processing"""
    import uuid
    from pathlib import Path

    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    from .services.enhanced_cda_processor import EnhancedCDAProcessor

    try:
        if "cda_file" not in request.FILES:
            messages.error(request, "No file was uploaded. Please select a CDA file.")
            return redirect("patient_data:patient_search_enhanced")

        uploaded_file = request.FILES["cda_file"]
        auto_process = request.POST.get("auto_process") == "on"

        # Validate file type
        if not uploaded_file.name.lower().endswith((".xml", ".cda")):
            messages.error(
                request, "Invalid file type. Please upload an XML or CDA file."
            )
            return redirect("patient_data:patient_search_enhanced")

        # Generate unique filename
        file_extension = Path(uploaded_file.name).suffix
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"

        # Save file to uploads directory
        uploads_dir = Path(settings.BASE_DIR) / "media" / "uploads" / "cda_documents"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        file_path = uploads_dir / unique_filename

        # Save the uploaded file
        with open(file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        logger.info(f"CDA file uploaded: {uploaded_file.name} -> {unique_filename}")

        if auto_process:
            try:
                # Process the CDA document
                processor = EnhancedCDAProcessor()
                result = processor.process_cda_file(str(file_path))

                if result and "patient_info" in result:
                    patient_info = result["patient_info"]
                    patient_name = f"{patient_info.get('given_name', '')} {patient_info.get('family_name', '')}".strip()
                    patient_id = patient_info.get("patient_id", "Unknown")

                    # Store in session for search results
                    if "uploaded_cda_documents" not in request.session:
                        request.session["uploaded_cda_documents"] = []

                    document_info = {
                        "original_filename": uploaded_file.name,
                        "stored_filename": unique_filename,
                        "file_path": str(file_path),
                        "patient_name": patient_name,
                        "patient_id": patient_id,
                        "upload_date": timezone.now().isoformat(),
                        "processed": True,
                        "processing_result": result,
                    }

                    request.session["uploaded_cda_documents"].append(document_info)
                    request.session.modified = True

                    messages.success(
                        request,
                        f"Document '{uploaded_file.name}' uploaded and processed successfully. "
                        f"Patient: {patient_name} (ID: {patient_id})",
                    )

                    # Redirect to search results showing the uploaded document
                    return redirect("patient_data:uploaded_documents")

                else:
                    messages.warning(
                        request,
                        f"Document '{uploaded_file.name}' was uploaded but could not be processed. "
                        "The file may not contain valid patient data.",
                    )

            except Exception as e:
                logger.error(f"Error processing uploaded CDA document: {str(e)}")
                messages.error(
                    request,
                    f"Document '{uploaded_file.name}' was uploaded but processing failed: {str(e)}",
                )
        else:
            # Just store file info without processing
            if "uploaded_cda_documents" not in request.session:
                request.session["uploaded_cda_documents"] = []

            document_info = {
                "original_filename": uploaded_file.name,
                "stored_filename": unique_filename,
                "file_path": str(file_path),
                "upload_date": timezone.now().isoformat(),
                "processed": False,
            }

            request.session["uploaded_cda_documents"].append(document_info)
            request.session.modified = True

            messages.success(
                request,
                f"Document '{uploaded_file.name}' uploaded successfully. "
                "Use the process button to extract patient information.",
            )

        return redirect("patient_data:patient_search_enhanced")

    except Exception as e:
        logger.error(f"Error uploading CDA document: {str(e)}")
        messages.error(request, f"Upload failed: {str(e)}")
        return redirect("patient_data:patient_search_enhanced")


def uploaded_documents_view(request):
    """Display uploaded CDA documents"""
    uploaded_docs = request.session.get("uploaded_cda_documents", [])

    context = {
        "uploaded_documents": uploaded_docs,
        "total_documents": len(uploaded_docs),
    }

    return render(request, "patient_data/uploaded_documents.html", context)


def process_uploaded_document(request, doc_index):
    """Process a specific uploaded document"""
    try:
        uploaded_docs = request.session.get("uploaded_cda_documents", [])

        if doc_index >= len(uploaded_docs):
            messages.error(request, "Document not found.")
            return redirect("patient_data:uploaded_documents")

        document_info = uploaded_docs[doc_index]

        if document_info.get("processed"):
            messages.info(request, "Document has already been processed.")
            return redirect("patient_data:uploaded_documents")

        from .services.enhanced_cda_processor import EnhancedCDAProcessor

        processor = EnhancedCDAProcessor()
        result = processor.process_cda_file(document_info["file_path"])

        if result and "patient_info" in result:
            patient_info = result["patient_info"]
            patient_name = f"{patient_info.get('given_name', '')} {patient_info.get('family_name', '')}".strip()
            patient_id = patient_info.get("patient_id", "Unknown")

            # Update document info
            document_info.update(
                {
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "processed": True,
                    "processing_result": result,
                }
            )

            request.session["uploaded_cda_documents"] = uploaded_docs
            request.session.modified = True

            messages.success(
                request,
                f"Document processed successfully. Patient: {patient_name} (ID: {patient_id})",
            )
        else:
            messages.error(
                request,
                "Failed to process document. The file may not contain valid patient data.",
            )

        return redirect("patient_data:uploaded_documents")

    except Exception as e:
        logger.error(f"Error processing uploaded document: {str(e)}")
        messages.error(request, f"Processing failed: {str(e)}")
        return redirect("patient_data:uploaded_documents")


def view_uploaded_document(request, doc_index):
    """View details of an uploaded CDA document"""
    try:
        uploaded_docs = request.session.get("uploaded_cda_documents", [])

        if doc_index >= len(uploaded_docs):
            messages.error(request, "Document not found.")
            return redirect("patient_data:uploaded_documents")

        document_info = uploaded_docs[doc_index]

        if not document_info.get("processed"):
            messages.error(request, "Document has not been processed yet.")
            return redirect("patient_data:uploaded_documents")

        processing_result = document_info.get("processing_result")
        if not processing_result:
            messages.error(request, "No processing result available for this document.")
            return redirect("patient_data:uploaded_documents")

        # Create dual language sections if needed (but not for English documents)
        if processing_result.get("sections"):
            # Check if this is already marked as single language (English documents)
            if processing_result.get("is_single_language"):
                logger.info(
                    "Document is single-language (English), skipping dual language processing"
                )
                # Keep processing_result as is for single language display
            else:
                # Use the dual language processor for non-English documents
                dual_result = _create_dual_language_sections(
                    processing_result, processing_result, "en"
                )
                processing_result = dual_result

        context = {
            "document_info": document_info,
            "processing_result": processing_result,
            "patient_info": processing_result.get("patient_info", {}),
            "sections": processing_result.get("sections", []),
            "doc_index": doc_index,
            "is_single_language": processing_result.get("is_single_language", False),
        }

        return render(request, "patient_data/view_uploaded_document.html", context)

    except Exception as e:
        logger.error(f"Error viewing uploaded document: {str(e)}")
        messages.error(request, f"Error loading document: {str(e)}")
        return redirect("patient_data:uploaded_documents")


def generate_medication_table_html_interactive(entries):
    """Generate interactive HTML table for medications with collapsible details"""
    if not entries:
        return "<p>No medication data available.</p>"

    html_content = """
    <table class="clinical-table">
        <thead>
            <tr>
                <th>[MEDICINE] Medication</th>
                <th>📏 Dosage & Strength</th>
                <th>⏰ Frequency</th>
                <th>[DATA] Status</th>
                <th>📅 Start Date</th>
                <th>🔬 Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        medication = entry.get("Medication", "Not specified")
        dosage = entry.get("Dosage & Strength", "Not specified")
        frequency = entry.get("Frequency", "Not specified")
        status = entry.get("Status", "Unknown")
        start_date = entry.get("Start Date", "Not recorded")
        codes = entry.get("Codes", "")

        status_class = (
            "status-active" if status.lower() == "active" else "status-inactive"
        )

        codes_html = ""
        if codes:
            code_list = codes.split(", ") if isinstance(codes, str) else [str(codes)]
            for code in code_list:
                if code.strip():
                    codes_html += f'<span class="medical-code" title="Medical Code: {code.strip()}">{code.strip()}</span>'

        html_content += f"""
        <tr>
            <td><strong>{medication}</strong></td>
            <td>{dosage}</td>
            <td>{frequency}</td>
            <td><span class="status-badge {status_class}">{status}</span></td>
            <td>{start_date}</td>
            <td>{codes_html or "N/A"}</td>
        </tr>
        """

    html_content += """
        </tbody>
    </table>
    """

    return html_content


def generate_allergy_table_html_interactive(entries):
    """Generate interactive HTML table for allergies with collapsible details"""
    if not entries:
        return "<p>No allergy data available.</p>"

    html_content = """
    <table class="clinical-table">
        <thead>
            <tr>
                <th>[WARNING] Allergen</th>
                <th>🔥 Reaction</th>
                <th>[DATA] Severity</th>
                <th>[LIST] Status</th>
                <th>📅 First Noted</th>
                <th>🔬 Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        allergen = entry.get("Allergen", "Not specified")
        reaction = entry.get("Reaction", "Not specified")
        severity = entry.get("Severity", "Not specified")
        status = entry.get("Status", "Unknown")
        first_noted = entry.get("First Noted", "Not recorded")
        codes = entry.get("Codes", "")

        status_class = (
            "status-active" if status.lower() == "active" else "status-inactive"
        )

        codes_html = ""
        if codes:
            code_list = codes.split(", ") if isinstance(codes, str) else [str(codes)]
            for code in code_list:
                if code.strip():
                    codes_html += f'<span class="medical-code" title="Medical Code: {code.strip()}">{code.strip()}</span>'

        html_content += f"""
        <tr>
            <td><strong>{allergen}</strong></td>
            <td>{reaction}</td>
            <td>{severity}</td>
            <td><span class="status-badge {status_class}">{status}</span></td>
            <td>{first_noted}</td>
            <td>{codes_html or "N/A"}</td>
        </tr>
        """

    html_content += """
        </tbody>
    </table>
    """

    return html_content


def generate_procedure_table_html_interactive(entries):
    """Generate interactive HTML table for procedures with collapsible details"""
    if not entries:
        return "<p>No procedure data available.</p>"

    html_content = """
    <table class="clinical-table">
        <thead>
            <tr>
                <th>[HOSPITAL] Procedure</th>
                <th>📅 Date Performed</th>
                <th>[DATA] Status</th>
                <th>👨‍⚕️ Healthcare Provider</th>
                <th>🔬 Medical Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        procedure = entry.get("Procedure", "Not specified")
        date_performed = entry.get("Date Performed", "Not recorded")
        status = entry.get("Status", "Unknown")
        provider = entry.get("Healthcare Provider", "Not specified")
        codes = entry.get("Medical Codes", "")

        status_class = (
            "status-completed" if status.lower() == "completed" else "status-active"
        )

        codes_html = ""
        if codes:
            code_list = codes.split(", ") if isinstance(codes, str) else [str(codes)]
            for code in code_list:
                if code.strip():
                    codes_html += f'<span class="medical-code" title="Medical Code: {code.strip()}">{code.strip()}</span>'

        html_content += f"""
        <tr>
            <td><strong>{procedure}</strong></td>
            <td>{date_performed}</td>
            <td><span class="status-badge {status_class}">{status}</span></td>
            <td>{provider}</td>
            <td>{codes_html or "N/A"}</td>
        </tr>
        """

    html_content += """
        </tbody>
    </table>
    """

    return html_content


def generate_problem_table_html_interactive(entries):
    """Generate interactive HTML table for problems/diagnoses with collapsible details"""
    if not entries:
        return "<p>No problem data available.</p>"

    html_content = """
    <table class="clinical-table">
        <thead>
            <tr>
                <th>[STETHOSCOPE] Problem/Diagnosis</th>
                <th>[DATA] Status</th>
                <th>📅 Onset Date</th>
                <th>[NOTE] Notes</th>
                <th>🔬 Medical Codes</th>
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        problem = entry.get("Problem", entry.get("Diagnosis", "Not specified"))
        status = entry.get("Status", "Unknown")
        onset_date = entry.get("Onset Date", "Not recorded")
        notes = entry.get("Notes", "")
        codes = entry.get("Codes", "")

        status_class = (
            "status-active" if status.lower() == "active" else "status-inactive"
        )

        codes_html = ""
        if codes:
            code_list = codes.split(", ") if isinstance(codes, str) else [str(codes)]
            for code in code_list:
                if code.strip():
                    codes_html += f'<span class="medical-code" title="Medical Code: {code.strip()}">{code.strip()}</span>'

        html_content += f"""
        <tr>
            <td><strong>{problem}</strong></td>
            <td><span class="status-badge {status_class}">{status}</span></td>
            <td>{onset_date}</td>
            <td>{notes[:100] + '...' if len(notes) > 100 else notes}</td>
            <td>{codes_html or "N/A"}</td>
        </tr>
        """

    html_content += """
        </tbody>
    </table>
    """

    return html_content


def generate_generic_table_html_interactive(entries):
    """Generate interactive HTML table for generic clinical data"""
    if not entries:
        return "<p>No data available.</p>"

    # Get all unique keys from entries to create dynamic headers
    all_keys = set()
    for entry in entries:
        all_keys.update(entry.keys())

    headers = list(all_keys)

    html_content = """
    <table class="clinical-table">
        <thead>
            <tr>
    """

    for header in headers:
        html_content += f"<th>{header}</th>"

    html_content += """
            </tr>
        </thead>
        <tbody>
    """

    for entry in entries:
        html_content += "<tr>"
        for header in headers:
            value = entry.get(header, "")
            if "code" in header.lower() and value:
                # Handle medical codes
                codes_html = ""
                code_list = (
                    value.split(", ") if isinstance(value, str) else [str(value)]
                )
                for code in code_list:
                    if code.strip():
                        codes_html += f'<span class="medical-code" title="Medical Code: {code.strip()}">{code.strip()}</span>'
                html_content += f"<td>{codes_html}</td>"
            elif "status" in header.lower():
                # Handle status with badges
                status_class = (
                    "status-active" if value.lower() == "active" else "status-inactive"
                )
                html_content += (
                    f'<td><span class="status-badge {status_class}">{value}</span></td>'
                )
            else:
                # Regular content
                display_value = (
                    str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                )
                html_content += f"<td>{display_value}</td>"
    html_content += """
        </tbody>
    </table>
    """

    return html_content


def select_document_view(request, patient_id):
    """Handle document selection for patients with multiple CDA documents"""
    try:
        # Get the session data for this patient
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if not match_data:
            messages.error(
                request, "Patient session data not found. Please search again."
            )
            return redirect("patient_data:patient_data_form")

        if request.method == "POST":
            # Handle document selection
            document_type = request.POST.get("document_type")  # "L1" or "L3"
            document_index = int(request.POST.get("document_index", 0))

            if document_type == "L1" and "l1_documents" in match_data:
                if 0 <= document_index < len(match_data["l1_documents"]):
                    selected_doc = match_data["l1_documents"][document_index]
                    match_data["selected_l1_index"] = document_index
                    # Update preferred CDA type to L1 since user selected an L1 document
                    match_data["preferred_cda_type"] = "L1"
                    # Update displayed metadata to reflect selected document
                    match_data["file_path"] = selected_doc["path"]
                    match_data["cda_type"] = "L1"
                    request.session[session_key] = match_data
                    messages.success(
                        request, f"Selected L1 document {document_index + 1}"
                    )

            elif document_type == "L3" and "l3_documents" in match_data:
                if 0 <= document_index < len(match_data["l3_documents"]):
                    selected_doc = match_data["l3_documents"][document_index]
                    match_data["selected_l3_index"] = document_index
                    # Update preferred CDA type to L3 since user selected an L3 document
                    match_data["preferred_cda_type"] = "L3"
                    # Update displayed metadata to reflect selected document
                    match_data["file_path"] = selected_doc["path"]
                    match_data["cda_type"] = "L3"
                    request.session[session_key] = match_data
                    messages.success(
                        request, f"Selected L3 document {document_index + 1}"
                    )

            # Redirect back to patient details to show the selected document
            return redirect("patient_data:patient_details", patient_id=patient_id)

        # GET request - show document selection form
        context = {
            "patient_id": patient_id,
            "patient_data": match_data.get("patient_data", {}),
            "l1_documents": match_data.get("l1_documents", []),
            "l3_documents": match_data.get("l3_documents", []),
            "selected_l1_index": match_data.get("selected_l1_index", 0),
            "selected_l3_index": match_data.get("selected_l3_index", 0),
            "document_summary": match_data.get("document_summary", {}),
            "available_document_types": match_data.get("available_document_types", []),
        }

        return render(request, "patient_data/select_document.html", context)

    except Exception as e:
        logger.error(f"Error in select_document_view: {e}")
        messages.error(request, "Error accessing document selection.")
        return redirect("patient_data:patient_data_form")


def view_embedded_pdf(request, patient_id, pdf_index):
    """View an embedded PDF from a CDA document"""
    try:
        from .services.patient_search_service import PatientMatch

        # Get patient match data from session
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if not match_data:
            logger.error(f"No session data found for patient {patient_id}")
            return HttpResponse("Session data not found", status=404)

        # Get CDA content - reconstruct PatientMatch from session data
        patient_info = match_data.get("patient_data", {})
        search_result = PatientMatch(
            patient_id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=patient_info.get("birth_date", ""),
            gender=patient_info.get("gender", ""),
            country_code=match_data.get("country_code", "IE"),
            confidence_score=match_data.get("confidence_score", 0.95),
            file_path=match_data.get("file_path"),
            l1_cda_content=match_data.get("l1_cda_content"),
            l3_cda_content=match_data.get("l3_cda_content"),
            l1_cda_path=match_data.get("l1_cda_path"),
            l3_cda_path=match_data.get("l3_cda_path"),
            cda_content=match_data.get("cda_content"),
            patient_data=patient_info,
            preferred_cda_type="L1",
            l1_documents=match_data.get("l1_documents", []),
            l3_documents=match_data.get("l3_documents", []),
            selected_l1_index=match_data.get("selected_l1_index", 0),
            selected_l3_index=match_data.get("selected_l3_index", 0),
        )
        cda_content, actual_cda_type = search_result.get_rendering_cda("L1")

        if not cda_content:
            logger.error(f"No L1 CDA content found for patient {patient_id}")
            return HttpResponse("CDA content not found", status=404)

        # Extract PDFs using the service
        pdf_service = ClinicalDocumentPDFService()
        embedded_pdfs = pdf_service.extract_all_pdfs_from_xml(cda_content)

        if pdf_index >= len(embedded_pdfs):
            logger.error(f"PDF index {pdf_index} out of range for patient {patient_id}")
            return HttpResponse("PDF not found", status=404)

        pdf_info = embedded_pdfs[pdf_index]
        pdf_data = pdf_info.get("content")

        if not pdf_data:
            logger.error(f"No PDF data for index {pdf_index} for patient {patient_id}")
            return HttpResponse("PDF data not found", status=404)

        # Return PDF response
        response = HttpResponse(pdf_data, content_type="application/pdf")
        filename = pdf_info.get("filename", f"clinical_document_{pdf_index}.pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        # Allow iframe embedding for PDF viewing
        response["X-Frame-Options"] = "SAMEORIGIN"

        logger.info(
            f"Serving embedded PDF {pdf_index} ({filename}) for patient {patient_id}"
        )
        return response

    except Exception as e:
        logger.error(
            f"Error serving embedded PDF {pdf_index} for patient {patient_id}: {e}"
        )
        return HttpResponse("Error loading PDF", status=500)


def download_embedded_pdf(request, patient_id, pdf_index):
    """Download an embedded PDF from a CDA document"""
    try:
        from .services.patient_search_service import PatientMatch

        # Get patient match data from session
        session_key = f"patient_match_{patient_id}"
        match_data = request.session.get(session_key)

        if not match_data:
            logger.error(f"No session data found for patient {patient_id}")
            return HttpResponse("Session data not found", status=404)

        # Get CDA content - reconstruct PatientMatch from session data
        patient_info = match_data.get("patient_data", {})
        search_result = PatientMatch(
            patient_id=patient_id,
            given_name=patient_info.get("given_name", "Unknown"),
            family_name=patient_info.get("family_name", "Patient"),
            birth_date=patient_info.get("birth_date", ""),
            gender=patient_info.get("gender", ""),
            country_code=match_data.get("country_code", "IE"),
            confidence_score=match_data.get("confidence_score", 0.95),
            file_path=match_data.get("file_path"),
            l1_cda_content=match_data.get("l1_cda_content"),
            l3_cda_content=match_data.get("l3_cda_content"),
            l1_cda_path=match_data.get("l1_cda_path"),
            l3_cda_path=match_data.get("l3_cda_path"),
            cda_content=match_data.get("cda_content"),
            patient_data=patient_info,
            preferred_cda_type="L1",
            l1_documents=match_data.get("l1_documents", []),
            l3_documents=match_data.get("l3_documents", []),
            selected_l1_index=match_data.get("selected_l1_index", 0),
            selected_l3_index=match_data.get("selected_l3_index", 0),
        )
        cda_content, actual_cda_type = search_result.get_rendering_cda("L1")

        if not cda_content:
            logger.error(f"No L1 CDA content found for patient {patient_id}")
            return HttpResponse("CDA content not found", status=404)

        # Extract PDFs using the service
        pdf_service = ClinicalDocumentPDFService()
        embedded_pdfs = pdf_service.extract_all_pdfs_from_xml(cda_content)

        if pdf_index >= len(embedded_pdfs):
            logger.error(f"PDF index {pdf_index} out of range for patient {patient_id}")
            return HttpResponse("PDF not found", status=404)

        pdf_info = embedded_pdfs[pdf_index]
        pdf_data = pdf_info.get("content")

        if not pdf_data:
            logger.error(f"No PDF data for index {pdf_index} for patient {patient_id}")
            return HttpResponse("PDF data not found", status=404)

        # Return PDF download response
        response = HttpResponse(pdf_data, content_type="application/pdf")
        filename = pdf_info.get("filename", f"clinical_document_{pdf_index}.pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        logger.info(
            f"Downloaded embedded PDF {pdf_index} ({filename}) for patient {patient_id}"
        )
        return response

    except Exception as e:
        logger.error(
            f"Error downloading embedded PDF {pdf_index} for patient {patient_id}: {e}"
        )
        return HttpResponse("Error downloading PDF", status=500)


import json

from django.http import HttpResponse

# Placeholder for InteroperableHealthcareView
from django.views import View


class InteroperableHealthcareView(View):
    """
    Placeholder view for interoperable healthcare functionality.
    This is a temporary implementation to keep the application running.
    """

    def get(self, request, *args, **kwargs):
        return HttpResponse(
            json.dumps(
                {
                    "status": "placeholder",
                    "message": "InteroperableHealthcareView placeholder",
                }
            ),
            content_type="application/json",
        )

    def post(self, request, *args, **kwargs):
        return HttpResponse(
            json.dumps(
                {
                    "status": "placeholder",
                    "message": "InteroperableHealthcareView placeholder",
                }
            ),
            content_type="application/json",
        )
