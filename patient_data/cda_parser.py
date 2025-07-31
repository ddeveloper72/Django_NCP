"""
CDA Document Parser for EU Patient Summaries
Parses L1 and L3 CDA documents from test_data/eu_member_states
Extracts patient identifiers, demographics, and clinical content
"""

import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientIdentifier:
    """Patient identifier from CDA document"""

    extension: str  # Patient ID
    root: str  # OID of the assigning authority
    assigning_authority: Optional[str] = None


@dataclass
class PatientDemographics:
    """Patient demographic information from CDA"""

    given_name: str
    family_name: str
    birth_date: str
    gender: str
    address: Dict[str, str]
    telecom: List[str]


@dataclass
class ClinicalSection:
    """Clinical section from CDA document"""

    section_code: str
    section_title: str
    template_id: str
    content_text: str
    entries: List[Dict]


@dataclass
class CDADocument:
    """Parsed CDA document structure"""

    document_id: str
    template_id: str
    document_type: str  # L1, L3, PIVOT, FRIENDLY
    country_code: str
    language_code: str
    effective_time: str
    patient_identifiers: List[PatientIdentifier]
    patient_demographics: PatientDemographics
    clinical_sections: List[ClinicalSection]
    raw_filename: str
    file_path: str


class CDAParser:
    """Parser for EU CDA Patient Summary documents"""

    # XML namespaces used in CDA documents
    NAMESPACES = {
        "hl7": "urn:hl7-org:v3",
        "pharm": "urn:hl7-org:pharm",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    def __init__(self, test_data_path: str = "test_data/eu_member_states"):
        self.test_data_path = Path(test_data_path)

    def parse_document(self, file_path: Path) -> Optional[CDADocument]:
        """Parse a single CDA document"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract basic document metadata
            document_id = self._get_document_id(root)
            template_id = self._get_template_id(root)
            document_type = self._determine_document_type(file_path.name)
            country_code = self._get_country_code(root)
            language_code = self._get_language_code(root)
            effective_time = self._get_effective_time(root)

            # Extract patient information
            patient_identifiers = self._extract_patient_identifiers(root)
            patient_demographics = self._extract_patient_demographics(root)

            # Extract clinical sections
            clinical_sections = self._extract_clinical_sections(root)

            return CDADocument(
                document_id=document_id,
                template_id=template_id,
                document_type=document_type,
                country_code=country_code,
                language_code=language_code,
                effective_time=effective_time,
                patient_identifiers=patient_identifiers,
                patient_demographics=patient_demographics,
                clinical_sections=clinical_sections,
                raw_filename=file_path.name,
                file_path=str(file_path),
            )

        except Exception as e:
            logger.error(f"Error parsing CDA document {file_path}: {e}")
            return None

    def _get_document_id(self, root) -> str:
        """Extract document ID"""
        id_elem = root.find(".//hl7:id", self.NAMESPACES)
        if id_elem is not None:
            extension = id_elem.get("extension", "")
            root_oid = id_elem.get("root", "")
            return f"{extension}@{root_oid}" if extension else root_oid
        return "unknown"

    def _get_template_id(self, root) -> str:
        """Extract template ID"""
        template_elem = root.find(".//hl7:templateId", self.NAMESPACES)
        return template_elem.get("root", "") if template_elem is not None else ""

    def _determine_document_type(self, filename: str) -> str:
        """Determine document type from filename"""
        if "PIVOT-CDA-(L1)" in filename:
            return "L1-PIVOT"
        elif "PIVOT-CDA-(L3)" in filename:
            return "L3-PIVOT"
        elif "FRIENDLY-CDA-(L3)" in filename:
            return "L3-FRIENDLY"
        elif "L1" in filename:
            return "L1"
        elif "L3" in filename:
            return "L3"
        return "Unknown"

    def _get_country_code(self, root) -> str:
        """Extract country code"""
        realm_elem = root.find(".//hl7:realmCode", self.NAMESPACES)
        return realm_elem.get("code", "") if realm_elem is not None else ""

    def _get_language_code(self, root) -> str:
        """Extract language code"""
        lang_elem = root.find(".//hl7:languageCode", self.NAMESPACES)
        return lang_elem.get("code", "") if lang_elem is not None else ""

    def _get_effective_time(self, root) -> str:
        """Extract effective time"""
        time_elem = root.find(".//hl7:effectiveTime", self.NAMESPACES)
        return time_elem.get("value", "") if time_elem is not None else ""

    def _extract_patient_identifiers(self, root) -> List[PatientIdentifier]:
        """Extract all patient identifiers"""
        identifiers = []

        # Look for patient identifiers in recordTarget/patientRole/id
        patient_ids = root.findall(
            ".//hl7:recordTarget//hl7:patientRole/hl7:id", self.NAMESPACES
        )

        for id_elem in patient_ids:
            extension = id_elem.get("extension", "")
            root_oid = id_elem.get("root", "")
            assigning_authority = id_elem.get("assigningAuthorityName", "")

            if extension and root_oid:
                identifiers.append(
                    PatientIdentifier(
                        extension=extension,
                        root=root_oid,
                        assigning_authority=assigning_authority,
                    )
                )

        return identifiers

    def _extract_patient_demographics(self, root) -> Optional[PatientDemographics]:
        """Extract patient demographic information"""
        try:
            patient_elem = root.find(
                ".//hl7:recordTarget//hl7:patient", self.NAMESPACES
            )
            if patient_elem is None:
                return None

            # Extract name
            name_elem = patient_elem.find(".//hl7:n", self.NAMESPACES)
            given_name = ""
            family_name = ""

            if name_elem is not None:
                given_elem = name_elem.find(".//hl7:given", self.NAMESPACES)
                family_elem = name_elem.find(".//hl7:family", self.NAMESPACES)
                given_name = (
                    given_elem.text
                    if given_elem is not None and given_elem.text
                    else ""
                )
                family_name = (
                    family_elem.text
                    if family_elem is not None and family_elem.text
                    else ""
                )

            # Extract birth date
            birth_elem = patient_elem.find(".//hl7:birthTime", self.NAMESPACES)
            birth_date = birth_elem.get("value", "") if birth_elem is not None else ""

            # Extract gender
            gender_elem = patient_elem.find(
                ".//hl7:administrativeGenderCode", self.NAMESPACES
            )
            gender = gender_elem.get("code", "") if gender_elem is not None else ""

            # Extract address
            address = {}
            addr_elem = root.find(".//hl7:recordTarget//hl7:addr", self.NAMESPACES)
            if addr_elem is not None:
                for child in addr_elem:
                    tag = child.tag.replace("{urn:hl7-org:v3}", "")
                    address[tag] = child.text or ""

            # Extract telecom
            telecom = []
            telecom_elems = root.findall(
                ".//hl7:recordTarget//hl7:telecom", self.NAMESPACES
            )
            for telecom_elem in telecom_elems:
                value = telecom_elem.get("value", "")
                if value:
                    telecom.append(value)

            return PatientDemographics(
                given_name=given_name,
                family_name=family_name,
                birth_date=birth_date,
                gender=gender,
                address=address,
                telecom=telecom,
            )

        except Exception as e:
            logger.error(f"Error extracting patient demographics: {e}")
            return None

    def _extract_clinical_sections(self, root) -> List[ClinicalSection]:
        """Extract clinical sections from structured body"""
        sections = []

        try:
            section_elems = root.findall(
                ".//hl7:component/hl7:section", self.NAMESPACES
            )

            for section in section_elems:
                # Extract section code and title
                code_elem = section.find(".//hl7:code", self.NAMESPACES)
                title_elem = section.find(".//hl7:title", self.NAMESPACES)
                template_elem = section.find(".//hl7:templateId", self.NAMESPACES)
                text_elem = section.find(".//hl7:text", self.NAMESPACES)

                section_code = (
                    code_elem.get("code", "") if code_elem is not None else ""
                )
                section_title = (
                    title_elem.text
                    if title_elem is not None and title_elem.text
                    else ""
                )
                template_id = (
                    template_elem.get("root", "") if template_elem is not None else ""
                )

                # Extract text content (simplified)
                content_text = ""
                if text_elem is not None:
                    # Convert XML to text (simplified approach)
                    content_text = ET.tostring(
                        text_elem, encoding="unicode", method="text"
                    )

                # Extract entries (simplified)
                entries = []
                entry_elems = section.findall(".//hl7:entry", self.NAMESPACES)
                for entry in entry_elems[:5]:  # Limit to first 5 entries
                    entry_data = {
                        "type": entry.get("typeCode", ""),
                        "class": (
                            entry.find(".//*").get("classCode", "")
                            if len(entry) > 0
                            else ""
                        ),
                    }
                    entries.append(entry_data)

                sections.append(
                    ClinicalSection(
                        section_code=section_code,
                        section_title=section_title,
                        template_id=template_id,
                        content_text=content_text,
                        entries=entries,
                    )
                )

        except Exception as e:
            logger.error(f"Error extracting clinical sections: {e}")

        return sections

    def scan_test_data(self) -> Dict[str, List[CDADocument]]:
        """Scan all test data and parse CDA documents"""
        documents_by_country = {}

        if not self.test_data_path.exists():
            logger.warning(f"Test data path not found: {self.test_data_path}")
            return documents_by_country

        # Scan each country directory
        for country_dir in self.test_data_path.iterdir():
            if country_dir.is_dir():
                country_code = country_dir.name
                documents_by_country[country_code] = []

                # Parse all XML files in the country directory
                for xml_file in country_dir.glob("*.xml"):
                    document = self.parse_document(xml_file)
                    if document:
                        documents_by_country[country_code].append(document)
                        logger.info(
                            f"Parsed {document.document_type} document for {country_code}: {document.raw_filename}"
                        )

        return documents_by_country

    def find_patient_summaries(self, patient_id: str, oid: str) -> List[CDADocument]:
        """Find patient summaries matching patient ID and OID"""
        matching_documents = []
        documents_by_country = self.scan_test_data()

        for country_code, documents in documents_by_country.items():
            for document in documents:
                # Check if any patient identifier matches
                for identifier in document.patient_identifiers:
                    if identifier.extension == patient_id and (
                        identifier.root == oid or oid in identifier.root
                    ):
                        matching_documents.append(document)
                        break

        return matching_documents
