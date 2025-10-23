"""
Clinical Sections Pipeline Package

This package contains the Clinical Data Pipeline Manager and related orchestration services.
Coordinates between the Enhanced CDA XML Parser and specialized clinical section services.

Directory Contents:
- __init__.py: Package initialization and public API
- clinical_data_pipeline_manager.py: Main orchestrator for clinical data processing
"""

# Make pipeline manager available at package level
from .clinical_data_pipeline_manager import ClinicalDataPipelineManager

__all__ = ['ClinicalDataPipelineManager']