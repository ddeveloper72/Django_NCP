"""
Complete Clinical Section Services

All specialized service agents for clinical data processing implementing the unified pipeline.
Each service follows the ClinicalSectionServiceInterface for consistent integration.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from .clinical_data_pipeline_manager import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class ProblemsSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for problems/conditions section data processing.
    
    Handles:
    - Problem lists and medical conditions
    - History of past illness  
    - Problem status and severity
    - Clinical findings
    """
    
    def get_section_code(self) -> str:
        return "11450-4"
    
    def get_section_name(self) -> str:
        return "Problems"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract problems from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced problems data
        enhanced_problems = match_data.get('enhanced_problems', [])
        
        if enhanced_problems:
            logger.info(f"[PROBLEMS SERVICE] Found {len(enhanced_problems)} enhanced problems in session")
            return enhanced_problems
        
        # Check for clinical arrays problems
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        problems_data = clinical_arrays.get('problems', [])
        
        if problems_data:
            logger.info(f"[PROBLEMS SERVICE] Found {len(problems_data)} problems in clinical arrays")
            return problems_data
        
        logger.info("[PROBLEMS SERVICE] No problems data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract problems from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find problems section
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') in ['11450-4', '11348-0']:
                    # Parse problems section
                    problems = self._parse_problems_xml(section)
                    logger.info(f"[PROBLEMS SERVICE] Extracted {len(problems)} problems from CDA")
                    return problems
            
            logger.info("[PROBLEMS SERVICE] No problems section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[PROBLEMS SERVICE] Error extracting problems from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance problems data and store in session."""
        enhanced_problems = []
        
        for problem_data in raw_data:
            enhanced_problem = {
                'name': self._extract_field_value(problem_data, 'name', 'Unknown problem'),
                'display_name': self._extract_field_value(problem_data, 'name', 'Unknown problem'),
                'type': self._extract_field_value(problem_data, 'type', 'Clinical finding'),
                'status': self._extract_field_value(problem_data, 'status', 'Active'),
                'severity': self._extract_field_value(problem_data, 'severity', 'Not specified'),
                'time_period': self._extract_field_value(problem_data, 'time', 'Not specified'),
                'code': self._extract_field_value(problem_data, 'code', ''),
                'code_system': self._extract_field_value(problem_data, 'code_system', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_problems.append(enhanced_problem)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_problems'] = enhanced_problems
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[PROBLEMS SERVICE] Enhanced and stored {len(enhanced_problems)} problems")
        return enhanced_problems
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced problems to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Problems',
                'section_code': '11450-4',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # problem.field_name
            }
        }
    
    def _parse_problems_xml(self, section) -> List[Dict[str, Any]]:
        """Parse problems section XML into structured data."""
        problems = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Strategy 1: Extract from structured entries
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                problem = self._parse_problem_observation(observation)
                if problem:
                    problems.append(problem)
        
        # Strategy 2: Extract from narrative text
        if not problems:
            text_section = section.find('.//hl7:text', namespaces)
            if text_section is not None:
                paragraphs = text_section.findall('.//hl7:paragraph', namespaces)
                for paragraph in paragraphs:
                    text = self._extract_text_from_element(paragraph)
                    if text and text.strip():
                        problem = self._parse_problem_narrative(text)
                        if problem:
                            problems.append(problem)
        
        return problems
    
    def _parse_problem_observation(self, observation) -> Dict[str, Any]:
        """Parse problem information from structured observation element."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract problem name from value element
        value_elem = observation.find('hl7:value', namespaces)
        problem_name = "Unknown problem"
        code = ""
        code_system = ""
        
        if value_elem is not None:
            problem_name = value_elem.get('displayName', value_elem.get('code', 'Unknown problem'))
            code = value_elem.get('code', '')
            code_system = value_elem.get('codeSystem', '')
        
        # Extract status and severity
        status = "Active"
        severity = "Not specified"
        
        # Look for status observation
        status_obs = observation.find('.//hl7:observation[hl7:code/@code="33999-4"]', namespaces)
        if status_obs is not None:
            status_value = status_obs.find('hl7:value', namespaces)
            if status_value is not None:
                status = status_value.get('displayName', status_value.get('code', 'Active'))
        
        return {
            'name': problem_name,
            'type': 'Clinical finding',
            'status': status,
            'severity': severity,
            'time': 'Not specified',
            'code': code,
            'code_system': code_system
        }
    
    def _parse_problem_narrative(self, text: str) -> Dict[str, Any]:
        """Parse problem information from narrative text."""
        # Extract timing information if present
        time_info = "Not specified"
        if ' since ' in text:
            parts = text.split(' since ')
            problem_name = parts[0].strip()
            time_info = f"since {parts[1].strip()}"
        else:
            problem_name = text.strip()
        
        # Determine severity
        severity = "Not specified"
        if 'severe' in text.lower():
            severity = "Severe"
        elif 'moderate' in text.lower():
            severity = "Moderate"
        elif 'mild' in text.lower():
            severity = "Mild"
        
        return {
            'name': problem_name,
            'type': 'Clinical finding',
            'status': 'Active',
            'severity': severity,
            'time': time_info,
            'code': '',
            'code_system': ''
        }
    
    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from XML element."""
        if element is None:
            return ""
        
        text = element.text
        if text and text.strip():
            return text.strip()
        
        all_text = ''.join(element.itertext()).strip()
        return all_text if all_text else ""
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


class VitalSignsSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for vital signs and physical findings section data processing.
    
    Handles:
    - Vital signs measurements
    - Physical examination findings
    - Laboratory values
    - Clinical observations
    """
    
    def get_section_code(self) -> str:
        return "8716-3"
    
    def get_section_name(self) -> str:
        return "Vital Signs"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract vital signs from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_vitals = match_data.get('enhanced_vital_signs', [])
        
        if enhanced_vitals:
            logger.info(f"[VITAL SIGNS SERVICE] Found {len(enhanced_vitals)} enhanced vital signs in session")
            return enhanced_vitals
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        vitals_data = clinical_arrays.get('vital_signs', [])
        
        if vitals_data:
            logger.info(f"[VITAL SIGNS SERVICE] Found {len(vitals_data)} vital signs in clinical arrays")
            return vitals_data
        
        logger.info("[VITAL SIGNS SERVICE] No vital signs data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract vital signs from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') in ['8716-3', '29545-1']:
                    vitals = self._parse_vitals_xml(section)
                    logger.info(f"[VITAL SIGNS SERVICE] Extracted {len(vitals)} vital signs from CDA")
                    return vitals
            
            logger.info("[VITAL SIGNS SERVICE] No vital signs section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[VITAL SIGNS SERVICE] Error extracting vital signs from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance vital signs data and store in session."""
        enhanced_vitals = []
        
        for vital_data in raw_data:
            enhanced_vital = {
                'name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'display_name': self._extract_field_value(vital_data, 'name', 'Unknown measurement'),
                'value': self._extract_field_value(vital_data, 'value', 'Not specified'),
                'unit': self._extract_field_value(vital_data, 'unit', ''),
                'date': self._extract_field_value(vital_data, 'date', 'Not specified'),
                'status': self._extract_field_value(vital_data, 'status', 'Final'),
                'reference_range': self._extract_field_value(vital_data, 'reference_range', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_vitals.append(enhanced_vital)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_vital_signs'] = enhanced_vitals
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[VITAL SIGNS SERVICE] Enhanced and stored {len(enhanced_vitals)} vital signs")
        return enhanced_vitals
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced vital signs to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Vital Signs',
                'section_code': '8716-3',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # vital.field_name
            }
        }
    
    def _parse_vitals_xml(self, section) -> List[Dict[str, Any]]:
        """Parse vital signs section XML into structured data."""
        vitals = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                vital = self._parse_vital_observation(observation)
                if vital:
                    vitals.append(vital)
        
        return vitals
    
    def _parse_vital_observation(self, observation) -> Dict[str, Any]:
        """Parse vital sign observation into structured data."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract measurement name
        code_elem = observation.find('hl7:code', namespaces)
        name = "Unknown measurement"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown measurement'))
        
        # Extract value and unit
        value_elem = observation.find('hl7:value', namespaces)
        value = "Not specified"
        unit = ""
        if value_elem is not None:
            value = value_elem.get('value', 'Not specified')
            unit = value_elem.get('unit', '')
        
        # Extract date
        time_elem = observation.find('hl7:effectiveTime', namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        return {
            'name': name,
            'value': value,
            'unit': unit,
            'date': date,
            'status': 'Final',
            'reference_range': ''
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


class ProceduresSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for procedures section data processing.
    
    Handles:
    - Surgical procedures
    - Medical procedures  
    - Diagnostic procedures
    - Interventions
    """
    
    def get_section_code(self) -> str:
        return "47519-4"
    
    def get_section_name(self) -> str:
        return "Procedures"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract procedures from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_procedures = match_data.get('enhanced_procedures', [])
        
        if enhanced_procedures:
            logger.info(f"[PROCEDURES SERVICE] Found {len(enhanced_procedures)} enhanced procedures in session")
            return enhanced_procedures
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        procedures_data = clinical_arrays.get('procedures', [])
        
        if procedures_data:
            logger.info(f"[PROCEDURES SERVICE] Found {len(procedures_data)} procedures in clinical arrays")
            return procedures_data
        
        logger.info("[PROCEDURES SERVICE] No procedures data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract procedures from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '47519-4':
                    procedures = self._parse_procedures_xml(section)
                    logger.info(f"[PROCEDURES SERVICE] Extracted {len(procedures)} procedures from CDA")
                    return procedures
            
            logger.info("[PROCEDURES SERVICE] No procedures section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[PROCEDURES SERVICE] Error extracting procedures from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance procedures data and store in session."""
        enhanced_procedures = []
        
        for procedure_data in raw_data:
            enhanced_procedure = {
                'name': self._extract_field_value(procedure_data, 'name', 'Unknown procedure'),
                'display_name': self._extract_field_value(procedure_data, 'name', 'Unknown procedure'),
                'date': self._extract_field_value(procedure_data, 'date', 'Not specified'),
                'provider': self._extract_field_value(procedure_data, 'provider', 'Not specified'),
                'location': self._extract_field_value(procedure_data, 'location', 'Not specified'),
                'status': self._extract_field_value(procedure_data, 'status', 'Completed'),
                'indication': self._extract_field_value(procedure_data, 'indication', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_procedures.append(enhanced_procedure)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_procedures'] = enhanced_procedures
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[PROCEDURES SERVICE] Enhanced and stored {len(enhanced_procedures)} procedures")
        return enhanced_procedures
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced procedures to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Procedures',
                'section_code': '47519-4',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # procedure.field_name
            }
        }
    
    def _parse_procedures_xml(self, section) -> List[Dict[str, Any]]:
        """Parse procedures section XML into structured data."""
        procedures = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            procedure_elem = entry.find('.//hl7:procedure', namespaces)
            if procedure_elem is not None:
                procedure = self._parse_procedure_element(procedure_elem)
                if procedure:
                    procedures.append(procedure)
        
        return procedures
    
    def _parse_procedure_element(self, procedure_elem) -> Dict[str, Any]:
        """Parse procedure element into structured data."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract procedure name
        code_elem = procedure_elem.find('hl7:code', namespaces)
        name = "Unknown procedure"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown procedure'))
        
        # Extract date
        time_elem = procedure_elem.find('hl7:effectiveTime', namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = procedure_elem.find('hl7:statusCode', namespaces)
        status = "Completed"
        if status_elem is not None:
            status = status_elem.get('code', 'Completed')
        
        return {
            'name': name,
            'date': date,
            'provider': 'Not specified',
            'location': 'Not specified',
            'status': status,
            'indication': 'Not specified'
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


class ImmunizationsSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for immunizations section data processing.
    
    Handles:
    - Vaccination records
    - Immunization history
    - Vaccine details
    - Administration information
    """
    
    def get_section_code(self) -> str:
        return "11369-6"
    
    def get_section_name(self) -> str:
        return "Immunizations"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract immunizations from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_immunizations = match_data.get('enhanced_immunizations', [])
        
        if enhanced_immunizations:
            logger.info(f"[IMMUNIZATIONS SERVICE] Found {len(enhanced_immunizations)} enhanced immunizations in session")
            return enhanced_immunizations
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        immunizations_data = clinical_arrays.get('immunizations', [])
        
        if immunizations_data:
            logger.info(f"[IMMUNIZATIONS SERVICE] Found {len(immunizations_data)} immunizations in clinical arrays")
            return immunizations_data
        
        logger.info("[IMMUNIZATIONS SERVICE] No immunizations data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract immunizations from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '11369-6':
                    immunizations = self._parse_immunizations_xml(section)
                    logger.info(f"[IMMUNIZATIONS SERVICE] Extracted {len(immunizations)} immunizations from CDA")
                    return immunizations
            
            logger.info("[IMMUNIZATIONS SERVICE] No immunizations section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[IMMUNIZATIONS SERVICE] Error extracting immunizations from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance immunizations data and store in session."""
        enhanced_immunizations = []
        
        for immunization_data in raw_data:
            enhanced_immunization = {
                'name': self._extract_field_value(immunization_data, 'name', 'Unknown vaccine'),
                'display_name': self._extract_field_value(immunization_data, 'name', 'Unknown vaccine'),
                'date_administered': self._extract_field_value(immunization_data, 'date_administered', 'Not specified'),
                'dose_number': self._extract_field_value(immunization_data, 'dose_number', 'Not specified'),
                'manufacturer': self._extract_field_value(immunization_data, 'manufacturer', 'Not specified'),
                'lot_number': self._extract_field_value(immunization_data, 'lot_number', 'Not specified'),
                'route': self._extract_field_value(immunization_data, 'route', 'Not specified'),
                'site': self._extract_field_value(immunization_data, 'site', 'Not specified'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_immunizations.append(enhanced_immunization)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_immunizations'] = enhanced_immunizations
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[IMMUNIZATIONS SERVICE] Enhanced and stored {len(enhanced_immunizations)} immunizations")
        return enhanced_immunizations
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced immunizations to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Immunizations',
                'section_code': '11369-6',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # immunization.field_name
            }
        }
    
    def _parse_immunizations_xml(self, section) -> List[Dict[str, Any]]:
        """Parse immunizations section XML into structured data."""
        immunizations = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            substance_admin = entry.find('.//hl7:substanceAdministration', namespaces)
            if substance_admin is not None:
                immunization = self._parse_immunization_element(substance_admin)
                if immunization:
                    immunizations.append(immunization)
        
        return immunizations
    
    def _parse_immunization_element(self, substance_admin) -> Dict[str, Any]:
        """Parse immunization element into structured data."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract vaccine name
        consumable = substance_admin.find('.//hl7:consumable', namespaces)
        name = "Unknown vaccine"
        if consumable is not None:
            material = consumable.find('.//hl7:manufacturedMaterial', namespaces)
            if material is not None:
                code_elem = material.find('hl7:code', namespaces)
                if code_elem is not None:
                    name = code_elem.get('displayName', code_elem.get('code', 'Unknown vaccine'))
        
        # Extract date
        time_elem = substance_admin.find('hl7:effectiveTime', namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract route
        route_elem = substance_admin.find('.//hl7:routeCode', namespaces)
        route = "Not specified"
        if route_elem is not None:
            route = route_elem.get('displayName', route_elem.get('code', 'Not specified'))
        
        return {
            'name': name,
            'date_administered': date,
            'dose_number': 'Not specified',
            'manufacturer': 'Not specified',
            'lot_number': 'Not specified',
            'route': route,
            'site': 'Not specified'
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


class ResultsSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for laboratory results section data processing.
    
    Handles:
    - Laboratory test results
    - Diagnostic test results
    - Blood group information
    - Clinical observations
    """
    
    def get_section_code(self) -> str:
        return "30954-2"
    
    def get_section_name(self) -> str:
        return "Results"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract results from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_results = match_data.get('enhanced_results', [])
        
        if enhanced_results:
            logger.info(f"[RESULTS SERVICE] Found {len(enhanced_results)} enhanced results in session")
            return enhanced_results
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        results_data = clinical_arrays.get('results', [])
        
        if results_data:
            logger.info(f"[RESULTS SERVICE] Found {len(results_data)} results in clinical arrays")
            return results_data
        
        logger.info("[RESULTS SERVICE] No results data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract results from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') in ['30954-2', '18748-4', '34530-6']:
                    results = self._parse_results_xml(section)
                    logger.info(f"[RESULTS SERVICE] Extracted {len(results)} results from CDA")
                    return results
            
            logger.info("[RESULTS SERVICE] No results section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[RESULTS SERVICE] Error extracting results from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance results data and store in session."""
        enhanced_results = []
        
        for result_data in raw_data:
            enhanced_result = {
                'name': self._extract_field_value(result_data, 'name', 'Unknown test'),
                'display_name': self._extract_field_value(result_data, 'name', 'Unknown test'),
                'value': self._extract_field_value(result_data, 'value', 'Not specified'),
                'unit': self._extract_field_value(result_data, 'unit', ''),
                'reference_range': self._extract_field_value(result_data, 'reference_range', ''),
                'status': self._extract_field_value(result_data, 'status', 'Final'),
                'date': self._extract_field_value(result_data, 'date', 'Not specified'),
                'interpretation': self._extract_field_value(result_data, 'interpretation', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_results.append(enhanced_result)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_results'] = enhanced_results
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[RESULTS SERVICE] Enhanced and stored {len(enhanced_results)} results")
        return enhanced_results
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced results to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Results',
                'section_code': '30954-2',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # result.field_name
            }
        }
    
    def _parse_results_xml(self, section) -> List[Dict[str, Any]]:
        """Parse results section XML into structured data."""
        results = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                result = self._parse_result_observation(observation)
                if result:
                    results.append(result)
        
        return results
    
    def _parse_result_observation(self, observation) -> Dict[str, Any]:
        """Parse result observation into structured data."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract test name
        code_elem = observation.find('hl7:code', namespaces)
        name = "Unknown test"
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown test'))
        
        # Extract value and unit
        value_elem = observation.find('hl7:value', namespaces)
        value = "Not specified"
        unit = ""
        if value_elem is not None:
            value = value_elem.get('value', 'Not specified')
            unit = value_elem.get('unit', '')
        
        # Extract date
        time_elem = observation.find('hl7:effectiveTime', namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        return {
            'name': name,
            'value': value,
            'unit': unit,
            'reference_range': '',
            'status': 'Final',
            'date': date,
            'interpretation': ''
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


class MedicalDevicesSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for medical devices section data processing.
    
    Handles:
    - Implanted devices
    - Medical equipment
    - Device information
    - Device status
    """
    
    def get_section_code(self) -> str:
        return "46264-8"
    
    def get_section_name(self) -> str:
        return "Medical Devices"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract medical devices from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        enhanced_devices = match_data.get('enhanced_medical_devices', [])
        
        if enhanced_devices:
            logger.info(f"[MEDICAL DEVICES SERVICE] Found {len(enhanced_devices)} enhanced medical devices in session")
            return enhanced_devices
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        devices_data = clinical_arrays.get('medical_devices', [])
        
        if devices_data:
            logger.info(f"[MEDICAL DEVICES SERVICE] Found {len(devices_data)} medical devices in clinical arrays")
            return devices_data
        
        logger.info("[MEDICAL DEVICES SERVICE] No medical devices data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract medical devices from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            sections = root.findall('.//hl7:section', namespaces)
            
            for section in sections:
                code_elem = section.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') == '46264-8':
                    devices = self._parse_devices_xml(section)
                    logger.info(f"[MEDICAL DEVICES SERVICE] Extracted {len(devices)} medical devices from CDA")
                    return devices
            
            logger.info("[MEDICAL DEVICES SERVICE] No medical devices section found in CDA")
            return []
            
        except Exception as e:
            logger.error(f"[MEDICAL DEVICES SERVICE] Error extracting medical devices from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance medical devices data and store in session."""
        enhanced_devices = []
        
        for device_data in raw_data:
            enhanced_device = {
                'name': self._extract_field_value(device_data, 'name', 'Unknown device'),
                'display_name': self._extract_field_value(device_data, 'name', 'Unknown device'),
                'type': self._extract_field_value(device_data, 'type', 'Medical device'),
                'manufacturer': self._extract_field_value(device_data, 'manufacturer', 'Not specified'),
                'model': self._extract_field_value(device_data, 'model', 'Not specified'),
                'serial_number': self._extract_field_value(device_data, 'serial_number', 'Not specified'),
                'implant_date': self._extract_field_value(device_data, 'implant_date', 'Not specified'),
                'status': self._extract_field_value(device_data, 'status', 'Active'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_devices.append(enhanced_device)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_medical_devices'] = enhanced_devices
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[MEDICAL DEVICES SERVICE] Enhanced and stored {len(enhanced_devices)} medical devices")
        return enhanced_devices
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced medical devices to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Medical Devices',
                'section_code': '46264-8',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # device.field_name
            }
        }
    
    def _parse_devices_xml(self, section) -> List[Dict[str, Any]]:
        """Parse medical devices section XML into structured data."""
        devices = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            supply = entry.find('.//hl7:supply', namespaces)
            if supply is not None:
                device = self._parse_device_element(supply)
                if device:
                    devices.append(device)
        
        return devices
    
    def _parse_device_element(self, supply) -> Dict[str, Any]:
        """Parse device element into structured data."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract device name
        product = supply.find('.//hl7:product', namespaces)
        name = "Unknown device"
        manufacturer = "Not specified"
        model = "Not specified"
        
        if product is not None:
            material = product.find('.//hl7:manufacturedMaterial', namespaces)
            if material is not None:
                code_elem = material.find('hl7:code', namespaces)
                if code_elem is not None:
                    name = code_elem.get('displayName', code_elem.get('code', 'Unknown device'))
                
                # Extract manufacturer
                org = product.find('.//hl7:manufacturerOrganization', namespaces)
                if org is not None:
                    org_name = org.find('.//hl7:name', namespaces)
                    if org_name is not None:
                        manufacturer = org_name.text or "Not specified"
        
        # Extract date
        time_elem = supply.find('hl7:effectiveTime', namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        return {
            'name': name,
            'type': 'Medical device',
            'manufacturer': manufacturer,
            'model': model,
            'serial_number': 'Not specified',
            'implant_date': date,
            'status': 'Active'
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


# Register all services with the global pipeline manager
from .clinical_data_pipeline_manager import clinical_pipeline_manager

# Register all specialized services
clinical_pipeline_manager.register_service(ProblemsSectionService())
clinical_pipeline_manager.register_service(VitalSignsSectionService())
clinical_pipeline_manager.register_service(ProceduresSectionService())
clinical_pipeline_manager.register_service(ImmunizationsSectionService())
clinical_pipeline_manager.register_service(ResultsSectionService())
clinical_pipeline_manager.register_service(MedicalDevicesSectionService())