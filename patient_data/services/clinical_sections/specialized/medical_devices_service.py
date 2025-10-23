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
            enhanced_device = {
                'name': self._extract_field_value(device_data, 'name', 'Unknown device'),
                'display_name': self._extract_field_value(device_data, 'name', 'Unknown device'),
                'type': self._extract_field_value(device_data, 'type', 'Medical device'),
                'manufacturer': self._extract_field_value(device_data, 'manufacturer', 'Not specified'),
                'model': self._extract_field_value(device_data, 'model', 'Not specified'),
                'serial_number': self._extract_field_value(device_data, 'serial_number', 'Not specified'),
                'implant_date': self._format_cda_date(self._extract_field_value(device_data, 'implant_date', 'Not specified')),
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
        """Parse device element into structured data."""
        # Extract device name
        product = supply.find('.//hl7:product', self.namespaces)
        name = "Unknown device"
        manufacturer = "Not specified"
        model = "Not specified"
        
        if product is not None:
            material = product.find('.//hl7:manufacturedMaterial', self.namespaces)
            if material is not None:
                code_elem = material.find('hl7:code', self.namespaces)
                if code_elem is not None:
                    name = code_elem.get('displayName', code_elem.get('code', 'Unknown device'))
                
                # Extract manufacturer
                org = product.find('.//hl7:manufacturerOrganization', self.namespaces)
                if org is not None:
                    org_name = org.find('.//hl7:name', self.namespaces)
                    if org_name is not None:
                        manufacturer = org_name.text or "Not specified"
        
        # Extract date
        time_elem = supply.find('hl7:effectiveTime', self.namespaces)
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