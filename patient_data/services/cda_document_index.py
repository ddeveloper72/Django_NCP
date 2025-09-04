"""
CDA Document Index Management System

This system provides indexing and discovery of test CDA documents without
storing patient data persistently (maintaining realistic NCP workflow).

Features:
- Automatic discovery of CDA documents across EU member states
- Patient ID extraction and indexing
- Dynamic patient lookup for demonstration purposes
- Maintains NCP principle: no persistent patient storage
"""

import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def determine_cda_type_standalone(content: str, file_path: str = "") -> str:
    """
    Standalone function to determine CDA type from content using improved HL7 logic

    Detection rules:
    - Search for <entry> → If present, it's Level 3
    - Search for <section> without <entry> → Likely Level 2
    - If only <nonXMLBody> or plain <text> → It's Level 1
    """
    filename = os.path.basename(file_path).upper() if file_path else ""

    # First check filename patterns (fastest)
    # Check for explicit level indicators first (most specific)
    if "L3" in filename:
        return "L3"
    elif "L1" in filename:
        return "L1"
    elif "L2" in filename:
        return "L2"
    # Then check document type patterns (less specific)
    elif "FRIENDLY" in filename:
        return "L3"  # FRIENDLY documents are typically L3
    elif "PIVOT" in filename:
        return "L1"  # PIVOT documents are typically L1 (but L3 should be caught above)
    else:
        # Determine from content using improved HL7 logic
        try:
            # Count key structural elements
            entry_count = content.count("<entry")
            section_count = content.count("<section")
            has_nonxml_body = "<nonXMLBody" in content
            text_count = content.count("<text")

            # Apply HL7 CDA level detection rules
            if entry_count > 0:
                # Level 3: Structured entries present
                return "L3"
            elif section_count > 0 and entry_count == 0:
                # Level 2: Sections but no structured entries
                return "L2"
            elif has_nonxml_body or (text_count > 0 and entry_count == 0):
                # Level 1: Unstructured content or plain text without entries
                return "L1"
            else:
                # Fallback: check for legacy structuredBody pattern
                if "structuredBody" in content:
                    return "L3"

        except Exception as e:
            logger.warning(f"Error analyzing CDA content: {e}")

    return "Unknown"


@dataclass
class CDADocumentInfo:
    """Information about a CDA document"""

    file_path: str
    patient_id: str
    given_name: str
    family_name: str
    birth_date: str
    gender: str
    country_code: str
    cda_type: str  # L1, L3, etc.
    assigning_authority: str
    last_modified: float
    file_size: int

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CDADocumentInfo":
        return cls(**data)


