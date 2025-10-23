"""
Clinical Sections Package

Enterprise-grade clinical data processing with hybrid specialized architecture.

This package implements the hybrid specialized architecture pattern:
- Enhanced CDA XML Parser: Coordinator role for section discovery and routing
- Clinical Pipeline Manager: Orchestrator for specialized domain services
- Specialized Services: Domain expert agents for individual clinical sections

Directory Structure:
- base/: Base classes and interfaces for all clinical services
- pipeline/: Clinical data pipeline manager and orchestration
- specialized/: Domain-specific service agents for individual clinical sections
- extractors/: Raw data extraction utilities

Service Registry:
All specialized services are registered with the pipeline manager for
automatic discovery and routing of clinical section processing.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

# Import core components
from .base.clinical_service_base import ClinicalServiceBase
from .base.section_service_interface import ClinicalSectionServiceInterface
from .pipeline.clinical_data_pipeline_manager import ClinicalDataPipelineManager

# Import all specialized services
from .specialized.problems_service import ProblemsSectionService
from .specialized.vital_signs_service import VitalSignsSectionService
from .specialized.procedures_service import ProceduresSectionService
from .specialized.immunizations_service import ImmunizationsSectionService
from .specialized.results_service import ResultsSectionService
from .specialized.medical_devices_service import MedicalDevicesSectionService
from .specialized.allergies_service import AllergiesSectionService
from .specialized.past_illness_service import PastIllnessSectionService
from .specialized.pregnancy_history_service import PregnancyHistorySectionService
from .specialized.social_history_service import SocialHistorySectionService
from .specialized.advance_directives_service import AdvanceDirectivesSectionService
from .specialized.functional_status_service import FunctionalStatusSectionService

# Create global pipeline manager instance
clinical_pipeline_manager = ClinicalDataPipelineManager()

# Register all specialized services
def register_clinical_services():
    """
    Register all specialized clinical section services with the pipeline manager.
    
    This function implements the service registry pattern, automatically
    registering all available specialized services for clinical data processing.
    """
    services = [
        ProblemsSectionService(),
        VitalSignsSectionService(),
        ProceduresSectionService(),
        ImmunizationsSectionService(),
        ResultsSectionService(),
        MedicalDevicesSectionService(),
        AllergiesSectionService(),
        PastIllnessSectionService(),
        PregnancyHistorySectionService(),
        SocialHistorySectionService(),
        AdvanceDirectivesSectionService(),
        FunctionalStatusSectionService()
    ]
    
    for service in services:
        clinical_pipeline_manager.register_service(service)
    
    return len(services)

# Auto-register services on module import
registered_count = register_clinical_services()

# Public API exports
__all__ = [
    # Core infrastructure
    'ClinicalServiceBase',
    'ClinicalSectionServiceInterface', 
    'ClinicalDataPipelineManager',
    'clinical_pipeline_manager',
    
    # Specialized services
    'ProblemsSectionService',
    'VitalSignsSectionService',
    'ProceduresSectionService', 
    'ImmunizationsSectionService',
    'ResultsSectionService',
    'MedicalDevicesSectionService',
    'AllergiesSectionService',
    'PastIllnessSectionService',
    'PregnancyHistorySectionService',
    'SocialHistorySectionService',
    'AdvanceDirectivesSectionService',
    'FunctionalStatusSectionService',
    
    # Registry functions
    'register_clinical_services'
]

# Module metadata
__version__ = '1.0.0'
__author__ = 'Django_NCP Development Team'
__registry_info__ = {
    'registered_services': registered_count,
    'auto_registration': True,
    'architecture_pattern': 'hybrid_specialized'
}