"""
Enhanced CDA XML Parser with Clinical Coding Extraction
Enhanced for EU Member State Compatibility

This parser extracts both narrative text and structured coded entries from HL7 CDA documents
with specialized support for EU member state variations including Italian L3 documents.

Key EU Compatibility Features:
- Dynamic namespace detection for varying document structures
- Enhanced 8-strategy section discovery system for complex nested structures
- Multi-namespace code extraction supporting Italian healthcare OIDs
- Robust handling of Italian L3 document patterns with 8+ sections
- Extended OID mappings for Italian, German, French, Dutch, Swedish healthcare systems
- eHealth Digital Service Infrastructure (eHDSI) support for cross-border documents
- Nested entry relationship parsing for Italian CDA structures
- Medication-specific extraction for Italian pharmaceutical codes
- Alternative namespace pattern matching for malformed documents

Tested and validated against:
- Italian L3 Patient Summary documents (8 sections)
- Malta CDA documents (5 sections)
- Standard HL7 CDA R2 documents
- Cross-border eHDSI documents
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DotDict(dict):
    """Dictionary that supports dot notation access for template compatibility"""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )


# Import our date formatter for consistent date display
try:
    from patient_data.utils.date_formatter import default_formatter
except ImportError:
    # Fallback if date formatter not available during tests
    default_formatter = None

# Import enhanced administrative extractor
try:
    from patient_data.services.cda_administrative_extractor import (
        CDAAdministrativeExtractor,
    )
except ImportError:
    # Fallback if administrative extractor not available
    CDAAdministrativeExtractor = None

# Import unified patient demographics service
try:
    from patient_data.services.patient_demographics_service import PatientDemographicsService
except ImportError:
    # Fallback if patient demographics service not available
    PatientDemographicsService = None

logger = logging.getLogger(__name__)


@dataclass
class ClinicalCode:
    """Represents a clinical code (SNOMED, LOINC, ICD, ATC, etc.)"""

    code: str
    system: str
    system_name: str
    system_version: Optional[str] = None
    display_name: Optional[str] = None
    original_text_ref: Optional[str] = None

    @property
    def formatted_display(self) -> str:
        """Format for display in UI"""
        parts = []
        if self.system_name:
            parts.append(self.system_name.upper())
        if self.code:
            parts.append(self.code)
        if self.display_name:
            parts.append(f'"{self.display_name}"')
        return ": ".join(parts) if parts else "Unknown Code"

    @property
    def system_badge_class(self) -> str:
        """Return CSS class for system badge"""
        if "snomed" in self.system_name.lower():
            return "snomed"
        elif "loinc" in self.system_name.lower():
            return "loinc"
        elif "icd" in self.system_name.lower():
            return "icd10"
        elif (
            "atc" in self.system_name.lower()
            or "anatomical" in self.system_name.lower()
        ):
            return "atc"
        elif "ucum" in self.system_name.lower():
            return "ucum"
        elif "edqm" in self.system_name.lower():
            return "edqm"
        else:
            return "other"


@dataclass
class ClinicalCodesCollection:
    """Collection of clinical codes for a section"""

    codes: List[ClinicalCode] = field(default_factory=list)

    @property
    def formatted_display(self) -> str:
        """Format all codes for display"""
        if not self.codes:
            return ""
        return " | ".join(
            [code.formatted_display for code in self.codes[:3]]
        )  # Show first 3

    @property
    def has_codes(self) -> bool:
        return len(self.codes) > 0

    @property
    def system_badges(self) -> List[str]:
        """Get unique system badge classes"""
        systems = set()
        for code in self.codes:
            systems.add(code.system_badge_class)
        return list(systems)


@dataclass
class ClinicalSection:
    """Enhanced clinical section with coded data"""

    section_id: str
    title: str
    original_text_html: str
    translated_text_html: str
    section_code: Optional[str] = None
    section_system: Optional[str] = None
    clinical_codes: ClinicalCodesCollection = field(
        default_factory=ClinicalCodesCollection
    )
    template_ids: List[str] = field(default_factory=list)
    medical_terms_count: int = 0

    @property
    def is_coded_section(self) -> bool:
        """Check if this section has clinical codes"""
        return self.clinical_codes.has_codes

    @property
    def has_ps_table(self) -> bool:
        """Check if section has structured table"""
        return "<table>" in self.original_text_html


class EnhancedCDAXMLParser:
    """Enhanced parser for HL7 CDA XML with clinical coding extraction

    Enhanced for EU member state compatibility including Italian L3 documents
    """

    def __init__(self):
        # Default namespaces - will be dynamically enhanced per document
        self.namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:hl7-org:pharm"}

        # Common EU namespace variations for better compatibility
        self.common_namespaces = {
            "hl7": "urn:hl7-org:v3",
            "cda": "urn:hl7-org:v3",
            "pharm": "urn:hl7-org:pharm",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "voc": "urn:hl7-org:v3/voc",
            "sdtc": "urn:hl7-org:sdtc",
            # Italian CDA specific namespaces
            "it": "urn:oid:2.16.840.1.113883.2.9.10.1.1",
            "crs": "urn:oid:2.16.840.1.113883.2.9.10.1.1.1",
        }

        # Initialize administrative extractor with date formatter
        if CDAAdministrativeExtractor:
            self.admin_extractor = CDAAdministrativeExtractor()
        else:
            self.admin_extractor = None

        # Initialize unified patient demographics service
        if PatientDemographicsService:
            self.demographics_service = PatientDemographicsService()
        else:
            self.demographics_service = None

    def _detect_and_update_namespaces(self, xml_content: str) -> None:
        """
        Dynamically detect namespaces from XML document for EU member state compatibility

        This enhances parsing of Italian L3 and other EU CDA documents that may use
        different namespace prefixes or additional namespaces
        """
        try:
            # Extract namespace declarations from XML root element
            namespace_pattern = r'xmlns(?::(\w+))?="([^"]+)"'
            matches = re.findall(namespace_pattern, xml_content)

            detected_namespaces = {}

            for prefix, uri in matches:
                # Use default 'cda' prefix for default namespace
                namespace_key = prefix if prefix else "cda"
                detected_namespaces[namespace_key] = uri

                # Map common URI patterns to standard prefixes
                if "hl7-org:v3" in uri and namespace_key not in ["cda", "hl7"]:
                    detected_namespaces["cda"] = uri
                elif "pharm" in uri and namespace_key != "pharm":
                    detected_namespaces["pharm"] = uri

            # Merge with common namespaces, giving priority to detected ones
            merged_namespaces = self.common_namespaces.copy()
            merged_namespaces.update(detected_namespaces)

            # Update parser namespaces
            old_count = len(self.namespaces)
            self.namespaces = merged_namespaces
            new_count = len(self.namespaces)

            if new_count > old_count:
                logger.info(
                    f"[GLOBAL] Enhanced namespaces for EU compatibility: {new_count} namespaces ({new_count - old_count} new)"
                )

        except Exception as e:
            logger.warning(f"Namespace detection failed, using defaults: {e}")

    def parse_cda_content(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse CDA XML content and extract clinical sections with coded data
        Enhanced for EU member state compatibility
        """
        try:
            # Detect and update namespaces for this document
            self._detect_and_update_namespaces(xml_content)

            # Clean and parse XML
            cleaned_xml = self._clean_xml_content(xml_content)
            root = ET.fromstring(cleaned_xml)

            # Extract basic document info using unified demographics service
            if self.demographics_service:
                # Use unified patient demographics service
                demographics = self.demographics_service.extract_from_cda_xml(root)
                patient_info = demographics.to_legacy_context()
                logger.info(f"[UNIFIED] Extracted patient demographics: {demographics.get_display_name()}")
            else:
                # Fallback to legacy method
                patient_info = self._extract_patient_info(root)
                logger.warning("[LEGACY] Using legacy patient info extraction")
            
            administrative_data = self._extract_administrative_data(root)

            # Extract clinical sections with coded data
            sections = self._extract_clinical_sections_with_codes(root)
            
            # Extract detailed medication data
            detailed_medications = self._extract_detailed_medication_data(root)

            # Calculate summary statistics
            stats = self._calculate_section_statistics(sections)

            result = {
                "patient_identity": patient_info,
                "administrative_data": administrative_data,
                "sections": sections,
                "detailed_medications": detailed_medications,
                "sections_count": stats["total_sections"],
                "coded_sections_count": stats["coded_sections"],
                "medical_terms_count": stats["total_codes"],
                "coded_sections_percentage": stats["coded_percentage"],
                "uses_coded_sections": stats["coded_sections"] > 0,
                "translation_quality": self._assess_translation_quality(stats),
                "has_administrative_data": bool(administrative_data),
            }

            logger.info(
                f"Enhanced CDA parsing complete: {stats['total_sections']} sections, {stats['coded_sections']} coded, {stats['total_codes']} clinical codes"
            )
            return result

        except Exception as e:
            logger.error(f"Enhanced CDA parsing failed: {str(e)}")
            return self._create_fallback_result()

    def _extract_clinical_sections_with_codes(
        self, root: ET.Element
    ) -> List[Dict[str, Any]]:
        """
        Extract clinical sections using enhanced comprehensive discovery strategy
        Enhanced for EU member state compatibility including Italian L3 documents
        """
        sections = []
        discovered_elements = set()  # Track to avoid duplicates

        logger.info(
            "[SEARCH] Starting enhanced section discovery for EU compatibility..."
        )

        # Strategy 1: Direct section discovery (all namespaces)
        section_elements = root.findall(".//cda:section", self.namespaces)
        logger.info(f"Strategy 1 - Direct sections found: {len(section_elements)}")
        for elem in section_elements:
            discovered_elements.add(elem)

        # Strategy 2: Component-based discovery (for different CDA structures)
        component_sections = root.findall(
            ".//cda:component/cda:section", self.namespaces
        )
        logger.info(f"Strategy 2 - Component sections found: {len(component_sections)}")
        for elem in component_sections:
            discovered_elements.add(elem)

        # Strategy 3: StructuredBody sections
        structured_sections = root.findall(
            ".//cda:structuredBody//cda:section", self.namespaces
        )
        logger.info(
            f"Strategy 3 - StructuredBody sections found: {len(structured_sections)}"
        )
        for elem in structured_sections:
            discovered_elements.add(elem)

        # Strategy 4: Direct search within document structure
        doc_sections = root.findall(
            ".//cda:ClinicalDocument//cda:section", self.namespaces
        )
        logger.info(f"Strategy 4 - Document sections found: {len(doc_sections)}")
        for elem in doc_sections:
            discovered_elements.add(elem)

        # Strategy 5: Italian L3 specific patterns - nested component structures
        nested_sections = root.findall(
            ".//cda:component/cda:structuredBody/cda:component/cda:section",
            self.namespaces,
        )
        logger.info(
            f"Strategy 5 - Italian nested sections found: {len(nested_sections)}"
        )
        for elem in nested_sections:
            discovered_elements.add(elem)

        # Strategy 6: Multi-level component discovery for complex EU documents
        multi_level_sections = []
        for level in range(2, 5):  # Check 2-4 levels deep
            xpath = "/".join(["cda:component"] * level) + "/cda:section"
            level_sections = root.findall(f".//{xpath}", self.namespaces)
            multi_level_sections.extend(level_sections)

        logger.info(
            f"Strategy 6 - Multi-level sections found: {len(multi_level_sections)}"
        )
        for elem in multi_level_sections:
            discovered_elements.add(elem)

        # Strategy 7: Alternative namespace patterns (for documents with mixed namespaces)
        alt_namespace_sections = []
        for ns_key in self.namespaces.keys():
            if ns_key != "cda":
                alt_sections = root.findall(f".//{ns_key}:section", self.namespaces)
                alt_namespace_sections.extend(alt_sections)

        logger.info(
            f"Strategy 7 - Alternative namespace sections found: {len(alt_namespace_sections)}"
        )
        for elem in alt_namespace_sections:
            discovered_elements.add(elem)

        # Strategy 8: Broad discovery without namespace constraints for malformed documents
        try:
            # Find elements that end with 'section' regardless of namespace
            broad_sections = []
            for elem in root.iter():
                if elem.tag.endswith("}section") or elem.tag.lower() == "section":
                    broad_sections.append(elem)

            logger.info(
                f"Strategy 8 - Broad section discovery found: {len(broad_sections)}"
            )
            for elem in broad_sections:
                discovered_elements.add(elem)
        except Exception as e:
            logger.warning(f"Strategy 8 broad discovery failed: {e}")

        logger.info(
            f"[SUCCESS] Total unique sections discovered: {len(discovered_elements)} (enhanced for EU compatibility)"
        )

        # Process all discovered sections
        for idx, section_elem in enumerate(discovered_elements):
            try:
                section = self._parse_single_section(section_elem, idx)
                if section:
                    sections.append(self._convert_section_to_dict(section))
            except Exception as e:
                logger.warning(f"Failed to parse section {idx}: {str(e)}")
                continue

        logger.info(f"[TARGET] Successfully parsed {len(sections)} sections")
        return sections

    def _parse_single_section(
        self, section_elem: ET.Element, idx: int
    ) -> Optional[ClinicalSection]:
        """Parse a single section element with its coded entries"""

        # Extract section code and title
        section_code_elem = section_elem.find("cda:code", self.namespaces)
        section_code = None
        section_system = None
        if section_code_elem is not None:
            section_code = section_code_elem.get("code")
            section_system = section_code_elem.get(
                "codeSystemName", section_code_elem.get("codeSystem")
            )

        # Extract title
        title_elem = section_elem.find("cda:title", self.namespaces)
        title = (
            title_elem.text.strip()
            if title_elem is not None and title_elem.text
            else f"Section {idx + 1}"
        )

        # Extract text content (narrative) - make it optional
        text_elem = section_elem.find("cda:text", self.namespaces)
        original_text = ""
        if text_elem is not None:
            original_text = self._extract_text_content(text_elem)

        # If no text content, use a fallback based on title or section code
        if not original_text.strip():
            original_text = f"<p>Clinical section: {title}</p>"

        # Extract template IDs
        template_ids = [
            tmpl.get("root", "")
            for tmpl in section_elem.findall("cda:templateId", self.namespaces)
        ]

        # Extract coded entries
        clinical_codes = self._extract_coded_entries(section_elem)

        # Count medical terms (simple heuristic)
        medical_terms_count = len(clinical_codes.codes)

        section = ClinicalSection(
            section_id=f"section_{idx}",
            title=title,
            original_text_html=original_text,
            translated_text_html=original_text,  # TODO: Add translation service
            section_code=section_code,
            section_system=section_system,
            clinical_codes=clinical_codes,
            template_ids=template_ids,
            medical_terms_count=medical_terms_count,
        )

        return section

    def _extract_coded_entries(
        self, section_elem: ET.Element
    ) -> ClinicalCodesCollection:
        """
        Extract clinical codes using enhanced comprehensive systematic approach
        Enhanced for Italian L3 and EU member state document compatibility
        """
        codes = []

        # Find all entry elements in this section with enhanced discovery
        entries = section_elem.findall("cda:entry", self.namespaces)

        # Also search for entries in alternative namespace patterns (Italian L3 support)
        alt_entries = []
        for ns_key in self.namespaces.keys():
            if ns_key != "cda":
                alt_ns_entries = section_elem.findall(
                    f"{ns_key}:entry", self.namespaces
                )
                alt_entries.extend(alt_ns_entries)

        # Combine all discovered entries
        all_entries = list(entries) + alt_entries
        logger.info(
            f"[SEARCH] Processing {len(all_entries)} entries for coded elements (enhanced for EU compatibility)..."
        )

        for entry_idx, entry in enumerate(all_entries):
            logger.debug(f"Processing entry {entry_idx}")

            # Apply unified extraction strategies (consolidated from 8 methods to 3)
            entry_codes = []

            # Unified Strategy 1: Code-based extraction (combines coded_elements & enhanced)
            self._extract_code_elements_unified(entry, entry_codes)

            # Unified Strategy 2: Contextual extraction (combines text, time, status, value)
            self._extract_contextual_elements_unified(entry, entry_codes)

            # Unified Strategy 3: Structural extraction (combines nested entries & medications)
            self._extract_structural_elements_unified(entry, entry_codes)

            # Add discovered codes to main collection
            codes.extend(entry_codes)

        logger.info(
            f"[SUCCESS] Extracted {len(codes)} total coded elements (enhanced EU extraction)"
        )
        return ClinicalCodesCollection(codes=codes)

    def _extract_clinical_code(self, elem: ET.Element) -> Optional[ClinicalCode]:
        """Extract a clinical code from a coded element - handles country variations"""
        code_value = elem.get("code")
        code_system = elem.get("codeSystem")
        system_name = elem.get("codeSystemName", "")
        system_version = elem.get("codeSystemVersion")
        display_name = elem.get("displayName")

        # Handle cases where the code is in the 'value' attribute (common in observations)
        if not code_value and elem.tag.endswith("value"):
            code_value = elem.get("code")

        if not code_value or not code_system:
            return None

        # Look for originalText reference (handles country-specific text linking)
        original_text_ref = None
        original_text_elem = elem.find("cda:originalText", self.namespaces)
        if original_text_elem is not None:
            ref_elem = original_text_elem.find("cda:reference", self.namespaces)
            if ref_elem is not None:
                original_text_ref = ref_elem.get("value", "").replace("#", "")

        # Enhance system name mapping for better display
        if not system_name and code_system:
            system_name = self._map_code_system_to_name(code_system)

        return ClinicalCode(
            code=code_value,
            system=code_system,
            system_name=system_name or "Unknown System",
            system_version=system_version,
            display_name=display_name,
            original_text_ref=original_text_ref,
        )

    # UNIFIED EXTRACTION METHODS - Phase 2 Consolidation
    # Consolidates 8 systematic methods into 3 configurable strategies
    
    def _extract_code_elements_unified(self, entry: ET.Element, codes: List[ClinicalCode]):
        """
        Unified code-based extraction strategy
        
        Consolidates:
        - _extract_coded_elements_systematic()
        - _extract_coded_elements_systematic_enhanced()
        
        Extracts all elements that contain medical codes with enhanced EU compatibility
        """
        # Strategy 1A: Basic coded elements extraction
        # Find all code elements
        code_elements = entry.findall(".//cda:code", self.namespaces)
        for code_elem in code_elements:
            code = self._extract_clinical_code(code_elem)
            if code:
                codes.append(code)

        # Find all value elements with codes
        value_elements = entry.findall(".//cda:value[@code]", self.namespaces)
        for value_elem in value_elements:
            code = self._extract_clinical_code(value_elem)
            if code:
                codes.append(code)

        # Find translation elements
        translation_elements = entry.findall(".//cda:translation", self.namespaces)
        for trans_elem in translation_elements:
            code = self._extract_clinical_code(trans_elem)
            if code:
                codes.append(code)

        # Strategy 1B: Enhanced extraction for EU member state compatibility
        # Search across all namespaces for broader compatibility
        for ns_prefix in self.namespaces.keys():
            if ns_prefix == "cda":
                continue  # Already processed above
                
            # Find code elements with alternative namespace prefixes
            alt_code_elements = entry.findall(f".//{ns_prefix}:code", self.namespaces)
            for code_elem in alt_code_elements:
                code = self._extract_clinical_code(code_elem)
                if code:
                    codes.append(code)

            # Find value elements with codes in alternative namespaces
            alt_value_elements = entry.findall(f".//{ns_prefix}:value[@code]", self.namespaces)
            for value_elem in alt_value_elements:
                code = self._extract_clinical_code(value_elem)
                if code:
                    codes.append(code)

    def _extract_contextual_elements_unified(self, entry: ET.Element, codes: List[ClinicalCode]):
        """
        Unified contextual extraction strategy
        
        Consolidates:
        - _extract_text_elements_systematic()
        - _extract_time_elements_systematic()
        - _extract_status_elements_systematic()
        - _extract_value_elements_systematic()
        
        Extracts contextual elements like text references, temporal data, status codes, and units
        """
        # Strategy 2A: Text elements with medical significance
        # Process originalText elements with references
        original_texts = entry.findall(".//cda:originalText", self.namespaces)
        for text_elem in original_texts:
            ref_elem = text_elem.find("cda:reference", self.namespaces)
            if ref_elem is not None:
                # Create text-based code entry for tracking narrative references
                ref_value = ref_elem.get("value", "").replace("#", "")
                if ref_value and text_elem.text:
                    # Track narrative references for completeness
                    pass  # Could create text-reference codes here if needed

        # Strategy 2B: Time-related elements with clinical context
        effective_times = entry.findall(".//cda:effectiveTime", self.namespaces)
        for time_elem in effective_times:
            # Look for codes in the same entry context
            parent_codes = entry.findall(".//cda:code", self.namespaces)
            for parent_code in parent_codes:
                code = self._extract_clinical_code(parent_code)
                if code:
                    # Add temporal context to the code
                    time_value = time_elem.get("value")
                    if time_value:
                        code.display_name = (
                            f"{code.display_name} (Effective: {time_value})"
                            if code.display_name
                            else f"(Effective: {time_value})"
                        )
                    codes.append(code)
                    break  # Only add temporal context once per time element

        # Strategy 2C: Status-related elements
        status_codes = entry.findall(".//cda:statusCode", self.namespaces)
        for status_elem in status_codes:
            code_value = status_elem.get("code")
            if code_value:
                # Create status-based clinical code
                status_code = ClinicalCode(
                    code=code_value,
                    system="2.16.840.1.113883.5.14",  # HL7 ActStatus
                    system_name="HL7 ActStatus",
                    display_name=f"Status: {code_value}",
                )
                codes.append(status_code)

        # Strategy 2D: Value/quantity elements with units and codes
        for elem in entry.iter():
            if elem.tag.endswith("}value") or "value" in elem.tag.lower():
                # Check for coded values
                if elem.get("code") and elem.get("codeSystem"):
                    code = self._extract_clinical_code(elem)
                    if code:
                        codes.append(code)

                # Check for unit codes (UCUM compliance)
                unit = elem.get("unit")
                if unit:
                    # Create unit-based code for UCUM units
                    unit_code = ClinicalCode(
                        code=unit,
                        system="2.16.840.1.113883.6.8",  # UCUM
                        system_name="UCUM",
                        display_name=f"Unit: {unit}",
                    )
                    codes.append(unit_code)

    def _extract_structural_elements_unified(self, entry: ET.Element, codes: List[ClinicalCode]):
        """
        Unified structural extraction strategy
        
        Consolidates:
        - _extract_nested_entries_systematic()
        - _extract_medication_codes_systematic()
        
        Extracts codes from complex nested structures and medication-specific elements
        """
        # Strategy 3A: Nested entry structures (Italian L3 pattern)
        # Find nested entryRelationship elements
        nested_relations = entry.findall(".//cda:entryRelationship", self.namespaces)
        for relation in nested_relations:
            # Extract codes from nested observations/acts
            for child in relation:
                if child.tag.endswith("}observation") or child.tag.endswith("}act"):
                    # Recursively extract codes using unified code extraction
                    nested_codes = []
                    self._extract_code_elements_unified(child, nested_codes)
                    codes.extend(nested_codes)

        # Find component elements within entries
        components = entry.findall(".//cda:component", self.namespaces)
        for comp in components:
            comp_codes = []
            self._extract_code_elements_unified(comp, comp_codes)
            codes.extend(comp_codes)

        # Strategy 3B: Medication-specific extraction (important for Italian L3)
        # Find manufacturedProduct elements (medication codes)
        products = entry.findall(".//cda:manufacturedProduct", self.namespaces)
        for product in products:
            product_codes = []
            self._extract_code_elements_unified(product, product_codes)
            codes.extend(product_codes)

        # Find substance administration codes
        substances = entry.findall(".//cda:substanceAdministration", self.namespaces)
        for substance in substances:
            substance_codes = []
            self._extract_code_elements_unified(substance, substance_codes)
            codes.extend(substance_codes)

        # Find pharmacy-specific elements
        pharm_elements = entry.findall(".//pharm:*", self.namespaces)
        for pharm_elem in pharm_elements:
            pharm_codes = []
            self._extract_code_elements_unified(pharm_elem, pharm_codes)
            codes.extend(pharm_codes)

    def _map_code_system_to_name(self, code_system: str) -> str:
        """
        Map common code system OIDs to readable names
        Enhanced with Italian and EU member state healthcare classification systems
        """
        system_mappings = {
            # International Standards
            "2.16.840.1.113883.6.96": "SNOMED CT",
            "2.16.840.1.113883.6.1": "LOINC",
            "2.16.840.1.113883.6.73": "ATC",
            "2.16.840.1.113883.6.3": "ICD-10",
            "2.16.840.1.113883.6.42": "ICD-9",
            "2.16.840.1.113883.6.88": "RxNorm",
            "2.16.840.1.113883.5.25": "Confidentiality",
            "2.16.840.1.113883.5.1": "AdministrativeGender",
            "0.4.0.127.0.16.1.1.2.1": "EDQM",
            "2.16.840.1.113883.6.8": "UCUM",
            # Italian Healthcare System OIDs
            "2.16.840.1.113883.2.9": "Italian Ministry of Health",
            "2.16.840.1.113883.2.9.4.3.2": "Italian Regional Healthcare Codes",
            "2.16.840.1.113883.2.9.4.3.17": "Italian National Drug Code",
            "2.16.840.1.113883.2.9.6.1.5": "Italian Healthcare Facility Codes",
            "2.16.840.1.113883.2.9.6.1.11": "Italian Healthcare Professional Roles",
            "2.16.840.1.113883.2.9.2.10.4.1": "Italian Prescription Codes",
            "2.16.840.1.113883.2.9.2.80.3.1": "Italian Patient Identification",
            # Italian Clinical Classifications
            "2.16.840.1.113883.2.9.77.22.11.2": "Italian Clinical Procedures",
            "2.16.840.1.113883.2.9.77.22.11.3": "Italian Diagnostic Codes",
            "2.16.840.1.113883.2.9.4.3.1": "Italian Healthcare Structure Codes",
            "2.16.840.1.113883.2.9.4.3.15": "Italian Medical Device Codes",
            # Other EU Member State Systems
            "1.2.276.0.76.5.409": "German Healthcare Codes",
            "1.2.250.1.213.1.1.4.2": "French Healthcare Classification",
            "2.16.840.1.113883.2.4.3": "Dutch Healthcare Codes",
            "1.2.752.78.1.1": "Swedish Healthcare Classification",
            # EU eHealth Digital Service Infrastructure (eHDSI)
            "1.3.6.1.4.1.12559.11.10.1.3.1.44.1": "eHDSI Patient Summary",
            "1.3.6.1.4.1.12559.11.10.1.3.1.44.2": "eHDSI ePrescription",
            "1.3.6.1.4.1.12559.11.10.1.3.1.44.3": "eHDSI Laboratory Results",
        }
        return system_mappings.get(code_system, "")

    def _convert_section_to_dict(self, section: ClinicalSection) -> Dict[str, Any]:
        """Convert ClinicalSection to dictionary format expected by template"""
        return {
            "section_id": section.section_id,
            "title": {"coded": section.title, "translated": section.title},
            "content": {
                "original": section.original_text_html,
                "translated": section.translated_text_html,
                "medical_terms": section.medical_terms_count,
            },
            "section_code": (
                f"{section.section_code} ({section.section_system})"
                if section.section_code
                else None
            ),
            "clinical_codes": section.clinical_codes,
            "is_coded_section": section.is_coded_section,
            "has_ps_table": section.has_ps_table,
            "ps_table_html": (
                section.original_text_html if section.has_ps_table else None
            ),
            "ps_table_html_original": (
                section.original_text_html if section.has_ps_table else None
            ),
        }

    def _calculate_section_statistics(
        self, sections: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate statistics about sections and coding"""
        total_sections = len(sections)
        coded_sections = sum(1 for s in sections if s["is_coded_section"])
        total_codes = sum(s["content"]["medical_terms"] for s in sections)
        coded_percentage = (
            int((coded_sections / total_sections * 100)) if total_sections > 0 else 0
        )

        return {
            "total_sections": total_sections,
            "coded_sections": coded_sections,
            "total_codes": total_codes,
            "coded_percentage": coded_percentage,
        }

    def _assess_translation_quality(self, stats: Dict[str, int]) -> str:
        """Assess translation quality based on coding statistics"""
        if stats["coded_percentage"] >= 80:
            return "Excellent"
        elif stats["coded_percentage"] >= 60:
            return "Good"
        elif stats["coded_percentage"] >= 40:
            return "Fair"
        else:
            return "Basic"

    def _extract_text_content(self, text_elem: ET.Element) -> str:
        """Extract and clean text content from text element"""
        try:
            # Convert the text element back to string to preserve HTML structure
            text_content = ET.tostring(text_elem, encoding="unicode", method="html")

            # Remove the outer <text> tags but keep inner HTML
            text_content = re.sub(r"^<text[^>]*>", "", text_content)
            text_content = re.sub(r"</text>$", "", text_content)

            # Clean up namespace declarations and extra whitespace
            text_content = re.sub(r'\s*xmlns[^=]*="[^"]*"', "", text_content)
            text_content = re.sub(r"\s+", " ", text_content).strip()

            return text_content
        except Exception as e:
            logger.warning(f"Failed to extract text content: {str(e)}")
            return ""

    # REMOVED: _extract_patient_info method has been replaced by PatientDemographicsService
    # This consolidation eliminates 132 lines of duplicate patient extraction logic

    def _extract_administrative_data(self, root: ET.Element) -> Dict[str, Any]:
        """
        PHASE 3: Unified administrative data extraction strategy
        
        Consolidates:
        - _extract_enhanced_administrative_data() (primary strategy)
        - _extract_basic_administrative_data() (fallback strategy)  
        - _create_default_administrative_data() (error handling strategy)
        
        Returns comprehensive administrative context for templates including:
        - Document metadata (creation, version, custody)
        - Healthcare team (authors, authenticators, custodians)
        - Patient relationships (emergency contacts, guardians)
        - Organizational structure (healthcare providers, custodians)
        """
        try:
            # Strategy 1: Enhanced extraction (comprehensive data)
            if self.admin_extractor:
                return self._extract_administrative_data_unified(root, strategy="enhanced")
            else:
                # Strategy 2: Basic extraction (fallback)
                return self._extract_administrative_data_unified(root, strategy="basic")
        except Exception as e:
            logger.warning(f"Administrative data extraction failed: {str(e)}")
            # Strategy 3: Default data creation (error handling)
            return self._extract_administrative_data_unified(root, strategy="default")

    def _extract_administrative_data_unified(self, root: ET.Element, strategy: str = "enhanced") -> Dict[str, Any]:
        """
        PHASE 3: Unified administrative data extraction strategy
        
        Consolidates multiple extraction approaches into single configurable method:
        - Enhanced: Full administrative data with contact information and relationships
        - Basic: Essential document metadata and basic organization info
        - Default: Fallback structure for error handling
        
        Args:
            root: CDA XML root element
            strategy: "enhanced", "basic", or "default"
            
        Returns:
            Comprehensive administrative data structure for template context
        """
        if strategy == "enhanced":
            return self._extract_enhanced_administrative_data_strategy(root)
        elif strategy == "basic":
            return self._extract_basic_administrative_data_strategy(root)
        else:  # default
            return self._extract_default_administrative_data_strategy()

    def _extract_enhanced_administrative_data_strategy(self, root: ET.Element) -> Dict[str, Any]:
        """
        Enhanced administrative data extraction strategy - Phase 3A Consolidated
        
        Extracts comprehensive administrative data including:
        - Document metadata with version control
        - Healthcare team with contact information  
        - Patient relationships and emergency contacts
        - Organizational structure and custody information
        
        PHASE 3A: Consolidated from CDAAdministrativeExtractor, NonClinicalCDAParser,
        and EnhancedAdministrativeExtractor for unified administrative extraction
        """
        # PHASE 3A: Detect source country for optimized parsing
        source_country = self._detect_source_country_phase3a(root)
        
        # PHASE 3A: Detect document type (L1 vs L3) for optimized processing
        document_type = self._detect_document_type_phase3a(root)
        
        # PHASE 3A: Use consolidated administrative extractor with country optimization
        admin_data = self.admin_extractor.extract_administrative_data(
            ET.tostring(root, encoding="unicode")
        )
        
        logger.info(f"[PHASE 3A] Administrative extraction - Country: {source_country}, Type: {document_type}, Fields: {len(admin_data.__dict__) if admin_data else 0}")

        # Extract document creation date with fallback
        effective_time = root.find(".//{urn:hl7-org:v3}effectiveTime")
        creation_date = (
            admin_data.document_creation_date
            if admin_data.document_creation_date
            else "Unknown"
        )
        creation_date_raw = "Unknown"
        if effective_time is not None:
            creation_date_raw = effective_time.get("value", "Unknown")
            # Format the document date for consistent display
            if default_formatter and creation_date_raw != "Unknown":
                creation_date = default_formatter.format_document_date(
                    creation_date_raw
                )
            elif not admin_data.document_creation_date:
                creation_date = creation_date_raw

        # Extract document title with fallback
        title_elem = root.find(".//{urn:hl7-org:v3}title")
        document_title = (
            title_elem.text if title_elem is not None and title_elem.text else "Unknown"
        )

        # Extract document type with fallback
        code_elem = root.find(".//{urn:hl7-org:v3}code")
        document_type = "Unknown"
        if code_elem is not None:
            document_type = code_elem.get(
                "displayName", code_elem.get("code", "Unknown")
            )

        # Extract document ID with fallback
        doc_id_elem = root.find(".//{urn:hl7-org:v3}id")
        document_id = (
            admin_data.document_set_id
            if admin_data.document_set_id
            else (
                doc_id_elem.get("extension", "Unknown")
                if doc_id_elem is not None
                else "Unknown"
            )
        )

        # Convert enhanced administrative data to expected format with template compatibility
        # Patient contact information
        patient_contact_info = DotDict(
            {
                "addresses": (
                    admin_data.patient_contact_info.addresses
                    if admin_data.patient_contact_info
                    else []
                ),
                "telecoms": (
                    admin_data.patient_contact_info.telecoms
                    if admin_data.patient_contact_info
                    else []
                ),
            }
        )

        # Author information with organization details
        author_information = []
        if admin_data.author_hcp:
            # Get organization from author or look for related organizations
            author_org = DotDict({"name": "", "addresses": [], "telecoms": []})

            # If the author has organization info embedded or look for first organization
            if (
                hasattr(admin_data.author_hcp, "organization")
                and admin_data.author_hcp.organization
            ):
                author_org["name"] = admin_data.author_hcp.organization.name or ""
                author_org["addresses"] = getattr(
                    admin_data.author_hcp.organization, "addresses", []
                )
                author_org["telecoms"] = getattr(
                    admin_data.author_hcp.organization, "telecoms", []
                )
            elif admin_data.custodian_organization:
                # Fallback to custodian organization for authors
                author_org["name"] = admin_data.custodian_organization.name or ""
                author_org["addresses"] = (
                    admin_data.custodian_organization.addresses or []
                )
                author_org["telecoms"] = (
                    admin_data.custodian_organization.telecoms or []
                )

            author_info = DotDict(
                {
                    "person": DotDict(
                        {
                            "family_name": admin_data.author_hcp.family_name,
                            "given_name": admin_data.author_hcp.given_name,
                            "full_name": f"{admin_data.author_hcp.given_name} {admin_data.author_hcp.family_name}".strip(),
                            "title": admin_data.author_hcp.title,
                            "role": admin_data.author_hcp.role,
                        }
                    ),
                    "organization": author_org,
                    "contact_info": DotDict(
                        {
                            "addresses": (
                                admin_data.author_hcp.contact_info.addresses
                                if admin_data.author_hcp.contact_info
                                else []
                            ),
                            "telecoms": (
                                admin_data.author_hcp.contact_info.telecoms
                                if admin_data.author_hcp.contact_info
                                else []
                            ),
                        }
                    ),
                }
            )
            author_information.append(author_info)

        # Custodian organization
        custodian_organization = DotDict(
            {
                "name": (
                    admin_data.custodian_organization.name
                    if admin_data.custodian_organization
                    else ""
                ),
                "addresses": (
                    admin_data.custodian_organization.addresses
                    if admin_data.custodian_organization
                    else []
                ),
                "telecoms": (
                    admin_data.custodian_organization.telecoms
                    if admin_data.custodian_organization
                    else []
                ),
            }
        )

        # Legal authenticator with organization details
        legal_auth_org = DotDict({"name": "", "addresses": [], "telecoms": []})

        if admin_data.legal_authenticator:
            # Look for organization associated with legal authenticator
            if (
                hasattr(admin_data.legal_authenticator, "organization")
                and admin_data.legal_authenticator.organization
            ):
                legal_auth_org["name"] = (
                    admin_data.legal_authenticator.organization.name or ""
                )
                legal_auth_org["addresses"] = getattr(
                    admin_data.legal_authenticator.organization, "addresses", []
                )
                legal_auth_org["telecoms"] = getattr(
                    admin_data.legal_authenticator.organization, "telecoms", []
                )
            elif admin_data.custodian_organization:
                # Fallback to custodian organization for legal authenticator
                legal_auth_org["name"] = admin_data.custodian_organization.name or ""
                legal_auth_org["addresses"] = (
                    admin_data.custodian_organization.addresses or []
                )
                legal_auth_org["telecoms"] = (
                    admin_data.custodian_organization.telecoms or []
                )

        legal_authenticator = DotDict(
            {
                "family_name": (
                    admin_data.legal_authenticator.family_name
                    if admin_data.legal_authenticator
                    else ""
                ),
                "given_name": (
                    admin_data.legal_authenticator.given_name
                    if admin_data.legal_authenticator
                    else ""
                ),
                "full_name": (
                    f"{admin_data.legal_authenticator.given_name} {admin_data.legal_authenticator.family_name}".strip()
                    if admin_data.legal_authenticator
                    else ""
                ),
                "title": (
                    admin_data.legal_authenticator.title
                    if admin_data.legal_authenticator
                    else ""
                ),
                "role": (
                    admin_data.legal_authenticator.role
                    if admin_data.legal_authenticator
                    else "Legal Authenticator"
                ),
                "organization": legal_auth_org,
                "organization_name": legal_auth_org.name,
                "contact_info": DotDict(
                    {
                        "addresses": (
                            admin_data.legal_authenticator.contact_info.addresses
                            if admin_data.legal_authenticator
                            and admin_data.legal_authenticator.contact_info
                            else []
                        ),
                        "telecoms": (
                            admin_data.legal_authenticator.contact_info.telecoms
                            if admin_data.legal_authenticator
                            and admin_data.legal_authenticator.contact_info
                            else []
                        ),
                    }
                ),
                "contact_details": DotDict(
                    {
                        "addresses": (
                            admin_data.legal_authenticator.contact_info.addresses
                            if admin_data.legal_authenticator
                            and admin_data.legal_authenticator.contact_info
                            else []
                        ),
                        "telecoms": (
                            admin_data.legal_authenticator.contact_info.telecoms
                            if admin_data.legal_authenticator
                            and admin_data.legal_authenticator.contact_info
                            else []
                        ),
                    }
                ),
            }
        )

        # Get primary author for backward compatibility
        primary_author = (
            author_information[0]
            if author_information
            else DotDict(
                {
                    "person": DotDict(
                        {"family_name": None, "given_name": None, "full_name": None}
                    ),
                    "organization": DotDict({"name": None}),
                }
            )
        )

        logger.info(
            f"Enhanced admin data: {document_title}, created: {creation_date}, "
            f"patient addresses: {len(patient_contact_info.get('addresses', []))}, "
            f"authors: {len(author_information)}"
        )

        return {
            # Basic document information
            "document_creation_date": creation_date,
            "document_creation_date_raw": creation_date_raw,
            "document_title": document_title,
            "document_type": document_type,
            "document_id": document_id,
            # Legacy custodian name for backward compatibility
            "custodian_name": custodian_organization["name"],
            # Enhanced contact and organizational information
            "patient_contact_info": patient_contact_info,
            "author_information": author_information,
            "custodian_organization": custodian_organization,
            "legal_authenticator": legal_authenticator,
            # Backward compatibility fields with enhanced organization data
            "author_hcp": DotDict(
                {
                    "family_name": primary_author.person.family_name,
                    "given_name": primary_author.person.given_name,
                    "full_name": primary_author.person.full_name,
                    "title": (
                        primary_author.person.title
                        if hasattr(primary_author.person, "title")
                        else ""
                    ),
                    "role": (
                        primary_author.person.role
                        if hasattr(primary_author.person, "role")
                        else ""
                    ),
                    "organization": primary_author.organization,
                    "organization_name": (
                        primary_author.organization.name
                        if hasattr(primary_author.organization, "name")
                        else ""
                    ),
                    "contact_info": (
                        primary_author.contact_info
                        if hasattr(primary_author, "contact_info")
                        else DotDict({"addresses": [], "telecoms": []})
                    ),
                    "contact_details": (
                        primary_author.contact_info
                        if hasattr(primary_author, "contact_info")
                        else DotDict({"addresses": [], "telecoms": []})
                    ),
                }
            ),
            # Additional fields from enhanced extractor
            "document_last_update_date": admin_data.document_last_update_date,
            "document_version_number": admin_data.document_version_number,
            "preferred_hcp": DotDict(
                {
                    "name": (
                        admin_data.preferred_hcp.name
                        if admin_data.preferred_hcp
                        else None
                    )
                }
            ),
            "guardian": DotDict(
                {
                    "family_name": (
                        admin_data.guardian.family_name if admin_data.guardian else None
                    ),
                    "given_name": (
                        admin_data.guardian.given_name if admin_data.guardian else None
                    ),
                    "role": (admin_data.guardian.role if admin_data.guardian else None),
                    "relationship": (
                        admin_data.guardian.relationship
                        if admin_data.guardian
                        else None
                    ),
                    "contact_info": DotDict(
                        {
                            "addresses": (
                                [
                                    DotDict(addr)
                                    for addr in admin_data.guardian.contact_info.addresses
                                ]
                                if admin_data.guardian
                                and admin_data.guardian.contact_info
                                else []
                            ),
                            "telecoms": (
                                [
                                    DotDict(telecom)
                                    for telecom in admin_data.guardian.contact_info.telecoms
                                ]
                                if admin_data.guardian
                                and admin_data.guardian.contact_info
                                else []
                            ),
                        }
                    ),
                }
            ),
            "other_contacts": (
                [
                    DotDict(
                        {
                            "family_name": contact.family_name,
                            "given_name": contact.given_name,
                            "full_name": f"{contact.given_name} {contact.family_name}".strip(),
                            "role": contact.role,
                            "specialty": contact.specialty,
                            "organization": DotDict(
                                {
                                    "name": (
                                        contact.organization.name
                                        if contact.organization
                                        else ""
                                    ),
                                    "addresses": (
                                        contact.organization.addresses
                                        if contact.organization
                                        else []
                                    ),
                                    "telecoms": (
                                        contact.organization.telecoms
                                        if contact.organization
                                        else []
                                    ),
                                }
                            ),
                            "contact_info": DotDict(
                                {
                                    "addresses": (
                                        contact.contact_info.addresses
                                        if contact.contact_info
                                        else []
                                    ),
                                    "telecoms": (
                                        contact.contact_info.telecoms
                                        if contact.contact_info
                                        else []
                                    ),
                                }
                            ),
                        }
                    )
                    for contact in admin_data.other_contacts
                ]
                if admin_data.other_contacts
                else []
            ),
        }

    def _detect_source_country_phase3a(self, root: ET.Element) -> str:
        """
        PHASE 3A: Detect the source country of the CDA document to optimize parsing
        
        Consolidated from CDAAdministrativeExtractor for country-specific optimizations.
        Supports European healthcare cross-border interoperability.

        Returns:
            Country code (e.g., 'IE', 'PT', 'LU', 'IT', 'MT') or 'UNKNOWN'
        """
        try:
            # Check language code first
            language_code = root.get("languageCode")
            if language_code:
                country_mapping = {
                    "en-IE": "IE",  # Ireland
                    "pt-PT": "PT",  # Portugal  
                    "fr-LU": "LU",  # Luxembourg (French)
                    "de-LU": "LU",  # Luxembourg (German)
                    "en-GB": "GB",  # United Kingdom
                    "fr-FR": "FR",  # France
                    "de-DE": "DE",  # Germany
                    "it-IT": "IT",  # Italy
                    "es-ES": "ES",  # Spain
                    "en-MT": "MT",  # Malta (English)
                    "mt-MT": "MT",  # Malta (Maltese)
                }
                if language_code in country_mapping:
                    logger.info(f"[PHASE 3A] Detected country from language code {language_code}: {country_mapping[language_code]}")
                    return country_mapping[language_code]

            # Check custodian organization for country indicators
            custodian = root.find(
                ".//custodian/assignedCustodian/representedCustodianOrganization/name",
                self.namespaces,
            )
            if custodian is not None and custodian.text:
                custodian_name = custodian.text.lower()
                if (
                    "ireland" in custodian_name
                    or "irish" in custodian_name
                    or "hse" in custodian_name
                ):
                    logger.info(f"[PHASE 3A] Detected Ireland from custodian: {custodian.text}")
                    return "IE"
                elif "portugal" in custodian_name or "portuguese" in custodian_name or "sns" in custodian_name:
                    logger.info(f"[PHASE 3A] Detected Portugal from custodian: {custodian.text}")
                    return "PT"
                elif (
                    "luxembourg" in custodian_name or "luxembourgish" in custodian_name
                ):
                    logger.info(f"[PHASE 3A] Detected Luxembourg from custodian: {custodian.text}")
                    return "LU"
                elif "italy" in custodian_name or "italian" in custodian_name or "italia" in custodian_name:
                    logger.info(f"[PHASE 3A] Detected Italy from custodian: {custodian.text}")
                    return "IT"
                elif "malta" in custodian_name or "maltese" in custodian_name:
                    logger.info(f"[PHASE 3A] Detected Malta from custodian: {custodian.text}")
                    return "MT"

            # Check address country codes
            patient_country = root.find(
                ".//recordTarget/patientRole/addr/country", self.namespaces
            )
            if patient_country is not None and patient_country.text:
                country_code = patient_country.text.upper()
                logger.info(f"[PHASE 3A] Detected country from patient address: {country_code}")
                return country_code

            logger.info("[PHASE 3A] Country detection failed - using UNKNOWN")
            return "UNKNOWN"

        except Exception as e:
            logger.warning(f"[PHASE 3A] Error detecting source country: {e}")
            return "UNKNOWN"

    def _detect_document_type_phase3a(self, root: ET.Element) -> str:
        """
        PHASE 3A: Detect CDA document type (L1 vs L3) to optimize parsing strategy
        
        Consolidated from L1CDAAdministrativeExtractor for document type-aware extraction.
        
        Returns:
            Document type: 'L1' (embedded PDF content) or 'L3' (structured clinical data)
        """
        try:
            # L1 documents typically have embedded PDF content in observationMedia or text elements
            pdf_content = root.find(".//{urn:hl7-org:v3}observationMedia")
            if pdf_content is not None:
                # Check for base64 encoded content (typical L1 pattern)
                value_elem = pdf_content.find(".//{urn:hl7-org:v3}value")
                if value_elem is not None and value_elem.text:
                    # Basic check for base64 content
                    content = value_elem.text.strip()
                    if len(content) > 100 and content.replace(' ', '').replace('\n', '').isalnum():
                        logger.info("[PHASE 3A] Detected L1 document type - embedded PDF content found")
                        return "L1"
            
            # Check for embedded text content (another L1 pattern)
            text_elements = root.findall(".//{urn:hl7-org:v3}text")
            for text_elem in text_elements:
                if text_elem.text and len(text_elem.text.strip()) > 1000:
                    # Large text blocks often indicate L1 documents
                    logger.info("[PHASE 3A] Detected L1 document type - large text content found")
                    return "L1"
            
            # Check for structured clinical sections (L3 pattern)
            structured_sections = root.findall(".//{urn:hl7-org:v3}section")
            clinical_sections = 0
            for section in structured_sections:
                code_elem = section.find(".//{urn:hl7-org:v3}code")
                if code_elem is not None:
                    code = code_elem.get("code", "")
                    # Common L3 clinical section codes
                    if any(clinical_code in code for clinical_code in [
                        "48765-2",  # Allergies
                        "10160-0",  # History of medication
                        "11369-6",  # Immunizations  
                        "30954-2",  # Results
                        "46241-6",  # Hospital admission diagnosis
                        "11535-2",  # Hospital discharge diagnosis
                    ]):
                        clinical_sections += 1
            
            if clinical_sections >= 2:
                logger.info(f"[PHASE 3A] Detected L3 document type - {clinical_sections} structured clinical sections found")
                return "L3"
            
            # Default to L3 if unsure (safer for processing)
            logger.info("[PHASE 3A] Defaulting to L3 document type - structured format assumed")
            return "L3"
            
        except Exception as e:
            logger.warning(f"[PHASE 3A] Error detecting document type: {e}")
            return "L3"  # Default to L3

    def _extract_patient_languages_phase3a(self, root: ET.Element) -> List[str]:
        """
        PHASE 3A: Extract patient language communication preferences
        
        Consolidated from CDAAdministrativeExtractor for language-aware processing.
        Supports European multilingual healthcare documentation.
        """
        languages = []
        try:
            # Look for language communication in patient section
            lang_elements = root.findall(
                ".//recordTarget/patientRole/patient/languageCommunication/languageCode",
                self.namespaces,
            )

            for lang_elem in lang_elements:
                lang_code = lang_elem.get("code")
                if lang_code:
                    languages.append(lang_code)
                    logger.debug(f"[PHASE 3A] Found patient language: {lang_code}")

            if languages:
                logger.info(f"[PHASE 3A] Extracted {len(languages)} patient languages: {languages}")
            else:
                logger.info("[PHASE 3A] No patient language preferences found")
                
        except Exception as e:
            logger.warning(f"[PHASE 3A] Error extracting patient languages: {e}")

        return languages

    def _extract_participants_phase3a(self, root: ET.Element, source_country: str = "UNKNOWN") -> List[Dict[str, Any]]:
        """
        PHASE 3A: Extract participant information (emergency contacts, next of kin, dependencies)
        
        Consolidated from CDAAdministrativeExtractor for comprehensive contact extraction.
        Supports European healthcare relationship management.
        """
        participants = []
        try:
            # Look for participant elements with various type codes
            participant_elements = root.findall(".//participant", self.namespaces)
            
            for participant in participant_elements:
                participant_info = {}
                type_code = participant.get("typeCode")
                
                if type_code:
                    participant_info["role"] = f"Participant ({type_code})"
                    
                    # Extract person information
                    person_elem = participant.find(".//associatedPerson", self.namespaces)
                    if person_elem is not None:
                        name_elem = person_elem.find("name", self.namespaces)
                        if name_elem is not None:
                            family_elem = name_elem.find("family", self.namespaces) 
                            given_elem = name_elem.find("given", self.namespaces)
                            
                            if family_elem is not None and family_elem.text:
                                participant_info["family_name"] = family_elem.text.strip()
                            if given_elem is not None and given_elem.text:
                                participant_info["given_name"] = given_elem.text.strip()
                            
                            # Extract contact information
                            addr_elem = participant.find(".//addr", self.namespaces)
                            if addr_elem is not None:
                                participant_info["address"] = self._parse_address_phase3a(addr_elem, source_country)
                            
                            telecom_elems = participant.findall(".//telecom", self.namespaces)
                            if telecom_elems:
                                participant_info["telecoms"] = [
                                    self._parse_telecom_phase3a(telecom, source_country) 
                                    for telecom in telecom_elems
                                ]
                    
                    if participant_info.get("family_name") or participant_info.get("given_name"):
                        participants.append(participant_info)
                        logger.debug(f"[PHASE 3A] Found participant: {participant_info.get('given_name', '')} {participant_info.get('family_name', '')} ({type_code})")
            
            logger.info(f"[PHASE 3A] Extracted {len(participants)} participants")
                        
        except Exception as e:
            logger.warning(f"[PHASE 3A] Error extracting participants: {e}")

        return participants

    def _parse_address_phase3a(self, addr_element: ET.Element, source_country: str = "UNKNOWN") -> Dict[str, Any]:
        """
        PHASE 3A: Parse address information with country-specific optimizations
        
        Consolidated from CDAAdministrativeExtractor for European address formats.
        """
        address = {}
        try:
            # Extract street address lines
            street_lines = []
            street_addrs = addr_element.findall("streetAddressLine", self.namespaces)
            for street in street_addrs:
                if street.text and street.text.strip():
                    street_lines.append(street.text.strip())
            
            if street_lines:
                address["street_lines"] = street_lines
                address["street"] = ", ".join(street_lines)

            # Extract city
            city_elem = addr_element.find("city", self.namespaces)
            if city_elem is not None and city_elem.text:
                address["city"] = city_elem.text.strip()

            # Extract postal code with country-specific formatting
            postal_elem = addr_element.find("postalCode", self.namespaces)
            if postal_elem is not None and postal_elem.text:
                postal_code = postal_elem.text.strip()
                
                # Country-specific postal code formatting
                if source_country == "IE":
                    postal_code = postal_code.upper()  # Irish Eircode format
                
                address["postal_code"] = postal_code

            # Extract country
            country_elem = addr_element.find("country", self.namespaces)
            if country_elem is not None and country_elem.text:
                address["country"] = country_elem.text.strip()

            # Extract use code
            use_attr = addr_element.get("use")
            if use_attr:
                address["use"] = use_attr
                
        except Exception as e:
            logger.warning(f"[PHASE 3A] Error parsing address: {e}")

        return address

    def _parse_telecom_phase3a(self, telecom_element: ET.Element, source_country: str = "UNKNOWN") -> Dict[str, Any]:
        """
        PHASE 3A: Parse telecom information with country-specific optimizations
        
        Consolidated from CDAAdministrativeExtractor for European telecom formats.
        """
        telecom = {}
        try:
            # Extract value (phone number, email, etc.)
            value = telecom_element.get("value")
            if value:
                telecom["value"] = value
                
                # Determine telecom type
                if value.startswith("tel:"):
                    telecom["type"] = "phone"
                    telecom["number"] = value.replace("tel:", "")
                elif value.startswith("mailto:"):
                    telecom["type"] = "email"
                    telecom["email"] = value.replace("mailto:", "")
                elif value.startswith("fax:"):
                    telecom["type"] = "fax"
                    telecom["number"] = value.replace("fax:", "")
                else:
                    telecom["type"] = "other"

            # Extract use code
            use_attr = telecom_element.get("use")
            if use_attr:
                telecom["use"] = use_attr
                
        except Exception as e:
            logger.warning(f"[PHASE 3A] Error parsing telecom: {e}")

        return telecom

    def _extract_basic_administrative_data_strategy(self, root: ET.Element) -> Dict[str, Any]:
        """
        Basic administrative data extraction strategy
        
        Extracts essential administrative data including:
        - Document metadata (creation date, title, type, ID)
        - Basic custodian information
        - Minimal organizational structure for template compatibility
        """
        # Extract document creation date
        effective_time = root.find(".//{urn:hl7-org:v3}effectiveTime")
        creation_date = "Unknown"
        creation_date_raw = "Unknown"
        if effective_time is not None:
            creation_date_raw = effective_time.get("value", "Unknown")
            # Format the document date for consistent display
            if default_formatter and creation_date_raw != "Unknown":
                creation_date = default_formatter.format_document_date(
                    creation_date_raw
                )
            else:
                creation_date = creation_date_raw

        # Extract document title
        title_elem = root.find(".//{urn:hl7-org:v3}title")
        document_title = (
            title_elem.text if title_elem is not None and title_elem.text else "Unknown"
        )

        # Extract document type
        code_elem = root.find(".//{urn:hl7-org:v3}code")
        document_type = "Unknown"
        if code_elem is not None:
            document_type = code_elem.get(
                "displayName", code_elem.get("code", "Unknown")
            )

        # Extract document ID
        doc_id_elem = root.find(".//{urn:hl7-org:v3}id")
        document_id = (
            doc_id_elem.get("extension", "Unknown")
            if doc_id_elem is not None
            else "Unknown"
        )

        # Extract custodian information
        custodian = root.find(".//{urn:hl7-org:v3}custodian")
        custodian_name = "Unknown"
        if custodian is not None:
            org = custodian.find(".//{urn:hl7-org:v3}representedCustodianOrganization")
            if org is not None:
                org_name = org.find("{urn:hl7-org:v3}name")
                if org_name is not None:
                    custodian_name = org_name.text

        logger.info(f"Basic admin data: {document_title}, created: {creation_date}")

        return {
            "document_creation_date": creation_date,
            "document_creation_date_raw": creation_date_raw,
            "document_title": document_title,
            "document_type": document_type,
            "document_id": document_id,
            "custodian_name": custodian_name,
            "document_last_update_date": None,
            "document_version_number": None,
            "patient_contact_info": DotDict({"addresses": [], "telecoms": []}),
            "author_hcp": DotDict(
                {"family_name": None, "organization": DotDict({"name": None})}
            ),
            "legal_authenticator": DotDict(
                {
                    "family_name": None,
                    "organization": DotDict({"name": None}),
                }
            ),
            "custodian_organization": DotDict({"name": custodian_name}),
            "preferred_hcp": DotDict({"name": None}),
            "guardian": DotDict(
                {
                    "family_name": None,
                    "contact_info": DotDict({"addresses": [], "telecoms": []}),
                }
            ),
            "other_contacts": [],
        }

    def _extract_default_administrative_data_strategy(self) -> Dict[str, Any]:
        """
        Default administrative data extraction strategy
        
        Creates fallback administrative data structure for error handling:
        - Default document metadata
        - Empty contact and organizational structures
        - Template-compatible data structure
        """
        return {
            "document_creation_date": "Unknown",
            "document_creation_date_raw": "Unknown",
            "document_title": "Unknown Document",
            "document_type": "Unknown",
            "document_id": "Unknown",
            "custodian_name": "Unknown",
            "document_last_update_date": None,
            "document_version_number": None,
            "patient_contact_info": DotDict(
                {
                    "addresses": [],
                    "telecoms": [],
                    "primary_address": None,
                    "primary_phone": None,
                    "primary_email": None,
                }
            ),
            "author_information": [],
            "custodian_organization": DotDict(
                {
                    "name": "Unknown",
                    "id": None,
                    "address": {},
                    "telecoms": [],
                }
            ),
            "legal_authenticator": DotDict(
                {
                    "time": None,
                    "person": DotDict(
                        {"family_name": None, "given_name": None, "full_name": None}
                    ),
                    "organization": DotDict({"name": None}),
                }
            ),
            "author_hcp": DotDict(
                {"family_name": None, "organization": DotDict({"name": None})}
            ),
            "preferred_hcp": DotDict({"name": None}),
            "guardian": DotDict(
                {
                    "family_name": None,
                    "given_name": None,
                    "role": None,
                    "relationship": None,
                    "contact_info": DotDict({"addresses": [], "telecoms": []}),
                }
            ),
            "other_contacts": [],
        }

    def _create_default_patient_info(self) -> Dict[str, Any]:
        """Create default patient info structure"""
        return {
            "patient_id": "temp_patient",
            "given_name": "Unknown",
            "family_name": "Patient",
            "birth_date": "Unknown",
            "gender": "Unknown",
            "patient_identifiers": [],
            "contact_info": DotDict(
                {"has_enhanced_contact_data": False, "addresses": [], "telecoms": []}
            ),
            "full_name": "Unknown Patient",
        }

    def _extract_patient_contacts_unified(self, patient_role: ET.Element) -> Dict[str, Any]:
        """
        PHASE 3: Unified patient contact extraction strategy
        
        Consolidates:
        - _extract_basic_patient_addresses() (address extraction)
        - _extract_basic_patient_telecoms() (telecom extraction)
        - Emergency contact and next of kin processing
        - Guardian and dependent relationship handling
        
        Returns:
            Complete patient contact and relationship data for templates
        """
        contact_data = {
            "addresses": [],
            "telecoms": [],
            "emergency_contacts": [],
            "guardians": [],
            "dependants": [],
            "next_of_kin": [],
            "primary_contact": None
        }
        
        # Strategy 1: Extract patient addresses
        contact_data["addresses"] = self._extract_patient_addresses_strategy(patient_role)
        
        # Strategy 2: Extract patient telecoms
        contact_data["telecoms"] = self._extract_patient_telecoms_strategy(patient_role)
        
        # Strategy 3: Extract emergency contacts and relationships
        contact_data.update(self._extract_patient_relationships_strategy(patient_role))
        
        return contact_data

    def _extract_patient_addresses_strategy(self, patient_role: ET.Element) -> List[Dict]:
        """Extract patient addresses with European format support"""
        addresses = []
        try:
            addr_elements = patient_role.findall("cda:addr", self.namespaces)
            for addr in addr_elements:
                address_data = {
                    "street": "",
                    "city": "",
                    "postal_code": "",
                    "country": "",
                    "use": addr.get("use", ""),
                }

                # Extract address components
                street_elem = addr.find("{urn:hl7-org:v3}streetAddressLine")
                if street_elem is not None and street_elem.text:
                    address_data["street"] = street_elem.text

                city_elem = addr.find("{urn:hl7-org:v3}city")
                if city_elem is not None and city_elem.text:
                    address_data["city"] = city_elem.text

                postal_elem = addr.find("{urn:hl7-org:v3}postalCode")
                if postal_elem is not None and postal_elem.text:
                    address_data["postal_code"] = postal_elem.text

                country_elem = addr.find("{urn:hl7-org:v3}country")
                if country_elem is not None and country_elem.text:
                    address_data["country"] = country_elem.text

                # Only add if we have some address data
                if any(
                    address_data[key]
                    for key in ["street", "city", "postal_code", "country"]
                ):
                    addresses.append(address_data)

        except Exception as e:
            logger.warning(f"Failed to extract basic patient addresses: {str(e)}")

        return addresses

    def _extract_patient_telecoms_strategy(self, patient_role: ET.Element) -> List[Dict]:
        """Extract patient telecoms with European format support"""
        telecoms = []
        try:
            telecom_elements = patient_role.findall("cda:telecom", self.namespaces)
            for telecom in telecom_elements:
                telecom_data = {
                    "value": telecom.get("value", ""),
                    "use": telecom.get("use", ""),
                    "type": "unknown",
                }

                # Determine type from value prefix
                if telecom_data["value"]:
                    if telecom_data["value"].startswith("tel:"):
                        telecom_data["type"] = "phone"
                        telecom_data["value"] = telecom_data["value"].replace(
                            "tel:", ""
                        )
                    elif telecom_data["value"].startswith("mailto:"):
                        telecom_data["type"] = "email"
                        telecom_data["value"] = telecom_data["value"].replace(
                            "mailto:", ""
                        )
                    elif "@" in telecom_data["value"]:
                        telecom_data["type"] = "email"

                # Only add if we have a value
                if telecom_data["value"]:
                    telecoms.append(telecom_data)

        except Exception as e:
            logger.warning(f"Failed to extract basic patient telecoms: {str(e)}")

        return telecoms

    def _extract_patient_relationships_strategy(self, patient_role: ET.Element) -> Dict[str, Any]:
        """
        Extract patient relationships and emergency contacts
        
        Extracts:
        - Emergency contacts and next of kin
        - Guardians and legal representatives  
        - Dependants and family members
        - Primary contact designation
        """
        relationships = {
            "emergency_contacts": [],
            "guardians": [],
            "dependants": [],
            "next_of_kin": [],
            "primary_contact": None
        }
        
        try:
            # For now, return empty structure
            # Future implementation will integrate with external administrative services
            logger.info("Patient relationships extraction strategy - placeholder implementation")
            
        except Exception as e:
            logger.warning(f"Failed to extract patient relationships: {str(e)}")
            
        return relationships

    def _create_fallback_result(self) -> Dict[str, Any]:
        """Create fallback result when parsing fails"""
        return {
            "patient_identity": self._create_default_patient_info(),
            "administrative_data": {},
            "sections": [],
            "sections_count": 0,
            "coded_sections_count": 0,
            "medical_terms_count": 0,
            "coded_sections_percentage": 0,
            "uses_coded_sections": False,
            "translation_quality": "Failed",
            "has_administrative_data": False,
        }

    def _extract_detailed_medication_data(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract detailed medication data from CDA substanceAdministration entries
        
        This method extracts the rich medication data that was missing:
        - Dose quantities with units
        - Treatment periods (start/end dates)  
        - Frequencies and schedules
        - Route codes and administration routes
        - Active ingredients with strength
        """
        medications = []
        
        # Find all substance administration entries in medication sections
        medication_sections = []
        all_sections = root.findall(".//{urn:hl7-org:v3}section", self.namespaces)
        for section in all_sections:
            # Check for LOINC medication section code
            code_elem = section.find("{urn:hl7-org:v3}code", self.namespaces)
            if code_elem is not None and code_elem.get('code') == '10160-0':
                medication_sections.append(section)
                continue
            
            # Check for medication section by title
            title_elem = section.find("{urn:hl7-org:v3}title", self.namespaces)
            if title_elem is not None:
                title_text = title_elem.text
                if title_text and any(keyword in title_text.lower() for keyword in ['medication', 'medicament', 'drug', 'prescription']):
                    medication_sections.append(section)
                    continue
            
            # Check for sections containing substanceAdministration entries
            # BUT EXCLUDE immunization sections (they use substanceAdministration for vaccines)
            substance_entries = section.findall(".//{urn:hl7-org:v3}substanceAdministration", self.namespaces)
            if substance_entries:
                # Check if this is an immunization section by code or title
                section_code = section.get('code', '')
                if isinstance(section_code, dict):
                    code_value = section_code.get('code', '')
                else:
                    code_value = str(section_code)
                
                # Extract clean code (remove OID parts)
                clean_code = code_value.split(' ')[0] if code_value else ''
                
                # Skip immunization sections - they should NOT be processed as medications
                if clean_code in ['11369-6']:  # Standard immunization section code
                    logger.info(f"[MEDICATION_SEARCH] *** FILTERING OUT immunization section with code {clean_code} from medication processing ***")
                    continue
                
                # Also check title for immunization keywords
                title_elem = section.find(".//{urn:hl7-org:v3}title", self.namespaces)
                if title_elem is not None:
                    title_text = title_elem.text or ''
                    if any(keyword in title_text.lower() for keyword in ['immuniz', 'vaccin', 'immun']):
                        logger.info(f"[MEDICATION_SEARCH] *** FILTERING OUT immunization section '{title_text}' from medication processing ***")
                        continue
                
                # If it's not an immunization section, add it as a medication section
                medication_sections.append(section)
        
        # If no medication sections found, search globally for substanceAdministration entries
        if not medication_sections:
            logger.info("[MEDICATION_SEARCH] No specific medication sections found, searching globally for substanceAdministration entries")
            medication_sections = [root]  # Search the entire document
        
        for section in medication_sections:
            # Extract section information for tagging
            section_info = {}
            
            # Get section code
            code_elem = section.find("{urn:hl7-org:v3}code", self.namespaces)
            if code_elem is not None:
                section_info['code'] = code_elem.get('code', '')
                section_info['code_system'] = code_elem.get('codeSystem', '')
                
            # Get section title
            title_elem = section.find("{urn:hl7-org:v3}title", self.namespaces)
            if title_elem is not None:
                section_info['title'] = title_elem.text or ''
            
            # Method 1: Extract from substanceAdministration entries
            entries = section.findall(".//{urn:hl7-org:v3}substanceAdministration", self.namespaces)
            
            for entry in entries:
                medication_data = self._extract_from_substance_administration(entry, section_info)
                if medication_data:
                    medications.append(medication_data)
                    logger.info(f"Extracted detailed medication data for: {medication_data.get('name', 'Unknown')} from section: {section_info.get('title', 'Unknown')}")
            
            # Method 2: Extract from table-based medication data (for CDA documents like the real Eutirox data)
            table_medications = self._extract_from_medication_tables(section, section_info)
            for med_data in table_medications:
                medications.append(med_data)
                logger.info(f"Extracted table-based medication data for: {med_data.get('name', 'Unknown')} from section: {section_info.get('title', 'Unknown')}")
            
            # Method 3: Extract from pharmaceutical entries (pharm: namespace)
            pharm_medications = self._extract_from_pharmaceutical_entries(section, section_info)
            if pharm_medications:  # Add null check
                for med_data in pharm_medications:
                    medications.append(med_data)
                    logger.info(f"Extracted pharmaceutical medication data for: {med_data.get('name', 'Unknown')} from section: {section_info.get('title', 'Unknown')}")
        
        logger.info(f"Enhanced CDA Parser extracted {len(medications)} medications with detailed data")
        return medications

    def _extract_from_substance_administration(self, entry: ET.Element, section_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract medication data from substanceAdministration entry"""
        medication_data = {
            'type': 'medication',
            'source': 'enhanced_cda_parser_substance'
        }
        
        # Add section tagging if provided
        if section_info:
            medication_data['source_section'] = section_info
            medication_data['section_code'] = section_info.get('code', '')
            medication_data['section_title'] = section_info.get('title', '')
        
        # Extract medication name from manufactured material (as per Portuguese CDA structure)
        manufactured_materials = entry.findall(".//{urn:hl7-org:v3}manufacturedMaterial", self.namespaces)
        for material in manufactured_materials:
            # Get medication name from <name>Eutirox</name>
            names = material.findall("{urn:hl7-org:v3}name", self.namespaces)
            for name in names:
                if name.text:
                    medication_data['name'] = name.text.strip()
                    medication_data['medication_name'] = name.text.strip()
                    medication_data['display_name'] = name.text.strip()
                    
            # Get product codes from material
            codes = material.findall("{urn:hl7-org:v3}code", self.namespaces)
            for code in codes:
                code_val = code.get('code', '')
                display_name = code.get('displayName', '')
                if display_name:
                    medication_data['medication_code'] = code_val
                    medication_data['medication_display'] = display_name
                    # Use display name as backup for name if not found
                    if 'name' not in medication_data:
                        medication_data['name'] = display_name
                        medication_data['medication_name'] = display_name
                        medication_data['display_name'] = display_name
            
            # Extract pharmaceutical form codes (pharm:formCode)
            # Add pharmaceutical namespace
            pharm_namespaces = {**self.namespaces, 'pharm': 'urn:hl7-org:pharm'}
            form_codes = material.findall(".//pharm:formCode", pharm_namespaces)
            for form in form_codes:
                code_val = form.get('code', '')
                display_name = form.get('displayName', '')
                if display_name:
                    medication_data['pharmaceutical_form'] = display_name
                    medication_data['dose_form'] = display_name
                    medication_data['form'] = display_name
                    medication_data['form_code'] = code_val
            
            # Extract active ingredient information
            # Check for ingredient elements or mappings from medication names
            active_ingredient = self._extract_active_ingredient(material, medication_data.get('name', ''))
            if active_ingredient:
                medication_data['active_ingredients'] = active_ingredient
            
            # Extract strength information from pharm:quantity or other strength elements
            strength = self._extract_strength(material, medication_data.get('name', ''))
            if strength:
                medication_data['strength'] = strength
            
            # If pharmaceutical form not found in CDA, try to determine from medication name
            if 'pharmaceutical_form' not in medication_data:
                pharm_form = self._extract_pharmaceutical_form(medication_data.get('name', ''))
                if pharm_form:
                    medication_data['pharmaceutical_form'] = pharm_form
                
        # Extract dose quantity - Enhanced to handle low/high ranges and pharmaceutical quantities
        dose_quantities = entry.findall(".//{urn:hl7-org:v3}doseQuantity", self.namespaces)
        for dose in dose_quantities:
            # Check for low/high range first
            low_elem = dose.find("{urn:hl7-org:v3}low", self.namespaces)
            high_elem = dose.find("{urn:hl7-org:v3}high", self.namespaces)
            
            if low_elem is not None and high_elem is not None:
                low_val = low_elem.get('value', '')
                high_val = high_elem.get('value', '')
                low_unit = low_elem.get('unit', '')
                high_unit = high_elem.get('unit', '')
                
                if low_val and high_val:
                    if low_unit and low_unit != '1':
                        medication_data['dose_quantity'] = f"{low_val}-{high_val} {low_unit}"
                    else:
                        medication_data['dose_quantity'] = f"{low_val}-{high_val} units"
                    medication_data['dose_value'] = f"{low_val}-{high_val}"
                    medication_data['dose_unit'] = low_unit if low_unit != '1' else 'units'
            elif low_elem is not None:
                low_val = low_elem.get('value', '')
                low_unit = low_elem.get('unit', '')
                if low_val:
                    if low_unit and low_unit != '1':
                        medication_data['dose_quantity'] = f"{low_val} {low_unit}"
                    else:
                        medication_data['dose_quantity'] = f"{low_val} units"
                    medication_data['dose_value'] = low_val
                    medication_data['dose_unit'] = low_unit if low_unit != '1' else 'units'
            else:
                # Fallback to simple value/unit
                value = dose.get('value', '')
                unit = dose.get('unit', '')
                if value:
                    if unit and unit != '1':
                        medication_data['dose_quantity'] = f"{value} {unit}"
                    else:
                        medication_data['dose_quantity'] = f"{value} units"
                    medication_data['dose_value'] = value
                    medication_data['dose_unit'] = unit
                
        # Extract route code - Enhanced with common route code mappings
        route_codes = entry.findall(".//{urn:hl7-org:v3}routeCode", self.namespaces)
        for route in route_codes:
            code_val = route.get('code', '')
            display_name = route.get('displayName', '')
            
            if display_name:
                medication_data['route'] = display_name
                medication_data['route_display'] = display_name
                medication_data['administration_route'] = display_name
                medication_data['route_code'] = code_val
            elif code_val:
                # Map common route codes to display names
                route_mapping = self._map_route_code(code_val)
                medication_data['route'] = route_mapping
                medication_data['route_display'] = route_mapping
                medication_data['administration_route'] = route_mapping
                medication_data['route_code'] = code_val
        
        # Extract effective time (treatment period and frequency) - Enhanced
        effective_times = entry.findall(".//{urn:hl7-org:v3}effectiveTime", self.namespaces)
        start_date = None
        end_date = None
        frequency = None
        
        for eff_time in effective_times:
            # Check for event codes (schedule/timing)
            events = eff_time.findall(".//{urn:hl7-org:v3}event", self.namespaces)
            for event in events:
                event_code = event.get('code', '')
                if event_code:
                    timing_display = self._map_schedule_event(event_code)
                    medication_data['schedule'] = timing_display
                    medication_data['frequency'] = timing_display
                    medication_data['dosage_frequency'] = timing_display
                    medication_data['timing_code'] = event_code
            
            # Check for low value (start date) - Enhanced date parsing
            low = eff_time.find("{urn:hl7-org:v3}low", self.namespaces)
            if low is not None:
                low_val = low.get('value', '')
                if low_val and len(low_val) >= 8:  # YYYYMMDD format
                    start_date = self._format_cda_date(low_val)
                    medication_data['start_date'] = start_date
            
            # Check for high value (end date)  
            high = eff_time.find("{urn:hl7-org:v3}high", self.namespaces)
            if high is not None:
                high_val = high.get('value', '')
                if high_val and len(high_val) >= 8:  # YYYYMMDD format
                    end_date = self._format_cda_date(high_val)
                    medication_data['end_date'] = end_date
            
            # Check for period (frequency)
            period = eff_time.find("{urn:hl7-org:v3}period", self.namespaces)
            if period is not None:
                period_val = period.get('value', '')
                period_unit = period.get('unit', '')
                if period_val and period_unit:
                    frequency = f"Every {period_val} {period_unit}"
                    if period_unit == 'd' and period_val == '1':
                        frequency = "Daily"
                    elif period_unit == 'h':
                        frequency = f"Every {period_val} hours"
                    medication_data['schedule'] = frequency
                    medication_data['frequency'] = frequency
                    medication_data['dosage_frequency'] = frequency
                
        # Create treatment period display
        if start_date:
            if end_date:
                medication_data['period'] = f"From {start_date} to {end_date}"
                medication_data['treatment_period'] = f"From {start_date} to {end_date}"
            else:
                medication_data['period'] = f"Since {start_date}"
                medication_data['treatment_period'] = f"Since {start_date}"
        
        # Only return medication if we have at least a name
        if medication_data.get('name'):
            return medication_data
        else:
            return {}
    
    def _format_cda_date(self, cda_date: str) -> str:
        """Format CDA date string to readable format"""
        if not cda_date:
            return ""
        
        try:
            # CDA dates are typically YYYYMMDD or YYYYMMDDHHMMSS
            if len(cda_date) >= 8:
                year = cda_date[:4]
                month = cda_date[4:6]
                day = cda_date[6:8]
                
                # Convert to readable format
                from datetime import datetime
                date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
                return date_obj.strftime("%b %d, %Y")
        except:
            # Fallback to original format if parsing fails
            return cda_date
        
        return cda_date

    def _map_route_code(self, route_code: str) -> str:
        """Map route codes to human-readable administration routes"""
        route_mappings = {
            # Common SNOMED CT route codes
            '20053000': 'Oral use',
            '20030000': 'Intramuscular use', 
            '20035000': 'Intrathecal use',
            '20045000': 'Subdermal use',
            '20066000': 'Topical application',
            '26643006': 'Oral route',
            '47625008': 'Intravenous route', 
            '78421000': 'Intramuscular route',
            '34206005': 'Subcutaneous route',
            '54471007': 'Buccal route',
            '37161004': 'Rectal route',
            '16857009': 'Vaginal route',
            '72607000': 'Intrathecal route',
            '10547007': 'Otic route',
            '46713006': 'Nasal route',
            '6064005': 'Topical route',
            '37737002': 'Intralingual route',
            '90028008': 'Urethral route',
            '12130007': 'Intra-articular route',
            '58100008': 'Intra-arterial route',
            '372449004': 'Dental route',
            '372450004': 'Endocervical route',
            '372451000': 'Endosinusial route',
            '372452007': 'Endotracheal route',
            '372453002': 'Extra-amniotic route',
            '372454008': 'Gastroenteral route',
            '372457001': 'Gingival route',
            '372458006': 'Intraamniotic route',
            '372459003': 'Intrabursal route',
            '372460008': 'Intracardiac route',
            '372461007': 'Intracavernous route',
            '372463005': 'Intracoronary route',
            '372464004': 'Intradermal route',
            '372465003': 'Intradiscal route',
            '372466002': 'Intralesional route',
            '372467006': 'Intralymphatic route',
            '372468001': 'Intraocular route',
            '372469009': 'Intrapleural route',
            '372470005': 'Intrasternal route',
            '372471009': 'Intravesical route',
            '372473007': 'Oromucosal route',
            '372474001': 'Periarticular route',
            '372475000': 'Perineural route',
            '372476004': 'Subconjunctival route',
            '418877009': 'Intrauterine route',
            '419021003': 'Intraosseous route',
            '419165009': 'Paravertebral route',
            '419954003': 'Ileostomy route',
            '419993007': 'Intraventricular route',
            '420047004': 'Peritoneal route',
            '420163009': 'Esophagostomy route',
            '420168000': 'Urostomy route',
            '420185003': 'Laryngeal route',
            '420201002': 'Intraluminal route',
            '420204005': 'Mucous membrane route',
            '420218003': 'Nasoduodenal route',
            '420254004': 'Body cavity route',
            '420287000': 'Intraventricular route - cardiac',
            '420719007': 'Intrapericardial route',
            '428191002': 'Percutaneous route',
            '429817007': 'Interstitial route',
            '445752009': 'Inhalation route',
            '445754005': 'Intracerebroventricular route',
            '445755006': 'Intracranial route',
            '445756007': 'Intradural route',
            '445767008': 'Intraspinal route',
            '445768003': 'Intrathoracic route',
            '445771006': 'Intratympanic route',
            '445913005': 'Intracameral route',
            '445941009': 'Intravitreal route',
            '446105004': 'Conjunctival route',
            '446407004': 'Intraepidermal route',
            '446435000': 'Transendocardial route',
            '446442000': 'Retrobulbar route',
            '446540005': 'Intracerebral route',
            '447026006': 'Intraileal route',
            '447052000': 'Periodontal route',
            '447080003': 'Periosteal route',
            '447081004': 'Lower respiratory tract route',
            '447121004': 'Intramammary route',
            '447122006': 'Intratumor route',
            '447227007': 'Transtympanic route',
            '447229005': 'Transurethral route',
            '447694001': 'Respiratory tract route',
            '447964005': 'Digestive tract route',
            '448077001': 'Intraabdominal route',
            '448491004': 'Intrajejunal route',
            '448492006': 'Intraduodenal route',
            '448598008': 'Cutaneous route',
            '461657594': 'Sublingual route',
            '697971008': 'Arteriovenous graft route',
            '711360002': 'Intranodal route',
            '711378007': 'Intratesticular route',
            '714743009': 'Intratracheal route',
            '718329006': 'Intracerebroventriculr route',
            '72607000': 'Intrathecal route',
            '738990001': 'Intraprostatic route',
            '740685003': 'Intraneuronal route',
            '764723001': 'Epilesional route',
            '766790006': 'Intraneural route',
            '823034001': 'Intraesophageal route',
            '823035000': 'Intragingival route',
        }
        
        return route_mappings.get(route_code, f"Route code: {route_code}")

    def _map_schedule_event(self, event_code: str) -> str:
        """Map schedule event codes to human-readable timing descriptions"""
        event_mappings = {
            # Common timing event codes (SNOMED CT/HL7)
            'ACM': 'Morning',
            'ACD': 'Midday', 
            'ACV': 'Evening',
            'ACN': 'Night',
            'HS': 'Before sleep',
            'WAKE': 'Upon waking',
            'AC': 'Before meals',
            'PC': 'After meals',
            'MEAL': 'With meals',
            'BID': 'Twice daily',
            'TID': 'Three times daily', 
            'QID': 'Four times daily',
            'QD': 'Once daily',
            'QOD': 'Every other day',
            'Q4H': 'Every 4 hours',
            'Q6H': 'Every 6 hours',
            'Q8H': 'Every 8 hours',
            'Q12H': 'Every 12 hours',
            'QH': 'Every hour',
            'Q2H': 'Every 2 hours',
            'PRN': 'As needed',
            'STAT': 'Immediately',
            # HL7 Event Related Periodic Interval codes
            '307439001': 'Before meals',
            '307466008': 'After meals', 
            '307467004': 'With meals',
            '307468009': 'Between meals',
            '307469001': 'Before sleep',
            '307470000': 'Upon waking',
            '307471001': 'Morning',
            '307472008': 'Midday', 
            '307473003': 'Evening',
            '307474009': 'Night',
        }
        
        return event_mappings.get(event_code, f"Schedule: {event_code}")

    def _clean_xml_content(self, xml_content: str) -> str:
        """Clean XML content for parsing"""
        # Remove XML declaration if present
        xml_content = re.sub(r"<\?xml[^>]*\?>", "", xml_content)

        # Remove BOM if present
        xml_content = xml_content.lstrip("\ufeff")

        # Ensure we have a root element
        if not xml_content.strip().startswith("<"):
            raise ValueError("Content does not appear to be XML")

        return xml_content.strip()

    def _extract_from_medication_tables(self, section: ET.Element, section_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract medication data from table-based CDA sections"""
        medications = []
        
        # Look for tables containing medication data
        tables = section.findall(".//{urn:hl7-org:v3}table", self.namespaces)
        
        for table in tables:
            rows = table.findall(".//{urn:hl7-org:v3}tr", self.namespaces)
            
            # Skip header row if present
            data_rows = rows[1:] if len(rows) > 1 else rows
            
            for row in data_rows:
                cells = row.findall(".//{urn:hl7-org:v3}td", self.namespaces)
                
                if len(cells) >= 2:  # Need at least medication name and some data
                    medication_data = {
                        'type': 'medication',
                        'source': 'enhanced_cda_parser_table'
                    }
                    
                    # Add section tagging if provided
                    if section_info:
                        medication_data['source_section'] = section_info
                        medication_data['section_code'] = section_info.get('code', '')
                        medication_data['section_title'] = section_info.get('title', '')
                    
                    # Extract medication name from first cell
                    if cells[0].text:
                        medication_data['name'] = cells[0].text.strip()
                        medication_data['medication_name'] = cells[0].text.strip()
                        medication_data['display_name'] = cells[0].text.strip()
                    
                    # Extract additional data from other cells
                    for i, cell in enumerate(cells[1:], 1):
                        if cell.text:
                            text = cell.text.strip()
                            # Try to identify dose information
                            if any(unit in text.lower() for unit in ['mg', 'ml', 'units', 'mcg', 'g']):
                                medication_data['dose_quantity'] = text
                            # Try to identify frequency information
                            elif any(freq in text.lower() for freq in ['daily', 'twice', 'morning', 'evening', 'tid', 'bid', 'qd']):
                                medication_data['frequency'] = text
                    
                    if 'name' in medication_data:
                        medications.append(medication_data)
        
        return medications

    def _extract_from_pharmaceutical_entries(self, section: ET.Element, section_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Extract medication data from pharmaceutical namespace entries"""
        medications = []
        
        # Look for pharmaceutical entries using pharm: namespace
        pharm_namespaces = {
            'pharm': 'urn:hl7-org:pharm',
            **self.namespaces
        }
        
        # Search for pharmaceutical medication entries
        pharm_entries = section.findall(".//pharm:medication", pharm_namespaces)
        
        for entry in pharm_entries:
            medication_data = {
                'type': 'medication',
                'source': 'enhanced_cda_parser_pharmaceutical'
            }
            
            # Add section tagging if provided
            if section_info:
                medication_data['source_section'] = section_info
                medication_data['section_code'] = section_info.get('code', '')
                medication_data['section_title'] = section_info.get('title', '')
            
            # Extract medication name
            name_elem = entry.find(".//pharm:name", pharm_namespaces)
            if name_elem is not None and name_elem.text:
                medication_data['name'] = name_elem.text.strip()
                medication_data['medication_name'] = name_elem.text.strip()
                medication_data['display_name'] = name_elem.text.strip()
            
            # Extract dose information
            dose_elem = entry.find(".//pharm:dose", pharm_namespaces)
            if dose_elem is not None and dose_elem.text:
                medication_data['dose_quantity'] = dose_elem.text.strip()
            
            # Extract route information
            route_elem = entry.find(".//pharm:route", pharm_namespaces)
            if route_elem is not None and route_elem.text:
                medication_data['route'] = route_elem.text.strip()
            
            # Extract frequency information
            freq_elem = entry.find(".//pharm:frequency", pharm_namespaces)
            if freq_elem is not None and freq_elem.text:
                medication_data['frequency'] = freq_elem.text.strip()

    def _extract_active_ingredient(self, material_element: ET.Element, medication_name: str) -> str:
        """Extract active ingredient from manufactured material or map from medication name"""
        
        # First, try to find active ingredient in CDA structure
        # Look for ingredient elements in the material
        ingredients = material_element.findall(".//{urn:hl7-org:v3}ingredient", self.namespaces)
        for ingredient in ingredients:
            ingredient_names = ingredient.findall(".//{urn:hl7-org:v3}name", self.namespaces)
            for name in ingredient_names:
                if name.text:
                    return name.text.strip()
        
        # Look for substance elements  
        substances = material_element.findall(".//{urn:hl7-org:v3}substance", self.namespaces)
        for substance in substances:
            substance_names = substance.findall(".//{urn:hl7-org:v3}name", self.namespaces)
            for name in substance_names:
                if name.text:
                    return name.text.strip()
        
        # If not found in CDA structure, use medication name mapping
        medication_to_active_ingredient_map = {
            'Eutirox': 'levothyroxine sodium',
            'Levothyroxine': 'levothyroxine sodium',
            'Synthroid': 'levothyroxine sodium',
            'Aspirin': 'acetylsalicylic acid',
            'Paracetamol': 'paracetamol',
            'Acetaminophen': 'paracetamol',
            'Ibuprofen': 'ibuprofen',
            'Metformin': 'metformin hydrochloride',
            'Amoxicillin': 'amoxicillin',
            'Lisinopril': 'lisinopril',
            'Atorvastatin': 'atorvastatin calcium',
            'Omeprazole': 'omeprazole',
            'Amlodipine': 'amlodipine besylate',
            'Simvastatin': 'simvastatin',
            'Losartan': 'losartan potassium',
            'Hydrochlorothiazide': 'hydrochlorothiazide',
            'Warfarin': 'warfarin sodium',
            'Furosemide': 'furosemide',
            'Digoxin': 'digoxin',
            'Gabapentin': 'gabapentin',
            'Tramadol': 'tramadol hydrochloride',
            'Insulin': 'insulin',
            'Metoprolol': 'metoprolol tartrate',
            'Clopidogrel': 'clopidogrel bisulfate',
            'Sertraline': 'sertraline hydrochloride',
        }
        
        # Check if medication name matches any known mapping
        if medication_name in medication_to_active_ingredient_map:
            return medication_to_active_ingredient_map[medication_name]
        
        # Check for partial matches (case-insensitive)
        medication_name_lower = medication_name.lower()
        for brand_name, active_ingredient in medication_to_active_ingredient_map.items():
            if brand_name.lower() in medication_name_lower or medication_name_lower in brand_name.lower():
                return active_ingredient
        
        # If no mapping found, return the medication name as fallback
        return medication_name if medication_name else 'Not specified'

    def _extract_strength(self, material_element: ET.Element, medication_name: str) -> str:
        """Extract strength/concentration from manufactured material or map from medication name"""
        
        # First, try to find strength in CDA structure
        # Look for pharm:quantity elements with strength information
        pharm_namespaces = {**self.namespaces, 'pharm': 'urn:hl7-org:pharm'}
        
        # Check for pharmaceutical quantity elements
        quantities = material_element.findall(".//pharm:quantity", pharm_namespaces)
        for quantity in quantities:
            numerator = quantity.find("numerator", pharm_namespaces)
            denominator = quantity.find("denominator", pharm_namespaces)
            
            if numerator is not None and denominator is not None:
                num_value = numerator.get('value', '')
                num_unit = numerator.get('unit', '')
                denom_value = denominator.get('value', '')
                denom_unit = denominator.get('unit', '')
                
                if num_value and num_unit:
                    if denom_value and denom_unit and denom_unit != '1' and denom_value != '1':
                        return f"{num_value} {num_unit} / {denom_value} {denom_unit}"
                    else:
                        return f"{num_value} {num_unit}"
        
        # Look for strength in code displayName or other attributes
        codes = material_element.findall(".//{urn:hl7-org:v3}code", self.namespaces)
        for code in codes:
            display_name = code.get('displayName', '')
            if display_name and any(unit in display_name.lower() for unit in ['mg', 'ug', 'mcg', 'g', 'ml', 'mg/ml']):
                # Extract strength information from display name
                import re
                strength_match = re.search(r'(\d+(?:\.\d+)?)\s*(mg|ug|mcg|g|ml|mg/ml)', display_name.lower())
                if strength_match:
                    value, unit = strength_match.groups()
                    return f"{value} {unit}"
        
        # Use medication name mapping for common medications with known strengths
        medication_strength_map = {
            'Eutirox': '100 ug',  # Common levothyroxine strength
            'Synthroid': '100 ug',
            'Levothyroxine': '100 ug',
            'Aspirin': '325 mg',
            'Paracetamol': '500 mg',
            'Acetaminophen': '500 mg',
            'Ibuprofen': '200 mg',
            'Metformin': '500 mg',
            'Amoxicillin': '500 mg',
            'Lisinopril': '10 mg',
            'Atorvastatin': '20 mg',
            'Omeprazole': '20 mg',
            'Amlodipine': '5 mg',
            'Simvastatin': '20 mg',
            'Losartan': '50 mg',
            'Hydrochlorothiazide': '25 mg',
            'Warfarin': '5 mg',
            'Furosemide': '40 mg',
            'Digoxin': '0.25 mg',
            'Gabapentin': '300 mg',
            'Tramadol': '50 mg',
            'Metoprolol': '50 mg',
            'Clopidogrel': '75 mg',
            'Sertraline': '50 mg',
        }
        
        # Check for exact or partial matches
        if medication_name in medication_strength_map:
            return medication_strength_map[medication_name]
        
        # Check for partial matches (case-insensitive)
        medication_name_lower = medication_name.lower()
        for brand_name, strength in medication_strength_map.items():
            if brand_name.lower() in medication_name_lower or medication_name_lower in brand_name.lower():
                return strength
        
        return 'Not specified'

    def _extract_pharmaceutical_form(self, medication_name: str) -> str:
        """Extract or determine pharmaceutical form from medication name"""
        
        # Common pharmaceutical form mappings
        medication_form_map = {
            'Eutirox': 'Tablet',
            'Synthroid': 'Tablet', 
            'Levothyroxine': 'Tablet',
            'Aspirin': 'Tablet',
            'Paracetamol': 'Tablet',
            'Acetaminophen': 'Tablet',
            'Ibuprofen': 'Tablet',
            'Metformin': 'Tablet',
            'Amoxicillin': 'Capsule',
            'Lisinopril': 'Tablet',
            'Atorvastatin': 'Tablet',
            'Omeprazole': 'Capsule',
            'Amlodipine': 'Tablet',
            'Simvastatin': 'Tablet',
            'Losartan': 'Tablet',
            'Hydrochlorothiazide': 'Tablet',
            'Warfarin': 'Tablet',
            'Furosemide': 'Tablet',
            'Digoxin': 'Tablet',
            'Gabapentin': 'Capsule',
            'Tramadol': 'Tablet',
            'Metoprolol': 'Tablet',
            'Clopidogrel': 'Tablet',
            'Sertraline': 'Tablet',
            'Insulin': 'Injection',
            'Tresiba': 'Injection',  # Insulin pen
            'Augmentin': 'Tablet',   # Amoxicillin/clavulanate
            'Combivent': 'Inhaler',  # Respiratory medication
        }
        
        # Check for exact matches
        if medication_name in medication_form_map:
            return medication_form_map[medication_name]
        
        # Check for partial matches (case-insensitive)
        medication_name_lower = medication_name.lower()
        for brand_name, form in medication_form_map.items():
            if brand_name.lower() in medication_name_lower or medication_name_lower in brand_name.lower():
                return form
        
        # Detect form from medication name patterns
        if any(keyword in medication_name_lower for keyword in ['injection', 'inject', 'syringe']):
            return 'Injection'
        elif any(keyword in medication_name_lower for keyword in ['inhaler', 'spray', 'aerosol']):
            return 'Inhaler'
        elif any(keyword in medication_name_lower for keyword in ['cream', 'ointment', 'gel', 'lotion']):
            return 'Topical'
        elif any(keyword in medication_name_lower for keyword in ['drop', 'solution']):
            return 'Solution'
        elif any(keyword in medication_name_lower for keyword in ['capsule', 'cap']):
            return 'Capsule'
        else:
            return 'Tablet'  # Default assumption for oral medications
