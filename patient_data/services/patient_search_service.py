"""
EU Patient Search Services
Basic implementation for patient search and credential management
Enhanced with FHIR integration for unified search across CDA and FHIR sources
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging
import os
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

    # Multiple document support for user selection
    l1_documents: List[Dict[str, str]] = None  # List of {path, description, size}
    l3_documents: List[Dict[str, str]] = None  # List of {path, description, size}
    selected_l1_index: int = 0  # Index of currently selected L1 document
    selected_l3_index: int = 0  # Index of currently selected L3 document

    def __post_init__(self):
        if self.available_documents is None:
            self.available_documents = []
        if self.confidence_score == 1.0 and self.match_score != 1.0:
            self.confidence_score = self.match_score

        # Initialize document lists
        if self.l1_documents is None:
            self.l1_documents = []
        if self.l3_documents is None:
            self.l3_documents = []

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
        # If specific type is requested and available, use selected document
        if preferred_type == "L1" and self.l1_documents and len(self.l1_documents) > 0:
            content = self.get_selected_document_content("L1")
            if content:
                return content, "L1"
        elif (
            preferred_type == "L3" and self.l3_documents and len(self.l3_documents) > 0
        ):
            content = self.get_selected_document_content("L3")
            if content:
                return content, "L3"

        # Fallback to default logic (prefer L3, then L1) using selected documents
        if self.l3_documents and len(self.l3_documents) > 0:
            content = self.get_selected_document_content("L3")
            if content:
                return content, "L3"

        if self.l1_documents and len(self.l1_documents) > 0:
            content = self.get_selected_document_content("L1")
            if content:
                return content, "L1"

        # Legacy fallback to old content fields if document arrays are not available
        if preferred_type == "L1" and self.l1_cda_content:
            return self.l1_cda_content, "L1"
        elif preferred_type == "L3" and self.l3_cda_content:
            return self.l3_cda_content, "L3"

        # Final fallback to legacy content (prefer L3, then L1)
        if self.l3_cda_content:
            return self.l3_cda_content, "L3"
        elif self.l1_cda_content:
            return self.l1_cda_content, "L1"
        elif self.cda_content:
            # Legacy fallback for old session format - assume L3 if no type specified
            return self.cda_content, "L3"
        return None, "None"

    def get_orcd_cda(self) -> Optional[str]:
        """Get the CDA content for ORCD (PDF) extraction - prefer L1"""
        return self.l1_cda_content or self.l3_cda_content

    def get_available_document_types(self) -> List[str]:
        """Get list of available CDA document types for this patient"""
        types = []
        if self.l1_documents and len(self.l1_documents) > 0:
            types.append("L1")
        if self.l3_documents and len(self.l3_documents) > 0:
            types.append("L3")
        return types

    def get_document_list(self, cda_type: str) -> List[Dict[str, str]]:
        """Get list of available documents for a specific CDA type"""
        if cda_type == "L1":
            return self.l1_documents or []
        elif cda_type == "L3":
            return self.l3_documents or []
        return []

    def select_document(self, cda_type: str, document_index: int) -> bool:
        """Select a specific document by type and index"""
        if (
            cda_type == "L1"
            and self.l1_documents
            and 0 <= document_index < len(self.l1_documents)
        ):
            self.selected_l1_index = document_index
            return True
        elif (
            cda_type == "L3"
            and self.l3_documents
            and 0 <= document_index < len(self.l3_documents)
        ):
            self.selected_l3_index = document_index
            return True
        return False

    def get_selected_document_content(self, cda_type: str) -> Optional[str]:
        """Get content of the currently selected document for a CDA type"""
        try:
            if cda_type == "L1" and self.l1_documents:
                selected_doc = self.l1_documents[self.selected_l1_index]
                with open(selected_doc["path"], "r", encoding="utf-8") as f:
                    return f.read()
            elif cda_type == "L3" and self.l3_documents:
                selected_doc = self.l3_documents[self.selected_l3_index]
                with open(selected_doc["path"], "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error loading selected {cda_type} document: {e}")
        return None

    def get_document_summary(self) -> str:
        """Get a summary of available documents for UI display"""
        l1_count = len(self.l1_documents) if self.l1_documents else 0
        l3_count = len(self.l3_documents) if self.l3_documents else 0
        return f"L1: {l1_count} documents, L3: {l3_count} documents"

    def has_l1_cda(self) -> bool:
        """Check if L1 CDA content is available"""
        return bool(
            self.l1_cda_content or (self.l1_documents and len(self.l1_documents) > 0)
        )

    def has_l3_cda(self) -> bool:
        """Check if L3 CDA content is available"""
        return bool(
            self.l3_cda_content or (self.l3_documents and len(self.l3_documents) > 0)
        )


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

    def search_patient(self, credentials: PatientCredentials, use_local_cda: bool = True, use_hapi_fhir: bool = True) -> List[PatientMatch]:
        """
        Search for patient documents using NCP-to-NCP query with development options

        Args:
            credentials: Country code and patient identifier
            use_local_cda: Whether to search local CDA documents (default: True)
            use_hapi_fhir: Whether to search HAPI FHIR server (default: True)

        Returns:
            List of patient matches from selected sources
        """
        self.logger.info(
            f"NCP Query - Patient ID: {credentials.patient_id} from {credentials.country_code} "
            f"(CDA: {use_local_cda}, FHIR: {use_hapi_fhir})"
        )

        matches = []

        if credentials.patient_id:
            # Search CDA documents if enabled
            if use_local_cda:
                self.logger.info(f"Searching local CDA documents for patient {credentials.patient_id}")
                # Use the new CDA indexing system to find documents
                from .cda_document_index import get_cda_indexer

                indexer = get_cda_indexer()
                documents = indexer.find_patient_documents(
                    credentials.patient_id, credentials.country_code
                )

                # Initialize document lists
                l1_docs = []
                l3_docs = []

                if documents:
                    # Group documents by type (L1, L3)
                    l1_docs = [doc for doc in documents if doc.cda_type == "L1"]
                    l3_docs = [doc for doc in documents if doc.cda_type == "L3"]

                # Prepare document lists for user selection
                l1_document_list = []
                l3_document_list = []

                # Process all L1 documents
                for i, l1_doc in enumerate(l1_docs):
                    doc_info = {
                        "path": l1_doc.file_path,
                        "description": f"L1 Document {i+1} ({os.path.basename(l1_doc.file_path)})",
                        "size": str(l1_doc.file_size),
                        "last_modified": str(l1_doc.last_modified),
                    }
                    l1_document_list.append(doc_info)

                # Process all L3 documents
                for i, l3_doc in enumerate(l3_docs):
                    doc_info = {
                        "path": l3_doc.file_path,
                        "description": f"L3 Document {i+1} ({os.path.basename(l3_doc.file_path)})",
                        "size": str(l3_doc.file_size),
                        "last_modified": str(l3_doc.last_modified),
                    }
                    l3_document_list.append(doc_info)

                # Load default documents (first of each type) for backward compatibility
                l1_cda_content = None
                l3_cda_content = None
                l1_file_path = None
                l3_file_path = None

                # Load first L1 document if available
                if l1_docs:
                    l1_doc = l1_docs[0]
                    try:
                        with open(l1_doc.file_path, "r", encoding="utf-8") as f:
                            l1_cda_content = f.read()
                        l1_file_path = l1_doc.file_path
                        self.logger.info(
                            f"Loaded default L1 CDA from index: {l1_doc.file_path}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error loading L1 CDA {l1_doc.file_path}: {e}"
                        )

                # Load first L3 document if available
                if l3_docs:
                    l3_doc = l3_docs[0]
                    try:
                        with open(l3_doc.file_path, "r", encoding="utf-8") as f:
                            l3_cda_content = f.read()
                        l3_file_path = l3_doc.file_path
                        self.logger.info(
                            f"Loaded default L3 CDA from index: {l3_doc.file_path}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error loading L3 CDA {l3_doc.file_path}: {e}"
                        )

                # Use patient info from index (only if documents found)
                if documents:
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
                        l1_documents=l1_document_list,
                        l3_documents=l3_document_list,
                        patient_data={
                            "id": credentials.patient_id,
                            "name": f"{patient_info['given_name']} {patient_info['family_name']}",
                            "given_name": patient_info["given_name"],
                            "family_name": patient_info["family_name"],
                            "birth_date": patient_info["birth_date"],
                            "gender": patient_info["gender"],
                            "source": "CDA",  # Mark as CDA source
                        },
                        available_documents=["L1_CDA", "L3_CDA", "eDispensation", "ePS"],
                    )
                    matches.append(match)
                else:
                    if use_local_cda:  # Only log if CDA search was enabled
                        self.logger.info(f"No CDA documents found for patient {credentials.patient_id}")

            # Search FHIR if enabled (independent of CDA results)
            if use_hapi_fhir:
                self.logger.info(f"Searching FHIR server for patient documents for {credentials.patient_id}")
                
                try:
                    # Import FHIR services (uses factory to get correct service)
                    from eu_ncp_server.services.fhir_service_factory import get_fhir_service
                    from .fhir_bundle_parser import FHIRBundleParser
                    
                    # Get the configured FHIR service (HAPI or Azure)
                    fhir_service = get_fhir_service()
                    
                    # Search for patient documents (Compositions) - this is the key fix!
                    document_search_result = fhir_service.search_patient_documents(credentials.patient_id)
                    
                    # Extract documents from search results
                    fhir_documents = document_search_result.get('documents', [])
                    
                    if fhir_documents and len(fhir_documents) > 0:
                        self.logger.info(f"Found {len(fhir_documents)} FHIR patient documents for {credentials.patient_id}")
                        
                        # FIX: Process only the latest composition to prevent duplication
                        # Sort documents by date (newest first) and take only the first one
                        # This prevents processing duplicate/historical compositions
                        fhir_documents_sorted = sorted(
                            fhir_documents,
                            key=lambda doc: doc.get('date', ''),
                            reverse=True
                        )
                        latest_document = fhir_documents_sorted[0] if fhir_documents_sorted else None
                        
                        if latest_document:
                            self.logger.info(
                                f"Using latest composition (ID: {latest_document.get('id')}, "
                                f"Date: {latest_document.get('date')}) out of {len(fhir_documents)} found"
                            )
                        
                        # Also search for the actual patient resource
                        patient_search_result = fhir_service.search_patients({
                            'identifier': credentials.patient_id
                        })
                        fhir_patients = patient_search_result.get('patients', [])
                        
                        # Process only the latest document (not all documents)
                        if latest_document:
                            document_id = latest_document.get('id')
                            if document_id:
                                try:
                                    # Get Patient Summary Bundle using the composition
                                    ps_bundle = fhir_service.get_patient_summary(credentials.patient_id, "document_search")
                                    
                                    if ps_bundle:
                                        self.logger.info(f"Retrieved Patient Summary Bundle for document {document_id}")
                                        
                                        # ENHANCEMENT: Enrich bundle with Practitioner and Organization resources
                                        # FHIR IPS bundles often don't include these, but they're critical for healthcare team display
                                        self._enrich_bundle_with_healthcare_resources(ps_bundle, credentials.patient_id, fhir_service)
                                        
                                        # Parse FHIR Bundle using FHIRBundleParser
                                        bundle_parser = FHIRBundleParser()
                                        parsed_data = bundle_parser.parse_patient_summary_bundle(ps_bundle)
                                        
                                        if parsed_data and parsed_data.get('patient_identity'):
                                            patient_identity = parsed_data['patient_identity']
                                            
                                            # Create PatientMatch from FHIR data
                                            match = PatientMatch(
                                                patient_id=credentials.patient_id,
                                                given_name=patient_identity.get('given_name', 'Unknown'),
                                                family_name=patient_identity.get('family_name', 'Patient'),
                                                birth_date=patient_identity.get('birth_date', ''),
                                                gender=patient_identity.get('gender', ''),
                                                country_code=credentials.country_code,
                                                match_score=1.0,
                                                confidence_score=0.9,  # Slightly lower for FHIR since it's external
                                                # Store FHIR Bundle as JSON in patient_data
                                                patient_data={
                                                    "id": credentials.patient_id,
                                                    "name": f"{patient_identity.get('given_name', 'Unknown')} {patient_identity.get('family_name', 'Patient')}",
                                                    "given_name": patient_identity.get('given_name', 'Unknown'),
                                                    "family_name": patient_identity.get('family_name', 'Patient'),
                                                    "birth_date": patient_identity.get('birth_date', ''),
                                                    "gender": patient_identity.get('gender', ''),
                                                    "source": "FHIR",
                                                    "fhir_bundle": ps_bundle,  # Store original FHIR Bundle
                                                    "clinical_sections": parsed_data.get('sections', []),  # FIX: Use 'sections', not 'clinical_sections'
                                                    "clinical_arrays": parsed_data.get('clinical_arrays', {}),  # Also include clinical_arrays
                                                    "fhir_document_id": document_id
                                                },
                                                available_documents=["FHIR_Patient_Summary"],
                                                # No CDA content for FHIR patients
                                                l1_cda_content=None,
                                                l3_cda_content=None,
                                                l1_cda_path=None,
                                                l3_cda_path=None
                                            )
                                            
                                            matches.append(match)
                                            
                                            self.logger.info(f"Successfully created PatientMatch from FHIR data for {patient_identity.get('given_name')} {patient_identity.get('family_name')}")
                                            
                                except Exception as e:
                                    self.logger.error(f"Error processing FHIR document {document_id}: {e}")
                                    
                    # If FHIR search also found nothing, fall back to mock data                        
                    if not matches:
                        self.logger.warning(f"No results found in CDA or FHIR for patient {credentials.patient_id}, using fallback")
                        # Fallback to mock data continues below...
                        
                except Exception as e:
                    self.logger.error(f"Error during FHIR search: {e}")
                    # Continue without FHIR results if search fails
                
                # If no results found in either CDA or FHIR, return empty list
                if not matches:
                    self.logger.info(f"No patient found with ID {credentials.patient_id} in {credentials.country_code} from either CDA or FHIR sources")

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
        from datetime import date, timedelta

        recent_date = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        older_date = (date.today() - timedelta(days=10)).strftime("%Y-%m-%d")

        documents = [
            {
                "type": "CDA",
                "id": f"cda_{patient_id}",
                "title": "Clinical Document Architecture",
                "date": recent_date,
                "status": "available",
            },
            {
                "type": "ePS",
                "id": f"eps_{patient_id}",
                "title": "Electronic Prescription",
                "date": older_date,
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
        from datetime import date

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
                "date": date.today().strftime("%Y-%m-%d"),  # Use current date
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
            "last_updated": date.today().strftime("%Y-%m-%d"),  # Use current date
        }

        return summary
    
    def _enrich_bundle_with_healthcare_resources(self, bundle: Dict[str, Any], patient_id: str, hapi_service) -> None:
        """
        Enrich FHIR bundle with Practitioner and Organization resources from HAPI server
        
        FHIR IPS bundles often don't include Practitioner/Organization resources even though
        they're referenced in Composition.author and Composition.custodian. This method:
        1. Finds the Composition in the bundle
        2. Extracts author and custodian references
        3. Fetches only those specific resources by ID from HAPI
        4. Adds them to the bundle
        
        Args:
            bundle: FHIR Bundle to enrich (modified in place)
            patient_id: Patient identifier for logging
            hapi_service: HAPI FHIR service instance
        """
        try:
            added_count = 0
            
            # Find ALL Composition resources in bundle to get author/custodian references
            compositions = []
            for entry in bundle.get('entry', []):
                resource = entry.get('resource', {})
                if resource.get('resourceType') == 'Composition':
                    compositions.append(resource)
            
            if not compositions:
                self.logger.warning(f"No Composition found in bundle for patient {patient_id}, cannot enrich healthcare resources")
                return
            
            self.logger.info(f"Found {len(compositions)} Composition(s) to analyze for healthcare resource references")
            
            # Extract referenced Practitioner and Organization IDs from ALL Compositions
            # Note: author can be EITHER Practitioner OR Organization
            practitioner_ids = set()  # Use set to avoid duplicates
            organization_ids = set()
            
            for composition in compositions:
                # Extract from Composition.author
                for author in composition.get('author', []):
                    ref = author.get('reference', '')
                    
                    # Handle Practitioner references
                    if ref.startswith('Practitioner/'):
                        pract_id = ref.split('/')[-1]
                        practitioner_ids.add(pract_id)
                    elif ref.startswith('urn:uuid:') and 'practitioner' in ref.lower():
                        uuid = ref.replace('urn:uuid:', '')
                        practitioner_ids.add(uuid)
                    
                    # Handle Organization references in author (yes, authors can be organizations!)
                    elif ref.startswith('Organization/'):
                        org_id = ref.split('/')[-1]
                        organization_ids.add(org_id)
                    elif ref.startswith('urn:uuid:') and 'organization' in ref.lower():
                        uuid = ref.replace('urn:uuid:', '')
                        organization_ids.add(uuid)
                    
                    # Handle bare UUIDs (try as Practitioner first, fallback to Organization)
                    elif ref.startswith('urn:uuid:'):
                        uuid = ref.replace('urn:uuid:', '')
                        # We'll try fetching as Practitioner, if that fails the warning will be logged
                        practitioner_ids.add(uuid)
                
                # Extract referenced Organization ID from Composition.custodian (in addition to author orgs)
                custodian = composition.get('custodian', {})
                if custodian:
                    ref = custodian.get('reference', '')
                    if ref.startswith('Organization/'):
                        org_id = ref.split('/')[-1]
                        organization_ids.add(org_id)
                    elif ref.startswith('urn:uuid:'):
                        uuid = ref.replace('urn:uuid:', '')
                        organization_ids.add(uuid)
            
            self.logger.info(f"Extracted {len(practitioner_ids)} Practitioner reference(s) and {len(organization_ids)} Organization reference(s) from Compositions")
            
            # Fetch specific Practitioner resources by ID
            for pract_id in practitioner_ids:
                try:
                    practitioner = hapi_service.get_resource_by_id('Practitioner', pract_id)
                    if practitioner:
                        bundle.setdefault('entry', []).append({
                            'fullUrl': f"urn:uuid:{pract_id}",
                            'resource': practitioner
                        })
                        added_count += 1
                        self.logger.info(f"Added referenced Practitioner {pract_id} to bundle")
                except Exception as e:
                    self.logger.warning(f"Could not fetch Practitioner {pract_id}: {str(e)}")
            
            # Fetch specific Organization resources by ID
            for org_id in organization_ids:
                try:
                    organization = hapi_service.get_resource_by_id('Organization', org_id)
                    if organization:
                        bundle.setdefault('entry', []).append({
                            'fullUrl': f"urn:uuid:{org_id}",
                            'resource': organization
                        })
                        added_count += 1
                        self.logger.info(f"Added referenced Organization {org_id} to bundle")
                except Exception as e:
                    self.logger.warning(f"Could not fetch Organization {org_id}: {str(e)}")
            
            if added_count > 0:
                self.logger.info(f"Enriched FHIR bundle with {added_count} specific healthcare resources referenced in Composition")
            else:
                self.logger.warning(f"No specific Practitioner or Organization resources could be fetched from HAPI for patient {patient_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to enrich bundle with healthcare resources: {str(e)}")
            # Don't raise - enrichment is optional, continue with original bundle