class CDADocumentIndexer:
    """
    CDA Document Index Manager

    Scans test_data directories and builds an index of available CDA documents
    without storing patient data persistently.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = os.path.join(
            settings.BASE_DIR, "test_data", "eu_member_states"
        )
        self.index_file = os.path.join(settings.BASE_DIR, "cda_document_index.json")
        self.index_cache = None

    def extract_patient_info_from_cda(self, file_path: str) -> Optional[Dict[str, str]]:
        """Extract patient information from CDA file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            root = ET.fromstring(content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "ext": "urn:hl7-EE-DL-Ext:v1",
            }

            # Find patient role
            patient_role = root.find(".//hl7:patientRole", namespaces)
            if patient_role is None:
                return None

            # Extract patient ID
            patient_id = ""
            assigning_authority = ""
            id_elements = patient_role.findall("hl7:id", namespaces)
            if id_elements:
                # Use the first ID element (usually the primary one)
                first_id = id_elements[0]
                patient_id = first_id.get("extension", "")
                assigning_authority = first_id.get("assigningAuthorityName", "")

            if not patient_id:
                return None

            # Extract patient details
            patient = patient_role.find("hl7:patient", namespaces)
            given_name = "Unknown"
            family_name = "Patient"
            birth_date = ""
            gender = ""

            if patient is not None:
                # Extract name
                name_elem = patient.find("hl7:name", namespaces)
                if name_elem is not None:
                    given_elem = name_elem.find("hl7:given", namespaces)
                    family_elem = name_elem.find("hl7:family", namespaces)
                    if given_elem is not None:
                        given_name = given_elem.text or "Unknown"
                    if family_elem is not None:
                        family_name = family_elem.text or "Patient"

                # Extract birth date
                birth_elem = patient.find("hl7:birthTime", namespaces)
                if birth_elem is not None:
                    birth_value = birth_elem.get("value", "")
                    # Convert YYYYMMDD to readable format
                    if len(birth_value) >= 8:
                        birth_date = (
                            f"{birth_value[:4]}-{birth_value[4:6]}-{birth_value[6:8]}"
                        )

                # Extract gender
                gender_elem = patient.find("hl7:administrativeGenderCode", namespaces)
                if gender_elem is not None:
                    gender_code = gender_elem.get("code", "")
                    gender_map = {"M": "Male", "F": "Female", "U": "Unknown"}
                    gender = gender_map.get(gender_code, gender_code)

            return {
                "patient_id": patient_id,
                "given_name": given_name,
                "family_name": family_name,
                "birth_date": birth_date,
                "gender": gender,
                "assigning_authority": assigning_authority,
            }

        except Exception as e:
            self.logger.error(f"Error extracting patient info from {file_path}: {e}")
            return None

    def determine_cda_type(self, file_path: str) -> str:
        """
        Determine CDA type from filename or content using improved HL7 logic

        Detection rules:
        - Search for <entry> → If present, it's Level 3
        - Search for <section> without <entry> → Likely Level 2
        - If only <nonXMLBody> or plain <text> → It's Level 1
        """
        filename = os.path.basename(file_path).upper()

        # First check filename patterns (fastest)
        # Check for explicit level indicators first (most specific)
        if "L3" in filename:
            return "L3"
        elif "L1" in filename:
            return "L1"
        elif "L2" in filename:
            return "L2"
        # Then check document type patterns (less specific)
        elif "FRIENDLY" in filename:
            return "L3"  # FRIENDLY documents are typically L3
        elif "PIVOT" in filename:
            return (
                "L1"  # PIVOT documents are typically L1 (but L3 should be caught above)
            )
        else:
            # Determine from content using improved HL7 logic
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Count key structural elements
                entry_count = content.count("<entry")
                section_count = content.count("<section")
                has_nonxml_body = "<nonXMLBody" in content
                text_count = content.count("<text")

                # Apply HL7 CDA level detection rules
                if entry_count > 0:
                    # Level 3: Structured entries present
                    return "L3"
                elif section_count > 0 and entry_count == 0:
                    # Level 2: Sections but no structured entries
                    return "L2"
                elif has_nonxml_body or (text_count > 0 and entry_count == 0):
                    # Level 1: Unstructured content or plain text without entries
                    return "L1"
                else:
                    # Fallback: check for legacy structuredBody pattern
                    if "structuredBody" in content:
                        return "L3"

            except Exception as e:
                self.logger.warning(f"Error reading CDA content from {file_path}: {e}")

        return "Unknown"

    def scan_cda_documents(self) -> List[CDADocumentInfo]:
        """Scan all CDA documents and extract patient information"""
        documents = []

        if not os.path.exists(self.base_path):
            self.logger.warning(f"Test data path not found: {self.base_path}")
            return documents

        for country_code in os.listdir(self.base_path):
            country_path = os.path.join(self.base_path, country_code)

            if not os.path.isdir(country_path):
                continue

            self.logger.info(f"Scanning CDA documents for country: {country_code}")

            for filename in os.listdir(country_path):
                if filename.endswith(".xml"):
                    file_path = os.path.join(country_path, filename)

                    # Extract patient information
                    patient_info = self.extract_patient_info_from_cda(file_path)
                    if patient_info:
                        # Get file stats
                        stat = os.stat(file_path)

                        doc_info = CDADocumentInfo(
                            file_path=file_path,
                            patient_id=patient_info["patient_id"],
                            given_name=patient_info["given_name"],
                            family_name=patient_info["family_name"],
                            birth_date=patient_info["birth_date"],
                            gender=patient_info["gender"],
                            country_code=country_code,
                            cda_type=self.determine_cda_type(file_path),
                            assigning_authority=patient_info["assigning_authority"],
                            last_modified=stat.st_mtime,
                            file_size=stat.st_size,
                        )

                        documents.append(doc_info)
                        self.logger.info(
                            f"Indexed: {patient_info['given_name']} {patient_info['family_name']} "
                            f"({patient_info['patient_id']}) from {country_code} - {self.determine_cda_type(file_path)}"
                        )

        return documents

    def build_index(
        self, force_rebuild: bool = False
    ) -> Dict[str, List[CDADocumentInfo]]:
        """Build or load the CDA document index"""

        # Check if index file exists and is recent
        if not force_rebuild and os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)

                # Convert back to CDADocumentInfo objects
                index = {}
                for patient_id, docs_data in index_data.items():
                    index[patient_id] = [
                        CDADocumentInfo.from_dict(doc) for doc in docs_data
                    ]

                self.logger.info(f"Loaded CDA index with {len(index)} patients")
                return index

            except Exception as e:
                self.logger.warning(f"Failed to load existing index: {e}")

        # Build new index
        self.logger.info("Building new CDA document index...")
        documents = self.scan_cda_documents()

        # Group by patient ID
        index = {}
        for doc in documents:
            if doc.patient_id not in index:
                index[doc.patient_id] = []
            index[doc.patient_id].append(doc)

        # Save index to file
        try:
            index_data = {}
            for patient_id, docs in index.items():
                index_data[patient_id] = [doc.to_dict() for doc in docs]

            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                f"Saved CDA index with {len(index)} patients to {self.index_file}"
            )

        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")

        return index

    def get_index(self) -> Dict[str, List[CDADocumentInfo]]:
        """Get the current index (cached)"""
        if self.index_cache is None:
            self.index_cache = self.build_index()
        return self.index_cache

    def find_patient_documents(
        self, patient_id: str, country_code: Optional[str] = None
    ) -> List[CDADocumentInfo]:
        """Find all CDA documents for a specific patient"""
        index = self.get_index()

        if patient_id not in index:
            return []

        documents = index[patient_id]

        # Filter by country if specified
        if country_code:
            documents = [
                doc
                for doc in documents
                if doc.country_code.upper() == country_code.upper()
            ]

        return documents

    def get_all_patients(self) -> List[Dict[str, str]]:
        """Get a summary of all indexed patients"""
        index = self.get_index()
        patients = []

        for patient_id, documents in index.items():
            # Use the first document to get patient info
            if documents:
                doc = documents[0]
                patients.append(
                    {
                        "patient_id": patient_id,
                        "given_name": doc.given_name,
                        "family_name": doc.family_name,
                        "birth_date": doc.birth_date,
                        "gender": doc.gender,
                        "country_code": doc.country_code,
                        "assigning_authority": doc.assigning_authority,
                        "document_count": len(documents),
                        "cda_types": list(set(d.cda_type for d in documents)),
                    }
                )

        return patients

    def refresh_index(self):
        """Force refresh of the index"""
        self.index_cache = None
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        return self.build_index(force_rebuild=True)


# Global indexer instance
_indexer = None


def get_cda_indexer() -> CDADocumentIndexer:
    """Get the global CDA indexer instance"""
    global _indexer
    if _indexer is None:
        _indexer = CDADocumentIndexer()
    return _indexer
