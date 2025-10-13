"""
Patient Data Models Package

Django NCP Healthcare Portal - Patient Data Models
Generated: December 19, 2024
Purpose: Unified patient data models for European healthcare interoperability
"""

# Import all models from the main models.py file
from ..models import *

# Import new unified patient demographics models
from .patient_demographics import PatientDemographics, PatientIdentifier

# Extend __all__ with new models
try:
    __all__.extend(['PatientDemographics', 'PatientIdentifier'])
except NameError:
    # If __all__ doesn't exist from the main models import, create it
    __all__ = ['PatientDemographics', 'PatientIdentifier']