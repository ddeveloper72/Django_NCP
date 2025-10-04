"""
Enhanced CDA Clinical Section Processor
Provides comprehensive clinical section processing with proper titles and table rendering
"""

import logging
import re
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, NavigableString
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class EnhancedCDAProcessor:
    """Enhanced processor for CDA clinical sections with proper titles and tables"""

    def __init__(self, target_language: str = "en", country_code: str = None):
        self.target_language = target_language
        self.country_code = country_code

        # Initialize CTS-compliant terminology service
        from translation_services.terminology_translator import TerminologyTranslator

        self.terminology_service = TerminologyTranslator(
            target_language=target_language
        )

        # Initialize country-specific mapper
        from .country_specific_cda_mapper import CountrySpecificCDAMapper

        self.country_mapper = CountrySpecificCDAMapper()

        # Import MVC models for Central Terminology Server integration
        from translation_services.mvc_models import (
            ValueSetCatalogue,
            ValueSetConcept,
            ConceptTranslation,
        )

        self.ValueSetCatalogue = ValueSetCatalogue
        self.ValueSetConcept = ValueSetConcept
        self.ConceptTranslation = ConceptTranslation

        logger.info(
            f"Initialized Enhanced CDA Processor with CTS-compliant terminology service for language: {target_language}, country: {country_code}"
        )

    def process_clinical_sections(
        self, cda_content: str, source_language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Process CDA content and extract enhanced clinical sections with proper titles and tables

        Args:
            cda_content: Raw CDA XML or HTML content
            source_language: Source language code (fr, de, it, etc.)

        Returns:
            Dictionary with enhanced sections data
        """
        try:
            # Check if CDA content is valid
            if not cda_content or not isinstance(cda_content, str):
                logger.warning("No valid CDA content provided")
                return {
                    "success": False,
                    "error": "No valid CDA content provided",
                    "sections": [],
                    "sections_count": 0,
                    "medical_terms_count": 0,
                    "coded_sections_count": 0,
                }

            # Determine content type and parse accordingly
            if (
                cda_content.strip().startswith("<?xml")
                or "<ClinicalDocument" in cda_content
            ):
                logger.info("Processing XML CDA content")
                return self._process_xml_cda(cda_content, source_language)
            elif cda_content.strip().startswith("<html") or "<body" in cda_content:
                logger.info("Processing HTML CDA content")
                return self._process_html_cda(cda_content, source_language)
            else:
                logger.warning("Unknown CDA content format, treating as HTML")
                return self._process_html_cda(cda_content, source_language)

        except Exception as e:
            logger.error(f"Error processing CDA content: {e}")
            return {
                "success": False,
                "error": str(e),
                "sections": [],
                "sections_count": 0,
                "medical_terms_count": 0,
                "coded_sections_count": 0,
            }

    def _process_xml_cda(
        self, xml_content: str, source_language: str
    ) -> Dict[str, Any]:
        """Process XML CDA document and extract clinical sections"""
        try:
            # Parse XML with namespace handling
            root = ET.fromstring(xml_content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "ext": "urn:hl7-EE-DL-Ext:v1",
                "xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "pharm": "urn:hl7-org:pharm",
            }

            sections = []
            sections_count = 0
            medical_terms_count = 0
            coded_sections_count = 0

            # Try country-specific extraction first if country code is available
            if self.country_code:
                logger.info(
                    f"Attempting country-specific extraction for {self.country_code}"
                )
                try:
                    country_data = self.country_mapper.extract_clinical_data(
                        xml_content, self.country_code
                    )

                    # Debug log the extracted data (reduced output)
                    logger.info(f"Country-specific extraction results: {country_data}")

                    # Count total items for quick summary
                    total_items = sum(len(items) for items in country_data.values())

                    # Only write to debug file if needed, no console spam
                    if total_items > 0:
                        logger.info(
                            f"[SUCCESS] Country extraction found {total_items} clinical items"
                        )
                        try:
                            debug_summary = f"Malta extraction: {total_items} items\n"
                            for section_name, items in country_data.items():
                                if items:
                                    debug_summary += f"  {section_name}: {len(items)}\n"

                            with open(
                                "malta_extraction_debug.txt", "w", encoding="utf-8"
                            ) as f:
                                f.write(debug_summary)
                        except Exception:
                            pass  # Ignore file write errors
                    else:
                        logger.info("[ERROR] Country extraction found no clinical items")

                    if any(country_data.values()):  # If any data was extracted
                        logger.info(
                            f"Successfully extracted data using {self.country_code} patterns"
                        )
                        sections = self._convert_country_data_to_sections(country_data)

                        # Debug log the converted sections
                        logger.info(f"Converted to {len(sections)} sections")
                        for section in sections:
                            logger.info(
                                f"Section {section['title']}: {section.get('medical_terms_count', 0)} items"
                            )

                        sections_count = len(sections)
                        coded_sections_count = len(
                            [s for s in sections if s.get("is_coded_section")]
                        )
                        medical_terms_count = sum(
                            s.get("medical_terms_count", 0) for s in sections
                        )

                        # Extract patient identity
                        # Use simple extraction since complex field mapper has XPath issues
                        patient_identity = self._simple_patient_id_extraction(
                            root, namespaces
                        )

                        return {
                            "success": True,
                            "content_type": "xml_country_specific",
                            "sections": sections,
                            "sections_count": sections_count,
                            "medical_terms_count": medical_terms_count,
                            "coded_sections_count": coded_sections_count,
                            "coded_sections_percentage": (
                                int((coded_sections_count / sections_count * 100))
                                if sections_count > 0
                                else 0
                            ),
                            "uses_coded_sections": coded_sections_count > 0,
                            "translation_quality": "High",
                            "extraction_method": "country_specific",
                            "patient_identity": patient_identity,
                        }
                except Exception as e:
                    logger.warning(
                        f"Country-specific extraction failed, trying document mapping: {e}"
                    )

                    # Try document-specific mapping approach
                    try:
                        from .document_mapper_integration import (
                            DocumentMapperIntegration,
                        )

                        logger.info("Attempting document-specific mapping as fallback")
                        document_integration = DocumentMapperIntegration()

                        # Extract patient ID from XML if available
                        patient_id = self._extract_patient_id(xml_content)

                        document_data = (
                            document_integration.extract_clinical_data_with_mapping(
                                xml_content, self.country_code, patient_id
                            )
                        )

                        if any(document_data.values()):  # If any data was extracted
                            logger.info(
                                "Successfully extracted data using document mapping"
                            )
                            sections = self._convert_country_data_to_sections(
                                document_data
                            )

                            sections_count = len(sections)
                            coded_sections_count = len(
                                [s for s in sections if s.get("is_coded_section")]
                            )
                            medical_terms_count = sum(
                                s.get("medical_terms_count", 0) for s in sections
                            )

                            # Extract patient identity
                            # Use simple extraction since complex field mapper has XPath issues
                            patient_identity = self._simple_patient_id_extraction(
                                root, namespaces
                            )

                            return {
                                "success": True,
                                "content_type": "xml_document_mapping",
                                "sections": sections,
                                "sections_count": sections_count,
                                "medical_terms_count": medical_terms_count,
                                "coded_sections_count": coded_sections_count,
                                "coded_sections_percentage": (
                                    int((coded_sections_count / sections_count * 100))
                                    if sections_count > 0
                                    else 0
                                ),
                                "uses_coded_sections": coded_sections_count > 0,
                                "translation_quality": "High",
                                "extraction_method": "document_mapping",
                                "patient_identity": patient_identity,
                            }
                        else:
                            logger.info(
                                "Document mapping extracted no data, falling back to generic"
                            )

                    except Exception as doc_e:
                        logger.warning(f"Document mapping also failed: {doc_e}")

            # Fall back to generic section parsing
            logger.info("Using generic XML section parsing")
            # Find all section elements
            section_elements = root.findall(".//hl7:section", namespaces)

            for section_elem in section_elements:
                section_data = self._extract_xml_section(
                    section_elem, namespaces, source_language
                )
                if section_data:
                    sections.append(section_data)
                    sections_count += 1

                    # Count medical terms and coded sections
                    if section_data.get("is_coded_section"):
                        coded_sections_count += 1

                    medical_terms = section_data.get("content", {}).get(
                        "medical_terms", 0
                    )
                    medical_terms_count += medical_terms

            # Extract patient identity regardless of processing method
            # Use simple extraction since complex field mapper has XPath issues
            patient_identity = self._simple_patient_id_extraction(root, namespaces)

            return {
                "success": True,
                "content_type": "xml_enhanced",
                "sections": sections,
                "sections_count": sections_count,
                "medical_terms_count": medical_terms_count,
                "coded_sections_count": coded_sections_count,
                "coded_sections_percentage": (
                    int((coded_sections_count / sections_count * 100))
                    if sections_count > 0
                    else 0
                ),
                "uses_coded_sections": coded_sections_count > 0,
                "translation_quality": (
                    "High" if coded_sections_count > (sections_count / 2) else "Medium"
                ),
                "patient_identity": patient_identity,
            }

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return {"success": False, "error": f"XML parsing error: {e}"}

    def _convert_country_data_to_sections(
        self, country_data: Dict[str, List]
    ) -> List[Dict]:
        """Convert country-specific extracted data to section format"""
        sections = []

        # Convert allergies
        if country_data.get("allergies"):
            sections.append(
                {
                    "title": "Allergies and Adverse Reactions",
                    "section_code": "48765-2",
                    "type": "allergies",
                    "table_data": country_data["allergies"],
                    "is_coded_section": True,
                    "medical_terms_count": len(country_data["allergies"]),
                    "has_entries": len(country_data["allergies"]) > 0,
                }
            )

        # Convert medications
        if country_data.get("medications"):
            sections.append(
                {
                    "title": "Current Medications",
                    "section_code": "10160-0",
                    "type": "medications",
                    "table_data": country_data["medications"],
                    "is_coded_section": True,
                    "medical_terms_count": len(country_data["medications"]),
                    "has_entries": len(country_data["medications"]) > 0,
                }
            )

        # Convert problems
        if country_data.get("problems"):
            sections.append(
                {
                    "title": "Problem List",
                    "section_code": "11450-4",
                    "type": "problems",
                    "table_data": country_data["problems"],
                    "is_coded_section": True,
                    "medical_terms_count": len(country_data["problems"]),
                    "has_entries": len(country_data["problems"]) > 0,
                }
            )

        return sections

    def _extract_xml_section(
        self, section_elem, namespaces: Dict, source_language: str
    ) -> Optional[Dict[str, Any]]:
        """Extract individual section from XML CDA"""
        try:
            section_id = section_elem.get("ID", f"section_{len(section_elem)}")

            # Extract section code
            code_elem = section_elem.find("hl7:code", namespaces)
            section_code = ""
            if code_elem is not None:
                section_code = code_elem.get("code", "")

            # Extract section title
            title_elem = section_elem.find("hl7:title", namespaces)
            original_title = (
                title_elem.text if title_elem is not None else "Unknown Section"
            )

            # Get enhanced title based on section code or original title
            enhanced_title = self._get_enhanced_section_title(
                section_code, original_title, source_language
            )

            # Extract section content
            text_elem = section_elem.find("hl7:text", namespaces)
            original_content = ""
            if text_elem is not None:
                # Convert XML content to HTML for display
                original_content = self._xml_to_html(text_elem)

            # Extract structured entries for table generation
            entries = section_elem.findall("hl7:entry", namespaces)

            # Use field mapper for value set extraction if available
            from .enhanced_cda_field_mapper import EnhancedCDAFieldMapper

            field_mapper = EnhancedCDAFieldMapper()
            clinical_fields = field_mapper.get_clinical_section_fields(section_code)

            # Extract table data using both structured extraction and field mapping
            table_data = self._extract_structured_data_with_valusets(
                entries, namespaces, clinical_fields, section_code
            )

            # Generate PS-compliant table if structured data exists
            ps_table_html = ""
            ps_table_html_original = ""
            has_ps_table = False

            if table_data:
                ps_table_html, ps_table_html_original = self._generate_ps_tables(
                    table_data, section_code, enhanced_title, source_language
                )
                has_ps_table = True

            # Translate content
            translated_content = self._translate_content(
                original_content, source_language
            )

            # Count medical terms (simplified)
            medical_terms_count = len(
                re.findall(
                    r"\b(?:medication|allergy|condition|diagnosis|procedure)\b",
                    original_content.lower(),
                )
            )

            return {
                "section_id": section_id,
                "title": {
                    "coded": enhanced_title["target"],
                    "translated": enhanced_title["target"],
                    "original": enhanced_title["source"],
                },
                "is_coded_section": len(entries) > 0,
                "content": {
                    "original": original_content,
                    "translated": translated_content,
                    "medical_terms": medical_terms_count,
                },
                "clinical_codes": {
                    "section_code": section_code,
                    "entries_count": len(entries),
                    "formatted_display": (
                        f"{len(entries)} coded entries"
                        if entries
                        else "No coded entries"
                    ),
                },
                "section_code": section_code,
                "has_ps_table": has_ps_table,
                "ps_table_html": ps_table_html,
                "ps_table_html_original": ps_table_html_original,
                "structured_data": table_data,  # Include structured data for debugging and table generation
                "table_rows": (
                    self._generate_table_rows(
                        table_data, section_code, self.target_language
                    )
                    if table_data
                    else []
                ),
            }

        except Exception as e:
            logger.error(f"Error extracting XML section: {e}")
            return None

    def _process_html_cda(
        self, html_content: str, source_language: str
    ) -> Dict[str, Any]:
        """Process HTML CDA content and extract clinical sections"""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            sections = []

            # Look for section elements in HTML - prioritize by data-code attribute
            section_elements = soup.find_all(attrs={"data-code": True})

            if not section_elements:
                # Fallback: Look for section/div elements with section-related classes
                section_elements = soup.find_all(
                    ["div", "section"],
                    class_=lambda x: x and "section" in x.lower() if x else False,
                )

            if not section_elements:
                # Second fallback: Look for any section elements
                section_elements = soup.find_all("section")

            # Final fallback: Look for headings that might indicate sections
            if not section_elements:
                section_elements = soup.find_all(["h1", "h2", "h3", "h4"])

            for i, elem in enumerate(section_elements):
                section_data = self._extract_html_section(elem, source_language, i)
                if section_data:
                    sections.append(section_data)

            sections_count = len(sections)
            coded_sections_count = sum(1 for s in sections if s.get("is_coded_section"))
            medical_terms_count = sum(
                s.get("content", {}).get("medical_terms", 0) for s in sections
            )

            return {
                "success": True,
                "content_type": "html_enhanced",
                "sections": sections,
                "sections_count": sections_count,
                "medical_terms_count": medical_terms_count,
                "coded_sections_count": coded_sections_count,
                "coded_sections_percentage": (
                    int((coded_sections_count / sections_count * 100))
                    if sections_count > 0
                    else 0
                ),
                "uses_coded_sections": coded_sections_count > 0,
                "translation_quality": "Medium" if sections_count > 0 else "Basic",
            }

        except Exception as e:
            logger.error(f"Error processing HTML CDA: {e}")
            return {"success": False, "error": str(e)}

    def _extract_html_section(
        self, elem, source_language: str, index: int
    ) -> Optional[Dict[str, Any]]:
        """Extract individual section from HTML CDA"""
        try:
            # Get section title
            if elem.name in ["h1", "h2", "h3", "h4"]:
                section_title = elem.get_text().strip()
                # Find content after heading
                content_elem = elem.find_next_sibling()
            else:
                # Look for title within div/section
                title_elem = elem.find(["h1", "h2", "h3", "h4"])
                section_title = (
                    title_elem.get_text().strip()
                    if title_elem
                    else f"Section {index + 1}"
                )
                content_elem = elem

            # Extract section code if available
            section_code = elem.get("data-code", "") or elem.get("id", "")

            # Get enhanced title
            enhanced_title = self._get_enhanced_section_title(
                section_code, section_title, source_language
            )

            # Extract content
            original_content = str(content_elem) if content_elem else ""

            # Look for tables in the content
            tables = content_elem.find_all("table") if content_elem else []
            has_ps_table = len(tables) > 0

            # Extract table data using value set integration if section code available
            table_data = []
            ps_table_html = ""
            ps_table_html_original = ""

            if has_ps_table and section_code:
                logger.info(
                    f"HTML section {section_code}: Applying value set integration for table processing"
                )

                # Use field mapper for value set extraction if available
                from .enhanced_cda_field_mapper import EnhancedCDAFieldMapper

                field_mapper = EnhancedCDAFieldMapper()
                clinical_fields = field_mapper.get_clinical_section_fields(section_code)

                if clinical_fields:
                    logger.info(
                        f"Found {len(clinical_fields)} clinical fields for section {section_code}"
                    )
                    # Extract structured data with value set support from HTML table
                    table_data = self._extract_html_table_with_valusets(
                        tables[0], clinical_fields, section_code
                    )
                    logger.info(
                        f"Extracted {len(table_data)} entries with value set support"
                    )

                    # Generate PS tables from extracted data
                    if table_data:
                        ps_table_html, ps_table_html_original = (
                            self._generate_ps_tables(
                                table_data,
                                section_code,
                                enhanced_title,
                                source_language,
                            )
                        )
                else:
                    logger.info(
                        f"No clinical fields found for section {section_code}, using standard extraction"
                    )
                    # Fall back to standard table extraction
                    standard_table_data = self._extract_table_data(tables[0])
                    ps_table_html, ps_table_html_original = (
                        self._generate_ps_tables_from_html(
                            tables[0], enhanced_title, source_language
                        )
                    )
            elif has_ps_table:
                # Standard table processing without section code
                standard_table_data = self._extract_table_data(tables[0])
                ps_table_html, ps_table_html_original = (
                    self._generate_ps_tables_from_html(
                        tables[0], enhanced_title, source_language
                    )
                )

            # Translate content
            translated_content = self._translate_content(
                original_content, source_language
            )

            # Count medical terms
            medical_terms_count = len(
                re.findall(
                    r"\b(?:medication|drug|allergy|condition|diagnosis|procedure|treatment)\b",
                    original_content.lower(),
                )
            )

            return {
                "section_id": f"html_section_{index}",
                "title": {
                    "coded": enhanced_title["target"],
                    "translated": enhanced_title["target"],
                    "original": enhanced_title["source"],
                },
                "is_coded_section": has_ps_table,
                "content": {
                    "original": original_content,
                    "translated": translated_content,
                    "medical_terms": medical_terms_count,
                },
                "clinical_codes": {
                    "section_code": section_code,
                    "tables_count": len(tables),
                    "formatted_display": (
                        f"{len(tables)} structured tables"
                        if tables
                        else "No structured data"
                    ),
                },
                "section_code": section_code,
                "has_ps_table": has_ps_table,
                "ps_table_html": ps_table_html,
                "ps_table_html_original": ps_table_html_original,
                "table_data": table_data,  # Include table data for debugging
            }

        except Exception as e:
            logger.error(f"Error extracting HTML section: {e}")
            return None

    def _extract_html_table_with_valusets(
        self, table_elem, clinical_fields: list, section_code: str
    ) -> list:
        """
        Extract HTML table data with value set integration
        """
        try:
            table_data = []

            # Get table headers
            headers = []
            thead = table_elem.find("thead")
            if thead:
                header_row = thead.find("tr")
                if header_row:
                    headers = [
                        th.get_text().strip()
                        for th in header_row.find_all(["th", "td"])
                    ]

            # Process table rows
            tbody = table_elem.find("tbody")
            if not tbody:
                tbody = table_elem  # Some tables don't have explicit tbody

            rows = tbody.find_all("tr")

            # Skip header row if no explicit thead
            if not thead and rows:
                rows = rows[1:]  # Skip first row as headers

            logger.info(f"Processing {len(rows)} table rows for section {section_code}")

            for i, row in enumerate(rows):
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue

                try:
                    entry_data = {
                        "type": "html_valueset_entry",
                        "data": {},
                        "fields": {},
                        "row_index": i,
                    }

                    # Map cells to headers and clinical fields
                    cell_data = {}
                    for j, cell in enumerate(cells):
                        if j < len(headers):
                            cell_data[headers[j]] = cell.get_text().strip()

                    # Map to clinical fields using value sets
                    for field in clinical_fields:
                        field_label = field.get("label", "")
                        has_valueset = field.get("valueSet", "NO").upper() == "YES"
                        needs_translation = (
                            field.get("translation", "NO").upper() == "YES"
                        )

                        # Try to match field label with table headers
                        matched_value = None
                        for header, value in cell_data.items():
                            if self._fuzzy_match_field_to_header(field_label, header):
                                matched_value = value
                                break

                        if matched_value:
                            # Apply value set lookup if needed
                            if has_valueset and matched_value:
                                translated_value = self._lookup_valueset_term(
                                    matched_value, field_label
                                )
                                final_value = (
                                    translated_value
                                    if translated_value
                                    else matched_value
                                )
                            else:
                                final_value = matched_value

                            entry_data["fields"][field_label] = {
                                "value": final_value,
                                "original_value": matched_value,
                                "needs_translation": needs_translation,
                                "has_valueset": has_valueset,
                                "matched_header": next(
                                    (
                                        h
                                        for h, v in cell_data.items()
                                        if v == matched_value
                                    ),
                                    None,
                                ),
                            }

                            logger.debug(
                                f"Mapped {field_label} -> {final_value} (from {matched_value})"
                            )

                    # Determine entry type based on section code
                    entry_data["section_type"] = self._determine_entry_type(
                        section_code
                    )
                    entry_data["section_code"] = section_code

                    # Only add if we extracted meaningful data
                    if entry_data["fields"]:
                        table_data.append(entry_data)

                except Exception as row_error:
                    logger.warning(
                        f"Error processing table row {i} for section {section_code}: {row_error}"
                    )
                    continue

            logger.info(
                f"Successfully extracted {len(table_data)} entries with value set support from HTML table"
            )
            return table_data

        except Exception as e:
            logger.error(
                f"Error extracting HTML table with value sets for section {section_code}: {e}"
            )
            return []

    def _fuzzy_match_field_to_header(self, field_label: str, header: str) -> bool:
        """
        Fuzzy match clinical field labels to table headers
        """
        field_lower = field_label.lower()
        header_lower = header.lower()

        # Direct match
        if field_lower == header_lower:
            return True

        # Enhanced field mappings for IE patient data and other formats
        field_mappings = {
            # Medication mappings
            "medication": [
                "médicament",
                "medication",
                "drug",
                "medicine",
                "name",
                "nom",
            ],
            "medication code": ["medication code", "code", "drug code", "name", "nom"],
            "medication displayname": [
                "medication name",
                "name",
                "nom",
                "drug name",
                "medication displayname",
            ],
            "medication originaltext": ["name", "nom", "medication name", "drug name"],
            # Allergy mappings
            "allergen": [
                "allergène",
                "allergen",
                "substance",
                "agent",
                "causative agent",
            ],
            "allergen code": ["allergen code", "agent", "causative agent", "substance"],
            "allergen displayname": [
                "agent",
                "allergen",
                "substance",
                "causative agent",
            ],
            "allergen originaltext": ["agent", "allergen", "substance", "description"],
            "allergy type": ["reaction type", "allergy type", "type", "propensity"],
            "reaction": [
                "réaction",
                "reaction",
                "symptôme",
                "symptom",
                "clinical manifestation",
                "manifestation",
            ],
            "reaction code": [
                "reaction code",
                "clinical manifestation",
                "manifestation",
                "symptom",
            ],
            "reaction displayname": [
                "clinical manifestation",
                "manifestation",
                "symptom",
                "reaction",
            ],
            # Problem mappings
            "problem": ["problème", "problem", "condition", "diagnostic"],
            "problem code": ["problem code", "condition code", "diagnostic code"],
            "problem displayname": [
                "problem",
                "condition",
                "diagnostic",
                "description",
            ],
            # Procedure mappings
            "procedure": ["procédure", "procedure", "intervention", "act"],
            "procedure code": ["procedure code", "intervention code", "act code"],
            "procedure displayname": [
                "procedure",
                "intervention",
                "act",
                "description",
            ],
            # Generic mappings
            "code": ["code", "coded value"],
            "displayname": [
                "nom",
                "name",
                "libellé",
                "display",
                "description",
                "designation",
            ],
            "originaltext": ["text", "original text", "description", "narrative"],
        }

        # Check specific field mappings first
        for field_key, possible_headers in field_mappings.items():
            if field_key in field_lower:
                for possible_header in possible_headers:
                    if possible_header in header_lower:
                        return True

        # Fallback: check for partial word matches
        field_words = field_lower.split()
        header_words = header_lower.split()

        # If any significant word matches (length > 3), consider it a match
        for field_word in field_words:
            if len(field_word) > 3:  # Skip short words like "of", "the", etc.
                for header_word in header_words:
                    if field_word in header_word or header_word in field_word:
                        return True

        return False

    def _get_enhanced_section_title(
        self, section_code: str, original_title: str, source_language: str
    ) -> Dict[str, str]:
        """Get enhanced section title using CTS-compliant translation service"""

        try:
            # Use Central Terminology Server for section code translation
            if section_code:
                # Query MVC for LOINC section codes
                cts_translation = self._query_cts_for_section_title(
                    section_code, source_language
                )
                if cts_translation:
                    logger.info(
                        f"CTS translation found for section code {section_code}"
                    )
                    return cts_translation

            # Fallback: Use terminology service for content-based translation
            if original_title:
                content_translation = self._translate_section_title_content(
                    original_title, source_language
                )
                if content_translation:
                    logger.info(
                        f"Content-based translation applied for: {original_title}"
                    )
                    return content_translation

            # Final fallback: Return original with basic translation attempt
            logger.warning(
                f"No CTS translation found for section code {section_code}, title: {original_title}"
            )
            return {
                "source": original_title,
                "target": self._basic_title_translation(
                    original_title, source_language
                ),
            }

        except Exception as e:
            logger.error(f"Error in CTS section title translation: {e}")
            return {
                "source": original_title,
                "target": original_title,  # Return original on error
            }

    def _query_cts_for_section_title(
        self, section_code: str, source_language: str
    ) -> Optional[Dict[str, str]]:
        """Query Central Terminology Server for section title translation"""
        try:
            # Enhanced LOINC section code lookup with multiple fallback strategies

            # Strategy 1: Direct LOINC code match
            concept = self.ValueSetConcept.objects.filter(
                code=section_code,
                code_system__icontains="loinc",
                status="active",
            ).first()

            # Strategy 2: Try without code system filter (broader search)
            if not concept:
                concept = self.ValueSetConcept.objects.filter(
                    code=section_code,
                    status="active",
                ).first()

            # Strategy 3: Try with SNOMED CT for clinical section codes
            if not concept:
                concept = self.ValueSetConcept.objects.filter(
                    code=section_code,
                    code_system__icontains="snomed",
                    status="active",
                ).first()

            if concept:
                # Get translation for target language
                translation = self.ConceptTranslation.objects.filter(
                    concept=concept, language_code=self.target_language
                ).first()

                if translation:
                    # Get source language display
                    source_translation = self.ConceptTranslation.objects.filter(
                        concept=concept, language_code=source_language
                    ).first()

                    logger.info(
                        f"CTS translation found for LOINC code {section_code}: {concept.display} -> {translation.translated_display}"
                    )

                    return {
                        "source": (
                            source_translation.translated_display
                            if source_translation
                            else concept.display
                        ),
                        "target": translation.translated_display,
                    }
                else:
                    # Use concept display as fallback
                    logger.info(
                        f"CTS concept found for {section_code} but no translation available"
                    )
                    return {
                        "source": concept.display,
                        "target": concept.display,  # Same if no translation
                    }

            # Strategy 4: Common LOINC section codes mapping (hardcoded fallback for development)
            loinc_section_mappings = {
                "10160-0": {"en": "Medication Summary", "lv": "Zāļu kopsavilkums"},
                "46264-8": {"en": "Medical Devices", "lv": "Medicīniskās ierīces"},
                "11450-4": {"en": "Problem List", "lv": "Problēmu saraksts"},
                "47519-4": {"en": "Procedures", "lv": "Procedūras"},
                "48765-2": {
                    "en": "Allergies and Intolerances",
                    "lv": "Alerģijas un nepanesamības",
                },
                "29762-2": {"en": "Social History", "lv": "Sociālā anamnēze"},
                "8716-3": {"en": "Vital Signs", "lv": "Dzīvībai svarīgie rādītāji"},
                "30954-2": {
                    "en": "Relevant Diagnostic Tests",
                    "lv": "Attiecīgie diagnostiskie testi",
                },
            }

            if section_code in loinc_section_mappings:
                mapping = loinc_section_mappings[section_code]
                source_text = mapping.get(
                    source_language, mapping.get("en", section_code)
                )
                target_text = mapping.get(
                    self.target_language, mapping.get("en", section_code)
                )

                logger.info(
                    f"Using hardcoded LOINC mapping for {section_code}: {source_text} -> {target_text}"
                )

                return {
                    "source": source_text,
                    "target": target_text,
                }

            logger.warning(f"No CTS translation found for section code {section_code}")
            return None

        except Exception as e:
            logger.error(f"Error querying CTS for section code {section_code}: {e}")
            return None

    def _translate_section_title_content(
        self, title: str, source_language: str
    ) -> Optional[Dict[str, str]]:
        """Translate section title using terminology service for medical content"""
        try:
            # Use terminology translator for medical terms in title
            translation_result = self.terminology_service._translate_term(
                code=None, system="", original_display=title  # No specific code
            )

            if translation_result and translation_result.get("translated_display"):
                return {
                    "source": title,
                    "target": translation_result["translated_display"],
                }

            # Try MVC lookup for partial matches
            medical_keywords = self._extract_medical_keywords(title)
            if medical_keywords:
                translated_keywords = []
                for keyword in medical_keywords:
                    keyword_translation = self._translate_medical_keyword(
                        keyword, source_language
                    )
                    translated_keywords.append(keyword_translation or keyword)

                # Reconstruct title with translated keywords
                translated_title = title
                for orig, trans in zip(medical_keywords, translated_keywords):
                    translated_title = translated_title.replace(orig, trans)

                return {"source": title, "target": translated_title}

            return None

        except Exception as e:
            logger.error(f"Error in content-based title translation: {e}")
            return None

    def _extract_medical_keywords(self, title: str) -> List[str]:
        """Extract medical keywords from section title for translation"""
        # Common medical terms that appear in section titles
        medical_patterns = [
            r"\b(?:medication|médicament|medikament|farmaco)s?\b",
            r"\b(?:allergy|allergie|allergia)s?\b",
            r"\b(?:problem|problème|problema)s?\b",
            r"\b(?:procedure|procédure|verfahren|procedura)s?\b",
            r"\b(?:history|histoire|geschichte|storia)\b",
            r"\b(?:summary|résumé|zusammenfassung|riassunto)\b",
            r"\b(?:plan|piano)\b",
            r"\b(?:care|soin|cura|pflege)\b",
        ]

        keywords = []
        title_lower = title.lower()

        for pattern in medical_patterns:
            matches = re.findall(pattern, title_lower, re.IGNORECASE)
            keywords.extend(matches)

        return list(set(keywords))  # Remove duplicates

    def _translate_medical_keyword(
        self, keyword: str, source_language: str
    ) -> Optional[str]:
        """Translate individual medical keyword using MVC"""
        try:
            # Look for concept with matching display text
            concept = self.ValueSetConcept.objects.filter(
                display__icontains=keyword, status="active"
            ).first()

            if concept:
                translation = self.ConceptTranslation.objects.filter(
                    concept=concept, language_code=self.target_language
                ).first()

                if translation:
                    return translation.translated_display

            return None

        except Exception as e:
            logger.error(f"Error translating keyword {keyword}: {e}")
            return None

    def _basic_title_translation(self, title: str, source_language: str) -> str:
        """Basic fallback translation when CTS is unavailable - CTS-compliant approach"""
        try:
            # Even in fallback, try to use MVC for basic medical terms
            words = title.split()
            translated_words = []

            for word in words:
                # Clean word (remove punctuation)
                clean_word = re.sub(r"[^\w\s]", "", word)

                # Try to find translation in MVC
                translated_word = self._lookup_term_in_mvc(clean_word, source_language)
                if translated_word:
                    # Preserve original punctuation
                    translated_words.append(word.replace(clean_word, translated_word))
                else:
                    translated_words.append(word)

            translated_title = " ".join(translated_words)

            # Log fallback usage
            if translated_title != title:
                logger.info(
                    f"Basic fallback translation applied: {title} -> {translated_title}"
                )
            else:
                logger.warning(f"No fallback translation available for: {title}")

            return translated_title

        except Exception as e:
            logger.error(f"Error in basic fallback translation: {e}")
            return title  # Return original if even fallback fails

    def _extract_structured_data(
        self, entries, namespaces: Dict
    ) -> List[Dict[str, Any]]:
        """Extract structured data from CDA entries for table generation"""
        structured_data = []

        for entry in entries:
            try:
                entry_data = {"type": "structured_entry", "data": {}}

                # Extract substance administration (medications)
                sub_admin = entry.find(".//hl7:substanceAdministration", namespaces)
                if sub_admin is not None:
                    entry_data["data"] = self._extract_medication_data(
                        sub_admin, namespaces
                    )
                    entry_data["section_type"] = "medication"

                # Extract observation (allergies, lab results, etc.)
                obs_elem = entry.find(".//hl7:observation", namespaces)
                if obs_elem is not None:
                    obs_data = self._extract_observation_data(obs_elem, namespaces)
                    entry_data["data"] = obs_data
                    entry_data["section_type"] = "observation"

                    # Convert observation data to structured fields format
                    entry_data["fields"] = (
                        self._convert_observation_to_structured_fields(obs_data)
                    )

                # Extract procedure data
                procedure = entry.find(".//hl7:procedure", namespaces)
                if procedure is not None:
                    entry_data["data"] = self._extract_procedure_data(
                        procedure, namespaces
                    )
                    entry_data["section_type"] = "procedure"

                # Extract act (general activities)
                act_elem = entry.find(".//hl7:act", namespaces)
                if act_elem is not None:
                    entry_data["data"] = self._extract_act_data(act_elem, namespaces)
                    entry_data["section_type"] = "act"

                # Only add if we extracted meaningful data
                if entry_data["data"]:
                    structured_data.append(entry_data)

            except Exception as e:
                logger.error(f"Error extracting entry data: {e}")
                continue

        # If no structured data was found, try to extract from HTML tables
        if not structured_data:
            structured_data = self._extract_from_html_tables(entries, namespaces)

        return structured_data

    def _extract_structured_data_with_valusets(
        self, entries, namespaces: Dict, clinical_fields: List[Dict], section_code: str
    ) -> List[Dict[str, Any]]:
        """
        Extract structured data from CDA entries using field mapper and value sets
        """
        structured_data = []

        for entry in entries:
            try:
                entry_data = {"type": "valueset_entry", "data": {}, "fields": {}}

                # Use field mapper to extract specific fields with value set support
                for field in clinical_fields:
                    field_label = field.get("label", "")
                    xpath = field.get("xpath", "")
                    needs_translation = field.get("translation", "NO").upper() == "YES"
                    has_valueset = field.get("valueSet", "NO").upper() == "YES"

                    if not xpath:
                        continue

                    try:
                        # Process XPath for CDA namespace - field mappings use simplified paths
                        # Convert paths like "consumable/manufacturedProduct/code/@code"
                        # to proper namespaced XPath ".//hl7:consumable/hl7:manufacturedProduct/hl7:code"
                        entry_xpath = self._convert_field_xpath_to_namespaced(xpath)

                        # Extract value based on XPath
                        extracted_value = self._extract_field_with_valueset(
                            entry,
                            entry_xpath,
                            namespaces,
                            field_label,
                            has_valueset,
                            needs_translation,
                            xpath,  # Pass original xpath for attribute handling
                        )

                        if extracted_value:
                            entry_data["fields"][field_label] = {
                                "value": extracted_value,
                                "needs_translation": needs_translation,
                                "has_valueset": has_valueset,
                                "xpath": xpath,
                            }

                    except Exception as field_error:
                        logger.warning(
                            f"Error extracting field '{field_label}' for section {section_code}: {field_error}"
                        )
                        continue

                # Determine entry type based on section code
                entry_data["section_type"] = self._determine_entry_type(section_code)
                entry_data["section_code"] = section_code

                # Only add if we extracted meaningful data
                if entry_data["fields"]:
                    structured_data.append(entry_data)

            except Exception as e:
                logger.error(f"Error processing entry for section {section_code}: {e}")
                continue

        logger.info(
            f"Extracted {len(structured_data)} entries with value set support for section {section_code}"
        )
        return structured_data

    def _extract_field_with_valueset(
        self,
        entry_elem,
        namespaced_xpath: str,
        namespaces: Dict,
        field_label: str,
        has_valueset: bool,
        needs_translation: bool,
        original_xpath: str = "",
    ) -> Optional[str]:
        """
        Extract field value and apply value set lookup if needed
        namespaced_xpath: The converted XPath with hl7: prefixes
        original_xpath: The original field mapper XPath (for attribute extraction)
        """
        try:
            # Determine if we need attribute extraction from original xpath
            if original_xpath and "/@" in original_xpath:
                attr_name = original_xpath.split("/@")[1]
                # Find element using namespaced xpath
                elem = entry_elem.find(namespaced_xpath, namespaces)
                if elem is not None:
                    raw_value = elem.get(attr_name)
                    if raw_value and has_valueset:
                        # Look up in value sets for proper medical terminology
                        translated_value = self._lookup_valueset_term(
                            raw_value, field_label
                        )
                        return translated_value if translated_value else raw_value
                    return raw_value
            else:
                # Element text extraction
                elem = entry_elem.find(namespaced_xpath, namespaces)
                if elem is not None:
                    raw_value = elem.text
                    if raw_value and has_valueset:
                        translated_value = self._lookup_valueset_term(
                            raw_value, field_label
                        )
                        return translated_value if translated_value else raw_value
                    return raw_value

        except Exception as e:
            logger.warning(
                f"Field extraction error for '{field_label}' with XPath '{namespaced_xpath}' (orig: '{original_xpath}'): {e}"
            )

        return None

    def _determine_entry_type(self, section_code: str) -> str:
        """Determine entry type based on section code"""
        section_type_map = {
            "48765-2": "allergy",  # Allergies
            "11450-4": "problem",  # Problem list
            "47519-4": "procedure",  # History of procedures
            "10160-0": "medication",  # History of medication use
            "46264-8": "medical_device",  # Medical equipment
        }
        return section_type_map.get(section_code, "observation")

    def _convert_field_xpath_to_namespaced(self, xpath: str) -> str:
        """
        Convert field mapper XPath to proper namespaced XPath for CDA extraction

        Examples:
        - "consumable/manufacturedProduct/code/@code"
          -> ".//hl7:consumable/hl7:manufacturedProduct/hl7:code"
        - "participant/participantRole/code/@code"
          -> ".//hl7:participant/hl7:participantRole/hl7:code"
        - "pharm:ingredient/pharm:ingredientSubstance/pharm:code/@code"
          -> ".//pharm:ingredient/pharm:ingredientSubstance/pharm:code"
        """
        if not xpath:
            return xpath

        # Handle attribute extraction - split the attribute part
        if "/@" in xpath:
            element_path, attr_name = xpath.split("/@")
            # Convert element path to namespaced XPath
            path_parts = element_path.split("/")
            namespaced_parts = []
            for part in path_parts:
                if part:
                    # Check if already has namespace prefix
                    if ":" in part:
                        namespaced_parts.append(part)  # Keep existing namespace
                    else:
                        namespaced_parts.append(f"hl7:{part}")  # Add hl7 namespace
            namespaced_xpath = ".//{}".format("/".join(namespaced_parts))
        else:
            # Just element path
            path_parts = xpath.split("/")
            namespaced_parts = []
            for part in path_parts:
                if part:
                    # Check if already has namespace prefix
                    if ":" in part:
                        namespaced_parts.append(part)  # Keep existing namespace
                    else:
                        namespaced_parts.append(f"hl7:{part}")  # Add hl7 namespace
            namespaced_xpath = ".//{}".format("/".join(namespaced_parts))

        return namespaced_xpath

    def _lookup_valueset_term(self, code: str, field_label: str) -> Optional[str]:
        """
        Look up medical terminology in value sets
        Enhanced to use MVC/CTS value sets
        """
        if not code or not code.strip():
            return None

        try:
            # Try to find concept in MVC value sets
            concept = self.ValueSetConcept.objects.filter(
                code=code.strip(), status="active"
            ).first()

            if not concept:
                # Try partial match on display name for allergens/conditions
                concept = self.ValueSetConcept.objects.filter(
                    display__icontains=code.strip(), status="active"
                ).first()

            if concept:
                # Get translation for target language
                translation = self.ConceptTranslation.objects.filter(
                    concept=concept, language_code=self.target_language
                ).first()

                if translation:
                    logger.info(
                        f"Value set translation found for {field_label}: {code} -> {translation.translated_display}"
                    )
                    return translation.translated_display
                else:
                    # Return original display name if no translation
                    logger.info(
                        f"Value set concept found for {field_label} but no translation: {concept.display}"
                    )
                    return concept.display

            return None

        except Exception as e:
            logger.error(
                f"Error looking up value set term '{code}' for {field_label}: {e}"
            )
            return None

    def _extract_medication_data(self, sub_admin, namespaces) -> Dict[str, Any]:
        """Extract comprehensive medication data from substanceAdministration element"""
        data = {}

        try:
            # Get medication code and display name
            consumable = sub_admin.find(
                ".//hl7:consumable/hl7:manufacturedProduct/hl7:manufacturedMaterial",
                namespaces,
            )
            if consumable is not None:
                # Extract medication name from <name> element
                name_elem = consumable.find("hl7:name", namespaces)
                if name_elem is not None and name_elem.text:
                    data["medication_name"] = name_elem.text.strip()
                else:
                    # Fallback to code displayName
                    code_elem = consumable.find("hl7:code", namespaces)
                    if code_elem is not None:
                        data["medication_name"] = code_elem.get("displayName", "Unknown Medication")

                # Extract pharmaceutical form (tablet, injection, etc.)
                pharm_form = consumable.find(".//pharm:formCode", namespaces)
                if pharm_form is not None:
                    data["pharmaceutical_form_code"] = pharm_form.get("code", "")
                    # Use lookup for form display name
                    data["pharmaceutical_form"] = self._lookup_form_code(
                        pharm_form.get("code", "")
                    ) or pharm_form.get("displayName", "")

                # Extract ingredient information with strength
                ingredient = consumable.find(
                    ".//pharm:ingredient/pharm:ingredientSubstance", namespaces
                )
                if ingredient is not None:
                    ing_code = ingredient.find("pharm:code", namespaces)
                    if ing_code is not None:
                        data["ingredient_code"] = ing_code.get("code", "")
                        # ATC codes need lookup - H03AA01 = levothyroxine sodium
                        data["ingredient_display"] = self._lookup_atc_code(
                            ing_code.get("code", "")
                        ) or ing_code.get("displayName", "Unknown Ingredient")

                    # Extract strength information (numerator/denominator)
                    quantity_elem = consumable.find(".//pharm:ingredient/pharm:quantity", namespaces)
                    if quantity_elem is not None:
                        numerator = quantity_elem.find("hl7:numerator", namespaces)
                        denominator = quantity_elem.find("hl7:denominator", namespaces)
                        
                        if numerator is not None:
                            strength_value = numerator.get("value", "")
                            strength_unit = numerator.get("unit", "")
                            denom_value = denominator.get("value", "1") if denominator is not None else "1"
                            
                            if strength_value and strength_unit:
                                data["strength"] = f"{strength_value} {strength_unit}"
                                if denom_value != "1":
                                    denom_unit = denominator.get("unit", "") if denominator is not None else ""
                                    data["strength"] += f" / {denom_value} {denom_unit}".strip()

            # Extract comprehensive dosage information - handle both HL7 and pharmaceutical namespaces
            dose_quantity = sub_admin.find(".//hl7:doseQuantity", namespaces)
            pharm_quantity = sub_admin.find(".//pharm:quantity", namespaces)
            
            if pharm_quantity is not None:
                # Handle pharmaceutical quantity with numerator/denominator
                numerator = pharm_quantity.find("numerator", namespaces)
                denominator = pharm_quantity.find("denominator", namespaces)
                
                if numerator is not None:
                    num_value = numerator.get("value", "")
                    num_unit = numerator.get("unit", "")
                    
                    if denominator is not None:
                        denom_value = denominator.get("value", "")
                        denom_unit = denominator.get("unit", "")
                        
                        # Format as "5 mg/1" for strength display
                        if num_value and denom_value:
                            if denom_value == "1" and denom_unit in ["1", ""]:
                                data["dose_quantity"] = f"{num_value} {num_unit}".strip()
                                data["strength"] = f"{num_value} {num_unit}".strip()
                            else:
                                data["dose_quantity"] = f"{num_value} {num_unit}/{denom_value} {denom_unit}".strip()
                                data["strength"] = f"{num_value} {num_unit}/{denom_value} {denom_unit}".strip()
                        else:
                            data["dose_quantity"] = f"{num_value} {num_unit}".strip()
                            data["strength"] = f"{num_value} {num_unit}".strip()
                            
                        # Store raw values for template flexibility
                        data["dose_value"] = num_value
                        data["dose_unit"] = num_unit
                        
            elif dose_quantity is not None:
                # Handle standard HL7 doseQuantity
                # Check for range (low/high)
                low_elem = dose_quantity.find("hl7:low", namespaces)
                high_elem = dose_quantity.find("hl7:high", namespaces)
                
                if low_elem is not None and high_elem is not None:
                    low_val = low_elem.get("value", "")
                    high_val = high_elem.get("value", "")
                    unit = low_elem.get("unit", "")
                    
                    if low_val == high_val:
                        data["dose_quantity"] = f"{low_val} {unit}".strip()
                        data["dose_value"] = low_val
                        data["dose_unit"] = unit
                    else:
                        data["dose_quantity"] = f"{low_val}-{high_val} {unit}".strip()
                        data["dose_value"] = f"{low_val}-{high_val}"
                        data["dose_unit"] = unit
                else:
                    # Single value
                    value = dose_quantity.get("value", "")
                    unit = dose_quantity.get("unit", "")
                    data["dose_quantity"] = f"{value} {unit}".strip() if value else "Not specified"
                    data["dose_value"] = value
                    data["dose_unit"] = unit

            # Extract route of administration
            route_elem = sub_admin.find("hl7:routeCode", namespaces)
            if route_elem is not None:
                data["route_code"] = route_elem.get("code", "")
                data["route_display"] = self._lookup_route_code(
                    route_elem.get("code", "")
                ) or route_elem.get("displayName", "Unknown route")

            # Extract timing/frequency information
            effective_times = sub_admin.findall(".//hl7:effectiveTime", namespaces)
            
            for et in effective_times:
                et_type = et.get("{http://www.w3.org/2001/XMLSchema-instance}type", "")
                
                # Date range (IVL_TS)
                if et_type == "IVL_TS":
                    low_elem = et.find("hl7:low", namespaces)
                    high_elem = et.find("hl7:high", namespaces)
                    
                    if low_elem is not None:
                        start_date = low_elem.get("value", "")
                        data["start_date"] = self._format_hl7_date(start_date)
                        data["start_date_raw"] = start_date
                    
                    if high_elem is not None and high_elem.get("nullFlavor") != "UNK":
                        end_date = high_elem.get("value", "")
                        data["end_date"] = self._format_hl7_date(end_date)
                        data["end_date_raw"] = end_date

                # Event-based timing (EIVL_TS)
                elif et_type == "EIVL_TS":
                    event_elem = et.find("hl7:event", namespaces)
                    if event_elem is not None:
                        event_code = event_elem.get("code", "")
                        data["frequency_code"] = event_code
                        data["frequency_display"] = self._lookup_frequency_code(event_code)

                # Periodic timing (PIVL_TS)
                elif et_type == "PIVL_TS":
                    period = et.find("hl7:period", namespaces)
                    if period is not None:
                        value = period.get("value", "")
                        unit = period.get("unit", "")
                        data["period"] = f"Every {value} {unit}" if value else "As directed"

            # Extract status
            status_code = sub_admin.find("hl7:statusCode", namespaces)
            if status_code is not None:
                data["status"] = status_code.get("code", "active")

            # Create comprehensive medication summary (like XML Notepad output)
            summary_parts = []
            if "medication_name" in data:
                summary_parts.append(data["medication_name"])
            
            if "ingredient_display" in data and "strength" in data:
                summary_parts.append(f"{data['ingredient_display']} {data['strength']}")
            
            if "pharmaceutical_form" in data:
                summary_parts.append(data["pharmaceutical_form"])
            
            dose_info = []
            if "dose_quantity" in data:
                dose_info.append(data["dose_quantity"])
            if "frequency_display" in data:
                dose_info.append(data["frequency_display"])
            if dose_info:
                summary_parts.append(" ".join(dose_info))
            
            if "start_date" in data:
                time_part = f"since {data['start_date']}"
                if "end_date" in data:
                    time_part = f"between {data['start_date']} and {data['end_date']}"
                summary_parts.append(time_part)
            
            if "route_display" in data:
                summary_parts.append(f"({data['route_display']})")
            
            data["medication_summary"] = " : ".join(summary_parts) if summary_parts else "Unknown medication"

        except Exception as e:
            logger.error(f"Error extracting medication data: {e}")

        return data

    def _extract_observation_data(self, obs_elem, namespaces) -> Dict[str, Any]:
        """Extract observation data (allergies, lab results, problems, vital signs, etc.)"""
        data = {}

        try:
            # Extract observation ID
            id_elem = obs_elem.find("hl7:id", namespaces)
            if id_elem is not None:
                data["id"] = id_elem.get("root", "")

            # Get observation code (REACTION TYPE for allergies)
            code_elem = obs_elem.find("hl7:code", namespaces)
            if code_elem is not None:
                code_value = code_elem.get("code", "")
                display_name = code_elem.get("displayName", "")
                
                data["code"] = code_value
                data["display"] = display_name if display_name else f"Code: {code_value}" if code_value else "Unknown Observation"
                data["code_system"] = self._get_code_system_name(
                    code_elem.get("codeSystem", "")
                )
                data["code_system_name"] = code_elem.get("codeSystemName", "")

                # For allergies: The observation/code element contains the REACTION TYPE
                # e.g., code="420134006" = "Propensity to adverse reactions"
                data["reaction_type_code"] = code_value
                
                # Use CTS lookup for reaction type if displayName is missing
                if display_name and display_name.strip():
                    data["reaction_type_display"] = display_name
                elif code_value:
                    # Try CTS lookup for SNOMED CT reaction type codes
                    cts_reaction_type = self._lookup_valueset_term(code_value, "reaction_type")
                    if cts_reaction_type:
                        data["reaction_type_display"] = cts_reaction_type
                    else:
                        data["reaction_type_display"] = f"Reaction Type: {code_value}"
                else:
                    data["reaction_type_display"] = "Unknown Reaction Type"

                # Extract translation if available (e.g., Italian translation)
                translation_elem = code_elem.find("hl7:translation", namespaces)
                if translation_elem is not None:
                    data["translation_display"] = translation_elem.get(
                        "displayName", ""
                    )
                    data["translation_code"] = translation_elem.get("code", "")

            # Extract value - CLINICAL MANIFESTATION for allergies
            value_elem = obs_elem.find("hl7:value", namespaces)
            if value_elem is not None:
                # Check the type of value (PQ = Physical Quantity, CD = Coded Display, etc.)
                xsi_type = value_elem.get(
                    "{http://www.w3.org/2001/XMLSchema-instance}type"
                ) or value_elem.get("xsi:type")

                if xsi_type == "PQ":
                    # Physical Quantity (e.g., vital signs with units)
                    data["value"] = value_elem.get("value", "")
                    data["unit"] = value_elem.get("unit", "")
                    data["value_type"] = "quantity"

                    # Format display value with unit
                    if data["value"] and data["unit"]:
                        data["formatted_value"] = f"{data['value']} {data['unit']}"
                    else:
                        data["formatted_value"] = data["value"]

                elif xsi_type == "CD":
                    # Coded Display (e.g., conditions, problems)
                    value_code = value_elem.get("code", "")
                    value_display = value_elem.get("displayName", value_elem.get("value", ""))
                    
                    data["value"] = value_display if value_display else f"Value: {value_code}" if value_code else ""
                    data["value_code"] = value_code
                    data["value_type"] = "coded"
                    data["formatted_value"] = data["value"]

                    # For allergies: The observation/value element contains the CLINICAL MANIFESTATION
                    # e.g., code="43116000" = "Eczema"
                    data["manifestation_code"] = value_code
                    
                    # Extract code system for manifestation - if not available, assume SNOMED CT from CTS
                    manifestation_code_system = value_elem.get("codeSystem", "")
                    if manifestation_code_system:
                        data["manifestation_code_system"] = self._get_code_system_name(manifestation_code_system)
                    else:
                        # CTS provides SNOMED CT codes for manifestations
                        data["manifestation_code_system"] = "SNOMED CT"
                    
                    # Use CTS lookup for manifestation if displayName is missing
                    if value_display and value_display.strip():
                        data["manifestation_display"] = value_display
                    elif value_code:
                        # Try CTS lookup for SNOMED CT manifestation codes
                        cts_manifestation = self._lookup_valueset_term(value_code, "manifestation")
                        if cts_manifestation:
                            data["manifestation_display"] = cts_manifestation
                        else:
                            data["manifestation_display"] = f"Manifestation: {value_code}"
                    else:
                        data["manifestation_display"] = "Unknown Reaction"

                    # For problem observations, map value fields to condition fields
                    data["condition_code"] = value_elem.get("code", "")
                    data["condition_display"] = value_elem.get(
                        "displayName", "Unknown Condition"
                    )
                    data["condition_system"] = self._get_code_system_name(
                        value_elem.get("codeSystem", "")
                    )

                    # For legacy allergies support, also extract agent information
                    data["agent_code"] = value_elem.get("code", "")
                    data["agent_display"] = value_elem.get(
                        "displayName", "Unknown Agent"
                    )

                else:
                    # Default handling for other types
                    data["value"] = value_elem.get(
                        "displayName", value_elem.get("value", "")
                    )
                    data["value_type"] = "text"
                    data["formatted_value"] = data["value"]

            # Extract status
            status_code = obs_elem.find("hl7:statusCode", namespaces)
            if status_code is not None:
                data["status"] = status_code.get("code", "completed")

            # Extract effective time (when the observation was made)
            effective_time = obs_elem.find("hl7:effectiveTime", namespaces)
            if effective_time is not None:
                time_value = effective_time.get("value", "")
                if time_value:
                    data["effective_time"] = time_value
                    # Try to format the date/time
                    data["formatted_time"] = self._format_hl7_datetime(time_value)

            # Also check for low/high time in effectiveTime
            effective_time_low = obs_elem.find("hl7:effectiveTime/hl7:low", namespaces)
            if effective_time_low is not None:
                onset_value = effective_time_low.get("value", "")
                if onset_value:
                    data["onset_date"] = self._format_hl7_datetime(onset_value)

            # Extract participant (for allergies - causative agent)
            participant = obs_elem.find(
                ".//hl7:participant/hl7:participantRole/hl7:playingEntity", namespaces
            )
            if participant is not None:
                agent_code = participant.find("hl7:code", namespaces)
                if agent_code is not None:
                    code_value = agent_code.get("code", "")
                    display_name = agent_code.get("displayName", "")
                    code_system = agent_code.get("codeSystem", "")
                    
                    data["agent_code"] = code_value
                    
                    # Extract code system for agent - if not available, assume SNOMED CT from CTS
                    if code_system:
                        data["agent_code_system"] = self._get_code_system_name(code_system)
                    else:
                        # CTS provides SNOMED CT codes for agents
                        data["agent_code_system"] = "SNOMED CT"
                    
                    # Use CTS lookup for agent if displayName is missing
                    if display_name and display_name.strip():
                        data["agent_display"] = display_name
                    elif code_value:
                        # Try CTS lookup for SNOMED CT agent codes
                        cts_agent = self._lookup_valueset_term(code_value, "agent")
                        if cts_agent:
                            data["agent_display"] = cts_agent
                        else:
                            data["agent_display"] = f"Agent (Code: {code_value})"
                    else:
                        data["agent_display"] = "Unknown Agent"

            # ENHANCED: Extract agent from pharm:code elements (e.g., J01CA04)
            # This is where the actual allergen/causative agent is specified
            try:
                pharm_codes = obs_elem.findall(".//pharm:code", namespaces)
                for pharm_code in pharm_codes:
                    code_value = pharm_code.get("code", "")
                    display_name = pharm_code.get("displayName", "")
                    code_system = pharm_code.get("codeSystem", "")
                    
                    # If we found a pharm:code with meaningful data, use it as the agent
                    if code_value and (display_name or code_value != "ASSERTION"):
                        data["agent_code"] = code_value
                        data["agent_display"] = display_name if display_name else f"Agent (Code: {code_value})"
                        
                        # Extract code system for pharm agent - if not available, assume SNOMED CT from CTS
                        if code_system:
                            data["agent_code_system"] = self._get_code_system_name(code_system)
                        else:
                            # CTS provides SNOMED CT codes for pharmaceutical agents
                            data["agent_code_system"] = "SNOMED CT"
                        
                        # Break after finding the first meaningful pharm:code
                        break
            except Exception as pharm_e:
                # Pharmaceutical namespace not available or other error - continue without pharm:code extraction
                pass

            # If no agent found yet, try looking in entry/act/code (alternative structure)
            if not data.get("agent_code"):
                # Look for act elements that might contain agent information
                act_elem = obs_elem.find("../hl7:act", namespaces)
                if act_elem is not None:
                    act_code = act_elem.find("hl7:code", namespaces)
                    if act_code is not None:
                        code_value = act_code.get("code", "")
                        display_name = act_code.get("displayName", "")
                        code_system = act_code.get("codeSystem", "")
                        if code_value and display_name:
                            data["agent_code"] = code_value
                            data["agent_display"] = display_name
                            
                            # Extract code system for act agent - if not available, assume SNOMED CT from CTS
                            if code_system:
                                data["agent_code_system"] = self._get_code_system_name(code_system)
                            else:
                                # CTS provides SNOMED CT codes for agents
                                data["agent_code_system"] = "SNOMED CT"

            # Extract severity (for allergies and problems)
            entryRelationship = obs_elem.find(
                ".//hl7:entryRelationship[@typeCode='SUBJ']/hl7:observation", namespaces
            )
            if entryRelationship is not None:
                severity_code = entryRelationship.find(
                    "hl7:code[@code='SEV']", namespaces
                )
                if severity_code is not None:
                    severity_value = entryRelationship.find("hl7:value", namespaces)
                    if severity_value is not None:
                        data["severity"] = severity_value.get(
                            "displayName", severity_value.get("code", "unknown")
                        )

            # Extract manifestation (for allergies)
            manifestation = obs_elem.find(
                ".//hl7:entryRelationship[@typeCode='MFST']/hl7:observation/hl7:value",
                namespaces,
            )
            if manifestation is not None:
                manifestation_code = manifestation.get("code", "")
                manifestation_display = manifestation.get("displayName", "")
                manifestation_code_system = manifestation.get("codeSystem", "")
                
                data["manifestation_code"] = manifestation_code
                
                # Extract code system for manifestation - if not available, assume SNOMED CT from CTS
                if manifestation_code_system:
                    data["manifestation_code_system"] = self._get_code_system_name(manifestation_code_system)
                else:
                    # CTS provides SNOMED CT codes for manifestations
                    data["manifestation_code_system"] = "SNOMED CT"
                
                # Use CTS lookup for manifestation if displayName is missing
                if manifestation_display and manifestation_display.strip():
                    data["manifestation_display"] = manifestation_display
                elif manifestation_code:
                    # Try CTS lookup for SNOMED CT manifestation codes
                    cts_manifestation = self._lookup_valueset_term(manifestation_code, "manifestation")
                    if cts_manifestation:
                        data["manifestation_display"] = cts_manifestation
                    else:
                        data["manifestation_display"] = f"Manifestation: {manifestation_code}"
                else:
                    data["manifestation_display"] = "Unknown Reaction"

            # Extract interpretation codes (normal, high, low, etc.)
            interpretation = obs_elem.find("hl7:interpretationCode", namespaces)
            if interpretation is not None:
                data["interpretation"] = interpretation.get("code", "")
                data["interpretation_display"] = interpretation.get("displayName", "")

            # Extract reference ranges
            reference_range = obs_elem.find(
                "hl7:referenceRange/hl7:observationRange", namespaces
            )
            if reference_range is not None:
                low_elem = reference_range.find("hl7:value/hl7:low", namespaces)
                high_elem = reference_range.find("hl7:value/hl7:high", namespaces)
                if low_elem is not None or high_elem is not None:
                    data["reference_range"] = {}
                    if low_elem is not None:
                        data["reference_range"]["low"] = low_elem.get("value", "")
                        data["reference_range"]["low_unit"] = low_elem.get("unit", "")
                    if high_elem is not None:
                        data["reference_range"]["high"] = high_elem.get("value", "")
                        data["reference_range"]["high_unit"] = high_elem.get("unit", "")

            # Enhanced allergy-specific extraction
            # Extract criticality information - use safer XPath approach
            try:
                # Find COMP entryRelationships first, then search within them
                comp_entries = obs_elem.findall(".//hl7:entryRelationship[@typeCode='COMP']", namespaces)
                for comp_entry in comp_entries:
                    # Look for observation with CRIT code
                    crit_obs = comp_entry.find("hl7:observation", namespaces)
                    if crit_obs is not None:
                        crit_code = crit_obs.find("hl7:code", namespaces)
                        if crit_code is not None and crit_code.get("code") == "CRIT":
                            crit_value = crit_obs.find("hl7:value", namespaces)
                            if crit_value is not None:
                                data["criticality"] = crit_value.get("displayName", crit_value.get("code", ""))
                                break
            except Exception as e:
                # Criticality extraction failed, but continue processing
                pass

            # Extract certainty/verification status - use safer XPath approach
            try:
                # Find COMP entryRelationships first, then search within them
                comp_entries = obs_elem.findall(".//hl7:entryRelationship[@typeCode='COMP']", namespaces)
                for comp_entry in comp_entries:
                    # Look for observation with CERT code
                    cert_obs = comp_entry.find("hl7:observation", namespaces)
                    if cert_obs is not None:
                        cert_code = cert_obs.find("hl7:code", namespaces)
                        if cert_code is not None and cert_code.get("code") == "CERT":
                            cert_value = cert_obs.find("hl7:value", namespaces)
                            if cert_value is not None:
                                data["certainty"] = cert_value.get("displayName", cert_value.get("code", ""))
                                break
            except Exception as e:
                # Certainty extraction failed, but continue processing
                pass
            
            # Alternative certainty extraction from verification status
            if not data.get("certainty"):
                verification = obs_elem.find(".//hl7:verificationStatus", namespaces)
                if verification is not None:
                    data["certainty"] = verification.get("displayName", verification.get("code", ""))

            # Extract end date for allergy duration
            effective_time_high = obs_elem.find("hl7:effectiveTime/hl7:high", namespaces)
            if effective_time_high is not None:
                end_value = effective_time_high.get("value", "")
                if end_value:
                    data["end_date"] = self._format_hl7_datetime(end_value)

            # Extract reaction type (for allergies) - can be in code or separate observation
            if data.get("code") and not data.get("type_code"):
                data["type_code"] = data["code"]
                data["type_display"] = data.get("display", "Propensity to adverse reaction")

        except Exception as e:
            logger.error(f"Error extracting observation data: {e}")

        return data

    def _format_hl7_datetime(self, hl7_datetime: str) -> str:
        """Format HL7 datetime string to human readable format"""
        try:
            if not hl7_datetime:
                return ""

            # Strip whitespace and validate input
            hl7_datetime = hl7_datetime.strip()
            
            # Handle different HL7 datetime formats
            if len(hl7_datetime) >= 14:
                # YYYYMMDDHHMMSS format
                year = hl7_datetime[0:4]
                month = hl7_datetime[4:6]
                day = hl7_datetime[6:8]
                hour = hl7_datetime[8:10]
                minute = hl7_datetime[10:12]
                return f"{month}/{day}/{year} {hour}:{minute}"
            elif len(hl7_datetime) >= 8:
                # YYYYMMDD format
                year = hl7_datetime[0:4]
                month = hl7_datetime[4:6]
                day = hl7_datetime[6:8]
                return f"{month}/{day}/{year}"
            elif len(hl7_datetime) == 6:
                # YYYYMM format (year and month only)
                year = hl7_datetime[0:4]
                month = hl7_datetime[4:6]
                return f"{month}/{year}"
            elif len(hl7_datetime) == 4 and hl7_datetime.isdigit():
                # YYYY format (year only) - common in allergy onset/end dates
                return hl7_datetime
            else:
                # Fallback for unknown formats - return as-is
                return hl7_datetime
        except Exception:
            return hl7_datetime
        except Exception:
            return hl7_datetime

    def _convert_observation_to_structured_fields(
        self, obs_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """Convert observation data to structured fields format for table display"""
        fields = {}

        try:
            # Extract main observation name/type
            if obs_data.get("display"):
                fields["Observation Type"] = {"value": obs_data["display"]}

            # Extract the measured value with unit
            if obs_data.get("formatted_value"):
                if obs_data.get("value_type") == "quantity":
                    fields["Value"] = {"value": obs_data["formatted_value"]}
                else:
                    fields["Result"] = {"value": obs_data["formatted_value"]}
            elif obs_data.get("value"):
                fields["Value"] = {"value": str(obs_data["value"])}

            # Extract date/time information
            if obs_data.get("formatted_time"):
                fields["Date Performed"] = {"value": obs_data["formatted_time"]}
            elif obs_data.get("effective_time"):
                fields["Date Performed"] = {"value": obs_data["effective_time"]}

            # Extract status
            if obs_data.get("status"):
                fields["Status"] = {"value": obs_data["status"].title()}

            # Extract codes
            if obs_data.get("code"):
                fields["Code"] = {"value": obs_data["code"]}

            # Extract interpretation (normal, high, low, etc.)
            if obs_data.get("interpretation_display"):
                fields["Interpretation"] = {"value": obs_data["interpretation_display"]}
            elif obs_data.get("interpretation"):
                fields["Interpretation"] = {"value": obs_data["interpretation"]}

            # Extract reference range
            if obs_data.get("reference_range"):
                ref_range = obs_data["reference_range"]
                range_text = ""
                if ref_range.get("low"):
                    range_text += f"Low: {ref_range['low']}"
                    if ref_range.get("low_unit"):
                        range_text += f" {ref_range['low_unit']}"
                if ref_range.get("high"):
                    if range_text:
                        range_text += ", "
                    range_text += f"High: {ref_range['high']}"
                    if ref_range.get("high_unit"):
                        range_text += f" {ref_range['high_unit']}"
                if range_text:
                    fields["Reference Range"] = {"value": range_text}

            # For allergies - extract agent information
            if obs_data.get("agent_display"):
                fields["Allergen"] = {"value": obs_data["agent_display"]}
                if obs_data.get("agent_code"):
                    fields["Allergen Code"] = {"value": obs_data["agent_code"]}

            # Extract severity
            if obs_data.get("severity"):
                fields["Severity"] = {"value": obs_data["severity"]}

            # Extract manifestation (reaction)
            if obs_data.get("manifestation_display"):
                fields["Reaction"] = {"value": obs_data["manifestation_display"]}

            # For conditions/problems
            if obs_data.get("condition_display"):
                fields["Condition"] = {"value": obs_data["condition_display"]}
                if obs_data.get("condition_code"):
                    fields["Condition Code"] = {"value": obs_data["condition_code"]}

            # Extract onset date for problems/allergies
            if obs_data.get("onset_date"):
                fields["Onset Date"] = {"value": obs_data["onset_date"]}

            # Extract code system information
            if obs_data.get("code_system_name"):
                fields["Code System"] = {"value": obs_data["code_system_name"]}

            # Extract translation if available (for international display)
            if obs_data.get("translation_display"):
                fields["Local Name"] = {"value": obs_data["translation_display"]}

        except Exception as e:
            logger.error(f"Error converting observation to structured fields: {e}")

        return fields

    def _extract_procedure_data(self, procedure, namespaces) -> Dict[str, Any]:
        """Extract procedure data with enhanced code support and target site"""
        data = {}

        try:
            # Get procedure code with CTS integration
            code_elem = procedure.find("hl7:code", namespaces)
            if code_elem is not None:
                procedure_code = code_elem.get("code", "")
                code_system = code_elem.get("codeSystem", "")
                display_name = code_elem.get("displayName", "")
                
                data["procedure_code"] = procedure_code
                data["procedure_code_system"] = self._get_code_system_name(code_system)
                
                # Use CTS for procedure translation if display name is missing
                if display_name and display_name.strip():
                    data["procedure_display"] = display_name
                elif procedure_code and code_system:
                    # Use CTS to get procedure description
                    cts_procedure = self._lookup_valueset_term(procedure_code, "procedure")
                    data["procedure_display"] = cts_procedure or f"Procedure: {procedure_code}"
                else:
                    data["procedure_display"] = "Unknown Procedure"

            # Extract target site code with CTS integration  
            target_site_elem = procedure.find("hl7:targetSiteCode", namespaces)
            if target_site_elem is not None:
                target_site_code = target_site_elem.get("code", "")
                target_site_system = target_site_elem.get("codeSystem", "")
                target_site_display = target_site_elem.get("displayName", "")
                
                data["target_site_code"] = target_site_code
                data["target_site_code_system"] = self._get_code_system_name(target_site_system) if target_site_system else "SNOMED CT"
                
                # Use CTS for target site translation if display name is missing
                if target_site_display and target_site_display.strip():
                    data["target_site_display"] = target_site_display
                elif target_site_code and target_site_system:
                    # Use CTS to get target site description
                    cts_target_site = self._lookup_valueset_term(target_site_code, "anatomy") 
                    data["target_site_display"] = cts_target_site or f"Body Site: {target_site_code}"
                else:
                    data["target_site_display"] = "Not specified"

            # Extract effective time (date) with formatting
            effectiveTime = procedure.find("hl7:effectiveTime", namespaces)
            if effectiveTime is not None:
                time_value = effectiveTime.get("value", "")
                if time_value:
                    data["date"] = time_value
                    # Format the date for display
                    data["formatted_date"] = self._format_hl7_datetime(time_value)
                else:
                    data["date"] = "Not specified"
                    data["formatted_date"] = "Not specified"
            else:
                data["date"] = "Not specified"
                data["formatted_date"] = "Not specified"

            # Extract performer
            performer = procedure.find(
                ".//hl7:performer/hl7:assignedEntity/hl7:assignedPerson/hl7:name",
                namespaces,
            )
            if performer is not None:
                data["performer"] = performer.text or "Not specified"

            # Extract status
            status_code = procedure.find("hl7:statusCode", namespaces)
            if status_code is not None:
                data["status"] = status_code.get("code", "completed")

        except Exception as e:
            logger.error(f"Error extracting procedure data: {e}")

        return data

    def _extract_medical_device_data(self, device_elem, namespaces) -> Dict[str, Any]:
        """Extract medical device data with enhanced code support and usage details"""
        data = {}

        try:
            # Get device code with CTS integration
            code_elem = device_elem.find("hl7:code", namespaces)
            if code_elem is not None:
                device_code = code_elem.get("code", "")
                code_system = code_elem.get("codeSystem", "")
                display_name = code_elem.get("displayName", "")
                
                data["device_code"] = device_code
                data["device_code_system"] = self._get_code_system_name(code_system)
                
                # Use CTS for device translation if display name is missing
                if display_name and display_name.strip():
                    data["device_display"] = display_name
                elif device_code and code_system:
                    # Use CTS to get device description
                    cts_device = self._lookup_valueset_term(device_code, "device")
                    data["device_display"] = cts_device or f"Medical Device: {device_code}"
                else:
                    data["device_display"] = "Unknown Medical Device"

            # Extract participantRole for device-specific information
            participant_role = device_elem.find("hl7:participant/hl7:participantRole", namespaces)
            if participant_role is not None:
                # Get device name from participantRole
                device_name = participant_role.find("hl7:playingDevice/hl7:code", namespaces)
                if device_name is not None:
                    device_display = device_name.get("displayName", "")
                    if device_display and not data.get("device_display", "").startswith("Unknown"):
                        data["device_display"] = device_display

            # Extract effective time (usage period) with formatting
            effectiveTime = device_elem.find("hl7:effectiveTime", namespaces)
            if effectiveTime is not None:
                # Check for low/high time range (usage period)
                low_elem = effectiveTime.find("hl7:low", namespaces)
                high_elem = effectiveTime.find("hl7:high", namespaces)
                
                if low_elem is not None:
                    low_value = low_elem.get("value", "")
                    if low_value:
                        data["start_date"] = low_value
                        data["formatted_start_date"] = self._format_hl7_datetime(low_value)
                
                if high_elem is not None:
                    high_value = high_elem.get("value", "")
                    if high_value:
                        data["end_date"] = high_value
                        data["formatted_end_date"] = self._format_hl7_datetime(high_value)
                
                # Format usage period for display
                if data.get("formatted_start_date") and data.get("formatted_end_date"):
                    data["usage_period"] = f"{data['formatted_start_date']} - {data['formatted_end_date']}"
                elif data.get("formatted_start_date"):
                    data["usage_period"] = f"Since {data['formatted_start_date']}"
                else:
                    # Try single value for point in time
                    time_value = effectiveTime.get("value", "")
                    if time_value:
                        data["start_date"] = time_value
                        data["formatted_start_date"] = self._format_hl7_datetime(time_value)
                        data["usage_period"] = data["formatted_start_date"]

            # Set default if no time information
            if not data.get("usage_period"):
                data["usage_period"] = "Not specified"
                data["formatted_start_date"] = "Not specified"

            # Extract status
            status_code = device_elem.find("hl7:statusCode", namespaces)
            if status_code is not None:
                data["status"] = status_code.get("code", "active")
                # Map status codes to readable text
                status_map = {
                    "active": "Active",
                    "completed": "Completed", 
                    "cancelled": "Cancelled",
                    "suspended": "Suspended"
                }
                data["status_display"] = status_map.get(data["status"], data["status"].title())
            else:
                data["status"] = "active"
                data["status_display"] = "Active"

        except Exception as e:
            logger.error(f"Error extracting medical device data: {e}")

        return data

    def _extract_act_data(self, act_elem, namespaces) -> Dict[str, Any]:
        """Extract general act data"""
        data = {}

        try:
            # Get act code
            code_elem = act_elem.find("hl7:code", namespaces)
            if code_elem is not None:
                data["code"] = code_elem.get("code", "")
                data["display"] = code_elem.get("displayName", "Unknown Activity")
                data["code_system"] = self._get_code_system_name(
                    code_elem.get("codeSystem", "")
                )

            # Extract text/description
            text_elem = act_elem.find("hl7:text", namespaces)
            if text_elem is not None:
                data["description"] = text_elem.text or "No description"

            # Extract status
            status_code = act_elem.find("hl7:statusCode", namespaces)
            if status_code is not None:
                data["status"] = status_code.get("code", "active")

        except Exception as e:
            logger.error(f"Error extracting act data: {e}")

        return data

    def _extract_from_html_tables(self, entries, namespaces) -> List[Dict[str, Any]]:
        """Extract data from HTML tables if no structured CDA data is available"""
        structured_data = []

        try:
            # Look for HTML table content in the text elements
            for entry in entries:
                text_elem = entry.find(".//hl7:text", namespaces)
                if text_elem is not None:
                    # Parse HTML table content
                    html_content = ET.tostring(text_elem, encoding="unicode")
                    soup = BeautifulSoup(html_content, "html.parser")

                    tables = soup.find_all("table")
                    for table in tables:
                        rows = table.find_all("tr")
                        headers = []

                        # Get headers
                        if rows:
                            header_row = rows[0]
                            headers = [
                                th.get_text(strip=True)
                                for th in header_row.find_all(["th", "td"])
                            ]

                        # Process data rows
                        for row in rows[1:]:
                            cells = [
                                td.get_text(strip=True)
                                for td in row.find_all(["td", "th"])
                            ]
                            if len(cells) >= len(headers):
                                row_data = dict(zip(headers, cells))
                                structured_data.append(
                                    {
                                        "type": "html_table_row",
                                        "data": self._normalize_html_table_data(
                                            row_data
                                        ),
                                        "section_type": "table",
                                    }
                                )

        except Exception as e:
            logger.error(f"Error extracting from HTML tables: {e}")

        return structured_data

    def _normalize_html_table_data(self, row_data: Dict[str, str]) -> Dict[str, str]:
        """Normalize HTML table data to standard format"""
        normalized = {}

        # Map common table headers to standard fields
        header_mappings = {
            # Medications
            "brand name": "medication_display",
            "medication": "medication_display",
            "active ingredient": "ingredient_display",
            "ingredient": "ingredient_display",
            "dosage": "dosage",
            "dose": "dosage",
            "posology": "posology",
            "frequency": "posology",
            # Allergies
            "allergy type": "type_display",
            "causative agent": "agent_display",
            "agent": "agent_display",
            "manifestation": "manifestation_display",
            "reaction": "manifestation_display",
            "severity": "severity",
            # General
            "status": "status",
            "date": "date",
            "code": "code",
        }

        for original_key, value in row_data.items():
            normalized_key = header_mappings.get(
                original_key.lower(), original_key.lower().replace(" ", "_")
            )
            normalized[normalized_key] = value

        return normalized

    def _get_code_system_name(self, oid: str) -> str:
        """Convert OID to human-readable code system name"""
        oid_mappings = {
            "2.16.840.1.113883.6.1": "LOINC",
            "2.16.840.1.113883.6.96": "SNOMED",
            "2.16.840.1.113883.6.3": "ICD-10",
            "2.16.840.1.113883.6.73": "ATC",
            "2.16.840.1.113883.6.88": "RxNorm",
        }
        return oid_mappings.get(oid, "Unknown")

    def _generate_ps_tables(
        self,
        table_data: List[Dict],
        section_code: str,
        title: Dict,
        source_language: str,
    ) -> tuple:
        """Generate PS-compliant tables with actual coded medical data"""

        # Define column headers based on section type
        column_headers = self._get_section_column_headers(
            section_code, target_language=self.target_language
        )
        source_headers = self._get_section_column_headers(
            section_code, target_language=source_language
        )

        # Generate table rows with coded medical data
        enhanced_rows = self._generate_table_rows(
            table_data, section_code, target_language=self.target_language
        )
        original_rows = self._generate_table_rows(
            table_data, section_code, target_language=source_language
        )

        # Build enhanced table (target language)
        table_html = f"""
        <div class="ps-table-container">
            <div class="ps-table-header">
                <h4 class="ps-table-title">
                    <i class="fas fa-table me-2"></i>
                    {title['target']}
                    <span class="ps-compliance-badge">
                        <i class="fas fa-check-circle"></i>
                        PS Guidelines Compliant
                    </span>
                </h4>
            </div>
            <table class="table table-striped ps-compliant-table">
                <thead class="table-primary">
                    <tr>
                        {''.join([f'<th scope="col">{header}</th>' for header in column_headers])}
                        <th scope="col">
                            <i class="fas fa-code"></i> Code
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {enhanced_rows if enhanced_rows else self._get_no_data_row(len(column_headers) + 1, self.target_language)}
                </tbody>
            </table>
        </div>
        """

        # Build original table (source language)
        table_html_original = f"""
        <div class="ps-table-container">
            <div class="ps-table-header">
                <h4 class="ps-table-title">
                    <i class="fas fa-table me-2"></i>
                    {title['source']}
                </h4>
            </div>
            <table class="table table-striped ps-compliant-table">
                <thead class="table-secondary">
                    <tr>
                        {''.join([f'<th scope="col">{header}</th>' for header in source_headers])}
                        <th scope="col">
                            <i class="fas fa-code"></i> Code
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {original_rows if original_rows else self._get_no_data_row(len(source_headers) + 1, source_language)}
                </tbody>
            </table>
        </div>
        """

        return table_html, table_html_original

    def _get_section_column_headers(
        self, section_code: str, target_language: str = "en"
    ) -> List[str]:
        """Get appropriate column headers for different clinical sections"""

        headers_map = {
            "en": {
                "10160-0": [
                    "Medication",
                    "Active Ingredient",
                    "Dosage",
                    "Posology",
                    "Status",
                ],  # Medication History
                "48765-2": [
                    "Code",
                    "Reaction Type",
                    "Clinical Manifestation",
                    "Agent",
                    "Time",
                    "Severity",
                    "Criticality",
                    "Status",
                    "Certainty",
                ],  # Allergies
                "11450-4": [
                    "Condition",
                    "Status",
                    "Onset Date",
                    "Severity",
                    "Priority",
                ],  # Problem List
                "47519-4": [
                    "Procedure",
                    "Date",
                    "Performer",
                    "Status",
                    "Location",
                ],  # Procedures
                "30954-2": [
                    "Test",
                    "Result",
                    "Reference Range",
                    "Date",
                    "Status",
                ],  # Laboratory Results
                "10157-6": [
                    "Vaccine",
                    "Date",
                    "Dose",
                    "Route",
                    "Status",
                ],  # Immunizations
                "18776-5": [
                    "Treatment",
                    "Instructions",
                    "Duration",
                    "Frequency",
                    "Status",
                ],  # Treatment Plan
                "default": ["Item", "Description", "Value", "Date", "Status"],
            },
            "fr": {
                "10160-0": [
                    "Médicament",
                    "Principe actif",
                    "Dosage",
                    "Posologie",
                    "Statut",
                ],
                "48765-2": [
                    "Code",
                    "Type de réaction",
                    "Manifestation clinique",
                    "Agent",
                    "Durée",
                    "Sévérité",
                    "Criticité",
                    "Statut",
                    "Certitude",
                ],
                "11450-4": [
                    "Condition",
                    "Statut",
                    "Date d'apparition",
                    "Sévérité",
                    "Priorité",
                ],
                "47519-4": ["Procédure", "Date", "Exécutant", "Statut", "Lieu"],
                "30954-2": ["Test", "Résultat", "Plage de référence", "Date", "Statut"],
                "10157-6": ["Vaccin", "Date", "Dose", "Voie", "Statut"],
                "18776-5": [
                    "Traitement",
                    "Instructions",
                    "Durée",
                    "Fréquence",
                    "Statut",
                ],
                "default": ["Élément", "Description", "Valeur", "Date", "Statut"],
            },
            "de": {
                "10160-0": [
                    "Medikament",
                    "Wirkstoff",
                    "Dosierung",
                    "Anwendung",
                    "Status",
                ],
                "48765-2": [
                    "Code",
                    "Reaktionstyp",
                    "Klinische Manifestation",
                    "Auslöser",
                    "Zeit",
                    "Schweregrad",
                    "Kritikalität",
                    "Status",
                    "Gewissheit",
                ],
                "11450-4": [
                    "Erkrankung",
                    "Status",
                    "Beginn",
                    "Schweregrad",
                    "Priorität",
                ],
                "47519-4": ["Eingriff", "Datum", "Durchführer", "Status", "Ort"],
                "30954-2": ["Test", "Ergebnis", "Referenzbereich", "Datum", "Status"],
                "10157-6": ["Impfstoff", "Datum", "Dosis", "Verabreichung", "Status"],
                "18776-5": [
                    "Behandlung",
                    "Anweisungen",
                    "Dauer",
                    "Häufigkeit",
                    "Status",
                ],
                "default": ["Element", "Beschreibung", "Wert", "Datum", "Status"],
            },
            "it": {
                "10160-0": [
                    "Farmaco",
                    "Principio attivo",
                    "Dosaggio",
                    "Posologia",
                    "Stato",
                ],
                "48765-2": [
                    "Codice",
                    "Tipo di reazione",
                    "Manifestazione clinica",
                    "Agente",
                    "Tempo",
                    "Gravità",
                    "Criticità",
                    "Stato",
                    "Certezza",
                ],
                "11450-4": [
                    "Condizione",
                    "Stato",
                    "Data insorgenza",
                    "Gravità",
                    "Priorità",
                ],
                "47519-4": ["Procedura", "Data", "Esecutore", "Stato", "Luogo"],
                "30954-2": ["Test", "Risultato", "Range riferimento", "Data", "Stato"],
                "10157-6": ["Vaccino", "Data", "Dose", "Via", "Stato"],
                "18776-5": [
                    "Trattamento",
                    "Istruzioni",
                    "Durata",
                    "Frequenza",
                    "Stato",
                ],
                "default": ["Elemento", "Descrizione", "Valore", "Data", "Stato"],
            },
        }

        # Get headers for target language, fallback to English, then default
        lang_headers = headers_map.get(target_language, headers_map["en"])
        return lang_headers.get(section_code, lang_headers["default"])

    def _generate_table_rows(
        self, table_data: List[Dict], section_code: str, target_language: str = "en"
    ) -> str:
        """Generate HTML table rows with coded medical data"""

        if not table_data:
            return ""

        rows_html = []

        for item in table_data:
            try:
                # Extract coded data based on section type
                if section_code == "10160-0":  # Medication History
                    row_html = self._generate_medication_row(item, target_language)
                elif section_code == "48765-2":  # Allergies
                    row_html = self._generate_allergy_row(item, target_language)
                elif section_code == "11450-4":  # Problem List
                    row_html = self._generate_problem_row(item, target_language)
                elif section_code == "47519-4":  # Procedures
                    row_html = self._generate_procedure_row(item, target_language)
                elif section_code == "30954-2":  # Laboratory Results
                    row_html = self._generate_lab_result_row(item, target_language)
                elif section_code == "10157-6":  # Immunizations
                    row_html = self._generate_immunization_row(item, target_language)
                else:
                    # Generic row for unknown section types
                    row_html = self._generate_generic_row(item, target_language)

                if row_html:
                    rows_html.append(row_html)

            except Exception as e:
                logger.error(f"Error generating table row: {e}")
                continue

        return "\n".join(rows_html)

    def _generate_medication_row(self, item: Dict, target_language: str) -> str:
        """Generate medication table row with coded medical data"""

        # Extract medication data from item
        data = item.get("data", {})

        # Use terminology service to translate coded values
        medication_name = self._translate_coded_value(
            data.get("medication_code", ""),
            data.get("medication_display", "Unknown Medication"),
            target_language,
        )

        active_ingredient = self._translate_coded_value(
            data.get("ingredient_code", ""),
            data.get("ingredient_display", "Unknown Ingredient"),
            target_language,
        )

        dosage = data.get("dosage", "Not specified")
        posology = data.get("posology", "As directed")
        status = self._translate_status(data.get("status", "active"), target_language)

        # Generate code badge
        code_badge = self._generate_code_badge(
            data.get("medication_code", ""), data.get("code_system", "")
        )

        return f"""
        <tr>
            <td><strong>{medication_name}</strong></td>
            <td>{active_ingredient}</td>
            <td>{dosage}</td>
            <td>{posology}</td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'active'))}">{status}</span>
            </td>
            <td>{code_badge}</td>
        </tr>
        """

    def _generate_allergy_row(self, item: Dict, target_language: str) -> str:
        """Generate allergy table row with coded medical data for all 9 columns"""

        data = item.get("data", {})

        # 1. Code - Extract observation code (main allergy code)
        observation_code = data.get("code", "")
        code_badge = self._generate_code_badge(
            observation_code, data.get("code_system", "")
        )

        # 2. Reaction Type - Extract allergy type from observation or value
        reaction_type = self._translate_coded_value(
            data.get("type_code", data.get("code", "")),
            data.get("type_display", data.get("display", "Propensity to adverse reaction")),
            target_language,
        )

        # 3. Clinical Manifestation - Extract manifestation details
        manifestation = self._translate_coded_value(
            data.get("manifestation_code", ""),
            data.get("manifestation_display", "Unknown Reaction"),
            target_language,
        )

        # 4. Agent - Extract causative agent
        causative_agent = self._translate_coded_value(
            data.get("agent_code", ""),
            data.get("agent_display", "Unknown Agent"),
            target_language,
        )

        # 5. Time - Extract timing information with enhanced date range handling
        time_info = ""
        onset_date = data.get("onset_date", "")
        end_date = data.get("end_date", "")
        
        # Handle date ranges intelligently
        if onset_date and end_date:
            # Both start and end dates available - create a date range
            if onset_date == end_date:
                # Same date
                time_info = onset_date
            else:
                # Different dates - show as range
                time_info = f"{onset_date} - {end_date}"
        elif onset_date:
            # Only start date available
            time_info = f"From {onset_date}"
        elif end_date:
            # Only end date available (unusual but possible)
            time_info = f"Until {end_date}"
        elif data.get("formatted_time"):
            # Use formatted effective time
            time_info = data["formatted_time"]
        elif data.get("effective_time"):
            # Use raw effective time, format it
            time_info = self._format_hl7_datetime(data["effective_time"])
        else:
            time_info = "Unknown"

        # 6. Severity - Extract and translate severity
        severity = self._translate_severity(
            data.get("severity", "unknown"), target_language
        )

        # 7. Criticality - Extract criticality information (usually found in nested observations)
        criticality = data.get("criticality", "")
        if not criticality:
            # Infer criticality from severity for display purposes
            severity_lower = data.get("severity", "").lower()
            if "severe" in severity_lower or "life threatening" in severity_lower:
                criticality = "High"
            elif "moderate" in severity_lower:
                criticality = "Medium"
            elif "mild" in severity_lower:
                criticality = "Low"
            else:
                criticality = "Unknown"

        # 8. Status - Extract and translate status
        status = self._translate_status(data.get("status", "active"), target_language)

        # 9. Certainty - Extract certainty information
        certainty = data.get("certainty", "")
        if not certainty:
            # Common certainty values in CDA: confirmed, probable, possible, suspected
            certainty = data.get("certainty_display", "Unknown")

        return f"""
        <tr>
            <td>{code_badge}</td>
            <td>{reaction_type}</td>
            <td>{manifestation}</td>
            <td><strong>{causative_agent}</strong></td>
            <td>{time_info}</td>
            <td>
                <span class="badge bg-{self._get_severity_color(data.get('severity', 'unknown'))}">{severity}</span>
            </td>
            <td>
                <span class="badge bg-{self._get_criticality_color(criticality.lower())}">{criticality}</span>
            </td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'active'))}">{status}</span>
            </td>
            <td>{certainty}</td>
        </tr>
        """

    def _generate_generic_row(self, item: Dict, target_language: str) -> str:
        """Generate generic table row for unknown section types"""

        data = item.get("data", {})

        # Extract basic information
        display_name = self._translate_coded_value(
            data.get("code", ""), data.get("display", "Unknown Item"), target_language
        )

        description = data.get("description", "No description available")
        value = data.get("value", "Not specified")
        date = data.get("date", "Not specified")
        status = self._translate_status(data.get("status", "unknown"), target_language)

        code_badge = self._generate_code_badge(
            data.get("code", ""), data.get("code_system", "")
        )

        return f"""
        <tr>
            <td><strong>{display_name}</strong></td>
            <td>{description}</td>
            <td>{value}</td>
            <td>{date}</td>
            <td>
                <span class="badge bg-secondary">{status}</span>
            </td>
            <td>{code_badge}</td>
        </tr>
        """

    def _translate_coded_value(
        self, code: str, display: str, target_language: str
    ) -> str:
        """Translate a coded medical value using the terminology service"""

        if not code or not display:
            return display or "Unknown"

        try:
            # Use the terminology service to translate with SNOMED CT system as default
            # Most clinical codes in CDA are SNOMED CT (2.16.840.1.113883.6.96)
            translated = self.terminology_service._translate_term(
                code=code, system="2.16.840.1.113883.6.96", original_display=display
            )

            if translated and translated.get("display"):
                return translated.get("display", display)
            else:
                return display

        except Exception as e:
            logger.error(f"Error translating coded value {code}: {e}")
            return display

    def _translate_status(self, status: str, target_language: str) -> str:
        """Translate status values"""
        status_translations = {
            "en": {
                "active": "Active",
                "inactive": "Inactive",
                "completed": "Completed",
                "cancelled": "Cancelled",
                "unknown": "Unknown",
            },
            "fr": {
                "active": "Actif",
                "inactive": "Inactif",
                "completed": "Terminé",
                "cancelled": "Annulé",
                "unknown": "Inconnu",
            },
            "de": {
                "active": "Aktiv",
                "inactive": "Inaktiv",
                "completed": "Abgeschlossen",
                "cancelled": "Abgebrochen",
                "unknown": "Unbekannt",
            },
            "it": {
                "active": "Attivo",
                "inactive": "Inattivo",
                "completed": "Completato",
                "cancelled": "Annullato",
                "unknown": "Sconosciuto",
            },
        }

        lang_map = status_translations.get(target_language, status_translations["en"])
        return lang_map.get(status.lower(), status.title())

    def _translate_severity(self, severity: str, target_language: str) -> str:
        """Translate severity values"""
        severity_translations = {
            "en": {
                "mild": "Mild",
                "moderate": "Moderate",
                "severe": "Severe",
                "unknown": "Unknown",
            },
            "fr": {
                "mild": "Léger",
                "moderate": "Modéré",
                "severe": "Sévère",
                "unknown": "Inconnu",
            },
            "de": {
                "mild": "Leicht",
                "moderate": "Mäßig",
                "severe": "Schwer",
                "unknown": "Unbekannt",
            },
            "it": {
                "mild": "Lieve",
                "moderate": "Moderato",
                "severe": "Grave",
                "unknown": "Sconosciuto",
            },
        }

        lang_map = severity_translations.get(
            target_language, severity_translations["en"]
        )
        return lang_map.get(severity.lower(), severity.title())

    def _generate_code_badge(self, code: str, code_system: str) -> str:
        """Generate a visual badge for medical codes"""

        if not code:
            return '<span class="badge bg-light text-dark">No Code</span>'

        # Determine code system color
        system_colors = {
            "LOINC": "primary",
            "SNOMED": "success",
            "ICD-10": "info",
            "ATC": "warning",
            "RxNorm": "secondary",
        }

        color = system_colors.get(code_system, "dark")

        return f"""
        <span class="badge bg-{color}" title="{code_system}: {code}">
            <i class="fas fa-code"></i> {code}
        </span>
        """

    def _get_status_color(self, status: str) -> str:
        """Get Bootstrap color class for status"""
        color_map = {
            "active": "success",
            "inactive": "secondary",
            "completed": "primary",
            "cancelled": "danger",
            "unknown": "warning",
        }
        return color_map.get(status.lower(), "secondary")

    def _get_severity_color(self, severity: str) -> str:
        """Get Bootstrap color class for severity"""
        color_map = {
            "mild": "success",
            "moderate": "warning",
            "severe": "danger",
            "unknown": "secondary",
        }
        return color_map.get(severity.lower(), "secondary")

    def _get_criticality_color(self, criticality: str) -> str:
        """Get Bootstrap color class for criticality"""
        color_map = {
            "low": "success",
            "medium": "warning", 
            "high": "danger",
            "unknown": "secondary",
        }
        return color_map.get(criticality.lower(), "secondary")

    def _get_no_data_row(self, colspan: int, language: str) -> str:
        """Generate a 'no data' row in the appropriate language"""

        no_data_text = {
            "en": "No clinical data available for this section",
            "fr": "Aucune donnée clinique disponible pour cette section",
            "de": "Keine klinischen Daten für diesen Abschnitt verfügbar",
            "it": "Nessun dato clinico disponibile per questa sezione",
            "es": "No hay datos clínicos disponibles para esta sección",
            "pt": "Nenhum dado clínico disponível para esta seção",
        }

        text = no_data_text.get(language, no_data_text["en"])

        return f"""
        <tr>
            <td colspan="{colspan}" class="text-center text-muted">
                <em><i class="fas fa-info-circle"></i> {text}</em>
            </td>
        </tr>
        """

    def _generate_problem_row(self, item: Dict, target_language: str) -> str:
        """Generate problem/condition table row with coded medical data"""

        data = item.get("data", {})

        # Use condition fields if available, fallback to generic fields
        condition_code = data.get("condition_code", data.get("agent_code", ""))
        condition_display = data.get(
            "condition_display",
            data.get("agent_display", data.get("value", "Unknown Condition")),
        )

        condition = self._translate_coded_value(
            condition_code,
            condition_display,
            target_language,
        )

        status = self._translate_status(data.get("status", "active"), target_language)
        onset_date = data.get("onset_date", "Not specified")
        severity = self._translate_severity(
            data.get("severity", "unknown"), target_language
        )
        priority = data.get("priority", "Normal")

        code_badge = self._generate_code_badge(
            condition_code, data.get("condition_system", data.get("code_system", ""))
        )

        return f"""
        <tr>
            <td><strong>{condition}</strong></td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'active'))}">{status}</span>
            </td>
            <td>{onset_date}</td>
            <td>
                <span class="badge bg-{self._get_severity_color(data.get('severity', 'unknown'))}">{severity}</span>
            </td>
            <td>{priority}</td>
            <td>{code_badge}</td>
        </tr>
        """

    def _generate_procedure_row(self, item: Dict, target_language: str) -> str:
        """Generate procedure table row with coded medical data"""

        data = item.get("data", {})

        procedure = self._translate_coded_value(
            data.get("procedure_code", ""),
            data.get("procedure_display", "Unknown Procedure"),
            target_language,
        )

        date = data.get("date", "Not specified")
        performer = data.get("performer", "Not specified")
        status = self._translate_status(
            data.get("status", "completed"), target_language
        )
        location = data.get("location", "Not specified")

        code_badge = self._generate_code_badge(
            data.get("procedure_code", ""), data.get("code_system", "")
        )

        return f"""
        <tr>
            <td><strong>{procedure}</strong></td>
            <td>{date}</td>
            <td>{performer}</td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'completed'))}">{status}</span>
            </td>
            <td>{location}</td>
            <td>{code_badge}</td>
        </tr>
        """

    def _generate_lab_result_row(self, item: Dict, target_language: str) -> str:
        """Generate laboratory result table row with coded medical data"""

        data = item.get("data", {})

        test_name = self._translate_coded_value(
            data.get("test_code", ""),
            data.get("test_display", "Unknown Test"),
            target_language,
        )

        result = data.get("result", "Pending")
        reference_range = data.get("reference_range", "Not available")
        date = data.get("date", "Not specified")
        status = self._translate_status(data.get("status", "final"), target_language)

        code_badge = self._generate_code_badge(
            data.get("test_code", ""), data.get("code_system", "LOINC")
        )

        return f"""
        <tr>
            <td><strong>{test_name}</strong></td>
            <td>{result}</td>
            <td>{reference_range}</td>
            <td>{date}</td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'final'))}">{status}</span>
            </td>
            <td>{code_badge}</td>
        </tr>
        """

    def _generate_immunization_row(self, item: Dict, target_language: str) -> str:
        """Generate immunization table row with coded medical data"""

        data = item.get("data", {})

        vaccine = self._translate_coded_value(
            data.get("vaccine_code", ""),
            data.get("vaccine_display", "Unknown Vaccine"),
            target_language,
        )

        date = data.get("date", "Not specified")
        dose = data.get("dose", "Not specified")
        route = data.get("route", "Not specified")
        status = self._translate_status(
            data.get("status", "completed"), target_language
        )

        code_badge = self._generate_code_badge(
            data.get("vaccine_code", ""), data.get("code_system", "")
        )

        return f"""
        <tr>
            <td><strong>{vaccine}</strong></td>
            <td>{date}</td>
            <td>{dose}</td>
            <td>{route}</td>
            <td>
                <span class="badge bg-{self._get_status_color(data.get('status', 'completed'))}">{status}</span>
            </td>
            <td>{code_badge}</td>
        </tr>
        """

    def _generate_ps_tables_from_html(
        self, table_elem, title: Dict, source_language: str
    ) -> tuple:
        """Generate PS-compliant tables from existing HTML table"""

        # Enhanced table with PS guidelines styling
        enhanced_table = f"""
        <div class="ps-table-container">
            <div class="ps-table-header">
                <h4 class="ps-table-title">
                    <i class="fas fa-table me-2"></i>
                    {title['target']}
                    <span class="ps-compliance-badge">
                        <i class="fas fa-check-circle"></i>
                        PS Guidelines Compliant
                    </span>
                </h4>
            </div>
            <div class="ps-table-content">
                {str(table_elem)}
            </div>
        </div>
        """

        # Original table with minimal styling
        original_table = f"""
        <div class="ps-table-container">
            <div class="ps-table-header">
                <h4 class="ps-table-title">
                    <i class="fas fa-table me-2"></i>
                    {title['source']}
                </h4>
            </div>
            <div class="ps-table-content">
                {str(table_elem)}
            </div>
        </div>
        """

        return enhanced_table, original_table

    def _extract_table_data(self, table_elem) -> List[Dict]:
        """Extract data from HTML table for processing"""
        data = []

        rows = table_elem.find_all("tr")
        headers = []

        # Get headers from first row
        if rows:
            header_cells = rows[0].find_all(["th", "td"])
            headers = [cell.get_text().strip() for cell in header_cells]

        # Get data from remaining rows
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_data[headers[i]] = cell.get_text().strip()
            if row_data:
                data.append(row_data)

        return data

    def _xml_to_html(self, xml_elem) -> str:
        """Convert XML element to HTML for display"""
        # Simplified conversion - would be more sophisticated in practice
        content = ""

        if xml_elem.text:
            content += xml_elem.text

        for child in xml_elem:
            if child.tag.endswith("table"):
                content += self._convert_xml_table_to_html(child)
            elif child.tag.endswith("paragraph"):
                content += f"<p>{child.text or ''}</p>"
            else:
                content += child.text or ""

            if child.tail:
                content += child.tail

        return content

    def _convert_xml_table_to_html(self, table_elem) -> str:
        """Convert XML table to HTML table"""
        html = "<table class='cda-table'>"

        # Process table content - simplified
        for row in table_elem.findall(".//tr"):
            html += "<tr>"
            for cell in row.findall(".//td"):
                html += f"<td>{cell.text or ''}</td>"
            html += "</tr>"

        html += "</table>"
        return html

    def _translate_content(self, content: str, source_language: str) -> str:
        """Translate content using CTS-compliant terminology service"""
        try:
            # Use terminology service for comprehensive translation
            translation_result = self.terminology_service.translate_clinical_document(
                document_content=content, source_language=source_language
            )

            if translation_result and translation_result.get("content"):
                logger.info(
                    f"CTS translation applied, {translation_result.get('translations_applied', 0)} terms translated"
                )
                return translation_result["content"]

            # Fallback: Extract and translate medical terms individually
            return self._translate_medical_terms_in_content(content, source_language)

        except Exception as e:
            logger.error(f"Error in CTS content translation: {e}")
            return content  # Return original content on error

    def _translate_medical_terms_in_content(
        self, content: str, source_language: str
    ) -> str:
        """Translate medical terms in content using MVC lookups"""
        try:
            # Extract potential medical terms
            medical_term_patterns = [
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",  # Capitalized terms
                r"\b\d+[\.,]\d+\s*(?:mg|ml|g|l|%)\b",  # Dosages
                r"\b(?:Dr|Prof|Docteur)\.?\s+[A-Z][a-z]+\b",  # Medical titles
            ]

            translated_content = content
            translation_count = 0

            for pattern in medical_term_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    term = match.group()
                    translated_term = self._lookup_term_in_mvc(term, source_language)
                    if translated_term and translated_term != term:
                        translated_content = translated_content.replace(
                            term, translated_term
                        )
                        translation_count += 1

            if translation_count > 0:
                logger.info(
                    f"MVC-based translation: {translation_count} terms translated"
                )

            return translated_content

        except Exception as e:
            logger.error(f"Error in MVC-based content translation: {e}")
            return content

    def _lookup_term_in_mvc(self, term: str, source_language: str) -> Optional[str]:
        """Look up term translation in Master Value Catalogue"""
        try:
            # Search for concept with matching display text
            concept = self.ValueSetConcept.objects.filter(
                display__iexact=term.strip(), status="active"
            ).first()

            if not concept:
                # Try partial match
                concept = self.ValueSetConcept.objects.filter(
                    display__icontains=term.strip(), status="active"
                ).first()

            if concept:
                # Get translation for target language
                translation = self.ConceptTranslation.objects.filter(
                    concept=concept, language_code=self.target_language
                ).first()

                if translation:
                    return translation.translated_display

            return None

        except Exception as e:
            logger.error(f"Error looking up term '{term}' in MVC: {e}")
            return None

    def _extract_patient_identity(
        self, root: ET.Element, namespaces: Dict, field_mapper
    ) -> Dict[str, Any]:
        """
        Extract patient identity data using field mapper - NO TRANSLATION needed
        """
        patient_identity = {
            "given_name": None,
            "family_name": None,
            "birth_date": None,
            "gender": None,
            "patient_identifiers": [],
            "primary_patient_id": None,
            "secondary_patient_id": None,
        }

        try:
            # Get Patient Block field mappings from the JSON
            patient_fields = field_mapper.get_patient_fields()

            for field in patient_fields:
                label = field.get("label", "")
                xpath = field.get("xpath", "")
                translation_needed = field.get("translation", "NO").upper() == "YES"

                # Skip if translation is needed - we only want direct CDA data here
                if translation_needed:
                    continue

                # Convert to namespaced XPath
                namespaced_xpath = field_mapper.convert_xpath_to_namespaced(xpath)

                try:
                    if label == "Given Name":
                        elem = root.find(namespaced_xpath, namespaces)
                        if elem is not None:
                            patient_identity["given_name"] = elem.text

                    elif label == "Family Name":
                        elem = root.find(namespaced_xpath, namespaces)
                        if elem is not None:
                            patient_identity["family_name"] = elem.text

                    elif label == "Birthdate":
                        # Handle @value attribute extraction properly
                        if "/@" in namespaced_xpath:
                            elem_path = namespaced_xpath.split("/@")[0]
                            attr_name = namespaced_xpath.split("/@")[1]
                            elem = root.find(elem_path, namespaces)
                            if elem is not None:
                                patient_identity["birth_date"] = elem.get(attr_name)
                        else:
                            elem = root.find(namespaced_xpath, namespaces)
                            if elem is not None:
                                patient_identity["birth_date"] = elem.text

                    elif label == "Gender":
                        # Handle @code attribute extraction properly
                        if "/@" in namespaced_xpath:
                            elem_path = namespaced_xpath.split("/@")[0]
                            attr_name = namespaced_xpath.split("/@")[1]
                            elem = root.find(elem_path, namespaces)
                            if elem is not None:
                                patient_identity["gender"] = elem.get(attr_name)
                        else:
                            elem = root.find(namespaced_xpath, namespaces)
                            if elem is not None:
                                patient_identity["gender"] = elem.text

                    elif label == "Primary Patient ID":
                        # Handle @extension attribute extraction properly
                        if "/@" in namespaced_xpath:
                            elem_path = namespaced_xpath.split("/@")[0]
                            attr_name = namespaced_xpath.split("/@")[1]
                            elem = root.find(elem_path, namespaces)
                            if elem is not None:
                                primary_id = elem.get(attr_name)
                                root_attr = elem.get("root")
                                patient_identity["primary_patient_id"] = primary_id

                                # Add to identifiers array
                                if primary_id:
                                    patient_identity["patient_identifiers"].append(
                                        {
                                            "extension": primary_id,
                                            "root": root_attr,
                                            "type": "Primary",
                                        }
                                    )

                    elif label == "Secondary Patient ID":
                        # Handle @extension attribute extraction properly
                        if "/@" in namespaced_xpath:
                            elem_path = namespaced_xpath.split("/@")[0]
                            attr_name = namespaced_xpath.split("/@")[1]
                            elem = root.find(elem_path, namespaces)
                            if elem is not None:
                                secondary_id = elem.get(attr_name)
                                root_attr = elem.get("root")
                                patient_identity["secondary_patient_id"] = secondary_id

                                # Add to identifiers array
                                if secondary_id:
                                    patient_identity["patient_identifiers"].append(
                                        {
                                            "extension": secondary_id,
                                            "root": root_attr,
                                            "type": "Secondary",
                                        }
                                    )

                except Exception as field_error:
                    logger.warning(
                        f"Error extracting {label} with XPath {namespaced_xpath}: {field_error}"
                    )
                    continue

            logger.info(
                f"Extracted patient identity - Name: {patient_identity.get('given_name')} {patient_identity.get('family_name')}, "
                f"Birth: {patient_identity.get('birth_date')}, Gender: {patient_identity.get('gender')}, "
                f"Primary ID: {patient_identity.get('primary_patient_id')}, "
                f"Identifiers: {len(patient_identity['patient_identifiers'])}"
            )
            return patient_identity

        except Exception as e:
            logger.error(f"Error extracting patient identity: {e}")

            # Fallback: try to extract at least the patient ID using simple method
            try:
                patient_id = self._extract_patient_id(
                    ET.tostring(root, encoding="unicode")
                )
                if patient_id:
                    patient_identity["primary_patient_id"] = patient_id
                    patient_identity["patient_id"] = patient_id  # Add convenient access
                    logger.info(
                        f"Fallback patient ID extraction successful: {patient_id}"
                    )
            except Exception as fallback_e:
                logger.error(
                    f"Fallback patient ID extraction also failed: {fallback_e}"
                )

            return patient_identity

    def _extract_patient_id(self, xml_content: str) -> Optional[str]:
        """
        Extract patient ID from CDA XML content
        """
        try:
            root = ET.fromstring(xml_content)
            namespaces = self._get_xml_namespaces(root)

            # Look for patient ID in various locations
            patient_id_paths = [
                ".//hl7:recordTarget/hl7:patientRole/hl7:id/@extension",
                ".//hl7:recordTarget/hl7:patientRole/hl7:id/@root",
                ".//hl7:patient/hl7:id/@extension",
                ".//hl7:patient/hl7:id/@root",
            ]

            for path in patient_id_paths:
                try:
                    result = root.xpath(path, namespaces=namespaces)
                    if result and result[0]:
                        return str(result[0])
                except:
                    # Try with findall if xpath not available
                    path_parts = path.replace("@", "").split("/")
                    elements = root.findall("//".join(path_parts[:-1]), namespaces)
                    for elem in elements:
                        attr_name = path_parts[-1]
                        if attr_name in elem.attrib:
                            return elem.attrib[attr_name]

            return None

        except Exception as e:
            logger.warning(f"Could not extract patient ID: {e}")
            return None

    def _simple_patient_id_extraction(
        self, root: ET.Element, namespaces: Dict
    ) -> Dict[str, Any]:
        """
        Comprehensive patient identity extraction based on EHDSI templates
        Extracts all available demographic and header information
        """
        patient_identity = {
            "given_name": None,
            "family_name": None,
            "birth_date": None,
            "gender": None,
            "patient_identifiers": [],
            "primary_patient_id": None,
            "secondary_patient_id": None,
        }

        try:
            # Extract comprehensive patient demographics following EHDSI structure
            patient_role = root.find(".//hl7:recordTarget/hl7:patientRole", namespaces)

            if patient_role is not None:
                patient = patient_role.find("hl7:patient", namespaces)

                if patient is not None:
                    # Patient name - extract all components
                    name_elem = patient.find("hl7:name", namespaces)
                    if name_elem is not None:
                        given_elem = name_elem.find("hl7:given", namespaces)
                        family_elem = name_elem.find("hl7:family", namespaces)
                        prefix_elem = name_elem.find("hl7:prefix", namespaces)
                        suffix_elem = name_elem.find("hl7:suffix", namespaces)

                        patient_identity["given_name"] = (
                            given_elem.text
                            if given_elem is not None and given_elem.text
                            else None
                        )
                        patient_identity["family_name"] = (
                            family_elem.text
                            if family_elem is not None and family_elem.text
                            else None
                        )
                        patient_identity["prefix"] = (
                            prefix_elem.text
                            if prefix_elem is not None and prefix_elem.text
                            else None
                        )
                        patient_identity["suffix"] = (
                            suffix_elem.text
                            if suffix_elem is not None and suffix_elem.text
                            else None
                        )

                        # Create full name for display
                        name_parts = []
                        if patient_identity["prefix"]:
                            name_parts.append(patient_identity["prefix"])
                        if patient_identity["given_name"]:
                            name_parts.append(patient_identity["given_name"])
                        if patient_identity["family_name"]:
                            name_parts.append(patient_identity["family_name"])
                        if patient_identity["suffix"]:
                            name_parts.append(patient_identity["suffix"])

                        patient_identity["full_name"] = (
                            " ".join(name_parts) if name_parts else None
                        )

                    # Gender
                    gender_elem = patient.find(
                        "hl7:administrativeGenderCode", namespaces
                    )
                    if gender_elem is not None:
                        patient_identity["gender"] = gender_elem.get(
                            "displayName"
                        ) or gender_elem.get("code")
                        patient_identity["gender_code"] = gender_elem.get("code")

                    # Birth date
                    birth_time = patient.find("hl7:birthTime", namespaces)
                    if birth_time is not None:
                        birth_value = birth_time.get("value")
                        patient_identity["birth_date"] = birth_value

                        # Format birth date for display
                        if birth_value and len(birth_value) >= 8:
                            try:
                                year = birth_value[:4]
                                month = birth_value[4:6]
                                day = birth_value[6:8]
                                patient_identity["birth_date_formatted"] = (
                                    f"{day}/{month}/{year}"
                                )
                            except:
                                patient_identity["birth_date_formatted"] = birth_value

                # Patient identifiers - extract all IDs
                id_elements = patient_role.findall("hl7:id", namespaces)
                for i, id_elem in enumerate(id_elements):
                    extension = id_elem.get("extension")
                    root_id = id_elem.get("root")

                    if extension and extension != "N/A":
                        identifier = {
                            "extension": extension,
                            "root": root_id,
                            "type": "primary" if i == 0 else "secondary",
                        }
                        patient_identity["patient_identifiers"].append(identifier)

                        # Set primary and secondary IDs
                        if i == 0:
                            patient_identity["primary_patient_id"] = extension
                            patient_identity["patient_id"] = (
                                extension  # Convenient access
                            )
                        elif i == 1:
                            patient_identity["secondary_patient_id"] = extension

                # Extract document metadata
                patient_identity["document_metadata"] = self._extract_document_metadata(
                    root, namespaces
                )

                logger.info(
                    f"Comprehensive extraction - Name: {patient_identity.get('full_name')}, "
                    f"Birth: {patient_identity.get('birth_date_formatted')}, "
                    f"Gender: {patient_identity.get('gender')}, "
                    f"ID: {patient_identity.get('patient_id')}"
                )

                return patient_identity

            logger.warning("Comprehensive patient extraction found no patient role")
            return patient_identity

        except Exception as e:
            logger.error(f"Comprehensive patient extraction failed: {e}")
            return patient_identity

    def _extract_document_metadata(
        self, root: ET.Element, namespaces: Dict
    ) -> Dict[str, Any]:
        """Extract document metadata"""
        metadata = {}

        try:
            # Document creation date
            effective_time = root.find(".//hl7:effectiveTime", namespaces)
            if effective_time is not None:
                metadata["creation_date"] = effective_time.get("value")

            # Document title
            title = root.find(".//hl7:title", namespaces)
            if title is not None:
                metadata["title"] = title.text

            # Document language
            language_code = root.find(".//hl7:languageCode", namespaces)
            if language_code is not None:
                metadata["language_code"] = language_code.get("code")

        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")

        return metadata

    def _extract_administrative_data(
        self, root: ET.Element, namespaces: Dict
    ) -> Dict[str, Any]:
        """
        Extract administrative data from CDA - basic implementation
        """
        admin_data = {
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
        }

        try:
            # Extract document creation date
            effective_time = root.find("hl7:effectiveTime", namespaces)
            if effective_time is not None:
                admin_data["document_creation_date"] = effective_time.get("value")

            # Extract author information
            author = root.find("hl7:author/hl7:assignedAuthor", namespaces)
            if author is not None:
                author_person = author.find("hl7:assignedPerson/hl7:name", namespaces)
                if author_person is not None:
                    family = author_person.find("hl7:family", namespaces)
                    if family is not None:
                        admin_data["author_hcp"]["family_name"] = family.text

                # Author organization
                org = author.find("hl7:representedOrganization/hl7:name", namespaces)
                if org is not None:
                    admin_data["author_hcp"]["organization"]["name"] = org.text

            # Extract custodian
            custodian = root.find(
                "hl7:custodian/hl7:assignedCustodian/hl7:representedCustodianOrganization/hl7:name",
                namespaces,
            )
            if custodian is not None:
                admin_data["custodian_organization"]["name"] = custodian.text

            logger.info("Extracted administrative data from CDA")
            return admin_data

        except Exception as e:
            logger.error(f"Error extracting administrative data: {e}")
            return admin_data

    def extract_extended_header_data(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract comprehensive extended header data for patient viewer
        Includes next of kin, dependants, legal authenticator, organization details, etc.
        """
        try:
            import sys
            import os

            # Add the project root to Python path for imports
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            if project_root not in sys.path:
                sys.path.append(project_root)

            from patient_data.services.cda_administrative_extractor import (
                CDAAdministrativeExtractor,
            )

            administrative_extractor = CDAAdministrativeExtractor()
            return administrative_extractor.extract_administrative_data(xml_content)
        except Exception as e:
            logger.error(f"Error extracting extended header data: {e}")
            return {}

    def get_patient_emergency_contacts(self, xml_content: str) -> Dict[str, Any]:
        """
        Get patient emergency contacts including next of kin and guardians
        """
        try:
            extended_data = self.extract_extended_header_data(xml_content)
            return extended_data.get("emergency_contacts", {})
        except Exception as e:
            logger.error(f"Error getting emergency contacts: {e}")
            return {"has_emergency_contacts": False, "total_count": 0}

    def get_patient_healthcare_team(self, xml_content: str) -> Dict[str, Any]:
        """
        Get patient healthcare team information including authors and preferred HCP
        """
        try:
            extended_data = self.extract_extended_header_data(xml_content)
            return extended_data.get("healthcare_team", {})
        except Exception as e:
            logger.error(f"Error getting healthcare team: {e}")
            return {"has_healthcare_team": False, "total_count": 0}

    def get_patient_contact_details(self, xml_content: str) -> Dict[str, Any]:
        """
        Get comprehensive patient contact details for enhanced patient card display
        """
        try:
            extended_data = self.extract_extended_header_data(xml_content)
            return extended_data.get("patient_contact", {})
        except Exception as e:
            logger.error(f"Error getting patient contact details: {e}")
            return {"has_contact_info": False}

    def get_document_creation_info(self, xml_content: str) -> Dict[str, Any]:
        """
        Get document creation and metadata information for display
        """
        try:
            extended_data = self.extract_extended_header_data(xml_content)
            return {
                "document_info": extended_data.get("document_info", {}),
                "metadata": extended_data.get("metadata", {}),
            }
        except Exception as e:
            logger.error(f"Error getting document creation info: {e}")
            return {"document_info": {}, "metadata": {}}

    def get_patient_dependants(self, xml_content: str) -> Dict[str, Any]:
        """
        Get patient dependants information
        """
        try:
            extended_data = self.extract_extended_header_data(xml_content)
            return extended_data.get("dependants", {})
        except Exception as e:
            logger.error(f"Error getting dependants: {e}")
            return {"has_dependants": False, "total_count": 0}

    def get_comprehensive_patient_summary(self, xml_content: str) -> Dict[str, Any]:
        """
        Get comprehensive patient summary including all extended header information
        Suitable for display in patient summary tabs or extended views
        """
        try:
            import xml.etree.ElementTree as ET

            # Parse XML
            root = ET.fromstring(xml_content)
            namespaces = {"hl7": "urn:hl7-org:v3", "n1": "urn:hl7-org:v3"}

            # Get basic patient identity using existing method
            basic_identity = self._simple_patient_id_extraction(root, namespaces)

            # Get extended header data
            extended_data = self.extract_extended_header_data(xml_content)

            # Convert AdministrativeData object to dictionary format
            if hasattr(extended_data, "__dict__"):
                # Convert to dictionary for consistent access
                extended_dict = {
                    "patient_contact": {
                        "has_contact_info": bool(
                            extended_data.patient_contact_info.addresses
                            or extended_data.patient_contact_info.telecoms
                        ),
                        "addresses": extended_data.patient_contact_info.addresses,
                        "telecoms": extended_data.patient_contact_info.telecoms,
                    },
                    "healthcare_team": {
                        "has_healthcare_team": bool(
                            extended_data.author_hcp.family_name
                            or extended_data.author_hcp.given_name
                        ),
                        "author": {
                            "name": f"{extended_data.author_hcp.given_name} {extended_data.author_hcp.family_name}".strip(),
                            "organization": (
                                extended_data.author_hcp.organization.name
                                if hasattr(
                                    extended_data.author_hcp.organization, "name"
                                )
                                else ""
                            ),
                            "role": extended_data.author_hcp.role,
                        },
                        "total_count": (
                            1
                            if (
                                extended_data.author_hcp.family_name
                                or extended_data.author_hcp.given_name
                            )
                            else 0
                        ),
                    },
                    "document_info": {
                        "creation_date": extended_data.document_creation_date,
                        "last_update": extended_data.document_last_update_date,
                        "version": extended_data.document_version_number,
                        "set_id": extended_data.document_set_id,
                        "custodian": {
                            "name": extended_data.custodian_organization.name,
                            "addresses": extended_data.custodian_organization.addresses,
                            "telecoms": extended_data.custodian_organization.telecoms,
                        },
                    },
                    "emergency_contacts": {
                        "has_emergency_contacts": bool(extended_data.other_contacts),
                        "contacts": extended_data.other_contacts,
                        "total_count": len(extended_data.other_contacts),
                    },
                    "dependants": {
                        "has_dependants": False,  # Not extracted in current implementation
                        "total_count": 0,
                    },
                    "extended_demographics": {},
                    "metadata": {
                        "custodian_organization": extended_data.custodian_organization.name,
                        "author_organization": (
                            extended_data.author_hcp.organization.name
                            if hasattr(extended_data.author_hcp.organization, "name")
                            else ""
                        ),
                    },
                }
            else:
                extended_dict = extended_data

            # Combine for comprehensive summary
            comprehensive_summary = {
                # Basic patient information
                "patient_identity": basic_identity,
                # Document information
                "document_info": extended_dict.get("document_info", {}),
                # Contact information
                "contact_details": extended_dict.get("patient_contact", {}),
                # Family and emergency contacts
                "emergency_contacts": extended_dict.get("emergency_contacts", {}),
                # Healthcare team
                "healthcare_team": extended_dict.get("healthcare_team", {}),
                # Dependants
                "dependants": extended_dict.get("dependants", {}),
                # Extended demographics
                "extended_demographics": extended_dict.get("extended_demographics", {}),
                # Metadata
                "metadata": extended_dict.get("metadata", {}),
                # Summary statistics
                "summary_stats": {
                    "has_emergency_contacts": extended_dict.get(
                        "emergency_contacts", {}
                    ).get("has_emergency_contacts", False),
                    "emergency_contacts_count": extended_dict.get(
                        "emergency_contacts", {}
                    ).get("total_count", 0),
                    "has_healthcare_team": extended_dict.get("healthcare_team", {}).get(
                        "has_healthcare_team", False
                    ),
                    "healthcare_team_count": extended_dict.get(
                        "healthcare_team", {}
                    ).get("total_count", 0),
                    "has_dependants": extended_dict.get("dependants", {}).get(
                        "has_dependants", False
                    ),
                    "dependants_count": extended_dict.get("dependants", {}).get(
                        "total_count", 0
                    ),
                    "has_contact_info": extended_dict.get("patient_contact", {}).get(
                        "has_contact_info", False
                    ),
                },
            }

            logger.info(
                f"Generated comprehensive patient summary with {comprehensive_summary['summary_stats']['emergency_contacts_count']} emergency contacts, {comprehensive_summary['summary_stats']['healthcare_team_count']} healthcare team members"
            )

            return comprehensive_summary

        except Exception as e:
            logger.error(f"Error generating comprehensive patient summary: {e}")
            return {}

    def _lookup_atc_code(self, atc_code: str) -> str:
        """Lookup ATC code to get active ingredient name using CTS terminology service"""
        if not atc_code:
            return ""
            
        try:
            # Use CTS terminology service to resolve ATC codes
            resolved_name = self.terminology_service.resolve_code(atc_code)
            if resolved_name:
                logger.info(f"CTS resolved ATC code {atc_code} to '{resolved_name}'")
                return resolved_name
            else:
                logger.warning(f"CTS could not resolve ATC code: {atc_code}")
                return ""
        except Exception as e:
            logger.error(f"Error resolving ATC code {atc_code}: {e}")
            return ""

    def _lookup_route_code(self, route_code: str) -> str:
        """Lookup route code to get administration route using CTS Master Value Catalogue"""
        if not route_code:
            return ""
            
        try:
            # Use CTS terminology service to resolve the code
            resolved_display = self.terminology_service.resolve_code(
                code=route_code,
                code_system="0.4.0.127.0.16.1.1.2.1"  # EDQM Standard Terms
            )
            
            if resolved_display:
                logger.debug(f"CTS resolved route code {route_code} to: {resolved_display}")
                return resolved_display
                
        except Exception as e:
            logger.warning(f"Error resolving route code {route_code} via CTS: {e}")
            
        # Fallback to hardcoded lookup for critical values
        route_lookup = {
            "20053000": "Oral use",
            "20066000": "Subcutaneous use", 
            "20045000": "Intravenous use",
            "20030000": "Intramuscular use",
            "20054000": "Sublingual use",
            "20057000": "Inhalation use",
        }
        
        fallback = route_lookup.get(route_code, route_code)
        if fallback != route_code:
            logger.debug(f"Used fallback lookup for route code {route_code}: {fallback}")
        else:
            logger.warning(f"No translation found for route code {route_code}")
            
        return fallback

    def _lookup_frequency_code(self, freq_code: str) -> str:
        """Lookup frequency/timing code using CTS Master Value Catalogue"""
        if not freq_code:
            return ""
            
        try:
            # Use CTS terminology service to resolve the code
            resolved_display = self.terminology_service.resolve_code(
                code=freq_code,
                code_system=None  # Multiple systems possible for frequency codes
            )
            
            if resolved_display:
                logger.debug(f"CTS resolved frequency code {freq_code} to: {resolved_display}")
                return resolved_display
                
        except Exception as e:
            logger.warning(f"Error resolving frequency code {freq_code} via CTS: {e}")
            
        # Fallback to hardcoded lookup for critical values
        frequency_lookup = {
            "ACM": "ACM",  # ante cibum (before meals)
            "PCM": "PCM",  # post cibum (after meals) 
            "BID": "twice daily",
            "TID": "three times daily",
            "QID": "four times daily",
            "QD": "once daily",
            "PRN": "as needed",
        }
        
        fallback = frequency_lookup.get(freq_code, freq_code)
        if fallback != freq_code:
            logger.debug(f"Used fallback lookup for frequency code {freq_code}: {fallback}")
        else:
            logger.warning(f"No translation found for frequency code {freq_code}")
            
        return fallback

    def _lookup_form_code(self, form_code: str) -> str:
        """Lookup pharmaceutical form code using CTS Master Value Catalogue"""
        if not form_code:
            return ""
            
        try:
            # Use CTS terminology service to resolve the code
            resolved_display = self.terminology_service.resolve_code(
                code=form_code,
                code_system="0.4.0.127.0.16.1.1.2.1"  # EDQM Standard Terms
            )
            
            if resolved_display:
                logger.debug(f"CTS resolved form code {form_code} to: {resolved_display}")
                return resolved_display
                
        except Exception as e:
            logger.warning(f"Error resolving form code {form_code} via CTS: {e}")
            
        # Fallback to hardcoded lookup for critical values
        form_lookup = {
            "10219000": "Tablet",
            "10225000": "Film-coated tablet",
            "10226000": "Prolonged-release tablet",
            "10307000": "Solution for injection",
            "10316000": "Solution for injection in pre-filled pen",
            "30009000": "Box",
            "30077000": "Nebuliser solution",
            "30078000": "Single-dose container",
        }
        
        fallback = form_lookup.get(form_code, form_code)
        if fallback != form_code:
            logger.debug(f"Used fallback lookup for form code {form_code}: {fallback}")
        else:
            logger.warning(f"No translation found for form code {form_code}")
            
        return fallback

    def _format_hl7_date(self, hl7_date: str) -> str:
        """Format HL7 date string (YYYYMMDD) to readable format"""
        if not hl7_date or len(hl7_date) < 8:
            return hl7_date
        
        try:
            # Extract year, month, day
            year = hl7_date[:4]
            month = hl7_date[4:6]
            day = hl7_date[6:8]
            
            return f"{year}-{month}-{day}"
        except (ValueError, IndexError):
            return hl7_date
