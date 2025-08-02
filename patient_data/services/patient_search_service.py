"""
EU Patient Search Services
Basic implementation for patient search and credential management
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientCredentials:
    """Patient credentials for search operations"""

    given_name: str
    family_name: str
    birth_date: str
    gender: str
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
    preferred_cda_type: str = "L3"  # Default to L3 for rendering

    def __post_init__(self):
        if self.available_documents is None:
            self.available_documents = []
        if self.confidence_score == 1.0 and self.match_score != 1.0:
            self.confidence_score = self.match_score

        # Set legacy cda_content to preferred type for backward compatibility
        if self.preferred_cda_type == "L3" and self.l3_cda_content:
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

    def get_rendering_cda(self) -> tuple[Optional[str], str]:
        """Get the CDA content and type for rendering"""
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

    def search_patient(self, credentials: PatientCredentials) -> List[PatientMatch]:
        """
        Search for patient across EU member states

        Args:
            credentials: Patient search credentials

        Returns:
            List of patient matches
        """
        self.logger.info(
            f"Searching for patient: {credentials.given_name} {credentials.family_name}"
        )

        # For now, return a mock result based on the search credentials
        matches = []

        if credentials.patient_id:
            # Direct patient ID match
            # Load real CDA documents from test data
            import os
            from django.conf import settings

            # Try to load the real L1 CDA document for this patient
            test_data_path = os.path.join(
                settings.BASE_DIR,
                "test_data",
                "eu_member_states",
                credentials.country_code.upper(),
            )
            l1_cda_content = None
            l1_file_path = None

            # Look for the specific patient file
            if credentials.patient_id == "3843082788":  # CELESTINA DOE-CALLA
                celestina_file = os.path.join(
                    test_data_path, "CELESTINA_DOE-CALLA_38430827.xml"
                )
                if os.path.exists(celestina_file):
                    with open(celestina_file, "r", encoding="utf-8") as f:
                        l1_cda_content = f.read()
                    l1_file_path = celestina_file
                    logger.info(
                        f"Loaded real L1 CDA for patient {credentials.patient_id} from {celestina_file}"
                    )

            # If no real L1 found, use mock L1 content
            if not l1_cda_content:
                l1_file_path = f"test_data/eu_member_states/{credentials.country_code.lower()}/l1_cda_sample.xml"
                l1_cda_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.3.6.1.4.1.19376.1.5.3.1.1.1" extension="L1"/>
    <!-- L1 CDA with embedded PDF in nonXMLBody -->
    <component>
        <nonXMLBody>
            <text mediaType="application/pdf" representation="B64">
                JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKPD4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQo+PgplbmRvYmoKeHJlZgowIDQKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAwIG4gCjAwMDAwMDAwNzkgMDAwMDAgbiAKMDAwMDAwMDEzNiAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDQKL1Jvb3QgMSAwIFIKPj4Kc3RhcnR4cmVmCjIwNAolJUVPRgo=
            </text>
        </nonXMLBody>
    </component>
</ClinicalDocument>"""

            # Mock L3 CDA with structured clinical content
            l3_file_path = f"test_data/eu_member_states/{credentials.country_code.lower()}/l3_cda_sample.xml"
            l3_cda_content = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.3.6.1.4.1.19376.1.5.3.1.1.1" extension="L3"/>
    <!-- L3 CDA with structured clinical content -->
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.1.8"/>
                    <code code="10160-0" codeSystem="2.16.840.1.113883.6.1" displayName="HISTORY OF MEDICATION USE"/>
                    <title>Medications</title>
                    <text>
                        <table>
                            <thead>
                                <tr><th>Medication</th><th>Dosage</th><th>Frequency</th></tr>
                            </thead>
                            <tbody>
                                <tr><td>Aspirin</td><td>100mg</td><td>Once daily</td></tr>
                            </tbody>
                        </table>
                    </text>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

            match = PatientMatch(
                patient_id=credentials.patient_id,
                given_name=credentials.given_name,
                family_name=credentials.family_name,
                birth_date=credentials.birth_date,
                gender=credentials.gender,
                country_code=credentials.country_code,
                match_score=1.0,
                confidence_score=1.0,
                l1_cda_path=l1_file_path,
                l3_cda_path=l3_file_path,
                l1_cda_content=l1_cda_content,
                l3_cda_content=l3_cda_content,
                patient_data={
                    "id": credentials.patient_id,
                    "name": f"{credentials.given_name} {credentials.family_name}",
                    "birth_date": credentials.birth_date,
                    "gender": credentials.gender,
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
