"""
Problems Section Service

Specialized service for problems/conditions section data processing.

Handles:
- Problem lists and medical conditions  
- History of past illness
- Problem status and severity
- Clinical findings

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class ProblemsSectionService(ClinicalServiceBase):
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
            self._log_extraction_result('extract_from_session', len(enhanced_problems), 'Session')
            return enhanced_problems
        
        # Check for clinical arrays problems
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        problems_data = clinical_arrays.get('problems', [])
        
        if problems_data:
            self._log_extraction_result('extract_from_session', len(problems_data), 'Clinical Arrays')
            return problems_data
        
        self.logger.info("[PROBLEMS SERVICE] No problems data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract problems from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find problems section using base method
            section = self._find_section_by_code(root, ['11450-4', '11348-0'])
            
            if section is not None:
                problems = self._parse_problems_xml(section)
                self._log_extraction_result('extract_from_cda', len(problems), 'CDA')
                return problems
            
            self.logger.info("[PROBLEMS SERVICE] No problems section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[PROBLEMS SERVICE] Error extracting problems from CDA: {e}")
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
        
        self.logger.info(f"[PROBLEMS SERVICE] Enhanced and stored {len(enhanced_problems)} problems")
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
        
        # Strategy 1: Extract from structured entries
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                problem = self._parse_problem_observation(observation)
                if problem:
                    problems.append(problem)
        
        # Strategy 2: Extract from narrative text
        if not problems:
            text_section = section.find('.//hl7:text', self.namespaces)
            if text_section is not None:
                paragraphs = text_section.findall('.//hl7:paragraph', self.namespaces)
                for paragraph in paragraphs:
                    text = self._extract_text_from_element(paragraph)
                    if text and text.strip():
                        problem = self._parse_problem_narrative(text)
                        if problem:
                            problems.append(problem)
        
        return problems
    
    def _parse_problem_observation(self, observation) -> Dict[str, Any]:
        """Parse problem information from structured observation element."""
        # Extract problem name from value element
        value_elem = observation.find('hl7:value', self.namespaces)
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
        status_obs = observation.find('.//hl7:observation[hl7:code/@code="33999-4"]', self.namespaces)
        if status_obs is not None:
            status_value = status_obs.find('hl7:value', self.namespaces)
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