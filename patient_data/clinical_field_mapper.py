"""
Clinical Field Mapper
Transforms raw clinical data into template-compatible structures.

This service addresses the critical gap where templates expect items with:
1. A `data` object with structured fields like `allergen.display_value`, `severity.display_value`, etc.
2. Fallback flat fields like `allergen`, `name`, etc.

Currently only medications have proper template compatibility - this mapper extends that to all clinical sections.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClinicalFieldMapper:
    """Maps raw clinical data to template-compatible structures"""

    def __init__(self):
        self.mapping_stats = {
            "sections_processed": 0,
            "items_mapped": 0,
            "data_structures_added": 0,
            "fallback_fields_added": 0
        }
    
    def _format_cda_date(self, cda_date: str) -> str:
        """Format CDA date string (YYYYMMDD) to European display format (DD/MM/YYYY)"""
        from datetime import datetime
        import re
        
        if not cda_date or cda_date == "Not specified":
            return "Not recorded"
        
        try:
            # Remove any timezone info and clean up
            date_clean = re.sub(r'[T\+\-].*$', '', str(cda_date))
            
            # Handle different date formats
            if len(date_clean) == 8:  # YYYYMMDD
                dt = datetime.strptime(date_clean, '%Y%m%d')
                return dt.strftime('%d/%m/%Y')  # European format: DD/MM/YYYY
            elif len(date_clean) == 6:  # YYYYMM
                dt = datetime.strptime(date_clean, '%Y%m')
                return dt.strftime('%m/%Y')  # Month/Year format
            elif len(date_clean) == 4:  # YYYY
                return date_clean
            elif '/' in date_clean:  # Already formatted in European style
                return date_clean
            elif '-' in date_clean:  # ISO format - convert to European
                try:
                    dt = datetime.strptime(date_clean, '%Y-%m-%d')
                    return dt.strftime('%d/%m/%Y')
                except ValueError:
                    return date_clean
            else:
                return date_clean
        except (ValueError, AttributeError):
            return "Not recorded"

    def map_clinical_arrays(self, clinical_arrays: Dict[str, List]) -> Dict[str, List]:
        """Apply field mapping to all clinical sections for template compatibility"""
        try:
            logger.info("[FIELD_MAPPER] Starting clinical data mapping for template compatibility")
            
            # Apply section-specific mapping
            clinical_arrays["allergies"] = self._map_allergy_fields(clinical_arrays.get("allergies", []))
            clinical_arrays["problems"] = self._map_problem_fields(clinical_arrays.get("problems", []))
            clinical_arrays["procedures"] = self._map_procedure_fields(clinical_arrays.get("procedures", []))
            clinical_arrays["immunizations"] = self._map_immunization_fields(clinical_arrays.get("immunizations", []))
            clinical_arrays["vital_signs"] = self._map_vital_signs_fields(clinical_arrays.get("vital_signs", []))
            clinical_arrays["results"] = self._map_results_fields(clinical_arrays.get("results", []))
            clinical_arrays["medical_devices"] = self._map_medical_devices_fields(clinical_arrays.get("medical_devices", []))
            clinical_arrays["past_illness"] = self._map_past_illness_fields(clinical_arrays.get("past_illness", []))
            clinical_arrays["pregnancy_history"] = self._map_pregnancy_history_fields(clinical_arrays.get("pregnancy_history", []))
            clinical_arrays["social_history"] = self._map_social_history_fields(clinical_arrays.get("social_history", []))
            clinical_arrays["functional_status"] = self._map_functional_status_fields(clinical_arrays.get("functional_status", []))
            
            # Medications already have template compatibility fixes, just count them
            self.mapping_stats["sections_processed"] += 1
            self.mapping_stats["items_mapped"] += len(clinical_arrays.get("medications", []))
            
            logger.info(f"[FIELD_MAPPER] Clinical mapping complete: {self.mapping_stats}")
            return clinical_arrays
            
        except Exception as e:
            logger.error(f"[FIELD_MAPPER] Clinical mapping failed: {e}")
            return clinical_arrays

    def _map_allergy_fields(self, allergies: List[Dict]) -> List[Dict]:
        """Map allergy data for template compatibility
        
        Template expects:
        - allergy.data.allergen.display_value
        - allergy.data.allergen.value  
        - allergy.data.severity.display_value
        - allergy.data.reaction.display_value
        - allergy.allergen (fallback)
        - allergy.reaction (fallback)
        """
        mapped_allergies = []
        
        for allergy in allergies:
            if not allergy:
                continue
                
            mapped_allergy = dict(allergy)  # Create a copy
            
            # Extract core allergy information
            allergen_name = self._extract_allergen_name(allergy)
            reaction_info = self._extract_reaction_info(allergy)
            severity_info = self._extract_severity_info(allergy)
            
            # Create data structure for template compatibility
            mapped_allergy["data"] = {
                "allergen": {
                    "display_value": allergen_name,
                    "value": allergen_name
                },
                "reaction": {
                    "display_value": reaction_info,
                    "value": reaction_info
                },
                "severity": {
                    "display_value": severity_info,
                    "value": severity_info
                }
            }
            
            # Add fallback flat fields
            mapped_allergy["allergen"] = allergen_name
            mapped_allergy["reaction"] = reaction_info
            mapped_allergy["severity"] = severity_info
            mapped_allergy["display_name"] = allergen_name
            mapped_allergy["name"] = allergen_name
            
            mapped_allergies.append(mapped_allergy)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped allergy: {allergen_name} with severity {severity_info}")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_allergies

    def _map_problem_fields(self, problems: List[Dict]) -> List[Dict]:
        """Map problem data for template compatibility
        
        Template expects:
        - problem.data.problem.display_value
        - problem.data.problem.value
        - problem.data.status.display_value
        - problem.data.type.display_value
        - problem.data.clinical_status.display_value
        - problem.name (fallback)
        """
        mapped_problems = []
        
        for problem in problems:
            if not problem:
                continue
                
            mapped_problem = dict(problem)  # Create a copy
            
            # Extract core problem information
            problem_name = self._extract_problem_name(problem)
            status_info = self._extract_problem_status(problem)
            problem_type = self._extract_problem_type(problem)
            clinical_status = self._extract_clinical_status(problem)
            
            # Create data structure for template compatibility
            mapped_problem["data"] = {
                "problem": {
                    "display_value": problem_name,
                    "value": problem_name
                },
                "status": {
                    "display_value": status_info,
                    "value": status_info
                },
                "type": {
                    "display_value": problem_type,
                    "value": problem_type
                },
                "clinical_status": {
                    "display_value": clinical_status,
                    "value": clinical_status
                },
                "onset_date": {
                    "display_value": problem.get("onset_date", ""),
                    "value": problem.get("onset_date", "")
                }
            }
            
            # Add fallback flat fields
            mapped_problem["name"] = problem_name
            mapped_problem["display_name"] = problem_name
            mapped_problem["status"] = status_info
            mapped_problem["problem_type"] = problem_type
            
            mapped_problems.append(mapped_problem)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped problem: {problem_name} with status {status_info}")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_problems

    def _map_procedure_fields(self, procedures: List[Dict]) -> List[Dict]:
        """Map procedure data for template compatibility
        
        Template expects:
        - procedure.data.procedure.display_value
        - procedure.data.procedure.value
        - procedure.procedure_name (fallback)
        - procedure.name (fallback)
        - procedure.display_name (fallback)
        """
        mapped_procedures = []
        
        for procedure in procedures:
            if not procedure:
                continue
                
            mapped_procedure = dict(procedure)  # Create a copy
            
            # Extract core procedure information
            procedure_name = self._extract_procedure_name(procedure)
            procedure_date_raw = procedure.get("procedure_date", procedure.get("date", ""))
            
            # CRITICAL FIX: Handle procedure_code as dict (from EnhancedCDAProcessor) or string (from ProceduresSectionService)
            procedure_code_field = procedure.get("procedure_code", procedure.get("code", ""))
            if isinstance(procedure_code_field, dict):
                # Extract from dict structure: {"code": "64253000", "codeSystem": "...", "displayName": ""}
                procedure_code = procedure_code_field.get("code", "")
                code_system = procedure_code_field.get("codeSystem", "")
            else:
                procedure_code = procedure_code_field or ""
                code_system = procedure.get("code_system", "") or ""
            
            # Handle target_site as dict or string
            target_site_field = procedure.get("target_site", "")
            if isinstance(target_site_field, dict):
                target_site = target_site_field.get("displayName", target_site_field.get("code", ""))
            else:
                target_site = target_site_field or ""
            
            laterality = procedure.get("laterality", "") or ""
            status = procedure.get("status", "") or ""
            
            # Format date for display
            procedure_date = self._format_cda_date(procedure_date_raw)
            
            # Handle None values for display
            procedure_code_display = procedure_code if procedure_code else "Not specified"
            target_site_display = target_site if target_site else "Not specified"
            
            # Create data structure for template compatibility
            mapped_procedure["data"] = {
                "procedure": {
                    "display_value": procedure_name,
                    "value": procedure_name
                },
                "date": {
                    "display_value": procedure_date,
                    "value": procedure_date_raw
                },
                "procedure_code": {
                    "display_value": procedure_code_display,
                    "value": procedure_code
                },
                "code_system": {
                    "display_value": code_system,
                    "value": code_system
                },
                "target_site": {
                    "display_value": target_site_display,
                    "value": target_site
                },
                "laterality": {
                    "display_value": laterality,
                    "value": laterality
                },
                "status": {
                    "display_value": status,
                    "value": status
                }
            }
            
            # Add fallback flat fields with formatted values
            mapped_procedure["procedure_name"] = procedure_name
            mapped_procedure["name"] = procedure_name
            mapped_procedure["display_name"] = procedure_name
            mapped_procedure["date"] = procedure_date  # Formatted date
            mapped_procedure["procedure_code"] = procedure_code_display  # With fallback
            mapped_procedure["code_system"] = code_system
            mapped_procedure["target_site"] = target_site_display  # With fallback
            mapped_procedure["laterality"] = laterality
            mapped_procedure["status"] = status
            
            mapped_procedures.append(mapped_procedure)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped procedure: {procedure_name}")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_procedures

    def _map_immunization_fields(self, immunizations: List[Dict]) -> List[Dict]:
        """Map immunization data for template compatibility with comprehensive field support
        
        Comprehensive fields:
        - Vaccination (vaccine_name)
        - Brand Name (brand_name)
        - Vaccination Date (date_administered, date)
        - Agent (agent_code, agent_code_system, agent_display_name)
        - Marketing Authorization Holder (marketing_authorization_holder)
        - Dose number in series (dose_number)
        - Batch/lot number (lot_number, batch_number)
        - Administering Center (administering_center)
        - Health Professional Identification (health_professional_id, health_professional_name)
        - Country of Vaccination (country_of_vaccination)
        - Annotations (annotations)
        
        Template expects:
        - immunization.data.vaccine.display_value
        - immunization.data.date.display_value
        - immunization.data.brand_name.display_value
        - immunization.data.status.display_value
        """
        mapped_immunizations = []
        
        for immunization in immunizations:
            if not immunization:
                continue
                
            mapped_immunization = dict(immunization)  # Preserve ALL fields from service
            
            # Extract core immunization information
            vaccine_name = self._extract_vaccine_name(immunization)
            immunization_date_raw = immunization.get("date", immunization.get("date_administered", immunization.get("occurrence_date", "")))
            
            # Format date to European DD/MM/YYYY format (centralized formatter)
            from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
            immunization_date = ComprehensiveClinicalDataService.format_cda_date(immunization_date_raw)
            
            brand_name = immunization.get("brand_name", "")
            status = immunization.get("status", "Completed")
            dose_number = immunization.get("dose_number", "")
            lot_number = immunization.get("lot_number", immunization.get("batch_number", ""))
            route = immunization.get("route", "")
            site = immunization.get("site", "")
            
            # Agent information
            agent_code = immunization.get("agent_code", "")
            agent_display_name = immunization.get("agent_display_name", "")
            agent_code_system_name = immunization.get("agent_code_system_name", "")
            
            # Additional comprehensive fields
            marketing_auth_holder = immunization.get("marketing_authorization_holder", "")
            administering_center = immunization.get("administering_center", "")
            health_prof_id = immunization.get("health_professional_id", "")
            health_prof_name = immunization.get("health_professional_name", "")
            country = immunization.get("country_of_vaccination", "")
            annotations = immunization.get("annotations", "")
            
            # Create comprehensive data structure for template compatibility
            mapped_immunization["data"] = {
                "vaccine": {
                    "display_value": vaccine_name,
                    "value": vaccine_name
                },
                "date": {
                    "display_value": immunization_date,
                    "value": immunization_date
                },
                "brand_name": {
                    "display_value": brand_name,
                    "value": brand_name
                },
                "status": {
                    "display_value": status,
                    "value": status
                },
                "dose": {
                    "display_value": dose_number,
                    "value": dose_number
                },
                "lot_number": {
                    "display_value": lot_number,
                    "value": lot_number
                },
                "route": {
                    "display_value": route,
                    "value": route
                },
                "site": {
                    "display_value": site,
                    "value": site
                },
                "agent": {
                    "display_value": agent_display_name,
                    "value": agent_code,
                    "code_system": agent_code_system_name
                },
                "marketing_holder": {
                    "display_value": marketing_auth_holder,
                    "value": marketing_auth_holder
                },
                "administering_center": {
                    "display_value": administering_center,
                    "value": administering_center
                },
                "health_professional": {
                    "display_value": health_prof_name or health_prof_id,
                    "value": health_prof_id,
                    "name": health_prof_name
                },
                "country": {
                    "display_value": country,
                    "value": country
                },
                "annotations": {
                    "display_value": annotations,
                    "value": annotations
                }
            }
            
            # Add fallback flat fields for backward compatibility
            mapped_immunization["vaccine_name"] = vaccine_name
            mapped_immunization["name"] = vaccine_name
            mapped_immunization["display_name"] = vaccine_name
            mapped_immunization["date"] = immunization_date
            
            mapped_immunizations.append(mapped_immunization)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped immunization: {vaccine_name} on {immunization_date}")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_immunizations

    def _map_vital_signs_fields(self, vital_signs: List[Dict]) -> List[Dict]:
        """Map vital signs data for template compatibility"""
        mapped_vital_signs = []
        
        for vital_sign in vital_signs:
            if not vital_sign:
                continue
                
            mapped_vital_sign = dict(vital_sign)
            
            # Extract vital sign information
            vital_name = self._extract_vital_sign_name(vital_sign)
            vital_value = vital_sign.get("value", vital_sign.get("observation_value", ""))
            vital_unit = vital_sign.get("unit", "")
            vital_date = vital_sign.get("date", "")  # Already formatted by comprehensive service
            
            # Create data structure for template compatibility
            mapped_vital_sign["data"] = {
                "vital_sign": {
                    "display_value": vital_name,
                    "value": vital_name
                },
                "value": {
                    "display_value": f"{vital_value} {vital_unit}".strip(),
                    "value": vital_value
                },
                "unit": {
                    "display_value": vital_unit,
                    "value": vital_unit
                },
                "date": {
                    "display_value": vital_date,  # Already formatted by comprehensive service
                    "value": vital_date
                }
            }
            
            # Add fallback flat fields
            mapped_vital_sign["name"] = vital_name
            mapped_vital_sign["display_name"] = vital_name
            mapped_vital_sign["value"] = vital_value
            mapped_vital_sign["unit"] = vital_unit
            mapped_vital_sign["date"] = vital_date  # Already formatted by comprehensive service
            
            mapped_vital_signs.append(mapped_vital_sign)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped vital sign: {vital_name} = {vital_value} {vital_unit} on {vital_date}")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_vital_signs

    def _map_results_fields(self, results: List[Dict]) -> List[Dict]:
        """Map results data for template compatibility"""
        mapped_results = []
        
        for result in results:
            if not result:
                continue
                
            mapped_result = dict(result)
            
            # Extract result information
            result_name = self._extract_result_name(result)
            result_value = result.get("value", result.get("observation_value", ""))
            result_unit = result.get("unit", "")
            result_date = result.get("date", "")  # Already formatted by comprehensive service
            result_interpretation = result.get("interpretation", "")
            reference_range = result.get("reference_range", "")
            status = result.get("status", "Final")
            
            # Create data structure for template compatibility
            mapped_result["data"] = {
                "test": {
                    "display_value": result_name,
                    "value": result_name
                },
                "value": {
                    "display_value": f"{result_value} {result_unit}".strip(),
                    "value": result_value
                },
                "unit": {
                    "display_value": result_unit,
                    "value": result_unit
                },
                "date": {
                    "display_value": result_date,  # Already formatted by comprehensive service
                    "value": result_date
                },
                "interpretation": {
                    "display_value": result_interpretation,
                    "value": result_interpretation
                },
                "reference_range": {
                    "display_value": reference_range,
                    "value": reference_range
                },
                "status": {
                    "display_value": status,
                    "value": status
                }
            }
            
            # Add fallback flat fields
            mapped_result["name"] = result_name
            mapped_result["display_name"] = result_name
            mapped_result["value"] = result_value
            mapped_result["unit"] = result_unit
            mapped_result["date"] = result_date  # Already formatted by comprehensive service
            mapped_result["interpretation"] = result_interpretation
            mapped_result["reference_range"] = reference_range
            mapped_result["status"] = status
            
            mapped_results.append(mapped_result)
            
            self.mapping_stats["items_mapped"] += 1
            self.mapping_stats["data_structures_added"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped result: {result_name} = {result_value} {result_unit} on {result_date} ({result_interpretation or 'No interpretation'})")
        
        self.mapping_stats["sections_processed"] += 1
        return mapped_results

    # Extraction helper methods
    
    def _extract_allergen_name(self, allergy: Dict) -> str:
        """Extract allergen name from various possible field structures"""
        candidates = [
            allergy.get("allergen_name"),
            allergy.get("allergen"),
            allergy.get("substance_name"),
            allergy.get("display_name"),
            allergy.get("name"),
            allergy.get("observation_name"),
            allergy.get("observation_display"),
            allergy.get("problem_name"),  # Sometimes allergies are stored as problems
            allergy.get("code_display"),
            allergy.get("display_value"),
        ]
        
        # Try extracting from nested structures
        if "data" in allergy and isinstance(allergy["data"], dict):
            data = allergy["data"]
            candidates.extend([
                data.get("allergen_name"),
                data.get("allergen"),
                data.get("substance_name"),
                data.get("display_name"),
                data.get("name"),
                data.get("observation_name"),
                data.get("observation_display"),
            ])
        
        # Try extracting from the first field that contains substance info
        for field_name, field_value in allergy.items():
            if isinstance(field_value, str) and field_value.strip():
                if any(term in field_name.lower() for term in ["allergen", "substance", "agent", "trigger"]):
                    candidates.insert(0, field_value)  # Priority for allergy-specific fields
                elif any(term in field_name.lower() for term in ["name", "display"]) and "reaction" not in field_name.lower():
                    candidates.append(field_value)
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                clean_name = candidate.strip()
                # Skip generic values
                if clean_name.lower() not in ["unknown", "not specified", "n/a", "none"]:
                    return clean_name
        
        return "Unknown Allergen"

    def _extract_reaction_info(self, allergy: Dict) -> str:
        """Extract reaction information from allergy data"""
        candidates = [
            allergy.get("reaction"),
            allergy.get("reaction_display"),
            allergy.get("clinical_effect"),
            allergy.get("manifestation"),
            allergy.get("reaction_name"),
            allergy.get("adverse_reaction"),
        ]
        
        # Try extracting from nested structures
        if "data" in allergy and isinstance(allergy["data"], dict):
            data = allergy["data"]
            candidates.extend([
                data.get("reaction"),
                data.get("reaction_display"),
                data.get("clinical_effect"),
                data.get("manifestation"),
            ])
        
        # Try extracting from any field that contains reaction info
        for field_name, field_value in allergy.items():
            if isinstance(field_value, str) and field_value.strip():
                if any(term in field_name.lower() for term in ["reaction", "effect", "manifestation", "symptom"]):
                    candidates.insert(0, field_value)  # Priority for reaction-specific fields
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                clean_reaction = candidate.strip()
                # Skip generic values
                if clean_reaction.lower() not in ["unknown", "not specified", "n/a", "none"]:
                    return clean_reaction
        
        return "Not specified"

    def _extract_severity_info(self, allergy: Dict) -> str:
        """Extract severity information from allergy data"""
        candidates = [
            allergy.get("severity"),
            allergy.get("severity_display"),
            allergy.get("criticality"),
            "Moderate"  # Default severity
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return "Moderate"

    def _extract_problem_name(self, problem: Dict) -> str:
        """Extract problem name from various possible field structures"""
        candidates = [
            problem.get("problem_name"),
            problem.get("display_name"),
            problem.get("name"),
            problem.get("observation_name"),
            problem.get("observation_display"),
            problem.get("diagnosis"),
            problem.get("condition"),
            problem.get("code_display"),
            problem.get("display_value"),
        ]
        
        # Try extracting from nested structures
        if "data" in problem and isinstance(problem["data"], dict):
            data = problem["data"]
            candidates.extend([
                data.get("problem_name"),
                data.get("display_name"),
                data.get("name"),
                data.get("observation_name"),
                data.get("observation_display"),
            ])
        
        # Try extracting from any field that contains meaningful problem info
        for field_name, field_value in problem.items():
            if isinstance(field_value, str) and field_value.strip():
                if any(term in field_name.lower() for term in ["problem", "diagnosis", "condition", "disease"]):
                    candidates.insert(0, field_value)  # Priority for problem-specific fields
                elif any(term in field_name.lower() for term in ["name", "display"]) and "status" not in field_name.lower():
                    candidates.append(field_value)
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                clean_name = candidate.strip()
                # Skip generic values
                if clean_name.lower() not in ["unknown", "not specified", "n/a", "none", "problem"]:
                    return clean_name
        
        return "Unknown Problem"

    def _extract_problem_status(self, problem: Dict) -> str:
        """Extract problem status information"""
        candidates = [
            problem.get("status"),
            problem.get("problem_status"),
            problem.get("clinical_status"),
            "Active"  # Default status
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return "Active"

    def _extract_problem_type(self, problem: Dict) -> str:
        """Extract problem type information"""
        candidates = [
            problem.get("problem_type"),
            problem.get("type"),
            problem.get("category"),
            "Clinical finding"  # Default type
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return "Clinical finding"

    def _extract_clinical_status(self, problem: Dict) -> str:
        """Extract clinical status information"""
        candidates = [
            problem.get("clinical_status"),
            problem.get("verification_status"),
            problem.get("status"),
            ""  # Empty if not found
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return ""

    def _extract_procedure_name(self, procedure: Dict) -> str:
        """Extract procedure name from various possible field structures"""
        candidates = [
            procedure.get("procedure_name"),
            procedure.get("display_name"),
            procedure.get("name"),
            procedure.get("observation_name"),
            procedure.get("observation_display"),
            procedure.get("code_display"),
            procedure.get("display_value"),
            procedure.get("intervention"),
            procedure.get("operation"),
        ]
        
        # Try extracting from nested structures
        if "data" in procedure and isinstance(procedure["data"], dict):
            data = procedure["data"]
            candidates.extend([
                data.get("procedure_name"),
                data.get("display_name"),
                data.get("name"),
                data.get("observation_name"),
                data.get("observation_display"),
            ])
        
        # Try extracting from any field that contains meaningful procedure info
        # CRITICAL FIX: Exclude code/id fields from name extraction
        for field_name, field_value in procedure.items():
            if isinstance(field_value, str) and field_value.strip():
                # Skip fields that are clearly codes or IDs, not names
                if any(skip_term in field_name.lower() for skip_term in ["code", "id", "oid", "system", "reference"]):
                    continue
                if any(term in field_name.lower() for term in ["procedure", "intervention", "operation", "surgery", "treatment"]):
                    candidates.insert(0, field_value)  # Priority for procedure-specific fields
                elif any(term in field_name.lower() for term in ["name", "display"]) and "date" not in field_name.lower():
                    candidates.append(field_value)
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                clean_name = candidate.strip()
                # Skip generic values
                if clean_name.lower() not in ["unknown", "not specified", "n/a", "none", "procedure"]:
                    return clean_name
        
        return "Unknown Procedure"

    def _extract_vaccine_name(self, immunization: Dict) -> str:
        """Extract vaccine name from various possible field structures"""
        candidates = [
            immunization.get("vaccine_name"),
            immunization.get("display_name"),
            immunization.get("name"),
            immunization.get("observation_name"),
            immunization.get("observation_display"),
            immunization.get("substance_name"),
            immunization.get("code_display"),
            immunization.get("display_value"),
            immunization.get("immunization_name"),
        ]
        
        # Try extracting from nested structures
        if "data" in immunization and isinstance(immunization["data"], dict):
            data = immunization["data"]
            candidates.extend([
                data.get("vaccine_name"),
                data.get("display_name"),
                data.get("name"),
                data.get("observation_name"),
                data.get("observation_display"),
                data.get("substance_name"),
            ])
        
        # Try extracting from any field that contains meaningful vaccine info
        # CRITICAL: Exclude fields that are clearly not vaccine names (country, date, status, etc.)
        for field_name, field_value in immunization.items():
            if isinstance(field_value, str) and field_value.strip():
                # Skip fields that are not vaccine names
                if any(skip in field_name.lower() for skip in ["country", "date", "status", "route", "site", "center", "holder", "professional", "annotation", "lot", "batch", "dose"]):
                    continue
                if any(term in field_name.lower() for term in ["vaccine_name", "immunization_name"]):
                    candidates.insert(0, field_value)  # Highest priority for exact vaccine name fields
                elif any(term in field_name.lower() for term in ["name", "display"]):
                    candidates.append(field_value)
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                clean_name = candidate.strip()
                # Skip generic values
                if clean_name.lower() not in ["unknown", "not specified", "n/a", "none", "vaccine", "immunization"]:
                    return clean_name
        
        return "Unknown Vaccine"

    def _extract_vital_sign_name(self, vital_sign: Dict) -> str:
        """Extract vital sign name from various possible field structures"""
        candidates = [
            vital_sign.get("vital_sign_name"),
            vital_sign.get("display_name"),
            vital_sign.get("name"),
            vital_sign.get("observation_name"),
            vital_sign.get("observation_display"),
            "Unknown Vital Sign"
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return "Unknown Vital Sign"

    def _extract_result_name(self, result: Dict) -> str:
        """Extract result name from various possible field structures"""
        candidates = [
            result.get("result_name"),
            result.get("display_name"),
            result.get("name"),
            result.get("observation_name"),
            result.get("observation_display"),
            result.get("test_name"),
            "Unknown Result"
        ]
        
        for candidate in candidates:
            if candidate and isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        
        return "Unknown Result"

    def _map_medical_devices_fields(self, medical_devices: List[Dict]) -> List[Dict]:
        """Map medical devices data for template compatibility
        
        Expected fields:
        - Device Type (device_type, name)
        - Device ID (device_id)
        - Implant Date (implant_date)
        - Removal Date (removal_date) - optional
        - Device Code (device_code)
        - Status (Active/Removed)
        
        Template expects:
        - device.data.device_type.display_value
        - device.data.device_id.display_value
        - device.data.implant_date.display_value
        """
        mapped_devices = []
        
        for device in medical_devices:
            if not device:
                continue
            
            mapped_device = dict(device)  # Preserve ALL fields from service
            
            # Extract device information
            device_type = device.get("device_type", device.get("name", "Unknown device"))
            device_id = device.get("device_id", "Not specified")
            device_code = device.get("device_code", "")
            status = device.get("status", "Active")
            
            # Format dates to European DD/MM/YYYY format
            implant_date_raw = device.get("implant_date", "")
            removal_date_raw = device.get("removal_date", "")
            
            from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
            implant_date = ComprehensiveClinicalDataService.format_cda_date(implant_date_raw) if implant_date_raw else "Not recorded"
            removal_date = ComprehensiveClinicalDataService.format_cda_date(removal_date_raw) if removal_date_raw else ""
            
            # Create comprehensive data structure for template compatibility
            mapped_device["data"] = {
                "device_type": {
                    "display_value": device_type,
                    "value": device_type,
                    "code": device_code
                },
                "device_id": {
                    "display_value": device_id,
                    "value": device_id
                },
                "implant_date": {
                    "display_value": implant_date,
                    "value": implant_date_raw
                },
                "removal_date": {
                    "display_value": removal_date,
                    "value": removal_date_raw
                },
                "status": {
                    "display_value": status,
                    "value": status
                }
            }
            
            # Add fallback flat fields for backward compatibility
            mapped_device["name"] = device_type
            mapped_device["display_name"] = device_type
            mapped_device["device_type"] = device_type
            mapped_device["device_id"] = device_id
            mapped_device["implant_date"] = implant_date
            mapped_device["removal_date"] = removal_date
            mapped_device["status"] = status
            
            mapped_devices.append(mapped_device)
            self.mapping_stats["items_mapped"] += 1
        
        if mapped_devices:
            self.mapping_stats["sections_processed"] += 1
            logger.info(f"[FIELD_MAPPER] Mapped {len(mapped_devices)} medical devices")
        
        return mapped_devices
    
    def _map_past_illness_fields(self, past_illnesses: List[Dict]) -> List[Dict]:
        """Map past illness data for template compatibility
        
        Expected fields per user requirements:
        1. Closed/Inactive Problem (problem_name)
        2. Problem Type
        3. Time (from-to timeline)
        4. Problem Status
        5. Health Status
        
        Template expects:
        - illness.data.problem_name.display_value
        - illness.data.problem_type.display_value
        - illness.data.time_period.display_value
        - illness.data.problem_status.display_value
        - illness.data.health_status.display_value
        """
        mapped_illnesses = []
        
        for illness in past_illnesses:
            if not illness:
                continue
            
            mapped_illness = dict(illness)  # Preserve ALL fields from service
            
            # Extract illness information
            problem_name = illness.get("problem_name", "Unknown Problem")
            problem_type = illness.get("problem_type", "Problem")
            problem_status_raw = illness.get("problem_status", "Not specified")
            health_status_raw = illness.get("health_status", "Not specified")
            problem_code = illness.get("problem_code", "")
            problem_code_system = illness.get("problem_code_system", "")
            
            logger.info(f"[FIELD_MAPPER] Past Illness - Raw data: name='{problem_name}', code='{problem_code}', system='{problem_code_system}', problem_status='{problem_status_raw}', health_status='{health_status_raw}'")
            
            # Apply CTS translation if codes are not already translated
            # Check if problem_name looks like a code (contains "ref:" or is same as problem_code)
            if problem_name and ("ref:" in problem_name or problem_name == problem_code or len(problem_name) < 10):
                logger.info(f"[FIELD_MAPPER] Problem name needs translation: '{problem_name}'")
                if problem_code and problem_code_system:
                    try:
                        from patient_data.services.cts_integration.cts_service import CTSService
                        cts_service = CTSService()
                        logger.info(f"[FIELD_MAPPER] Calling CTS for code={problem_code}, system={problem_code_system}")
                        cts_result = cts_service.get_term_display(problem_code, problem_code_system)
                        logger.info(f"[FIELD_MAPPER] CTS returned: '{cts_result}'")
                        if cts_result and cts_result != problem_code:
                            problem_name = cts_result
                            logger.info(f"[FIELD_MAPPER] CTS resolved problem code {problem_code} to: {problem_name}")
                        else:
                            logger.warning(f"[FIELD_MAPPER] CTS returned no useful result for {problem_code}")
                    except Exception as cts_error:
                        logger.error(f"[FIELD_MAPPER] CTS resolution failed for problem {problem_code}: {cts_error}", exc_info=True)
                else:
                    logger.warning(f"[FIELD_MAPPER] Cannot translate problem_name - missing code or system")
            
            # Translate problem_status if it looks like a code (numeric SNOMED code)
            problem_status = problem_status_raw
            if problem_status_raw and problem_status_raw.isdigit():
                logger.info(f"[FIELD_MAPPER] Problem status needs translation: '{problem_status_raw}'")
                try:
                    from patient_data.services.cts_integration.cts_service import CTSService
                    cts_service = CTSService()
                    cts_result = cts_service.get_term_display(problem_status_raw, "2.16.840.1.113883.6.96")  # SNOMED CT
                    logger.info(f"[FIELD_MAPPER] CTS returned for problem_status: '{cts_result}'")
                    if cts_result and cts_result != problem_status_raw:
                        problem_status = cts_result
                        logger.info(f"[FIELD_MAPPER] CTS resolved problem_status code {problem_status_raw} to: {problem_status}")
                    else:
                        logger.warning(f"[FIELD_MAPPER] CTS returned no useful result for problem_status {problem_status_raw}")
                except Exception as cts_error:
                    logger.error(f"[FIELD_MAPPER] CTS resolution failed for problem_status {problem_status_raw}: {cts_error}", exc_info=True)
            
            # Translate health_status if it looks like a code (numeric SNOMED code)
            health_status = health_status_raw
            if health_status_raw and health_status_raw.isdigit():
                logger.info(f"[FIELD_MAPPER] Health status needs translation: '{health_status_raw}'")
                try:
                    from patient_data.services.cts_integration.cts_service import CTSService
                    cts_service = CTSService()
                    cts_result = cts_service.get_term_display(health_status_raw, "2.16.840.1.113883.6.96")  # SNOMED CT
                    logger.info(f"[FIELD_MAPPER] CTS returned for health_status: '{cts_result}'")
                    if cts_result and cts_result != health_status_raw:
                        health_status = cts_result
                        logger.info(f"[FIELD_MAPPER] CTS resolved health_status code {health_status_raw} to: {health_status}")
                    else:
                        logger.warning(f"[FIELD_MAPPER] CTS returned no useful result for health_status {health_status_raw}")
                except Exception as cts_error:
                    logger.error(f"[FIELD_MAPPER] CTS resolution failed for health_status {health_status_raw}: {cts_error}", exc_info=True)
            
            # Format time period to European DD/MM/YYYY format
            time_low_raw = illness.get("time_low", "")
            time_high_raw = illness.get("time_high", "")
            
            from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
            time_low = ComprehensiveClinicalDataService.format_cda_date(time_low_raw) if time_low_raw else ""
            time_high = ComprehensiveClinicalDataService.format_cda_date(time_high_raw) if time_high_raw else ""
            
            # Create time period display (from-to or just from)
            if time_low and time_high:
                time_period = f"{time_low} to {time_high}"
            elif time_low:
                time_period = f"From {time_low}"
            elif time_high:
                time_period = f"Until {time_high}"
            else:
                time_period = "Not recorded"
            
            # Determine if problem is closed/inactive
            act_status = illness.get("act_status", "completed")
            is_closed = act_status.lower() == "completed" and time_high
            status_display = "Closed/Inactive" if is_closed else "Active"
            
            # Create comprehensive data structure for template compatibility
            mapped_illness["data"] = {
                "problem_name": {
                    "display_value": problem_name,
                    "value": problem_name,
                    "code": problem_code
                },
                "problem_type": {
                    "display_value": problem_type,
                    "value": problem_type
                },
                "time_period": {
                    "display_value": time_period,
                    "time_low": time_low,
                    "time_high": time_high,
                    "raw_low": time_low_raw,
                    "raw_high": time_high_raw
                },
                "problem_status": {
                    "display_value": problem_status,
                    "value": problem_status
                },
                "health_status": {
                    "display_value": health_status,
                    "value": health_status
                },
                "status": {
                    "display_value": status_display,
                    "value": is_closed,
                    "is_closed": is_closed
                }
            }
            
            # Add fallback flat fields for backward compatibility
            mapped_illness["name"] = problem_name
            mapped_illness["display_name"] = problem_name
            mapped_illness["problem_name"] = problem_name
            mapped_illness["problem_type"] = problem_type
            mapped_illness["time_period"] = time_period
            mapped_illness["time_low"] = time_low
            mapped_illness["time_high"] = time_high
            mapped_illness["problem_status"] = problem_status
            mapped_illness["health_status"] = health_status
            mapped_illness["is_closed"] = is_closed
            mapped_illness["status_display"] = status_display
            
            mapped_illnesses.append(mapped_illness)
            self.mapping_stats["items_mapped"] += 1
            
            # LOG FINAL MAPPED STRUCTURE (removed emojis for Windows console compatibility)
            logger.info(f"[FIELD_MAPPER] Mapped illness #{len(mapped_illnesses)}:")
            logger.info(f"  - data.problem_name.display_value: '{mapped_illness['data']['problem_name']['display_value']}'")
            logger.info(f"  - data.problem_name.code: '{mapped_illness['data']['problem_name']['code']}'")
            logger.info(f"  - data.problem_type.display_value: '{mapped_illness['data']['problem_type']['display_value']}'")
            logger.info(f"  - data.time_period.display_value: '{mapped_illness['data']['time_period']['display_value']}'")
            logger.info(f"  - data.problem_status.display_value: '{mapped_illness['data']['problem_status']['display_value']}'")
            logger.info(f"  - data.health_status.display_value: '{mapped_illness['data']['health_status']['display_value']}'")
            logger.info(f"  - data.status.display_value: '{mapped_illness['data']['status']['display_value']}'")
        
        if mapped_illnesses:
            self.mapping_stats["sections_processed"] += 1
            logger.info(f"[FIELD_MAPPER] FINAL: Returning {len(mapped_illnesses)} mapped past illnesses to context")
        
        return mapped_illnesses

    def _map_pregnancy_history_fields(self, pregnancies: List[Dict]) -> List[Dict]:
        """
        Map pregnancy history data for template compatibility.
        
        Template expects nested structure:
        - pregnancy.data.outcome.display_value
        - pregnancy.data.status.display_value
        - pregnancy.data.delivery_date.display_value
        - pregnancy.data.gestational_age.display_value
        - pregnancy.pregnancy_type ('current' or 'past')
        
        Applies CTS fallback for outcome codes if primary translation failed.
        """
        if not pregnancies:
            return []
        
        logger.info(f"[FIELD_MAPPER] Pregnancy History - Mapping {len(pregnancies)} pregnancy records")
        
        mapped_pregnancies = []
        
        for pregnancy in pregnancies:
            # Get raw values
            pregnancy_type = pregnancy.get('pregnancy_type', 'past')
            outcome = pregnancy.get('outcome', 'Not specified')
            outcome_code = pregnancy.get('outcome_code')
            outcome_system = pregnancy.get('outcome_system')
            status = pregnancy.get('status', 'Not specified')
            status_code = pregnancy.get('status_code')
            delivery_date = pregnancy.get('delivery_date', 'Not specified')
            delivery_date_estimated = pregnancy.get('delivery_date_estimated', 'Not specified')
            observation_date = pregnancy.get('observation_date', 'Not specified')
            gestational_age = pregnancy.get('gestational_age', 'Not specified')
            birth_weight = pregnancy.get('birth_weight', 'Not specified')
            complications = pregnancy.get('complications', 'None reported')
            delivery_method = pregnancy.get('delivery_method', 'Not specified')
            pregnancy_number = pregnancy.get('pregnancy_number', 'Not specified')
            
            logger.info(f"[FIELD_MAPPER] Pregnancy - Raw data: type='{pregnancy_type}', outcome='{outcome}', delivery_date='{delivery_date}'")
            
            # CTS fallback for outcome if still coded
            if outcome_code and outcome_system and (len(outcome) < 10 or outcome == outcome_code):
                logger.info(f"[FIELD_MAPPER] Pregnancy outcome needs translation: '{outcome}'")
                logger.info(f"[FIELD_MAPPER] Calling CTS for code={outcome_code}, system={outcome_system}")
                
                from patient_data.services.cts_integration.cts_service import CTSService
                cts_service = CTSService()
                cts_result = cts_service.get_term_display(outcome_code, outcome_system)
                
                logger.info(f"[FIELD_MAPPER] CTS returned for outcome: '{cts_result}'")
                
                if cts_result and cts_result != outcome_code:
                    outcome = cts_result
                else:
                    logger.warning(f"[FIELD_MAPPER] CTS returned no useful result for outcome {outcome_code}")
            
            # Format delivery date to DD/MM/YYYY
            formatted_delivery_date = self._format_cda_date(delivery_date) if delivery_date != 'Not specified' else 'Not specified'
            formatted_delivery_date_estimated = self._format_cda_date(delivery_date_estimated) if delivery_date_estimated != 'Not specified' else 'Not specified'
            formatted_observation_date = self._format_cda_date(observation_date) if observation_date != 'Not specified' else 'Not specified'
            
            # Build nested data structure for template
            mapped_pregnancy = {
                # Original fields for fallback compatibility
                'description': pregnancy.get('description', 'Pregnancy record'),
                'pregnancy_type': pregnancy_type,
                'pregnancy_number': pregnancy_number,
                'outcome': outcome,
                'status': status,
                'delivery_date': formatted_delivery_date,
                'delivery_date_estimated': formatted_delivery_date_estimated,
                'observation_date': formatted_observation_date,
                'gestational_age': gestational_age,
                'birth_weight': birth_weight,
                'complications': complications,
                'delivery_method': delivery_method,
                
                # Enhanced nested data structure for modern template
                'data': {
                    'pregnancy_type': {
                        'display_value': pregnancy_type.capitalize(),
                        'code': pregnancy_type,
                        'code_system': 'internal'
                    },
                    'outcome': {
                        'display_value': outcome,
                        'code': outcome_code,
                        'code_system': outcome_system
                    },
                    'status': {
                        'display_value': status,
                        'code': status_code,
                        'code_system': outcome_system
                    },
                    'delivery_date': {
                        'display_value': formatted_delivery_date,
                        'raw_value': delivery_date
                    },
                    'delivery_date_estimated': {
                        'display_value': formatted_delivery_date_estimated,
                        'raw_value': delivery_date_estimated
                    },
                    'observation_date': {
                        'display_value': formatted_observation_date,
                        'raw_value': observation_date
                    },
                    'gestational_age': {
                        'display_value': gestational_age
                    },
                    'birth_weight': {
                        'display_value': birth_weight
                    },
                    'complications': {
                        'display_value': complications
                    },
                    'delivery_method': {
                        'display_value': delivery_method
                    },
                    'pregnancy_number': {
                        'display_value': pregnancy_number
                    }
                }
            }
            
            mapped_pregnancies.append(mapped_pregnancy)
            self.mapping_stats["items_mapped"] += 1
            
            # Log final mapped structure
            logger.info(f"[FIELD_MAPPER] Mapped pregnancy #{len(mapped_pregnancies)}:")
            logger.info(f"  - data.pregnancy_type.display_value: '{mapped_pregnancy['data']['pregnancy_type']['display_value']}'")
            logger.info(f"  - data.outcome.display_value: '{mapped_pregnancy['data']['outcome']['display_value']}'")
            logger.info(f"  - data.delivery_date.display_value: '{mapped_pregnancy['data']['delivery_date']['display_value']}'")
        
        if mapped_pregnancies:
            self.mapping_stats["sections_processed"] += 1
            logger.info(f"[FIELD_MAPPER] FINAL: Returning {len(mapped_pregnancies)} mapped pregnancy records to context")
        
        return mapped_pregnancies

    def _map_social_history_fields(self, social_history: List[Dict]) -> List[Dict]:
        """Map social history data for template compatibility
        
        User Requirements:
        1. Observation Type (category)
        2. Observation Value (description)
        3. Observation Time (start_date/end_date)
        
        Template expects:
        - social.data.observation_type.display_value
        - social.data.observation_value.display_value
        - social.data.observation_time.display_value
        """
        mapped_social = []
        
        for social in social_history:
            if not social:
                continue
            
            mapped_item = dict(social)  # Preserve ALL fields from service
            
            # Extract social history information
            observation_type = social.get("category", "Lifestyle")
            observation_value = social.get("description", "Not specified")
            quantity = social.get("quantity", "Not specified")
            frequency = social.get("frequency", "Not specified")
            value_code = social.get("value_code")
            value_system = social.get("value_system")
            start_date_raw = social.get("start_date", "")
            end_date_raw = social.get("end_date", "")
            status = social.get("status", "Active")
            
            # If we have a quantity, use it as the observation value
            if quantity != "Not specified" and quantity != "":
                observation_value = quantity
            
            # Try CTS translation for observation value if we have a code
            if value_code and value_system and observation_value in [value_code, "Not specified"]:
                logger.info(f"[FIELD_MAPPER] Social history observation value needs translation: '{value_code}'")
                logger.info(f"[FIELD_MAPPER] Calling CTS for code={value_code}, system={value_system}")
                
                from patient_data.services.cts_integration.cts_service import CTSService
                cts_service = CTSService()
                cts_result = cts_service.get_term_display(value_code, value_system)
                
                logger.info(f"[FIELD_MAPPER] CTS returned for observation value: '{cts_result}'")
                
                if cts_result and cts_result != value_code:
                    observation_value = cts_result
                    logger.info(f"[FIELD_MAPPER] Using CTS translation: '{observation_value}'")
                else:
                    logger.warning(f"[FIELD_MAPPER] CTS returned no useful result for observation value {value_code}")
                    # Keep original value_code as fallback
                    if observation_value == "Not specified":
                        observation_value = f"Code: {value_code}"
            
            # Format dates to European DD/MM/YYYY format
            start_date = self._format_cda_date(start_date_raw) if start_date_raw and start_date_raw != "Not specified" else ""
            end_date = self._format_cda_date(end_date_raw) if end_date_raw and end_date_raw != "Not specified" else ""
            
            # Create observation time display
            if start_date and end_date:
                observation_time = f"{start_date} to {end_date}"
            elif start_date:
                observation_time = f"From {start_date}"
            elif end_date:
                observation_time = f"Until {end_date}"
            else:
                observation_time = "Not recorded"
            
            # Create comprehensive data structure for template compatibility
            mapped_item["data"] = {
                "observation_type": {
                    "display_value": observation_type,
                    "value": observation_type
                },
                "observation_value": {
                    "display_value": observation_value,
                    "value": observation_value,
                    "quantity": quantity,
                    "frequency": frequency
                },
                "observation_time": {
                    "display_value": observation_time,
                    "start_date": start_date,
                    "end_date": end_date,
                    "raw_start": start_date_raw,
                    "raw_end": end_date_raw
                },
                "status": {
                    "display_value": status,
                    "value": status,
                    "is_active": status.lower() == "active"
                }
            }
            
            # Add fallback flat fields for backward compatibility
            mapped_item["name"] = f"{observation_type}: {observation_value}"
            mapped_item["display_name"] = observation_type
            mapped_item["observation_type"] = observation_type
            mapped_item["observation_value"] = observation_value
            mapped_item["quantity"] = quantity
            mapped_item["frequency"] = frequency
            mapped_item["observation_time"] = observation_time
            mapped_item["status"] = status
            
            mapped_social.append(mapped_item)
            self.mapping_stats["items_mapped"] += 1
            
            # LOG FINAL MAPPED STRUCTURE
            logger.info(f"[FIELD_MAPPER] Mapped social history #{len(mapped_social)}:")
            logger.info(f"  - data.observation_type.display_value: '{mapped_item['data']['observation_type']['display_value']}'")
            logger.info(f"  - data.observation_value.display_value: '{mapped_item['data']['observation_value']['display_value']}'")
            logger.info(f"  - data.observation_time.display_value: '{mapped_item['data']['observation_time']['display_value']}'")
        
        if mapped_social:
            self.mapping_stats["sections_processed"] += 1
            logger.info(f"[FIELD_MAPPER] FINAL: Returning {len(mapped_social)} mapped social history items to context")
        
        return mapped_social

    def _map_functional_status_fields(self, functional_status: List[Dict]) -> List[Dict]:
        """Map functional status data for template compatibility
        
        User Requirements:
        1. Observation Time (assessment_date)
        2. Observation Code (assessment + category)
        3. Onset Time (not in current data - using assessment_date)
        4. Result (level + score)
        
        Template expects:
        - status.data.observation_time.display_value
        - status.data.observation_code.display_value
        - status.data.onset_time.display_value
        - status.data.result.display_value
        """
        mapped_status = []
        
        for status in functional_status:
            if not status:
                continue
            
            mapped_item = dict(status)  # Preserve ALL fields from service
            
            # Extract functional status information
            assessment = status.get("assessment", "General assessment")
            category = status.get("category", "ADL")
            score = status.get("score", "Not specified")
            level = status.get("level", "Not specified")
            assessment_date_raw = status.get("assessment_date", "")
            
            # Format assessment date to European DD/MM/YYYY format
            observation_time = self._format_cda_date(assessment_date_raw) if assessment_date_raw and assessment_date_raw != "Not specified" else "Not recorded"
            onset_time = observation_time  # Using same as observation time since onset not in data
            
            # Create observation code display (assessment type + category)
            observation_code = f"{assessment} ({category})"
            
            # Create result display (level + score if available)
            if level != "Not specified" and score != "Not specified":
                result = f"{level} - Score: {score}"
            elif level != "Not specified":
                result = level
            elif score != "Not specified":
                result = f"Score: {score}"
            else:
                result = "Not specified"
            
            # Create comprehensive data structure for template compatibility
            mapped_item["data"] = {
                "observation_time": {
                    "display_value": observation_time,
                    "raw_date": assessment_date_raw
                },
                "observation_code": {
                    "display_value": observation_code,
                    "assessment": assessment,
                    "category": category
                },
                "onset_time": {
                    "display_value": onset_time,
                    "raw_date": assessment_date_raw
                },
                "result": {
                    "display_value": result,
                    "level": level,
                    "score": score
                }
            }
            
            # Add fallback flat fields for backward compatibility
            mapped_item["name"] = assessment
            mapped_item["display_name"] = assessment
            mapped_item["observation_time"] = observation_time
            mapped_item["observation_code"] = observation_code
            mapped_item["onset_time"] = onset_time
            mapped_item["result"] = result
            
            mapped_status.append(mapped_item)
            self.mapping_stats["items_mapped"] += 1
            
            # LOG FINAL MAPPED STRUCTURE
            logger.info(f"[FIELD_MAPPER] Mapped functional status #{len(mapped_status)}:")
            logger.info(f"  - data.observation_time.display_value: '{mapped_item['data']['observation_time']['display_value']}'")
            logger.info(f"  - data.observation_code.display_value: '{mapped_item['data']['observation_code']['display_value']}'")
            logger.info(f"  - data.onset_time.display_value: '{mapped_item['data']['onset_time']['display_value']}'")
            logger.info(f"  - data.result.display_value: '{mapped_item['data']['result']['display_value']}'")
        
        if mapped_status:
            self.mapping_stats["sections_processed"] += 1
            logger.info(f"[FIELD_MAPPER] FINAL: Returning {len(mapped_status)} mapped functional status assessments to context")
        
        return mapped_status

    def get_mapping_statistics(self) -> Dict[str, int]:
        """Get mapping statistics for debugging and monitoring"""
        return self.mapping_stats.copy()
