"""
Patient Data Loader Service
Loads and parses sample patient data from OpenNCP integration files
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientInfo:
    """Patient information from properties files"""

    patient_id: str
    oid: str
    family_name: str
    given_name: str
    administrative_gender: str
    birth_date: datetime
    street: str
    city: str
    postal_code: str
    country: str
    telephone: str
    email: str

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}"

    @property
    def birth_date_formatted(self) -> str:
        return self.birth_date.strftime("%Y/%m/%d")


class PatientDataLoader:
    """Loads patient data from OpenNCP integration files"""

    def __init__(self):
        self.integration_path = Path(__file__).parent / "sample_data" / "integration"
        self.oid_mapping = self._load_oid_mapping()
        self._patient_cache = {}

    def _load_oid_mapping(self) -> Dict:
        """Load OID to country mapping"""
        mapping_file = self.integration_path / "oid_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, "r") as f:
                return json.load(f)
        return {}

    def get_available_oids(self) -> List[str]:
        """Get list of available OIDs with patient data"""
        oids = []
        if self.integration_path.exists():
            for item in self.integration_path.iterdir():
                if (
                    item.is_dir()
                    and item.name.replace(".", "").replace("_", "").isdigit()
                ):
                    oids.append(item.name)
        return sorted(oids)

    def get_patients_for_oid(self, oid: str) -> List[str]:
        """Get list of patient IDs for a given OID"""
        oid_path = self.integration_path / oid
        patient_ids = []

        if oid_path.exists():
            for file_path in oid_path.glob("*.properties"):
                # Extract patient ID from filename (e.g., "1-1234-W8.properties" -> "1-1234-W8")
                patient_id = file_path.stem
                patient_ids.append(patient_id)

        return sorted(patient_ids)

    def load_patient_data(self, oid: str, patient_id: str) -> Optional[PatientInfo]:
        """Load patient data from properties file"""
        cache_key = f"{oid}:{patient_id}"

        if cache_key in self._patient_cache:
            return self._patient_cache[cache_key]

        patient_file = self.integration_path / oid / f"{patient_id}.properties"

        if not patient_file.exists():
            logger.warning(f"Patient file not found: {patient_file}")
            return None

        try:
            # Parse properties file
            properties = {}
            with open(patient_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        properties[key.strip()] = value.strip()

            # Extract birth date
            birth_year = int(properties.get("birthDate.year", "1900"))
            birth_month = int(properties.get("birthDate.month", "1"))
            birth_day = int(properties.get("birthDate.day", "1"))
            birth_date = datetime(birth_year, birth_month, birth_day)

            # Create PatientInfo object
            patient_info = PatientInfo(
                patient_id=patient_id,
                oid=oid,
                family_name=properties.get("familyName", ""),
                given_name=properties.get("givenName", ""),
                administrative_gender=properties.get("administrativeGender", ""),
                birth_date=birth_date,
                street=properties.get("street", ""),
                city=properties.get("city", ""),
                postal_code=properties.get("postalCode", ""),
                country=properties.get("country", ""),
                telephone=properties.get("telephone", ""),
                email=properties.get("email", ""),
            )

            # Cache the result
            self._patient_cache[cache_key] = patient_info
            return patient_info

        except Exception as e:
            logger.error(f"Error loading patient data from {patient_file}: {str(e)}")
            return None

    def search_patient(
        self, oid: str, patient_id: str, birth_date: str
    ) -> Tuple[bool, Optional[PatientInfo], str]:
        """
        Search for a patient and validate birth date
        Returns: (found, patient_info, message)
        """
        patient_info = self.load_patient_data(oid, patient_id)

        if not patient_info:
            return False, None, f"Patient {patient_id} not found in {oid}"

        # Validate birth date
        try:
            provided_date = datetime.strptime(birth_date, "%Y/%m/%d").date()
            if patient_info.birth_date.date() != provided_date:
                return False, patient_info, "Birth date does not match records"
        except ValueError:
            return False, patient_info, "Invalid birth date format"

        return True, patient_info, "Patient found and validated"

    def get_country_for_oid(self, oid: str) -> str:
        """Get country name for OID"""
        if oid in self.oid_mapping:
            return self.oid_mapping[oid].get("country_name", f"Country_{oid}")
        return f"Country_{oid}"

    def get_all_patients(self) -> Dict[str, List[PatientInfo]]:
        """Get all patients grouped by OID"""
        all_patients = {}

        for oid in self.get_available_oids():
            patients = []
            for patient_id in self.get_patients_for_oid(oid):
                patient_info = self.load_patient_data(oid, patient_id)
                if patient_info:
                    patients.append(patient_info)
            all_patients[oid] = patients

        return all_patients


# Global instance
patient_loader = PatientDataLoader()
