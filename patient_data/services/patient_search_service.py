"""
EU Patient Search Services
Basic implementation for patient search and credential management
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class PatientCredentials:
    """NCP-to-NCP patient query credentials"""

    country_code: str
    patient_id: str


@dataclass
class PatientMatch:
    """Patient match result from search"""

    patient_id: str
    given_name: str
    family_name: str
    birth_date: str
    gender: str
    country_code: str
    match_score: float = 1.0
    available_documents: List[str] = None
    file_path: Optional[str] = None
    confidence_score: float = 1.0
    patient_data: Optional[Dict[str, Any]] = None
    cda_content: Optional[str] = None
    # Enhanced CDA support
    l1_cda_content: Optional[str] = None
    l3_cda_content: Optional[str] = None
    l1_cda_path: Optional[str] = None
    l3_cda_path: Optional[str] = None
    preferred_cda_type: str = "L3"  # Will be auto-determined in __post_init__

    def __post_init__(self):
        if self.available_documents is None:
            self.available_documents = []
        if self.confidence_score == 1.0 and self.match_score != 1.0:
            self.confidence_score = self.match_score

        # Auto-determine preferred CDA type based on what's actually available
        # Priority: Use what's available, prefer L1 for unstructured docs, L3 for structured
        if self.l1_cda_content and self.l3_cda_content:
            # Both available - determine which is more appropriate by analyzing structure
            # For now, prefer L1 as it's the original document format
            self.preferred_cda_type = "L1"
        elif self.l1_cda_content and not self.l3_cda_content:
            # Only L1 available - use it
            self.preferred_cda_type = "L1"
        elif self.l3_cda_content and not self.l1_cda_content:
            # Only L3 available - use it
            self.preferred_cda_type = "L3"
        # else: keep default "L3" if neither is available

        # Set legacy cda_content to preferred type for backward compatibility
        if self.preferred_cda_type == "L1" and self.l1_cda_content:
            self.cda_content = self.l1_cda_content
            self.file_path = self.l1_cda_path
        elif self.preferred_cda_type == "L3" and self.l3_cda_content:
            self.cda_content = self.l3_cda_content
            self.file_path = self.l3_cda_path
        elif self.l1_cda_content:
            self.cda_content = self.l1_cda_content
            self.file_path = self.l1_cda_path

    def has_l1_cda(self) -> bool:
        """Check if L1 CDA is available"""
        return bool(self.l1_cda_content)

    def has_l3_cda(self) -> bool:
        """Check if L3 CDA is available"""
        return bool(self.l3_cda_content)

    def get_rendering_cda(
        self, preferred_type: Optional[str] = None
    ) -> tuple[Optional[str], str]:
        """Get the CDA content and type for rendering

        Args:
            preferred_type: Preferred CDA type ('L1' or 'L3'). If None, defaults to L3.
        """
        # If specific type is requested and available, use it
        if preferred_type == "L1" and self.l1_cda_content:
            return self.l1_cda_content, "L1"
        elif preferred_type == "L3" and self.l3_cda_content:
            return self.l3_cda_content, "L3"

        # Fallback to default logic (prefer L3, then L1)
        if self.l3_cda_content:
            return self.l3_cda_content, "L3"
        elif self.l1_cda_content:
            return self.l1_cda_content, "L1"
        return None, "None"

    def get_orcd_cda(self) -> Optional[str]:
        """Get the CDA content for ORCD (PDF) extraction - prefer L1"""
        return self.l1_cda_content or self.l3_cda_content


class EUPatientSearchService:
    """
    EU Patient Search Service
    Handles patient search across EU member states
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def extract_patient_info_from_cda(self, cda_content: str) -> Dict[str, str]:
        """Extract patient information from CDA content"""
        try:
            root = ET.fromstring(cda_content)
            namespaces = {
                "hl7": "urn:hl7-org:v3",
                "ext": "urn:hl7-EE-DL-Ext:v1",
            }

            # Find patient role
            patient_role = root.find(".//hl7:patientRole", namespaces)
            if patient_role is None:
                # Return default values if patient info not found
                return {
                    "given_name": "Unknown",
                    "family_name": "Patient",
                    "birth_date": "",
                    "gender": "",
                }

            # Extract patient name
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
                "given_name": given_name,
                "family_name": family_name,
                "birth_date": birth_date,
                "gender": gender,
            }

        except Exception as e:
            self.logger.error(f"Error extracting patient info from CDA: {e}")
            return {
                "given_name": "Unknown",
                "family_name": "Patient",
                "birth_date": "",
                "gender": "",
            }

    def search_patient(self, credentials: PatientCredentials) -> List[PatientMatch]:
        """
        Search for patient documents using NCP-to-NCP query

        Args:
            credentials: Country code and patient identifier

        Returns:
            List of patient matches with CDA documents
        """
        self.logger.info(
            f"NCP Query - Patient ID: {credentials.patient_id} from {credentials.country_code}"
        )

        matches = []

        if credentials.patient_id:
            # Use the new CDA indexing system to find documents
            from .cda_document_index import get_cda_indexer

            indexer = get_cda_indexer()
            documents = indexer.find_patient_documents(
                credentials.patient_id, credentials.country_code
            )

            if documents:
                # Group documents by type (L1, L3)
                l1_docs = [doc for doc in documents if doc.cda_type == "L1"]
                l3_docs = [doc for doc in documents if doc.cda_type == "L3"]

                # Load CDA content
                l1_cda_content = None
                l3_cda_content = None
                l1_file_path = None
                l3_file_path = None

                # Load L1 document if available
                if l1_docs:
                    l1_doc = l1_docs[0]  # Use first L1 document
                    try:
                        with open(l1_doc.file_path, "r", encoding="utf-8") as f:
                            l1_cda_content = f.read()
                        l1_file_path = l1_doc.file_path
                        self.logger.info(
                            f"Loaded L1 CDA from index: {l1_doc.file_path}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error loading L1 CDA {l1_doc.file_path}: {e}"
                        )

                # Load L3 document if available
                if l3_docs:
                    l3_doc = l3_docs[0]  # Use first L3 document
                    try:
                        with open(l3_doc.file_path, "r", encoding="utf-8") as f:
                            l3_cda_content = f.read()
                        l3_file_path = l3_doc.file_path
                        self.logger.info(
                            f"Loaded L3 CDA from index: {l3_doc.file_path}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error loading L3 CDA {l3_doc.file_path}: {e}"
                        )

                # Use patient info from index
                first_doc = documents[0]
                patient_info = {
                    "given_name": first_doc.given_name,
                    "family_name": first_doc.family_name,
                    "birth_date": first_doc.birth_date,
                    "gender": first_doc.gender,
                }

                self.logger.info(
                    f"Found indexed patient: {patient_info['given_name']} {patient_info['family_name']} "
                    f"with {len(l1_docs)} L1 and {len(l3_docs)} L3 documents"
                )

                # Create PatientMatch from indexed data
                match = PatientMatch(
                    patient_id=credentials.patient_id,
                    given_name=patient_info["given_name"],
                    family_name=patient_info["family_name"],
                    birth_date=patient_info["birth_date"],
                    gender=patient_info["gender"],
                    country_code=credentials.country_code,
                    match_score=1.0,
                    confidence_score=1.0,
                    l1_cda_path=l1_file_path,
                    l3_cda_path=l3_file_path,
                    l1_cda_content=l1_cda_content,
                    l3_cda_content=l3_cda_content,
                    patient_data={
                        "id": credentials.patient_id,
                        "name": f"{patient_info['given_name']} {patient_info['family_name']}",
                        "given_name": patient_info["given_name"],
                        "family_name": patient_info["family_name"],
                        "birth_date": patient_info["birth_date"],
                        "gender": patient_info["gender"],
                    },
                    available_documents=["L1_CDA", "L3_CDA", "eDispensation", "ePS"],
                )
                matches.append(match)

            else:
                # Fallback to mock data if not found in index
                self.logger.warning(
                    f"Patient {credentials.patient_id} not found in index, using fallback"
                )
                patient_info = self.extract_patient_info_from_cda(
                    ""
                )  # Returns default values

                # Create fallback mock CDA content
                l1_cda_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.3.6.1.4.1.19376.1.5.3.1.1.1" extension="L1"/>
    <recordTarget>
        <patientRole>
            <id assigningAuthorityName="Mock Authority" extension="{}" root="2.16.840.1.113883.2.9.4.3.2"/>
            <patient>
                <name>
                    <family>Patient</family>
                    <given>Mock</given>
                </name>
                <administrativeGenderCode code="U"/>
                <birthTime value=""/>
            </patient>
        </patientRole>
    </recordTarget>
    <component>
        <nonXMLBody>
            <text mediaType="application/pdf" representation="B64">
                Mock PDF content
            </text>
        </nonXMLBody>
    </component>
