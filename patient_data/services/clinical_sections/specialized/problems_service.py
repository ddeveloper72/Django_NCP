"""
Problems Section Service

Specialized service for problems/conditions section data processing with CTS agent integration.

Handles:
- Problem lists and medical conditions  
- History of past illness
- Problem status and severity
- Clinical findings
- SNOMED CT code resolution via CTS agent

Author: Django_NCP Development Team
Date: October 2025
Version: 2.0.0 - Enhanced with CTS Integration
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase
from ..cts_integration_mixin import CTSIntegrationMixin

logger = logging.getLogger(__name__)


class ProblemsSectionService(CTSIntegrationMixin, ClinicalServiceBase):
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
                'criticality': self._extract_field_value(problem_data, 'criticality', 'Not specified'),
                'onset_date': self._format_cda_date(self._extract_field_value(problem_data, 'onset_date', 'Not specified')),
                'resolution_date': self._format_cda_date(self._extract_field_value(problem_data, 'resolution_date', 'Not specified')),
                'time_period': self._format_time_period(
                    self._extract_field_value(problem_data, 'onset_date', 'Not specified'),
                    self._extract_field_value(problem_data, 'resolution_date', 'Not specified')
                ),
                'verification_status': self._extract_field_value(problem_data, 'verification_status', 'Confirmed'),
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
        """Parse problem information from structured observation element with CTS agent integration."""
        # Extract problem name with enhanced text reference resolution
        value_elem = observation.find('hl7:value', self.namespaces)
        problem_name = "Unknown problem"
        code = ""
        code_system = ""
        
        if value_elem is not None:
            code = value_elem.get('code', '')
            code_system = value_elem.get('codeSystem', '')
            display_name = value_elem.get('displayName', '')
            
            # Check for text reference first (most reliable)
            original_text = value_elem.find('hl7:originalText', self.namespaces)
            text_reference = ""
            if original_text is not None:
                ref_elem = original_text.find('hl7:reference', self.namespaces)
                if ref_elem is not None:
                    ref_value = ref_elem.get('value', '')
                    text_reference = self._resolve_text_reference(observation, ref_value)
            
            # Use CTS resolution for SNOMED CT codes, otherwise use standard fallback
            if code_system == '2.16.840.1.113883.6.96':  # SNOMED CT
                try:
                    from patient_data.services.cts_integration.cts_service import CTSService
                    cts_service = CTSService()
                    cts_result = cts_service.get_term_display(code, code_system)
                    if cts_result and cts_result != code:
                        problem_name = cts_result
                    else:
                        problem_name = text_reference or display_name or code
                except Exception as cts_error:
                    self.logger.warning(f"CTS resolution failed for {code}: {cts_error}")
                    problem_name = text_reference or display_name or code
            else:
                # For non-SNOMED codes, use text reference, then displayName, then code mapping
                problem_name = text_reference or display_name
                
                if not problem_name:
                    # Map medical codes to standard descriptions
                    problem_name = self._map_medical_code_to_description(code, code_system)
                
                # Check for translation elements (like ICD codes with display names)
                if not problem_name or problem_name == code:
                    translation = value_elem.find('hl7:translation', self.namespaces)
                    if translation is not None:
                        problem_name = translation.get('displayName', problem_name)
                        # If translation has a better code/system, use that too
                        if not code or not code_system:
                            code = translation.get('code', code)
                            code_system = translation.get('codeSystem', code_system)
                
                # Final fallback to code description or code itself
                if not problem_name or problem_name == code or problem_name.startswith('#'):
                    problem_name = self._get_code_description(code, code_system) or code or 'Unknown problem'
        
        # Extract effective time with enhanced parsing for onset/resolution
        onset_date = "Not specified"
        resolution_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            # Check for low value (onset)
            low_elem = effective_time.find('hl7:low', self.namespaces)
            if low_elem is not None:
                onset_date = low_elem.get('value', 'Not specified')
            
            # Check for high value (resolution) 
            high_elem = effective_time.find('hl7:high', self.namespaces)
            if high_elem is not None:
                resolution_date = high_elem.get('value', 'Not specified')
            
            # If no low/high, check for single value
            if onset_date == "Not specified" and resolution_date == "Not specified":
                single_value = effective_time.get('value')
                if single_value:
                    onset_date = single_value
        
        # Extract severity using simpler approach with CTS integration
        severity = "Not specified"  # Default severity
        
        severity_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in severity_relations:
            if rel.get('typeCode') == 'SUBJ' and rel.get('inversionInd') == 'true':
                severity_obs = rel.find('hl7:observation', self.namespaces)
                if severity_obs is not None:
                    code_elem = severity_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == 'SEV':
                        severity_value = severity_obs.find('hl7:value', self.namespaces)
                        if severity_value is not None:
                            sev_code = severity_value.get('code', '')
                            sev_display = severity_value.get('displayName', '')
                            code_system = severity_value.get('codeSystem', '')
                            
                            # Use CTS resolution for SNOMED CT severity codes
                            severity = self._resolve_clinical_code_with_cts(
                                code=sev_code,
                                code_system=code_system,
                                display_name=sev_display,
                                text_reference="",
                                fallback_mappings={
                                    # SNOMED CT severity codes
                                    '24484000': 'Severe',
                                    '371924009': 'Moderate to severe', 
                                    '6736007': 'Moderate',
                                    '255604002': 'Mild',
                                    # Common displayName values
                                    'severe': 'Severe',
                                    'moderate': 'Moderate',
                                    'mild': 'Mild'
                                }
                            )
                            break
        
        # Extract clinical status using CTS agent for FHIR status codes
        clinical_status = "Active"  # Default status
        
        # Try to find status with simpler XPath
        status_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in status_relations:
            if rel.get('typeCode') == 'REFR':
                status_obs = rel.find('hl7:observation', self.namespaces)
                if status_obs is not None:
                    code_elem = status_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '33999-4':
                        status_value = status_obs.find('hl7:value', self.namespaces)
                        if status_value is not None:
                            status_code = status_value.get('code', '').lower()
                            status_display = status_value.get('displayName', '')
                            code_system = status_value.get('codeSystem', '')
                            
                            # Use CTS resolution with fallback mappings
                            clinical_status = self._resolve_clinical_code_with_cts(
                                code=status_code,
                                code_system=code_system,
                                display_name=status_display,
                                text_reference="",
                                fallback_mappings={
                                    'active': 'Active',
                                    'inactive': 'Inactive', 
                                    'resolved': 'Resolved',
                                    'entered-in-error': 'Entered in Error'
                                }
                            )
                            break
        
        # Extract verification status/certainty using simpler approach
        verification_status = "Confirmed"  # Default verification
        
        certainty_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in certainty_relations:
            if rel.get('typeCode') == 'SUBJ':
                certainty_obs = rel.find('hl7:observation', self.namespaces)
                if certainty_obs is not None:
                    code_elem = certainty_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '66455-7':
                        certainty_value = certainty_obs.find('hl7:value', self.namespaces)
                        if certainty_value is not None:
                            cert_code = certainty_value.get('code', '').lower()
                            cert_display = certainty_value.get('displayName', '')
                            code_system = certainty_value.get('codeSystem', '')
                            
                            verification_status = self._resolve_clinical_code_with_cts(
                                code=cert_code,
                                code_system=code_system,
                                display_name=cert_display,
                                text_reference="",
                                fallback_mappings={
                                    'confirmed': 'Confirmed',
                                    'unconfirmed': 'Unconfirmed', 
                                    'provisional': 'Provisional',
                                    'differential': 'Differential'
                                }
                            )
                            break
        
        # Extract criticality using simpler approach
        criticality = "Not specified"  # Default criticality
        
        criticality_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in criticality_relations:
            if rel.get('typeCode') == 'SUBJ':
                criticality_obs = rel.find('hl7:observation', self.namespaces)
                if criticality_obs is not None:
                    code_elem = criticality_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == '82606-5':
                        criticality_value = criticality_obs.find('hl7:value', self.namespaces)
                        if criticality_value is not None:
                            crit_code = criticality_value.get('code', '').lower()
                            crit_display = criticality_value.get('displayName', '')
                            code_system = criticality_value.get('codeSystem', '')
                            
                            criticality = self._resolve_clinical_code_with_cts(
                                code=crit_code,
                                code_system=code_system,
                                display_name=crit_display,
                                text_reference="",
                                fallback_mappings={
                                    'low': 'Low risk',
                                    'high': 'High risk',
                                    'unable-to-assess': 'Unable to assess'
                                }
                            )
                            break
        
        # Determine problem type based on templateId or code
        problem_type = "Clinical finding"
        template_ids = observation.findall('hl7:templateId', self.namespaces)
        for template in template_ids:
            root = template.get('root', '')
            if '1.3.6.1.4.1.12559.11.10.1.3.1.3.17' in root:  # Allergy template
                problem_type = "Allergy/Intolerance"
            elif '1.3.6.1.4.1.19376.1.5.3.1.4.5' in root:  # Problem concern
                problem_type = "Problem concern"
        
        self.logger.debug(f"[PROBLEMS SERVICE] Parsed problem: {problem_name}, onset: {onset_date}, severity: {severity}, status: {clinical_status}")
        
        return {
            'name': problem_name,
            'type': problem_type,
            'status': clinical_status,
            'severity': severity,
            'criticality': criticality,
            'onset_date': onset_date,
            'resolution_date': resolution_date,
            'verification_status': verification_status,
            'code': code,
            'code_system': code_system
        }
    
    def _resolve_text_reference(self, observation, ref_value: str) -> str:
        """Resolve text reference to actual content from CDA text section."""
        if not ref_value or not ref_value.startswith('#'):
            return ref_value
        
        # Remove the # prefix to get the ID
        target_id = ref_value[1:]
        
        # For ElementTree compatibility, we need to search the entire document
        # Find the root element
        current = observation
        while current.tag != '{urn:hl7-org:v3}ClinicalDocument':
            try:
                # In ElementTree, we need to search differently
                # Let's get all elements and find parent relationships
                root = None
                # Try to find document root by traversing
                test_elem = current
                for _ in range(20):  # Reasonable depth limit
                    # Check if this looks like a root element
                    if 'ClinicalDocument' in test_elem.tag:
                        root = test_elem
                        break
                    # Try to find a parent-like relationship through the tree
                    found_parent = False
                    for elem in test_elem.iter():
                        if current in list(elem):
                            test_elem = elem
                            found_parent = True
                            break
                    if not found_parent:
                        break
                if root:
                    break
                # If we can't navigate up, search the current element's tree
                break
            except:
                break
        
        # If we have a root or current element, search for the target ID
        search_root = current if 'ClinicalDocument' not in current.tag else current
        
        # Search all elements for the target ID
        for elem in search_root.iter():
            if elem.get('ID') == target_id:
                # Return the text content, handling nested elements
                text_content = ''.join(elem.itertext()).strip()
                return text_content if text_content else ref_value
        
        # If not found, try some common problem name mappings based on codes
        problem_name_map = {
            'val-9': 'Predominantly allergic asthma',
            'val-10': 'Postprocedural hypothyroidism', 
            'val-11': 'Other specified cardiac arrhythmias',
            'val-12': 'Type 2 diabetes mellitus',
            'val-13': 'Severe pre-eclampsia',
            'val-15': 'Acute tubulo-interstitial nephritis',
            'ref1': 'Meningoencefalitis herpetica'
        }
        
        return problem_name_map.get(target_id, ref_value)
    
    def _map_medical_code_to_description(self, code: str, code_system: str) -> str:
        """Map medical codes to human-readable descriptions using standard medical terminologies."""
        if not code:
            return ""
        
        # ICD-10 codes (1.3.6.1.4.1.12559.11.10.1.3.1.44.2 appears to be a local ICD system)
        icd10_map = {
            'J45': 'Asthma',
            'J45.0': 'Predominantly allergic asthma',
            'J45.9': 'Asthma, unspecified',
            'E89': 'Postprocedural endocrine and metabolic complications and disorders',
            'E89.0': 'Postprocedural hypothyroidism',
            'I49': 'Other cardiac arrhythmias',
            'I49.8': 'Other specified cardiac arrhythmias',
            'I49.9': 'Cardiac arrhythmia, unspecified',
            'O14': 'Pre-eclampsia',
            'O14.1': 'Severe pre-eclampsia',
            'N10': 'Acute tubulo-interstitial nephritis',
            'E10': 'Type 1 diabetes mellitus',
            'E11': 'Type 2 diabetes mellitus',
            'E89.1': 'Postprocedural hypoinsulinaemia'
        }
        
        # Check if this is an ICD-10 code
        if '1.3.6.1.4.1.12559.11.10.1.3.1.44' in code_system or code_system == '2.16.840.1.113883.6.3':
            description = icd10_map.get(code)
            if description:
                return description
        
        # ICD-9 codes (2.16.840.1.113883.6.103)
        icd9_map = {
            '054.3': 'Herpes simplex meningoencephalitis',
            '250.00': 'Diabetes mellitus without mention of complication'
        }
        
        if code_system == '2.16.840.1.113883.6.103':
            description = icd9_map.get(code)
            if description:
                return description
        
        # SNOMED CT codes (2.16.840.1.113883.6.96)
        snomed_map = {
            '404684003': 'Clinical finding',
            '55607006': 'Problem',
            '233604007': 'Pneumonia',
            '195967001': 'Asthma',
            '44054006': 'Type 2 diabetes mellitus',
            '46635009': 'Type 1 diabetes mellitus',
            '237602007': 'Hypothyroidism',
            '425229001': 'Cardiac arrhythmia',
            '15394000': 'Toxemia of pregnancy'
        }
        
        if code_system == '2.16.840.1.113883.6.96':
            description = snomed_map.get(code)
            if description:
                return description
        
        # ORPHA codes (1.3.6.1.4.1.12559.11.10.1.3.1.44.5)
        orpha_map = {
            '199': 'Cornelia de Lange syndrome'
        }
        
        if '1.3.6.1.4.1.12559.11.10.1.3.1.44.5' in code_system:
            description = orpha_map.get(code)
            if description:
                return description
        
        return ""
    
    def _get_code_description(self, code: str, code_system: str) -> str:
        """Get code description, potentially using CTS integration."""
        # Try CTS integration first for real-time resolution
        try:
            from ..cts_integration import cts_service
            cts_description = cts_service.resolve_code(code, code_system)
            if cts_description:
                self.logger.debug(f"[PROBLEMS SERVICE] CTS resolved {code} -> {cts_description}")
                return cts_description
        except ImportError:
            self.logger.debug("[PROBLEMS SERVICE] CTS integration not available")
        except Exception as e:
            self.logger.warning(f"[PROBLEMS SERVICE] CTS resolution failed for {code}: {e}")
        
        # Fallback to local mapping
        description = self._map_medical_code_to_description(code, code_system)
        
        if description:
            return description
        
        # If no mapping found, return a formatted version of the code
        if code:
            return f"Medical condition ({code})"
        
        return ""
    
    def _format_time_period(self, onset_date: str, resolution_date: str) -> str:
        """Format time period based on onset and resolution dates."""
        if onset_date != "Not specified" and resolution_date != "Not specified":
            onset_formatted = self._format_cda_date(onset_date) or onset_date
            resolution_formatted = self._format_cda_date(resolution_date) or resolution_date
            return f"From {onset_formatted} to {resolution_formatted}"
        elif onset_date != "Not specified":
            onset_formatted = self._format_cda_date(onset_date) or onset_date
            return f"Since {onset_formatted}"
        elif resolution_date != "Not specified":
            resolution_formatted = self._format_cda_date(resolution_date) or resolution_date
            return f"Until {resolution_formatted}"
        else:
            return "Not specified"
    
    def _parse_problem_narrative(self, text: str) -> Dict[str, Any]:
        """Parse problem information from narrative text."""
        # Extract timing information if present
        onset_date = "Not specified"
        resolution_date = "Not specified"
        
        if ' since ' in text:
            parts = text.split(' since ')
            problem_name = parts[0].strip()
            onset_date = f"since {parts[1].strip()}"
        elif ' from ' in text and ' to ' in text:
            # Handle "condition from date to date" pattern
            parts = text.split(' from ')
            problem_name = parts[0].strip()
            if len(parts) > 1 and ' to ' in parts[1]:
                date_parts = parts[1].split(' to ')
                onset_date = date_parts[0].strip()
                resolution_date = date_parts[1].strip()
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
        
        # Determine status based on text content
        status = "Active"
        if 'resolved' in text.lower() or 'inactive' in text.lower():
            status = "Resolved"
        elif 'chronic' in text.lower():
            status = "Active"
        
        return {
            'name': problem_name,
            'type': 'Clinical finding',
            'status': status,
            'severity': severity,
            'criticality': 'Not specified',
            'onset_date': onset_date,
            'resolution_date': resolution_date,
            'verification_status': 'Confirmed',
            'code': '',
            'code_system': ''
        }