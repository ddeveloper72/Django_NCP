"""
Clinical Section Services - Base Module

This module provides the base interfaces and abstractions for clinical section services.
Implements the enterprise-grade service interface pattern for consistent clinical data processing.

Author: Django_NCP Development Team
Date: October 2025
Version: 1.0.0
"""

from .section_service_interface import ClinicalSectionServiceInterface
from .clinical_service_base import ClinicalServiceBase

__all__ = [
    'ClinicalSectionServiceInterface',
    'ClinicalServiceBase'
]