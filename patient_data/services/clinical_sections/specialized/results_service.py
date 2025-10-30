"""
Results Section Service

Specialized service for laboratory results section data processing.

Handles:
- Laboratory test results
- Diagnostic test results
- Blood group information
- Clinical observations

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class ResultsSectionService(ClinicalServiceBase):
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
            self._log_extraction_result('extract_from_session', len(enhanced_results), 'Session')
            return enhanced_results
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        results_data = clinical_arrays.get('results', [])
        
        if results_data:
            self._log_extraction_result('extract_from_session', len(results_data), 'Clinical Arrays')
            return results_data
        
        self.logger.info("[RESULTS SERVICE] No results data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract results from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find results section using base method
            section = self._find_section_by_code(root, ['30954-2', '18748-4', '34530-6'])
            
            if section is not None:
                self.logger.info("[RESULTS SERVICE] Found results section in CDA")
                results = self._parse_results_xml(section)
                self._log_extraction_result('extract_from_cda', len(results), 'CDA')
                
                if results:
                    self.logger.info(f"[RESULTS SERVICE] Extracted {len(results)} results from CDA")
                    self.logger.info(f"[RESULTS SERVICE] First result: {results[0]}")
                
                return results
            
            self.logger.info("[RESULTS SERVICE] No results section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[RESULTS SERVICE] Error extracting results from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance results data and store in session."""
        enhanced_results = []
        
        for result_data in raw_data:
            # Preserve all extracted fields using dict() pattern
            enhanced_result = dict(result_data)
            
            # Ensure display_name is set
            if 'display_name' not in enhanced_result:
                enhanced_result['display_name'] = enhanced_result.get('name', 'Unknown test')
            
            # Mark as enhanced
            enhanced_result['source'] = 'cda_extraction_enhanced'
            
            self.logger.debug(f"[RESULTS SERVICE] Enhanced result: {enhanced_result.get('name')} with {len(enhanced_result)} fields")
            enhanced_results.append(enhanced_result)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_results'] = enhanced_results
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[RESULTS SERVICE] Enhanced and stored {len(enhanced_results)} results")
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
        
        self.logger.info("[RESULTS SERVICE] Starting XML parsing")
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        self.logger.info(f"[RESULTS SERVICE] Found {len(entries)} entries")
        
        for entry in entries:
            # Check for organizer pattern first (battery of tests)
            organizer = entry.find('hl7:organizer', self.namespaces)
            if organizer is not None:
                self.logger.info("[RESULTS SERVICE] Found organizer (battery of tests)")
                organizer_results = self._parse_result_organizer(organizer)
                results.extend(organizer_results)
                continue
            
            # Otherwise try direct observation
            observation = entry.find('hl7:observation', self.namespaces)
            if observation is not None:
                result = self._parse_result_observation(observation)
                if result:
                    self.logger.info(f"[RESULTS SERVICE] Parsed result: {result.get('name')} = {result.get('value')}")
                    results.append(result)
        
        self.logger.info(f"[RESULTS SERVICE] Total results parsed: {len(results)}")
        return results
    
    def _parse_result_organizer(self, organizer) -> List[Dict[str, Any]]:
        """Parse organizer (battery) containing multiple result observations."""
        results = []
        
        # Extract organizer-level information
        code_elem = organizer.find('hl7:code', self.namespaces)
        organizer_name = "Diagnostic test"
        if code_elem is not None:
            organizer_name = code_elem.get('displayName', code_elem.get('code', 'Diagnostic test'))
        
        # Find all component observations
        components = organizer.findall('.//hl7:component/hl7:observation', self.namespaces)
        self.logger.info(f"[RESULTS SERVICE] Found {len(components)} observations in organizer: {organizer_name}")
        
        for observation in components:
            result = self._parse_result_observation(observation)
            if result:
                # Add organizer context if result name is generic
                if result.get('name') == 'Unknown test':
                    result['name'] = organizer_name
                self.logger.info(f"[RESULTS SERVICE] Parsed organizer result: {result.get('name')} = {result.get('value')}")
                results.append(result)
        
        return results
    
    def _parse_result_observation(self, observation) -> Dict[str, Any]:
        """Parse result observation into structured data."""
        # Extract test name and LOINC code
        code_elem = observation.find('hl7:code', self.namespaces)
        name = "Unknown test"
        test_code = ""
        code_system = ""
        if code_elem is not None:
            name = code_elem.get('displayName', code_elem.get('code', 'Unknown test'))
            test_code = code_elem.get('code', '')
            code_system = code_elem.get('codeSystem', '')
        
        # Extract value and unit
        # Handle both physical quantities (PQ) and coded values (CE/CD)
        value_elem = observation.find('hl7:value', self.namespaces)
        value = "Not specified"
        unit = ""
        if value_elem is not None:
            value_type = value_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
            
            if 'PQ' in value_type:
                # Physical Quantity (numeric value with unit)
                value = value_elem.get('value', 'Not specified')
                unit = value_elem.get('unit', '')
            elif 'CE' in value_type or 'CD' in value_type:
                # Coded Element/Coded Data (use displayName)
                value = value_elem.get('displayName', value_elem.get('code', 'Not specified'))
            else:
                # Fallback to value attribute
                value = value_elem.get('value', value_elem.get('displayName', 'Not specified'))
        
        # Extract date
        time_elem = observation.find('hl7:effectiveTime', self.namespaces)
        date = "Not specified"
        if time_elem is not None:
            date = time_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Final"
        if status_elem is not None:
            status_code = status_elem.get('code', 'completed')
            status = self._map_status_code(status_code)
        
        # Extract interpretation (Normal, High, Low, etc.)
        interp_elem = observation.find('hl7:interpretationCode', self.namespaces)
        interpretation = ""
        if interp_elem is not None:
            interp_code = interp_elem.get('code', '')
            interpretation = self._map_interpretation_code(interp_code)
        
        # Extract text reference for narrative
        text_elem = observation.find('hl7:text/hl7:reference', self.namespaces)
        text_reference = ""
        if text_elem is not None:
            text_reference = text_elem.get('value', '')
        
        # Extract reference range if available
        reference_range = self._extract_reference_range(observation)
        
        return {
            'name': name,
            'test_code': test_code,
            'code_system': code_system,
            'value': value,
            'unit': unit,
            'reference_range': reference_range,
            'status': status,
            'date': date,
            'interpretation': interpretation,
            'text_reference': text_reference,
            'observation_id': observation.find('hl7:id', self.namespaces).get('root', '') if observation.find('hl7:id', self.namespaces) is not None else ''
        }
    
    def _map_status_code(self, status_code: str) -> str:
        """Map CDA status codes to display values."""
        status_map = {
            'completed': 'Final',
            'active': 'Preliminary',
            'aborted': 'Cancelled',
            'obsolete': 'Corrected'
        }
        return status_map.get(status_code.lower(), status_code.capitalize())
    
    def _map_interpretation_code(self, code: str) -> str:
        """Map HL7 interpretation codes to display values."""
        interpretation_map = {
            'N': 'Normal',
            'H': 'High',
            'L': 'Low',
            'HH': 'Critical High',
            'LL': 'Critical Low',
            'A': 'Abnormal',
            '<': 'Below Range',
            '>': 'Above Range',
            'I': 'Intermediate',
            'MS': 'Moderately Susceptible',
            'R': 'Resistant',
            'S': 'Susceptible',
            'VS': 'Very Susceptible'
        }
        return interpretation_map.get(code, code)
    
    def _extract_reference_range(self, observation) -> str:
        """Extract reference range from observation."""
        # Look for referenceRange element
        ref_range_elem = observation.find('.//hl7:referenceRange', self.namespaces)
        if ref_range_elem is not None:
            # Try to get low and high values
            low_elem = ref_range_elem.find('.//hl7:low', self.namespaces)
            high_elem = ref_range_elem.find('.//hl7:high', self.namespaces)
            
            if low_elem is not None and high_elem is not None:
                low_val = low_elem.get('value', '')
                high_val = high_elem.get('value', '')
                unit = low_elem.get('unit', high_elem.get('unit', ''))
                if low_val and high_val:
                    return f"{low_val}-{high_val} {unit}".strip()
            elif low_elem is not None:
                low_val = low_elem.get('value', '')
                unit = low_elem.get('unit', '')
                return f"≥ {low_val} {unit}".strip()
            elif high_elem is not None:
                high_val = high_elem.get('value', '')
                unit = high_elem.get('unit', '')
                return f"≤ {high_val} {unit}".strip()
        
        return ""