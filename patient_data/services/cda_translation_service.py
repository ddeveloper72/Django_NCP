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

    def __init__(self):
        self.translator = MedicalTerminologyTranslator()

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

        # Find all section divs
        section_divs = soup.find_all("div", class_="section")

        for section_div in section_divs:
            section_data = {}

            # Extract section title
            title_h3 = section_div.find("h3")
            if title_h3:
                section_data["title"] = title_h3.get_text(strip=True)
                section_data["section_id"] = title_h3.get("id", "")

            # Extract section content
            content_div = section_div.find("div", class_="section-content")
            if content_div:
                # Extract tables
                tables = content_div.find_all("table")
                section_data["tables"] = []

                for table in tables:
                    table_data = self._extract_table_data(table)
                    if table_data:
                        section_data["tables"].append(table_data)

                # Extract other content
                section_data["content"] = content_div.get_text(strip=True)

            if section_data:
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

        # Translate sections
        translated_sections = []
        for section in cda_data["sections"]:
            translated_section = {
                "section_id": section.get("section_id", ""),
                "title_original": section.get("title", ""),
                "title_translated": self.translator.translate_term(
                    section.get("title", ""), source_lang
                ),
                "content_original": section.get("content", ""),
                "content_translated": self.translator.translate_text_block(
                    section.get("content", ""), source_lang
                ),
                "tables": [],
            }

            # Translate tables
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
