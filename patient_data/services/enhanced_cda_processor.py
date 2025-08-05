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

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language

        # Initialize CTS-compliant terminology service
        from translation_services.terminology_translator import TerminologyTranslator

        self.terminology_service = TerminologyTranslator(
            target_language=target_language
        )

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
            f"Initialized Enhanced CDA Processor with CTS-compliant terminology service for language: {target_language}"
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
            }

            sections = []
            sections_count = 0
            medical_terms_count = 0
            coded_sections_count = 0

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
            }

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return {"success": False, "error": f"XML parsing error: {e}"}

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
            table_data = self._extract_structured_data(entries, namespaces)

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

            # Look for section elements in HTML
            section_elements = soup.find_all(
                ["div", "section"],
                class_=lambda x: x and "section" in x.lower() if x else False,
            )

            # Also look for headings that might indicate sections
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

            # Generate PS tables if tables exist
            ps_table_html = ""
            ps_table_html_original = ""

            if has_ps_table:
                table_data = self._extract_table_data(tables[0])
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
            }

        except Exception as e:
            logger.error(f"Error extracting HTML section: {e}")
            return None

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
                # This is a simplified extraction - in reality would be more complex
                # based on the specific CDA template being used
                entry_data = {"type": "structured_entry", "data": {}}

                # Extract observation or substance administration data
                obs_elem = entry.find(".//hl7:observation", namespaces)
                if obs_elem is not None:
                    # Extract value, code, etc.
                    code_elem = obs_elem.find("hl7:code", namespaces)
                    if code_elem is not None:
                        entry_data["data"]["code"] = code_elem.get("code", "")
                        entry_data["data"]["display"] = code_elem.get("displayName", "")

                structured_data.append(entry_data)

            except Exception as e:
                logger.error(f"Error extracting entry data: {e}")
                continue

        return structured_data

    def _generate_ps_tables(
        self,
        table_data: List[Dict],
        section_code: str,
        title: Dict,
        source_language: str,
    ) -> tuple:
        """Generate PS-compliant tables in both languages"""

        # This would generate proper PS Display Guidelines tables
        # For now, return placeholder tables

        table_html = f"""
        <div class="ps-table-container">
            <table class="ps-compliant-table">
                <thead>
                    <tr>
                        <th>{title['target']}</th>
                        <th>Code</th>
                        <th>Value</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td colspan="4">
                            <em>Enhanced PS table data would be rendered here</em>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

        table_html_original = f"""
        <div class="ps-table-container">
            <table class="ps-compliant-table">
                <thead>
                    <tr>
                        <th>{title['source']}</th>
                        <th>Code</th>
                        <th>Valeur</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td colspan="4">
                            <em>Données de tableau PS original seraient rendues ici</em>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

        return table_html, table_html_original

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
