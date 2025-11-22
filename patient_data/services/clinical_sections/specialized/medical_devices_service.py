"""
Medical Devices Section Service

Specialized service for medical devices section data processing.

Handles:
- Implanted devices
- Medical equipment
- Device information
- Device status

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any
from django.http import HttpRequest
from ..base.clinical_service_base import ClinicalServiceBase

logger = logging.getLogger(__name__)


class MedicalDevicesSectionService(ClinicalServiceBase):
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
            self._log_extraction_result('extract_from_session', len(enhanced_devices), 'Session')
            return enhanced_devices
        
        clinical_arrays = match_data.get('enhanced_clinical_data', {}).get('clinical_sections', {})
        devices_data = clinical_arrays.get('medical_devices', [])
        
        if devices_data:
            self._log_extraction_result('extract_from_session', len(devices_data), 'Clinical Arrays')
            return devices_data
        
        self.logger.info("[MEDICAL DEVICES SERVICE] No medical devices data found in session")
        return []
    
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """Extract medical devices from CDA content using specialized parsing."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(cda_content)
            
            # Find medical devices section using base method
            section = self._find_section_by_code(root, ['46264-8'])
            
            if section is not None:
                devices = self._parse_devices_xml(section)
                self._log_extraction_result('extract_from_cda', len(devices), 'CDA')
                return devices
            
            self.logger.info("[MEDICAL DEVICES SERVICE] No medical devices section found in CDA")
            return []
            
        except Exception as e:
            self.logger.error(f"[MEDICAL DEVICES SERVICE] Error extracting medical devices from CDA: {e}")
            return []
    
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance medical devices data and store in session."""
        enhanced_devices = []
        
        for device_data in raw_data:
            # Format dates using centralized formatter
            implant_date_raw = self._extract_field_value(device_data, 'implant_date', '')
            removal_date_raw = self._extract_field_value(device_data, 'removal_date', '')
            
            enhanced_device = {
                'name': self._extract_field_value(device_data, 'device_type', self._extract_field_value(device_data, 'name', 'Unknown device')),
                'display_name': self._extract_field_value(device_data, 'device_type', self._extract_field_value(device_data, 'name', 'Unknown device')),
                'device_type': self._extract_field_value(device_data, 'device_type', 'Unknown device'),
                'device_id': self._extract_field_value(device_data, 'device_id', 'Not specified'),
                'device_code': self._extract_field_value(device_data, 'device_code', ''),
                'implant_date': implant_date_raw,  # Keep raw for field mapper
                'removal_date': removal_date_raw,  # Keep raw for field mapper
                'status': self._extract_field_value(device_data, 'status', 'Active'),
                'source': 'MedicalDevicesSectionService'
            }
            enhanced_devices.append(enhanced_device)
        
        # Store in session
        session_key = f"patient_match_{session_id}"
        match_data = request.session.get(session_key, {})
        match_data['enhanced_medical_devices'] = enhanced_devices
        request.session[session_key] = match_data
        request.session.modified = True
        
        self.logger.info(f"[MEDICAL DEVICES SERVICE] Enhanced and stored {len(enhanced_devices)} medical devices")
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
        
        entries = section.findall('.//hl7:entry', self.namespaces)
        for entry in entries:
            supply = entry.find('.//hl7:supply', self.namespaces)
            if supply is not None:
                device = self._parse_device_element(supply)
                if device:
                    devices.append(device)
        
        return devices
    
    def _parse_device_element(self, supply) -> Dict[str, Any]:
        """Parse device element into structured data.
        
        XML Structure:
        <supply>
            <effectiveTime><low value="20141020"/></effectiveTime>
            <participant typeCode="DEV">
                <participantRole classCode="MANU">
                    <id root="2.999" extension="ABC-Device-ID"/>
                    <playingDevice>
                        <code code="J0105" displayName="IMPLANTABLE DEFIBRILLATORS"/>
                    </playingDevice>
                </participantRole>
            </participant>
        </supply>
        """
        device_type = "Unknown device"
        device_id = "Not specified"
        device_code = ""
        implant_date = ""
        removal_date = ""
        
        # Extract device type and ID from participant element
        participant = supply.find('.//hl7:participant[@typeCode="DEV"]', self.namespaces)
        if participant is not None:
            participant_role = participant.find('hl7:participantRole[@classCode="MANU"]', self.namespaces)
            if participant_role is not None:
                # Extract device ID
                id_elem = participant_role.find('hl7:id', self.namespaces)
                if id_elem is not None:
                    device_id = id_elem.get('extension', 'Not specified')
                    logger.info(f"[MEDICAL DEVICES] Found device ID: {device_id}")
                
                # Extract device type from playingDevice/code
                playing_device = participant_role.find('hl7:playingDevice', self.namespaces)
                if playing_device is not None:
                    code_elem = playing_device.find('hl7:code', self.namespaces)
                    if code_elem is not None:
                        device_type = code_elem.get('displayName', code_elem.get('code', 'Unknown device'))
                        device_code = code_elem.get('code', '')
                        logger.info(f"[MEDICAL DEVICES] Found device type: {device_type} (code: {device_code})")
        
        # Extract implant date from effectiveTime/low
        time_elem = supply.find('hl7:effectiveTime', self.namespaces)
        if time_elem is not None:
            low_elem = time_elem.find('hl7:low', self.namespaces)
            if low_elem is not None:
                # Check for nullFlavor first (unknown/not available dates)
                null_flavor = low_elem.get('nullFlavor', '')
                if null_flavor:
                    logger.info(f"[MEDICAL DEVICES] Implant date has nullFlavor: {null_flavor}")
                    implant_date = ''  # No date available
                else:
                    implant_date = low_elem.get('value', '')
                    logger.info(f"[MEDICAL DEVICES] Found implant date: {implant_date}")
            
            # Extract removal date from effectiveTime/high (if present)
            high_elem = time_elem.find('hl7:high', self.namespaces)
            if high_elem is not None:
                null_flavor = high_elem.get('nullFlavor', '')
                if null_flavor:
                    logger.info(f"[MEDICAL DEVICES] Removal date has nullFlavor: {null_flavor}")
                    removal_date = ''
                else:
                    removal_date = high_elem.get('value', '')
                    logger.info(f"[MEDICAL DEVICES] Found removal date: {removal_date}")
        
        return {
            'name': device_type,
            'device_type': device_type,
            'device_id': device_id,
            'device_code': device_code,
            'implant_date': implant_date,
            'removal_date': removal_date,
            'status': 'Removed' if removal_date else 'Active',
            'source': 'MedicalDevicesSectionService'
        }