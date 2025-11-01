"""
FHIR Procedures Extractor

Extracts Procedure resources from FHIR bundles and converts them
to the common section format for template rendering.

Part of the FHIR-CDA architecture separation initiative.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry

logger = logging.getLogger(__name__)


class FHIRProceduresExtractor(FHIRSectionServiceBase):
    """
    Extract Procedure resources from FHIR bundles.
    
    Maps FHIR procedure data to common section format compatible with
    existing procedures templates.
    
    FHIR Resources Extracted:
    - Procedure (surgical procedures, diagnostic procedures, therapeutic interventions)
    
    Key Fields:
    - code: Procedure identification (CodeableConcept)
    - status: preparation, in-progress, completed, stopped, etc.
    - performedDateTime/performedPeriod: When procedure was performed
    - performer: Who performed the procedure
    - location: Where procedure was performed
    - reasonCode/reasonReference: Why procedure was performed
    - bodySite: Target body site
    - outcome: Result of procedure
    - note: Additional clinical notes
    """
    
    def __init__(self):
        """Initialize procedures extractor with section configuration."""
        super().__init__()
        self.section_id = "procedures"
        self.section_title = "Procedures and Interventions"
        self.section_code = "47519-4"  # LOINC: History of Procedures Document
        self.section_system = "http://loinc.org"
        self.fhir_resource_type = "Procedure"
        self.icon_class = "fa-user-md"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract procedure data from FHIR Procedure resource.
        
        Args:
            resource: FHIR Procedure resource
            
        Returns:
            FHIRSectionEntry with procedure data, or None if extraction fails
        """
        try:
            entry_id = resource.get("id", "unknown")
            
            # Extract procedure code and text
            code_concept = resource.get("code", {})
            procedure_text = code_concept.get("text", "Unknown Procedure")
            procedure_codings = code_concept.get("coding", [])
            
            # Extract status
            status = resource.get("status", "unknown")
            status_display = status.capitalize()
            
            # Extract performed date/period
            performed_datetime = resource.get("performedDateTime")
            performed_period = resource.get("performedPeriod", {})
            procedure_date = None
            end_date = None
            
            if performed_datetime:
                procedure_date = performed_datetime
            elif performed_period:
                procedure_date = performed_period.get("start")
                end_date = performed_period.get("end")
            
            # Extract performers
            performers_list = resource.get("performer", [])
            performers = []
            for performer in performers_list:
                actor = performer.get("actor", {})
                display = actor.get("display")
                reference = actor.get("reference")
                
                if display:
                    performers.append(display)
                elif reference:
                    performers.append(reference)
            
            performer_text = ", ".join(performers) if performers else None
            
            # Extract location
            location = resource.get("location", {})
            location_display = location.get("display") if location else None
            
            # Extract reason
            reason_codes = resource.get("reasonCode", [])
            reason_text = None
            if reason_codes:
                # Get first reason
                reason_concept = reason_codes[0]
                if reason_concept.get("text"):
                    reason_text = reason_concept.get("text")
                elif reason_concept.get("coding"):
                    reason_text = self._safe_get_coding_display(reason_concept["coding"])
            
            # Extract body site
            body_sites = resource.get("bodySite", [])
            body_site = None
            if body_sites:
                body_site_concept = body_sites[0]
                if body_site_concept.get("text"):
                    body_site = body_site_concept.get("text")
                elif body_site_concept.get("coding"):
                    body_site = self._safe_get_coding_display(body_site_concept["coding"])
            
            # Extract outcome
            outcome_concept = resource.get("outcome", {})
            outcome = None
            if outcome_concept.get("text"):
                outcome = outcome_concept.get("text")
            elif outcome_concept.get("coding"):
                outcome = self._safe_get_coding_display(outcome_concept["coding"])
            
            # Extract category
            categories = resource.get("category", [])
            category = None
            if categories:
                category_concept = categories[0]
                if category_concept.get("text"):
                    category = category_concept.get("text")
                elif category_concept.get("coding"):
                    category = self._safe_get_coding_display(category_concept["coding"])
            
            # Extract notes
            notes = resource.get("note", [])
            note_text = None
            if notes:
                note_text = " ".join([note.get("text", "") for note in notes if note.get("text")])
            
            # Build coded concepts from procedure coding
            coded_concepts = self._extract_coding_to_concepts(procedure_codings)
            
            # Build table data structure (compatible with CDA format)
            table_data = {
                "procedure_name": procedure_text,
                "name": procedure_text,  # Generic alias
                "display_name": procedure_text,
                "status": status_display,
                "procedure_date": procedure_date,
                "performed_date": procedure_date,  # Alias
                "date": procedure_date,  # Another alias
                "end_date": end_date,
                "performer": performer_text,
                "performers": performer_text,  # Alias
                "location": location_display,
                "reason": reason_text,
                "indication": reason_text,  # Alias
                "body_site": body_site,
                "outcome": outcome,
                "category": category,
                "notes": note_text,
            }
            
            # Build display text (primary procedure name)
            display_text = procedure_text
            
            # Create normalized entry
            return FHIRSectionEntry(
                entry_id=entry_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                table_data=table_data,
                clinical_status=status,
                verification_status=None,  # Not applicable to procedures
                onset_date=procedure_date,
                recorded_date=None,  # Could extract from meta.lastUpdated if needed
                recorder=performer_text,
                notes=note_text,
                category=category,
            )
            
        except Exception as e:
            logger.error(f"[FHIR PROCEDURES] Failed to extract procedure {resource.get('id')}: {e}")
            return None
    
    def _get_table_columns(self) -> List[Dict[str, str]]:
        """
        Define table columns for procedure display.
        
        Returns:
            List of column definitions with key and label
        """
        return [
            {"key": "procedure_name", "label": "Procedure"},
            {"key": "procedure_date", "label": "Date Performed"},
            {"key": "status", "label": "Status"},
            {"key": "performer", "label": "Performed By"},
            {"key": "reason", "label": "Indication"},
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Define display configuration for procedures.
        
        Returns:
            Display configuration with colors, icons, timeline settings
        """
        return {
            "display_format": "card",  # Use card layout like CDA procedures
            "show_timeline": True,
            "group_by": None,  # Don't group by default
            "status_colors": {
                "completed": "success",
                "in-progress": "primary",
                "preparation": "info",
                "not-done": "warning",
                "stopped": "danger",
                "on-hold": "warning",
                "entered-in-error": "secondary",
                "unknown": "secondary",
            },
            "severity_colors": {},  # Not applicable to procedures
            "badge_fields": ["status"],
            "collapsible": True,
        }
