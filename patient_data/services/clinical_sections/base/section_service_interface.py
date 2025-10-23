"""
Clinical Section Service Interface

Defines the standard interface that all clinical section services must implement.
Ensures consistent behavior across all specialized clinical domain services.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from django.http import HttpRequest


class ClinicalSectionServiceInterface(ABC):
    """
    Abstract interface for clinical section services
    
    All specialized clinical section services (medications, allergies, problems, etc.)
    must implement this interface to ensure consistent behavior and integration
    with the clinical data pipeline manager.
    """
    
    @abstractmethod
    def get_section_code(self) -> str:
        """
        Return the standard LOINC section code for this clinical domain
        
        Returns:
            str: LOINC code (e.g., '10160-0' for medications, '48765-2' for allergies)
        """
        pass
    
    @abstractmethod
    def get_section_name(self) -> str:
        """
        Return the human-readable section name
        
        Returns:
            str: Section name (e.g., 'Medications', 'Allergies', 'Problems')
        """
        pass
    
    @abstractmethod
    def extract_from_session(self, request: HttpRequest, session_id: str) -> List[Dict[str, Any]]:
        """
        Extract clinical data from Django session storage
        
        Args:
            request: Django HTTP request object with session
            session_id: Patient session identifier
            
        Returns:
            List[Dict[str, Any]]: Standardized clinical data items with direct field access
        """
        pass
    
    @abstractmethod
    def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
        """
        Extract clinical data from CDA XML content using specialized parsing
        
        Args:
            cda_content: CDA XML content string
            
        Returns:
            List[Dict[str, Any]]: Standardized clinical data items
        """
        pass
    
    @abstractmethod
    def enhance_and_store(self, request: HttpRequest, session_id: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance raw clinical data and store in session for future use
        
        Args:
            request: Django HTTP request object with session
            session_id: Patient session identifier
            raw_data: Raw clinical data from CDA extraction
            
        Returns:
            List[Dict[str, Any]]: Enhanced clinical data items ready for templates
        """
        pass
    
    @abstractmethod
    def get_template_data(self, enhanced_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert enhanced clinical data to template-ready format
        
        Args:
            enhanced_data: Enhanced clinical data items
            
        Returns:
            Dict[str, Any]: Template-ready data structure with metadata
        """
        pass
    
    def get_service_metadata(self) -> Dict[str, Any]:
        """
        Return service metadata for registration and debugging
        
        Returns:
            Dict[str, Any]: Service metadata including code, name, capabilities
        """
        return {
            'section_code': self.get_section_code(),
            'section_name': self.get_section_name(),
            'service_class': self.__class__.__name__,
            'supports_session_extraction': True,
            'supports_cda_extraction': True,
            'supports_enhancement': True,
            'template_ready': True
        }
    
    def validate_clinical_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate clinical data structure and content
        
        Args:
            data: Clinical data to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if not isinstance(data, list):
            return False
        
        for item in data:
            if not isinstance(item, dict):
                return False
            
            # Check for required fields (can be overridden in subclasses)
            required_fields = ['name', 'display_name']
            for field in required_fields:
                if field not in item:
                    return False
        
        return True