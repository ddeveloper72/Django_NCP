"""
FHIR Agent Service - Bridge between FHIR Bundle parsing and Django view layer

This service acts as the interface between FHIRBundleParser (enhanced data extraction) 
and patient_cda_view (template rendering). It transforms FHIR Bundle data into
the same context structure expected by CDA templates for unified UI rendering.

Architecture:
- Leverages enhanced FHIRBundleParser for comprehensive resource extraction
- Outputs data in CDA-compatible format for template consistency
- Provides clinical sections AND extended patient information
- Maintains Healthcare Organisation UI standards
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union

from .fhir_bundle_parser import FHIRBundleParser
from .session_data_service import SessionDataService

logger = logging.getLogger(__name__)


class FHIRAgentService:
    """
    FHIR Agent for extracting and formatting FHIR Bundle data for Django views.
    
    Transforms FHIR Bundle resources into CDA-compatible context data for 
    unified template rendering across both FHIR and CDA documents.
    """
    
    def __init__(self):
        self.fhir_bundle_parser = FHIRBundleParser()  # Use enhanced parser
        
    def extract_patient_context_data(
        self, 
        fhir_bundle_content: Union[str, dict], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Extract FHIR Bundle data and format for patient_cda_view template context.
        
        Args:
            fhir_bundle_content: FHIR Bundle as JSON string or dict
            session_id: Session identifier for logging and session management
            
        Returns:
            Dictionary with CDA-compatible context data for templates
        """
        try:
            logger.info(f"[FHIR AGENT] Processing FHIR Bundle for session {session_id}")
            
            # Parse FHIR Bundle using enhanced parser with extended patient information
            bundle_result = self.fhir_bundle_parser.parse_patient_summary_bundle(fhir_bundle_content)
            
            if not bundle_result.get("success", False):
                logger.warning(f"[FHIR AGENT] Enhanced FHIR parsing failed: {bundle_result.get('error')}")
                logger.info(f"[FHIR AGENT] Attempting fallback parsing for session {session_id}")
                
                # Try fallback parsing for basic FHIR structures
                fallback_result = self._fallback_fhir_parsing(fhir_bundle_content, session_id)
                if fallback_result and not fallback_result.get("error"):
                    return fallback_result
                else:
                    logger.error(f"[FHIR AGENT] Both enhanced and fallback parsing failed")
                    return self._create_error_context(session_id, bundle_result.get('error'))
            
            # Enhanced parser already returns the extended patient information!
            # No need for additional transformation - return the enhanced data directly
            logger.info(f"[FHIR AGENT] Enhanced FHIR parsing successful with extended patient information")
            logger.info(f"[FHIR AGENT] Extended data available: admin={bool(bundle_result.get('administrative_data'))}, contact={bool(bundle_result.get('contact_data'))}, healthcare={bool(bundle_result.get('healthcare_data'))}")
            
            return bundle_result
            
        except Exception as e:
            logger.error(f"[FHIR AGENT] Error processing FHIR Bundle: {str(e)}")
            return self._create_error_context(session_id, str(e))
    
    def _transform_to_cda_context(
        self, 
        patient_summary: Dict[str, Any], 
        session_id: str
    ) -> Dict[str, Any]:
        """
        Transform FHIR patient summary to CDA-compatible context structure.
        
        Maps FHIR resources to the same context structure used by CDA templates
        for unified rendering across document types.
        """
        context = {
            "session_id": session_id,
            "document_type": "FHIR Bundle",
            "has_clinical_data": True,
        }
        
        # Extract patient demographics
        demographics = patient_summary.get("demographics", {})
        context["patient_data"] = self._extract_patient_demographics(demographics)
        context["patient_information"] = self._extract_patient_demographics(demographics)  # Alias for compatibility
        
        # Extract clinical sections in CDA-compatible format
        context["clinical_arrays"] = self._extract_clinical_sections(patient_summary)
        
        # Extract administrative data
        context["admin_data"] = self._extract_administrative_data(patient_summary)
        
        # Add processing statistics
        context["processing_stats"] = self._generate_processing_stats(patient_summary)
        
        # Add section availability flags (matching CDA pattern)
        context.update(self._get_section_availability_flags(patient_summary))
        
        return context
    
    def _extract_patient_demographics(self, demographics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient demographic data in CDA-compatible format."""
        if not demographics:
            return {"given_name": "Unknown", "family_name": "Patient"}
            
        # Handle both FHIR name structure (list) and fallback structure (dict)
        name_data = demographics.get("name", {})
        if isinstance(name_data, list):
            # Standard FHIR format
            primary_name = name_data[0] if name_data else {}
        else:
            # Fallback format
            primary_name = name_data
        
        return {
            "given_name": " ".join(primary_name.get("given", [])) or "Unknown",
            "family_name": primary_name.get("family", "Patient"),
            "birth_date": demographics.get("birth_date", "Unknown"),
            "gender": demographics.get("gender", "Unknown"),
            "identifier": demographics.get("identifier", []),
            "telecom": demographics.get("telecom", []),
            "address": demographics.get("address", []),
        }
    
    def _extract_clinical_sections(self, patient_summary: Dict[str, Any]) -> Dict[str, List]:
        """
        Extract clinical data sections in CDA-compatible array format.
        
        Maps FHIR resources to the same section structure used by CDA clinical arrays
        for consistent template rendering.
        """
        clinical_arrays = {
            "allergies": self._format_allergies(patient_summary.get("allergies", [])),
            "medications": self._format_medications(patient_summary.get("medications", [])),
            "conditions": self._format_conditions(patient_summary.get("conditions", [])),
            "procedures": self._format_procedures(patient_summary.get("procedures", [])),
            "observations": self._format_observations(patient_summary.get("observations", [])),
            "immunizations": self._format_immunizations(patient_summary.get("immunizations", [])),
            "encounters": self._format_encounters(patient_summary.get("encounters", [])),
            "diagnostic_reports": self._format_diagnostic_reports(patient_summary.get("diagnostic_reports", [])),
        }
        
        return clinical_arrays
    
    def _format_allergies(self, allergies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR AllergyIntolerance resources for CDA-compatible display."""
        formatted_allergies = []
        
        for allergy in allergies:
            formatted_allergies.append({
                "substance": self._extract_display_text(allergy.get("substance", {})),
                "category": allergy.get("category", ["Unknown"])[0] if allergy.get("category") else "Unknown",
                "criticality": allergy.get("criticality", "Unknown"),
                "clinical_status": allergy.get("clinical_status", "Unknown"),
                "verification_status": allergy.get("verification_status", "Unknown"),
                "type": allergy.get("type", "Unknown"),
                "onset": allergy.get("onset_datetime", "Unknown"),
                "reactions": self._format_allergy_reactions(allergy.get("reactions", [])),
                "source": "FHIR AllergyIntolerance",
            })
            
        return formatted_allergies
    
    def _format_medications(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR MedicationStatement resources for CDA-compatible display."""
        formatted_medications = []
        
        for medication in medications:
            formatted_medications.append({
                "medication_name": self._extract_medication_name(medication.get("medication", {})),
                "status": medication.get("status", "Unknown"),
                "dosage": self._format_medication_dosage(medication.get("dosage", [])),
                "effective_period": self._format_period(medication.get("effective_period", {})),
                "date_asserted": medication.get("date_asserted", "Unknown"),
                "reason": self._format_reason_codes(medication.get("reason_code", [])),
                "source": "FHIR MedicationStatement",
            })
            
        return formatted_medications
    
    def _format_conditions(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR Condition resources for CDA-compatible display."""
        formatted_conditions = []
        
        for condition in conditions:
            formatted_conditions.append({
                "condition_name": self._extract_display_text(condition.get("code", {})),
                "clinical_status": condition.get("clinical_status", "Unknown"),
                "verification_status": condition.get("verification_status", "Unknown"),
                "severity": self._extract_display_text(condition.get("severity", {})),
                "onset": self._format_onset(condition.get("onset", {})),
                "category": self._format_categories(condition.get("category", [])),
                "recorded_date": condition.get("recorded_date", "Unknown"),
                "source": "FHIR Condition",
            })
            
        return formatted_conditions
    
    def _format_procedures(self, procedures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR Procedure resources for CDA-compatible display."""
        formatted_procedures = []
        
        for procedure in procedures:
            formatted_procedures.append({
                "procedure_name": self._extract_display_text(procedure.get("code", {})),
                "status": procedure.get("status", "Unknown"),
                "performed": self._format_performed_period(procedure),
                "category": self._extract_display_text(procedure.get("category", {})),
                "body_site": self._format_body_sites(procedure.get("body_site", [])),
                "outcome": self._extract_display_text(procedure.get("outcome", {})),
                "notes": procedure.get("notes", []),
                "source": "FHIR Procedure",
            })
            
        return formatted_procedures
    
    def _format_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR Observation resources for CDA-compatible display."""
        formatted_observations = []
        
        for observation in observations:
            formatted_observations.append({
                "observation_name": self._extract_display_text(observation.get("code", {})),
                "value": self._format_observation_value(observation.get("value", {})),
                "status": observation.get("status", "Unknown"),
                "category": self._format_categories(observation.get("category", [])),
                "effective_datetime": observation.get("effective_datetime", "Unknown"),
                "interpretation": self._format_interpretations(observation.get("interpretation", [])),
                "reference_range": self._format_reference_ranges(observation.get("reference_range", [])),
                "component": observation.get("component", []),
                "source": "FHIR Observation",
            })
            
        return formatted_observations
    
    def _format_immunizations(self, immunizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR Immunization resources for CDA-compatible display."""
        formatted_immunizations = []
        
        for immunization in immunizations:
            formatted_immunizations.append({
                "vaccine_name": self._extract_display_text(immunization.get("vaccine_code", {})),
                "status": immunization.get("status", "Unknown"),
                "occurrence_datetime": immunization.get("occurrence_datetime", "Unknown"),
                "recorded": immunization.get("recorded", "Unknown"),
                "lot_number": immunization.get("lot_number", "Unknown"),
                "expiration_date": immunization.get("expiration_date", "Unknown"),
                "site": self._extract_display_text(immunization.get("site", {})),
                "route": self._extract_display_text(immunization.get("route", {})),
                "dose_quantity": immunization.get("dose_quantity", "Unknown"),
                "reason": self._format_reason_codes(immunization.get("reason_code", [])),
                "source": "FHIR Immunization",
            })
            
        return formatted_immunizations
    
    def _format_encounters(self, encounters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR Encounter resources for CDA-compatible display."""
        formatted_encounters = []
        
        for encounter in encounters:
            formatted_encounters.append({
                "encounter_type": self._extract_display_text(encounter.get("class", {})),
                "status": encounter.get("status", "Unknown"),
                "type": self._format_encounter_types(encounter.get("type", [])),
                "period": self._format_period(encounter.get("period", {})),
                "diagnosis": self._format_encounter_diagnosis(encounter.get("diagnosis", [])),
                "hospitalization": encounter.get("hospitalization", {}),
                "location": encounter.get("location", []),
                "source": "FHIR Encounter",
            })
            
        return formatted_encounters
    
    def _format_diagnostic_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format FHIR DiagnosticReport resources for CDA-compatible display."""
        formatted_reports = []
        
        for report in reports:
            formatted_reports.append({
                "report_name": self._extract_display_text(report.get("code", {})),
                "status": report.get("status", "Unknown"),
                "category": self._format_categories(report.get("category", [])),
                "effective_datetime": report.get("effective_datetime", "Unknown"),
                "issued": report.get("issued", "Unknown"),
                "result_references": report.get("result_references", []),
                "conclusion": report.get("conclusion", ""),
                "coded_diagnosis": self._format_coded_diagnosis(report.get("coded_diagnosis", [])),
                "source": "FHIR DiagnosticReport",
            })
            
        return formatted_reports
    
    def _extract_administrative_data(self, patient_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Extract administrative and metadata information."""
        composition = patient_summary.get("composition", {})
        care_providers = patient_summary.get("care_providers", {})
        
        return {
            "document_title": composition.get("title", "FHIR Patient Summary"),
            "document_date": composition.get("date", "Unknown"),
            "document_status": composition.get("status", "Unknown"),
            "practitioners": care_providers.get("practitioners", []),
            "organizations": care_providers.get("organizations", []),
            "composition_sections": composition.get("sections", []),
            "metadata": patient_summary.get("summary_metadata", {}),
        }
    
    def _generate_processing_stats(self, patient_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate processing statistics for FHIR data"""
        clinical_sections = patient_summary.get("allergies", []) + \
                           patient_summary.get("conditions", []) + \
                           patient_summary.get("medications", []) + \
                           patient_summary.get("observations", [])
        
        return {
            "total_sections": len([k for k, v in patient_summary.items() if isinstance(v, list) and v]),
            "total_entries": len(clinical_sections),
            "has_coded_data": True,  # FHIR is inherently coded
            "processing_time": "< 1 second",
            "data_quality": "Good"
        }
    
    def _get_section_availability_flags(self, patient_summary: Dict[str, Any]) -> Dict[str, bool]:
        """Create availability flags for template conditional rendering."""
        return {
            "has_allergies": bool(patient_summary.get("allergies")),
            "has_medications": bool(patient_summary.get("medications")),
            "has_conditions": bool(patient_summary.get("conditions")),
            "has_procedures": bool(patient_summary.get("procedures")),
            "has_observations": bool(patient_summary.get("observations")),
            "has_immunizations": bool(patient_summary.get("immunizations")),
            "has_encounters": bool(patient_summary.get("encounters")),
            "has_diagnostic_reports": bool(patient_summary.get("diagnostic_reports")),
            "has_administrative_data": bool(patient_summary.get("composition")),
        }
    
    # Helper methods for data formatting
    
    def _extract_display_text(self, codeable_concept: Dict[str, Any]) -> str:
        """Extract human-readable text from FHIR CodeableConcept with CTS resolution."""
        if not codeable_concept:
            return "Unknown"
        
        # Extract code and system from first coding
        coding = codeable_concept.get("coding", [])
        code = None
        code_system = None
        display_from_fhir = None
        text_value = codeable_concept.get("text", "")
        
        if coding:
            code = coding[0].get("code")
            code_system = coding[0].get("system", "")
            display_from_fhir = coding[0].get("display", "")
        
        # If we have a code, try CTS resolution
        if code:
            try:
                from patient_data.services.cts_integration.cts_service import CTSService
                cts_service = CTSService()
                
                # Try CTS resolution
                cts_result = cts_service.get_term_display(code, code_system)
                if cts_result and cts_result != code:
                    logger.info(f"[FHIR CTS] Resolved {code} → {cts_result}")
                    return cts_result
            except Exception as e:
                logger.debug(f"[FHIR CTS] Resolution failed for {code}: {e}")
        
        # Fallback hierarchy: text > display > code
        if text_value:
            return text_value
        if display_from_fhir:
            return display_from_fhir
        if code:
            return code
            
        return "Unknown"
    
    def _extract_medication_name(self, medication: Dict[str, Any]) -> str:
        """Extract medication name from FHIR medication data."""
        if not medication:
            return "Unknown Medication"
            
        # Check for medication code
        if medication.get("code"):
            return self._extract_display_text(medication["code"])
            
        # Check for medication form
        if medication.get("form"):
            return self._extract_display_text(medication["form"])
            
        return "Unknown Medication"
    
    def _format_medication_dosage(self, dosage_list: List[Dict[str, Any]]) -> List[str]:
        """Format FHIR dosage instructions for display."""
        formatted_dosage = []
        
        for dosage in dosage_list:
            dosage_text = dosage.get("text", "")
            if dosage_text:
                formatted_dosage.append(dosage_text)
            elif dosage.get("dose_quantity"):
                formatted_dosage.append(f"Dose: {dosage['dose_quantity']}")
                
        return formatted_dosage or ["Dosage not specified"]
    
    def _format_period(self, period: Dict[str, Any]) -> str:
        """Format FHIR Period for display."""
        if not period:
            return "Unknown"
            
        start = period.get("start", "")
        end = period.get("end", "")
        
        if start and end:
            return f"{start} to {end}"
        elif start:
            return f"From {start}"
        elif end:
            return f"Until {end}"
            
        return "Unknown period"
    
    def _format_reason_codes(self, reason_codes: List[Dict[str, Any]]) -> List[str]:
        """Format reason codes for display."""
        return [self._extract_display_text(reason) for reason in reason_codes]
    
    def _format_onset(self, onset: Dict[str, Any]) -> str:
        """Format condition onset information."""
        if not onset:
            return "Unknown"
            
        if onset.get("datetime"):
            return onset["datetime"]
        elif onset.get("age"):
            return f"Age {onset['age']}"
        elif onset.get("period"):
            return self._format_period(onset["period"])
        elif onset.get("range"):
            return f"Range: {onset['range']}"
        elif onset.get("string"):
            return onset["string"]
            
        return "Unknown onset"
    
    def _format_categories(self, categories: List[Dict[str, Any]]) -> List[str]:
        """Format category codes for display."""
        return [self._extract_display_text(category) for category in categories]
    
    def _format_performed_period(self, procedure: Dict[str, Any]) -> str:
        """Format procedure performed period."""
        if procedure.get("performed_period"):
            return self._format_period(procedure["performed_period"])
        elif procedure.get("performed_datetime"):
            return procedure["performed_datetime"]
            
        return "Unknown"
    
    def _format_body_sites(self, body_sites: List[Dict[str, Any]]) -> List[str]:
        """Format body site codes for display."""
        return [self._extract_display_text(site) for site in body_sites]
    
    def _format_observation_value(self, value: Dict[str, Any]) -> str:
        """Format FHIR observation value for display."""
        if not value:
            return "No value"
            
        if value.get("quantity"):
            qty = value["quantity"]
            return f"{qty.get('value', '')} {qty.get('unit', '')}"
        elif value.get("codeable_concept"):
            return self._extract_display_text(value["codeable_concept"])
        elif value.get("string"):
            return value["string"]
        elif value.get("boolean") is not None:
            return "Yes" if value["boolean"] else "No"
        elif value.get("integer") is not None:
            return str(value["integer"])
            
        return "Unknown value"
    
    def _format_interpretations(self, interpretations: List[Dict[str, Any]]) -> List[str]:
        """Format observation interpretations."""
        return [self._extract_display_text(interp) for interp in interpretations]
    
    def _format_reference_ranges(self, ranges: List[Dict[str, Any]]) -> List[str]:
        """Format reference ranges for display."""
        formatted_ranges = []
        
        for range_item in ranges:
            range_text = range_item.get("text", "")
            if range_text:
                formatted_ranges.append(range_text)
            else:
                low = range_item.get("low", {})
                high = range_item.get("high", {})
                if low or high:
                    range_str = f"{low.get('value', '')} - {high.get('value', '')} {low.get('unit', high.get('unit', ''))}"
                    formatted_ranges.append(range_str.strip())
                    
        return formatted_ranges
    
    def _format_allergy_reactions(self, reactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format allergy reaction details."""
        formatted_reactions = []
        
        for reaction in reactions:
            formatted_reactions.append({
                "substance": self._extract_display_text(reaction.get("substance", {})),
                "manifestation": [self._extract_display_text(m) for m in reaction.get("manifestation", [])],
                "severity": reaction.get("severity", "Unknown"),
                "onset": reaction.get("onset", "Unknown"),
                "description": reaction.get("description", ""),
            })
            
        return formatted_reactions
    
    def _format_encounter_types(self, types: List[Dict[str, Any]]) -> List[str]:
        """Format encounter types."""
        return [self._extract_display_text(enc_type) for enc_type in types]
    
    def _format_encounter_diagnosis(self, diagnoses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format encounter diagnosis information."""
        formatted_diagnoses = []
        
        for diagnosis in diagnoses:
            formatted_diagnoses.append({
                "condition_reference": diagnosis.get("condition_reference", ""),
                "use": self._extract_display_text(diagnosis.get("use", {})),
                "rank": diagnosis.get("rank", "Unknown"),
            })
            
        return formatted_diagnoses
    
    def _format_coded_diagnosis(self, coded_diagnoses: List[Dict[str, Any]]) -> List[str]:
        """Format coded diagnosis from diagnostic reports."""
        return [self._extract_display_text(diagnosis) for diagnosis in coded_diagnoses]
    
    def _fallback_fhir_parsing(self, fhir_bundle_content: Union[str, dict], session_id: str) -> Dict[str, Any]:
        """
        Fallback FHIR parsing for basic structures when strict parsing fails.
        
        Handles simple FHIR Bundle dictionaries for testing and development.
        """
        try:
            # Handle string/dict conversion
            if isinstance(fhir_bundle_content, str):
                bundle_data = json.loads(fhir_bundle_content)
            else:
                bundle_data = fhir_bundle_content
                
            if not isinstance(bundle_data, dict) or bundle_data.get("resourceType") != "Bundle":
                return {"error": "Invalid Bundle structure"}
                
            logger.info(f"[FHIR AGENT] Using fallback parsing for basic FHIR Bundle")
            
            # Extract resources manually
            entries = bundle_data.get("entry", [])
            resources = {"Patient": [], "Condition": [], "AllergyIntolerance": [], "Observation": []}
            
            for entry in entries:
                resource = entry.get("resource", {})
                resource_type = resource.get("resourceType")
                if resource_type in resources:
                    resources[resource_type].append(resource)
            
            logger.info(f"[FHIR AGENT] Extracted resources: {[(k, len(v)) for k, v in resources.items() if v]}")
            
            # Build basic patient summary
            patient_summary = {
                "demographics": self._extract_fallback_demographics(resources.get("Patient", [])),
                "conditions": self._extract_fallback_conditions(resources.get("Condition", [])),
                "allergies": self._extract_fallback_allergies(resources.get("AllergyIntolerance", [])),
                "observations": self._extract_fallback_observations(resources.get("Observation", []))
            }
            
            logger.info(f"[FHIR AGENT] Built patient summary with demographics: {bool(patient_summary['demographics'])}")
            
            # Transform to CDA context
            context_data = self._transform_to_cda_context(patient_summary, session_id)
            
            # Add fallback metadata
            context_data.update({
                "data_source": "FHIR",
                "bundle_id": bundle_data.get("id", "unknown"),
                "fallback_parsing": True,
                "resource_counts": {k: len(v) for k, v in resources.items() if v},
                "fhir_agent_processed": True,
            })
            
            logger.info(f"[FHIR AGENT] Fallback parsing successful for session {session_id}")
            return context_data
            
        except Exception as e:
            logger.error(f"[FHIR AGENT] Fallback parsing failed: {str(e)}")
            return {"error": f"Fallback parsing failed: {str(e)}"}
    
    def _extract_fallback_demographics(self, patients: List[Dict]) -> Dict[str, Any]:
        """Extract basic patient demographics from simple FHIR structure"""
        if not patients:
            return {}
            
        patient = patients[0]
        demographics = {
            "id": patient.get("id"),
            "name": {},
            "birth_date": patient.get("birthDate"),
            "gender": patient.get("gender"),
            "identifier": patient.get("identifier", []),
            "address": patient.get("address", []),
            "telecom": patient.get("telecom", [])
        }
        
        # Extract name
        names = patient.get("name", [])
        if names:
            name = names[0]
            demographics["name"] = {
                "family": name.get("family"),
                "given": name.get("given", [])
            }
        
        return demographics
    
    def _extract_fallback_conditions(self, conditions: List[Dict]) -> List[Dict[str, Any]]:
        """Extract basic condition data from simple FHIR structure"""
        extracted = []
        for condition in conditions:
            extracted.append({
                "id": condition.get("id"),
                "code": {"text": condition.get("code", {}).get("text", "Unknown condition")},
                "clinical_status": condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "unknown"),
                "verification_status": "confirmed",
                "category": [],
                "severity": None,
                "onset_datetime": condition.get("onsetDateTime", condition.get("onsetString")),
                "recorded_date": None
            })
        return extracted
    
    def _extract_fallback_allergies(self, allergies: List[Dict]) -> List[Dict[str, Any]]:
        """Extract basic allergy data from simple FHIR structure"""
        extracted = []
        for allergy in allergies:
            extracted.append({
                "id": allergy.get("id"),
                "substance": {"text": allergy.get("code", {}).get("text", "Unknown allergy")},
                "category": ["medication"],  # Default category as list
                "criticality": allergy.get("criticality", "unknown"),
                "clinical_status": "active",  # Default status
                "verification_status": "confirmed",  # Default verification
                "type": allergy.get("type", "allergy"),
                "onset_datetime": None,
                "reactions": []
            })
        return extracted
    
    def _extract_fallback_observations(self, observations: List[Dict]) -> List[Dict[str, Any]]:
        """Extract basic observation data from simple FHIR structure"""
        extracted = []
        for obs in observations:
            extracted.append({
                "id": obs.get("id"),
                "code": {"text": obs.get("code", {}).get("text", "Unknown observation")},
                "value": obs.get("valueString") or obs.get("valueQuantity", {}),
                "status": obs.get("status", "unknown"),
                "effective_date": obs.get("effectiveDateTime"),
                "category": [],
                "interpretation": [],
                "reference_range": []
            })
        return extracted
    
    def _create_error_context(self, session_id: str, error_message: str) -> Dict[str, Any]:
        """Create error context when FHIR processing fails."""
        return {
            "session_id": session_id,
            "data_source": "FHIR",
            "has_clinical_data": False,
            "error": True,
            "error_message": error_message,
            "patient_data": {"given_name": "Unknown", "family_name": "Patient"},
            "clinical_arrays": {},
            "admin_data": {},
        }
    
    def get_fhir_bundle_from_session(self, session_id: str) -> Optional[Union[str, dict]]:
        """
        Retrieve FHIR Bundle content from encrypted session data.
        
        Works with PatientSession model and decrypts stored FHIR Bundle data.
        """
        try:
            from patient_data.models import PatientSession
            from patient_data.services.session_data_service import SessionDataService
            from django.http import HttpRequest
            
            # Get the PatientSession
            try:
                patient_session = PatientSession.objects.get(session_id=session_id)
                logger.info(f"[FHIR AGENT] Found PatientSession for {session_id}")
                
                # Create a mock request object for SessionDataService
                class MockRequest:
                    def __init__(self):
                        self.session = {}
                
                mock_request = MockRequest()
                
                # Use SessionDataService to get patient data with proper decryption
                session_service = SessionDataService()
                patient_data, debug_info = session_service.get_patient_data(mock_request, session_id)
                
                if patient_data:
                    logger.info(f"[FHIR AGENT] Retrieved patient data for {session_id}")
                    logger.debug(f"[FHIR AGENT] Debug info: {debug_info}")
                    
                    # Check various possible FHIR Bundle locations in the data
                    fhir_bundle = None
                    
                    # Option 1: Direct FHIR Bundle in patient_data
                    if isinstance(patient_data, dict):
                        if patient_data.get("resourceType") == "Bundle":
                            fhir_bundle = patient_data
                        # Option 2: Nested in patient_data structure
                        elif patient_data.get("patient_data", {}).get("fhir_bundle"):
                            fhir_bundle = patient_data["patient_data"]["fhir_bundle"]
                        # Option 3: In cda_content as JSON string
                        elif patient_data.get("cda_content"):
                            cda_content = patient_data["cda_content"]
                            if isinstance(cda_content, str):
                                try:
                                    import json
                                    parsed_content = json.loads(cda_content)
                                    if parsed_content.get("resourceType") == "Bundle":
                                        fhir_bundle = parsed_content
                                except json.JSONDecodeError:
                                    pass
                        # Option 4: Direct access to various data keys
                        for key in ["fhir_data", "bundle_data", "clinical_data", "patient_bundle"]:
                            if patient_data.get(key):
                                data = patient_data[key]
                                if isinstance(data, dict) and data.get("resourceType") == "Bundle":
                                    fhir_bundle = data
                                    break
                                elif isinstance(data, str):
                                    try:
                                        import json
                                        parsed_data = json.loads(data)
                                        if parsed_data.get("resourceType") == "Bundle":
                                            fhir_bundle = parsed_data
                                            break
                                    except json.JSONDecodeError:
                                        continue
                    
                    if fhir_bundle:
                        logger.info(f"[FHIR AGENT] Successfully extracted FHIR Bundle for {session_id}")
                        logger.info(f"[FHIR AGENT] Bundle type: {fhir_bundle.get('type')}, entries: {len(fhir_bundle.get('entry', []))}")
                        return fhir_bundle
                    else:
                        logger.warning(f"[FHIR AGENT] Patient data found but no FHIR Bundle detected for {session_id}")
                        logger.debug(f"[FHIR AGENT] Available keys: {list(patient_data.keys()) if isinstance(patient_data, dict) else 'Not a dict'}")
                else:
                    logger.warning(f"[FHIR AGENT] No patient data retrieved for {session_id}")
                    
            except PatientSession.DoesNotExist:
                logger.warning(f"[FHIR AGENT] No PatientSession found for {session_id}")
                
            # Fallback: Try Django session storage for backwards compatibility
            from django.contrib.sessions.models import Session
            session_key = f"patient_match_{session_id}"
            
            for db_session in Session.objects.all():
                try:
                    session_data = db_session.get_decoded()
                    if session_key in session_data:
                        match_data = session_data[session_key]
                        
                        # Check multiple patterns for FHIR data source detection
                        is_fhir_source = (
                            match_data.get("data_source") in ["FHIR", "FHIR_Enhanced"] or
                            match_data.get("patient_data", {}).get("source") == "FHIR" or
                            "fhir_bundle" in match_data
                        )
                        
                        if is_fhir_source:
                            # Try different locations for FHIR bundle
                            fhir_bundle = (
                                match_data.get("fhir_bundle") or
                                match_data.get("patient_data", {}).get("fhir_bundle")
                            )
                            
                            if fhir_bundle:
                                logger.info(f"[FHIR AGENT] Found FHIR Bundle in Django session storage for {session_id}")
                                logger.info(f"[FHIR AGENT] Data source: {match_data.get('data_source')}")
                                logger.info(f"[FHIR AGENT] Emergency contacts available: {match_data.get('has_emergency_contacts', False)}")
                                return fhir_bundle
                except Exception:
                    continue
                    
            logger.warning(f"[FHIR AGENT] No FHIR Bundle found for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"[FHIR AGENT] Error retrieving FHIR Bundle: {str(e)}")
            import traceback
            logger.debug(f"[FHIR AGENT] Traceback: {traceback.format_exc()}")
            return None