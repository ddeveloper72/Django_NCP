"""
View Processors Package

Dedicated processors for different data source types to eliminate
hybrid processing issues and ensure clean separation of concerns.

Modules:
- fhir_processor: Handles FHIR bundle processing and context building
- cda_processor: Handles CDA document processing and context building  
- context_builders: Shared context building utilities
"""

from .fhir_processor import FHIRViewProcessor
from .cda_processor import CDAViewProcessor
from .context_builders import ContextBuilder

__all__ = [
    'FHIRViewProcessor',
    'CDAViewProcessor', 
    'ContextBuilder'
]