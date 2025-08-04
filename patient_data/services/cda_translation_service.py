"""
CDA Translation Service for EU Cross-Border Patient Documents
Provides medical terminology translation using Central Terminology Server (CTS)
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from pathlib import Path
from translation_services.terminology_translator import TerminologyTranslatorCompat


@dataclass
class TranslatedSection:
    """Represents a CDA section with original and translated content"""

    section_id: str
    title_original: str
    title_translated: str
    content_original: str
    content_translated: str
    language_code: str
    subsections: List["TranslatedSection"] = None


class CDATranslationService:
    """Service for translating CDA documents using Central Terminology Server (CTS)"""

    def __init__(self, target_language: str = "en"):
        """
        Initialize CDA Translation Service with CTS-based terminology support

        Args:
            target_language: Target language for terminology translations (default: English)
        """
        # Use proper CTS-based terminology translator instead of hardcoded dictionaries
        self.translator = TerminologyTranslatorCompat(target_language=target_language)
        from .ps_table_renderer import PSTableRenderer

        self.table_renderer = PSTableRenderer(target_language=target_language)

    def _translate_text_compatibility(
        self, text: str, source_lang: str = "auto"
    ) -> str:
        """
        Compatibility method to handle individual text translation
        Note: This is a bridge method - full document translation is preferred for CTS accuracy
        """
        if not text or not isinstance(text, str):
            return text

        # For individual text pieces, return as-is since proper CTS translation
        # works best with full document context including codes and structure
        return text

    def parse_cda_html(self, html_content: str) -> Dict:
        """Parse CDA HTML document and extract structured data"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract patient information
        patient_info = self._extract_patient_info(soup)

        # Extract document metadata
        document_info = self._extract_document_info(soup)

        # Extract medical sections
        sections = self._extract_sections(soup)

        # Use CTS-based translation service for proper terminology handling
        document_text = soup.get_text()
        translation_result = self.translator.translate_clinical_document(
            document_content=html_content,
            source_language="auto",  # Let CTS determine source language
        )

        return {
            "patient_info": patient_info,
            "document_info": document_info,
            "sections": sections,
            "language": translation_result.get("source_language", "unknown"),
            "original_html": html_content,
            "translation_stats": {
                "translations_applied": translation_result.get(
                    "translations_applied", 0
                ),
                "terminology_map": translation_result.get("terminology_map", {}),
                "untranslated_terms": translation_result.get("untranslated_terms", []),
            },
        }

    def _extract_patient_info(self, soup) -> Dict:
        """Extract patient information from CDA HTML"""
        patient_info = {}

        # Look for patient table
        header_table = soup.find("table", class_="header_table")
        if header_table:
            rows = header_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    patient_info[label] = value

        return patient_info

    def _extract_document_info(self, soup) -> Dict:
        """Extract document metadata"""
        doc_info = {}

        # Extract title
        title = soup.find("title")
        if title:
            doc_info["title"] = title.get_text(strip=True)

        # Extract creation date from title or header
        h1_title = soup.find("h1", class_="title")
        if h1_title:
            doc_info["document_title"] = h1_title.get_text(strip=True)

        return doc_info

    def _extract_sections(self, soup) -> List[Dict]:
        """Extract medical sections from CDA HTML"""
        sections = []

        # Try to find sections in both formats:
        # 1. HTML div format: <div class="section">
        # 2. CDA XML format: <section>
        section_elements = soup.find_all("div", class_="section")
        if not section_elements:
            section_elements = soup.find_all("section")

        for section_element in section_elements:
            section_data = {}

            # Extract section title and ID/code for HTML div format
            title_h3 = section_element.find("h3")
            if title_h3:
                section_data["title"] = title_h3.get_text(strip=True)
                section_data["section_id"] = title_h3.get("id", "")

                # Try to extract LOINC code from various attributes or text
                section_code = ""
                if "data-code" in title_h3.attrs:
                    section_code = title_h3["data-code"]
                elif "id" in title_h3.attrs and "-" in title_h3["id"]:
                    # Check if ID contains LOINC-like code
                    potential_code = title_h3["id"].split("-")[0]
                    if potential_code.replace(".", "").isdigit():
                        section_code = potential_code

                # Look for code in text content (format: "Title (LOINC-CODE)")
                title_text = title_h3.get_text(strip=True)
                import re

                code_match = re.search(r"\(([0-9\-]+)\)", title_text)
                if code_match:
                    section_code = code_match.group(1)

                section_data["section_code"] = section_code

            # Extract section title for CDA XML format
            title_element = section_element.find("title")
            if title_element:
                if not section_data.get("title"):
                    section_data["title"] = title_element.get_text(strip=True)
                    section_data["section_id"] = f"section-{len(sections) + 1}"

                # Always extract code from code element for CDA XML format
                code_element = section_element.find("code")
                if code_element and code_element.get("code"):
                    section_data["section_code"] = code_element.get("code")
                elif not section_data.get("section_code"):
                    section_data["section_code"] = ""

            # Extract section content
            content_div = section_element.find("div", class_="section-content")
            if not content_div:
                # For CDA XML format, look for text element
                content_div = section_element.find("text")

            if content_div:
                # Extract tables
                tables = content_div.find_all("table")
                section_data["tables"] = []

                for table in tables:
                    table_data = self._extract_table_data(table)
                    if table_data:
                        section_data["tables"].append(table_data)

                # Extract content - preserve HTML for table rendering
                section_data["content"] = str(content_div)  # Keep HTML structure
                section_data["content_text"] = content_div.get_text(
                    strip=True
                )  # Text only for display
            else:
                # Fallback: extract all text content from section
                section_data["content"] = section_element.get_text(strip=True)
                section_data["content_text"] = section_element.get_text(strip=True)
                section_data["tables"] = []

            if section_data and section_data.get("title"):
                sections.append(section_data)

        return sections

    def _extract_table_data(self, table) -> Dict:
        """Extract structured data from HTML table"""
        table_data = {"headers": [], "rows": []}

        # Extract headers
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = header_row.find_all("th")
                table_data["headers"] = [th.get_text(strip=True) for th in headers]

        # Extract data rows
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                row_data = [cell.get_text(strip=True) for cell in cells]
                if any(row_data):  # Only add non-empty rows
                    table_data["rows"].append(row_data)

        return table_data if table_data["headers"] or table_data["rows"] else None

    def _create_translated_table_html(
        self, rendered_section: Dict, source_lang: str
    ) -> str:
        """Create translated version of table HTML with English headers and content"""
        print(
            f"DEBUG: _create_translated_table_html called with section: {rendered_section.get('title', 'Unknown')}"
        )

        original_table_html = rendered_section.get("table_html", "")
        if not original_table_html:
            print("DEBUG: No table_html found in rendered_section")
            return ""

        print(f"DEBUG: Processing table HTML of length: {len(original_table_html)}")

        # Parse the original table HTML
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(original_table_html, "html.parser")

        # Translate table headers
        header_cells = soup.find_all("th", class_="ps-th")
        for th in header_cells:
            original_text = th.get_text(strip=True)
            translated_text = self.translator.translate_term(original_text, source_lang)
            th.string = translated_text

        # Translate table cell content and add code system badges
        data_cells = soup.find_all("td", class_="ps-td")
        table_rows = soup.find_all("tr", class_="ps-tr")

        print(f"DEBUG: Found {len(table_rows)} rows with class 'ps-tr'")
        print(f"DEBUG: Found {len(data_cells)} cells with class 'ps-td'")

        # If no structured rows found, try without class
        if not table_rows:
            table_rows = soup.find_all("tr")
            print(
                f"DEBUG: Fallback - Found {len(table_rows)} rows without class restriction"
            )

        if not data_cells:
            all_cells = soup.find_all("td")
            print(
                f"DEBUG: Fallback - Found {len(all_cells)} cells without class restriction"
            )

        # Determine section type from rendered_section for badge placement
        section_title = rendered_section.get("title", {})
        if isinstance(section_title, dict):
            title_text = section_title.get(
                "original", section_title.get("translated", "")
            ).lower()
        else:
            title_text = str(section_title).lower()

        # Determine section type for badge enhancement
        section_type = "generic"
        if any(
            word in title_text for word in ["medication", "médicament", "medicamento"]
        ):
            section_type = "medications"
        elif any(word in title_text for word in ["allerg", "adverse"]):
            section_type = "allergies"
        elif any(word in title_text for word in ["problem", "diagnosis", "diagnostic"]):
            section_type = "problems"

        print(
            f"DEBUG: Table section type detected: '{section_type}' from title: '{title_text}'"
        )

        # Import badge enhancement from PSTableRenderer
        from .ps_table_renderer import PSTableRenderer

        ps_renderer = PSTableRenderer()

        # Process each row
        for row_index, row in enumerate(table_rows):
            cells_in_row = row.find_all("td", class_="ps-td")
            # If no structured cells found, try without class
            if not cells_in_row:
                cells_in_row = row.find_all("td")

            for col_index, td in enumerate(cells_in_row):
                # Check if cell already has enhanced table structure from PS renderer
                enhanced_div = td.find("div", class_="table-cell-enhanced")
                existing_badges = td.find_all("span", class_="code-system-badge")
                has_enhanced_structure = enhanced_div is not None
                has_existing_badges = len(existing_badges) > 0

                print(
                    f"DEBUG: Processing cell [{row_index},{col_index}], enhanced structure: {has_enhanced_structure}, existing badges: {has_existing_badges}"
                )

                if has_enhanced_structure or has_existing_badges:
                    # Cell already has enhanced structure from PS renderer - skip adding new badges
                    # Just translate text content within the existing structure
                    print(
                        f"DEBUG: Skipping badge addition for cell [{row_index},{col_index}] - already enhanced"
                    )

                    if has_enhanced_structure:
                        # Find and translate the primary content within the enhanced structure
                        primary_content_div = enhanced_div.find(
                            "div", class_="primary-content"
                        )
                        if primary_content_div and primary_content_div.get_text(
                            strip=True
                        ):
                            original_text = primary_content_div.get_text(strip=True)
                            translated_text = self._translate_text_compatibility(
                                original_text, source_lang
                            )
                            primary_content_div.string = translated_text
                            print(
                                f"DEBUG: Translated primary content: '{original_text}' -> '{translated_text}'"
                            )
                    else:
                        # Handle legacy badge structure
                        text_parts = []
                        for content in td.contents:
                            if (
                                hasattr(content, "name")
                                and content.name == "span"
                                and "code-system-badge" in content.get("class", [])
                            ):
                                # Keep the badge as-is
                                continue
                            else:
                                # Translate the text part
                                text_content = str(content).strip()
                                if text_content:
                                    text_parts.append(text_content)

                        if text_parts:
                            original_text = "".join(text_parts)
                            translated_text = self.translator.translate_text_block(
                                original_text, source_lang
                            )
                            # Replace just the text parts, keep badges
                            new_contents = []
                            for content in td.contents:
                                if (
                                    hasattr(content, "name")
                                    and content.name == "span"
                                    and "code-system-badge" in content.get("class", [])
                                ):
                                    new_contents.append(content)
                                else:
                                    new_contents.append(translated_text)
                                    break  # Only replace first text part

                            td.clear()
                            for content in new_contents:
                                if hasattr(content, "name"):
                                    td.append(content)
                                else:
                                    td.append(content)
                else:
                    # No existing badges - process normally
                    original_text = td.get_text(strip=True)
                    print(f"DEBUG: Processing cell without badges: '{original_text}'")

                    if original_text:  # Only translate non-empty cells
                        translated_text = self.translator.translate_text_block(
                            original_text, source_lang
                        )

                        print(f"DEBUG: Using PS renderer for badge enhancement")
                        # Let PS table renderer handle badge creation to avoid duplication
                        code_system, code = ps_renderer._detect_code_system(
                            translated_text
                        )
                        if code_system:
                            # Use PS renderer's badge method for consistent structure
                            enhanced_text = ps_renderer._add_code_system_badge(
                                translated_text, code_system, code
                            )
                            print(
                                f"DEBUG: Enhanced '{translated_text}' with PS renderer structure"
                            )
                        else:
                            enhanced_text = translated_text
                            print(
                                f"DEBUG: No code system found for '{translated_text}'"
                            )

                        # Handle HTML content properly
                        if '<div class="table-cell-enhanced">' in enhanced_text:
                            # Enhanced text with PS renderer structure - parse and insert
                            td.clear()
                            # Parse the enhanced content and set it as the cell's innerHTML
                            from bs4 import NavigableString

                            fragment_soup = BeautifulSoup(enhanced_text, "html.parser")

                            # Add content directly without creating extra wrappers
                            for item in fragment_soup.contents:
                                if isinstance(item, NavigableString):
                                    td.append(item)
                                else:
                                    # Clone the tag properly
                                    td.append(item)
                        else:
                            # Simple text without badges
                            td.string = enhanced_text

        # Convert back to string with HTML formatting preserved
        html_output = str(soup)

        # Fix any remaining HTML escaping issues
        html_output = (
            html_output.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        )

        print(f"DEBUG: Final HTML output (first 200 chars): {html_output[:200]}...")
        print(
            f"DEBUG: Contains enhanced table cells: {'<div class=\"table-cell-enhanced\">' in html_output}"
        )

        return html_output

    def create_bilingual_document(self, cda_data: Dict) -> Dict:
        """Create bilingual version with original + English translation"""
        source_lang = cda_data["language"]

        # Translate patient information
        translated_patient_info = {}
        for key, value in cda_data["patient_info"].items():
            translated_key = self.translator.translate_term(key, source_lang)
            translated_value = self.translator.translate_text_block(value, source_lang)
            translated_patient_info[key] = {
                "original": value,
                "translated": translated_value,
                "key_original": key,
                "key_translated": translated_key,
            }

        # Translate sections and render as PS Display Guidelines tables
        translated_sections = []

        # First, render sections with PSTableRenderer to get the base table structure
        rendered_sections = self.table_renderer.render_section_tables(
            cda_data["sections"]
        )

        for section, rendered_section in zip(cda_data["sections"], rendered_sections):
            # Create translated version of the table
            translated_table_html = self._create_translated_table_html(
                rendered_section, source_lang
            )

            translated_section = {
                "section_id": section.get("section_id", ""),
                "section_code": section.get("section_code", ""),
                "title_original": section.get("title", ""),
                "title_translated": self.translator.translate_term(
                    section.get("title", ""), source_lang
                ),
                "content_original": section.get(
                    "content_text", ""
                ),  # Use text version for translation
                "content_translated": self.translator.translate_text_block(
                    section.get("content_text", ""), source_lang
                ),
                # Preserve structure for PSTableRenderer
                "content": section.get(
                    "content", ""
                ),  # HTML structure for table parsing
                "tables": [],
                "ps_table_html": translated_table_html,  # Translated PS Guidelines table
                "ps_table_html_original": rendered_section.get(
                    "table_html", ""
                ),  # Original PS Guidelines table
            }

            # Translate original tables
            for table in section.get("tables", []):
                translated_table = {
                    "headers_original": table["headers"],
                    "headers_translated": [
                        self.translator.translate_term(h, source_lang)
                        for h in table["headers"]
                    ],
                    "rows": table["rows"],  # Keep original data rows for now
                }
                translated_section["tables"].append(translated_table)

            translated_sections.append(translated_section)

        return {
            "source_language": source_lang,
            "patient_info": translated_patient_info,
            "sections": translated_sections,
            "document_info": cda_data["document_info"],
        }


def process_cda_file(file_path: str) -> Dict:
    """Process a CDA HTML file and return bilingual translation"""
    service = CDATranslationService()

    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Parse the CDA document
    cda_data = service.parse_cda_html(html_content)

    # Create bilingual version
    bilingual_data = service.create_bilingual_document(cda_data)

    return bilingual_data


# Example usage
if __name__ == "__main__":
    # Test with Luxembourg CDA file
    lu_file = "/test_data/eu_member_states/LU/DefaultXsltOutput.htm"
    result = process_cda_file(lu_file)
    print(f"Detected language: {result['source_language']}")
    print(f"Sections found: {len(result['sections'])}")