</ClinicalDocument>""".format(
                    credentials.patient_id
                )

                l3_cda_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.3.6.1.4.1.19376.1.5.3.1.1.1" extension="L3"/>
    <recordTarget>
        <patientRole>
            <id assigningAuthorityName="Mock Authority" extension="{}" root="2.16.840.1.113883.2.9.4.3.2"/>
            <patient>
                <name>
                    <family>Patient</family>
                    <given>Mock</given>
                </name>
                <administrativeGenderCode code="U"/>
                <birthTime value=""/>
            </patient>
        </patientRole>
    </recordTarget>
    <component>
        <structuredBody>
            <component>
                <section>
                    <title>Mock Clinical Section</title>
                    <text>No real clinical data available for this patient ID.</text>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>""".format(
                    credentials.patient_id
                )

                l1_file_path = f"mock/l1_{credentials.patient_id}.xml"
                l3_file_path = f"mock/l3_{credentials.patient_id}.xml"

                # Create fallback match
                match = PatientMatch(
                    patient_id=credentials.patient_id,
                    given_name=patient_info["given_name"],
                    family_name=patient_info["family_name"],
                    birth_date=patient_info["birth_date"],
                    gender=patient_info["gender"],
                    country_code=credentials.country_code,
                    match_score=1.0,
                    confidence_score=1.0,
                    l1_cda_path=l1_file_path,
                    l3_cda_path=l3_file_path,
                    l1_cda_content=l1_cda_content,
                    l3_cda_content=l3_cda_content,
                    patient_data={
                        "id": credentials.patient_id,
                        "name": f"{patient_info['given_name']} {patient_info['family_name']}",
                        "given_name": patient_info["given_name"],
                        "family_name": patient_info["family_name"],
                        "birth_date": patient_info["birth_date"],
                        "gender": patient_info["gender"],
                    },
                    available_documents=["L1_CDA", "L3_CDA", "eDispensation", "ePS"],
                )
                matches.append(match)

        return matches

    def get_patient_documents(
        self, patient_id: str, country_code: str
    ) -> List[Dict[str, Any]]:
        """
        Get available documents for a patient

        Args:
            patient_id: Patient identifier
            country_code: Country code

        Returns:
            List of available documents
        """
        self.logger.info(
            f"Getting documents for patient {patient_id} in {country_code}"
        )

        # Mock document list
        documents = [
            {
                "type": "CDA",
                "id": f"cda_{patient_id}",
                "title": "Clinical Document Architecture",
                "date": "2024-01-15",
                "status": "available",
            },
            {
                "type": "ePS",
                "id": f"eps_{patient_id}",
                "title": "Electronic Prescription",
                "date": "2024-01-10",
                "status": "available",
            },
        ]

        return documents

    def get_patient_summary(self, match: "PatientMatch") -> Dict[str, Any]:
        """
        Get a summary of patient information for display

        Args:
            match: PatientMatch object with patient information

        Returns:
            Dictionary with patient summary data structured for template access
        """
        self.logger.info(f"Getting patient summary for {match.patient_id}")

        # Create a comprehensive patient summary with nested structure for template
        rendering_cda, cda_type = match.get_rendering_cda()

        summary = {
            "patient_info": {
                "name": f"{match.given_name} {match.family_name}",
                "patient_id": match.patient_id,
                "given_name": match.given_name,
                "family_name": match.family_name,
                "birth_date": match.birth_date,
                "gender": match.gender,
                "country_code": match.country_code,
            },
            "document_info": {
                "title": f"Clinical Document Architecture ({cda_type})",
                "date": "2024-01-15",  # Mock date
                "type": cda_type,
                "file_path": match.file_path,
                "status": "available",
                "rendering_type": cda_type,
                "has_l1": match.has_l1_cda(),
                "has_l3": match.has_l3_cda(),
            },
            "match_info": {
                "confidence_score": match.confidence_score,
                "match_score": match.match_score,
                "status": "active" if match.confidence_score > 0.8 else "uncertain",
            },
            "available_documents": match.available_documents or [],
            "cda_available": match.has_l1_cda() or match.has_l3_cda(),
            "l1_cda_available": match.has_l1_cda(),
            "l3_cda_available": match.has_l3_cda(),
            "eps_available": "ePS" in (match.available_documents or []),
            "edispensation_available": "eDispensation"
            in (match.available_documents or []),
            "document_count": len(match.available_documents or []),
            "last_updated": "2024-01-15",  # Mock date
        }

        return summary
