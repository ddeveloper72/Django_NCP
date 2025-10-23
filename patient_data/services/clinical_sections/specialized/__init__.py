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
- allergies_service.py: Allergies and adverse reactions
- past_illness_service.py: History of past illness
- pregnancy_history_service.py: History of pregnancies
- social_history_service.py: Social history and lifestyle factors
- advance_directives_service.py: Advance directives and care preferences
- functional_status_service.py: Functional status assessments
"""

# Import all specialized services for easy access
from .problems_service import ProblemsSectionService
from .vital_signs_service import VitalSignsSectionService  
from .procedures_service import ProceduresSectionService
from .immunizations_service import ImmunizationsSectionService
from .results_service import ResultsSectionService
from .medical_devices_service import MedicalDevicesSectionService
from .allergies_service import AllergiesSectionService
from .past_illness_service import PastIllnessSectionService
from .pregnancy_history_service import PregnancyHistorySectionService
from .social_history_service import SocialHistorySectionService
from .advance_directives_service import AdvanceDirectivesSectionService
from .functional_status_service import FunctionalStatusSectionService

__all__ = [
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
    'FunctionalStatusSectionService'
]