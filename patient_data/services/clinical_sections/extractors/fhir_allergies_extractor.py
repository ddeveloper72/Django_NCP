"""
FHIR Allergies Section Extractor
Extracts AllergyIntolerance resources from FHIR R4 bundles

Handles:
- AllergyIntolerance resources (food, medication, environment)
- Clinical and verification status
- Severity levels
- Reaction manifestations
- Coded concepts for CTS integration
"""

from typing import Dict, Any, List, Optional
from ..base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry
import logging

logger = logging.getLogger(__name__)


class FHIRAllergiesExtractor(FHIRSectionServiceBase):
    """
    Extract allergies and intolerances from FHIR R4 AllergyIntolerance resources
    
    FHIR R4 AllergyIntolerance Structure:
    - code: Allergen identification (CodeableConcept)
    - clinicalStatus: active | inactive | resolved
    - verificationStatus: unconfirmed | confirmed | refuted | entered-in-error
    - category: food | medication | environment | biologic
    - criticality: low | high | unable-to-assess
    - reaction: Adverse reaction events
    """
    
    def __init__(self):
        super().__init__()
        self.section_id = "allergies"
        self.section_title = "Allergies and Intolerances"
        self.section_code = "48765-2"  # LOINC: Allergies and adverse reactions Document
        self.fhir_resource_type = "AllergyIntolerance"
        self.icon_class = "fa-exclamation-triangle"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract allergy entry from AllergyIntolerance resource
        
        Args:
            resource: FHIR AllergyIntolerance resource
            
        Returns:
            FHIRSectionEntry with allergy data
        """
        try:
            # Extract resource ID
            allergy_id = resource.get("id", "unknown")
            
            # Get allergen code and display text
            code_data = resource.get("code", {})
            allergen_display = self._safe_get_coding_display(code_data)
            
            if not allergen_display:
                allergen_display = "Unknown allergen"
            
            # Extract coded concepts from main allergen code
            coded_concepts = []
            coding_list = code_data.get("coding", [])
            if coding_list:
                coded_concepts.extend(self._extract_coding_to_concepts(coding_list, "allergen"))
            
            # Get clinical status
            clinical_status_obj = resource.get("clinicalStatus", {})
            clinical_status = self._safe_get_coding_code(clinical_status_obj)
            
            # Get verification status
            verification_status_obj = resource.get("verificationStatus", {})
            verification_status = self._safe_get_coding_code(verification_status_obj)
            
            # Combine statuses for display
            status_display = f"{clinical_status or 'unknown'}/{verification_status or 'unknown'}"
            
            # Get onset date
            onset_date = resource.get("onsetDateTime") or resource.get("onsetString")
            
            # Get recorded date
            recorded_date = resource.get("recordedDate")
            
            # Get criticality/severity
            criticality = resource.get("criticality")  # low, high, unable-to-assess
            
            # Get category
            category_list = resource.get("category", [])
            category = category_list[0] if category_list else None
            
            # Extract reaction details
            reactions = resource.get("reaction", [])
            reaction_texts = []
            for reaction in reactions:
                # Get reaction severity
                reaction_severity = reaction.get("severity", "")
                
                # Get manifestations
                for manifestation in reaction.get("manifestation", []):
                    manifest_display = self._safe_get_coding_display(manifestation)
                    if manifest_display:
                        if reaction_severity:
                            reaction_texts.append(f"{manifest_display} ({reaction_severity})")
                        else:
                            reaction_texts.append(manifest_display)
                    
                    # Extract coded concepts from manifestations
                    manifest_coding = manifestation.get("coding", [])
                    if manifest_coding:
                        coded_concepts.extend(
                            self._extract_coding_to_concepts(manifest_coding, "reaction")
                        )
            
            # Build display text
            display_text = allergen_display
            if criticality:
                display_text += f" [Criticality: {criticality}]"
            if category:
                display_text += f" ({category})"
            
            # Get notes
            notes = []
            for note in resource.get("note", []):
                note_text = note.get("text")
                if note_text:
                    notes.append(note_text)
            
            # Add reaction details to notes
            if reaction_texts:
                notes.insert(0, f"Reactions: {', '.join(reaction_texts)}")
            
            return FHIRSectionEntry(
                entry_id=allergy_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                clinical_status=status_display,
                onset_date=onset_date,
                recorded_date=recorded_date,
                notes=notes if notes else None,
                severity=criticality,
                category=category,
                verification_status=verification_status,
                fhir_resource_reference=f"AllergyIntolerance/{allergy_id}",
                raw_resource=resource
            )
            
        except Exception as e:
            logger.error(f"[FHIR ALLERGIES] Error extracting allergy entry: {e}")
            logger.exception("Full traceback:")
            return None
    
    def _get_table_columns(self) -> List[str]:
        """Columns for allergy table display"""
        return [
            "display_text",
            "category", 
            "severity",
            "clinical_status",
            "onset_date"
        ]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """Display configuration for allergies section"""
        return {
            "show_timeline": True,
            "show_severity": True,
            "show_status": True,
            "enable_filtering": True,
            "severity_colors": {
                "high": "danger",
                "low": "warning",
                "unable-to-assess": "secondary"
            },
            "status_colors": {
                "active": "danger",
                "inactive": "secondary",
                "resolved": "success"
            }
        }
