"""
Coded Results Extractor Service

Extracts coded results data from CDA documents with dual structure:
1. Blood Group results (ABO/Rh typing)
2. Diagnostic Results (imaging, lab tests, etc.)

Handles LOINC codes (18748-4, 34530-6, LP6406-5), SNOMED codes (278147001),
performer/author information, and clinical terminology integration.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from translation_services.terminology_translator import TerminologyTranslator


@dataclass
class BloodGroupEntry:
    """Data structure for blood group results"""
    diagnostic_date: Optional[str] = None
    blood_group: Optional[str] = None
    blood_group_code: Optional[str] = None
    blood_group_system: Optional[str] = None
    blood_group_display: Optional[str] = None
    test_code: Optional[str] = None
    test_system: Optional[str] = None
    test_display: Optional[str] = None
    status: Optional[str] = None
    performer_name: Optional[str] = None
    performer_organization: Optional[str] = None
    author_name: Optional[str] = None
    author_organization: Optional[str] = None
    author_time: Optional[str] = None


@dataclass
class DiagnosticResultEntry:
    """Data structure for diagnostic results"""
    diagnostic_date: Optional[str] = None
    result_type: Optional[str] = None
    result_value: Optional[str] = None
    result_code: Optional[str] = None
    result_system: Optional[str] = None
    result_display: Optional[str] = None
    performer_reporter: Optional[str] = None
    performer_organization: Optional[str] = None
    author_name: Optional[str] = None
    author_organization: Optional[str] = None
    author_time: Optional[str] = None
    comment: Optional[str] = None
    status: Optional[str] = None
    interpretation: Optional[str] = None
    reference_range: Optional[str] = None
    method: Optional[str] = None
    target_site: Optional[str] = None


class CodedResultsExtractor:
    """
    Extracts coded results data from CDA documents with CTS integration.
    
    Handles both blood group typing and diagnostic imaging/lab results
    with proper LOINC/SNOMED code resolution.
    """
    
    def __init__(self):
        self.translator = TerminologyTranslator()
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def extract_coded_results(self, cda_root: ET.Element) -> Dict[str, List]:
        """
        Extract all coded results from CDA document.
        
        Returns:
            Dict with 'blood_group' and 'diagnostic_results' lists
        """
        blood_group_results = []
        diagnostic_results = []
        
        try:
            # Find coded results section
            coded_results_section = self._find_coded_results_section(cda_root)
            if coded_results_section is None:
                return {
                    'blood_group': blood_group_results,
                    'diagnostic_results': diagnostic_results
                }
            
            # Extract organizers within the section
            organizers = coded_results_section.findall('.//hl7:organizer', self.namespaces)
            
            for organizer in organizers:
                # Determine type based on code
                organizer_code = self._extract_code_info(organizer)
                
                if self._is_blood_group_organizer(organizer_code):
                    blood_group_entry = self._extract_blood_group_data(organizer)
                    if blood_group_entry:
                        blood_group_results.append(blood_group_entry)
                else:
                    diagnostic_entry = self._extract_diagnostic_result_data(organizer)
                    if diagnostic_entry:
                        diagnostic_results.append(diagnostic_entry)
            
        except Exception as e:
            print(f"Error extracting coded results: {e}")
        
        return {
            'blood_group': blood_group_results,
            'diagnostic_results': diagnostic_results
        }
    
    def _find_coded_results_section(self, cda_root: ET.Element) -> Optional[ET.Element]:
        """Find the coded results section in CDA document"""
        # Look for section with coded results template IDs or codes
        sections = cda_root.findall('.//hl7:section', self.namespaces)
        
        for section in sections:
            # Check for coded results section codes
            code_elem = section.find('./hl7:code', self.namespaces)
            if code_elem is not None:
                code = code_elem.get('code', '')
                # Common codes for laboratory/diagnostic results sections
                if code in ['18725-2', '30954-2', '11502-2', '18748-4']:
                    return section
            
            # Check template IDs for coded results
            template_ids = section.findall('./hl7:templateId', self.namespaces)
            for template_id in template_ids:
                root = template_id.get('root', '')
                if 'coded' in root.lower() or 'result' in root.lower():
                    return section
        
        return None
    
    def _is_blood_group_organizer(self, code_info: Dict) -> bool:
        """Determine if organizer contains blood group data"""
        code = code_info.get('code', '')
        display = code_info.get('display', '').lower()
        
        # LOINC codes for blood typing
        blood_group_codes = ['34530-6', '883-9', '882-1']
        if code in blood_group_codes:
            return True
        
        # Check display name for blood group indicators
        blood_indicators = ['blood group', 'abo', 'rh group', 'blood type']
        return any(indicator in display for indicator in blood_indicators)
    
    def _extract_blood_group_data(self, organizer: ET.Element) -> Optional[BloodGroupEntry]:
        """Extract blood group specific data from organizer"""
        try:
            entry = BloodGroupEntry()
            
            # Extract organizer level information
            organizer_code = self._extract_code_info(organizer)
            entry.test_code = organizer_code.get('code')
            entry.test_system = organizer_code.get('system')
            entry.test_display = organizer_code.get('display')
            
            # Resolve test code with CTS
            if entry.test_code and entry.test_system:
                resolved = self.translator.resolve_code(
                    entry.test_code, entry.test_system
                )
                if resolved.get('display'):
                    entry.test_display = resolved['display']
            
            # Extract status
            entry.status = self._extract_status(organizer)
            
            # Extract performer and author
            performer_info = self._extract_performer_info(organizer)
            entry.performer_name = performer_info.get('name')
            entry.performer_organization = performer_info.get('organization')
            
            author_info = self._extract_author_info(organizer)
            entry.author_name = author_info.get('name')
            entry.author_organization = author_info.get('organization')
            entry.author_time = author_info.get('time')
            
            # Extract blood group value from component observation
            observation = organizer.find('.//hl7:component/hl7:observation', self.namespaces)
            if observation is not None:
                # Extract effective time (diagnostic date)
                entry.diagnostic_date = self._extract_effective_time(observation)
                
                # Extract blood group value
                value_elem = observation.find('./hl7:value', self.namespaces)
                if value_elem is not None:
                    entry.blood_group_code = value_elem.get('code')
                    entry.blood_group_system = value_elem.get('codeSystem')
                    entry.blood_group_display = value_elem.get('displayName')
                    entry.blood_group = entry.blood_group_display or entry.blood_group_code
                    
                    # Resolve blood group code with CTS
                    if entry.blood_group_code and entry.blood_group_system:
                        resolved = self.translator.resolve_code(
                            entry.blood_group_code, entry.blood_group_system
                        )
                        if resolved.get('display'):
                            entry.blood_group = resolved['display']
            
            return entry if entry.blood_group or entry.test_code else None
            
        except Exception as e:
            print(f"Error extracting blood group data: {e}")
            return None
    
    def _extract_diagnostic_result_data(self, organizer: ET.Element) -> Optional[DiagnosticResultEntry]:
        """Extract diagnostic result data from organizer"""
        try:
            entry = DiagnosticResultEntry()
            
            # Extract organizer level information
            organizer_code = self._extract_code_info(organizer)
            entry.result_type = organizer_code.get('display') or organizer_code.get('code')
            
            # Extract status
            entry.status = self._extract_status(organizer)
            
            # Extract performer and author
            performer_info = self._extract_performer_info(organizer)
            entry.performer_reporter = performer_info.get('name')
            entry.performer_organization = performer_info.get('organization')
            
            author_info = self._extract_author_info(organizer)
            entry.author_name = author_info.get('name')
            entry.author_organization = author_info.get('organization')
            entry.author_time = author_info.get('time')
            
            # Extract observation data
            observation = organizer.find('.//hl7:component/hl7:observation', self.namespaces)
            if observation is not None:
                # Extract effective time (diagnostic date)
                entry.diagnostic_date = self._extract_effective_time(observation)
                
                # Extract observation code (result type)
                obs_code = self._extract_code_info(observation)
                if obs_code.get('display'):
                    entry.result_type = obs_code['display']
                entry.result_code = obs_code.get('code')
                entry.result_system = obs_code.get('system')
                entry.result_display = obs_code.get('display')
                
                # Resolve result code with CTS
                if entry.result_code and entry.result_system:
                    resolved = self.translator.resolve_code(
                        entry.result_code, entry.result_system
                    )
                    if resolved.get('display'):
                        entry.result_type = resolved['display']
                
                # Extract value
                value_elem = observation.find('./hl7:value', self.namespaces)
                if value_elem is not None:
                    xsi_type = value_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type', '')
                    
                    if 'CD' in xsi_type or 'CE' in xsi_type:
                        entry.result_value = value_elem.get('displayName') or value_elem.get('code')
                    elif 'PQ' in xsi_type:
                        value = value_elem.get('value', '')
                        unit = value_elem.get('unit', '')
                        entry.result_value = f"{value} {unit}".strip()
                    else:
                        entry.result_value = value_elem.get('value') or value_elem.text
                
                # Extract interpretation
                interp_elem = observation.find('./hl7:interpretationCode', self.namespaces)
                if interp_elem is not None:
                    entry.interpretation = interp_elem.get('displayName') or interp_elem.get('code')
                
                # Extract method
                method_elem = observation.find('./hl7:methodCode', self.namespaces)
                if method_elem is not None:
                    entry.method = method_elem.get('displayName') or method_elem.get('code')
                
                # Extract target site
                target_elem = observation.find('./hl7:targetSiteCode', self.namespaces)
                if target_elem is not None:
                    entry.target_site = target_elem.get('displayName') or target_elem.get('code')
                
                # Extract reference range
                range_elem = observation.find('.//hl7:referenceRange/hl7:observationRange/hl7:value', self.namespaces)
                if range_elem is not None:
                    range_value = range_elem.get('value', '')
                    range_unit = range_elem.get('unit', '')
                    entry.reference_range = f"{range_value} {range_unit}".strip()
                
                # Extract comment from entryRelationship
                comment_act = observation.find('.//hl7:entryRelationship/hl7:act', self.namespaces)
                if comment_act is not None:
                    comment_code = comment_act.find('./hl7:code', self.namespaces)
                    if comment_code is not None and comment_code.get('code') == '48767-8':
                        text_ref = comment_act.find('./hl7:text/hl7:reference', self.namespaces)
                        if text_ref is not None:
                            entry.comment = text_ref.get('value', '').replace('#', '')
            
            return entry if entry.result_type or entry.result_value else None
            
        except Exception as e:
            print(f"Error extracting diagnostic result data: {e}")
            return None
    
    def _extract_code_info(self, element: ET.Element) -> Dict[str, str]:
        """Extract code information from element"""
        code_elem = element.find('./hl7:code', self.namespaces)
        if code_elem is not None:
            return {
                'code': code_elem.get('code', ''),
                'system': code_elem.get('codeSystem', ''),
                'display': code_elem.get('displayName', ''),
                'system_name': code_elem.get('codeSystemName', '')
            }
        return {}
    
    def _extract_status(self, element: ET.Element) -> Optional[str]:
        """Extract status code from element"""
        status_elem = element.find('./hl7:statusCode', self.namespaces)
        return status_elem.get('code') if status_elem is not None else None
    
    def _extract_effective_time(self, element: ET.Element) -> Optional[str]:
        """Extract and format effective time"""
        time_elem = element.find('./hl7:effectiveTime', self.namespaces)
        if time_elem is not None:
            value = time_elem.get('value')
            if value and len(value) >= 8:
                try:
                    # Parse YYYYMMDD format
                    date_obj = datetime.strptime(value[:8], '%Y%m%d')
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    return value
        return None
    
    def _extract_performer_info(self, element: ET.Element) -> Dict[str, str]:
        """Extract performer information"""
        performer_elem = element.find('./hl7:performer', self.namespaces)
        if performer_elem is None:
            return {}
        
        info = {}
        
        # Extract performer name
        person_elem = performer_elem.find('.//hl7:assignedPerson/hl7:name', self.namespaces)
        if person_elem is not None:
            family = person_elem.find('./hl7:family', self.namespaces)
            given = person_elem.find('./hl7:given', self.namespaces)
            
            name_parts = []
            if given is not None and given.text:
                name_parts.append(given.text)
            if family is not None and family.text:
                name_parts.append(family.text)
            
            if name_parts:
                info['name'] = ' '.join(name_parts)
        
        # Extract organization
        org_elem = performer_elem.find('.//hl7:representedOrganization/hl7:name', self.namespaces)
        if org_elem is not None and org_elem.text:
            info['organization'] = org_elem.text
        
        return info
    
    def _extract_author_info(self, element: ET.Element) -> Dict[str, str]:
        """Extract author information"""
        author_elem = element.find('./hl7:author', self.namespaces)
        if author_elem is None:
            return {}
        
        info = {}
        
        # Extract author time
        time_elem = author_elem.find('./hl7:time', self.namespaces)
        if time_elem is not None:
            value = time_elem.get('value')
            if value and len(value) >= 8:
                try:
                    date_obj = datetime.strptime(value[:8], '%Y%m%d')
                    info['time'] = date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    info['time'] = value
        
        # Extract author name
        person_elem = author_elem.find('.//hl7:assignedPerson/hl7:name', self.namespaces)
        if person_elem is not None:
            family = person_elem.find('./hl7:family', self.namespaces)
            given = person_elem.find('./hl7:given', self.namespaces)
            
            name_parts = []
            if given is not None and given.text:
                name_parts.append(given.text)
            if family is not None and family.text:
                name_parts.append(family.text)
            
            if name_parts:
                info['name'] = ' '.join(name_parts)
        
        # Extract organization
        org_elem = author_elem.find('.//hl7:representedOrganization/hl7:name', self.namespaces)
        if org_elem is not None and org_elem.text:
            info['organization'] = org_elem.text
        
        return info