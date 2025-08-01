"""
EU Patient Data Search Service
Intelligent search through EU member state CDA documents
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PatientCredentials:
    """Patient search credentials from form submission"""

    given_name: str = ""
    family_name: str = ""
    birth_date: str = ""  # Format: YYYYMMDD or YYYY-MM-DD
    gender: str = ""  # M/F
    country_code: str = ""
    patient_id: str = ""

    def normalize_birth_date(self) -> str:
        """Convert birth date to YYYYMMDD format"""
        if not self.birth_date:
            return ""

        # Remove any non-digit characters
        clean_date = re.sub(r"\D", "", self.birth_date)

        # Ensure 8 digits
        if len(clean_date) == 8:
            return clean_date

        return ""


@dataclass
class PatientMatch:
    """Result of patient search"""

    file_path: str
    country_code: str
    confidence_score: float
    patient_data: Dict
    cda_content: str


class EUPatientSearchService:
    """Service for searching EU member state patient data"""

    def __init__(self, test_data_path: str = None):
        if test_data_path is None:
            test_data_path = os.path.join(
                os.path.dirname(__file__), "..", "test_data", "eu_member_states"
            )
        self.test_data_path = test_data_path
        self.namespaces = {"hl7": "urn:hl7-org:v3", "ext": "urn:hl7-EE-DL-Ext:v1"}

    def search_patient(self, credentials: PatientCredentials) -> Optional[PatientMatch]:
        """
        Smart search for patient across EU member states
        Returns the best matching CDA document
        """
        logger.info(
            f"Searching for patient: {credentials.given_name} {credentials.family_name}"
        )

        matches = []

        # Search specific country first if provided
        if credentials.country_code:
            country_matches = self._search_country(
                credentials, credentials.country_code.upper()
            )
            matches.extend(country_matches)
        else:
            # Search all countries
            for country_dir in os.listdir(self.test_data_path):
                country_path = os.path.join(self.test_data_path, country_dir)
                if os.path.isdir(country_path):
                    country_matches = self._search_country(credentials, country_dir)
                    matches.extend(country_matches)

        # Return best match (highest confidence score)
        if matches:
            best_match = max(matches, key=lambda x: x.confidence_score)
            logger.info(
                f"Best match found: {best_match.file_path} (score: {best_match.confidence_score})"
            )
            return best_match

        logger.warning(
            f"No matches found for patient: {credentials.given_name} {credentials.family_name}"
        )
        return None

    def _search_country(
        self, credentials: PatientCredentials, country_code: str
    ) -> List[PatientMatch]:
        """Search for patient within a specific country's data"""
        matches = []
        country_path = os.path.join(self.test_data_path, country_code)

        if not os.path.exists(country_path):
            return matches

        # Search all XML files in country directory
        for root, dirs, files in os.walk(country_path):
            for file in files:
                if file.endswith(".xml"):
                    file_path = os.path.join(root, file)
                    try:
                        match = self._analyze_cda_file(
                            credentials, file_path, country_code
                        )
                        if match and match.confidence_score > 0:
                            matches.append(match)
                    except Exception as e:
                        logger.error(f"Error analyzing file {file_path}: {e}")

        return matches

    def _analyze_cda_file(
        self, credentials: PatientCredentials, file_path: str, country_code: str
    ) -> Optional[PatientMatch]:
        """Analyze a single CDA file for patient match"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract patient data from CDA
            patient_data = self._extract_patient_data(root)

            # Calculate confidence score
            confidence = self._calculate_confidence(credentials, patient_data)

            if confidence > 0:
                # Read full CDA content
                with open(file_path, "r", encoding="utf-8") as f:
                    cda_content = f.read()

                return PatientMatch(
                    file_path=file_path,
                    country_code=country_code,
                    confidence_score=confidence,
                    patient_data=patient_data,
                    cda_content=cda_content,
                )

        except ET.ParseError as e:
            logger.error(f"XML parsing error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error analyzing {file_path}: {e}")

        return None

    def _extract_patient_data(self, root: ET.Element) -> Dict:
        """Extract patient information from CDA XML"""
        patient_data = {}

        try:
            # Find patient element
            patient_role = root.find(
                ".//hl7:recordTarget/hl7:patientRole", self.namespaces
            )
            if patient_role is not None:
                patient = patient_role.find("hl7:patient", self.namespaces)

                if patient is not None:
                    # Extract names
                    name_elem = patient.find("hl7:name", self.namespaces)
                    if name_elem is not None:
                        given = name_elem.find("hl7:given", self.namespaces)
                        family = name_elem.find("hl7:family", self.namespaces)

                        if given is not None and given.text:
                            patient_data["given_name"] = given.text.strip()
                        if family is not None and family.text:
                            patient_data["family_name"] = family.text.strip()

                    # Extract birth date
                    birth_time = patient.find("hl7:birthTime", self.namespaces)
                    if birth_time is not None:
                        patient_data["birth_date"] = birth_time.get("value", "")

                    # Extract gender
                    gender = patient.find(
                        "hl7:administrativeGenderCode", self.namespaces
                    )
                    if gender is not None:
                        patient_data["gender"] = gender.get("code", "")

                # Extract patient ID
                id_elem = patient_role.find("hl7:id", self.namespaces)
                if id_elem is not None:
                    patient_data["patient_id"] = id_elem.get("extension", "")

                # Extract address/country
                addr = patient_role.find("hl7:addr", self.namespaces)
                if addr is not None:
                    country = addr.find("hl7:country", self.namespaces)
                    if country is not None:
                        patient_data["country"] = country.text

            # Extract document metadata
            realm_code = root.find("hl7:realmCode", self.namespaces)
            if realm_code is not None:
                patient_data["document_country"] = realm_code.get("code", "")

            # Extract document title
            title = root.find("hl7:title", self.namespaces)
            if title is not None:
                patient_data["document_title"] = title.text

            # Extract effective time
            effective_time = root.find("hl7:effectiveTime", self.namespaces)
            if effective_time is not None:
                patient_data["document_date"] = effective_time.get("value", "")

        except Exception as e:
            logger.error(f"Error extracting patient data: {e}")

        return patient_data

    def _calculate_confidence(
        self, credentials: PatientCredentials, patient_data: Dict
    ) -> float:
        """Calculate confidence score for patient match (0.0 to 1.0)"""
        score = 0.0
        max_score = 0.0

        # Name matching (most important)
        if credentials.given_name and patient_data.get("given_name"):
            max_score += 0.4
            if self._fuzzy_match(credentials.given_name, patient_data["given_name"]):
                score += 0.4

        if credentials.family_name and patient_data.get("family_name"):
            max_score += 0.4
            if self._fuzzy_match(credentials.family_name, patient_data["family_name"]):
                score += 0.4

        # Birth date matching
        if credentials.birth_date and patient_data.get("birth_date"):
            max_score += 0.15
            cred_date = credentials.normalize_birth_date()
            patient_date = re.sub(r"\D", "", patient_data["birth_date"])[:8]

            if cred_date and patient_date and cred_date == patient_date:
                score += 0.15

        # Gender matching
        if credentials.gender and patient_data.get("gender"):
            max_score += 0.05
            if credentials.gender.upper() == patient_data["gender"].upper():
                score += 0.05

        # Patient ID exact match (if provided)
        if credentials.patient_id and patient_data.get("patient_id"):
            max_score += 0.3
            if credentials.patient_id == patient_data["patient_id"]:
                score += 0.3

        # Normalize score
        if max_score > 0:
            return score / max_score

        return 0.0

    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching"""
        if not str1 or not str2:
            return False

        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        # Exact match
        if str1 == str2:
            return True

        # Contains match
        if str1 in str2 or str2 in str1:
            return True

        # Simple character similarity
        common_chars = len(set(str1) & set(str2))
        total_chars = len(set(str1) | set(str2))

        if total_chars > 0:
            similarity = common_chars / total_chars
            return similarity >= threshold

        return False

    def get_patient_summary(self, match: PatientMatch) -> Dict:
        """Extract structured patient summary from CDA match"""
        summary = {
            "patient_info": {
                "name": f"{match.patient_data.get('given_name', '')} {match.patient_data.get('family_name', '')}".strip(),
                "birth_date": self._format_date(
                    match.patient_data.get("birth_date", "")
                ),
                "gender": self._format_gender(match.patient_data.get("gender", "")),
                "patient_id": match.patient_data.get("patient_id", ""),
                "country": match.patient_data.get("country", match.country_code),
            },
            "document_info": {
                "title": match.patient_data.get("document_title", "Patient Summary"),
                "country": match.country_code,
                "date": self._format_date(match.patient_data.get("document_date", "")),
                "file_path": match.file_path,
                "confidence": round(match.confidence_score * 100, 1),
            },
            "cda_content": match.cda_content,
        }

        return summary

    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        if not date_str:
            return "Not provided"

        # Extract date part (YYYYMMDD)
        clean_date = re.sub(r"\D", "", date_str)[:8]

        if len(clean_date) == 8:
            try:
                year = clean_date[:4]
                month = clean_date[4:6]
                day = clean_date[6:8]

                date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                return date_obj.strftime("%d %B %Y")
            except ValueError:
                pass

        return date_str

    def _format_gender(self, gender_code: str) -> str:
        """Format gender code for display"""
        gender_map = {"M": "Male", "F": "Female", "U": "Unknown"}
        return gender_map.get(gender_code.upper(), gender_code)
