"""
FHIR Immunizations Extractor

Extracts Immunization resources from FHIR bundles and converts them
to the common section format for template rendering.

Handles vaccination records and immunization history.

Part of the FHIR-CDA architecture separation initiative.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry

logger = logging.getLogger(__name__)


class FHIRImmunizationsExtractor(FHIRSectionServiceBase):
    """
    Extract Immunization resources from FHIR bundles.
    
    Maps FHIR immunization data to common section format compatible with
    existing immunizations templates.
    
    FHIR Resources Extracted:
    - Immunization (vaccination records)
    
    Key Fields:
    - vaccineCode: Vaccine product administered
    - status: completed, entered-in-error, not-done
    - statusReason: Why immunization not done (if applicable)
    - occurrenceDateTime/occurrenceString: When administered
    - lotNumber: Vaccine lot/batch number
    - manufacturer: Vaccine manufacturer
    - site: Body site where administered
    - route: Route of administration
    - doseQuantity: Amount administered
    - performer: Who administered
    - protocolApplied: Vaccination protocol details (dose number, series)
    - reaction: Adverse reactions
    - note: Additional clinical notes
    """
    
    def __init__(self):
        """Initialize immunizations extractor with section configuration."""
        super().__init__()
        self.section_id = "immunizations"
        self.section_title = "Immunization History"
        self.section_code = "11369-6"  # LOINC: History of Immunization Narrative
        self.section_system = "http://loinc.org"
        self.fhir_resource_type = "Immunization"
        self.icon_class = "fa-syringe"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract immunization data from FHIR Immunization resource.
        
        Args:
            resource: FHIR Immunization resource
            
        Returns:
            FHIRSectionEntry with immunization data, or None if extraction fails
        """
        try:
            entry_id = resource.get("id", "unknown")
            
            # Extract vaccine code and text
            vaccine_concept = resource.get("vaccineCode", {})
            vaccine_text = vaccine_concept.get("text")
            if not vaccine_text and vaccine_concept.get("coding"):
                vaccine_text = self._safe_get_coding_display(vaccine_concept["coding"])
            if not vaccine_text:
                vaccine_text = "Unknown Vaccine"
            
            vaccine_codings = vaccine_concept.get("coding", [])
            
            # Extract status
            status = resource.get("status", "unknown")
            status_display = status.capitalize()
            
            # Extract status reason (why not done)
            status_reason = None
            status_reason_concept = resource.get("statusReason", {})
            if status_reason_concept:
                if status_reason_concept.get("text"):
                    status_reason = status_reason_concept.get("text")
                elif status_reason_concept.get("coding"):
                    status_reason = self._safe_get_coding_display(status_reason_concept["coding"])
            
            # Extract occurrence date
            occurrence_datetime = resource.get("occurrenceDateTime")
            occurrence_string = resource.get("occurrenceString")
            immunization_date = occurrence_datetime or occurrence_string
            
            # Extract lot number
            lot_number = resource.get("lotNumber")
            
            # Extract manufacturer
            manufacturer_ref = resource.get("manufacturer", {})
            manufacturer = manufacturer_ref.get("display") or manufacturer_ref.get("reference")
            
            # Extract site (body site)
            site_concept = resource.get("site", {})
            site = None
            if site_concept:
                if site_concept.get("text"):
                    site = site_concept.get("text")
                elif site_concept.get("coding"):
                    site = self._safe_get_coding_display(site_concept["coding"])
            
            # Extract route
            route_concept = resource.get("route", {})
            route = None
            if route_concept:
                if route_concept.get("text"):
                    route = route_concept.get("text")
                elif route_concept.get("coding"):
                    route = self._safe_get_coding_display(route_concept["coding"])
            
            # Extract dose quantity
            dose_quantity = resource.get("doseQuantity", {})
            dose_value = dose_quantity.get("value")
            dose_unit = dose_quantity.get("unit")
            dose_text = None
            if dose_value and dose_unit:
                dose_text = f"{dose_value} {dose_unit}"
            elif dose_value:
                dose_text = str(dose_value)
            
            # Extract performer (who administered)
            performers = resource.get("performer", [])
            performer_text = None
            if performers:
                performer = performers[0]
                actor = performer.get("actor", {})
                performer_text = actor.get("display") or actor.get("reference")
            
            # Extract protocol applied (dose number, series)
            protocols = resource.get("protocolApplied", [])
            dose_number = None
            series = None
            target_disease = None
            
            if protocols:
                protocol = protocols[0]
                dose_number = protocol.get("doseNumberPositiveInt") or protocol.get("doseNumberString")
                series = protocol.get("series")
                
                # Extract target disease
                target_diseases = protocol.get("targetDisease", [])
                if target_diseases:
                    target_concept = target_diseases[0]
                    if target_concept.get("text"):
                        target_disease = target_concept.get("text")
                    elif target_concept.get("coding"):
                        target_disease = self._safe_get_coding_display(target_concept["coding"])
            
            # Extract reactions
            reactions = resource.get("reaction", [])
            reaction_text = None
            if reactions:
                reaction = reactions[0]
                detail = reaction.get("detail", {})
                reaction_text = detail.get("display") or detail.get("reference")
            
            # Extract notes
            notes = resource.get("note", [])
            note_text = None
            if notes:
                note_text = " ".join([note.get("text", "") for note in notes if note.get("text")])
            
            # Build coded concepts from vaccine coding
            coded_concepts = self._extract_coding_to_concepts(vaccine_codings)
            
            # Build table data structure (compatible with CDA format)
            table_data = {
                "vaccine_name": vaccine_text,
                "vaccination_name": vaccine_text,  # Alias for CDA compatibility
                "name": vaccine_text,  # Generic alias
                "display_name": vaccine_text,
                "status": status_display,
                "status_reason": status_reason,
                "immunization_date": immunization_date,
                "vaccination_date": immunization_date,  # Alias
                "date": immunization_date,  # Another alias
                "lot_number": lot_number,
                "batch_lot_number": lot_number,  # CDA alias
                "manufacturer": manufacturer,
                "marketing_authorization_holder": manufacturer,  # CDA alias
                "site": site,
                "route": route,
                "dose": dose_text,
                "dose_number": dose_number,
                "series": series,
                "target_disease": target_disease,
                "performer": performer_text,
                "health_professional_name": performer_text,  # CDA alias
                "reaction": reaction_text,
                "notes": note_text,
            }
            
            # Build display text (vaccine name with dose number if available)
            if dose_number:
                display_text = f"{vaccine_text} (Dose {dose_number})"
            else:
                display_text = vaccine_text
            
            # Create normalized entry
            return FHIRSectionEntry(
                entry_id=entry_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                table_data=table_data,
                clinical_status=status,
                verification_status=None,  # Not applicable to immunizations
                onset_date=immunization_date,
                recorded_date=None,  # Could extract from recorded if needed
                recorder=performer_text,
                notes=note_text,
            )
            
        except Exception as e:
            logger.error(f"[FHIR IMMUNIZATIONS] Failed to extract immunization {resource.get('id')}: {e}")
            return None
    
    def _get_table_columns(self) -> List[Dict[str, str]]:
        """
        Define table columns for immunization display.
        
        Returns:
            List of column definitions with key and label
        """
        return [
            {"key": "vaccine_name", "label": "Vaccine"},
            {"key": "immunization_date", "label": "Date Administered"},
            {"key": "dose_number", "label": "Dose #"},
            {"key": "lot_number", "label": "Lot Number"},
            {"key": "performer", "label": "Administered By"},
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Define display configuration for immunizations.
        
        Returns:
            Display configuration with colors, icons, timeline settings
        """
        return {
            "display_format": "card",  # Use card layout like CDA immunizations
            "show_timeline": True,
            "group_by": "target_disease",  # Group by disease protected against
            "status_colors": {
                "completed": "success",
                "entered-in-error": "secondary",
                "not-done": "warning",
            },
            "severity_colors": {},  # Not applicable to immunizations
            "badge_fields": ["status", "dose_number"],
            "collapsible": True,
        }
