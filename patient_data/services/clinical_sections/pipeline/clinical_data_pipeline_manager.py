"""
Clinical Data Pipeline Manager

Coordination system for specialized clinical section service agents.

Author: Django_NCP Development Team
Date: October 2025
"""

import logging
from typing import Dict, List, Any, Optional
from django.http import HttpRequest
from ..base.section_service_interface import ClinicalSectionServiceInterface

logger = logging.getLogger(__name__)


class ClinicalDataPipelineManager:
    """Pipeline manager for coordinating clinical section services."""
    
    def __init__(self):
        """Initialize the pipeline manager."""
        self._service_registry: Dict[str, ClinicalSectionServiceInterface] = {}
        logger.info("[PIPELINE MANAGER] Initialized")
    
    def register_service(self, service: ClinicalSectionServiceInterface) -> None:
        """Register a clinical section service."""
        section_code = service.get_section_code()
        section_name = service.get_section_name().lower().replace(' ', '_')
        
        self._service_registry[section_code] = service
        self._service_registry[section_name] = service
        
        logger.info(f"[PIPELINE MANAGER] Registered: {service.get_section_name()}")
    
    def get_service(self, section_identifier: str) -> Optional[ClinicalSectionServiceInterface]:
        """Get a registered service."""
        return self._service_registry.get(section_identifier)
    
    def get_all_services(self) -> Dict[str, ClinicalSectionServiceInterface]:
        """Get unique services."""
        unique_services = {}
        for key, service in self._service_registry.items():
            if service.get_section_code() not in unique_services:
                unique_services[service.get_section_code()] = service
        return unique_services
