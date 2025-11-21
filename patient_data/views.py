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
from .services.immunizations_extractor import ImmunizationsExtractor
from .services.pregnancy_history_extractor import PregnancyHistoryExtractor
from .services.social_history_extractor import SocialHistoryExtractor

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
            use_fhir = form.cleaned_data.get("use_fhir", True)

            # Log the NCP query with development options
            logger.info(
                "NCP Document Query: Patient ID %s from %s (CDA: %s, FHIR: %s)",
                patient_id,
                country_code,
                use_local_cda,
                use_fhir,
            )

            # Create search credentials for NCP-to-NCP query
            credentials = PatientCredentials(
                country_code=country_code,
                patient_id=patient_id,
            )

            # Search for matching documents with development options
            search_service = EUPatientSearchService()
            matches = search_service.search_patient(credentials, use_local_cda, use_fhir)

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
                # Handle anonymous users for public patient search
                session_user = request.user if request.user.is_authenticated else None
                
                if session_user:
                    # Authenticated user - create full PatientSession
                    patient_session = PatientSession.objects.create(
                        session_id=session_id,
                        user=session_user,
                        country_code=country_code,
                        search_criteria_hash=hash(f"{country_code}_{patient_id}"),
                        status="active",
                        expires_at=timezone.now() + timedelta(hours=8),
                        client_ip=request.META.get("REMOTE_ADDR", ""),
                        last_action="patient_search_successful",
                        encryption_key_version=1,  # Set default encryption version
                    )
                    
                    # Encrypt and store patient data for authenticated users
                    patient_session.encrypt_patient_data(patient_session_data)
                else:
                    # Anonymous user - use session storage only (no PatientSession model)
                    logger.info(f"Anonymous patient search for {patient_id} from {country_code}")
                
                # Store in Django session for both authenticated and anonymous users
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
            "preferred_cda_type": getattr(match, "preferred_cda_type", "L3"),  # Use actual detected type
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
                        "preferred_cda_type": search_result.preferred_cda_type,  # Use actual detected type instead of hardcoded L3
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
            "social_history": [],
            "laboratory_results": [],
            "results": [],
            "immunizations": [],
            "pregnancy_history": [],
        }
        
        # PHASE 3B: Initialize administrative data variables for template context
        administrative_data = {}
        healthcare_data = {}
        
        try:
            # PRIORITY 1: Check for FHIR bundle data FIRST (with deduplication fix)
            fhir_bundle = match_data.get("fhir_bundle")
            if fhir_bundle:
                logger.info(f"[PATIENT_DETAILS] Using FHIR bundle data for patient {patient_id}")
                
                from patient_data.services.fhir_bundle_parser import FHIRBundleParser
                
                parser = FHIRBundleParser()
                fhir_result = parser.parse_patient_summary_bundle(fhir_bundle)
                
                if fhir_result and isinstance(fhir_result, dict):
                    # Extract clinical arrays from FHIR (with deduplication)
                    clinical_arrays = fhir_result.get('clinical_arrays', clinical_arrays)
                    administrative_data = fhir_result.get('administrative_data', {})
                    healthcare_data = fhir_result.get('healthcare_data', {})
                    
                    logger.info(
                        f"[PATIENT_DETAILS] FHIR clinical arrays extracted: "
                        f"problems={len(clinical_arrays['problems'])}, "
                        f"allergies={len(clinical_arrays['allergies'])}, "
                        f"medications={len(clinical_arrays['medications'])}, "
                        f"laboratory_results={len(clinical_arrays.get('laboratory_results', []))}, "
                        f"vital_signs={len(clinical_arrays.get('vital_signs', []))}"
                    )
            
            # FALLBACK: Use CDA content if no FHIR bundle
            elif match_data.get("cda_content"):
                logger.info(f"[PATIENT_DETAILS] Using CDA content for patient {patient_id}")
                
                # Import and use the comprehensive clinical data service
                from .services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
                
                comprehensive_service = ComprehensiveClinicalDataService()
                cda_content = match_data.get("cda_content")
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
                    
                    # PHASE 3B: Extract administrative data from enhanced parser for Healthcare Team & Contacts tab
                    administrative_data = comprehensive_data.get("administrative_data", {})
                    healthcare_data = comprehensive_data.get("healthcare_data", {})
                    
                    logger.info(f"[PHASE_3B] Administrative data extracted: {len(administrative_data)} keys")
                    logger.info(f"[PHASE_3B] Healthcare data extracted: {len(healthcare_data)} keys")
                    
                    # ENHANCED ALLERGIES: Follow medications pattern with Django session storage
                    # Check if enhanced allergies already in context (from CDA processor), 
                    # otherwise check session for enhanced allergies and override if available
                    if 'allergies' in clinical_arrays and len(clinical_arrays['allergies']) > 0:
                        # Check if first allergy has enhanced data structure (from CDA processor)
                        first_allergy = clinical_arrays['allergies'][0]
                        if 'data' in first_allergy and isinstance(first_allergy['data'], dict):
                            logger.info(f"[ENHANCED_ALLERGIES] Using {len(clinical_arrays['allergies'])} enhanced allergies already in context from CDA processor")
                        else:
                            # Fallback to session-based enhanced allergies
                            enhanced_allergies = request.session.get('enhanced_allergies')
                            if enhanced_allergies:
                                logger.info(f"[ENHANCED_ALLERGIES] Found {len(enhanced_allergies)} enhanced allergies in session, overriding clinical arrays")
                                clinical_arrays["allergies"] = enhanced_allergies
                            else:
                                logger.info("[ENHANCED_ALLERGIES] No enhanced allergies found in session, using clinical arrays")
                    else:
                        # No allergies in context, check session
                        enhanced_allergies = request.session.get('enhanced_allergies')
                        if enhanced_allergies:
                            logger.info(f"[ENHANCED_ALLERGIES] Found {len(enhanced_allergies)} enhanced allergies in session")
                            clinical_arrays["allergies"] = enhanced_allergies
                        else:
                            logger.info("[ENHANCED_ALLERGIES] No enhanced allergies found in context or session")
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
            # DEBUG: Log medication data structure for troubleshooting
            medications = clinical_arrays["medications"]
            logger.info(f"[DEBUG_MEDICATIONS] Count: {len(medications)}")
            if medications:
                for i, med in enumerate(medications[:3], 1):  # Log first 3 medications
                    logger.info(f"[DEBUG_MED_{i}] Keys: {list(med.keys())}")
                    logger.info(f"[DEBUG_MED_{i}] medication_name: {med.get('medication_name', 'MISSING')}")
                    logger.info(f"[DEBUG_MED_{i}] name: {med.get('name', 'MISSING')}")
                    logger.info(f"[DEBUG_MED_{i}] display_name: {med.get('display_name', 'MISSING')}")
                    if 'data' in med:
                        data = med['data']
                        logger.info(f"[DEBUG_MED_{i}] data.medication_name: {data.get('medication_name', 'MISSING')}")
                        logger.info(f"[DEBUG_MED_{i}] data.dose_quantity: {data.get('dose_quantity', 'MISSING')}")
                        logger.info(f"[DEBUG_MED_{i}] data.route_display: {data.get('route_display', 'MISSING')}")
                        logger.info(f"[DEBUG_MED_{i}] data.pharmaceutical_form: {data.get('pharmaceutical_form', 'MISSING')}")
                        logger.info(f"[DEBUG_MED_{i}] data.ingredient_display: {data.get('ingredient_display', 'MISSING')}")
                    else:
                        logger.info(f"[DEBUG_MED_{i}] NO DATA FIELD")
            
            # DEBUG: Log laboratory results before adding to context
            lab_results = clinical_arrays.get("laboratory_results", [])
            logger.info(f"[CONTEXT_DEBUG] Laboratory results count: {len(lab_results)}")
            if lab_results:
                logger.info(f"[CONTEXT_DEBUG] First lab result keys: {list(lab_results[0].keys())}")
                logger.info(f"[CONTEXT_DEBUG] First lab result data: {lab_results[0]}")
            
            context.update(
                {
                    "medications": clinical_arrays["medications"],
                    "allergies": clinical_arrays["allergies"],
                    "problems": clinical_arrays["problems"],
                    "procedures": clinical_arrays["procedures"],
                    "vital_signs": clinical_arrays["vital_signs"],
                    "social_history": clinical_arrays.get("social_history", []),
                    "laboratory_results": clinical_arrays.get("laboratory_results", []),
                    "results": clinical_arrays["results"],
                    "immunizations": clinical_arrays["immunizations"],
                    "pregnancy_history": clinical_arrays.get("pregnancy_history", []),
                    "coded_results": {"blood_group": [], "diagnostic_results": []},  # Initialize for template compatibility
                }
            )
            
            # ENHANCED PROCEDURES: Check if enhanced procedures already in context (from CDA processor), 
            # otherwise check session for enhanced procedures and override if available
            if 'procedures' in context and len(context['procedures']) > 0:
                # Check if first procedure has enhanced data structure (from CDA processor)
                first_proc = context['procedures'][0]
                if 'data' in first_proc and isinstance(first_proc['data'], dict):
                    logger.info(f"[ENHANCED_PROCEDURES] Using {len(context['procedures'])} enhanced procedures already in context from CDA processor")
                    logger.info(f"[ENHANCED_PROCEDURES] First procedure: {first_proc.get('data', {}).get('procedure_name', {}).get('value', 'Unknown')}")
                else:
                    # Fallback to session-based enhanced procedures
                    enhanced_procedures = request.session.get('enhanced_procedures')
                    if enhanced_procedures:
                        logger.info(f"[ENHANCED_PROCEDURES] Found {len(enhanced_procedures)} enhanced procedures in session, overriding clinical arrays")
                        context["procedures"] = enhanced_procedures
                        logger.info(f"[ENHANCED_PROCEDURES] First procedure: {enhanced_procedures[0].get('procedure_name', enhanced_procedures[0].get('name', 'Unknown'))} - Code: {enhanced_procedures[0].get('procedure_code', 'N/A')}")
                    else:
                        logger.info("[ENHANCED_PROCEDURES] No enhanced procedures found in session, using clinical arrays")
            else:
                # No procedures in context, check session
                enhanced_procedures = request.session.get('enhanced_procedures')
                if enhanced_procedures:
                    logger.info(f"[ENHANCED_PROCEDURES] Found {len(enhanced_procedures)} enhanced procedures in session")
                    context["procedures"] = enhanced_procedures
                else:
                    logger.info("[ENHANCED_PROCEDURES] No enhanced procedures found in context or session")
            
            # ENHANCED MEDICATIONS: Check if enhanced medications already in context (from CDA processor), 
            # otherwise check session for enhanced medications and override if available
            if 'medications' in context and len(context['medications']) > 0:
                # Check if first medication has enhanced data structure (from CDA processor)
                first_med = context['medications'][0]
                if 'data' in first_med and isinstance(first_med['data'], dict):
                    logger.info(f"[ENHANCED_MEDICATIONS] Using {len(context['medications'])} enhanced medications already in context from CDA processor")
                    logger.info(f"[ENHANCED_MEDICATIONS] First medication: {first_med.get('data', {}).get('medication_name', {}).get('value', 'Unknown')}")
                else:
                    # Fallback to session-based enhanced medications
                    enhanced_medications = request.session.get('enhanced_medications')
                    if enhanced_medications:
                        logger.info(f"[ENHANCED_MEDICATIONS] Found {len(enhanced_medications)} enhanced medications in session, overriding clinical arrays")
                        context["medications"] = enhanced_medications
                        logger.info(f"[ENHANCED_MEDICATIONS] First medication: {enhanced_medications[0].get('medication_name', 'Unknown')} - Dose: {enhanced_medications[0].get('dose_quantity', 'N/A')}")
                    else:
                        logger.info("[ENHANCED_MEDICATIONS] No enhanced medications found in session, using clinical arrays")
            else:
                # No medications in context, check session
                enhanced_medications = request.session.get('enhanced_medications')
                if enhanced_medications:
                    logger.info(f"[ENHANCED_MEDICATIONS] Found {len(enhanced_medications)} enhanced medications in session")
                    context["medications"] = enhanced_medications
                else:
                    logger.info("[ENHANCED_MEDICATIONS] No enhanced medications found in context or session")
            
            # PHASE 3B: Add administrative and healthcare data to context for Healthcare Team & Contacts tab
            context.update({
                "administrative_data": administrative_data,
                "healthcare_data": healthcare_data,
                "has_administrative_data": bool(administrative_data and any(administrative_data.values())),
                "has_healthcare_data": bool(healthcare_data and any(healthcare_data.values())),
            })
            
            # Extract patient_contact_info from administrative_data for Extended Patient Information tab
            # This follows the same pattern as context_builders.py
            from dataclasses import is_dataclass, asdict
            if administrative_data:
                patient_contact = getattr(administrative_data, 'patient_contact_info', None)
                if patient_contact and is_dataclass(patient_contact):
                    context['patient_contact_info'] = asdict(patient_contact)
                    logger.debug(f"[PATIENT_DETAILS] Extracted patient_contact_info: {len(patient_contact.addresses)} addresses, {len(patient_contact.telecoms)} telecoms")
                elif patient_contact:
                    context['patient_contact_info'] = patient_contact
                    logger.debug(f"[PATIENT_DETAILS] Added patient_contact_info dict to context")
                else:
                    logger.info(f"[PATIENT_DETAILS] No patient_contact_info found in administrative_data")
            
            total_clinical_items = sum(
                len(arr) for arr in clinical_arrays.values()
            )
            logger.info(
                f"[PATIENT_DETAILS] Added {total_clinical_items} clinical array items to context for patient {patient_id}"
            )
            
            # DEBUG: Log medication structure for troubleshooting
            medications = clinical_arrays.get("medications", [])
            logger.info(f"[DEBUG_MEDICATIONS] Patient {patient_id} - Medication count: {len(medications)}")
            if medications:
                first_med = medications[0]
                logger.info(f"[DEBUG_MEDICATIONS] First medication structure keys: {list(first_med.keys())}")
                logger.info(f"[DEBUG_MEDICATIONS] medication_name: {first_med.get('medication_name', 'MISSING')}")
                logger.info(f"[DEBUG_MEDICATIONS] name: {first_med.get('name', 'MISSING')}")
                if 'data' in first_med:
                    data_fields = first_med['data']
                    logger.info(f"[DEBUG_MEDICATIONS] data fields: {list(data_fields.keys())}")
                    logger.info(f"[DEBUG_MEDICATIONS] data.medication_name: {data_fields.get('medication_name', 'MISSING')}")
                    logger.info(f"[DEBUG_MEDICATIONS] data.dose_quantity: {data_fields.get('dose_quantity', 'MISSING')}")
                else:
                    logger.info(f"[DEBUG_MEDICATIONS] No 'data' field found")
        else:
            # Ensure clinical arrays exist even if empty for template compatibility
            context.update(
                {
                    "medications": [],
                    "allergies": [],
                    "problems": [],
                    "procedures": [],
                    "vital_signs": [],
                    "social_history": [],
                    "laboratory_results": [],
                    "results": [],
                    "pregnancy_history": [],
                    "immunizations": [],
                    "coded_results": {"blood_group": [], "diagnostic_results": []},  # Initialize for template compatibility
                }
            )
            
            # PHASE 3B: Initialize empty administrative data for template compatibility
            context.update({
                "administrative_data": {},
                "healthcare_data": {},
                "has_administrative_data": False,
                "has_healthcare_data": False,
            })
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
                # Initialize empty clinical arrays for template compatibility
                "medications": [],
                "allergies": [],
                "problems": [],
                "procedures": [],
                "vital_signs": [],
                "results": [],
                "immunizations": [],
            }
        )
        
        # ENHANCED PROCEDURES FALLBACK: Check session for enhanced procedures even with expired match_data
        enhanced_procedures = request.session.get('enhanced_procedures')
        if enhanced_procedures:
            logger.info(f"[ENHANCED_PROCEDURES_FALLBACK] Found {len(enhanced_procedures)} enhanced procedures in session despite match_data expiry")
            context["procedures"] = enhanced_procedures
            logger.info(f"[ENHANCED_PROCEDURES_FALLBACK] First procedure: {enhanced_procedures[0].get('procedure_name', enhanced_procedures[0].get('name', 'Unknown'))} - Code: {enhanced_procedures[0].get('procedure_code', 'N/A')}")
        else:
            logger.info("[ENHANCED_PROCEDURES_FALLBACK] No enhanced procedures found in session")

        # ENHANCED ALLERGIES FALLBACK: Check session for enhanced allergies even with expired match_data
        enhanced_allergies = request.session.get('enhanced_allergies')
        if enhanced_allergies:
            logger.info(f"[ENHANCED_ALLERGIES_FALLBACK] Found {len(enhanced_allergies)} enhanced allergies in session despite match_data expiry")
            context["allergies"] = enhanced_allergies
            logger.info(f"[ENHANCED_ALLERGIES_FALLBACK] First allergy: {enhanced_allergies[0].get('allergen', enhanced_allergies[0].get('name', 'Unknown'))} - Severity: {enhanced_allergies[0].get('severity', 'N/A')}")
        else:
            logger.info("[ENHANCED_ALLERGIES_FALLBACK] No enhanced allergies found in session")

        # ENHANCED MEDICATIONS FALLBACK: Check session for enhanced medications even with expired match_data
        enhanced_medications = request.session.get('enhanced_medications')
        if enhanced_medications:
            logger.info(f"[ENHANCED_MEDICATIONS_FALLBACK] Found {len(enhanced_medications)} enhanced medications in session despite match_data expiry")
            context["medications"] = enhanced_medications
            logger.info(f"[ENHANCED_MEDICATIONS_FALLBACK] First medication: {enhanced_medications[0].get('medication_name', enhanced_medications[0].get('name', 'Unknown'))} - Dose: {enhanced_medications[0].get('dose_quantity', 'N/A')}")
        else:
            logger.info("[ENHANCED_MEDICATIONS_FALLBACK] No enhanced medications found in session")

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
    """View for displaying patient documents with clean FHIR-CDA architecture separation

    PHASE 2: FHIR-CDA ARCHITECTURE SEPARATION
    This view now uses a clean router pattern that detects document type and delegates 
    to appropriate processor. Country agnostic - only cares about document type.

    ARCHITECTURE: Three-tier ID system implementation
    - session_id: URL parameter for privacy-compliant navigation (from URL)
    - patient_id: Healthcare/government identifier (from document)
    - database_id: Internal database primary key (auto-generated)

    Args:
        session_id: Session identifier from URL for privacy-compliant routing
        cda_type: Optional CDA type ('L1' or 'L3'). If None, defaults to L3 preference.
    """
    print(f"**** ROUTER CALLED FOR SESSION {session_id}, CDA_TYPE: {cda_type} ****")
    logger.info(f"[ROUTER] patient_cda_view called for session_id: {session_id}, cda_type: {cda_type}")
    
    # Session data recovery logic for cross-session compatibility
    target_key = f"patient_match_{session_id}"
    if target_key not in request.session:
        logger.info(f"[ROUTER] Session data not in current request.session, searching database...")
        from django.contrib.sessions.models import Session
        
        for db_session in Session.objects.all():
            try:
                session_data = db_session.get_decoded()
                if target_key in session_data:
                    logger.info(f"[ROUTER] Found {target_key} in database session, copying to current session")
                    request.session[target_key] = session_data[target_key]
                    request.session.save()
                    break
            except:
                continue
    
    try:
        # PHASE 2: FHIR-CDA ARCHITECTURE SEPARATION
        # Clean router implementation that detects document type and delegates to appropriate processor
        logger.info(f"[ROUTER] Starting document type detection for session {session_id}")
        
        from .view_processors.context_builders import ContextBuilder
        from .view_processors.fhir_processor import FHIRViewProcessor  
        from .view_processors.cda_processor import CDAViewProcessor
        
        # Initialize context builder and processors
        context_builder = ContextBuilder()
        fhir_processor = FHIRViewProcessor()
        cda_processor = CDAViewProcessor()
        
        # Detect document type from session data (country agnostic)
        data_source = context_builder.detect_data_source(request, session_id)
        logger.info(f"[ROUTER] Detected data source: {data_source}")
        
        # Route to appropriate processor based on document type (country agnostic)
        if data_source == "FHIR":
            logger.info(f"[ROUTER] Routing to FHIR processor for session {session_id}")
            response = fhir_processor.process_fhir_document(request, session_id, cda_type)
        else:
            logger.info(f"[ROUTER] Routing to CDA processor for session {session_id}")
            response = cda_processor.process_cda_document(request, session_id, cda_type)
        
        # Return response directly from processor (already rendered)
        logger.info(f"[ROUTER] Returning {data_source} response for session {session_id}")
        return response
    
    except Exception as e:
        logger.error(f"[ROUTER] Error in patient_cda_view router: {e}")
        import traceback
        logger.error(f"[ROUTER] Full traceback: {traceback.format_exc()}")
        # Re-raise the exception to see the full Django debug page
        raise e
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
                sections_html += generate_medication_table_html(
                    transformed_entries
                )
            elif (
                "allergi" in section_title.lower() or "adverse" in section_title.lower()
            ):
                sections_html += generate_allergy_table_html(
                    transformed_entries
                )
            elif "procedure" in section_title.lower():
                sections_html += generate_procedure_table_html(
                    transformed_entries
                )
            elif (
                "problem" in section_title.lower()
                or "diagnosis" in section_title.lower()
            ):
                sections_html += generate_problem_table_html(
                    transformed_entries
                )
            else:
                # Generic table for other sections
                sections_html += generate_generic_table_html(
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
