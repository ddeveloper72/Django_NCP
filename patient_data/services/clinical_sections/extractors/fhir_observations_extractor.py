"""
FHIR Observations Extractor

Extracts Observation resources from FHIR bundles and converts them
to the common section format for template rendering.

Handles vital signs, laboratory results, and other clinical observations.

Part of the FHIR-CDA architecture separation initiative.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry

logger = logging.getLogger(__name__)


class FHIRObservationsExtractor(FHIRSectionServiceBase):
    """
    Extract Observation resources from FHIR bundles.
    
    Maps FHIR observation data to common section format compatible with
    existing vital signs and results templates.
    
    FHIR Resources Extracted:
    - Observation (vital signs, lab results, clinical measurements)
    
    Key Fields:
    - code: Observation type (LOINC coded)
    - status: final, preliminary, registered, amended, etc.
    - category: vital-signs, laboratory, imaging, etc.
    - valueQuantity/valueString/valueCodeableConcept: Observation result
    - effectiveDateTime/effectivePeriod: When observation was made
    - component: Multi-component observations (e.g., blood pressure)
    - interpretation: Clinical interpretation codes
    - referenceRange: Normal ranges for comparison
    - note: Additional clinical notes
    """
    
    def __init__(self):
        """Initialize observations extractor with section configuration."""
        super().__init__()
        self.section_id = "observations"
        self.section_title = "Clinical Observations"
        self.section_code = "30954-2"  # LOINC: Relevant diagnostic tests/laboratory data
        self.section_system = "http://loinc.org"
        self.fhir_resource_type = "Observation"
        self.icon_class = "fa-flask"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract observation data from FHIR Observation resource.
        
        Args:
            resource: FHIR Observation resource
            
        Returns:
            FHIRSectionEntry with observation data, or None if extraction fails
        """
        try:
            entry_id = resource.get("id", "unknown")
            
            # Extract observation code and text
            code_concept = resource.get("code", {})
            observation_text = code_concept.get("text")
            if not observation_text and code_concept.get("coding"):
                observation_text = self._safe_get_coding_display(code_concept)
            if not observation_text:
                observation_text = "Unknown Observation"
            
            observation_codings = code_concept.get("coding", [])
            
            # Extract status
            status = resource.get("status", "unknown")
            status_display = status.capitalize()
            
            # Extract category (vital-signs, laboratory, imaging, etc.)
            categories = resource.get("category", [])
            category = None
            if categories:
                category_concept = categories[0]
                if category_concept.get("coding"):
                    category = self._safe_get_coding_code(category_concept)
                    if not category:
                        category = self._safe_get_coding_display(category_concept)
            
            # Extract effective date/time
            effective_datetime = resource.get("effectiveDateTime")
            effective_period = resource.get("effectivePeriod", {})
            observation_date = None
            
            if effective_datetime:
                observation_date = effective_datetime
            elif effective_period:
                observation_date = effective_period.get("start")
            
            # Extract value (can be Quantity, String, CodeableConcept, etc.)
            value_quantity = resource.get("valueQuantity", {})
            value_string = resource.get("valueString")
            value_codeable = resource.get("valueCodeableConcept", {})
            
            value_text = None
            value_numeric = None
            value_unit = None
            
            if value_quantity:
                value_numeric = value_quantity.get("value")
                value_unit = value_quantity.get("unit")
                value_text = f"{value_numeric} {value_unit}" if value_numeric and value_unit else str(value_numeric)
            elif value_string:
                value_text = value_string
            elif value_codeable:
                if value_codeable.get("text"):
                    value_text = value_codeable.get("text")
                elif value_codeable.get("coding"):
                    value_text = self._safe_get_coding_display(value_codeable)
            
            # Extract components (for multi-component observations like blood pressure)
            components = resource.get("component", [])
            component_data = []
            
            for comp in components:
                comp_code = comp.get("code", {})
                comp_name = comp_code.get("text")
                if not comp_name and comp_code.get("coding"):
                    comp_name = self._safe_get_coding_display(comp_code)
                
                comp_value_qty = comp.get("valueQuantity", {})
                if comp_value_qty:
                    comp_value = comp_value_qty.get("value")
                    comp_unit = comp_value_qty.get("unit")
                    component_data.append({
                        "name": comp_name,
                        "value": comp_value,
                        "unit": comp_unit,
                        "display": f"{comp_name}: {comp_value} {comp_unit}" if comp_value and comp_unit else comp_name
                    })
            
            # Extract interpretation
            interpretations = resource.get("interpretation", [])
            interpretation_text = None
            if interpretations:
                interp_concept = interpretations[0]
                if interp_concept.get("text"):
                    interpretation_text = interp_concept.get("text")
                elif interp_concept.get("coding"):
                    interpretation_text = self._safe_get_coding_display(interp_concept)
            
            # Extract reference range
            reference_ranges = resource.get("referenceRange", [])
            reference_range_text = None
            if reference_ranges:
                ref_range = reference_ranges[0]
                low = ref_range.get("low", {}).get("value")
                high = ref_range.get("high", {}).get("value")
                unit = ref_range.get("low", {}).get("unit") or ref_range.get("high", {}).get("unit")
                
                if low and high:
                    reference_range_text = f"{low}-{high} {unit}" if unit else f"{low}-{high}"
                elif low:
                    reference_range_text = f">{low} {unit}" if unit else f">{low}"
                elif high:
                    reference_range_text = f"<{high} {unit}" if unit else f"<{high}"
            
            # Extract notes
            notes = resource.get("note", [])
            note_text = None
            if notes:
                note_text = " ".join([note.get("text", "") for note in notes if note.get("text")])
            
            # Build coded concepts from observation coding
            coded_concepts = self._extract_coding_to_concepts(observation_codings)
            
            # Build table data structure (compatible with CDA format)
            table_data = {
                "observation_name": observation_text,
                "name": observation_text,  # Generic alias
                "display_name": observation_text,
                "status": status_display,
                "category": category,
                "observation_date": observation_date,
                "date": observation_date,  # Alias
                "value": value_text,
                "value_numeric": value_numeric,
                "value_unit": value_unit,
                "components": component_data,
                "interpretation": interpretation_text,
                "reference_range": reference_range_text,
                "notes": note_text,
            }
            
            # Build display text (observation name with value)
            if value_text:
                display_text = f"{observation_text}: {value_text}"
            elif component_data:
                # For multi-component observations, show first component
                display_text = f"{observation_text}: {component_data[0]['display']}"
            else:
                display_text = observation_text
            
            # Create normalized entry
            return FHIRSectionEntry(
                entry_id=entry_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                table_data=table_data,
                clinical_status=status,
                verification_status=None,  # Not applicable to observations
                onset_date=observation_date,
                recorded_date=None,  # Could extract from issued if needed
                notes=note_text,
                category=category,
            )
            
        except Exception as e:
            logger.error(f"[FHIR OBSERVATIONS] Failed to extract observation {resource.get('id')}: {e}")
            return None
    
    def _get_table_columns(self) -> List[Dict[str, str]]:
        """
        Define table columns for observation display.
        
        Returns:
            List of column definitions with key and label
        """
        return [
            {"key": "observation_name", "label": "Observation"},
            {"key": "value", "label": "Value"},
            {"key": "reference_range", "label": "Reference Range"},
            {"key": "interpretation", "label": "Interpretation"},
            {"key": "observation_date", "label": "Date"},
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Define display configuration for observations.
        
        Returns:
            Display configuration with colors, icons, timeline settings
        """
        return {
            "display_format": "table",  # Use table layout for observations
            "show_timeline": True,
            "group_by": "category",  # Group by vital-signs, laboratory, etc.
            "status_colors": {
                "final": "success",
                "preliminary": "warning",
                "registered": "info",
                "amended": "primary",
                "corrected": "primary",
                "cancelled": "danger",
                "entered-in-error": "secondary",
            },
            "interpretation_colors": {
                "high": "danger",
                "low": "warning",
                "normal": "success",
                "abnormal": "danger",
                "critical": "danger",
            },
            "severity_colors": {},  # Not applicable to observations
            "badge_fields": ["status", "interpretation"],
            "collapsible": True,
        }
