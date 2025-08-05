"""
CDA Translation Manager
Manages translation state and rendering for CDA documents in the viewer
"""

import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils.translation import gettext as _

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BeautifulSoup = None
    BEAUTIFULSOUP_AVAILABLE = False
    logging.warning(
        "BeautifulSoup4 not available. HTML CDA processing will be limited."
    )

from .enhanced_cda_translation_service import EnhancedCDATranslationService
from .enhanced_cda_xml_parser import EnhancedCDAXMLParser
from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger(__name__)


class CDATranslationManager:
    """
    Manages translation functionality for CDA document viewer
    Handles section-level translations, terminology mapping, and rendering
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self.translation_service = EnhancedCDATranslationService(target_language)
        self.terminology_translator = TerminologyTranslator(target_language)
        self.xml_parser = EnhancedCDAXMLParser()

    def process_cda_for_viewer(
        self, cda_content: str, source_language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Process CDA content for the document viewer with translation capabilities

        Args:
            cda_content: Raw CDA HTML or XML content
            source_language: Source language code

        Returns:
            Dictionary with processed content for viewer rendering
        """
        try:
            # Check if content is HTML (transformed) or XML (raw)
            if self._is_html_content(cda_content):
                return self._process_html_cda(cda_content, source_language)
            else:
                return self._process_xml_cda(cda_content, source_language)

        except Exception as e:
            logger.error(f"Error processing CDA for viewer: {e}")
            return self._create_error_response(str(e))

    def _is_html_content(self, content: str) -> bool:
        """Check if content is HTML (XSLT transformed) rather than raw XML"""
        return (
            content.strip().lower().startswith("<!doctype html")
            or "<html" in content.lower()
        )

    def _process_html_cda(
        self, html_content: str, source_language: str
    ) -> Dict[str, Any]:
        """
        Process HTML-transformed CDA content with translation features
        This handles the Luxembourg-style HTML documents
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.error("BeautifulSoup4 not available for HTML processing")
            return self._create_error_response(
                "HTML processing not available - BeautifulSoup4 required"
            )

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract document metadata
            document_info = self._extract_html_document_info(soup)

            # Extract patient information
            patient_info = self._extract_html_patient_info(soup)

            # Extract clinical sections
            clinical_sections = self._extract_html_clinical_sections(
                soup, source_language
            )

            # Generate translation toggles for each section
            translation_controls = self._generate_translation_controls(
                clinical_sections
            )

            return {
                "success": True,
                "content_type": "html",
                "document_info": document_info,
                "patient_info": patient_info,
                "clinical_sections": clinical_sections,
                "translation_controls": translation_controls,
                "source_language": source_language,
                "target_language": self.target_language,
                "original_content": html_content,
                "translation_available": True,
            }

        except Exception as e:
            logger.error(f"Error processing HTML CDA: {e}")
            return self._create_error_response(f"HTML processing error: {e}")

    def _extract_html_document_info(self, soup) -> Dict[str, str]:
        """Extract document metadata from HTML CDA"""
        info = {}

        # Document title
        title_elem = soup.find("title")
        if title_elem:
            info["title"] = title_elem.get_text().strip()

        # Creation date from header table
        header_table = soup.find("table", class_="header_table")
        if header_table:
            rows = header_table.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    if "Creation Date" in cells[0].get_text():
                        info["creation_date"] = cells[1].get_text().strip()
                    elif "Last Update" in cells[0].get_text():
                        info["last_update"] = cells[1].get_text().strip()
                    elif "Original Document Language" in cells[0].get_text():
                        info["original_language"] = cells[1].get_text().strip()

        return info

    def _extract_html_patient_info(self, soup) -> Dict[str, str]:
        """Extract patient information from HTML CDA"""
        patient_info = {}

        # Look for patient information in header table
        header_table = soup.find("table", class_="header_table")
        if header_table:
            # Find patient name
            name_cells = header_table.find_all("td")
            for i, cell in enumerate(name_cells):
                text = cell.get_text().strip()
                if text and len(text) > 2:  # Likely a name
                    # Check if previous cell was a header
                    prev_cells = header_table.find_all("th")
                    for header in prev_cells:
                        if "Family Name" in header.get_text():
                            patient_info["family_name"] = text
                        elif "Given Name" in header.get_text():
                            patient_info["given_name"] = text

            # Extract identifiers and other info
            rows = header_table.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    header_text = cells[0].get_text().strip()
                    value_text = cells[1].get_text().strip()

                    if "Primary Patient Identifier" in header_text:
                        patient_info["primary_id"] = value_text
                    elif "Secondary Patient Identifier" in header_text:
                        patient_info["secondary_id"] = value_text
                    elif "Gender" in header_text:
                        patient_info["gender"] = value_text
                    elif "Date of Birth" in header_text:
                        patient_info["birth_date"] = value_text

        return patient_info

    def _extract_html_clinical_sections(
        self, soup, source_language: str
    ) -> List[Dict[str, Any]]:
        """Extract clinical sections from HTML CDA with translation and coded elements"""
        sections = []

        # Find all collapsible sections (clinical content)
        collapsible_sections = soup.find_all("div", class_="wrap-collapsible")

        for section_div in collapsible_sections:
            # Get section title from label
            label = section_div.find(
                "label", class_=["lbl-toggle-title", "lbl-toggle-main"]
            )
            if not label:
                continue

            section_title = label.get_text().strip()
            section_id = label.get("for", f"section_{len(sections)}")

            # Extract original content
            content_div = section_div.find(
                "div", class_=["collapsible-content-title", "collapsible-content-main"]
            )
            original_content = ""
            if content_div:
                original_content = str(content_div)

            # Check for existing translation toggles
            translation_toggles = section_div.find_all(
                "button", class_=["toggle-button-translated", "toggle-button-original"]
            )
            has_translation_ui = len(translation_toggles) > 0

            # Extract narrative content for translation
            narrative_content = self._extract_narrative_from_section(content_div)

            # Extract coded elements (SNOMED CT, ICD-10, LOINC, ATC, etc.)
            coded_elements = self._extract_coded_elements_from_section(content_div)

            # Translate both narrative and coded elements
            translated_content = ""
            translated_codes = []

            if narrative_content:
                try:
                    # Use the enhanced terminology translator for medical content
                    translation_result = (
                        self.terminology_translator.translate_clinical_document(
                            narrative_content, source_language
                        )
                    )
                    translated_content = translation_result.get(
                        "content", narrative_content
                    )

                    # Get terminology mappings from the translation result
                    terminology_map = translation_result.get("terminology_map", {})

                except Exception as e:
                    logger.warning(
                        f"Failed to translate section '{section_title}': {e}"
                    )
                    translated_content = narrative_content

            # Translate coded elements using terminology services
            if coded_elements:
                translated_codes = self._translate_coded_elements(
                    coded_elements, source_language
                )

            section_data = {
                "id": section_id,
                "title": section_title,
                "original_content": original_content,
                "narrative_content": narrative_content,
                "translated_content": translated_content,
                "coded_elements": coded_elements,
                "translated_codes": translated_codes,
                "has_translation_ui": has_translation_ui,
                "translation_quality": self._assess_section_translation_quality(
                    narrative_content, translated_content
                ),
                "terminology_mappings": self._extract_terminology_mappings_enhanced(
                    narrative_content, coded_elements
                ),
            }

            sections.append(section_data)

        return sections

    def _extract_narrative_from_section(self, content_div) -> str:
        """Extract narrative text content from a section for translation"""
        if not content_div:
            return ""

        # Look for narrative tables and content
        narrative_text = []

        # Extract from tables
        tables = content_div.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                for cell in row.find_all(["td", "th"]):
                    text = cell.get_text().strip()
                    if text and len(text) > 3:  # Skip short labels
                        narrative_text.append(text)

        # Extract from paragraphs and divs
        for elem in content_div.find_all(["p", "div", "span"]):
            text = elem.get_text().strip()
            if text and len(text) > 3:
                narrative_text.append(text)

        return "\n".join(narrative_text)

    def _generate_translation_controls(
        self, clinical_sections: List[Dict]
    ) -> Dict[str, Any]:
        """Generate translation control UI for sections"""
        controls = {
            "global_toggle": True,
            "section_toggles": [],
            "languages": [
                {"code": "fr", "name": "French", "flag": "🇫🇷"},
                {"code": "en", "name": "English", "flag": "🇬🇧"},
                {"code": "de", "name": "German", "flag": "🇩🇪"},
                {"code": "es", "name": "Spanish", "flag": "🇪🇸"},
                {"code": "it", "name": "Italian", "flag": "🇮🇹"},
            ],
        }

        for section in clinical_sections:
            section_control = {
                "section_id": section["id"],
                "title": section["title"],
                "has_translation": bool(section["translated_content"]),
                "quality": section["translation_quality"],
                "terminology_count": len(section["terminology_mappings"]),
            }
            controls["section_toggles"].append(section_control)

        return controls

    def _assess_section_translation_quality(
        self, original: str, translated: str
    ) -> str:
        """Assess translation quality for a section"""
        if not translated or translated == original:
            return "none"

        # Simple quality assessment based on length and content differences
        if len(translated) < len(original) * 0.5:
            return "poor"
        elif len(translated) > len(original) * 2:
            return "poor"
        else:
            return "good"

    def _extract_terminology_mappings(self, content: str) -> List[Dict[str, str]]:
        """Extract medical terminology that can be mapped/translated"""
        mappings = []

        # Use terminology translator to find medical terms
        try:
            medical_terms = self.terminology_translator.extract_medical_terms(content)
            for term in medical_terms:
                mapping = {
                    "original": term["original"],
                    "translated": term.get("translated", ""),
                    "category": term.get("category", "general"),
                    "confidence": term.get("confidence", 0.8),
                }
                mappings.append(mapping)
        except Exception as e:
            logger.warning(f"Failed to extract terminology mappings: {e}")

        return mappings

    def _extract_terminology_mappings_enhanced(
        self, narrative_content: str, coded_elements: List[Dict]
    ) -> Dict[str, Any]:
        """Enhanced terminology mapping extraction with coded elements integration"""
        mappings = {
            "narrative_mappings": self._extract_terminology_mappings(narrative_content),
            "coded_mappings": [],
            "cross_references": [],
        }

        # Process coded elements for terminology mappings
        for coded_element in coded_elements:
            code = coded_element.get("code")
            code_system = coded_element.get("codeSystem")
            display_name = coded_element.get("displayName", "")

            try:
                # Get concept mapping from terminology services
                concept_mapping = self.terminology_translator.get_concept_mapping(
                    code, code_system
                )

                if concept_mapping:
                    mappings["coded_mappings"].append(
                        {
                            "code": code,
                            "codeSystem": code_system,
                            "originalDisplay": display_name,
                            "conceptMapping": concept_mapping,
                            "synonyms": concept_mapping.get("synonyms", []),
                            "related_concepts": concept_mapping.get(
                                "related_concepts", []
                            ),
                        }
                    )

                    # Look for cross-references between narrative and codes
                    if display_name.lower() in narrative_content.lower():
                        mappings["cross_references"].append(
                            {
                                "code": code,
                                "codeSystem": code_system,
                                "narrative_context": self._extract_narrative_context(
                                    narrative_content, display_name
                                ),
                            }
                        )

            except Exception as e:
                logger.warning(f"Failed to get concept mapping for {code}: {e}")

        return mappings

    def _extract_narrative_context(self, narrative: str, term: str) -> str:
        """Extract context around a term in narrative text"""
        import re

        # Find the term in the narrative (case insensitive)
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        match = pattern.search(narrative)

        if match:
            start = max(0, match.start() - 100)
            end = min(len(narrative), match.end() + 100)
            return narrative[start:end].strip()

        return ""

    def _extract_coded_elements_from_section(self, content_div) -> List[Dict[str, Any]]:
        """Extract coded elements (SNOMED CT, ICD-10, LOINC, ATC, etc.) from CDA section"""
        coded_elements = []

        if not content_div:
            return coded_elements

        # Look for various coded element patterns in the HTML
        # Pattern 1: Direct code attributes
        coded_attrs = [
            "data-code",
            "data-snomed",
            "data-icd10",
            "data-loinc",
            "data-atc",
        ]
        for attr in coded_attrs:
            elements = content_div.find_all(attrs={attr: True})
            for elem in elements:
                code_value = elem.get(attr)
                code_system = attr.replace("data-", "").upper()
                display_name = elem.get_text().strip()

                coded_elements.append(
                    {
                        "code": code_value,
                        "codeSystem": code_system,
                        "displayName": display_name,
                        "element_type": elem.name,
                        "context": self._get_element_context(elem),
                    }
                )

        # Pattern 2: Look for code tables or structured data
        code_tables = content_div.find_all(
            "table", class_=["codes", "terminology", "diagnoses"]
        )
        for table in code_tables:
            rows = table.find_all("tr")
            for row in rows[1:]:  # Skip header
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    code = cells[0].get_text().strip()
                    display = cells[1].get_text().strip()
                    code_system = "UNKNOWN"

                    # Try to identify code system from code pattern
                    if self._is_snomed_code(code):
                        code_system = "SNOMED_CT"
                    elif self._is_icd10_code(code):
                        code_system = "ICD10"
                    elif self._is_loinc_code(code):
                        code_system = "LOINC"
                    elif self._is_atc_code(code):
                        code_system = "ATC"

                    coded_elements.append(
                        {
                            "code": code,
                            "codeSystem": code_system,
                            "displayName": display,
                            "element_type": "table_entry",
                            "context": "tabular_data",
                        }
                    )

        # Pattern 3: Look for inline code references in text
        text_content = content_div.get_text()
        inline_codes = self._extract_inline_codes(text_content)
        coded_elements.extend(inline_codes)

        return coded_elements

    def _is_snomed_code(self, code: str) -> bool:
        """Check if code follows SNOMED CT pattern"""
        return code.isdigit() and len(code) >= 6

    def _is_icd10_code(self, code: str) -> bool:
        """Check if code follows ICD-10 pattern"""
        import re

        return bool(re.match(r"^[A-Z]\d{2}(\.\d+)?$", code))

    def _is_loinc_code(self, code: str) -> bool:
        """Check if code follows LOINC pattern"""
        import re

        return bool(re.match(r"^\d{4,5}-\d$", code))

    def _is_atc_code(self, code: str) -> bool:
        """Check if code follows ATC pattern"""
        import re

        return bool(re.match(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$", code))

    def _extract_inline_codes(self, text: str) -> List[Dict[str, Any]]:
        """Extract inline code references from text"""
        import re

        inline_codes = []

        # Common patterns for inline codes in medical text
        patterns = [
            (r"SNOMED\s+(\d{6,})", "SNOMED_CT"),
            (r"ICD-?10?\s+([A-Z]\d{2}(?:\.\d+)?)", "ICD10"),
            (r"LOINC\s+(\d{4,5}-\d)", "LOINC"),
            (r"ATC\s+([A-Z]\d{2}[A-Z]{2}\d{2})", "ATC"),
        ]

        for pattern, code_system in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                code = match.group(1)
                context = text[max(0, match.start() - 50) : match.end() + 50]

                inline_codes.append(
                    {
                        "code": code,
                        "codeSystem": code_system,
                        "displayName": f"Code referenced in text",
                        "element_type": "inline_reference",
                        "context": context.strip(),
                    }
                )

        return inline_codes

    def _get_element_context(self, element) -> str:
        """Get context information for a coded element"""
        # Look for parent containers that might provide context
        parent = element.parent
        while parent and parent.name:
            if parent.get("class"):
                classes = " ".join(parent.get("class"))
                if any(
                    keyword in classes.lower()
                    for keyword in [
                        "diagnosis",
                        "medication",
                        "procedure",
                        "observation",
                    ]
                ):
                    return classes
            parent = parent.parent

        return "general"

    def _translate_coded_elements(
        self, coded_elements: List[Dict[str, Any]], source_language: str
    ) -> List[Dict[str, Any]]:
        """Translate coded elements using terminology services"""
        translated_codes = []

        for coded_element in coded_elements:
            code = coded_element.get("code")
            code_system = coded_element.get("codeSystem")
            original_display = coded_element.get("displayName", "")

            translated_display = original_display
            terminology_mapping = None

            try:
                # Use the EnhancedCDATranslationService for terminology translation
                if hasattr(self.enhanced_translator, "translate_coded_concept"):
                    translation_result = (
                        self.enhanced_translator.translate_coded_concept(
                            code=code,
                            code_system=code_system,
                            source_language=source_language,
                            target_language="en",
                        )
                    )

                    if translation_result:
                        translated_display = translation_result.get(
                            "translated_display", original_display
                        )
                        terminology_mapping = translation_result.get("mapping_info", {})

                # Fallback to terminology translator
                elif hasattr(self.terminology_translator, "get_concept_translation"):
                    concept_translation = (
                        self.terminology_translator.get_concept_translation(
                            code, code_system, source_language
                        )
                    )
                    if concept_translation:
                        translated_display = concept_translation.get(
                            "preferred_term_en", original_display
                        )
                        terminology_mapping = concept_translation

            except Exception as e:
                logger.warning(
                    f"Failed to translate coded element {code} ({code_system}): {e}"
                )

            translated_codes.append(
                {
                    "code": code,
                    "codeSystem": code_system,
                    "originalDisplay": original_display,
                    "translatedDisplay": translated_display,
                    "element_type": coded_element.get("element_type"),
                    "context": coded_element.get("context"),
                    "terminology_mapping": terminology_mapping,
                    "translation_confidence": self._assess_code_translation_confidence(
                        original_display, translated_display, terminology_mapping
                    ),
                }
            )

        return translated_codes

    def _assess_code_translation_confidence(
        self, original: str, translated: str, mapping: Dict
    ) -> str:
        """Assess confidence level of code translation"""
        if not mapping:
            return "low"

        if original == translated:
            return "exact_match"

        # Check if we have authoritative mapping
        if mapping.get("mapping_source") in ["SNOMED_CT", "ICD10", "LOINC"]:
            return "high"

        if mapping.get("confidence_score", 0) > 0.8:
            return "high"
        elif mapping.get("confidence_score", 0) > 0.6:
            return "medium"
        else:
            return "low"

    def _process_xml_cda(
        self, xml_content: str, source_language: str
    ) -> Dict[str, Any]:
        """Process raw XML CDA content using the enhanced XML parser with clinical coding"""
        try:
            logger.info(
                f"Processing XML CDA content with enhanced parser (length: {len(xml_content)})"
            )

            # Use enhanced parser to extract sections and coded data
            parsed_result = self.xml_parser.parse_cda_content(xml_content)

            # Convert to format expected by the viewer
            translation_result = {
                "sections": parsed_result.get("sections", []),
                "sections_count": parsed_result.get("sections_count", 0),
                "coded_sections_count": parsed_result.get("coded_sections_count", 0),
                "medical_terms_count": parsed_result.get("medical_terms_count", 0),
                "uses_coded_sections": parsed_result.get("uses_coded_sections", False),
                "translation_quality": parsed_result.get(
                    "translation_quality", "Basic"
                ),
            }

            logger.info(
                f"Enhanced XML parsing complete: {translation_result['sections_count']} sections, "
                f"{translation_result['coded_sections_count']} coded, "
                f"{translation_result['medical_terms_count']} clinical codes extracted"
            )

            return {
                "success": True,
                "content_type": "xml_enhanced",
                "translation_result": translation_result,
                "patient_identity": parsed_result.get("patient_identity", {}),
                "administrative_data": parsed_result.get("administrative_data", {}),
                "has_administrative_data": parsed_result.get(
                    "has_administrative_data", False
                ),
                "sections_count": translation_result["sections_count"],
                "coded_sections_count": translation_result["coded_sections_count"],
                "medical_terms_count": translation_result["medical_terms_count"],
                "coded_sections_percentage": parsed_result.get(
                    "coded_sections_percentage", 0
                ),
                "uses_coded_sections": translation_result["uses_coded_sections"],
                "translation_quality": translation_result["translation_quality"],
                "source_language": source_language,
                "target_language": self.target_language,
                "original_content": xml_content,
                "translation_available": True,
            }

        except Exception as e:
            logger.error(f"Error processing XML CDA with enhanced parser: {e}")
            return self._create_error_response(f"Enhanced XML processing error: {e}")

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response structure"""
        return {
            "success": False,
            "error": error_message,
            "content_type": "error",
            "translation_available": False,
        }

    def get_translation_status(self) -> Dict[str, Any]:
        """Get current translation service status"""
        return {
            "target_language": self.target_language,
            "service_available": True,
            "terminology_service_available": bool(self.terminology_translator),
            "supported_languages": ["en", "fr", "de", "es", "it"],
        }
