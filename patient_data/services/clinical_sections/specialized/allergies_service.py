"""
Allergies Section Service

Specialized service for allergies and adverse reactions section data processing.

Handles:
- Allergies and adverse reactions
- Allergy severity and criticality
- Reaction manifestations
- Substance identification

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class AllergiesSectionService(ClinicalServiceBase):
    """
    Specialized service for allergies and adverse reactions section data processing.
    
    Handles:
    - Allergies and adverse reactions
    - Allergy severity and criticality
    - Reaction manifestations  
    - Substance identification
    """
    
    def get_section_code(self) -> str:
        return "48765-2"
    
    def get_section_name(self) -> str:
        return "Allergies"
    
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """Extract allergies from session storage."""
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        
        # Check for enhanced allergies data
        enhanced_allergies = match_data.get('enhanced_allergies', [])
        
        if enhanced_allergies:
            self._log_extraction_result('extract_from_session', len(enhanced_allergies), 'Session')
            return enhanced_allergies
        
        # Check for clinical arrays allergies
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        allergies_data = clinical_arrays.get('allergies', [])
        
        if allergies_data:
            self._log_extraction_result('extract_from_session', len(allergies_data), 'Clinical Arrays')
            return allergies_data
        
        self.logger.info("[ALLERGIES SERVICE] No allergies data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract allergies from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find allergies section using base method
            section = self._find_section_by_code(root, ['48765-2', '10155-0'])
            
            if section is not None:
                allergies = self._parse_allergies_xml(section)
                self._log_extraction_result('extract_from_cda', len(allergies), 'CDA')
                return allergies
            
            self.logger.info("[ALLERGIES SERVICE] No allergies section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[ALLERGIES SERVICE] Error extracting allergies from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance comprehensive allergies data and store in session."""
        enhanced_allergies = []
        
        for allergy_data in raw_data:
            enhanced_allergy = {
                # Primary fields for display
                'name': self._extract_field_value(allergy_data, 'agent', 'Unknown allergen'),
                'display_name': self._extract_field_value(allergy_data, 'agent', 'Unknown allergen'),
                
                # Comprehensive allergy data (9 fields from Portuguese CDA)
                'reaction_type': self._extract_field_value(allergy_data, 'reaction_type', 'Propensity to adverse reaction'),
                'clinical_manifestation': self._extract_field_value(allergy_data, 'clinical_manifestation', 'Not specified'),
                'agent': self._extract_field_value(allergy_data, 'agent', 'Unknown allergen'),
                'time': self._extract_field_value(allergy_data, 'time', 'Not specified'),
                'severity': self._extract_field_value(allergy_data, 'severity', 'Not specified'),
                'criticality': self._extract_field_value(allergy_data, 'criticality', 'Not specified'),
                'status': self._extract_field_value(allergy_data, 'status', 'Active'),
                'certainty': self._extract_field_value(allergy_data, 'certainty', 'Confirmed'),
                'process_establishing': self._extract_field_value(allergy_data, 'process_establishing', 'Not specified'),
                
                # Backward compatibility fields
                'substance': self._extract_field_value(allergy_data, 'substance', 'Unknown allergen'),
                'reaction': self._extract_field_value(allergy_data, 'clinical_manifestation', 'Not specified'),
                'onset_date': self._extract_field_value(allergy_data, 'time', 'Not specified'),
                'verification_status': self._extract_field_value(allergy_data, 'certainty', 'Confirmed'),
                
                'source': 'cda_extraction_enhanced'
            }
            enhanced_allergies.append(enhanced_allergy)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_allergies'] = enhanced_allergies
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[ALLERGIES SERVICE] Enhanced and stored {len(enhanced_allergies)} comprehensive allergies")
        return enhanced_allergies
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert enhanced allergies to template-ready format."""
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': 'Allergies',
                'section_code': '48765-2',
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'template_pattern': 'direct_field_access'  # allergy.field_name
            }
        }
    
    def _parse_allergies_xml(self, section) -> List[Dict[str, Any]]:
        """Parse allergies section XML into structured data."""
        allergies = []
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', self.namespaces)
            if observation is not None:
                allergy = self._parse_allergy_observation(observation)
                if allergy:
                    allergies.append(allergy)
        
        return allergies
    
    def _parse_allergy_observation(self, observation) -> Dict[str, Any]:
        """Parse allergy observation into comprehensive structured data matching Portuguese CDA format."""
        allergy_data = {}
        
        # 1. Extract Reaction Type (main observation code) with CTS agent support
        reaction_type = "Unknown"
        obs_code = observation.find('hl7:code', self.namespaces)
        if obs_code is not None:
            type_code = obs_code.get('code', '')
            type_display = obs_code.get('displayName', '')
            code_system = obs_code.get('codeSystem', '')
            
            # Priority 1: Use CTS agent for SNOMED CT codes (2.16.840.1.113883.6.96)
            if type_code and code_system == '2.16.840.1.113883.6.96':
                try:
                    from patient_data.services.cts_integration.cts_service import CTSService
                    cts_service = CTSService()
                    cts_result = cts_service.get_term_display(type_code, code_system)
                    if cts_result and cts_result != type_code:
                        reaction_type = cts_result
                    else:
                        reaction_type = type_display or "Propensity to adverse reaction"
                except Exception as cts_error:
                    self.logger.warning(f"CTS resolution failed for reaction type {type_code}: {cts_error}")
                    reaction_type = type_display or "Propensity to adverse reaction"
            else:
                reaction_type = type_display or "Propensity to adverse reaction"
            
            # Priority 2: Resolve text reference if needed
            original_text = obs_code.find('hl7:originalText', self.namespaces)
            if original_text is not None:
                ref_elem = original_text.find('hl7:reference', self.namespaces)
                if ref_elem is not None:
                    ref_value = ref_elem.get('value', '')
                    resolved_text = self._resolve_text_reference(observation, ref_value)
                    if resolved_text and resolved_text != ref_value:
                        reaction_type = resolved_text
        
        # 2. Extract Agent/Allergen Substance with CTS agent support
        agent = "Unknown substance"
        agent_code = ""
        agent_system = ""
        participant = observation.find('.//hl7:participant[@typeCode="CSM"]', self.namespaces)
        if participant is not None:
            entity = participant.find('.//hl7:playingEntity/hl7:code', self.namespaces)
            if entity is not None:
                agent_display = entity.get('displayName', '')
                agent_code = entity.get('code', '')
                agent_system = entity.get('codeSystem', '')
                
                # Priority 1: Use CTS agent for SNOMED CT (2.16.840.1.113883.6.96) or ATC codes (2.16.840.1.113883.6.73)
                if agent_code and agent_system in ['2.16.840.1.113883.6.96', '2.16.840.1.113883.6.73']:
                    try:
                        from patient_data.services.cts_integration.cts_service import CTSService
                        cts_service = CTSService()
                        cts_result = cts_service.get_term_display(agent_code, agent_system)
                        if cts_result and cts_result != agent_code:
                            agent = cts_result
                        else:
                            agent = agent_display or agent_code
                    except Exception as cts_error:
                        self.logger.warning(f"CTS resolution failed for agent {agent_code}: {cts_error}")
                        agent = agent_display or agent_code
                else:
                    agent = agent_display or agent_code
                
                # Priority 2: Resolve text reference for agent
                original_text = entity.find('hl7:originalText', self.namespaces)
                if original_text is not None:
                    ref_elem = original_text.find('hl7:reference', self.namespaces)
                    if ref_elem is not None:
                        ref_value = ref_elem.get('value', '')
                        resolved_text = self._resolve_text_reference(observation, ref_value)
                        if resolved_text and resolved_text != ref_value:
                            agent = resolved_text
                
                # Priority 3: Fallback to code mapping if no displayName
                if not agent or agent == agent_code:
                    agent = self._map_substance_code_to_description(agent_code, agent_system) or f"Substance ({agent_code})"

        # 3. Extract Clinical Manifestation (reaction symptoms) with CTS agent support
        manifestation = "Not specified"
        mfst_entry = observation.find('.//hl7:entryRelationship[@typeCode="MFST"]', self.namespaces)
        if mfst_entry is not None:
            mfst_obs = mfst_entry.find('hl7:observation', self.namespaces)
            if mfst_obs is not None:
                mfst_value = mfst_obs.find('hl7:value', self.namespaces)
                if mfst_value is not None:
                    mfst_code = mfst_value.get('code', '')
                    mfst_display = mfst_value.get('displayName', '')
                    code_system = mfst_value.get('codeSystem', '')
                    
                    # Priority 1: Use CTS agent for SNOMED CT codes (2.16.840.1.113883.6.96)
                    if mfst_code and code_system == '2.16.840.1.113883.6.96':
                        try:
                            from patient_data.services.cts_integration.cts_service import CTSService
                            cts_service = CTSService()
                            cts_result = cts_service.get_term_display(mfst_code, code_system)
                            if cts_result and cts_result != mfst_code:
                                manifestation = cts_result
                            else:
                                manifestation = mfst_display or mfst_code
                        except Exception as cts_error:
                            self.logger.warning(f"CTS resolution failed for manifestation {mfst_code}: {cts_error}")
                            manifestation = mfst_display or mfst_code
                    else:
                        manifestation = mfst_display or mfst_code
                    
                    # Priority 2: Resolve text reference for manifestation
                    original_text = mfst_value.find('hl7:originalText', self.namespaces)
                    if original_text is not None:
                        ref_elem = original_text.find('hl7:reference', self.namespaces)
                        if ref_elem is not None:
                            ref_value = ref_elem.get('value', '')
                            resolved_text = self._resolve_text_reference(observation, ref_value)
                            if resolved_text and resolved_text != ref_value:
                                manifestation = resolved_text
                    
                    # Priority 3: Fallback to code mapping
                    if not manifestation or manifestation == mfst_code:
                        manifestation = self._map_reaction_code_to_description(mfst_code, code_system) or "Not specified"

        # 4. Extract Time Information (onset/duration)
        time_info = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', self.namespaces)
        if effective_time is not None:
            # Check for interval (IVL_TS) with low/high
            if effective_time.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'IVL_TS':
                low_elem = effective_time.find('hl7:low', self.namespaces)
                high_elem = effective_time.find('hl7:high', self.namespaces)
                if low_elem is not None and high_elem is not None:
                    low_val = self._format_cda_date(low_elem.get('value', ''))
                    high_val = self._format_cda_date(high_elem.get('value', ''))
                    time_info = f"from {low_val} until {high_val}"
                elif low_elem is not None:
                    low_val = self._format_cda_date(low_elem.get('value', ''))
                    time_info = f"since {low_val}"
            else:
                # Single onset time
                low_elem = effective_time.find('hl7:low', self.namespaces)
                if low_elem is not None:
                    onset_val = self._format_cda_date(low_elem.get('value', ''))
                    time_info = f"since {onset_val}"
                else:
                    # Direct value
                    value = effective_time.get('value', '')
                    if value:
                        formatted_val = self._format_cda_date(value)
                        time_info = f"since {formatted_val}"

        # 5. Extract Severity with CTS agent support
        severity = "Not specified"
        severity_relations = observation.findall('.//hl7:entryRelationship', self.namespaces)
        for rel in severity_relations:
            if rel.get('typeCode') == 'SUBJ' and rel.get('inversionInd') == 'true':
                severity_obs = rel.find('hl7:observation', self.namespaces)
                if severity_obs is not None:
                    code_elem = severity_obs.find('hl7:code', self.namespaces)
                    if code_elem is not None and code_elem.get('code') == 'SEV':
                        severity_value = severity_obs.find('hl7:value', self.namespaces)
                        if severity_value is not None:
                            severity_code = severity_value.get('code', '')
                            severity_display = severity_value.get('displayName', '')
                            code_system = severity_value.get('codeSystem', '')
                            
                            # Use CTS agent for SNOMED CT codes (2.16.840.1.113883.6.96)
                            if severity_code and code_system == '2.16.840.1.113883.6.96':
                                try:
                                    from patient_data.services.cts_integration.cts_service import CTSService
                                    cts_service = CTSService()
                                    cts_result = cts_service.get_term_display(severity_code, code_system)
                                    if cts_result and cts_result != severity_code:
                                        severity = cts_result
                                        break
                                except Exception as cts_error:
                                    self.logger.warning(f"CTS resolution failed for severity {severity_code}: {cts_error}")
                            
                            severity = severity_display or severity_code or "Not specified"

        # 6. Extract Criticality (code="82606-5") with CTS agent support
        criticality = "Not specified"
        criticality_relations = observation.findall('.//hl7:entryRelationship[@typeCode="SUBJ"]', self.namespaces)
        for rel in criticality_relations:
            criticality_obs = rel.find('hl7:observation', self.namespaces)
            if criticality_obs is not None:
                code_elem = criticality_obs.find('hl7:code', self.namespaces)
                if code_elem is not None and code_elem.get('code') == '82606-5':
                    criticality_value = criticality_obs.find('hl7:value', self.namespaces)
                    if criticality_value is not None:
                        criticality_code = criticality_value.get('code', '').lower()
                        criticality_display = criticality_value.get('displayName', '')
                        code_system = criticality_value.get('codeSystem', '')
                        
                        # Priority 1: Use CTS agent for FHIR codes (2.16.840.1.113883.4.642.4.130)
                        if criticality_code and code_system == '2.16.840.1.113883.4.642.4.130':
                            try:
                                from patient_data.services.cts_integration.cts_service import CTSService
                                cts_service = CTSService()
                                cts_result = cts_service.get_term_display(criticality_code, code_system)
                                if cts_result and cts_result != criticality_code:
                                    criticality = cts_result
                                    break
                            except Exception as cts_error:
                                self.logger.warning(f"CTS resolution failed for criticality {criticality_code}: {cts_error}")
                        
                        # Priority 2: Resolve text reference for criticality
                        text_elem = criticality_obs.find('hl7:text', self.namespaces)
                        if text_elem is not None:
                            ref_elem = text_elem.find('hl7:reference', self.namespaces)
                            if ref_elem is not None:
                                ref_value = ref_elem.get('value', '')
                                resolved_text = self._resolve_text_reference(observation, ref_value)
                                if resolved_text and resolved_text != ref_value:
                                    criticality = resolved_text
                                    break
                        
                        # Priority 3: Map standard FHIR criticality codes
                        criticality_mappings = {
                            'low': 'low risk',
                            'high': 'high risk',
                            'unable-to-assess': 'unable to assess'
                        }
                        
                        if criticality_code in criticality_mappings:
                            criticality = criticality_mappings[criticality_code]
                        else:
                            criticality = criticality_display or criticality_code or "Not specified"

        # 7. Extract Status (code="33999-4") with CTS agent support
        status = "Active"
        status_relations = observation.findall('.//hl7:entryRelationship[@typeCode="REFR"]', self.namespaces)
        for rel in status_relations:
            status_obs = rel.find('hl7:observation', self.namespaces)
            if status_obs is not None:
                code_elem = status_obs.find('hl7:code', self.namespaces)
                if code_elem is not None and code_elem.get('code') == '33999-4':
                    status_value = status_obs.find('hl7:value', self.namespaces)
                    if status_value is not None:
                        status_code = status_value.get('code', '').lower()
                        status_display = status_value.get('displayName', '')
                        code_system = status_value.get('codeSystem', '')
                        
                        # Priority 1: Use CTS agent for clinical code resolution
                        if status_code and code_system:
                            try:
                                from patient_data.services.cts_integration.cts_service import CTSService
                                cts_service = CTSService()
                                cts_result = cts_service.get_term_display(status_code, code_system)
                                if cts_result and cts_result != status_code:
                                    status = cts_result
                                    break
                            except Exception as cts_error:
                                self.logger.warning(f"CTS resolution failed for status {status_code}: {cts_error}")
                        
                        # Priority 2: Resolve text reference (more reliable than displayName)
                        text_elem = status_obs.find('hl7:text', self.namespaces)
                        if text_elem is not None:
                            ref_elem = text_elem.find('hl7:reference', self.namespaces)
                            if ref_elem is not None:
                                ref_value = ref_elem.get('value', '')
                                resolved_text = self._resolve_text_reference(observation, ref_value)
                                if resolved_text and resolved_text != ref_value:
                                    status = resolved_text
                                    break
                        
                        # Priority 3: Handle known displayName issues and code mappings
                        if status_display == "Inctive":  # Handle CDA typo
                            status_display = "Inactive"
                        
                        # Map clinical codes to proper status values
                        status_mappings = {
                            'active': 'Active',
                            'inactive': 'Inactive', 
                            'resolved': 'Resolved',
                            'entered-in-error': 'Entered in Error',
                            'confirmed': 'Confirmed',
                            'unconfirmed': 'Unconfirmed',
                            'provisional': 'Provisional'
                        }
                        
                        if status_code in status_mappings:
                            status = status_mappings[status_code]
                        else:
                            status = status_display or status_code.title()
                        break
        
        # Fallback: Check parent act statusCode (concern-level status)
        if status == "Active":
            # Find parent act using proper namespace handling
            current = observation
            for _ in range(5):  # Search up to 5 levels
                parent = current.getparent() if hasattr(current, 'getparent') else None
                if parent is None:
                    break
                if parent.tag.endswith('}act'):
                    status_code_elem = parent.find('hl7:statusCode', self.namespaces)
                    if status_code_elem is not None:
                        act_status = status_code_elem.get('code', '').lower()
                        act_mappings = {
                            'active': 'Active',
                            'suspended': 'Suspended',
                            'aborted': 'Aborted',
                            'completed': 'Completed'
                        }
                        if act_status in act_mappings:
                            status = act_mappings[act_status]
                            break
                current = parent

        # 8. Extract Certainty (code="66455-7")
        certainty = "Confirmed"
        certainty_relations = observation.findall('.//hl7:entryRelationship[@typeCode="SUBJ"]', self.namespaces)
        for rel in certainty_relations:
            certainty_obs = rel.find('hl7:observation', self.namespaces)
            if certainty_obs is not None:
                code_elem = certainty_obs.find('hl7:code', self.namespaces)
                if code_elem is not None and code_elem.get('code') == '66455-7':
                    certainty_value = certainty_obs.find('hl7:value', self.namespaces)
                    if certainty_value is not None:
                        certainty = certainty_value.get('displayName', certainty_value.get('code', 'Confirmed'))
                        
                        # Resolve text reference for certainty
                        text_elem = certainty_obs.find('hl7:text', self.namespaces)
                        if text_elem is not None:
                            ref_elem = text_elem.find('hl7:reference', self.namespaces)
                            if ref_elem is not None:
                                ref_value = ref_elem.get('value', '')
                                resolved_text = self._resolve_text_reference(observation, ref_value)
                                if resolved_text and resolved_text != ref_value:
                                    certainty = resolved_text

        # 9. Extract Process of Establishing Problem
        process_info = "Not specified"
        # Look for manifestation observation's code for process information
        if mfst_entry is not None:
            mfst_obs = mfst_entry.find('hl7:observation', self.namespaces)
            if mfst_obs is not None:
                process_code = mfst_obs.find('hl7:code', self.namespaces)
                if process_code is not None:
                    process_info = process_code.get('displayName', '')
                    
                    # Resolve text reference for process
                    original_text = process_code.find('hl7:originalText', self.namespaces)
                    if original_text is not None:
                        ref_elem = original_text.find('hl7:reference', self.namespaces)
                        if ref_elem is not None:
                            ref_value = ref_elem.get('value', '')
                            resolved_text = self._resolve_text_reference(observation, ref_value)
                            if resolved_text and resolved_text != ref_value:
                                process_info = resolved_text
                    
                    if not process_info:
                        process_info = "Finding reported by subject or history provider"
        
        self.logger.debug(f"[ALLERGIES SERVICE] Parsed comprehensive allergy data:")
        self.logger.debug(f"  - Reaction Type: {reaction_type}")
        self.logger.debug(f"  - Agent: {agent}")
        self.logger.debug(f"  - Manifestation: {manifestation}")
        self.logger.debug(f"  - Time: {time_info}")
        self.logger.debug(f"  - Severity: {severity}")
        self.logger.debug(f"  - Criticality: {criticality}")
        self.logger.debug(f"  - Status: {status}")
        self.logger.debug(f"  - Certainty: {certainty}")
        self.logger.debug(f"  - Process: {process_info}")
        
        return {
            'substance': agent,  # Main allergen for backward compatibility
            'reaction_type': reaction_type,
            'clinical_manifestation': manifestation,
            'agent': agent,
            'time': time_info,
            'severity': severity,
            'criticality': criticality,
            'status': status,
            'certainty': certainty,
            'process_establishing': process_info,
            'reaction': manifestation,  # Backward compatibility
            'onset_date': time_info,   # Backward compatibility
            'verification_status': certainty  # Backward compatibility
        }
    
    def _resolve_text_reference(self, observation, ref_value: str) -> str:
        """Resolve text reference to actual content from CDA text section."""
        if not ref_value or not ref_value.startswith('#'):
            return ref_value
        
        # Remove the # prefix to get the ID
        target_id = ref_value[1:]
        
        # Try to find the referenced element in the parent section
        # Walk up to find the section element
        current = observation
        section = None
        for _ in range(10):  # Limit search depth
            parent = current.getparent() if hasattr(current, 'getparent') else None
            if parent is None:
                break
            if parent.tag.endswith('section'):
                section = parent
                break
            current = parent
        
        if section is not None:
            # Look for element with matching ID in the text section
            text_section = section.find('hl7:text', self.namespaces)
            if text_section is not None:
                # Search for elements with matching ID
                for elem in text_section.iter():
                    if elem.get('ID') == target_id:
                        # Return the text content, handling nested elements
                        text_content = ''.join(elem.itertext()).strip()
                        return text_content if text_content else ref_value
        
        return ref_value
    
    def _map_substance_code_to_description(self, code: str, code_system: str) -> str:
        """Map substance codes to human-readable descriptions."""
        if not code:
            return ""
        
        # SNOMED CT substance codes (2.16.840.1.113883.6.96)
        snomed_substances = {
            '260176001': 'Kiwi fruit',
            '47703008': 'Lactose',
            '111088007': 'Latex',
            '387207008': 'Aspirin',
            '387517004': 'Paracetamol',
            '387362001': 'Ibuprofen',
            '226760005': 'Dairy products',
            '412061001': 'Shellfish',
            '412062008': 'Tree nuts',
            '762952008': 'Peanuts',
            '227493005': 'Cashew nuts',
            '102261002': 'Almonds',
            '256306003': 'Penicillin',
            '387467008': 'Codeine',
            '387248006': 'Morphine',
            '372687004': 'Amoxicillin',
            '387467008': 'Codeine',
            '226355009': 'Bee venom',
            '260147004': 'Animal dander',
            '226916002': 'House dust mite',
            '226934003': 'Pollen',
            '762706009': 'Tree pollen',
            '256277009': 'Grass pollen',
            '440037006': 'Contrast media',
            '387585008': 'Sulfonamides',
            '14443002': 'Eggs',
            '226529007': 'Fish',
            '226553002': 'Nuts',
            '260170001': 'Strawberry',
            '260174005': 'Chocolate'
        }
        
        if code_system == '2.16.840.1.113883.6.96':
            description = snomed_substances.get(code)
            if description:
                return description
        
        # ATC codes (Anatomical Therapeutic Chemical Classification) - 2.16.840.1.113883.6.73
        atc_substances = {
            'N02BA01': 'acetylsalicylic acid',  # Aspirin - matches CDA document
            'N02BE01': 'Paracetamol',
            'M01AE01': 'Ibuprofen',
            'J01CA04': 'Amoxicillin',
            'J01AA02': 'Doxycycline',
            'N02AA01': 'Morphine',
            'N02AA05': 'Oxycodone',
            'J01CR02': 'Co-amoxiclav',
            'J01FA09': 'Clarithromycin',
            'N03AX16': 'Pregabalin',
            'N05BA12': 'Alprazolam'
        }
        
        # Check various ATC code systems
        if code_system == '2.16.840.1.113883.6.73' or 'atc' in code_system.lower() or code.startswith(('A', 'B', 'C', 'D', 'G', 'H', 'J', 'L', 'M', 'N', 'P', 'R', 'S', 'V')):
            description = atc_substances.get(code)
            if description:
                return description
        
        return ""
    
    def _map_reaction_code_to_description(self, code: str, code_system: str) -> str:
        """Map reaction codes to human-readable descriptions."""
        if not code:
            return ""
        
        # SNOMED CT reaction codes (2.16.840.1.113883.6.96)
        snomed_reactions = {
            '43116000': 'Eczema',       # From Portuguese CDA
            '62315008': 'Diarrhea',     # From Portuguese CDA
            '195967001': 'Asthma',      # From Portuguese CDA
            '126485001': 'Urticaria',   # From Portuguese CDA
            '422587007': 'Nausea',
            '422400008': 'Vomiting',
            '418363000': 'Itching',
            '271807003': 'Skin rash',
            '247472004': 'Hives',
            '267036007': 'Dyspnea (difficulty breathing)',
            '70076002': 'Bronchospasm',
            '162290004': 'Dry mouth',
            '25064002': 'Headache',
            '404640003': 'Dizziness',
            '426000000': 'Fever',
            '39579001': 'Anaphylactic shock',
            '49727002': 'Cough',
            '91175000': 'Seizure',
            '386661006': 'Fever',
            '418290006': 'Itching',
            '271757001': 'Papular rash',
            '271759003': 'Bullous rash',
            '23924001': 'Tight chest',
            '21522001': 'Abdominal pain',
            '73430006': 'Sleep disturbance',
            '386033004': 'Nausea and vomiting',
            '410429000': 'Cardiac arrest',
            '230145002': 'Difficulty breathing',
            '24484000': 'Severe headache',
            '386661006': 'Fever',
            '271759003': 'Vesicular rash',
            '418799008': 'Finding reported by subject or history provider'  # Process code
        }
        
        if code_system == '2.16.840.1.113883.6.96':
            description = snomed_reactions.get(code)
            if description:
                return description
        
        # ICD-10 reaction codes if present
        icd10_reactions = {
            'T78.0': 'Anaphylactic shock',
            'T78.1': 'Other adverse food reactions',
            'T78.2': 'Anaphylactic shock, unspecified',
            'T78.3': 'Angioneurotic edema',
            'T78.4': 'Allergy, unspecified',
            'L20': 'Atopic dermatitis',
            'L23': 'Allergic contact dermatitis',
            'L50': 'Urticaria'
        }
        
        if 'icd' in code_system.lower():
            description = icd10_reactions.get(code)
            if description:
                return description
        
        return ""
    
    def _get_substance_description(self, code: str, code_system: str) -> str:
        """Get substance description, potentially using CTS integration."""
        # Try CTS integration first for real-time resolution
        try:
            from ..cts_integration import cts_service
            cts_description = cts_service.resolve_code(code, code_system)
            if cts_description:
                self.logger.debug(f"[ALLERGIES SERVICE] CTS resolved {code} -> {cts_description}")
                return cts_description
        except ImportError:
            self.logger.debug("[ALLERGIES SERVICE] CTS integration not available")
        except Exception as e:
            self.logger.warning(f"[ALLERGIES SERVICE] CTS resolution failed for {code}: {e}")
        
        # Fallback to local mapping
        description = self._map_substance_code_to_description(code, code_system)
        
        if description:
            return description
        
        # If no mapping found, return a formatted version of the code
        if code:
            return f"Substance ({code})"
        
        return "Unknown allergen"
    
    def _format_cda_date(self, date_str: str) -> str:
        """Format CDA date string to readable format."""
        if not date_str or date_str == "Not specified":
            return date_str
        
        try:
            # Remove any non-digit characters for processing
            clean_date = ''.join(filter(str.isdigit, date_str))
            
            if len(clean_date) >= 8:  # YYYYMMDD
                year = clean_date[:4]
                month = clean_date[4:6]
                day = clean_date[6:8]
                return f"{year}-{month}-{day}"
            elif len(clean_date) == 4:  # YYYY
                return clean_date
            elif len(clean_date) == 6:  # YYYYMM
                year = clean_date[:4]
                month = clean_date[4:6]
                return f"{year}-{month}"
            else:
                return date_str
        except Exception as e:
            self.logger.warning(f"[ALLERGIES SERVICE] Date formatting error for '{date_str}': {e}")
            return date_str