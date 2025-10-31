"""
Past Illness Section Service

Specialized service for history of past illness section data processing with CTS agent integration.

Handles:
- History of past illness
- Previous medical conditions
- Resolved conditions
- Historical clinical context
- SNOMED CT and ICD-10 code resolution via CTS agent

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


class PastIllnessSectionService(CTSIntegrationMixin, ClinicalServiceBase):
    """
    Specialized service for history of past illness section data processing.
    
    Handles:
    - History of past illness
    - Previous medical conditions
    - Resolved conditions
    - Historical clinical context
    """
    
    def get_section_code(self) -> str:
        return "11348-0"
    
    def get_section_name(self) -> str:
        return "Past Illness"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract past illness from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced past illness data
        enhanced_past_illness = match_data.get('enhanced_past_illness', [])
        
        if enhanced_past_illness:
            self._log_extraction_result('extract_from_session', len(enhanced_past_illness), 'Session')
            return enhanced_past_illness
        
        # Check for clinical arrays past illness
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        past_illness_data = clinical_arrays.get('past_illness', [])
        
        if past_illness_data:
            self._log_extraction_result('extract_from_session', len(past_illness_data), 'Clinical Arrays')
            return past_illness_data
        
        self.logger.info("[PAST ILLNESS SERVICE] No past illness data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract past illness from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find past illness section using base method
            # CRITICAL: Search for both possible codes:
            # - 10157-6 (History of Past Illness - standard LOINC)
            # - 11348-0 (History of Past Illness - alternative)
            # Do NOT include 11450-4 (Problem List - that's for active problems)
            section = self._find_section_by_code(root, ['10157-6', '11348-0'])
            
            if section is not None:
                # Log which section code was found
                section_code_elem = section.find('hl7:code', self.namespaces)
                found_code = section_code_elem.get('code') if section_code_elem is not None else 'unknown'
                
                past_illnesses = self._parse_past_illness_xml(section)
                self.logger.info(f"[PAST ILLNESS SERVICE] Found {len(past_illnesses)} past illness entries in section {found_code}")
                self._log_extraction_result('extract_from_cda', len(past_illnesses), 'CDA')
                return past_illnesses
            
            self.logger.info("[PAST ILLNESS SERVICE] No past illness section (10157-6 or 11348-0) found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[PAST ILLNESS SERVICE] Error extracting past illness from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance past illness data and store in session.
        
        Expected fields from user requirements:
        1. Closed/Inactive Problem (problem_name)
        2. Problem Type
        3. Time (from-to timeline)
        4. Problem Status
        5. Health Status
        """
        enhanced_past_illness = []
        
        for illness_data in raw_data:
            # Extract time values
            time_low = illness_data.get('time_low', '')
            time_high = illness_data.get('time_high', '')
            
            enhanced_illness = {
                # Core fields matching user requirements
                'problem_name': self._extract_field_value(illness_data, 'problem_name', 'Unknown Problem'),
                'problem_type': self._extract_field_value(illness_data, 'problem_type', 'Problem'),
                'time_low': time_low,
                'time_high': time_high,
                'problem_status': self._extract_field_value(illness_data, 'problem_status', 'Not specified'),
                'health_status': self._extract_field_value(illness_data, 'health_status', 'Not specified'),
                
                # Additional metadata
                'problem_code': illness_data.get('problem_code'),
                'problem_code_system': illness_data.get('problem_code_system'),
                'act_status': illness_data.get('act_status', 'completed'),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_past_illness.append(enhanced_illness)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_past_illness'] = enhanced_past_illness
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[PAST ILLNESS SERVICE] Enhanced and stored {len(enhanced_past_illness)} past illness records")
        return enhanced_past_illness
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced past illness to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Past Illness',
                'section_code': '11348-0',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # illness.field_name
            }
        }
    
    def _parse_past_illness_xml(self, section) -> List[Dict[str, Any]]:
        """
        Parse past illness section XML into structured data.
        
        Expected structure:
        - entry/act (classCode="ACT", moodCode="EVN")
          - effectiveTime (from act level - time period)
          - statusCode (from act level - "completed")
          - entryRelationship[@typeCode="SUBJ"]
            - observation (the main problem observation)
              - code (problem type code - typically 55607006)
              - value (problem/condition code - ICD-10 code)
              - effectiveTime (from observation level)
              - entryRelationship[@typeCode="REFR"] (Problem Status)
                - observation with code="33999-4"
                - value (problem status code)
              - entryRelationship[@typeCode="REFR"] (Health Status)
                - observation with code="11323-3"
                - value (health status code)
        """
        past_illnesses = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        logger.info(f"[PAST ILLNESS SERVICE] Found {len(entries)} entries in section")
        
        for entry in entries:
            # Look for the act element (should be direct child)
            act = entry.find('hl7:act', self.namespaces)
            if act is not None:
                illness = self._parse_illness_act(act)
                if illness:
                    past_illnesses.append(illness)
            else:
                # Fallback: try to find observation directly (old structure)
                observation = entry.find('.//hl7:observation', self.namespaces)
                if observation is not None:
                    illness = self._parse_illness_observation(observation)
                    if illness:
                        past_illnesses.append(illness)
        
        return past_illnesses
    
    def _parse_illness_act(self, act) -> Dict[str, Any]:
        """
        Parse past illness act element (new structure).
        
        Extracts:
        - Problem name from nested observation value
        - Problem type from observation code
        - Time period from effectiveTime (low/high)
        - Problem status from entryRelationship observation (code 33999-4)
        - Health status from entryRelationship observation (code 11323-3)
        """
        # Extract act-level data
        act_status = act.find('hl7:statusCode', self.namespaces)
        act_status_code = act_status.get('code') if act_status is not None else 'completed'
        
        # Extract act-level effectiveTime
        act_effective_time = act.find('hl7:effectiveTime', self.namespaces)
        act_time_low = None
        act_time_high = None
        
        if act_effective_time is not None:
            low_elem = act_effective_time.find('hl7:low', self.namespaces)
            high_elem = act_effective_time.find('hl7:high', self.namespaces)
            act_time_low = low_elem.get('value') if low_elem is not None else None
            act_time_high = high_elem.get('value') if high_elem is not None else None
        
        # Find the primary observation in entryRelationship with typeCode="SUBJ"
        entry_rel_subj = act.find('hl7:entryRelationship[@typeCode="SUBJ"]', self.namespaces)
        if entry_rel_subj is None:
            logger.warning("[PAST ILLNESS SERVICE] No SUBJ entryRelationship found in act")
            return None
        
        observation = entry_rel_subj.find('hl7:observation', self.namespaces)
        if observation is None:
            logger.warning("[PAST ILLNESS SERVICE] No observation found in SUBJ entryRelationship")
            return None
        
        # Extract problem name from observation value
        value_elem = observation.find('hl7:value', self.namespaces)
        problem_name = "Unknown Problem"
        problem_code = None
        problem_code_system = None
        
        if value_elem is not None:
            problem_code = value_elem.get('code')
            problem_code_system = value_elem.get('codeSystem')
            display_name = value_elem.get('displayName', '')
            
            logger.info(f"[PAST ILLNESS SERVICE] Extracted from value element - code: {problem_code}, system: {problem_code_system}, displayName: {display_name}")
            
            # CRITICAL: Prioritize CTS translation over displayName
            # displayName often contains narrative references like "Problem (ref: #val-17)" which are not useful
            if problem_code and problem_code_system:
                try:
                    from patient_data.services.cts_integration.cts_service import CTSService
                    cts_service = CTSService()
                    logger.info(f"[PAST ILLNESS SERVICE] Calling CTS for code={problem_code}, system={problem_code_system}")
                    cts_result = cts_service.get_term_display(problem_code, problem_code_system)
                    logger.info(f"[PAST ILLNESS SERVICE] CTS returned: '{cts_result}'")
                    
                    if cts_result and cts_result != problem_code:
                        problem_name = cts_result
                        logger.info(f"[PAST ILLNESS SERVICE] CTS resolved {problem_code} to: {problem_name}")
                    else:
                        # CTS failed - use displayName only if it looks useful (not a reference)
                        if display_name and "ref:" not in display_name.lower() and len(display_name) > 10:
                            problem_name = display_name
                            logger.info(f"[PAST ILLNESS SERVICE] Using displayName: {display_name}")
                        else:
                            problem_name = problem_code
                            logger.warning(f"[PAST ILLNESS SERVICE] CTS failed and displayName unusable, using code: {problem_code}")
                except Exception as cts_error:
                    logger.error(f"[PAST ILLNESS SERVICE] CTS exception for {problem_code}: {cts_error}", exc_info=True)
                    # CTS exception - use displayName only if it looks useful
                    if display_name and "ref:" not in display_name.lower() and len(display_name) > 10:
                        problem_name = display_name
                    else:
                        problem_name = problem_code
            else:
                # No code available - use displayName if present
                problem_name = display_name if display_name else "Unknown Problem"
                logger.warning(f"[PAST ILLNESS SERVICE] No code/system available, using displayName: {display_name}")
            
            # Fallback: Try to resolve narrative reference if still no valid name
            if not problem_name or problem_name == problem_code or problem_name == "Unknown Problem":
                original_text = value_elem.find('hl7:originalText', self.namespaces)
                if original_text is not None:
                    reference = original_text.find('hl7:reference', self.namespaces)
                    if reference is not None:
                        ref_value = reference.get('value', '')
                        logger.warning(f"[PAST ILLNESS SERVICE] Problem name not resolved, has reference: {ref_value}")
                        problem_name = f"Problem (ref: {ref_value})"
        
        # Extract problem type from observation code
        code_elem = observation.find('hl7:code', self.namespaces)
        problem_type = "Problem"
        if code_elem is not None:
            problem_type = code_elem.get('displayName', 'Problem')
        
        # Extract observation-level effectiveTime (may override act time)
        obs_effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        time_low = act_time_low
        time_high = act_time_high
        
        if obs_effective_time is not None:
            low_elem = obs_effective_time.find('hl7:low', self.namespaces)
            high_elem = obs_effective_time.find('hl7:high', self.namespaces)
            time_low = low_elem.get('value') if low_elem is not None else time_low
            time_high = high_elem.get('value') if high_elem is not None else time_high
        
        # Extract Problem Status (code 33999-4) from entryRelationship
        problem_status = self._extract_related_observation_value(
            observation, '33999-4', 'Not specified'
        )
        
        # Extract Health Status (code 11323-3) from entryRelationship
        health_status = self._extract_related_observation_value(
            observation, '11323-3', 'Not specified'
        )
        
        illness_dict = {
            'problem_name': problem_name,
            'problem_type': problem_type,
            'time_low': time_low,
            'time_high': time_high,
            'problem_status': problem_status,
            'health_status': health_status,
            'problem_code': problem_code,
            'problem_code_system': problem_code_system,
            'act_status': act_status_code
        }
        
        # LOG SERVICE OUTPUT
        logger.info(f"[PAST ILLNESS SERVICE] Returning illness data:")
        logger.info(f"  problem_name: '{problem_name}'")
        logger.info(f"  problem_code: '{problem_code}'")
        logger.info(f"  problem_code_system: '{problem_code_system}'")
        logger.info(f"  problem_status: '{problem_status}'")
        logger.info(f"  health_status: '{health_status}'")
        logger.info(f"  time: {time_low} to {time_high}")
        
        return illness_dict
    
    def _extract_related_observation_value(self, observation, code_value: str, default: str) -> str:
        """
        Extract value from related observation with specific code.
        
        Looks for entryRelationship[@typeCode="REFR"]/observation with matching code.
        Uses CTS resolution for SNOMED CT codes.
        """
        entry_relationships = observation.findall('hl7:entryRelationship[@typeCode="REFR"]', self.namespaces)
        
        for rel in entry_relationships:
            rel_obs = rel.find('hl7:observation', self.namespaces)
            if rel_obs is not None:
                code_elem = rel_obs.find('hl7:code', self.namespaces)
                if code_elem is not None and code_elem.get('code') == code_value:
                    # Found matching observation, extract value
                    value_elem = rel_obs.find('hl7:value', self.namespaces)
                    if value_elem is not None:
                        value_code = value_elem.get('code')
                        value_code_system = value_elem.get('codeSystem')
                        display_name = value_elem.get('displayName', '')
                        
                        logger.info(f"[PAST ILLNESS SERVICE] Extracting {code_value} - code: {value_code}, system: {value_code_system}, displayName: {display_name}")
                        
                        # CRITICAL: Prioritize CTS resolution for SNOMED CT codes
                        if value_code and value_code_system:
                            try:
                                from patient_data.services.cts_integration.cts_service import CTSService
                                cts_service = CTSService()
                                logger.info(f"[PAST ILLNESS SERVICE] Calling CTS for {code_value} code={value_code}, system={value_code_system}")
                                cts_result = cts_service.get_term_display(value_code, value_code_system)
                                logger.info(f"[PAST ILLNESS SERVICE] CTS returned: '{cts_result}'")
                                
                                if cts_result and cts_result != value_code:
                                    logger.info(f"[PAST ILLNESS SERVICE] CTS resolved {code_value} code {value_code} to: {cts_result}")
                                    return cts_result
                                else:
                                    # CTS failed - use displayName only if useful, otherwise use code
                                    if display_name and len(display_name) > 2:
                                        logger.warning(f"[PAST ILLNESS SERVICE] CTS failed, using displayName: {display_name}")
                                        return display_name
                                    else:
                                        logger.warning(f"[PAST ILLNESS SERVICE] CTS failed, no displayName, using code: {value_code}")
                                        return value_code if value_code else default
                            except Exception as cts_error:
                                logger.error(f"[PAST ILLNESS SERVICE] CTS exception for {value_code}: {cts_error}", exc_info=True)
                                # CTS exception - use displayName if available
                                return display_name if display_name else (value_code if value_code else default)
                        else:
                            logger.warning(f"[PAST ILLNESS SERVICE] No code/system for {code_value}, using displayName")
                            return display_name if display_name else default
        
        return default
    
    def _parse_illness_observation(self, observation) -> Dict[str, Any]:
        """Parse past illness observation into structured data."""
        # Extract condition name
        value_elem = observation.find('hl7:value', self.namespaces)
        condition = "Unknown condition"
        if value_elem is not None:
            condition = value_elem.get('displayName', value_elem.get('code', 'Unknown condition'))
        
        # Extract onset date
        onset_date = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            low_elem = effective_time.find('hl7:low', self.namespaces)
            if low_elem is not None:
                onset_date = low_elem.get('value', 'Not specified')
            else:
                onset_date = effective_time.get('value', 'Not specified')
        
        # Extract resolution date
        resolution_date = "Not specified"
        if effective_time is not None:
            high_elem = effective_time.find('hl7:high', self.namespaces)
            if high_elem is not None:
                resolution_date = high_elem.get('value', 'Not specified')
        
        # Extract status
        status_elem = observation.find('hl7:statusCode', self.namespaces)
        status = "Resolved"
        if status_elem is not None:
            status = status_elem.get('code', 'Resolved')
        
        return {
            'condition': condition,
            'onset_date': onset_date,
            'resolution_date': resolution_date,
            'status': status,
            'severity': 'Not specified',
            'clinical_status': 'Inactive',
            'verification_status': 'Confirmed'
        }