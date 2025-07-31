"""
Local Patient Search Service
Searches for Patient Summary documents in local CDA test data following PS Display Guidelines
"""

import os
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from .clinical_pdf_service import ClinicalDocumentPDFService, TestDataManager

logger = logging.getLogger(__name__)


class LocalPatientSearchService:
    """
    Service for searching Patient Summary documents in local CDA test data
    Uses existing clinical PDF service infrastructure for rendering
    """

    def __init__(self):
        self.test_data_manager = TestDataManager()
        self.pdf_service = ClinicalDocumentPDFService()
        self.test_data_path = Path(settings.BASE_DIR) / "test_data" / "eu_member_states"

    def search_patient_summaries(
        self, country_code: str, patient_id: str = None, oid: str = None
    ) -> Tuple[bool, List[Dict], str]:
        """
        Search for Patient Summary documents in local CDA test data

        Args:
            country_code: Two-letter country code (e.g., 'IT', 'GR')
            patient_id: Optional patient identifier to match
            oid: Optional OID to match against document root

        Returns:
            Tuple of (success, documents_list, message)
        """
        try:
            logger.info(f"Searching local CDA documents for country: {country_code}")

            # Check if country directory exists
            country_path = self.test_data_path / country_code.upper()
            if not country_path.exists():
                return False, [], f"No test data available for country: {country_code}"

            # Find all CDA XML files in country directory
            cda_files = list(country_path.glob("*.xml"))
            if not cda_files:
                return False, [], f"No CDA documents found for country: {country_code}"

            logger.info(f"Found {len(cda_files)} CDA files for {country_code}")

            matching_documents = []

            for cda_file in cda_files:
                try:
                    # Parse the CDA document
                    doc_info = self._parse_cda_document(cda_file)
                    if not doc_info:
                        continue

                    # Apply filters if provided
                    if patient_id and doc_info.get("patient_id") != patient_id:
                        continue

                    if oid and not self._matches_oid(doc_info, oid):
                        continue

                    # Extract PDFs from the document using existing service
                    pdf_results = self.pdf_service.extract_pdfs_from_xml(str(cda_file))
                    doc_info["extracted_pdfs"] = pdf_results

                    matching_documents.append(doc_info)

                except Exception as e:
                    logger.warning(f"Error processing CDA file {cda_file}: {e}")
                    continue

            if matching_documents:
                message = f"Found {len(matching_documents)} Patient Summary document(s)"
                if patient_id:
                    message += f" for patient ID: {patient_id}"
                return True, matching_documents, message
            else:
                message = f"No matching Patient Summary documents found"
                if patient_id:
                    message += f" for patient ID: {patient_id}"
                return False, [], message

        except Exception as e:
            logger.error(f"Error in local patient search: {e}", exc_info=True)
            return False, [], f"Search error: {str(e)}"

    def _parse_cda_document(self, file_path: Path) -> Optional[Dict]:
        """
        Parse CDA document to extract patient and document information

        Returns:
            Dictionary with document information or None if parsing fails
        """
        try:
            # Parse XML with namespace handling
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Define namespace mapping for CDA
            ns = {"cda": "urn:hl7-org:v3"}

            # Extract document information
            doc_info = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "document_type": "Patient Summary",
                "country_code": file_path.parent.name,
            }

            # Extract document ID and root
            doc_id_elem = root.find(".//cda:id", ns)
            if doc_id_elem is not None:
                doc_info["document_id"] = doc_id_elem.get("extension", "")
                doc_info["document_root"] = doc_id_elem.get("root", "")

            # Extract effective time
            effective_time_elem = root.find(".//cda:effectiveTime", ns)
            if effective_time_elem is not None:
                doc_info["effective_time"] = effective_time_elem.get("value", "")

            # Extract patient information
            patient_role = root.find(".//cda:recordTarget/cda:patientRole", ns)
            if patient_role is not None:
                # Patient ID
                patient_id_elem = patient_role.find(".//cda:id", ns)
                if patient_id_elem is not None:
                    doc_info["patient_id"] = patient_id_elem.get("extension", "")
                    doc_info["patient_id_root"] = patient_id_elem.get("root", "")
                    doc_info["assigning_authority"] = patient_id_elem.get(
                        "assigningAuthorityName", ""
                    )

                # Patient name
                patient_elem = patient_role.find(".//cda:patient", ns)
                if patient_elem is not None:
                    name_elem = patient_elem.find(".//cda:name", ns)
                    if name_elem is not None:
                        family_name = name_elem.find(".//cda:family", ns)
                        given_name = name_elem.find(".//cda:given", ns)
                        doc_info["patient_family_name"] = (
                            family_name.text if family_name is not None else ""
                        )
                        doc_info["patient_given_name"] = (
                            given_name.text if given_name is not None else ""
                        )

                    # Gender
                    gender_elem = patient_elem.find(
                        ".//cda:administrativeGenderCode", ns
                    )
                    if gender_elem is not None:
                        doc_info["patient_gender"] = gender_elem.get("code", "")

                    # Birth time
                    birth_elem = patient_elem.find(".//cda:birthTime", ns)
                    if birth_elem is not None:
                        doc_info["patient_birth_time"] = birth_elem.get("value", "")

                # Patient address
                addr_elem = patient_role.find(".//cda:addr", ns)
                if addr_elem is not None:
                    country_elem = addr_elem.find(".//cda:country", ns)
                    city_elem = addr_elem.find(".//cda:city", ns)
                    doc_info["patient_country"] = (
                        country_elem.text if country_elem is not None else ""
                    )
                    doc_info["patient_city"] = (
                        city_elem.text if city_elem is not None else ""
                    )

            # Determine document validation level (L1/L3) from filename
            if "L1" in file_path.name:
                doc_info["validation_level"] = "L1"
            elif "L3" in file_path.name:
                doc_info["validation_level"] = "L3"
            else:
                doc_info["validation_level"] = "Unknown"

            # Determine document format (PIVOT/FRIENDLY) from filename
            if "PIVOT" in file_path.name:
                doc_info["document_format"] = "PIVOT"
            elif "FRIENDLY" in file_path.name:
                doc_info["document_format"] = "FRIENDLY"
            else:
                doc_info["document_format"] = "Unknown"

            # Add file modification time
            doc_info["file_modified"] = datetime.fromtimestamp(
                file_path.stat().st_mtime
            )

            return doc_info

        except Exception as e:
            logger.error(f"Error parsing CDA document {file_path}: {e}")
            return None

    def _matches_oid(self, doc_info: Dict, target_oid: str) -> bool:
        """
        Check if document matches the target OID

        Args:
            doc_info: Document information dictionary
            target_oid: OID to match against

        Returns:
            True if document matches OID
        """
        # Check various OID fields
        oid_fields = ["document_root", "patient_id_root"]

        for field in oid_fields:
            if field in doc_info and target_oid in doc_info[field]:
                return True

        return False

    def get_available_countries(self) -> List[str]:
        """
        Get list of available countries in test data

        Returns:
            List of country codes
        """
        try:
            if not self.test_data_path.exists():
                return []

            countries = []
            for item in self.test_data_path.iterdir():
                if item.is_dir() and len(item.name) == 2:
                    countries.append(item.name)

            return sorted(countries)

        except Exception as e:
            logger.error(f"Error getting available countries: {e}")
            return []

    def render_patient_summary_with_guidelines(
        self, cda_file_path: str, target_language: str = "en"
    ) -> Dict:
        """
        Render Patient Summary document following PS Display Guidelines
        Uses existing clinical PDF service for rendering

        Args:
            cda_file_path: Path to CDA document
            target_language: Target language for translation

        Returns:
            Dictionary with rendered content and metadata
        """
        try:
            logger.info(
                f"Rendering Patient Summary with PS Display Guidelines: {cda_file_path}"
            )

            # Use existing clinical PDF service for rendering
            result = self.pdf_service.render_translated_document(
                cda_file_path,
                target_language=target_language,
                follow_ps_guidelines=True,
            )

            return result

        except Exception as e:
            logger.error(f"Error rendering Patient Summary: {e}", exc_info=True)
            return {"success": False, "error": str(e), "rendered_content": None}
