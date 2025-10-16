"""
SessionDataEnhancementService - Complete XML Resource Loading for Session Management

This service addresses the core issue where sessions store incomplete XML excerpts from
database instead of loading complete source XML files from project folders.

Key Features:
- Loads complete XML documents from source files in project folders
- Maintains session compatibility with existing PatientMatch structure
- Extracts ALL resources available in XML documents
- Supports enhanced CDA parsing with EnhancedCDAXMLParser integration
- Follows Django_NCP security and service layer patterns

Architecture Pattern:
- Service Layer: Business logic extracted from views (50-line limit compliance)
- Session Enhancement: Augments existing session data with complete XML resources
- Healthcare Domain: European CDA document processing for cross-border interoperability
- Security: Maintains audit trails and patient data privacy

Usage in Views:
```python
from patient_data.services.session_data_enhancement_service import SessionDataEnhancementService

enhancement_service = SessionDataEnhancementService()
enhanced_match_data = enhancement_service.enhance_session_with_complete_xml(
    match_data, patient_id, country_code
)
request.session[session_key] = enhanced_match_data
```
"""

import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from pathlib import Path
from django.conf import settings

from .enhanced_cda_xml_parser import EnhancedCDAXMLParser
from .cda_parser_service import CDAParserService
from .cda_document_index import get_cda_indexer

logger = logging.getLogger(__name__)


