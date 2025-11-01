"""
FHIR Conditions Extractor

Extracts Condition resources from FHIR bundles and converts them
to the common section format for template rendering.

Part of the FHIR-CDA architecture separation initiative.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry

logger = logging.getLogger(__name__)


class FHIRConditionsExtractor(FHIRSectionServiceBase):
    """
    Extract Condition resources from FHIR bundles.
    
    Maps FHIR condition/problem data to common section format compatible with
    existing problems/conditions templates.
    
    FHIR Resources Extracted:
    - Condition (diagnoses, problems, health concerns)
    
    Key Fields:
    - code: Condition identification (CodeableConcept)
    - clinicalStatus: active, inactive, resolved, remission, etc.
    - verificationStatus: unconfirmed, provisional, confirmed, refuted, etc.
    - severity: Subjective severity assessment
    - onsetDateTime/onsetPeriod: When condition started
    - abatementDateTime: When condition resolved
    - category: problem-list-item, encounter-diagnosis, health-concern
    - note: Additional clinical notes
    """
    
    def __init__(self):
        """Initialize conditions extractor with section configuration."""
        super().__init__()
        self.section_id = "problems"
        self.section_title = "Problem List"
        self.section_code = "11450-4"  # LOINC: Problem list - Reported
        self.section_system = "http://loinc.org"
        self.fhir_resource_type = "Condition"
        self.icon_class = "fa-stethoscope"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract condition data from FHIR Condition resource.
        
        Args:
            resource: FHIR Condition resource
            
        Returns:
            FHIRSectionEntry with condition data, or None if extraction fails
        """
        try:
            entry_id = resource.get("id", "unknown")
            
            # Extract condition code and text
            code_concept = resource.get("code", {})
            condition_text = code_concept.get("text", "Unknown Condition")
            condition_codings = code_concept.get("coding", [])
            
            # Extract clinical status
            clinical_status_concept = resource.get("clinicalStatus", {})
            clinical_status = None
            if clinical_status_concept.get("coding"):
                clinical_status = clinical_status_concept["coding"][0].get("code", "unknown")
            
            clinical_status_display = clinical_status.capitalize() if clinical_status else "Unknown"
            
            # Extract verification status
            verification_status_concept = resource.get("verificationStatus", {})
            verification_status = None
            if verification_status_concept.get("coding"):
                verification_status = verification_status_concept["coding"][0].get("code", "unknown")
            
            verification_display = verification_status.capitalize() if verification_status else "Unknown"
            
            # Extract severity
            severity_concept = resource.get("severity", {})
            severity = None
            if severity_concept.get("coding"):
                severity = self._safe_get_coding_display(severity_concept["coding"])
            elif severity_concept.get("text"):
                severity = severity_concept.get("text")
            
            # Extract onset date/period
            onset_datetime = resource.get("onsetDateTime")
            onset_period = resource.get("onsetPeriod", {})
            onset_date = None
            
            if onset_datetime:
                onset_date = onset_datetime
            elif onset_period:
                onset_date = onset_period.get("start")
            
            # Extract abatement (resolution) date
            abatement_datetime = resource.get("abatementDateTime")
            abatement_date = abatement_datetime if abatement_datetime else None
            
            # Extract category
            categories = resource.get("category", [])
            category = None
            if categories:
                # Get first category
                category_concept = categories[0]
                if category_concept.get("coding"):
                    category = self._safe_get_coding_display(category_concept["coding"])
                elif category_concept.get("text"):
                    category = category_concept.get("text")
            
            # Extract recorder (who recorded the condition)
            recorder_ref = resource.get("recorder", {}).get("reference")
            
            # Extract notes
            notes = resource.get("note", [])
            note_text = None
            if notes:
                note_text = " ".join([note.get("text", "") for note in notes if note.get("text")])
            
            # Build coded concepts from condition coding
            coded_concepts = self._extract_coding_to_concepts(condition_codings)
            
            # Build table data structure (compatible with CDA format)
            table_data = {
                "condition_name": condition_text,
                "problem_name": condition_text,  # Alias for problems template
                "name": condition_text,  # Generic alias
                "display_name": condition_text,
                "clinical_status": clinical_status_display,
                "status": clinical_status_display,  # Alias
                "verification_status": verification_display,
                "severity": severity,
                "onset_date": onset_date,
                "start_date": onset_date,  # Alias
                "abatement_date": abatement_date,
                "end_date": abatement_date,  # Alias
                "category": category,
                "recorder": recorder_ref,
                "notes": note_text,
            }
            
            # Build display text (primary condition name)
            display_text = condition_text
            
            # Create normalized entry
            return FHIRSectionEntry(
                entry_id=entry_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                table_data=table_data,
                clinical_status=clinical_status,
                verification_status=verification_status,
                onset_date=onset_date,
                recorded_date=None,  # Could extract from meta.lastUpdated if needed
                recorder=recorder_ref,
                notes=note_text,
                severity=severity,
                category=category,
            )
            
        except Exception as e:
            logger.error(f"[FHIR PROBLEMS] Failed to extract condition {resource.get('id')}: {e}")
            return None
    
    def _get_table_columns(self) -> List[Dict[str, str]]:
        """
        Define table columns for condition/problem display.
        
        Returns:
            List of column definitions with key and label
        """
        return [
            {"key": "condition_name", "label": "Condition"},
            {"key": "clinical_status", "label": "Status"},
            {"key": "verification_status", "label": "Verification"},
            {"key": "severity", "label": "Severity"},
            {"key": "onset_date", "label": "Onset Date"},
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Define display configuration for conditions.
        
        Returns:
            Display configuration with colors, icons, timeline settings
        """
        return {
            "display_format": "card",  # Use card layout like CDA problems
            "show_timeline": True,
            "group_by": "clinical_status",  # Group by active/resolved/etc
            "status_colors": {
                "active": "danger",
                "inactive": "secondary",
                "resolved": "success",
                "remission": "info",
                "recurrence": "warning",
            },
            "verification_colors": {
                "confirmed": "success",
                "provisional": "warning",
                "differential": "info",
                "unconfirmed": "secondary",
                "refuted": "danger",
                "entered-in-error": "secondary",
            },
            "severity_colors": {
                "severe": "danger",
                "moderate": "warning",
                "mild": "info",
            },
            "badge_fields": ["clinical_status", "verification_status", "severity"],
            "collapsible": True,
        }
