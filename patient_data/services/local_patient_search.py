"""
Local Patient Search Service

Provides local patient search functionality for the Django NCP server.
This is a stub implementation for testing URL endpoints.
"""

import logging

logger = logging.getLogger(__name__)


class LocalPatientSearchService:
    """Service for searching patients in local database"""

    def __init__(self):
        """Initialize the local patient search service"""
        self.logger = logger

    def search_patients(self, search_params):
        """
        Search for patients based on provided parameters

        Args:
            search_params (dict): Search parameters including patient identifiers

        Returns:
            dict: Search results or empty result set
        """
        self.logger.info(f"Local patient search requested with params: {search_params}")

        # Return empty result set for now
        return {
            "patients_found": [],
            "total_count": 0,
            "search_performed": True,
            "message": "Local patient search service is available but no test data configured",
        }

    def get_patient_by_id(self, patient_id):
        """
        Get specific patient by ID

        Args:
            patient_id (str): Patient identifier

        Returns:
            dict or None: Patient data if found, None otherwise
        """
        self.logger.info(f"Local patient lookup for ID: {patient_id}")
        return None