class SessionDataEnhancementService:
    """
    Enhanced session management service that loads complete XML resources
    
    Addresses the fundamental issue where sessions store incomplete XML excerpts
    from database instead of complete source documents from project folders.
    """

    def __init__(self):
        """Initialize enhancement service with XML parsers"""
        self.enhanced_parser = EnhancedCDAXMLParser()
        self.cda_parser = CDAParserService()
        self.cda_indexer = get_cda_indexer()
        
        # Define project XML document folders
        self.xml_folders = [
            "malta_test_documents",
            "irish_test_documents", 
            "test_documents",
            "cyprus_test_documents",
            "italian_test_documents",
            "test_data/eu_member_states/PT",
            "test_data/eu_member_states/MT", 
            "test_data/eu_member_states/IE",
            "test_data/eu_member_states/CY",
            "test_data/eu_member_states/IT"
        ]

    def enhance_session_with_complete_xml(
        self, 
        match_data: Dict[str, Any], 
        patient_id: str, 
        country_code: str
    ) -> Dict[str, Any]:
        """
        Enhance session data with complete XML resources from source files
        
        Args:
            match_data: Existing session match data (may contain incomplete XML)
            patient_id: Patient identifier for document lookup
            country_code: Country code for targeted document search
            
        Returns:
            Enhanced match data with complete XML resources and parsed clinical sections
        """
        try:
            logger.info(f"Enhancing session for patient {patient_id} from {country_code}")
            
            # Step 1: Find complete XML file for this patient
            complete_xml_content = self._load_complete_xml_file(patient_id, country_code)
            
            if not complete_xml_content:
                logger.warning(f"No complete XML file found for patient {patient_id}")
                return match_data
            
            # Step 2: Parse complete XML with enhanced parser
            parsed_resources = self._extract_all_xml_resources(complete_xml_content)
            
            # Step 3: Enhance match_data with complete resources
            enhanced_match_data = self._enhance_match_data(
                match_data, complete_xml_content, parsed_resources
            )
            
            logger.info(f"Successfully enhanced session with {len(parsed_resources)} clinical sections")
            return enhanced_match_data
            
        except Exception as e:
            logger.error(f"Error enhancing session data: {e}")
            # Return original match_data on error to maintain functionality
            return match_data

    def _load_complete_xml_file(self, patient_id: str, country_code: str) -> Optional[str]:
        """
        Load complete XML file from project folders based on patient ID and country
        
        Strategy:
        1. Use CDA indexer to find exact file path
        2. Fallback to country-specific folder search
        3. Fallback to general project folder search
        """
        try:
            # Strategy 1: Use CDA indexer for exact match
            patients = self.cda_indexer.get_all_patients()
            for patient in patients:
                if patient["patient_id"] == patient_id:
                    file_path = patient.get("file_path")
                    if file_path and os.path.exists(file_path):
                        return self._read_xml_file(file_path)
            
            # Strategy 2: Search country-specific folders
            country_folder_map = {
                "MT": "malta_test_documents",
                "IE": "irish_test_documents", 
                "CY": "cyprus_test_documents",
                "IT": "italian_test_documents"
            }
            
            target_folder = country_folder_map.get(country_code)
            if target_folder:
                xml_content = self._search_folder_for_patient(target_folder, patient_id)
                if xml_content:
                    return xml_content
            
            # Strategy 3: Search all XML folders
            for folder in self.xml_folders:
                xml_content = self._search_folder_for_patient(folder, patient_id)
                if xml_content:
                    return xml_content
                    
            return None
            
        except Exception as e:
            logger.error(f"Error loading complete XML file: {e}")
            return None

    def _search_folder_for_patient(self, folder_name: str, patient_id: str) -> Optional[str]:
        """Search specific folder for XML file containing patient ID"""
        try:
            folder_path = Path(settings.BASE_DIR) / folder_name
            if not folder_path.exists():
                return None
                
            # Search XML files in folder
            for xml_file in folder_path.glob("*.xml"):
                xml_content = self._read_xml_file(str(xml_file))
                if xml_content and patient_id in xml_content:
                    logger.info(f"Found matching XML file: {xml_file}")
                    return xml_content
                    
            return None
            
        except Exception as e:
            logger.error(f"Error searching folder {folder_name}: {e}")
            return None

    def _read_xml_file(self, file_path: str) -> Optional[str]:
        """Read XML file content with encoding handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='iso-8859-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading XML file {file_path}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error reading XML file {file_path}: {e}")
            return None

    def _extract_all_xml_resources(self, xml_content: str) -> Dict[str, Any]:
        """
        Extract ALL resources from complete XML using EnhancedCDAXMLParser
        
        Returns comprehensive clinical sections including:
        - Medications with complete pharmaceutical details
        - Allergies and adverse reactions
        - Problems and diagnoses  
        - Procedures and interventions
        - Laboratory results
        - Immunizations
        - Social history
        - All coded entries with SNOMED/LOINC/ICD codes
        """
        try:
            # Use enhanced parser to extract all clinical sections
            parsed_data = self.enhanced_parser.parse_cda_content(xml_content)
            
            # Administrative data is already included in parsed_data
            admin_data = parsed_data.get("administrative_data", {})
            
            # Combine all resources
            all_resources = {
                "clinical_sections": parsed_data.get("sections", {}),
                "administrative_data": admin_data,
                "medication_details": parsed_data.get("medications", []),
                "allergy_details": parsed_data.get("allergies", []),
                "problem_details": parsed_data.get("problems", []),
                "procedure_details": parsed_data.get("procedures", []),
                "immunization_details": parsed_data.get("immunizations", []),
                "coded_entries": parsed_data.get("coded_entries", []),
                "raw_sections": parsed_data.get("raw_sections", {}),
                "parsing_metadata": {
                    "parser_version": "enhanced_cda_xml_parser",
                    "total_sections": len(parsed_data.get("sections", {})),
                    "has_medications": len(parsed_data.get("medications", [])) > 0,
                    "has_allergies": len(parsed_data.get("allergies", [])) > 0,
                    "extraction_timestamp": self._get_current_timestamp()
                }
            }
            
            return all_resources
            
        except Exception as e:
            logger.error(f"Error extracting XML resources: {e}")
            return {}

    def _enhance_match_data(
        self, 
        original_match_data: Dict[str, Any], 
        complete_xml_content: str,
        parsed_resources: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance original match data with complete XML and parsed resources
        
        Maintains backward compatibility while adding enhanced resources
        """
        enhanced_data = original_match_data.copy()
        
        # Replace incomplete CDA content with complete XML
        enhanced_data["cda_content"] = complete_xml_content
        enhanced_data["complete_xml_content"] = complete_xml_content
        
        # Add all parsed clinical resources
        enhanced_data["parsed_resources"] = parsed_resources
        
        # Enhance clinical sections for easier template access
        enhanced_data["clinical_sections"] = parsed_resources.get("clinical_sections", {})
        enhanced_data["administrative_data"] = parsed_resources.get("administrative_data", {})
        
        # Add resource availability flags
        enhanced_data["has_complete_xml"] = True
        enhanced_data["has_enhanced_parsing"] = True
        enhanced_data["total_clinical_sections"] = len(parsed_resources.get("clinical_sections", {}))
        enhanced_data["medication_count"] = len(parsed_resources.get("medication_details", []))
        enhanced_data["allergy_count"] = len(parsed_resources.get("allergy_details", []))
        
        # Add enhancement metadata
        enhanced_data["enhancement_metadata"] = {
            "service": "SessionDataEnhancementService",
            "enhancement_timestamp": self._get_current_timestamp(),
            "original_cda_size": len(original_match_data.get("cda_content", "")),
            "complete_xml_size": len(complete_xml_content),
            "size_improvement_ratio": len(complete_xml_content) / max(1, len(original_match_data.get("cda_content", ""))),
            "parsing_success": len(parsed_resources) > 0
        }
        
        return enhanced_data

    def _get_current_timestamp(self) -> str:
        """Get current timestamp for metadata"""
        from django.utils import timezone
        return timezone.now().isoformat()

    def get_enhanced_session_summary(self, enhanced_match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary of enhanced session data for debugging and monitoring
        
        Useful for understanding what resources are available in the session
        """
        try:
            metadata = enhanced_match_data.get("enhancement_metadata", {})
            parsed_resources = enhanced_match_data.get("parsed_resources", {})
            
            summary = {
                "session_enhanced": enhanced_match_data.get("has_complete_xml", False),
                "enhancement_timestamp": metadata.get("enhancement_timestamp"),
                "xml_size_improvement": f"{metadata.get('size_improvement_ratio', 1):.2f}x",
                "clinical_sections": {
                    "total_sections": enhanced_match_data.get("total_clinical_sections", 0),
                    "available_sections": list(parsed_resources.get("clinical_sections", {}).keys()),
                    "medication_count": enhanced_match_data.get("medication_count", 0),
                    "allergy_count": enhanced_match_data.get("allergy_count", 0)
                },
                "parsing_details": parsed_resources.get("parsing_metadata", {}),
                "administrative_data_available": bool(parsed_resources.get("administrative_data")),
                "coded_entries_count": len(parsed_resources.get("coded_entries", []))
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating enhanced session summary: {e}")
            return {"error": str(e)}