"""
Central Terminology Service
Medical Code Extraction and Processing for NCPeH Architecture

This service implements the Central Terminology Service architecture for
the Django NCP application. It extracts medical terminology directly from
CDA documents without using hardcoded mappings, following the NCPeH
specification for English-speaking Member States.

Architecture:
- Extracts medical codes directly from CDA document structure
- Processes Friendly CDA documents with dual-language terminology
- Handles SNOMED CT, ICD-10, and other international code systems
- No hardcoded medical terminology mappings
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CentralTerminologyService:
    """
    Central Terminology Service for NCPeH Medical Code Processing

    Implements the European Central Terminology Service architecture
    for extracting and processing medical terminology from CDA documents.
    """

    def __init__(self):
        """Initialize the Central Terminology Service"""
        # Code system OID mappings (international standards - not hardcoded medical data)
        self.code_system_oids = {
            "2.16.840.1.113883.6.96": "SNOMED CT",
            "2.16.840.1.113883.6.1": "LOINC",
            "2.16.840.1.113883.6.88": "RxNorm",
            "2.16.840.1.113883.6.3": "ICD-10-CM",
            "2.16.840.1.113883.6.4": "ICD-10-PCS",
            "2.16.840.1.113883.6.103": "ICD-9-CM",
            "2.16.840.1.113883.5.83": "UCUM",
            "2.16.840.1.113883.6.73": "ATC",
        }

        # CSS badge mappings for code systems (styling - not medical data)
        self.code_system_badges = {
            "2.16.840.1.113883.6.96": "badge bg-primary",  # SNOMED CT
            "2.16.840.1.113883.6.1": "badge bg-success",  # LOINC
            "2.16.840.1.113883.6.88": "badge bg-warning",  # RxNorm
            "2.16.840.1.113883.6.3": "badge bg-danger",  # ICD-10-CM
            "2.16.840.1.113883.6.4": "badge bg-danger",  # ICD-10-PCS
            "2.16.840.1.113883.6.103": "badge bg-secondary",  # ICD-9-CM
            "2.16.840.1.113883.5.83": "badge bg-info",  # UCUM
            "2.16.840.1.113883.6.73": "badge bg-dark",  # ATC
        }

    def extract_medical_codes_from_fields(
        self, fields: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Extract all medical codes from CDA document fields

        Args:
            fields: Dictionary of fields extracted from CDA document entry

        Returns:
            List of medical code dictionaries with code, system, display, etc.
        """
        extracted_codes = []

        logger.info(
            f"[SEARCH] TERMINOLOGY SERVICE: Analyzing {len(fields)} fields for medical codes"
        )

        # Strategy 1: Direct code field extraction
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict):
                # Look for direct code values with system information
                if field_data.get("code") and field_data.get("codeSystem"):
                    code_info = {
                        "code": str(field_data["code"]),
                        "system": self.get_code_system_name(field_data["codeSystem"]),
                        "system_oid": field_data["codeSystem"],
                        "display": field_data.get("displayName", ""),
                        "field": field_name,
                        "badge": self.get_code_system_badge(field_data["codeSystem"]),
                    }
                    extracted_codes.append(code_info)
                    logger.info(
                        f"[SUCCESS] Found code: {code_info['code']} ({code_info['system']}) in {field_name}"
                    )

                # Look for nested code structures
                elif field_data.get("value") and isinstance(field_data["value"], dict):
                    nested_value = field_data["value"]
                    if nested_value.get("code") and nested_value.get("codeSystem"):
                        code_info = {
                            "code": str(nested_value["code"]),
                            "system": self.get_code_system_name(
                                nested_value["codeSystem"]
                            ),
                            "system_oid": nested_value["codeSystem"],
                            "display": nested_value.get("displayName", ""),
                            "field": field_name,
                            "badge": self.get_code_system_badge(
                                nested_value["codeSystem"]
                            ),
                        }
                        extracted_codes.append(code_info)
                        logger.info(
                            f"[SUCCESS] Found nested code: {code_info['code']} ({code_info['system']}) in {field_name}"
                        )

        # Strategy 2: Pattern-based code extraction for Friendly CDA documents
        # Extract codes that match medical code patterns (SNOMED CT, ICD-10, etc.)
        for field_name, field_data in fields.items():
            if isinstance(field_data, dict) and field_data.get("value"):
                value_str = str(field_data["value"])

                # Look for SNOMED CT codes (typically 6-18 digits)
                snomed_codes = re.findall(r"\b\d{6,18}\b", value_str)
                for code in snomed_codes:
                    if self._is_valid_snomed_code(code):
                        code_info = {
                            "code": code,
                            "system": "SNOMED CT",
                            "system_oid": "2.16.840.1.113883.6.96",
                            "display": "",
                            "field": f"{field_name}_pattern",
                            "badge": "badge bg-primary",
                        }
                        extracted_codes.append(code_info)
                        logger.info(
                            f"[SUCCESS] Extracted SNOMED CT pattern: {code} from {field_name}"
                        )

                # Look for ICD-10 codes (format: A00.0, Z99.9, etc.)
                icd10_codes = re.findall(r"\b[A-Z]\d{2}\.?[A-Z0-9]*\b", value_str)
                for code in icd10_codes:
                    code_info = {
                        "code": code,
                        "system": "ICD-10",
                        "system_oid": "2.16.840.1.113883.6.3",
                        "display": "",
                        "field": f"{field_name}_icd10_pattern",
                        "badge": "badge bg-danger",
                    }
                    extracted_codes.append(code_info)
                    logger.info(
                        f"[SUCCESS] Extracted ICD-10 pattern: {code} from {field_name}"
                    )

        logger.info(
            f"[TARGET] TERMINOLOGY SERVICE: Extracted {len(extracted_codes)} medical codes from CDA fields"
        )
        return extracted_codes

    def extract_condition_terminology(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract condition/problem terminology from CDA fields

        Args:
            fields: CDA document fields for a condition/problem entry

        Returns:
            Dictionary with condition information and extracted codes
        """
        result = {
            "display_value": "Unknown Problem",
            "codes": [],
            "has_terminology": False,
            "extraction_method": "cda_direct",
        }

        # Extract display name from CDA fields
        display_fields = [
            "Value DisplayName",
            "Problem DisplayName",
            "Observation Value DisplayName",
            "DisplayName",
            "Problem Description",
            "Condition Name",
            "Problem",
        ]

        for field_name in display_fields:
            if field_name in fields and fields[field_name]:
                field_data = fields[field_name]
                if isinstance(field_data, dict):
                    display_value = (
                        field_data.get("displayName")
                        or field_data.get("value")
                        or field_data.get("text")
                    )
                    if display_value and display_value != "Not specified":
                        result["display_value"] = display_value
                        break
                elif isinstance(field_data, str) and field_data != "Not specified":
                    result["display_value"] = field_data
                    break

        # Extract medical codes using the terminology service
        result["codes"] = self.extract_medical_codes_from_fields(fields)
        result["has_terminology"] = len(result["codes"]) > 0

        logger.info(
            f"[HOSPITAL] Condition terminology: '{result['display_value']}' with {len(result['codes'])} codes"
        )
        return result

    def extract_procedure_terminology(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract procedure terminology from CDA fields

        Args:
            fields: CDA document fields for a procedure entry

        Returns:
            Dictionary with procedure information and extracted codes
        """
        result = {
            "display_value": "Unknown Procedure",
            "codes": [],
            "has_terminology": False,
            "extraction_method": "cda_direct",
        }

        # Extract display name from CDA fields
        display_fields = [
            "Procedure DisplayName",
            "Procedure OriginalText",
            "Procedure Code",
            "Procedure",
        ]

        for field_name in display_fields:
            if field_name in fields and fields[field_name]:
                field_data = fields[field_name]
                if isinstance(field_data, dict):
                    display_value = (
                        field_data.get("displayName")
                        or field_data.get("value")
                        or field_data.get("text")
                    )
                    if display_value and display_value != "Not specified":
                        result["display_value"] = display_value
                        break
                elif isinstance(field_data, str) and field_data != "Not specified":
                    result["display_value"] = field_data
                    break

        # Extract medical codes using the terminology service
        result["codes"] = self.extract_medical_codes_from_fields(fields)
        result["has_terminology"] = len(result["codes"]) > 0

        logger.info(
            f"[HOSPITAL] Procedure terminology: '{result['display_value']}' with {len(result['codes'])} codes"
        )
        return result

    def get_code_system_name(self, oid_or_name: str) -> str:
        """
        Convert OID or system identifier to readable name

        Args:
            oid_or_name: OID string or system name

        Returns:
            Human-readable system name
        """
        return self.code_system_oids.get(oid_or_name, f"Code System ({oid_or_name})")

    def get_code_system_badge(self, oid_or_name: str) -> str:
        """
        Get CSS badge class for code system

        Args:
            oid_or_name: OID string or system name

        Returns:
            CSS badge class
        """
        return self.code_system_badges.get(oid_or_name, "badge bg-outline-secondary")

    def _is_valid_snomed_code(self, code: str) -> bool:
        """
        Validate if a code matches SNOMED CT patterns

        Args:
            code: Potential SNOMED CT code

        Returns:
            True if code appears to be a valid SNOMED CT code
        """
        # SNOMED CT codes are typically 6-18 digits
        if not code.isdigit():
            return False
        if len(code) < 6 or len(code) > 18:
            return False
        # Additional validation could be added here
        return True


# Global instance for use in views
terminology_service = CentralTerminologyService()
