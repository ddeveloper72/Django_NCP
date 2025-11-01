"""
FHIR Medications Extractor

Extracts MedicationStatement resources from FHIR bundles and converts them
to the common section format for template rendering.

Part of the FHIR-CDA architecture separation initiative.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry

logger = logging.getLogger(__name__)


class FHIRMedicationsExtractor(FHIRSectionServiceBase):
    """
    Extract MedicationStatement resources from FHIR bundles.
    
    Maps FHIR medication data to common section format compatible with
    existing medication templates.
    
    FHIR Resources Extracted:
    - MedicationStatement (active medications)
    
    Key Fields:
    - medicationCodeableConcept: Medication name and codes
    - status: active, completed, stopped, etc.
    - reasonCode: Indication/reason for medication
    - effectiveDateTime/effectivePeriod: Treatment timing
    - dosage: Dosage instructions (if available)
    - note: Additional clinical notes
    """
    
    def __init__(self):
        """Initialize medications extractor with section configuration."""
        super().__init__()
        self.section_id = "medications"
        self.section_title = "Medication Summary"
        self.section_code = "10160-0"  # LOINC: History of Medication use Narrative
        self.section_system = "http://loinc.org"
        self.fhir_resource_type = "MedicationStatement"
        self.icon_class = "fa-pills"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract medication data from FHIR MedicationStatement resource.
        
        Args:
            resource: FHIR MedicationStatement resource
            
        Returns:
            FHIRSectionEntry with medication data, or None if extraction fails
        """
        try:
            entry_id = resource.get("id", "unknown")
            
            # Extract medication name and coding
            medication_concept = resource.get("medicationCodeableConcept", {})
            medication_text = medication_concept.get("text", "Unknown Medication")
            medication_codings = medication_concept.get("coding", [])
            
            # Extract status
            status = resource.get("status", "unknown")
            status_display = status.capitalize()
            
            # Extract reason/indication
            reason_codes = resource.get("reasonCode", [])
            reason_text = None
            if reason_codes:
                # Get first reason (primary indication)
                reason_text = reason_codes[0].get("text")
                if not reason_text and reason_codes[0].get("coding"):
                    reason_text = self._safe_get_coding_display(reason_codes[0]["coding"])
            
            # Extract timing information
            effective_datetime = resource.get("effectiveDateTime")
            effective_period = resource.get("effectivePeriod", {})
            start_date = None
            end_date = None
            
            if effective_datetime:
                start_date = effective_datetime
            elif effective_period:
                start_date = effective_period.get("start")
                end_date = effective_period.get("end")
            
            # Extract dosage information (if available)
            dosage_list = resource.get("dosage", [])
            dosage_text = None
            route = None
            
            if dosage_list:
                first_dosage = dosage_list[0]
                dosage_text = first_dosage.get("text")
                
                # Extract route
                route_concept = first_dosage.get("route", {})
                if route_concept.get("coding"):
                    route = self._safe_get_coding_display(route_concept["coding"])
                elif route_concept.get("text"):
                    route = route_concept.get("text")
            
            # Extract notes
            notes = resource.get("note", [])
            note_text = None
            if notes:
                note_text = " ".join([note.get("text", "") for note in notes if note.get("text")])
            
            # Build coded concepts from medication coding
            coded_concepts = self._extract_coding_to_concepts(medication_codings)
            
            # Build table data structure (compatible with CDA format)
            table_data = {
                "medication_name": medication_text,
                "name": medication_text,  # Alias for template compatibility
                "display_name": medication_text,  # Another alias
                "status": status_display,
                "indication": reason_text,
                "reason": reason_text,  # Alias
                "start_date": start_date,
                "end_date": end_date,
                "dosage_text": dosage_text,
                "route": route,
                "notes": note_text,
            }
            
            # Build display text (primary medication name)
            display_text = medication_text
            
            # Create normalized entry
            return FHIRSectionEntry(
                entry_id=entry_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                table_data=table_data,
                clinical_status=status,
                verification_status=None,  # Not applicable to medications
                onset_date=start_date,
                recorded_date=None,  # Could extract from meta.lastUpdated if needed
                notes=note_text,
            )
            
        except Exception as e:
            logger.error(f"[FHIR MEDICATIONS] Failed to extract medication {resource.get('id')}: {e}")
            return None
    
    def _get_table_columns(self) -> List[Dict[str, str]]:
        """
        Define table columns for medication display.
        
        Returns:
            List of column definitions with key and label
        """
        return [
            {"key": "medication_name", "label": "Medication"},
            {"key": "indication", "label": "Indication"},
            {"key": "status", "label": "Status"},
            {"key": "start_date", "label": "Start Date"},
            {"key": "dosage_text", "label": "Dosage"},
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Define display configuration for medications.
        
        Returns:
            Display configuration with colors, icons, timeline settings
        """
        return {
            "display_format": "card",  # Use card layout like CDA medications
            "show_timeline": True,
            "group_by": None,
            "status_colors": {
                "active": "success",
                "completed": "primary",
                "stopped": "warning",
                "on-hold": "info",
                "discontinued": "danger",
                "entered-in-error": "secondary",
            },
            "severity_colors": {},  # Not applicable to medications
            "badge_fields": ["status"],
            "collapsible": True,
        }
