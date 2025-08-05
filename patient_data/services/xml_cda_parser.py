"""
XML CDA Parser
Simple, focused parser for extracting clinical sections from XML CDA documents
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class XMLCDAParser:
    """
    Simple parser for extracting clinical sections from XML CDA documents
    Focuses on getting sections quickly without complex translation workflows
    """

    def __init__(self):
        # CDA namespace mapping
        self.namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

    def extract_clinical_sections(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Extract clinical sections from XML CDA content

        Args:
            xml_content: Raw XML CDA content

        Returns:
            List of clinical sections with text content
        """
        sections = []

        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Register namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)

            # Find all sections in structuredBody
            section_elements = root.findall(
                ".//cda:structuredBody//cda:section", self.namespaces
            )

            logger.info(f"Found {len(section_elements)} sections in CDA document")

            for i, section in enumerate(section_elements):
                section_data = self._parse_section(section, i)
                if section_data:
                    sections.append(section_data)

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        except Exception as e:
            logger.error(f"Error extracting clinical sections: {e}")

        return sections

    def _parse_section(self, section_element, index: int) -> Optional[Dict[str, Any]]:
        """Parse individual section element"""
        try:
            # Get section title
            title_elem = section_element.find("cda:title", self.namespaces)
            title = (
                title_elem.text.strip()
                if title_elem is not None
                else f"Section {index + 1}"
            )

            # Get section code for identification
            code_elem = section_element.find("cda:code", self.namespaces)
            section_code = ""
            if code_elem is not None:
                code = code_elem.get("code", "")
                display_name = code_elem.get("displayName", "")
                code_system = code_elem.get("codeSystemName", "")
                section_code = (
                    f"{code} ({code_system})" if code and code_system else code
                )

            # Get section text content
            text_elem = section_element.find("cda:text", self.namespaces)
            text_content = (
                self._extract_text_content(text_elem) if text_elem is not None else ""
            )

            # Count medical terms (simple heuristic)
            medical_terms_count = self._count_medical_terms(text_content)

            # Check if section has coded entries
            entries = section_element.findall(".//cda:entry", self.namespaces)
            has_coded_elements = len(entries) > 0

            return {
                "id": f"section_{index}",
                "title": title,
                "section_code": section_code,
                "original_content": text_content,
                "translated_content": text_content,  # For now, no translation
                "has_coded_elements": has_coded_elements,
                "medical_terms_count": medical_terms_count,
                "entries_count": len(entries),
            }

        except Exception as e:
            logger.error(f"Error parsing section {index}: {e}")
            return None

    def _extract_text_content(self, text_element) -> str:
        """Extract readable text content from CDA text element"""
        if text_element is None:
            return ""

        # Convert element to string and clean up
        content_parts = []

        # Handle tables
        tables = text_element.findall(".//table")
        for table in tables:
            table_text = self._extract_table_text(table)
            if table_text:
                content_parts.append(table_text)

        # Handle other text content
        for elem in text_element.iter():
            if elem.text and elem.text.strip():
                # Skip content that's already in tables
                if not any(elem in table for table in tables):
                    content_parts.append(elem.text.strip())

        return "\n".join(content_parts) if content_parts else ""

    def _extract_table_text(self, table_element) -> str:
        """Extract text from HTML table in CDA text"""
        rows = []

        # Get headers
        headers = []
        for th in table_element.findall(".//th"):
            if th.text:
                headers.append(th.text.strip())

        if headers:
            rows.append(" | ".join(headers))
            rows.append("-" * len(" | ".join(headers)))

        # Get data rows
        for tr in table_element.findall(".//tr"):
            cells = []
            for td in tr.findall(".//td"):
                cell_text = ""
                # Get all text content including nested elements
                for elem in td.iter():
                    if elem.text:
                        cell_text += elem.text.strip() + " "
                cells.append(cell_text.strip())

            if cells and any(cell for cell in cells):  # Skip empty rows
                rows.append(" | ".join(cells))

        return "\n".join(rows) if rows else ""

    def _count_medical_terms(self, text: str) -> int:
        """Simple heuristic to count potential medical terms"""
        if not text:
            return 0

        # Look for medical indicators
        medical_indicators = [
            "allergia",
            "allergic",
            "medication",
            "drug",
            "diagnosis",
            "symptom",
            "condition",
            "treatment",
            "procedure",
            "mg",
            "ml",
            "tablet",
            "dose",
            "daily",
            "chronic",
            "acute",
            "eczema",
            "farmaco",
            "medicina",
            "diagnosi",
            "sintomo",
            "terapia",
        ]

        text_lower = text.lower()
        count = 0
        for indicator in medical_indicators:
            if indicator in text_lower:
                count += 1

        return min(count, 10)  # Cap at reasonable number

    def get_section_summary(self, xml_content: str) -> Dict[str, Any]:
        """Get quick summary of sections without full parsing"""
        try:
            root = ET.fromstring(xml_content)
            sections = root.findall(
                ".//cda:structuredBody//cda:section", self.namespaces
            )

            return {
                "total_sections": len(sections),
                "has_clinical_content": len(sections) > 0,
                "content_type": "xml_cda",
            }
        except Exception as e:
            logger.error(f"Error getting section summary: {e}")
            return {
                "total_sections": 0,
                "has_clinical_content": False,
                "content_type": "error",
            }
