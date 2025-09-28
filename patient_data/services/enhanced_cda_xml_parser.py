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
        self.namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:ihe:pharm:medication"}

        # Common EU namespace variations for better compatibility
        self.common_namespaces = {
            "hl7": "urn:hl7-org:v3",
            "cda": "urn:hl7-org:v3",
            "pharm": "urn:ihe:pharm:medication",
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

            # Extract basic document info
            patient_info = self._extract_patient_info(root)
            administrative_data = self._extract_administrative_data(root)

            # Extract clinical sections with coded data
            sections = self._extract_clinical_sections_with_codes(root)

            # Calculate summary statistics
            stats = self._calculate_section_statistics(sections)

            result = {
                "patient_identity": patient_info,
                "administrative_data": administrative_data,
                "sections": sections,
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

            # Apply enhanced extraction strategies
            entry_codes = []

            # Strategy 1: Extract all elements with codes (comprehensive)
            self._extract_coded_elements_systematic_enhanced(entry, entry_codes)

            # Strategy 2: Extract all text elements with references
            self._extract_text_elements_systematic(entry, entry_codes)

            # Strategy 3: Extract all time elements with context
            self._extract_time_elements_systematic(entry, entry_codes)

            # Strategy 4: Extract all status elements
            self._extract_status_elements_systematic(entry, entry_codes)

            # Strategy 5: Extract all value/quantity elements
            self._extract_value_elements_systematic(entry, entry_codes)

            # Strategy 6: Enhanced nested entry discovery for Italian L3 patterns
            self._extract_nested_entries_systematic(entry, entry_codes)

            # Strategy 7: Extract medication-specific codes (important for Italian L3)
            self._extract_medication_codes_systematic(entry, entry_codes)

            # Add discovered codes to main collection
            codes.extend(entry_codes)

        logger.info(
            f"[SUCCESS] Extracted {len(codes)} total coded elements (enhanced EU extraction)"
        )
        return ClinicalCodesCollection(codes=codes)

    def _extract_coded_elements_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract all elements that contain medical codes systematically"""

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

    def _extract_text_elements_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract text content with medical significance"""

        # Process originalText elements with references
        original_texts = entry.findall(".//cda:originalText", self.namespaces)
        for text_elem in original_texts:
            ref_elem = text_elem.find("cda:reference", self.namespaces)
            if ref_elem is not None:
                # Create text-based code entry for tracking
                ref_value = ref_elem.get("value", "").replace("#", "")
                if ref_value and text_elem.text:
                    # This helps track narrative references
                    pass  # Could create text-reference codes here

    def _extract_time_elements_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract time-related elements with clinical context"""

        # Process effectiveTime elements - these often have clinical significance
        effective_times = entry.findall(".//cda:effectiveTime", self.namespaces)
        for time_elem in effective_times:
            # Check if time has associated codes or context
            # Since ElementTree doesn't have getparent(), search parent context differently
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

    def _extract_status_elements_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract status-related elements"""

        # Status codes often indicate clinical state
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

    def _extract_value_elements_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract value/quantity elements with units and codes"""

        # Find all value elements
        for elem in entry.iter():
            if elem.tag.endswith("}value") or "value" in elem.tag.lower():
                # Check for coded values
                if elem.get("code") and elem.get("codeSystem"):
                    code = self._extract_clinical_code(elem)
                    if code:
                        codes.append(code)

                # Check for unit codes
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

    def _extract_coded_elements_systematic_enhanced(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Enhanced extraction for Italian L3 and EU member state compatibility"""

        # Original systematic extraction
        self._extract_coded_elements_systematic(entry, codes)

        # Enhanced: Search across all namespaces
        for ns_prefix in self.namespaces.keys():
            # Find code elements with alternative namespace prefixes
            code_elements = entry.findall(f".//{ns_prefix}:code", self.namespaces)
            for code_elem in code_elements:
                code = self._extract_clinical_code(code_elem)
                if code:
                    codes.append(code)

            # Find value elements with codes in alternative namespaces
            value_elements = entry.findall(
                f".//{ns_prefix}:value[@code]", self.namespaces
            )
            for value_elem in value_elements:
                code = self._extract_clinical_code(value_elem)
                if code:
                    codes.append(code)

    def _extract_nested_entries_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract codes from nested entry structures (Italian L3 pattern)"""

        # Find nested entryRelationship elements (common in Italian L3)
        nested_relations = entry.findall(".//cda:entryRelationship", self.namespaces)
        for relation in nested_relations:
            # Extract codes from nested observations/acts
            for child in relation:
                if child.tag.endswith("}observation") or child.tag.endswith("}act"):
                    # Recursively extract codes from nested elements
                    nested_codes = []
                    self._extract_coded_elements_systematic(child, nested_codes)
                    codes.extend(nested_codes)

        # Find component elements within entries (another Italian L3 pattern)
        components = entry.findall(".//cda:component", self.namespaces)
        for comp in components:
            comp_codes = []
            self._extract_coded_elements_systematic(comp, comp_codes)
            codes.extend(comp_codes)

    def _extract_medication_codes_systematic(
        self, entry: ET.Element, codes: List[ClinicalCode]
    ):
        """Extract medication-specific codes important for Italian L3 documents"""

        # Find manufacturedProduct elements (medication codes)
        products = entry.findall(".//cda:manufacturedProduct", self.namespaces)
        for product in products:
            product_codes = []
            self._extract_coded_elements_systematic(product, product_codes)
            codes.extend(product_codes)

        # Find substance administration codes
        substances = entry.findall(".//cda:substanceAdministration", self.namespaces)
        for substance in substances:
            substance_codes = []
            self._extract_coded_elements_systematic(substance, substance_codes)
            codes.extend(substance_codes)

        # Find pharmacy-specific elements
        pharm_elements = entry.findall(".//pharm:*", self.namespaces)
        for pharm_elem in pharm_elements:
            pharm_codes = []
            self._extract_coded_elements_systematic(pharm_elem, pharm_codes)
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

    def _extract_patient_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract comprehensive patient information with enhanced administrative data integration"""
        try:
            # Find patient role with proper namespace
            patient_role = root.find(
                ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
            )
            if patient_role is None:
                return self._create_default_patient_info()

            # Extract all patient ID elements with full details
            patient_id_elems = patient_role.findall("cda:id", self.namespaces)
            patient_id = "Unknown"
            patient_identifiers = []

            for patient_id_elem in patient_id_elems:
                extension = patient_id_elem.get("extension", "")
                authority = patient_id_elem.get("assigningAuthorityName", "")
                root_val = patient_id_elem.get("root", "")

                # Use first non-empty extension as primary patient_id
                if patient_id == "Unknown" and extension:
                    patient_id = extension

                # Create identifier object structure expected by template
                if extension:
                    identifier_obj = {
                        "extension": extension,
                        "assigningAuthorityName": authority,
                        "root": root_val,
                    }
                    patient_identifiers.append(identifier_obj)

            # Extract patient name
            patient = patient_role.find("{urn:hl7-org:v3}patient")
            if patient is not None:
                name = patient.find("{urn:hl7-org:v3}name")
                if name is not None:
                    given = name.find("{urn:hl7-org:v3}given")
                    family = name.find("{urn:hl7-org:v3}family")
                    given_name = given.text if given is not None else "Unknown"
                    family_name = family.text if family is not None else "Unknown"
                else:
                    given_name = family_name = "Unknown"
            else:
                given_name = family_name = "Unknown"

            # Extract birth date and gender
            birth_date = "Unknown"
            birth_date_raw = "Unknown"
            gender = "Unknown"
            if patient is not None:
                birth_elem = patient.find("{urn:hl7-org:v3}birthTime")
                if birth_elem is not None:
                    birth_date_raw = birth_elem.get("value", "Unknown")
                    # Format the birth date for consistent display
                    if default_formatter and birth_date_raw != "Unknown":
                        birth_date = default_formatter.format_patient_birth_date(
                            birth_date_raw
                        )
                    else:
                        birth_date = birth_date_raw

                gender_elem = patient.find("{urn:hl7-org:v3}administrativeGenderCode")
                if gender_elem is not None:
                    gender = gender_elem.get(
                        "displayName", gender_elem.get("code", "Unknown")
                    )

            # Extract enhanced contact information using administrative extractor if available
            patient_contact_data = DotDict()
            if self.admin_extractor:
                try:
                    # Extract patient contact info using enhanced extractor
                    admin_data = self.admin_extractor.extract_administrative_data(
                        ET.tostring(root, encoding="unicode")
                    )
                    if admin_data and admin_data.patient_contact_info:
                        contact_info = admin_data.patient_contact_info
                        patient_contact_data = DotDict(
                            {
                                "addresses": (
                                    contact_info.addresses
                                    if contact_info.addresses
                                    else []
                                ),
                                "telecoms": (
                                    contact_info.telecoms
                                    if contact_info.telecoms
                                    else []
                                ),
                                "has_enhanced_contact_data": True,
                            }
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to extract enhanced patient contact info: {str(e)}"
                    )
                    patient_contact_data = DotDict({"has_enhanced_contact_data": False})
            else:
                # Fallback to basic contact extraction
                addresses = self._extract_basic_patient_addresses(patient_role)
                telecoms = self._extract_basic_patient_telecoms(patient_role)
                patient_contact_data = DotDict(
                    {
                        "addresses": addresses,
                        "telecoms": telecoms,
                        "has_enhanced_contact_data": False,
                    }
                )

            logger.info(
                f"Extracted patient info: {given_name} {family_name}, ID: {patient_id}, Enhanced Contact: {patient_contact_data.get('has_enhanced_contact_data', False)}"
            )

            return {
                "patient_id": patient_id,
                "given_name": given_name,
                "family_name": family_name,
                "birth_date": birth_date,
                "birth_date_raw": birth_date_raw,  # Keep raw format for calculations
                "gender": gender,
                "patient_identifiers": patient_identifiers,
                "contact_info": patient_contact_data,
                "full_name": f"{given_name} {family_name}".strip(),
            }
        except Exception as e:
            logger.warning(f"Failed to extract patient info: {str(e)}")
            return self._create_default_patient_info()

    def _extract_administrative_data(self, root: ET.Element) -> Dict[str, Any]:
        """Extract comprehensive administrative data with enhanced contact information"""
        try:
            # Use enhanced extractor if available
            if self.admin_extractor:
                return self._extract_enhanced_administrative_data(root)
            else:
                # Fallback to basic extraction
                return self._extract_basic_administrative_data(root)
        except Exception as e:
            logger.warning(f"Failed to extract administrative data: {str(e)}")
            return self._create_default_administrative_data()

    def _extract_enhanced_administrative_data(self, root: ET.Element) -> Dict[str, Any]:
        """Extract administrative data using enhanced extractor"""
        # Use the enhanced administrative extractor to get comprehensive data
        admin_data = self.admin_extractor.extract_administrative_data(
            ET.tostring(root, encoding="unicode")
        )

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
                "organization": legal_auth_org,
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
                    "organization": primary_author.organization,
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

    def _extract_basic_administrative_data(self, root: ET.Element) -> Dict[str, Any]:
        """Basic administrative data extraction (fallback)"""

    def _extract_basic_administrative_data(self, root: ET.Element) -> Dict[str, Any]:
        """Basic administrative data extraction (fallback)"""
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

    def _create_default_administrative_data(self) -> Dict[str, Any]:
        """Create default administrative data structure"""
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

    def _extract_basic_patient_addresses(self, patient_role: ET.Element) -> List[Dict]:
        """Extract basic patient addresses as fallback"""
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

    def _extract_basic_patient_telecoms(self, patient_role: ET.Element) -> List[Dict]:
        """Extract basic patient telecoms as fallback"""
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
