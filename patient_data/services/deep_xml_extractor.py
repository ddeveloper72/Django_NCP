"""
Deep XML Endpoint Extractor
Discovers and extracts all available data endpoints from CDA XML
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DeepXMLExtractor:
    """
    Extract comprehensive data from XML by discovering all available endpoints
    """

    def __init__(self):
        self.namespaces = {
            "hl7": "urn:hl7-org:v3",
            "pharm": "urn:hl7-org:pharm",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }
        self.discovered_endpoints = {}
        self.code_systems = {
            "2.16.840.1.113883.6.96": "SNOMED CT",
            "2.16.840.1.113883.6.1": "LOINC",
            "2.16.840.1.113883.6.103": "ICD-9-CM",
            "2.16.840.1.113883.6.90": "ICD-10-CM",
            "2.16.840.1.113883.6.73": "ATC",
            "1.3.6.1.4.1.12559.11.10.1.3.1.44.2": "eHDSI",
        }

    def extract_all_endpoints(
        self, xml_content: str, section_code: str, patient_id: str
    ) -> Dict[str, Any]:
        """
        Comprehensive extraction of all available endpoints in XML section

        Args:
            xml_content: Full CDA XML content
            section_code: LOINC section code (e.g., '11450-4')
            patient_id: Patient identifier for logging

        Returns:
            Dictionary with all discovered endpoints and their data
        """
        try:
            root = ET.fromstring(xml_content)

            # Find the specific section
            section_xpath = f".//hl7:section[hl7:code[@code='{section_code}']]"
            sections = root.findall(section_xpath, self.namespaces)

            all_endpoints = {
                "section_code": section_code,
                "patient_id": patient_id,
                "entries": [],
                "discovered_fields": set(),
                "endpoint_summary": {},
                "extraction_timestamp": datetime.now().isoformat(),
            }

            for section in sections:
                logger.info(f"[SEARCH] Deep extraction for section {section_code}")

                # Extract all entries in this section
                entries = section.findall(".//hl7:entry", self.namespaces)

                for i, entry in enumerate(entries):
                    entry_data = self._extract_entry_endpoints(entry, f"entry_{i}")
                    all_endpoints["entries"].append(entry_data)

                    # Track discovered field patterns
                    for field_name in entry_data.keys():
                        all_endpoints["discovered_fields"].add(field_name)

            # Convert set to list for JSON serialization
            all_endpoints["discovered_fields"] = list(
                all_endpoints["discovered_fields"]
            )

            # Create endpoint summary
            all_endpoints["endpoint_summary"] = self._create_endpoint_summary(
                all_endpoints["entries"]
            )

            logger.info(
                f"[SUCCESS] Extracted {len(all_endpoints['entries'])} entries with {len(all_endpoints['discovered_fields'])} unique fields"
            )

            return all_endpoints

        except Exception as e:
            logger.error(f"[ERROR] Deep extraction failed: {e}")
            return {"error": str(e), "entries": []}

    def _extract_entry_endpoints(
        self, entry_elem: ET.Element, entry_id: str
    ) -> Dict[str, Any]:
        """Extract all possible endpoints from a single entry"""

        endpoints = {
            "entry_id": entry_id,
            "entry_type": entry_elem.get("typeCode", "unknown"),
        }

        # Strategy 1: Extract all elements with codes
        self._extract_coded_elements(entry_elem, endpoints)

        # Strategy 2: Extract all text values
        self._extract_text_elements(entry_elem, endpoints)

        # Strategy 3: Extract all time elements
        self._extract_time_elements(entry_elem, endpoints)

        # Strategy 4: Extract all status elements
        self._extract_status_elements(entry_elem, endpoints)

        # Strategy 5: Extract all quantity/value elements
        self._extract_value_elements(entry_elem, endpoints)

        # Strategy 6: Extract relationship structures
        self._extract_relationships(entry_elem, endpoints)

        return endpoints

    def _extract_coded_elements(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract all elements that contain medical codes"""

        # Find all code elements
        codes = elem.findall(".//hl7:code", self.namespaces)
        for i, code in enumerate(codes):
            code_value = code.get("code")
            display_name = code.get("displayName")
            code_system = code.get("codeSystem")
            system_name = self.code_systems.get(code_system, "Unknown System")

            if code_value:
                field_key = f"code_{i}_{code_value}"
                endpoints[field_key] = {
                    "value": code_value,
                    "display_name": display_name,
                    "code_system": code_system,
                    "system_name": system_name,
                    "xpath": f".//hl7:code[@code='{code_value}']",
                    "type": "coded_value",
                }

        # Find all value elements with codes
        values = elem.findall(".//hl7:value[@code]", self.namespaces)
        for i, value in enumerate(values):
            code_value = value.get("code")
            display_name = value.get("displayName")
            code_system = value.get("codeSystem")

            if code_value:
                field_key = f"value_code_{i}_{code_value}"
                endpoints[field_key] = {
                    "value": code_value,
                    "display_name": display_name,
                    "code_system": code_system,
                    "system_name": self.code_systems.get(code_system, "Unknown System"),
                    "xpath": f".//hl7:value[@code='{code_value}']",
                    "type": "value_code",
                }

    def _extract_text_elements(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract all text content and originalText elements"""

        # Extract originalText elements
        original_texts = elem.findall(".//hl7:originalText", self.namespaces)
        for i, text_elem in enumerate(original_texts):
            if text_elem.text:
                endpoints[f"original_text_{i}"] = {
                    "value": text_elem.text.strip(),
                    "xpath": ".//hl7:originalText",
                    "type": "original_text",
                }

        # Extract translation elements
        translations = elem.findall(".//hl7:translation", self.namespaces)
        for i, trans in enumerate(translations):
            display_name = trans.get("displayName")
            if display_name:
                endpoints[f"translation_{i}"] = {
                    "value": display_name,
                    "code": trans.get("code"),
                    "xpath": ".//hl7:translation",
                    "type": "translation",
                }

    def _extract_time_elements(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract all time-related elements"""

        # Extract effectiveTime elements
        effective_times = elem.findall(".//hl7:effectiveTime", self.namespaces)
        for i, time_elem in enumerate(effective_times):
            # Single value
            time_value = time_elem.get("value")
            if time_value:
                endpoints[f"effective_time_{i}"] = {
                    "value": time_value,
                    "formatted": self._format_hl7_date(time_value),
                    "xpath": ".//hl7:effectiveTime/@value",
                    "type": "datetime",
                }

            # Low value
            low_elem = time_elem.find("hl7:low", self.namespaces)
            if low_elem is not None:
                low_value = low_elem.get("value")
                if low_value:
                    endpoints[f"effective_time_low_{i}"] = {
                        "value": low_value,
                        "formatted": self._format_hl7_date(low_value),
                        "xpath": ".//hl7:effectiveTime/hl7:low/@value",
                        "type": "datetime_start",
                    }

            # High value
            high_elem = time_elem.find("hl7:high", self.namespaces)
            if high_elem is not None:
                high_value = high_elem.get("value")
                if high_value:
                    endpoints[f"effective_time_high_{i}"] = {
                        "value": high_value,
                        "formatted": self._format_hl7_date(high_value),
                        "xpath": ".//hl7:effectiveTime/hl7:high/@value",
                        "type": "datetime_end",
                    }

    def _extract_status_elements(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract all status-related elements"""

        # Status codes
        status_codes = elem.findall(".//hl7:statusCode", self.namespaces)
        for i, status in enumerate(status_codes):
            code_value = status.get("code")
            if code_value:
                endpoints[f"status_code_{i}"] = {
                    "value": code_value,
                    "xpath": ".//hl7:statusCode/@code",
                    "type": "status",
                }

        # Class codes
        for class_elem in elem.iter():
            class_code = class_elem.get("classCode")
            mood_code = class_elem.get("moodCode")

            if class_code:
                tag_name = (
                    class_elem.tag.split("}")[-1]
                    if "}" in class_elem.tag
                    else class_elem.tag
                )
                endpoints[f"{tag_name}_class_code"] = {
                    "value": class_code,
                    "xpath": f".//{tag_name}/@classCode",
                    "type": "class_code",
                }

            if mood_code:
                tag_name = (
                    class_elem.tag.split("}")[-1]
                    if "}" in class_elem.tag
                    else class_elem.tag
                )
                endpoints[f"{tag_name}_mood_code"] = {
                    "value": mood_code,
                    "xpath": f".//{tag_name}/@moodCode",
                    "type": "mood_code",
                }

    def _extract_value_elements(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract numeric values, quantities, and measurements"""

        values = elem.findall(".//hl7:value", self.namespaces)
        for i, value_elem in enumerate(values):
            # Numeric values
            if value_elem.get("value"):
                endpoints[f"numeric_value_{i}"] = {
                    "value": value_elem.get("value"),
                    "unit": value_elem.get("unit"),
                    "xpath": ".//hl7:value/@value",
                    "type": "numeric",
                }

        # Quantities
        quantities = elem.findall(".//hl7:quantity", self.namespaces)
        for i, qty in enumerate(quantities):
            if qty.get("value"):
                endpoints[f"quantity_{i}"] = {
                    "value": qty.get("value"),
                    "unit": qty.get("unit"),
                    "xpath": ".//hl7:quantity",
                    "type": "quantity",
                }

    def _extract_relationships(self, elem: ET.Element, endpoints: Dict[str, Any]):
        """Extract entryRelationship and participant structures"""

        # Entry relationships
        relationships = elem.findall(".//hl7:entryRelationship", self.namespaces)
        for i, rel in enumerate(relationships):
            type_code = rel.get("typeCode")
            if type_code:
                endpoints[f"relationship_{i}_type"] = {
                    "value": type_code,
                    "xpath": ".//hl7:entryRelationship/@typeCode",
                    "type": "relationship_type",
                }

        # Participants
        participants = elem.findall(".//hl7:participant", self.namespaces)
        for i, participant in enumerate(participants):
            type_code = participant.get("typeCode")
            if type_code:
                endpoints[f"participant_{i}_type"] = {
                    "value": type_code,
                    "xpath": ".//hl7:participant/@typeCode",
                    "type": "participant_type",
                }

    def _create_endpoint_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of discovered endpoints for admin interface"""

        summary = {
            "total_entries": len(entries),
            "field_frequency": {},
            "data_types": set(),
            "code_systems": set(),
            "suggested_columns": [],
        }

        # Count field frequency across all entries
        for entry in entries:
            for field_name, field_data in entry.items():
                if field_name not in ["entry_id", "entry_type"]:
                    summary["field_frequency"][field_name] = (
                        summary["field_frequency"].get(field_name, 0) + 1
                    )

                    if isinstance(field_data, dict):
                        data_type = field_data.get("type", "unknown")
                        summary["data_types"].add(data_type)

                        system_name = field_data.get("system_name")
                        if system_name:
                            summary["code_systems"].add(system_name)

        # Convert sets to lists
        summary["data_types"] = list(summary["data_types"])
        summary["code_systems"] = list(summary["code_systems"])

        # Suggest columns based on frequency (fields present in >50% of entries)
        threshold = len(entries) * 0.5
        for field_name, frequency in summary["field_frequency"].items():
            if frequency >= threshold:
                summary["suggested_columns"].append(
                    {
                        "field_name": field_name,
                        "frequency": frequency,
                        "coverage": f"{(frequency/len(entries)*100):.1f}%",
                    }
                )

        return summary

    def _format_hl7_date(self, hl7_date: str) -> str:
        """Format HL7 date string for display"""
        if not hl7_date:
            return "Not specified"

        # Handle HL7 date format (YYYYMMDDHHMMSS+ZZZZ)
        try:
            if len(hl7_date) >= 8:
                year = hl7_date[:4]
                month = hl7_date[4:6]
                day = hl7_date[6:8]
                return f"{day}/{month}/{year}"
        except:
            pass

        return hl7_date
