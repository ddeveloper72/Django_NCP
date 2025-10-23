"""
Specialized Clinical Section Services Package

This package contains domain-specific service agents for individual clinical sections.
Each service implements the ClinicalSectionServiceInterface for consistent behavior.

Directory Contents:
- problems_service.py: Problems and conditions processing
- vital_signs_service.py: Vital signs and measurements
- procedures_service.py: Clinical procedures and operations  
- immunizations_service.py: Immunization and vaccination records
- results_service.py: Laboratory and diagnostic results
- medical_devices_service.py: Medical devices and implants
- medications_service.py: Medication lists and prescriptions (Enhanced CDA)
- allergies_service.py: Allergies and adverse reactions (Enhanced CDA)
"""

# Import all specialized services for easy access
from .problems_service import ProblemsSectionService
from .vital_signs_service import VitalSignsSectionService  
from .procedures_service import ProceduresSectionService
from .immunizations_service import ImmunizationsSectionService
from .results_service import ResultsSectionService
from .medical_devices_service import MedicalDevicesSectionService

__all__ = [
    'ProblemsSectionService',
    'VitalSignsSectionService', 
    'ProceduresSectionService',
    'ImmunizationsSectionService',
    'ResultsSectionService',
    'MedicalDevicesSectionService'
]