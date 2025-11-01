"""
FHIR Section Base Service
Base class for FHIR R4 resource extraction following Django_NCP patterns

This base class provides common functionality for extracting clinical sections
from FHIR bundles and normalizing them into the Django_NCP common format.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FHIRSectionEntry:
    """
    Common FHIR section entry format (matches CDA pattern)
    Normalized data structure for template rendering
    """
    entry_id: str
    display_text: str
    coded_concepts: List[Dict[str, Any]] = field(default_factory=list)
    table_data: Optional[Dict[str, Any]] = None
    clinical_status: Optional[str] = None
    onset_date: Optional[str] = None
    recorded_date: Optional[str] = None
    recorder: Optional[str] = None
    notes: Optional[List[str]] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    fhir_resource_reference: Optional[str] = None
    verification_status: Optional[str] = None
    raw_resource: Optional[Dict[str, Any]] = None


class FHIRSectionServiceBase:
    """
    Base service for extracting clinical sections from FHIR resources
    Follows Django_NCP service layer pattern
    
    Architecture:
    - Extracts resources from FHIR bundle
    - Normalizes to common section format
    - Compatible with existing CDA templates
    """
    
    def __init__(self):
        self.section_id: str = "unknown"
        self.section_title: str = "Unknown Section"
        self.section_code: str = None
        self.section_system: str = "http://loinc.org"
        self.fhir_resource_type: str = None
        self.icon_class: str = "fa-file-medical"
    
    def extract_section(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract clinical section from FHIR bundle
        Returns normalized section data matching CDA format
        
        Args:
            fhir_bundle: FHIR R4 Bundle resource
            
        Returns:
            Normalized section data compatible with Django_NCP templates
        """
        logger.info(f"[FHIR {self.section_id.upper()}] Extracting section from bundle")
        
        # Find relevant resources in bundle
        resources = self._find_resources_in_bundle(fhir_bundle)
        
        if not resources:
            logger.info(f"[FHIR {self.section_id.upper()}] No resources found")
            return self._create_empty_section()
        
        logger.info(f"[FHIR {self.section_id.upper()}] Found {len(resources)} resources")
        
        # Extract entries from resources
        entries = []
        for resource in resources:
            try:
                entry = self._extract_entry_from_resource(resource)
                if entry:
                    entries.append(asdict(entry))
                    logger.debug(f"[FHIR {self.section_id.upper()}] Extracted entry: {entry.display_text}")
            except Exception as e:
                logger.error(f"[FHIR {self.section_id.upper()}] Error extracting entry: {e}")
        
        # Build section data structure
        clinical_codes = self._extract_all_codes(entries)
        has_structured_codes = self._has_coded_data(entries)
        
        section_data = {
            "section_id": self.section_id,
            "title": self.section_title,
            "section_code": self.section_code,
            "section_system": self.section_system,
            "has_entries": len(entries) > 0,
            "entry_count": len(entries),
            "clinical_table": {
                "entries": entries,
                "columns": self._get_table_columns(),
                "display_config": self._get_display_config()
            },
            "clinical_codes": clinical_codes,
            "is_coded_section": has_structured_codes,
            "fhir_resource_type": self.fhir_resource_type,
            "data_source": "FHIR",
            "icon_class": self.icon_class,
            # Bundle quality metadata
            "bundle_has_structured_codes": has_structured_codes,
            "display_text_only": not has_structured_codes and len(clinical_codes) > 0,
        }
        
        # Log extraction results with bundle quality assessment
        if has_structured_codes:
            logger.info(
                f"[FHIR {self.section_id.upper()}] Section extracted: {len(entries)} entries, "
                f"{len(clinical_codes)} coded concepts ✅ CTS integration available"
            )
        elif len(clinical_codes) > 0:
            logger.warning(
                f"[FHIR {self.section_id.upper()}] Section extracted: {len(entries)} entries, "
                f"{len(clinical_codes)} display-only concepts ⚠️ No structured codes - CTS integration limited"
            )
        else:
            logger.info(
                f"[FHIR {self.section_id.upper()}] Section extracted: {len(entries)} entries, "
                f"no coded concepts"
            )
        
        return section_data
    
    def _find_resources_in_bundle(self, fhir_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find resources of specific type in FHIR bundle
        
        Args:
            fhir_bundle: FHIR Bundle resource
            
        Returns:
            List of resources matching the resource type
        """
        resources = []
        entries = fhir_bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == self.fhir_resource_type:
                resources.append(resource)
        
        return resources
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract entry from FHIR resource (to be implemented by subclasses)
        
        SUBCLASSES MUST OVERRIDE THIS METHOD
        
        Args:
            resource: FHIR resource dict
            
        Returns:
            FHIRSectionEntry or None if extraction fails
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _extract_entry_from_resource()"
        )
    
    def _get_table_columns(self) -> List[str]:
        """
        Get table column configuration for this section
        Override in subclasses for section-specific columns
        """
        return ["display_text", "onset_date", "clinical_status"]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """
        Get display configuration for this section
        Override in subclasses for section-specific display settings
        """
        return {
            "show_timeline": False,
            "show_severity": False,
            "show_status": True,
            "enable_filtering": True,
        }
    
    def _extract_all_codes(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all coded concepts from entries
        For CTS terminology integration
        """
        codes = []
        for entry in entries:
            entry_codes = entry.get("coded_concepts", [])
            codes.extend(entry_codes)
        return codes
    
    def _has_coded_data(self, entries: List[Dict[str, Any]]) -> bool:
        """
        Check if entries contain ACTUAL coded data (not just text)
        
        Returns True only if entries have codes with systems for CTS integration
        Returns False for text-only data
        """
        for entry in entries:
            coded_concepts = entry.get("coded_concepts", [])
            for concept in coded_concepts:
                # Has actual structured code (not just display text)
                if concept.get("code") and concept.get("system"):
                    return True
        return False
    
    def _create_empty_section(self) -> Dict[str, Any]:
        """Create empty section structure"""
        return {
            "section_id": self.section_id,
            "title": self.section_title,
            "section_code": self.section_code,
            "has_entries": False,
            "entry_count": 0,
            "clinical_table": {
                "entries": [],
                "columns": [],
                "display_config": {}
            },
            "clinical_codes": [],
            "is_coded_section": False,
            "fhir_resource_type": self.fhir_resource_type,
            "data_source": "FHIR",
        }
    
    def _get_system_name(self, system: str) -> str:
        """
        Get human-readable system name from URI
        
        Args:
            system: Code system URI
            
        Returns:
            Human-readable system name
        """
        system_map = {
            "http://snomed.info/sct": "SNOMED CT",
            "http://www.whocc.no/atc": "ATC",
            "http://loinc.org": "LOINC",
            "http://hl7.org/fhir/sid/icd-10": "ICD-10",
            "http://hl7.org/fhir/sid/icd-10-cm": "ICD-10-CM",
            "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
            "http://terminology.hl7.org/CodeSystem/v3-NullFlavor": "HL7 NullFlavor",
        }
        return system_map.get(system, system)
    
    def _extract_coding_to_concepts(
        self, 
        coding_list: List[Dict[str, Any]], 
        concept_type: str = None
    ) -> List[Dict[str, Any]]:
        """
        Extract FHIR coding array to coded concepts
        
        RESILIENT DESIGN: Works with both structured codes and text-only data
        - If bundle has code + system: Full CTS integration available
        - If bundle has only display/text: Gracefully extracts display text
        
        Args:
            coding_list: List of FHIR coding objects
            concept_type: Optional type label (e.g., 'reaction', 'manifestation')
            
        Returns:
            List of coded concept dicts (may have None for code/system)
        """
        concepts = []
        for coding in coding_list:
            has_code = coding.get("code") is not None
            has_system = coding.get("system") is not None
            has_display = coding.get("display") is not None
            
            concept = {
                "code": coding.get("code"),
                "system": coding.get("system"),
                "display": coding.get("display"),
                "system_name": self._get_system_name(coding.get("system", "")),
            }
            if concept_type:
                concept["type"] = concept_type
            
            # Only add if we have at least a code or display
            # This allows text-only bundles to work while supporting coded bundles
            if has_code or has_display:
                concepts.append(concept)
                
                # Log warning if display-only (no structured code)
                if has_display and not has_code:
                    logger.debug(
                        f"[FHIR] Display-only concept (no code): {concept['display']} "
                        f"- CTS lookups not available for this entry"
                    )
        
        return concepts
    
    def _safe_get_coding_code(self, codeable_concept: Dict[str, Any], index: int = 0) -> Optional[str]:
        """Safely extract code from CodeableConcept"""
        if not codeable_concept:
            return None
        coding_list = codeable_concept.get("coding", [])
        if coding_list and len(coding_list) > index:
            return coding_list[index].get("code")
        return None
    
    def _safe_get_coding_display(self, codeable_concept: Dict[str, Any], index: int = 0) -> Optional[str]:
        """Safely extract display from CodeableConcept"""
        if not codeable_concept:
            return None
        
        # Try text first
        text = codeable_concept.get("text")
        if text:
            return text
        
        # Fall back to coding display
        coding_list = codeable_concept.get("coding", [])
        if coding_list and len(coding_list) > index:
            return coding_list[index].get("display")
        
        return None
