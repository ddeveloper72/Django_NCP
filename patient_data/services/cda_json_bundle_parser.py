#!/usr/bin/env python3
"""
CDA JSON Bundle Parser - Universal approach for all EU countries

This parser converts CDA XML to a JSON document bundle, then uses
JSONPath queries to extract clinical data. This approach is:
- Country-agnostic (works with IT, FR, DE, etc.)
- Future-proof (new countries need no parser changes)
- Performance optimized (JSON queries vs XML XPath)
- Modular (separate conversion from extraction)
"""

import json
import xmltodict
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClinicalCode:
    """Clinical code representation"""

    code: str
    system: str
    system_name: str
    display: str = ""
    original_text: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ClinicalSection:
    """Clinical section representation"""

    title: str
    section_code: str
    system: str
    content: str
    clinical_codes: List[ClinicalCode]
    is_coded_section: bool = False

    def to_dict(self):
        return {
            "title": self.title,
            "section_code": self.section_code,
            "system": self.system,
            "content": self.content,
            "clinical_codes": [code.to_dict() for code in self.clinical_codes],
            "is_coded_section": self.is_coded_section,
        }


class CDAJSONBundleParser:
    """
    Universal CDA Parser using JSON Bundle approach

    Workflow:
    1. Convert XML → JSON Bundle
    2. Extract clinical data using JSONPath queries
    3. Country-specific patterns handled dynamically
    """

    def __init__(self):
        self.code_system_mappings = {
            # Standard OID mappings
            "2.16.840.1.113883.6.96": {"name": "SNOMED-CT", "short": "SNOMED"},
            "2.16.840.1.113883.6.1": {"name": "LOINC", "short": "LOINC"},
            "2.16.840.1.113883.6.73": {"name": "ATC", "short": "ATC"},
            "2.16.840.1.113883.6.3": {"name": "ICD-10", "short": "ICD10"},
            "2.16.840.1.113883.6.4": {"name": "ICD-10-PCS", "short": "ICD10PCS"},
            "2.16.840.1.113883.6.42": {"name": "ICD-9-CM", "short": "ICD9"},
            "2.16.840.1.113883.6.103": {"name": "ICD-9", "short": "ICD9"},
            # European-specific mappings
            "1.2.276.0.76.5.409": {"name": "ALPHA-ID", "short": "ALPHA"},
            "1.2.276.0.76.5.493": {"name": "OPS", "short": "OPS"},
            "2.16.840.1.113883.2.4.4.40.267": {"name": "NL-Coding", "short": "NL"},
            # Italian-specific (from your CDA)
            "2.16.840.1.113883.2.9.77.22.11.2": {
                "name": "IT-Regione",
                "short": "IT-REG",
            },
            "2.16.840.1.113883.2.9.77.22.11.3": {"name": "IT-ATC", "short": "IT-ATC"},
        }

        # JSONPath patterns for finding coded elements across countries
        self.coded_element_patterns = [
            # Standard HL7 CDA patterns
            "$..*[?(@.code)]",  # Any element with 'code' attribute
            "$..*[?(@.value)]",  # Any element with 'value' attribute
            "$..*[?(@.codeSystem)]",  # Any element with codeSystem
            # Common CDA structure patterns
            "$..component.section.entry..*[?(@.code)]",
            "$..component.section.entry..*[?(@.value)]",
            "$..observation[?(@.code)]",
            "$..act[?(@.code)]",
            "$..procedure[?(@.code)]",
            "$..substanceAdministration[?(@.code)]",
            # Text reference patterns
            "$..originalText.reference[@value]",
            "$..text..*[?(@.ID)]",
        ]

    def parse_cda_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse CDA file using JSON Bundle approach

        Args:
            file_path: Path to CDA XML file

        Returns:
            Dictionary with extracted clinical data
        """
        try:
            logger.info(f"Parsing CDA file: {file_path}")

            # Step 1: Convert XML to JSON Bundle
            json_bundle = self._xml_to_json_bundle(file_path)

            # Step 2: Extract patient identity
            patient_identity = self._extract_patient_identity(json_bundle)

            # Step 3: Extract clinical sections
            sections = self._extract_clinical_sections(json_bundle)

            # Step 4: Build result
            result = {
                "patient_identity": patient_identity,
                "sections": [section.to_dict() for section in sections],
                "total_sections": len(sections),
                "coded_sections": len([s for s in sections if s.is_coded_section]),
                "total_clinical_codes": sum(len(s.clinical_codes) for s in sections),
                "has_administrative_data": bool(patient_identity),
                "parsing_method": "JSON_Bundle",
                "json_bundle": json_bundle,  # Include for debugging
            }

            logger.info(
                f"Parsing complete: {len(sections)} sections, "
                f"{result['total_clinical_codes']} clinical codes"
            )

            return result

        except Exception as e:
            logger.error(f"Error parsing CDA file: {e}")
            raise

    def _xml_to_json_bundle(self, file_path: str) -> Dict[str, Any]:
        """
        Convert CDA XML to JSON bundle

        Args:
            file_path: Path to XML file

        Returns:
            JSON representation of the XML
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                xml_content = file.read()

            # Convert XML to dict, preserving structure
            json_bundle = xmltodict.parse(
                xml_content, process_namespaces=True, namespace_separator="__"
            )

            logger.debug(
                f"XML converted to JSON bundle with keys: {list(json_bundle.keys())}"
            )
            return json_bundle

        except Exception as e:
            logger.error(f"Error converting XML to JSON: {e}")
            raise

    def _extract_patient_identity(self, json_bundle: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract patient identity from JSON bundle using multiple patterns

        Args:
            json_bundle: JSON representation of CDA

        Returns:
            Patient identity data
        """
        patient_identity = {}

        try:
            # Find ClinicalDocument root
            clinical_doc = self._find_clinical_document(json_bundle)
            if not clinical_doc:
                return patient_identity

            # Look for patient data in various locations
            patient_patterns = [
                "recordTarget.patientRole.patient",
                "recordTarget.0.patientRole.patient",
                "recordTarget.patientRole.0.patient",
            ]

            for pattern in patient_patterns:
                patient_data = self._get_nested_value(clinical_doc, pattern)
                if patient_data:
                    break

            if patient_data:
                # Extract name
                name_data = patient_data.get("name", {})
                if isinstance(name_data, list):
                    name_data = name_data[0] if name_data else {}

                patient_identity["given_name"] = self._extract_text_value(
                    name_data.get("given")
                )
                patient_identity["family_name"] = self._extract_text_value(
                    name_data.get("family")
                )

                # Extract birth date
                birth_time = patient_data.get("birthTime", {})
                if isinstance(birth_time, dict):
                    patient_identity["birth_date"] = birth_time.get("@value", "")

                # Extract gender
                gender = patient_data.get("administrativeGenderCode", {})
                if isinstance(gender, dict):
                    patient_identity["gender"] = gender.get("@code", "")

        except Exception as e:
            logger.error(f"Error extracting patient identity: {e}")

        return patient_identity

    def _extract_clinical_sections(
        self, json_bundle: Dict[str, Any]
    ) -> List[ClinicalSection]:
        """
        Extract clinical sections from JSON bundle

        Args:
            json_bundle: JSON representation of CDA

        Returns:
            List of clinical sections
        """
        sections = []

        try:
            clinical_doc = self._find_clinical_document(json_bundle)
            if not clinical_doc:
                return sections

            # Find sections in various patterns
            section_patterns = [
                "component.structuredBody.component",
                "component.0.structuredBody.component",
                "component.structuredBody.component.0",
            ]

            section_data = None
            for pattern in section_patterns:
                section_data = self._get_nested_value(clinical_doc, pattern)
                if section_data:
                    break

            if not section_data:
                return sections

            # Ensure we have a list
            if not isinstance(section_data, list):
                section_data = [section_data]

            # Process each section
            for component in section_data:
                if not isinstance(component, dict):
                    continue

                section = component.get("section", {})
                if not section:
                    continue

                clinical_section = self._process_section(section)
                if clinical_section:
                    sections.append(clinical_section)

        except Exception as e:
            logger.error(f"Error extracting clinical sections: {e}")

        return sections

    def _process_section(
        self, section_data: Dict[str, Any]
    ) -> Optional[ClinicalSection]:
        """
        Process a single section from the JSON bundle

        Args:
            section_data: Section data from JSON bundle

        Returns:
            ClinicalSection object or None
        """
        try:
            # Extract section title
            title = self._extract_section_title(section_data)

            # Extract section code
            section_code_data = section_data.get("code", {})
            section_code = section_code_data.get("@code", "")
            system = section_code_data.get("@codeSystem", "")

            # Extract text content
            content = self._extract_section_content(section_data)

            # Extract clinical codes from entries
            clinical_codes = self._extract_codes_from_section(section_data)

            # Create section
            clinical_section = ClinicalSection(
                title=title,
                section_code=section_code,
                system=system,
                content=content,
                clinical_codes=clinical_codes,
                is_coded_section=len(clinical_codes) > 0,
            )

            return clinical_section

        except Exception as e:
            logger.error(f"Error processing section: {e}")
            return None

    def _extract_codes_from_section(
        self, section_data: Dict[str, Any]
    ) -> List[ClinicalCode]:
        """
        Extract clinical codes from section using multiple patterns

        Args:
            section_data: Section data from JSON bundle

        Returns:
            List of clinical codes
        """
        codes = []

        try:
            # Look for entries
            entries = section_data.get("entry", [])
            if not isinstance(entries, list):
                entries = [entries] if entries else []

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                # Extract codes from this entry
                entry_codes = self._extract_codes_from_entry(entry)
                codes.extend(entry_codes)

        except Exception as e:
            logger.error(f"Error extracting codes from section: {e}")

        return codes

    def _extract_codes_from_entry(
        self, entry_data: Dict[str, Any]
    ) -> List[ClinicalCode]:
        """
        Extract codes from a single entry using recursive search

        Args:
            entry_data: Entry data from JSON bundle

        Returns:
            List of clinical codes
        """
        codes = []

        try:
            # Recursively search for coded elements
            self._recursive_code_search(entry_data, codes)

        except Exception as e:
            logger.error(f"Error extracting codes from entry: {e}")

        return codes

    def _recursive_code_search(
        self, data: Any, codes: List[ClinicalCode], path: str = ""
    ):
        """
        Recursively search for coded elements in the data structure

        Args:
            data: Data to search
            codes: List to append found codes to
            path: Current path for debugging
        """
        if isinstance(data, dict):
            # Check if this dict represents a coded element
            if self._is_coded_element(data):
                code = self._extract_clinical_code(data)
                if code:
                    codes.append(code)

            # Recurse into nested objects
            for key, value in data.items():
                self._recursive_code_search(value, codes, f"{path}.{key}")

        elif isinstance(data, list):
            # Recurse into list items
            for i, item in enumerate(data):
                self._recursive_code_search(item, codes, f"{path}[{i}]")

    def _is_coded_element(self, element: Dict[str, Any]) -> bool:
        """
        Check if an element represents a clinical code

        Args:
            element: Element to check

        Returns:
            True if element has coding information
        """
        # Check for code attributes
        has_code = "@code" in element or "code" in element
        has_system = "@codeSystem" in element or "codeSystem" in element
        has_value = "@value" in element or "value" in element

        return has_code or (has_system and has_value)

    def _extract_clinical_code(self, element: Dict[str, Any]) -> Optional[ClinicalCode]:
        """
        Extract clinical code from coded element

        Args:
            element: Coded element

        Returns:
            ClinicalCode object or None
        """
        try:
            # Extract code
            code = element.get("@code") or element.get("code", "")
            if not code:
                code = element.get("@value") or element.get("value", "")

            # Extract system
            system = element.get("@codeSystem") or element.get("codeSystem", "")

            # Extract display
            display = element.get("@displayName") or element.get("displayName", "")

            # Extract original text
            original_text = ""
            if "originalText" in element:
                orig_text = element["originalText"]
                if isinstance(orig_text, dict):
                    original_text = orig_text.get("#text", "")
                else:
                    original_text = str(orig_text)

            if not code:
                return None

            # Map system to name
            system_info = self.code_system_mappings.get(
                system, {"name": system, "short": "OTHER"}
            )

            return ClinicalCode(
                code=code,
                system=system,
                system_name=system_info["short"],
                display=display,
                original_text=original_text,
            )

        except Exception as e:
            logger.error(f"Error extracting clinical code: {e}")
            return None

    # Utility methods
    def _find_clinical_document(
        self, json_bundle: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find the ClinicalDocument root in the JSON bundle"""
        for key, value in json_bundle.items():
            if "ClinicalDocument" in key or "clinicalDocument" in key:
                return value
        return json_bundle  # Fallback to root

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation path"""
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _extract_text_value(self, data: Any) -> str:
        """Extract text value from various formats"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return data.get("#text", data.get("@value", ""))
        elif isinstance(data, list) and data:
            return self._extract_text_value(data[0])
        return ""

    def _extract_section_title(self, section_data: Dict[str, Any]) -> str:
        """Extract section title"""
        title = section_data.get("title", {})
        if isinstance(title, dict):
            return title.get("#text", "")
        return str(title) if title else ""

    def _extract_section_content(self, section_data: Dict[str, Any]) -> str:
        """Extract section text content"""
        text_data = section_data.get("text", {})
        if isinstance(text_data, dict):
            return text_data.get("#text", "")
        return str(text_data) if text_data else ""


# Test function
def test_json_bundle_parser():
    """Test the JSON bundle parser"""
    parser = CDAJSONBundleParser()

    # Test with Italian CDA
    italian_cda_path = "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    try:
        result = parser.parse_cda_file(italian_cda_path)
        print(
            f"✅ JSON Bundle Parser: {result['total_sections']} sections, {result['total_clinical_codes']} codes"
        )
        return result
    except Exception as e:
        print(f"❌ JSON Bundle Parser Error: {e}")
        return None


if __name__ == "__main__":
    test_json_bundle_parser()
