"""
Allergies Section Service

Specialized service agent for allergies and intolerances clinical data processing.
Implements the ClinicalSectionServiceInterface for consistent pipeline integration.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from .clinical_sections.pipeline.clinical_data_pipeline_manager import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class AllergiesSectionService(ClinicalSectionServiceInterface):
    """
    Specialized service for allergies and intolerances section data processing.
    
    Handles:
    - Food allergies and intolerances  
    - Medication allergies
    - Environmental allergies
    - Severity assessment
    - Reaction documentation
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
            logger.info(f"[ALLERGIES SERVICE] Found {len(enhanced_allergies)} enhanced allergies in session")
            return enhanced_allergies
        
        # Check for clinical arrays allergies
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        allergies_data = clinical_arrays.get('allergies', [])
        
        if allergies_data:
            logger.info(f"[ALLERGIES SERVICE] Found {len(allergies_data)} allergies in clinical arrays")
            return allergies_data
        
        logger.info("[ALLERGIES SERVICE] No allergies data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract allergies from CDA content using specialized parsing with problems cross-reference."""
        try:
            # Use lxml for better XPath support like other successful services
            try:
                from lxml import etree
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(cda_content.encode('utf-8'), parser)
                logger.info("[ALLERGIES SERVICE] Using lxml for XML parsing")
            except ImportError:
                # Use defusedxml as recommended by security best practices
                try:
                    from defusedxml import ElementTree as ET
                    root = ET.fromstring(cda_content)
                    logger.info("[ALLERGIES SERVICE] Using defusedxml for XML parsing")
                except ImportError:
                    from defusedxml import ElementTree as ET
                    root = ET.fromstring(cda_content)
                    logger.info("[ALLERGIES SERVICE] Using xml.etree for XML parsing")
            
            # Find allergies section
            namespaces = {'hl7': 'urn:hl7-org:v3'}
            
            # Find allergies sections by code
            sections = root.xpath('.//hl7:section[hl7:code[@code="48765-2"]]', namespaces=namespaces) if hasattr(root, 'xpath') else root.findall('.//hl7:section', namespaces)
            
            if not sections and hasattr(root, 'xpath'):
                # Try broader search
                sections = root.xpath('.//hl7:section', namespaces=namespaces)
                sections = [s for s in sections if s.find('hl7:code', namespaces) is not None and s.find('hl7:code', namespaces).get('code') == '48765-2']
            
            if not sections:
                # Fallback to element tree approach
                sections = root.findall('.//hl7:section', namespaces)
                sections = [s for s in sections if s.find('hl7:code', namespaces) is not None and s.find('hl7:code', namespaces).get('code') == '48765-2']
            
            allergies = []
            for section in sections:
                # Parse allergies section
                section_allergies = self._parse_allergies_xml(section)
                allergies.extend(section_allergies)
            
            # NEW: Cross-reference with Problems section for temporal data
            enhanced_allergies = self._cross_reference_with_problems(root, allergies, namespaces)
            
            logger.info(f"[ALLERGIES SERVICE] Extracted {len(enhanced_allergies)} allergies from CDA")
            return enhanced_allergies
            
        except Exception as e:
            logger.error(f"[ALLERGIES SERVICE] Error extracting allergies from CDA: {e}")
            import traceback
            logger.error(f"[ALLERGIES SERVICE] Traceback: {traceback.format_exc()}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance allergies data and store in session."""
        enhanced_allergies = []
        
        for allergy_data in raw_data:
            # Apply enhancement pattern following medications model
            enhanced_allergy = {
                'allergen': self._extract_field_value(allergy_data, 'allergen', 'Unknown allergen'),
                'display_name': self._extract_field_value(allergy_data, 'allergen', 'Unknown allergen'),
                'type': self._extract_field_value(allergy_data, 'type', 'Allergy'),
                'reaction': self._extract_field_value(allergy_data, 'reaction', 'Unknown reaction'),
                'severity': self._extract_field_value(allergy_data, 'severity', 'Not specified'),
                'status': self._extract_field_value(allergy_data, 'status', 'Active'),
                'date_identified': self._extract_field_value(allergy_data, 'date', 'Not specified'),
                'notes': self._extract_field_value(allergy_data, 'notes', ''),
                'source': 'cda_extraction_enhanced'
            }
            enhanced_allergies.append(enhanced_allergy)
        
        # Store in session using consistent pattern
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_allergies'] = enhanced_allergies
        request.session[session_key] = match_data
        request.session.modified = True
        
        logger.info(f"[ALLERGIES SERVICE] Enhanced and stored {len(enhanced_allergies)} allergies")
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
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Strategy 1: Extract from narrative paragraphs
        text_section = section.find('.//hl7:text', namespaces) or section.find('.//text')
        if text_section is not None:
            paragraphs = text_section.findall('.//hl7:paragraph', namespaces) or text_section.findall('.//paragraph')
            
            for paragraph in paragraphs:
                text = self._extract_text_from_element(paragraph)
                if text and ('allergy' in text.lower() or 'intolerance' in text.lower()):
                    allergy = self._parse_allergy_narrative(text)
                    if allergy:
                        allergies.append(allergy)
        
        # Strategy 2: Extract from table-based data (NEW - COMPREHENSIVE TABLE EXTRACTION)
        if text_section is not None:
            table_allergies = self._extract_table_allergies(text_section)
            allergies.extend(table_allergies)
        
        # Strategy 3: Extract from structured entries
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                allergy = self._parse_allergy_observation(observation)
                if allergy:
                    allergies.append(allergy)
        
        return allergies
    
    def _extract_table_allergies(self, text_section) -> List[Dict[str, Any]]:
        """Extract allergies from table-based structures in CDA narrative text."""
        allergies = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Find all tables in the text section
        tables = text_section.findall('.//hl7:table', namespaces) or text_section.findall('.//table')
        
        for table in tables:
            table_allergies = self._parse_allergy_table(table)
            allergies.extend(table_allergies)
        
        logger.info(f"[ALLERGIES SERVICE] Extracted {len(allergies)} allergies from table structures")
        return allergies
    
    def _parse_allergy_table(self, table) -> List[Dict[str, Any]]:
        """Parse individual allergy table to extract allergy data."""
        allergies = []
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Get all table rows
        rows = table.findall('.//hl7:tr', namespaces) or table.findall('.//tr')
        
        # Skip header row (usually first row)
        data_rows = rows[1:] if len(rows) > 1 else rows
        
        for row in data_rows:
            # Get all cells in the row
            cells = row.findall('.//hl7:td', namespaces) or row.findall('.//td')
            
            if len(cells) >= 2:
                # Extract text from cells
                cell_texts = []
                for cell in cells:
                    cell_text = self._extract_text_from_element(cell)
                    cell_texts.append(cell_text.strip() if cell_text else "")
                
                # Filter out empty or header-like rows
                if cell_texts and not any(header in cell_texts[0].lower() for header in ['allergen', 'substance', 'agent', 'type']):
                    # First cell typically contains allergen/agent
                    # Second cell typically contains reaction/manifestation
                    allergen = cell_texts[0] if cell_texts[0] else "Unknown Allergen"
                    reaction = cell_texts[1] if len(cell_texts) > 1 and cell_texts[1] else "Not specified"
                    
                    # Additional fields if more columns exist
                    severity = cell_texts[2] if len(cell_texts) > 2 and cell_texts[2] else "Not specified"
                    status = cell_texts[3] if len(cell_texts) > 3 and cell_texts[3] else "Active"
                    
                    # Create comprehensive allergy data with all clinical fields
                    allergy_data = {
                        'allergen': allergen,
                        'agent': allergen,  # Alias for template compatibility
                        'substance': allergen,  # Another alias
                        'name': allergen,  # Template expects this field
                        'display_name': allergen,
                        'type': self._determine_allergy_type(allergen),
                        'reaction': reaction,
                        'clinical_manifestation': reaction,  # Alias for template
                        'severity': severity,
                        'status': status,
                        'date': 'Not specified',
                        'date_identified': 'Not specified',
                        'time': self._extract_time_from_context(cell_texts),  # NEW: Extract time if present
                        'criticality': self._determine_criticality_from_context(cell_texts, severity),  # NEW: Enhanced criticality
                        'certainty': self._determine_certainty_from_context(cell_texts),  # NEW: Extract certainty
                        'process': 'Finding reported by subject or history provider',
                        'reaction_type': 'Propensity to adverse reaction',
                        'source': 'table_extraction_enhanced',
                        'enhanced_data': True
                    }
                    
                    allergies.append(allergy_data)
                    logger.info(f"[ALLERGIES SERVICE] Table extraction found: {allergen} -> {reaction}")
        
        return allergies
    
    def _determine_allergy_type(self, allergen: str) -> str:
        """Determine allergy type based on allergen name."""
        allergen_lower = allergen.lower()
        
        # Food allergies
        food_terms = ['kiwi', 'nut', 'milk', 'egg', 'soy', 'wheat', 'shellfish', 'fish', 'lactose', 'gluten']
        if any(term in allergen_lower for term in food_terms):
            return 'Food allergy'
        
        # Medication allergies
        medication_terms = ['penicillin', 'aspirin', 'ibuprofen', 'antibiotic', 'medication', 'drug']
        if any(term in allergen_lower for term in medication_terms):
            return 'Medication allergy'
        
        # Environmental allergies
        environmental_terms = ['pollen', 'dust', 'mold', 'pet', 'latex', 'insect']
        if any(term in allergen_lower for term in environmental_terms):
            return 'Environmental allergy'
        
        return 'Allergy'
    
    def _determine_criticality(self, severity: str) -> str:
        """Map severity to criticality level."""
        severity_lower = severity.lower()
        
        if 'severe' in severity_lower or 'high' in severity_lower:
            return 'high risk'
        elif 'moderate' in severity_lower or 'medium' in severity_lower:
            return 'medium risk'
        elif 'mild' in severity_lower or 'low' in severity_lower:
            return 'low risk'
        else:
            return 'unknown risk'
    
    def _extract_time_from_context(self, cell_texts: List[str]) -> str:
        """Extract time information from table cell context."""
        import re
        
        for text in cell_texts:
            if not text:
                continue
            
            # Look for date patterns like "since YYYY-MM-DD", "from YYYY until YYYY"
            date_patterns = [
                r'since\s+(\d{4}-\d{2}-\d{2})',
                r'since\s+(\d{4})',
                r'from\s+(\d{4})\s+until\s+(\d{4})',
                r'between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    if 'since' in text.lower():
                        return f"since {match.group(1)}"
                    elif 'from' in text.lower() and 'until' in text.lower():
                        if len(match.groups()) >= 2:
                            return f"from {match.group(1)} until {match.group(2)}"
                    elif 'between' in text.lower() and 'and' in text.lower():
                        if len(match.groups()) >= 2:
                            return f"from {match.group(1)} until {match.group(2)}"
                    else:
                        return f"since {match.group(1)}"
        
        return "Not specified"
    
    def _determine_criticality_from_context(self, cell_texts: List[str], severity: str) -> str:
        """Determine criticality from table context and severity."""
        # First check if criticality is explicitly mentioned in cells
        for text in cell_texts:
            if not text:
                continue
            text_lower = text.lower()
            
            if 'high risk' in text_lower or 'critical' in text_lower:
                return 'high risk'
            elif 'low risk' in text_lower or 'minimal' in text_lower:
                return 'low risk'
            elif 'medium risk' in text_lower or 'moderate risk' in text_lower:
                return 'medium risk'
        
        # Fallback to severity-based mapping
        return self._determine_criticality(severity)
    
    def _determine_certainty_from_context(self, cell_texts: List[str]) -> str:
        """Determine certainty from table context."""
        for text in cell_texts:
            if not text:
                continue
            text_lower = text.lower()
            
            if 'confirmed' in text_lower or 'certain' in text_lower:
                return 'confirmed'
            elif 'suspected' in text_lower or 'possible' in text_lower:
                return 'suspected'
            elif 'probable' in text_lower or 'likely' in text_lower:
                return 'probable'
            elif 'uncertain' in text_lower or 'unknown' in text_lower:
                return 'uncertain'
        
        # Default to confirmed for patient-reported allergies
        return 'confirmed'
    
    def _parse_allergy_narrative(self, text: str) -> Dict[str, Any]:
        """Parse allergy information from narrative text."""
        allergen = "Unknown"
        reaction = "Unknown"
        allergy_type = "Unknown"
        status = "Active"
        
        # Handle format: "Kiwi fruit - eczema (Unknown Severity)"
        if ' - ' in text and '(' in text:
            parts = text.split(' - ')
            if len(parts) >= 2:
                allergen = parts[0].strip()
                reaction_part = parts[1].split('(')[0].strip()
                reaction = reaction_part
        
        # Extract allergen
        elif 'allergy to' in text.lower():
            parts = text.lower().split('allergy to')
            if len(parts) > 1:
                allergen_part = parts[1].split(',')[0].strip()
                allergen = allergen_part.title()
        elif 'intolerance to' in text.lower():
            parts = text.lower().split('intolerance to')
            if len(parts) > 1:
                allergen_part = parts[1].split(',')[0].strip()
                allergen = allergen_part.title()
        
        # Extract reaction
        if reaction == "Unknown" and 'reaction:' in text.lower():
            reaction_part = text.lower().split('reaction:')[1].strip()
            reaction = reaction_part.title()
        
        # Determine allergy type
        if 'food' in text.lower():
            allergy_type = "Food allergy"
        elif 'medication' in text.lower():
            allergy_type = "Medication allergy"
        elif 'intolerance' in text.lower():
            allergy_type = "Food intolerance"
        else:
            allergy_type = "Allergy"
        
        return {
            'allergen': allergen,
            'type': allergy_type,
            'reaction': reaction,
            'status': status,
            'severity': 'Not specified',
            'date': 'Not specified'
        }
    
    def _parse_allergy_observation(self, observation) -> Dict[str, Any]:
        """Parse allergy information from structured observation element with complete CDA fields."""
        namespaces = {'hl7': 'urn:hl7-org:v3'}
        
        # Extract participant (allergen)
        allergen = "Unknown"
        participant = observation.find('.//hl7:participant', namespaces)
        if participant is not None:
            code_elem = participant.find('.//hl7:code', namespaces)
            if code_elem is not None:
                allergen = code_elem.get('displayName', code_elem.get('code', 'Unknown'))
        
        # Extract value (reaction type) - improved to check entryRelationship
        reaction = "Unknown"
        value_elem = observation.find('hl7:value', namespaces)
        if value_elem is not None:
            reaction = value_elem.get('displayName', value_elem.get('code', 'Unknown'))
        
        # Also check entryRelationship for manifestation (MFST)
        if reaction == "Unknown":
            for entry_rel in observation.findall('.//hl7:entryRelationship', namespaces):
                if entry_rel.get('typeCode') == 'MFST':
                    mfst_obs = entry_rel.find('hl7:observation', namespaces)
                    if mfst_obs is not None:
                        mfst_code = mfst_obs.find('hl7:code', namespaces)
                        if mfst_code is not None:
                            reaction = mfst_code.get('displayName', mfst_code.get('code', 'Unknown'))
                            break
        
        # Extract severity - fix XPath syntax for lxml
        severity = "Not specified"
        # Find observation with code="SEV" using proper lxml syntax
        for sev_obs in observation.findall('.//hl7:observation', namespaces):
            code_elem = sev_obs.find('hl7:code', namespaces)
            if code_elem is not None and code_elem.get('code') == 'SEV':
                severity_value = sev_obs.find('hl7:value', namespaces)
                if severity_value is not None:
                    severity = severity_value.get('displayName', severity_value.get('code', 'Not specified'))
                break
        
        # NEW: Extract effectiveTime (time when allergy was identified/reported)
        time_identified = "Not specified"
        effective_time = observation.find('hl7:effectiveTime', namespaces)
        if effective_time is not None:
            # Handle different time formats
            time_value = effective_time.get('value')
            if time_value:
                # Convert YYYYMMDD format to readable format
                if len(time_value) >= 8 and time_value.isdigit():
                    formatted_time = f"{time_value[:4]}-{time_value[4:6]}-{time_value[6:8]}"
                    time_identified = f"since {formatted_time}"
                else:
                    time_identified = time_value
            else:
                # Check for low/high time ranges
                low_elem = effective_time.find('hl7:low', namespaces)
                high_elem = effective_time.find('hl7:high', namespaces)
                if low_elem is not None and high_elem is not None:
                    low_val = low_elem.get('value', '')
                    high_val = high_elem.get('value', '')
                    if low_val and high_val:
                        low_formatted = self._format_date(low_val)
                        high_formatted = self._format_date(high_val)
                        time_identified = f"from {low_formatted} until {high_formatted}"
                elif low_elem is not None:
                    low_val = low_elem.get('value', '')
                    if low_val:
                        low_formatted = self._format_date(low_val)
                        time_identified = f"since {low_formatted}"
        
        # NEW: Extract criticality
        criticality = "Unknown risk"
        # Look for criticality in entryRelationship observations
        for entry_rel in observation.findall('.//hl7:entryRelationship', namespaces):
            crit_obs = entry_rel.find('hl7:observation', namespaces)
            if crit_obs is not None:
                code_elem = crit_obs.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') in ['CRIT', 'criticality', '82606-5']:
                    crit_value = crit_obs.find('hl7:value', namespaces)
                    if crit_value is not None:
                        crit_display = crit_value.get('displayName', crit_value.get('code', ''))
                        if 'high' in crit_display.lower():
                            criticality = "high risk"
                        elif 'low' in crit_display.lower():
                            criticality = "low risk"
                        elif 'medium' in crit_display.lower() or 'moderate' in crit_display.lower():
                            criticality = "medium risk"
                        else:
                            criticality = crit_display.lower() if crit_display else "Unknown risk"
        
        # NEW: Extract certainty/confidence
        certainty = "Unknown"
        # Look for certainty in statusCode or other attributes
        status_code = observation.find('hl7:statusCode', namespaces)
        if status_code is not None:
            status_val = status_code.get('code', '')
            if status_val == 'completed':
                certainty = "confirmed"
            elif status_val == 'active':
                certainty = "confirmed"
            elif status_val in ['uncertain', 'provisional']:
                certainty = "uncertain"
        
        # Look for certainty code in observations
        for cert_obs in observation.findall('.//hl7:observation', namespaces):
            code_elem = cert_obs.find('hl7:code', namespaces)
            if code_elem is not None and code_elem.get('code') in ['CONF', 'certainty', '103332005']:
                cert_value = cert_obs.find('hl7:value', namespaces)
                if cert_value is not None:
                    certainty = cert_value.get('displayName', cert_value.get('code', 'Unknown'))
        
        # NEW: Extract status (active/resolved/suspended)
        status = "active"
        # Check for problem status in entryRelationship
        for entry_rel in observation.findall('.//hl7:entryRelationship', namespaces):
            status_obs = entry_rel.find('hl7:observation', namespaces)
            if status_obs is not None:
                code_elem = status_obs.find('hl7:code', namespaces)
                if code_elem is not None and code_elem.get('code') in ['33999-4', 'status']:
                    status_value = status_obs.find('hl7:value', namespaces)
                    if status_value is not None:
                        status_display = status_value.get('displayName', status_value.get('code', ''))
                        if status_display:
                            status = status_display.lower()
        
        return {
            'allergen': allergen,
            'agent': allergen,  # Template compatibility
            'name': allergen,   # Template expects this
            'display_name': allergen,
            'type': 'Allergy',
            'reaction': reaction,
            'clinical_manifestation': reaction,  # Template compatibility
            'status': status,
            'severity': severity,
            'time': time_identified,
            'date': time_identified,
            'date_identified': time_identified,
            'criticality': criticality,
            'certainty': certainty,
            'process': 'Finding reported by subject or history provider',  # Standard for patient-reported
            'reaction_type': 'Propensity to adverse reaction',
            'source': 'structured_cda_observation',
            'enhanced_data': True
        }
    
    def _format_date(self, date_str: str) -> str:
        """Format CDA date string to readable format."""
        if not date_str:
            return "Not specified"
        
        # Handle YYYYMMDD format
        if len(date_str) >= 8 and date_str[:8].isdigit():
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        # Handle YYYY format
        if len(date_str) == 4 and date_str.isdigit():
            return date_str
        
        return date_str
    
    def _cross_reference_with_problems(self, root, allergies: List[Dict[str, Any]], namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """Cross-reference allergies with problems section to get temporal and status data."""
        try:
            # Find problems section (Problem List - code 11450-4)
            problem_sections = []
            if hasattr(root, 'xpath'):
                problem_sections = root.xpath('.//hl7:section[hl7:code[@code="11450-4"]]', namespaces=namespaces)
            
            if not problem_sections:
                # Fallback search
                all_sections = root.findall('.//hl7:section', namespaces)
                problem_sections = [s for s in all_sections if s.find('hl7:code', namespaces) is not None and s.find('hl7:code', namespaces).get('code') == '11450-4']
            
            if not problem_sections:
                logger.info("[ALLERGIES SERVICE] No problems section found for cross-reference")
                return allergies
            
            # Extract allergy-related problems
            allergy_problems = {}
            for section in problem_sections:
                problems = self._extract_allergy_related_problems(section, namespaces)
                for problem in problems:
                    # Map by reaction/manifestation name
                    reaction = problem.get('reaction', '').lower()
                    if reaction:
                        allergy_problems[reaction] = problem
            
            logger.info(f"[ALLERGIES SERVICE] Found {len(allergy_problems)} allergy-related problems for cross-reference")
            
            # Enhance allergies with problems data
            enhanced_allergies = []
            for allergy in allergies:
                enhanced_allergy = allergy.copy()
                reaction = allergy.get('reaction', '').lower()
                
                # Cross-reference with problems
                if reaction in allergy_problems:
                    problem = allergy_problems[reaction]
                    
                    # Add temporal data from problems
                    if problem.get('onset'):
                        enhanced_allergy['time'] = self._format_problem_onset(problem['onset'])
                        enhanced_allergy['date'] = enhanced_allergy['time']
                        enhanced_allergy['date_identified'] = enhanced_allergy['time']
                    
                    # Add status from problems
                    if problem.get('status'):
                        enhanced_allergy['status'] = problem['status'].lower()
                    
                    # Add severity if available
                    if problem.get('severity') and problem['severity'] != 'Not specified':
                        enhanced_allergy['severity'] = problem['severity']
                    
                    # Determine criticality based on enhanced data
                    if enhanced_allergy.get('severity'):
                        enhanced_allergy['criticality'] = self._determine_criticality(enhanced_allergy['severity'])
                    
                    # Set certainty based on problems source
                    enhanced_allergy['certainty'] = 'confirmed'
                    enhanced_allergy['process'] = 'Finding reported by subject or history provider'
                    
                    logger.info(f"[ALLERGIES SERVICE] Enhanced {allergy.get('allergen')} with problems data: time={enhanced_allergy.get('time')}, status={enhanced_allergy.get('status')}")
                
                enhanced_allergies.append(enhanced_allergy)
            
            return enhanced_allergies
            
        except Exception as e:
            logger.error(f"[ALLERGIES SERVICE] Error in cross-reference: {e}")
            return allergies
    
    def _extract_allergy_related_problems(self, section, namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract allergy-related problems from problems section."""
        problems = []
        
        # Strategy 1: Look for narrative paragraphs with allergy terms
        text_section = section.find('.//hl7:text', namespaces) or section.find('.//text')
        if text_section is not None:
            paragraphs = text_section.findall('.//hl7:paragraph', namespaces) or text_section.findall('.//paragraph')
            
            for paragraph in paragraphs:
                text = self._extract_text_from_element(paragraph)
                if text and self._is_allergy_related_problem(text):
                    problem = self._parse_problem_narrative(text)
                    if problem:
                        problems.append(problem)
        
        # Strategy 2: Look for structured entries
        entries = section.findall('.//hl7:entry', namespaces)
        for entry in entries:
            observation = entry.find('.//hl7:observation', namespaces)
            if observation is not None:
                problem = self._parse_problem_observation(observation, namespaces)
                if problem and self._is_allergy_related_problem(problem.get('name', '')):
                    problems.append(problem)
        
        return problems
    
    def _is_allergy_related_problem(self, text: str) -> bool:
        """Check if a problem is allergy-related."""
        allergy_terms = [
            'allergy', 'allergic', 'asthma', 'eczema', 'urticaria', 'reaction',
            'intolerance', 'hypersensitivity', 'dermatitis', 'rhinitis'
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in allergy_terms)
    
    def _parse_problem_narrative(self, text: str) -> Dict[str, Any]:
        """Parse problem information from narrative text."""
        import re
        
        # Extract problem name (usually at the beginning)
        problem_name = text.split(',')[0].split(' since')[0].split(' from')[0].strip()
        
        # Extract onset date
        onset = None
        date_patterns = [
            r'since\s+(\d{4}-\d{2}-\d{2})',
            r'since\s+(\d{4})',
            r'from\s+(\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                onset = match.group(1)
                break
        
        # Determine reaction type
        reaction = 'Unknown'
        if 'asthma' in text.lower():
            reaction = 'asthma'
        elif 'eczema' in text.lower():
            reaction = 'eczema'
        elif 'urticaria' in text.lower():
            reaction = 'urticaria'
        elif 'diarrhea' in text.lower():
            reaction = 'diarrhea'
        
        return {
            'name': problem_name,
            'reaction': reaction,
            'onset': onset,
            'status': 'active',  # Default from problems
            'severity': 'Not specified',
            'source': 'problems_narrative'
        }
    
    def _parse_problem_observation(self, observation, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse problem from structured observation."""
        # Extract problem name/code
        name = "Unknown"
        value_elem = observation.find('hl7:value', namespaces)
        if value_elem is not None:
            name = value_elem.get('displayName', value_elem.get('code', 'Unknown'))
        
        # Extract onset from effectiveTime
        onset = None
        effective_time = observation.find('hl7:effectiveTime', namespaces)
        if effective_time is not None:
            low_elem = effective_time.find('hl7:low', namespaces)
            if low_elem is not None:
                onset_val = low_elem.get('value')
                if onset_val:
                    onset = self._format_date(onset_val)
        
        # Extract status
        status = "active"
        status_code = observation.find('hl7:statusCode', namespaces)
        if status_code is not None:
            status_val = status_code.get('code', 'active')
            if status_val == 'completed':
                status = 'active'
        
        return {
            'name': name,
            'reaction': name.lower() if name != 'Unknown' else 'unknown',
            'onset': onset,
            'status': status,
            'severity': 'Not specified',
            'source': 'problems_observation'
        }
    
    def _format_problem_onset(self, onset: str) -> str:
        """Format problem onset to allergy time format."""
        if not onset:
            return "Not specified"
        
        # Handle different formats
        if len(onset) == 8 and onset.isdigit():  # YYYYMMDD
            formatted = f"{onset[:4]}-{onset[4:6]}-{onset[6:8]}"
            return f"since {formatted}"
        elif len(onset) == 4 and onset.isdigit():  # YYYY
            return f"since {onset}"
        elif '-' in onset:  # Already formatted
            return f"since {onset}"
        
        return onset
    
    def _extract_text_from_element(self, element) -> str:
        """Extract clean text from XML element."""
        if element is None:
            return ""
        
        # Try to find content tags first
        content_elements = element.findall('.//content')
        if content_elements:
            text = content_elements[-1].text
            if text and text.strip():
                return text.strip()
        
        # Fallback to element text
        text = element.text
        if text and text.strip():
            return text.strip()
        
        # If no direct text, try to get all text content
        all_text = ''.join(element.itertext()).strip()
        return all_text if all_text else ""
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default: str) -> str:
        """Extract field value handling both flat and nested structures."""
        value = data.get(field_name, default)
        
        if isinstance(value, dict):
            # Handle nested structures like {'value': 'X', 'display_value': 'Y'}
            return value.get('display_value', value.get('value', default))
        
        return str(value) if value else default


# Register the allergies service with the global pipeline manager
from .clinical_sections.pipeline.clinical_data_pipeline_manager import clinical_pipeline_manager
clinical_pipeline_manager.register_service(AllergiesSectionService())