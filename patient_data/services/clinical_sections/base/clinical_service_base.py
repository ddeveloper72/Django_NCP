"""
Clinical Service Base Class

Provides common functionality and helper methods for all clinical section services.
Implements shared patterns and utilities used across specialized services.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional
from django.http import HttpRequest
from .section_service_interface import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class ClinicalServiceBase(ClinicalSectionServiceInterface):
    """
    Base class for clinical section services providing common functionality
    
    Implements shared patterns, helper methods, and utilities that are used
    across multiple specialized clinical section services.
    """
    
    def __init__(self):
        """Initialize base clinical service"""
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize lxml availability check
        try:
            from lxml import etree
            self.LXML_AVAILABLE = True
            self.logger.info(f"[{self.get_section_name()}] lxml available for advanced XPath parsing")
        except ImportError:
            import xml.etree.ElementTree as etree
            self.LXML_AVAILABLE = False
            self.logger.warning(f"[{self.get_section_name()}] lxml not available, using ElementTree fallback")
        
        # Standard CDA namespaces
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'pharm': 'urn:ihe:pharm:medication',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def _extract_field_value(self, data: Dict[str, Any], field_name: str, default_value: str) -> str:
        """
        Extract field value from clinical data handling both flat and nested structures
        
        Args:
            data: Clinical data dictionary
            field_name: Field name to extract
            default_value: Default value if not found
            
        Returns:
            str: Extracted field value or default
        """
        field_data = data.get(field_name, {})
        
        # Handle nested dictionary structure (from Enhanced CDA Parser)
        if isinstance(field_data, dict):
            return (
                field_data.get('display_name') or 
                field_data.get('translated') or 
                field_data.get('value', default_value)
            )
        # Handle flat string structure
        elif isinstance(field_data, str) and field_data.strip():
            return field_data.strip()
        # Default fallback
        else:
            return default_value
    
    def _extract_text_from_element(self, element) -> str:
        """
        Extract clean text from XML element, handling nested content tags
        
        Args:
            element: XML element to extract text from
            
        Returns:
            str: Clean text content or "-" if empty
        """
        if element is None:
            return "-"
        
        # Try to find content tags first
        content_elements = element.findall('.//content')
        if content_elements:
            # Get text from the last content element (most specific)
            text = content_elements[-1].text
            if text and text.strip():
                return text.strip()
        
        # Fallback to element text
        text = element.text
        if text and text.strip():
            return text.strip()
        
        # If no direct text, try to get all text content
        all_text = ''.join(element.itertext()).strip()
        return all_text if all_text else "-"
    
    def _format_cda_date(self, cda_date: str) -> Optional[str]:
        """
        Format CDA date string to dd/mm/yyyy ISO format
        
        Args:
            cda_date: CDA date string (e.g., "19971006" or "1997-10-06")
            
        Returns:
            Optional[str]: Formatted date string (dd/mm/yyyy) or None if parsing fails
        """
        from datetime import datetime
        import re
        
        if not cda_date:
            return None
        
        try:
            # Remove any timezone info (e.g., "20091006T10:00:00+01:00" → "20091006")
            date_clean = re.sub(r'T[\d:]+.*$', '', cda_date)
            
            # Handle different date formats
            if len(date_clean) == 8 and date_clean.isdigit():
                # Format: YYYYMMDD
                date_obj = datetime.strptime(date_clean, '%Y%m%d')
            elif '-' in date_clean and len(date_clean) == 10:
                # Format: YYYY-MM-DD
                date_obj = datetime.strptime(date_clean, '%Y-%m-%d')
            elif '/' in date_clean:
                # Format: MM/DD/YYYY or DD/MM/YYYY
                if date_clean.split('/')[2] == '4':  # YYYY is 4 digits
                    date_obj = datetime.strptime(date_clean, '%m/%d/%Y')
                else:
                    date_obj = datetime.strptime(date_clean, '%d/%m/%Y')
            else:
                return cda_date  # Return original if format unknown
            
            # Format as dd/mm/yyyy ISO format (e.g., "18/06/2009")
            return date_obj.strftime("%d/%m/%Y")
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Could not parse date '{cda_date}': {e}")
            return cda_date  # Return original if parsing fails
    
    def _find_section_by_code(self, root, section_codes: List[str]):
        """
        Find clinical section in CDA XML by LOINC codes
        
        Args:
            root: XML root element
            section_codes: List of LOINC codes to search for
            
        Returns:
            XML element of found section or None
        """
        sections = root.findall('.//hl7:section', self.namespaces)
        
        for section in sections:
            code_elem = section.find('hl7:code', self.namespaces)
            if code_elem is not None:
                code = code_elem.get('code')
                if code in section_codes:
                    return section
        
        return None
    
    def _create_clinical_table_structure(self, headers: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create standardized clinical table structure for templates
        
        Args:
            headers: List of table headers
            rows: List of data rows
            
        Returns:
            Dict[str, Any]: Standardized clinical table structure
        """
        return {
            'clinical_table': {
                'headers': headers,
                'rows': rows
            },
            'item_count': len(rows),
            'has_data': len(rows) > 0
        }
    
    def _log_extraction_result(self, method_name: str, item_count: int, source: str = "CDA"):
        """
        Log extraction results for debugging and monitoring
        
        Args:
            method_name: Name of extraction method
            item_count: Number of items extracted
            source: Source of extraction (CDA, Session, etc.)
        """
        service_name = self.get_section_name()
        self.logger.info(f"[{service_name}] {method_name} extracted {item_count} items from {source}")
    
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Default template data conversion - can be overridden in specialized services
        
        Args:
            enhanced_data: Enhanced clinical data items
            
        Returns:
            Dict[str, Any]: Template-ready data structure
        """
        return {
            'items': enhanced_data,
            'metadata': {
                'section_name': self.get_section_name(),
                'section_code': self.get_section_code(),
                'item_count': len(enhanced_data),
                'has_items': len(enhanced_data) > 0,
                'service_class': self.__class__.__name__
            }
        }