"""
Patient Demographics Service

Django NCP Healthcare Portal - Unified Patient Demographic Processing
Generated: December 19, 2024
Purpose: Consolidate patient data extraction from CDA, FHIR, and session sources
"""

from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
import logging
from datetime import datetime

from ..models.patient_demographics import PatientDemographics, PatientIdentifier


logger = logging.getLogger(__name__)


class PatientDemographicsService:
    """
    Unified service for patient demographic processing across data sources
    
    Consolidates the scattered patient extraction logic from:
    - EnhancedCDAXMLParser._extract_patient_info()
    - FHIR bundle processing
    - Session data conversion
    
    Into a single, testable, maintainable service.
    """
    
    def __init__(self):
        """Initialize service with European healthcare standards"""
        # CDA XML namespace mappings for patient data extraction
        self.cda_namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # European gender code mappings
        self.gender_mappings = {
            'F': 'Female',
            'M': 'Male',
            'UN': 'Unknown',
            'f': 'Female',
            'm': 'Male',
            'female': 'Female',
            'male': 'Male',
            'feminino': 'Female',  # Portuguese
            'masculino': 'Male',   # Portuguese
            'féminin': 'Female',   # French
            'masculin': 'Male',    # French
        }
    
    def extract_from_cda_xml(self, xml_root: ET.Element) -> PatientDemographics:
        """
        Extract patient demographics from CDA XML document
        
        Consolidates the logic from EnhancedCDAXMLParser._extract_patient_info()
        into a dedicated, testable method.
        
        Args:
            xml_root: Root element of CDA XML document
            
        Returns:
            PatientDemographics: Populated patient demographics object
        """
        try:
            # Find patient role element in CDA structure
            patient_role = xml_root.find('.//hl7:patientRole', self.cda_namespaces)
            if patient_role is None:
                logger.warning("No patientRole element found in CDA XML")
                return self._create_empty_demographics()
            
            # Extract patient identifiers
            identifiers = self._extract_cda_identifiers(patient_role)
            
            # Find patient element for demographic data
            patient_element = patient_role.find('hl7:patient', self.cda_namespaces)
            if patient_element is None:
                logger.warning("No patient element found in CDA XML")
                return PatientDemographics(identifiers=identifiers)
            
            # Extract names
            given_name, family_name = self._extract_cda_names(patient_element)
            
            # Extract birth date
            birth_date = self._extract_cda_birth_date(patient_element)
            
            # Extract gender
            gender = self._extract_cda_gender(patient_element)
            
            # Extract patient ID (use first identifier extension as patient_id)
            patient_id = identifiers[0].extension if identifiers else ""
            
            # Create unified demographics object
            demographics = PatientDemographics(
                given_name=given_name,
                family_name=family_name,
                birth_date=birth_date,
                gender=gender,
                patient_id=patient_id,
                identifiers=identifiers
            )
            
            logger.info(f"Extracted patient demographics: {demographics.get_display_name()}")
            return demographics
            
        except Exception as e:
            logger.error(f"Error extracting patient demographics from CDA XML: {e}")
            return self._create_empty_demographics()
    
    def extract_from_fhir_bundle(self, fhir_bundle: Dict[str, Any]) -> PatientDemographics:
        """
        Extract patient demographics from FHIR bundle
        
        Standardized extraction for FHIR R4 patient resources with
        European healthcare identifier support.
        
        Args:
            fhir_bundle: FHIR bundle dictionary containing patient resource
            
        Returns:
            PatientDemographics: Populated patient demographics object
        """
        try:
            # Find Patient resource in FHIR bundle
            patient_resource = None
            if 'entry' in fhir_bundle:
                for entry in fhir_bundle['entry']:
                    if entry.get('resource', {}).get('resourceType') == 'Patient':
                        patient_resource = entry['resource']
                        break
            
            if not patient_resource:
                logger.warning("No Patient resource found in FHIR bundle")
                return self._create_empty_demographics()
            
            # Extract identifiers
            identifiers = self._extract_fhir_identifiers(patient_resource)
            
            # Extract names
            given_name, family_name = self._extract_fhir_names(patient_resource)
            
            # Extract birth date
            birth_date = patient_resource.get('birthDate', '')
            
            # Extract gender
            gender = self._normalize_gender(patient_resource.get('gender', 'unknown'))
            
            # Extract patient ID
            patient_id = patient_resource.get('id', '')
            
            # Create unified demographics object
            demographics = PatientDemographics(
                given_name=given_name,
                family_name=family_name,
                birth_date=birth_date,
                gender=gender,
                patient_id=patient_id,
                identifiers=identifiers
            )
            
            logger.info(f"Extracted FHIR patient demographics: {demographics.get_display_name()}")
            return demographics
            
        except Exception as e:
            logger.error(f"Error extracting patient demographics from FHIR bundle: {e}")
            return self._create_empty_demographics()
    
    def extract_from_session_data(self, session_data: Dict[str, Any]) -> PatientDemographics:
        """
        Convert existing session data format to unified PatientDemographics
        
        Handles the existing session data structure used by Diana Ferreira
        and other patients in the system.
        
        Args:
            session_data: Dictionary containing patient data from Django session
            
        Returns:
            PatientDemographics: Converted demographics object
        """
        try:
            # Use the built-in class method for session data conversion
            demographics = PatientDemographics.from_session_data(session_data)
            
            logger.info(f"Converted session data for patient: {demographics.get_display_name()}")
            return demographics
            
        except Exception as e:
            logger.error(f"Error converting session data to patient demographics: {e}")
            return self._create_empty_demographics()
    
    def create_unified_template_context(self, demographics: PatientDemographics) -> Dict[str, Any]:
        """
        Create unified template context with backward compatibility
        
        Provides both new unified structure and legacy aliases for
        smooth transition of existing templates.
        
        Args:
            demographics: PatientDemographics object
            
        Returns:
            Dict: Complete template context with unified and legacy formats
        """
        # Create the new unified structure
        unified_context = {
            'patient': demographics.to_template_context()
        }
        
        # Add backward compatibility aliases
        legacy_data = demographics.to_legacy_context()
        unified_context.update({
            'patient_data': legacy_data,
            'patient_information': legacy_data,
            'patient_identity': legacy_data,
            'patient_display_name': demographics.get_display_name()
        })
        
        return unified_context
    
    def create_template_context(self, demographics: PatientDemographics, 
                              include_legacy: bool = True) -> Dict[str, Any]:
        """
        Create template context for patient demographics
        
        Args:
            demographics: PatientDemographics object
            include_legacy: Whether to include backward compatibility aliases
            
        Returns:
            Dict: Template context dictionary
        """
        if include_legacy:
            return self.create_unified_template_context(demographics)
        else:
            return {'patient': demographics.to_template_context()}
    
    # Private helper methods for CDA extraction
    
    def _extract_cda_identifiers(self, patient_role: ET.Element) -> List[PatientIdentifier]:
        """Extract patient identifiers from CDA patientRole element"""
        identifiers = []
        
        # Find all id elements in patientRole
        for id_element in patient_role.findall('hl7:id', self.cda_namespaces):
            extension = id_element.get('extension', '')
            root = id_element.get('root', '')
            assigning_authority = id_element.get('assigningAuthorityName', '')
            
            if extension:  # Only add if extension exists
                identifier = PatientIdentifier(
                    extension=extension,
                    root=root,
                    assigning_authority_name=assigning_authority,
                    identifier_type='primary' if not identifiers else 'secondary'
                )
                identifiers.append(identifier)
        
        return identifiers
    
    def _extract_cda_names(self, patient_element: ET.Element) -> tuple[str, str]:
        """Extract given name and family name from CDA patient element"""
        given_name = "Unknown"
        family_name = "Unknown"
        
        # Find name element
        name_element = patient_element.find('hl7:name', self.cda_namespaces)
        if name_element is not None:
            # Extract given name
            given_elem = name_element.find('hl7:given', self.cda_namespaces)
            if given_elem is not None and given_elem.text:
                given_name = given_elem.text.strip()
            
            # Extract family name
            family_elem = name_element.find('hl7:family', self.cda_namespaces)
            if family_elem is not None and family_elem.text:
                family_name = family_elem.text.strip()
        
        return given_name, family_name
    
    def _extract_cda_birth_date(self, patient_element: ET.Element) -> str:
        """Extract birth date from CDA patient element"""
        birth_time_elem = patient_element.find('hl7:birthTime', self.cda_namespaces)
        if birth_time_elem is not None:
            return birth_time_elem.get('value', '')
        return ''
    
    def _extract_cda_gender(self, patient_element: ET.Element) -> str:
        """Extract gender from CDA patient element"""
        gender_elem = patient_element.find('hl7:administrativeGenderCode', self.cda_namespaces)
        if gender_elem is not None:
            gender_code = gender_elem.get('code', 'UN')
            return self._normalize_gender(gender_code)
        return 'Unknown'
    
    # Private helper methods for FHIR extraction
    
    def _extract_fhir_identifiers(self, patient_resource: Dict[str, Any]) -> List[PatientIdentifier]:
        """Extract patient identifiers from FHIR Patient resource"""
        identifiers = []
        
        for id_data in patient_resource.get('identifier', []):
            extension = id_data.get('value', '')
            system = id_data.get('system', '')
            assigning_org = id_data.get('assigner', {}).get('display', '')
            
            if extension:
                identifier = PatientIdentifier(
                    extension=extension,
                    root=system,
                    assigning_authority_name=assigning_org,
                    identifier_type='primary' if not identifiers else 'secondary'
                )
                identifiers.append(identifier)
        
        return identifiers
    
    def _extract_fhir_names(self, patient_resource: Dict[str, Any]) -> tuple[str, str]:
        """Extract given name and family name from FHIR Patient resource"""
        given_name = "Unknown"
        family_name = "Unknown"
        
        names = patient_resource.get('name', [])
        if names:
            # Use first name entry
            name_data = names[0]
            
            # Extract given names
            given_names = name_data.get('given', [])
            if given_names:
                given_name = ' '.join(given_names)
            
            # Extract family name
            if 'family' in name_data:
                family_name = name_data['family']
        
        return given_name, family_name
    
    # Private utility methods
    
    def _normalize_gender(self, gender_value: str) -> str:
        """Normalize gender value using European healthcare standards"""
        if not gender_value:
            return 'Unknown'
            
        # Check direct mappings first
        if gender_value in self.gender_mappings:
            return self.gender_mappings[gender_value]
        
        # Check case-insensitive mappings
        gender_lower = gender_value.lower()
        for key, value in self.gender_mappings.items():
            if key.lower() == gender_lower:
                return value
        
        # Return title case if no mapping found
        return gender_value.title()
    
    def _create_empty_demographics(self) -> PatientDemographics:
        """Create empty demographics object with default values"""
        return PatientDemographics(
            given_name="Unknown",
            family_name="Unknown",
            birth_date="",
            gender="Unknown",
            patient_id="",
            identifiers=[]
        )
    
    # Validation and quality assurance methods
    
    def validate_demographics(self, demographics: PatientDemographics) -> Dict[str, List[str]]:
        """
        Validate patient demographics for completeness and consistency
        
        Args:
            demographics: PatientDemographics object to validate
            
        Returns:
            Dict: Validation results with warnings and errors
        """
        warnings = []
        errors = []
        
        # Check required fields
        if demographics.given_name == "Unknown":
            warnings.append("Given name is unknown")
        
        if demographics.family_name == "Unknown":
            warnings.append("Family name is unknown")
        
        if not demographics.birth_date:
            warnings.append("Birth date is missing")
        
        if demographics.gender == "Unknown":
            warnings.append("Gender is unknown")
        
        if not demographics.identifiers:
            errors.append("No patient identifiers found")
        
        # Validate identifiers
        for i, identifier in enumerate(demographics.identifiers):
            if not identifier.extension:
                errors.append(f"Identifier {i+1}: Extension is empty")
        
        # Validate birth date format
        if demographics.birth_date and not self._is_valid_birth_date_format(demographics.birth_date):
            warnings.append(f"Birth date format may be invalid: {demographics.birth_date}")
        
        return {
            'warnings': warnings,
            'errors': errors,
            'is_valid': len(errors) == 0
        }
    
    def _is_valid_birth_date_format(self, birth_date: str) -> bool:
        """Check if birth date is in a recognized format"""
        formats = [
            '%Y%m%d',      # CDA format: 19820508
            '%Y-%m-%d',    # ISO format: 1982-05-08
            '%d/%m/%Y',    # Display format: 08/05/1982
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(birth_date, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def get_extraction_statistics(self) -> Dict[str, int]:
        """
        Get statistics about demographic extractions
        
        Returns:
            Dict: Statistics about extraction operations
        """
        # This would typically be implemented with actual metrics collection
        # For now, return placeholder structure
        return {
            'cda_extractions': 0,
            'fhir_extractions': 0,
            'session_conversions': 0,
            'extraction_errors': 0,
            'validation_warnings': 0
        }