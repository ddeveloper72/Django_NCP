"""
Enhanced CDA XML Parser with Clinical Coding Extraction
Extracts both narrative text and structured coded entries from HL7 CDA documents.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import logging
import re
from dataclasses import dataclass, field

# Import our date formatter for consistent date display
try:
    from patient_data.utils.date_formatter import default_formatter
except ImportError:
    # Fallback if date formatter not available during tests
    default_formatter = None

# Import enhanced administrative extractor
try:
    from patient_data.utils.administrative_extractor import (
        EnhancedAdministrativeExtractor,
    )
except ImportError:
    # Fallback if administrative extractor not available
    EnhancedAdministrativeExtractor = None

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
    """Enhanced parser for HL7 CDA XML with clinical coding extraction"""

    def __init__(self):
        self.namespaces = {"cda": "urn:hl7-org:v3", "pharm": "urn:ihe:pharm:medication"}
        # Initialize administrative extractor with date formatter
        if EnhancedAdministrativeExtractor:
            self.admin_extractor = EnhancedAdministrativeExtractor(default_formatter)
        else:
            self.admin_extractor = None

    def parse_cda_content(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse CDA XML content and extract clinical sections with coded data
        """
        try:
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
        """Extract clinical sections including structured coded entries"""
        sections = []

        # Find all section elements (using full namespace URI for default namespace)
        section_elements = root.findall(".//{urn:hl7-org:v3}section")

        for idx, section_elem in enumerate(section_elements):
            try:
                section = self._parse_single_section(section_elem, idx)
                if section:
                    sections.append(self._convert_section_to_dict(section))
            except Exception as e:
                logger.warning(f"Failed to parse section {idx}: {str(e)}")
                continue

        return sections

    def _parse_single_section(
        self, section_elem: ET.Element, idx: int
    ) -> Optional[ClinicalSection]:
        """Parse a single section element with its coded entries"""

        # Extract section code and title
        section_code_elem = section_elem.find("{urn:hl7-org:v3}code")
        section_code = None
        section_system = None
        if section_code_elem is not None:
            section_code = section_code_elem.get("code")
            section_system = section_code_elem.get(
                "codeSystemName", section_code_elem.get("codeSystem")
            )

        # Extract title
        title_elem = section_elem.find("{urn:hl7-org:v3}title")
        title = (
            title_elem.text.strip()
            if title_elem is not None and title_elem.text
            else f"Section {idx + 1}"
        )

        # Extract text content (narrative)
        text_elem = section_elem.find("{urn:hl7-org:v3}text")
        if text_elem is None:
            return None

        original_text = self._extract_text_content(text_elem)
        if not original_text.strip():
            return None

        # Extract template IDs
        template_ids = [
            tmpl.get("root", "")
            for tmpl in section_elem.findall("{urn:hl7-org:v3}templateId")
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
        """Extract clinical codes from entry elements in a section"""
        codes = []

        # Find all entry elements in this section
        entries = section_elem.findall("{urn:hl7-org:v3}entry")

        for entry in entries:
            # Enhanced search for coded elements to handle country variations
            coded_elements = []

            # Method 1: Find all elements with code attributes (current approach)
            for elem in entry.iter():
                if elem.get("code") and elem.get("codeSystem"):
                    coded_elements.append(elem)

            # Method 2: Look specifically for common CDA coded element patterns
            # This handles country-specific structural variations
            common_coded_patterns = [
                ".//observation/code",
                ".//observation/value[@code]",
                ".//act/code",
                ".//procedure/code",
                ".//substanceAdministration/code",
                ".//supply/code",
                ".//encounter/code",
                ".//participant/participantRole/code",
                ".//participant/participantRole/playingEntity/code",
                ".//entryRelationship/*/code",
                ".//entryRelationship/*/value[@code]",
            ]

            # Search with namespace for structured patterns
            for pattern in common_coded_patterns:
                # Convert pattern to use HL7 namespace
                ns_pattern = pattern.replace("//", "//{urn:hl7-org:v3}").replace(
                    "/", "/{urn:hl7-org:v3}"
                )
                pattern_elements = entry.findall(ns_pattern)
                for elem in pattern_elements:
                    if elem.get("code") and elem.get("codeSystem"):
                        if elem not in coded_elements:  # Avoid duplicates
                            coded_elements.append(elem)

            # Extract codes from all found elements
            for coded_elem in coded_elements:
                code = self._extract_clinical_code(coded_elem)
                if code:
                    codes.append(code)

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
        original_text_elem = elem.find("{urn:hl7-org:v3}originalText")
        if original_text_elem is not None:
            ref_elem = original_text_elem.find("{urn:hl7-org:v3}reference")
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

    def _map_code_system_to_name(self, code_system: str) -> str:
        """Map common code system OIDs to readable names for country variations"""
        system_mappings = {
            "2.16.840.1.113883.6.96": "SNOMED CT",
            "2.16.840.1.113883.6.1": "LOINC",
            "2.16.840.1.113883.6.73": "ATC",
            "2.16.840.1.113883.6.3": "ICD-10",
            "2.16.840.1.113883.6.42": "ICD-9",
            "2.16.840.1.113883.6.88": "RxNorm",
            "2.16.840.1.113883.5.25": "Confidentiality",
            "2.16.840.1.113883.5.1": "AdministrativeGender",
            "0.4.0.127.0.16.1.1.2.1": "EDQM",
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
        """Extract basic patient information with proper namespace handling"""
        try:
            # Find patient role with proper namespace
            patient_role = root.find(
                ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
            )
            if patient_role is None:
                return self._create_default_patient_info()

            # Extract all patient ID elements with full details
            patient_id_elems = patient_role.findall("{urn:hl7-org:v3}id")
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

            logger.info(
                f"Extracted patient info: {given_name} {family_name}, ID: {patient_id}"
            )

            return {
                "patient_id": patient_id,
                "given_name": given_name,
                "family_name": family_name,
                "birth_date": birth_date,
                "birth_date_raw": birth_date_raw,  # Keep raw format for calculations
                "gender": gender,
                "patient_identifiers": patient_identifiers,
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

        # Extract enhanced contact and organizational information
        patient_contact_info = self.admin_extractor.extract_patient_contact_info(root)
        author_information = self.admin_extractor.extract_author_information(root)
        custodian_info = self.admin_extractor.extract_custodian_information(root)
        legal_authenticator = self.admin_extractor.extract_legal_authenticator(root)

        # Get primary author for backward compatibility
        primary_author = (
            author_information[0]
            if author_information
            else {
                "person": {"family_name": None, "given_name": None, "full_name": None},
                "organization": {"name": None},
            }
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
            "custodian_name": custodian_info["organization"]["name"],
            # Enhanced contact and organizational information
            "patient_contact_info": patient_contact_info,
            "author_information": author_information,
            "custodian_organization": custodian_info["organization"],
            "legal_authenticator": legal_authenticator,
            # Backward compatibility fields
            "author_hcp": {
                "family_name": primary_author["person"]["family_name"],
                "given_name": primary_author["person"]["given_name"],
                "full_name": primary_author["person"]["full_name"],
                "organization": primary_author["organization"],
            },
            # Additional fields
            "document_last_update_date": None,
            "document_version_number": None,
            "preferred_hcp": {"name": None},
            "guardian": {"family_name": None},
            "other_contacts": [],
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
            "patient_contact_info": {"addresses": [], "telecoms": []},
            "author_hcp": {"family_name": None, "organization": {"name": None}},
            "legal_authenticator": {
                "family_name": None,
                "organization": {"name": None},
            },
            "custodian_organization": {"name": custodian_name},
            "preferred_hcp": {"name": None},
            "guardian": {"family_name": None},
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
            "patient_contact_info": {
                "addresses": [],
                "telecoms": [],
                "primary_address": None,
                "primary_phone": None,
                "primary_email": None,
            },
            "author_information": [],
            "custodian_organization": {
                "name": "Unknown",
                "id": None,
                "address": {},
                "telecoms": [],
            },
            "legal_authenticator": {
                "time": None,
                "person": {"family_name": None, "given_name": None, "full_name": None},
                "organization": {"name": None},
            },
            "author_hcp": {"family_name": None, "organization": {"name": None}},
            "preferred_hcp": {"name": None},
            "guardian": {"family_name": None},
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
        }

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
