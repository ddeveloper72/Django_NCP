"""
CDA Translation Service for EU Cross-Border Patient Documents
Provides medical terminology translation for Clinical Document Architecture files
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass
from pathlib import Path


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


class MedicalTerminologyTranslator:
    """Medical terminology translator for common EU languages to English"""

    def __init__(self):
        self.terminology_db = {
            # French medical terms
            "fr": {
                # Section headers
                "Historique de la prise médicamenteuse": "Medication History",
                "Allergies, effets indésirables, alertes": "Allergies, Adverse Reactions, Alerts",
                "Vaccinations": "Vaccinations",
                "Liste des problèmes": "Problem List",
                "Antécédents chirurgicaux": "Surgical History",
                "Liste des dispositifs médicaux": "Medical Devices List",
                # Patient information
                "Patient": "Patient",
                "Date de naissance": "Date of Birth",
                "Sexe": "Gender",
                "ID patient": "Patient ID",
                "Féminin": "Female",
                "Masculin": "Male",
                # Document metadata
                "Evènement documenté": "Documented Event",
                "Prestation de soins": "Care Provision",
                "Auteur": "Author",
                "Organisation": "Organization",
                "Créé le": "Created on",
                # Medication terms
                "Nom commercial": "Brand Name",
                "Principe actif et dosage": "Active Ingredient and Dosage",
                "Forme pharmaceutique": "Pharmaceutical Form",
                "Route": "Route",
                "Posologie": "Dosage",
                "Date de début": "Start Date",
                "Date de fin": "End Date",
                "Notes": "Notes",
                "orale": "oral",
                "cp": "tablet",
                "sol buv": "oral solution",
                "par Jour": "per Day",
                "par Heure": "per Hour",
                # Common medical terms
                "mg": "mg",
                "ml": "ml",
                "traitement": "treatment",
                "médicament": "medication",
                "allergie": "allergy",
                "vaccination": "vaccination",
                "problème": "problem",
                "chirurgie": "surgery",
                "dispositif": "device",
            },
            # German medical terms
            "de": {
                "Medikationsgeschichte": "Medication History",
                "Allergien": "Allergies",
                "Impfungen": "Vaccinations",
                "Problemliste": "Problem List",
                "Patient": "Patient",
                "Geburtsdatum": "Date of Birth",
                "Geschlecht": "Gender",
                "weiblich": "Female",
                "männlich": "Male",
                "oral": "oral",
                "Tablette": "tablet",
            },
            # Spanish medical terms
            "es": {
                "Historial de medicación": "Medication History",
                "Alergias": "Allergies",
                "Vacunas": "Vaccinations",
                "Lista de problemas": "Problem List",
                "Paciente": "Patient",
                "Fecha de nacimiento": "Date of Birth",
                "Sexo": "Gender",
                "Femenino": "Female",
                "Masculino": "Male",
                "oral": "oral",
                "comprimido": "tablet",
            },
            # Italian medical terms
            "it": {
                "Storia farmacologica": "Medication History",
                "Allergie": "Allergies",
                "Vaccinazioni": "Vaccinations",
                "Elenco problemi": "Problem List",
                "Paziente": "Patient",
                "Data di nascita": "Date of Birth",
                "Sesso": "Gender",
                "Femmina": "Female",
                "Maschio": "Male",
                "orale": "oral",
                "compressa": "tablet",
            },
        }

    def detect_language(self, text: str) -> str:
        """Detect the language of the medical document"""
        # Simple language detection based on common medical terms
        text_lower = text.lower()

        french_indicators = [
            "médical",
            "patient",
            "médicament",
            "allergie",
            "de naissance",
        ]
        german_indicators = ["patient", "medikament", "allergie", "geburtsdatum"]
        spanish_indicators = [
            "paciente",
            "medicamento",
            "alergia",
            "fecha de nacimiento",
        ]
        italian_indicators = ["paziente", "farmaco", "allergia", "data di nascita"]

        scores = {
            "fr": sum(1 for term in french_indicators if term in text_lower),
            "de": sum(1 for term in german_indicators if term in text_lower),
            "es": sum(1 for term in spanish_indicators if term in text_lower),
            "it": sum(1 for term in italian_indicators if term in text_lower),
        }

        return max(scores, key=scores.get) if max(scores.values()) > 0 else "fr"

    def translate_term(self, term: str, source_lang: str) -> str:
        """Translate a medical term from source language to English"""
        if source_lang not in self.terminology_db:
            return term

        # Direct translation lookup
        if term in self.terminology_db[source_lang]:
            return self.terminology_db[source_lang][term]

        # Case-insensitive lookup
        term_lower = term.lower()
        for original, translation in self.terminology_db[source_lang].items():
            if original.lower() == term_lower:
                return translation

        # Partial match for compound terms
        for original, translation in self.terminology_db[source_lang].items():
            if original.lower() in term_lower or term_lower in original.lower():
                return f"{translation} ({term})"

        return term

    def translate_text_block(self, text: str, source_lang: str) -> str:
        """Translate a block of medical text"""
        if not text or source_lang not in self.terminology_db:
            return text

        translated_text = text

        # Replace medical terms while preserving structure
        for original, translation in self.terminology_db[source_lang].items():
            # Use word boundaries to avoid partial replacements
            pattern = r"\b" + re.escape(original) + r"\b"
            translated_text = re.sub(
                pattern, translation, translated_text, flags=re.IGNORECASE
            )

        return translated_text


class CDATranslationService:
    """Service for translating CDA documents and creating bilingual displays"""

    def __init__(self, target_language: str = "en"):
        """
        Initialize CDA Translation Service with terminology support

        Args:
            target_language: Target language for terminology translations (default: English)
        """
        self.translator = MedicalTerminologyTranslator()
        from .ps_table_renderer import PSTableRenderer

        self.table_renderer = PSTableRenderer(target_language=target_language)

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

        # Detect document language
        full_text = soup.get_text()
        language = self.translator.detect_language(full_text)

        return {
            "patient_info": patient_info,
            "document_info": document_info,
            "sections": sections,
            "language": language,
            "original_html": html_content,
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
            if title_element and not section_data.get("title"):
                section_data["title"] = title_element.get_text(strip=True)
                section_data["section_id"] = f"section-{len(sections) + 1}"

                # Extract code from code element
                code_element = section_element.find("code")
                if code_element and code_element.get("code"):
                    section_data["section_code"] = code_element.get("code")
                else:
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
                section_data["content_text"] = content_div.get_text(strip=True)  # Text only for display
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

        # First, render sections with PSTableRenderer
        rendered_sections = self.table_renderer.render_section_tables(
            cda_data["sections"]
        )

        for section, rendered_section in zip(cda_data["sections"], rendered_sections):
            translated_section = {
                "section_id": section.get("section_id", ""),
                "section_code": section.get("section_code", ""),
                "title_original": section.get("title", ""),
                "title_translated": self.translator.translate_term(
                    section.get("title", ""), source_lang
                ),
                "content_original": section.get("content_text", ""),  # Use text version for translation
                "content_translated": self.translator.translate_text_block(
                    section.get("content_text", ""), source_lang
                ),
                # Preserve structure for PSTableRenderer
                "content": section.get("content", ""),  # HTML structure for table parsing
                "tables": [],
                "ps_table_html": rendered_section.get(
                    "table_html", ""
                ),  # PS Guidelines table
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
