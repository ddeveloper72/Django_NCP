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

    def __post_init__(self):
        if self.available_documents is None:
            self.available_documents = []
        if self.confidence_score == 1.0 and self.match_score != 1.0:
            self.confidence_score = self.match_score


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
            # Create a mock file path for testing
            file_path = f"test_data/eu_member_states/{credentials.country_code.lower()}/cda_sample.xml"

            match = PatientMatch(
                patient_id=credentials.patient_id,
                given_name=credentials.given_name,
                family_name=credentials.family_name,
                birth_date=credentials.birth_date,
                gender=credentials.gender,
                country_code=credentials.country_code,
                match_score=1.0,
                confidence_score=1.0,
                file_path=file_path,
                patient_data={
                    "id": credentials.patient_id,
                    "name": f"{credentials.given_name} {credentials.family_name}",
                    "birth_date": credentials.birth_date,
                    "gender": credentials.gender,
                },
                cda_content="Mock CDA content - to be loaded from file",
                available_documents=["CDA", "eDispensation", "ePS"],
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
                "title": "Clinical Document Architecture (CDA)",
                "date": "2024-01-15",  # Mock date
                "type": "CDA",
                "file_path": match.file_path,
                "status": "available",
            },
            "match_info": {
                "confidence_score": match.confidence_score,
                "match_score": match.match_score,
                "status": "active" if match.confidence_score > 0.8 else "uncertain",
            },
            "available_documents": match.available_documents or [],
            "cda_available": "CDA" in (match.available_documents or []),
            "eps_available": "ePS" in (match.available_documents or []),
            "edispensation_available": "eDispensation"
            in (match.available_documents or []),
            "document_count": len(match.available_documents or []),
            "last_updated": "2024-01-15",  # Mock date
        }

        return summary
