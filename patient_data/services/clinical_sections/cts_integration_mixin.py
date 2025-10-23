"""
CTS Integration Mixin for Clinical Services

This mixin provides standardized clinical code resolution using the CTS (Clinical Terminology Service)
for all clinical section services. It implements a priority-based resolution system:

1. CTS Agent Resolution (SNOMED CT, ATC, FHIR codes)
2. Text Reference Resolution 
3. DisplayName Resolution (with typo handling)
4. Fallback Code Mappings

Usage:
    class ProblemsSectionService(CTSIntegrationMixin, BaseClinicalSectionService):
        def extract_problem_data(self, observation):
            problem_code = self._extract_code_with_cts(
                observation, 
                xpath=".//hl7:value[@xsi:type='CD']",
                code_systems=['2.16.840.1.113883.6.96'],  # SNOMED CT
                fallback_name="Unknown Problem"
            )
"""

import logging
from typing import Dict, List, Optional, Any


class CTSIntegrationMixin:
    """
    Mixin providing standardized CTS (Clinical Terminology Service) integration
    for clinical code resolution across all clinical section services.
    """
    
    def __init__(self, *args, **kwargs):
        # Call parent __init__ to ensure proper MRO initialization
        super().__init__(*args, **kwargs)
        # Ensure logger is available
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def _resolve_clinical_code_with_cts(
        self, 
        code: str, 
        code_system: str, 
        display_name: str = "", 
        text_reference: str = "",
        fallback_mappings: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Resolve clinical code using CTS service with comprehensive fallback strategy.
        
        Args:
            code: Clinical code (e.g., "420134006")
            code_system: Code system OID (e.g., "2.16.840.1.113883.6.96" for SNOMED CT)
            display_name: DisplayName attribute from CDA (may have typos)
            text_reference: Resolved text reference content
            fallback_mappings: Local code mappings for known codes
            
        Returns:
            str: Resolved clinical term
        """
        if not code or not code_system:
            return text_reference or display_name or "Unknown"
        
        # Priority 1: CTS Agent Resolution for Clinical Codes
        if self._should_use_cts_for_code_system(code_system):
            try:
                from patient_data.services.cts_integration.cts_service import CTSService
                cts_service = CTSService()
                cts_result = cts_service.get_term_display(code, code_system)
                if cts_result and cts_result != code:
                    self.logger.debug(f"CTS resolved {code} ({code_system}) → {cts_result}")
                    return cts_result
            except Exception as cts_error:
                self.logger.warning(f"CTS resolution failed for {code} ({code_system}): {cts_error}")
        
        # Priority 2: Text Reference Resolution (most reliable from CDA text sections)
        if text_reference and text_reference.strip():
            self.logger.debug(f"Using text reference for {code}: {text_reference}")
            return text_reference.strip()
        
        # Priority 3: Handle Known DisplayName Issues and Apply Local Mappings
        if fallback_mappings and code.lower() in fallback_mappings:
            mapped_value = fallback_mappings[code.lower()]
            self.logger.debug(f"Using fallback mapping for {code}: {mapped_value}")
            return mapped_value
        
        # Priority 4: Clean DisplayName (handle common typos)
        cleaned_display = self._clean_display_name(display_name)
        if cleaned_display:
            return cleaned_display
        
        # Final fallback
        return code if code else "Unknown"
    
    def _should_use_cts_for_code_system(self, code_system: str) -> bool:
        """
        Determine if CTS should be used for the given code system.
        
        Returns True for:
        - SNOMED CT (2.16.840.1.113883.6.96)
        - ATC (2.16.840.1.113883.6.73) 
        - FHIR Value Sets (2.16.840.1.113883.4.642.*)
        - LOINC (2.16.840.1.113883.6.1)
        - ICD-10 (2.16.840.1.113883.6.3)
        """
        cts_code_systems = [
            '2.16.840.1.113883.6.96',    # SNOMED CT
            '2.16.840.1.113883.6.73',    # ATC
            '2.16.840.1.113883.6.1',     # LOINC
            '2.16.840.1.113883.6.3',     # ICD-10
            '2.16.840.1.113883.4.642',   # FHIR Value Sets (prefix)
        ]
        
        return any(code_system.startswith(cts_system) for cts_system in cts_code_systems)
    
    def _clean_display_name(self, display_name: str) -> str:
        """
        Clean display names and handle common CDA typos.
        
        Args:
            display_name: Original display name from CDA
            
        Returns:
            str: Cleaned display name
        """
        if not display_name:
            return ""
        
        # Common typo corrections found in European CDA documents
        typo_corrections = {
            'inctive': 'inactive',
            'comfirmed': 'confirmed', 
            'supsended': 'suspended',
            'moderte': 'moderate',
            'severy': 'severe'
        }
        
        cleaned = display_name.strip()
        
        # Apply typo corrections (case-insensitive)
        for typo, correction in typo_corrections.items():
            if typo in cleaned.lower():
                cleaned = cleaned.replace(typo.title(), correction.title())
                cleaned = cleaned.replace(typo.lower(), correction.lower())
                cleaned = cleaned.replace(typo.upper(), correction.upper())
        
        return cleaned
    
    def _extract_code_with_cts(
        self, 
        element, 
        xpath: str,
        code_systems: Optional[List[str]] = None,
        fallback_name: str = "Unknown",
        fallback_mappings: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Extract and resolve clinical code from XML element using CTS.
        
        Args:
            element: XML element to search
            xpath: XPath to find the code element
            code_systems: List of code systems to prioritize for CTS resolution
            fallback_name: Default name if resolution fails
            fallback_mappings: Local code mappings
            
        Returns:
            str: Resolved clinical term
        """
        try:
            code_elements = element.findall(xpath, getattr(self, 'namespaces', {}))
            
            for code_elem in code_elements:
                code = code_elem.get('code', '')
                code_system = code_elem.get('codeSystem', '')
                display_name = code_elem.get('displayName', '')
                
                # Skip if not in target code systems (if specified)
                if code_systems and code_system not in code_systems:
                    continue
                
                # Resolve text reference
                text_reference = ""
                original_text = code_elem.find('.//hl7:originalText', getattr(self, 'namespaces', {}))
                if original_text is not None:
                    ref_elem = original_text.find('hl7:reference', getattr(self, 'namespaces', {}))
                    if ref_elem is not None:
                        ref_value = ref_elem.get('value', '')
                        text_reference = self._resolve_text_reference(element, ref_value)
                
                # Resolve using CTS
                resolved_term = self._resolve_clinical_code_with_cts(
                    code=code,
                    code_system=code_system,
                    display_name=display_name,
                    text_reference=text_reference,
                    fallback_mappings=fallback_mappings
                )
                
                if resolved_term and resolved_term != "Unknown":
                    return resolved_term
            
            return fallback_name
            
        except Exception as e:
            self.logger.error(f"Error extracting code with CTS: {e}")
            return fallback_name
    
    def _extract_status_with_cts(
        self, 
        observation, 
        status_code_xpath: str = ".//hl7:entryRelationship[@typeCode='REFR']/hl7:observation/hl7:value[@xsi:type='CD']",
        parent_act_fallback: bool = True
    ) -> str:
        """
        Extract status using CTS with standardized fallback to parent act status.
        
        Args:
            observation: Observation element
            status_code_xpath: XPath to status code element
            parent_act_fallback: Whether to check parent act statusCode
            
        Returns:
            str: Resolved status
        """
        # Standard FHIR status mappings
        status_mappings = {
            'active': 'Active',
            'inactive': 'Inactive', 
            'resolved': 'Resolved',
            'entered-in-error': 'Entered in Error',
            'confirmed': 'Confirmed',
            'unconfirmed': 'Unconfirmed',
            'provisional': 'Provisional'
        }
        
        # Try to extract from observation status
        status = self._extract_code_with_cts(
            observation,
            xpath=status_code_xpath,
            code_systems=['2.16.840.1.113883.4.642.4.1373'],  # FHIR AllergyIntoleranceStatus
            fallback_name="Active",
            fallback_mappings=status_mappings
        )
        
        # Fallback to parent act status if needed
        if status == "Active" and parent_act_fallback:
            status = self._extract_parent_act_status(observation)
        
        return status
    
    def _extract_parent_act_status(self, observation) -> str:
        """Extract status from parent act element."""
        try:
            current = observation
            for _ in range(5):  # Search up to 5 levels
                parent = current.getparent() if hasattr(current, 'getparent') else None
                if parent is None:
                    break
                if parent.tag.endswith('}act'):
                    status_code_elem = parent.find('hl7:statusCode', getattr(self, 'namespaces', {}))
                    if status_code_elem is not None:
                        act_status = status_code_elem.get('code', '').lower()
                        act_mappings = {
                            'active': 'Active',
                            'suspended': 'Suspended',
                            'aborted': 'Aborted',
                            'completed': 'Completed'
                        }
                        if act_status in act_mappings:
                            return act_mappings[act_status]
                        break
                current = parent
        except Exception as e:
            self.logger.error(f"Error extracting parent act status: {e}")
        
        return "Active"
    
    def _resolve_text_reference(self, observation, ref_value: str) -> str:
        """
        Resolve text reference to actual content from CDA text section.
        This method should be implemented by the concrete service class.
        """
        if hasattr(self, '_resolve_text_reference'):
            return super()._resolve_text_reference(observation, ref_value)
        return ref_value