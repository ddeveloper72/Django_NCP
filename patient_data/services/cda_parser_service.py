"""
CDA Document Parser and Patient Summary Generator
Extracts HL7 CDA Level 3 clinical documents and generates comprehensive patient summaries
"""

import xml.etree.ElementTree as ET
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

from translation_services.terminology_translator import TerminologyTranslator

logger = logging.getLogger(__name__)


@dataclass
class PatientSummarySection:
    """Data class for patient summary sections"""

    code: str
    title: str
    content: str
    entries: List[Dict[str, Any]]
    narrative_text: str = ""


class CDAParserService:
    """Service for parsing CDA documents and extracting patient summary data"""

    # HL7 CDA namespaces
    NAMESPACES = {
        "cda": "urn:hl7-org:v3",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "pharm": "urn:ihe:pharm:medication",
    }

    # HL7 Patient Summary section codes
    PS_SECTION_CODES = {
        "48765-2": "Allergies and Intolerances",
        "10160-0": "History of Medication Use",
        "11450-4": "Problem List",
        "30954-2": "Relevant Diagnostic Tests and Laboratory Data",
        "47519-4": "History of Procedures",
        "10157-6": "History of Family Member Diseases",
        "29762-2": "Social History",
        "11369-6": "History of Immunizations",
        "46240-8": "History of Encounters",
        "8716-3": "Vital Signs",
        "47420-5": "Functional Status",
        "42348-3": "Advance Directives",
        "10183-2": "Hospital Discharge Medications",
        "57852-6": "Problem Concern Act",
        "48767-8": "Annotation",
    }

    def __init__(self):
        self.document = None
        self.root = None

    def parse_cda_document(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse CDA document and extract all patient summary information

        Args:
            xml_content: Raw XML content of CDA document

        Returns:
            Dictionary containing parsed patient summary data
        """
        try:
            self.root = ET.fromstring(xml_content)

            # Extract document header information
            header_info = self._extract_document_header()

            # Extract patient information
            patient_info = self._extract_patient_info()

            # Extract all clinical sections
            clinical_sections = self._extract_clinical_sections()

            # Generate structured patient summary
            summary = {
                "document_info": header_info,
                "patient_info": patient_info,
                "clinical_sections": clinical_sections,
                "structured_body": self._extract_structured_body(),
                "generation_timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Successfully parsed CDA document with {len(clinical_sections)} sections"
            )
            return summary

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid CDA document: {e}")
        except Exception as e:
            logger.error(f"Error parsing CDA document: {e}")
            raise

    def _extract_document_header(self) -> Dict[str, Any]:
        """Extract document header information"""
        header = {}

        try:
            # Document ID
            id_elem = self.root.find(".//cda:id[@root]", self.NAMESPACES)
            if id_elem is not None:
                header["document_id"] = id_elem.get("root", "")
                header["extension"] = id_elem.get("extension", "")

            # Document title
            title_elem = self.root.find(".//cda:title", self.NAMESPACES)
            if title_elem is not None:
                header["title"] = title_elem.text or "Patient Summary"

            # Effective time
            time_elem = self.root.find(".//cda:effectiveTime[@value]", self.NAMESPACES)
            if time_elem is not None:
                header["effective_time"] = time_elem.get("value", "")
                header["formatted_time"] = self._format_hl7_datetime(
                    time_elem.get("value", "")
                )

            # Document type code
            code_elem = self.root.find(".//cda:code[@code]", self.NAMESPACES)
            if code_elem is not None:
                header["document_type_code"] = code_elem.get("code", "")
                header["code_system"] = code_elem.get("codeSystem", "")
                header["display_name"] = code_elem.get("displayName", "")

            # Author information
            header["authors"] = self._extract_authors()

            # Custodian organization
            header["custodian"] = self._extract_custodian()

        except Exception as e:
            logger.warning(f"Error extracting document header: {e}")

        return header

    def _extract_patient_info(self) -> Dict[str, Any]:
        """Extract comprehensive patient information"""
        patient = {}

        try:
            # Patient role
            patient_role = self.root.find(".//cda:patientRole", self.NAMESPACES)
            if patient_role is None:
                return patient

            # Patient IDs
            patient["identifiers"] = []
            for id_elem in patient_role.findall(".//cda:id", self.NAMESPACES):
                identifier = {
                    "root": id_elem.get("root", ""),
                    "extension": id_elem.get("extension", ""),
                    "assigningAuthorityName": id_elem.get("assigningAuthorityName", ""),
                }
                patient["identifiers"].append(identifier)

            # Patient demographics
            patient_elem = patient_role.find(".//cda:patient", self.NAMESPACES)
            if patient_elem is not None:
                # Names
                patient["names"] = []
                for name_elem in patient_elem.findall(".//cda:name", self.NAMESPACES):
                    name = self._extract_name(name_elem)
                    if name:
                        patient["names"].append(name)

                # Birth time
                birth_elem = patient_elem.find(
                    ".//cda:birthTime[@value]", self.NAMESPACES
                )
                if birth_elem is not None:
                    patient["birth_time"] = birth_elem.get("value", "")
                    patient["formatted_birth_date"] = self._format_hl7_datetime(
                        birth_elem.get("value", "")
                    )

                # Administrative gender
                gender_elem = patient_elem.find(
                    ".//cda:administrativeGenderCode[@code]", self.NAMESPACES
                )
                if gender_elem is not None:
                    patient["gender_code"] = gender_elem.get("code", "")
                    patient["gender_display"] = self._format_gender(
                        gender_elem.get("code", "")
                    )

                # Marital status
                marital_elem = patient_elem.find(
                    ".//cda:maritalStatusCode[@code]", self.NAMESPACES
                )
                if marital_elem is not None:
                    patient["marital_status"] = {
                        "code": marital_elem.get("code", ""),
                        "display": marital_elem.get("displayName", ""),
                    }

                # Race and ethnicity
                race_elem = patient_elem.find(".//cda:raceCode[@code]", self.NAMESPACES)
                if race_elem is not None:
                    patient["race"] = {
                        "code": race_elem.get("code", ""),
                        "display": race_elem.get("displayName", ""),
                    }

                ethnic_elem = patient_elem.find(
                    ".//cda:ethnicGroupCode[@code]", self.NAMESPACES
                )
                if ethnic_elem is not None:
                    patient["ethnicity"] = {
                        "code": ethnic_elem.get("code", ""),
                        "display": ethnic_elem.get("displayName", ""),
                    }

                # Language communication
                patient["languages"] = []
                for lang_elem in patient_elem.findall(
                    ".//cda:languageCommunication", self.NAMESPACES
                ):
                    lang_code = lang_elem.find(
                        ".//cda:languageCode[@code]", self.NAMESPACES
                    )
                    if lang_code is not None:
                        language = {
                            "code": lang_code.get("code", ""),
                            "mode": self._extract_language_mode(lang_elem),
                        }
                        patient["languages"].append(language)

            # Addresses
            patient["addresses"] = []
            for addr_elem in patient_role.findall(".//cda:addr", self.NAMESPACES):
                address = self._extract_address(addr_elem)
                if address:
                    patient["addresses"].append(address)

            # Telecom (phone, email)
            patient["telecoms"] = []
            for telecom_elem in patient_role.findall(".//cda:telecom", self.NAMESPACES):
                telecom = self._extract_telecom(telecom_elem)
                if telecom:
                    patient["telecoms"].append(telecom)

            # Provider organization
            org_elem = patient_role.find(".//cda:providerOrganization", self.NAMESPACES)
            if org_elem is not None:
                patient["provider_organization"] = self._extract_organization(org_elem)

        except Exception as e:
            logger.warning(f"Error extracting patient info: {e}")

        return patient

    def _extract_clinical_sections(self) -> List[PatientSummarySection]:
        """Extract all clinical sections from structured body"""
        sections = []

        try:
            # Find all sections in structured body
            for section_elem in self.root.findall(
                ".//cda:structuredBody//cda:section", self.NAMESPACES
            ):
                section = self._parse_clinical_section(section_elem)
                if section:
                    sections.append(section)

        except Exception as e:
            logger.warning(f"Error extracting clinical sections: {e}")

        return sections

    def _parse_clinical_section(self, section_elem) -> Optional[PatientSummarySection]:
        """Parse individual clinical section"""
        try:
            # Get section code
            code_elem = section_elem.find(".//cda:code[@code]", self.NAMESPACES)
            if code_elem is None:
                return None

            section_code = code_elem.get("code", "")
            code_system = code_elem.get("codeSystem", "")
            display_name = code_elem.get("displayName", "")

            # Get section title
            title_elem = section_elem.find(".//cda:title", self.NAMESPACES)
            title = title_elem.text if title_elem is not None else display_name

            # Get narrative text
            text_elem = section_elem.find(".//cda:text", self.NAMESPACES)
            narrative_text = (
                self._extract_narrative_text(text_elem) if text_elem is not None else ""
            )

            # Extract structured entries
            entries = []
            for entry_elem in section_elem.findall(".//cda:entry", self.NAMESPACES):
                entry = self._parse_section_entry(entry_elem)
                if entry:
                    entries.append(entry)

            return PatientSummarySection(
                code=section_code,
                title=title
                or self.PS_SECTION_CODES.get(section_code, f"Section {section_code}"),
                content=narrative_text,
                entries=entries,
                narrative_text=narrative_text,
            )

        except Exception as e:
            logger.warning(f"Error parsing clinical section: {e}")
            return None

    def _parse_section_entry(self, entry_elem) -> Optional[Dict[str, Any]]:
        """Parse individual section entry (observation, procedure, etc.)"""
        try:
            entry = {}

            # Get entry type (observation, procedure, supply, etc.)
            for child in entry_elem:
                if child.tag.endswith("}observation"):
                    entry.update(self._parse_observation(child))
                elif child.tag.endswith("}procedure"):
                    entry.update(self._parse_procedure(child))
                elif child.tag.endswith("}supply"):
                    entry.update(self._parse_supply(child))
                elif child.tag.endswith("}act"):
                    entry.update(self._parse_act(child))
                elif child.tag.endswith("}encounter"):
                    entry.update(self._parse_encounter(child))
                elif child.tag.endswith("}substanceAdministration"):
                    entry.update(self._parse_substance_administration(child))

            return entry if entry else None

        except Exception as e:
            logger.warning(f"Error parsing section entry: {e}")
            return None

    def _parse_observation(self, obs_elem) -> Dict[str, Any]:
        """Parse observation entry"""
        observation = {"type": "observation"}

        try:
            # Class code
            observation["class_code"] = obs_elem.get("classCode", "")
            observation["mood_code"] = obs_elem.get("moodCode", "")

            # ID
            id_elem = obs_elem.find(".//cda:id", self.NAMESPACES)
            if id_elem is not None:
                observation["id"] = {
                    "root": id_elem.get("root", ""),
                    "extension": id_elem.get("extension", ""),
                }

            # Code (what was observed)
            code_elem = obs_elem.find(".//cda:code", self.NAMESPACES)
            if code_elem is not None:
                observation["code"] = {
                    "code": code_elem.get("code", ""),
                    "codeSystem": code_elem.get("codeSystem", ""),
                    "displayName": code_elem.get("displayName", ""),
                    "codeSystemName": code_elem.get("codeSystemName", ""),
                }

            # Status
            status_elem = obs_elem.find(".//cda:statusCode", self.NAMESPACES)
            if status_elem is not None:
                observation["status"] = status_elem.get("code", "")

            # Effective time
            time_elem = obs_elem.find(".//cda:effectiveTime", self.NAMESPACES)
            if time_elem is not None:
                observation["effective_time"] = self._extract_effective_time(time_elem)

            # Value
            value_elem = obs_elem.find(".//cda:value", self.NAMESPACES)
            if value_elem is not None:
                observation["value"] = self._extract_value(value_elem)

            # Interpretation
            interp_elem = obs_elem.find(".//cda:interpretationCode", self.NAMESPACES)
            if interp_elem is not None:
                observation["interpretation"] = {
                    "code": interp_elem.get("code", ""),
                    "displayName": interp_elem.get("displayName", ""),
                }

            # Reference ranges
            observation["reference_ranges"] = []
            for ref_elem in obs_elem.findall(".//cda:referenceRange", self.NAMESPACES):
                ref_range = self._extract_reference_range(ref_elem)
                if ref_range:
                    observation["reference_ranges"].append(ref_range)

        except Exception as e:
            logger.warning(f"Error parsing observation: {e}")

        return observation

    def _extract_structured_body(self) -> Dict[str, Any]:
        """Extract structured body with organized sections"""
        structured_body = {
            "allergies": [],
            "medications": [],
            "problems": [],
            "procedures": [],
            "vital_signs": [],
            "laboratory_results": [],
            "immunizations": [],
            "social_history": [],
            "functional_status": [],
            "advance_directives": [],
        }

        try:
            # Map section codes to categories
            section_mapping = {
                "48765-2": "allergies",  # Allergies and Intolerances
                "10160-0": "medications",  # History of Medication Use
                "11450-4": "problems",  # Problem List
                "30954-2": "laboratory_results",  # Relevant Diagnostic Tests
                "47519-4": "procedures",  # History of Procedures
                "11369-6": "immunizations",  # History of Immunizations
                "29762-2": "social_history",  # Social History
                "8716-3": "vital_signs",  # Vital Signs
                "47420-5": "functional_status",  # Functional Status
                "42348-3": "advance_directives",  # Advance Directives
            }

            for section_elem in self.root.findall(
                ".//cda:structuredBody//cda:section", self.NAMESPACES
            ):
                code_elem = section_elem.find(".//cda:code[@code]", self.NAMESPACES)
                if code_elem is not None:
                    section_code = code_elem.get("code", "")
                    category = section_mapping.get(section_code)

                    if category:
                        # Extract entries for this category
                        for entry_elem in section_elem.findall(
                            ".//cda:entry", self.NAMESPACES
                        ):
                            entry = self._parse_section_entry(entry_elem)
                            if entry:
                                structured_body[category].append(entry)

        except Exception as e:
            logger.warning(f"Error extracting structured body: {e}")

        return structured_body

    # Helper methods for parsing specific elements

    def _extract_name(self, name_elem) -> Dict[str, str]:
        """Extract name components"""
        name = {}
        try:
            name["use"] = name_elem.get("use", "")

            # Given names
            given_names = []
            for given_elem in name_elem.findall(".//cda:given", self.NAMESPACES):
                if given_elem.text:
                    given_names.append(given_elem.text)
            name["given"] = given_names

            # Family name
            family_elem = name_elem.find(".//cda:family", self.NAMESPACES)
            if family_elem is not None and family_elem.text:
                name["family"] = family_elem.text

            # Prefix
            prefix_elem = name_elem.find(".//cda:prefix", self.NAMESPACES)
            if prefix_elem is not None and prefix_elem.text:
                name["prefix"] = prefix_elem.text

            # Suffix
            suffix_elem = name_elem.find(".//cda:suffix", self.NAMESPACES)
            if suffix_elem is not None and suffix_elem.text:
                name["suffix"] = suffix_elem.text

        except Exception as e:
            logger.warning(f"Error extracting name: {e}")

        return name

    def _extract_address(self, addr_elem) -> Dict[str, str]:
        """Extract address components"""
        address = {}
        try:
            address["use"] = addr_elem.get("use", "")

            # Street address lines
            street_lines = []
            for line_elem in addr_elem.findall(
                ".//cda:streetAddressLine", self.NAMESPACES
            ):
                if line_elem.text:
                    street_lines.append(line_elem.text)
            address["streetAddressLine"] = street_lines

            # City
            city_elem = addr_elem.find(".//cda:city", self.NAMESPACES)
            if city_elem is not None and city_elem.text:
                address["city"] = city_elem.text

            # State
            state_elem = addr_elem.find(".//cda:state", self.NAMESPACES)
            if state_elem is not None and state_elem.text:
                address["state"] = state_elem.text

            # Postal code
            postal_elem = addr_elem.find(".//cda:postalCode", self.NAMESPACES)
            if postal_elem is not None and postal_elem.text:
                address["postalCode"] = postal_elem.text

            # Country
            country_elem = addr_elem.find(".//cda:country", self.NAMESPACES)
            if country_elem is not None and country_elem.text:
                address["country"] = country_elem.text

        except Exception as e:
            logger.warning(f"Error extracting address: {e}")

        return address

    def _extract_telecom(self, telecom_elem) -> Dict[str, str]:
        """Extract telecom information"""
        telecom = {}
        try:
            telecom["value"] = telecom_elem.get("value", "")
            telecom["use"] = telecom_elem.get("use", "")

            # Parse value to determine type
            value = telecom["value"]
            if value.startswith("tel:"):
                telecom["type"] = "phone"
                telecom["number"] = value.replace("tel:", "")
            elif value.startswith("mailto:"):
                telecom["type"] = "email"
                telecom["email"] = value.replace("mailto:", "")
            elif value.startswith("http"):
                telecom["type"] = "url"
                telecom["url"] = value
            else:
                telecom["type"] = "other"

        except Exception as e:
            logger.warning(f"Error extracting telecom: {e}")

        return telecom

    def _format_hl7_datetime(self, hl7_datetime: str) -> str:
        """Format HL7 datetime string to readable format with timezone support"""
        try:
            if not hl7_datetime or len(hl7_datetime) < 8:
                return hl7_datetime

            # Handle timezone-aware format: YYYYMMDDHHMMSS+ZZZZ or YYYYMMDD+ZZZZ
            timezone_info = ""
            core_datetime = hl7_datetime

            # Extract timezone if present (+ZZZZ or -ZZZZ)
            if "+" in hl7_datetime or (
                hl7_datetime.count("-") > 2
            ):  # More than 2 hyphens indicates timezone
                # Find timezone offset
                for i, char in enumerate(hl7_datetime):
                    if char in ["+", "-"] and i >= 8:  # Timezone starts after date
                        core_datetime = hl7_datetime[:i]
                        timezone_info = hl7_datetime[i:]
                        break

            # Parse core datetime
            if len(core_datetime) >= 8:
                year = core_datetime[:4]
                month = core_datetime[4:6]
                day = core_datetime[6:8]

                # Format date
                formatted_date = f"{year}-{month}-{day}"

                if len(core_datetime) >= 14:
                    # Include time (YYYYMMDDHHMMSS format)
                    hour = core_datetime[8:10]
                    minute = core_datetime[10:12]
                    second = core_datetime[12:14]
                    formatted_time = f"{hour}:{minute}:{second}"

                    # Combine date, time, and timezone
                    if timezone_info:
                        # Format timezone for better readability
                        if timezone_info == "+0000":
                            tz_display = " (UTC)"
                        elif timezone_info.startswith("+"):
                            tz_display = f" (UTC{timezone_info})"
                        elif timezone_info.startswith("-"):
                            tz_display = f" (UTC{timezone_info})"
                        else:
                            tz_display = f" ({timezone_info})"

                        return f"{formatted_date} {formatted_time}{tz_display}"
                    else:
                        return f"{formatted_date} {formatted_time}"
                else:
                    # Date only, but might have timezone
                    if timezone_info:
                        if timezone_info == "+0000":
                            tz_display = " (UTC)"
                        else:
                            tz_display = f" ({timezone_info})"
                        return f"{formatted_date}{tz_display}"
                    else:
                        return formatted_date

            return hl7_datetime
        except Exception as e:
            logger.warning(f"Error formatting HL7 datetime '{hl7_datetime}': {e}")
            return hl7_datetime

    def _format_gender(self, gender_code: str) -> str:
        """Format gender code to readable text"""
        gender_map = {
            "M": "Male",
            "F": "Female",
            "UN": "Undifferentiated",
            "UNK": "Unknown",
        }
        return gender_map.get(gender_code, gender_code)

    def _extract_narrative_text(self, text_elem) -> str:
        """Extract narrative text content"""
        try:
            # Handle various text formats
            if text_elem.text:
                return text_elem.text.strip()

            # Handle formatted text with paragraphs, lists, etc.
            text_parts = []
            for elem in text_elem.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())

            return " ".join(filter(None, text_parts))
        except:
            return ""

    def generate_patient_summary_html(self, parsed_data: Dict[str, Any]) -> str:
        """Generate HTML patient summary from parsed CDA data"""

        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Patient Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
                .header {{ background: #f4f4f4; padding: 20px; border-left: 5px solid #007bff; }}
                .patient-info {{ background: #f9f9f9; padding: 15px; margin: 20px 0; }}
                .section {{ margin: 20px 0; border: 1px solid #ddd; }}
                .section-header {{ background: #e9ecef; padding: 10px; font-weight: bold; }}
                .section-content {{ padding: 15px; }}
                .entry {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 3px solid #007bff; }}
                .code {{ font-family: monospace; background: #e9ecef; padding: 2px 4px; }}
                .date {{ color: #666; font-style: italic; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Patient Summary</h1>
                <p><strong>Document:</strong> {document_title}</p>
                <p><strong>Generated:</strong> {generation_date}</p>
                <p><strong>Document ID:</strong> {document_id}</p>
            </div>
            
            <div class="patient-info">
                <h2>Patient Information</h2>
                {patient_info_html}
            </div>
            
            <div class="clinical-sections">
                <h2>Clinical Information</h2>
                {sections_html}
            </div>
        </body>
        </html>
        """

        # Generate patient info HTML
        patient_info_html = self._generate_patient_info_html(
            parsed_data.get("patient_info", {})
        )

        # Generate sections HTML
        sections_html = self._generate_sections_html(
            parsed_data.get("clinical_sections", [])
        )

        # Fill template
        return html_template.format(
            document_title=parsed_data.get("document_info", {}).get(
                "title", "Patient Summary"
            ),
            generation_date=parsed_data.get("generation_timestamp", ""),
            document_id=parsed_data.get("document_info", {}).get("document_id", ""),
            patient_info_html=patient_info_html,
            sections_html=sections_html,
        )

    def _generate_patient_info_html(self, patient_info: Dict[str, Any]) -> str:
        """Generate HTML for patient information section"""
        html = "<table>"

        # Names
        if patient_info.get("names"):
            for name in patient_info["names"]:
                given_names = " ".join(name.get("given", []))
                family_name = name.get("family", "")
                full_name = f"{given_names} {family_name}".strip()
                if full_name:
                    html += (
                        f"<tr><td><strong>Name</strong></td><td>{full_name}</td></tr>"
                    )

        # Birth date
        if patient_info.get("formatted_birth_date"):
            html += f"<tr><td><strong>Birth Date</strong></td><td>{patient_info['formatted_birth_date']}</td></tr>"

        # Gender
        if patient_info.get("gender_display"):
            html += f"<tr><td><strong>Gender</strong></td><td>{patient_info['gender_display']}</td></tr>"

        # Identifiers
        if patient_info.get("identifiers"):
            for idx, identifier in enumerate(patient_info["identifiers"]):
                id_label = (
                    f"Patient ID {idx + 1}"
                    if len(patient_info["identifiers"]) > 1
                    else "Patient ID"
                )
                id_value = identifier.get("extension", identifier.get("root", ""))
                if id_value:
                    html += f"<tr><td><strong>{id_label}</strong></td><td>{id_value}</td></tr>"

        # Addresses
        if patient_info.get("addresses"):
            for idx, address in enumerate(patient_info["addresses"]):
                addr_parts = []
                if address.get("streetAddressLine"):
                    addr_parts.extend(address["streetAddressLine"])
                if address.get("city"):
                    addr_parts.append(address["city"])
                if address.get("state"):
                    addr_parts.append(address["state"])
                if address.get("postalCode"):
                    addr_parts.append(address["postalCode"])
                if address.get("country"):
                    addr_parts.append(address["country"])

                if addr_parts:
                    addr_label = (
                        f"Address {idx + 1}"
                        if len(patient_info["addresses"]) > 1
                        else "Address"
                    )
                    html += f"<tr><td><strong>{addr_label}</strong></td><td>{', '.join(addr_parts)}</td></tr>"

        # Telecoms
        if patient_info.get("telecoms"):
            for telecom in patient_info["telecoms"]:
                if telecom.get("type") == "phone" and telecom.get("number"):
                    html += f"<tr><td><strong>Phone</strong></td><td>{telecom['number']}</td></tr>"
                elif telecom.get("type") == "email" and telecom.get("email"):
                    html += f"<tr><td><strong>Email</strong></td><td>{telecom['email']}</td></tr>"

        html += "</table>"
        return html

    def _generate_sections_html(self, sections: List[PatientSummarySection]) -> str:
        """Generate HTML for clinical sections"""
        html = ""

        for section in sections:
            html += f"""
            <div class="section">
                <div class="section-header">
                    {section.title} <span class="code">({section.code})</span>
                </div>
                <div class="section-content">
            """

            # Add narrative text if available
            if section.narrative_text:
                html += f"<p>{section.narrative_text}</p>"

            # Add structured entries
            if section.entries:
                html += "<div class='entries'>"
                for entry in section.entries:
                    html += self._generate_entry_html(entry)
                html += "</div>"

            html += "</div></div>"

        return html

    def _generate_entry_html(self, entry: Dict[str, Any]) -> str:
        """Generate HTML for individual entry"""
        html = "<div class='entry'>"

        # Entry type
        entry_type = entry.get("type", "Unknown")
        html += f"<strong>Type:</strong> {entry_type.title()}<br>"

        # Code information
        if entry.get("code"):
            code_info = entry["code"]
            display_name = code_info.get("displayName", code_info.get("code", ""))
            code_value = code_info.get("code", "")
            if display_name:
                html += f"<strong>Code:</strong> {display_name}"
                if code_value:
                    html += f" <span class='code'>({code_value})</span>"
                html += "<br>"

        # Value
        if entry.get("value"):
            value_info = entry["value"]
            if isinstance(value_info, dict):
                if value_info.get("displayName"):
                    html += f"<strong>Value:</strong> {value_info['displayName']}<br>"
                elif value_info.get("value"):
                    html += f"<strong>Value:</strong> {value_info['value']}"
                    if value_info.get("unit"):
                        html += f" {value_info['unit']}"
                    html += "<br>"
            else:
                html += f"<strong>Value:</strong> {value_info}<br>"

        # Effective time
        if entry.get("effective_time"):
            time_info = entry["effective_time"]
            if isinstance(time_info, dict) and time_info.get("formatted"):
                html += f"<strong>Date:</strong> <span class='date'>{time_info['formatted']}</span><br>"
            elif isinstance(time_info, str):
                html += (
                    f"<strong>Date:</strong> <span class='date'>{time_info}</span><br>"
                )

        # Status
        if entry.get("status"):
            html += f"<strong>Status:</strong> {entry['status']}<br>"

        # Interpretation
        if entry.get("interpretation"):
            interp = entry["interpretation"]
            display = interp.get("displayName", interp.get("code", ""))
            if display:
                html += f"<strong>Interpretation:</strong> {display}<br>"

        html += "</div>"
        return html

    # Additional helper methods for parsing different entry types

    def _parse_procedure(self, proc_elem) -> Dict[str, Any]:
        """Parse procedure entry"""
        procedure = {"type": "procedure"}

        try:
            procedure["class_code"] = proc_elem.get("classCode", "")
            procedure["mood_code"] = proc_elem.get("moodCode", "")

            # Code
            code_elem = proc_elem.find(".//cda:code", self.NAMESPACES)
            if code_elem is not None:
                procedure["code"] = {
                    "code": code_elem.get("code", ""),
                    "codeSystem": code_elem.get("codeSystem", ""),
                    "displayName": code_elem.get("displayName", ""),
                }

            # Effective time
            time_elem = proc_elem.find(".//cda:effectiveTime", self.NAMESPACES)
            if time_elem is not None:
                procedure["effective_time"] = self._extract_effective_time(time_elem)

            # Target site
            site_elem = proc_elem.find(".//cda:targetSiteCode", self.NAMESPACES)
            if site_elem is not None:
                procedure["target_site"] = {
                    "code": site_elem.get("code", ""),
                    "displayName": site_elem.get("displayName", ""),
                }

        except Exception as e:
            logger.warning(f"Error parsing procedure: {e}")

        return procedure

    def _parse_substance_administration(self, subst_elem) -> Dict[str, Any]:
        """Parse substance administration (medication) entry"""
        medication = {"type": "medication"}

        try:
            medication["class_code"] = subst_elem.get("classCode", "")
            medication["mood_code"] = subst_elem.get("moodCode", "")

            # Effective time (dosing schedule) - capture ALL effectiveTime elements
            time_elems = subst_elem.findall(".//cda:effectiveTime", self.NAMESPACES)
            if time_elems:
                effective_times = []
                for time_elem in time_elems:
                    time_info = self._extract_effective_time(time_elem)
                    
                    # Also check for event elements (like ACM) in EIVL_TS time types
                    event_elem = time_elem.find(".//cda:event", self.NAMESPACES)
                    if event_elem is not None:
                        time_info["event"] = {
                            "code": event_elem.get("code", ""),
                            "code_system": event_elem.get("codeSystem", ""),
                            "display_name": event_elem.get("displayName", "")
                        }
                    
                    effective_times.append(time_info)
                
                medication["effective_time"] = effective_times[0] if len(effective_times) == 1 else effective_times
                
                # Extract event codes for frequency/schedule resolution
                for time_info in effective_times:
                    if "event" in time_info:
                        event_data = time_info["event"]
                        medication["event_code"] = event_data["code"]
                        medication["event_code_system"] = event_data["code_system"]
                        medication["event_display_name"] = event_data["display_name"]
                        break  # Use first event found

            # Dose quantity - Enhanced extraction for complex structures
            dose_elem = subst_elem.find(".//cda:doseQuantity", self.NAMESPACES)
            if dose_elem is not None:
                # Check for simple value/unit structure first
                simple_value = dose_elem.get("value", "")
                simple_unit = dose_elem.get("unit", "")
                
                if simple_value or simple_unit:
                    # Simple structure
                    medication["dose"] = {
                        "value": simple_value,
                        "unit": simple_unit,
                    }
                    medication["doseQuantity"] = {
                        "value": simple_value,
                        "unit": simple_unit,
                    }
                else:
                    # Check for complex low/high structure
                    low_elem = dose_elem.find(".//cda:low", self.NAMESPACES)
                    high_elem = dose_elem.find(".//cda:high", self.NAMESPACES)
                    
                    if low_elem is not None or high_elem is not None:
                        dose_quantity = {}
                        
                        if low_elem is not None:
                            dose_quantity["low"] = {
                                "value": low_elem.get("value", ""),
                                "unit": low_elem.get("unit", "")
                            }
                        
                        if high_elem is not None:
                            dose_quantity["high"] = {
                                "value": high_elem.get("value", ""),
                                "unit": high_elem.get("unit", "")
                            }
                        
                        medication["doseQuantity"] = dose_quantity
                        
                        # Also set simple dose for backward compatibility
                        if low_elem is not None:
                            medication["dose"] = {
                                "value": low_elem.get("value", ""),
                                "unit": low_elem.get("unit", ""),
                            }
                        else:
                            medication["dose"] = {"value": "", "unit": ""}
                        
                        logger.info(f"Extracted complex doseQuantity: {dose_quantity}")
                    else:
                        # No dose quantity found
                        medication["dose"] = {"value": "", "unit": ""}
            else:
                medication["dose"] = {"value": "", "unit": ""}

            # Route of administration
            route_elem = subst_elem.find(".//cda:routeCode", self.NAMESPACES)
            if route_elem is not None:
                route_code = route_elem.get("code", "")
                route_display = route_elem.get("displayName", "")
                
                # Try to resolve route code using CTS if displayName is empty
                if route_code and not route_display:
                    try:
                        translator = TerminologyTranslator()
                        resolved_display = translator.resolve_code(route_code)
                        if resolved_display:
                            route_display = resolved_display
                    except Exception as e:
                        logger.warning(f"Failed to resolve route code {route_code} via CTS: {e}")
                
                medication["route"] = {
                    "code": route_code,
                    "displayName": route_display,
                }
                
                # Add resolved display for template compatibility (for both expected paths)
                if route_display:
                    medication["route_display"] = route_display
                    # Also add to data structure for template
                    if "data" not in medication:
                        medication["data"] = {}
                    medication["data"]["route_display"] = route_display
                    if route_code:
                        medication["data"]["route_code"] = route_code

            # Consumable (medication information)
            consumable_elem = subst_elem.find(".//cda:consumable", self.NAMESPACES)
            if consumable_elem is not None:
                medication["medication"] = self._parse_medication_info(consumable_elem)
                
                # Also store raw consumable structure for enhanced processing
                medication["consumable"] = self._extract_consumable_structure(consumable_elem)

        except Exception as e:
            logger.warning(f"Error parsing substance administration: {e}")

        return medication

    def _parse_medication_info(self, consumable_elem) -> Dict[str, Any]:
        """Parse medication information from consumable element"""
        med_info = {}

        try:
            # Manufactured product
            product_elem = consumable_elem.find(
                ".//cda:manufacturedProduct", self.NAMESPACES
            )
            if product_elem is not None:
                material_elem = product_elem.find(
                    ".//cda:manufacturedMaterial", self.NAMESPACES
                )
                if material_elem is not None:
                    # Medication code
                    code_elem = material_elem.find(".//cda:code", self.NAMESPACES)
                    if code_elem is not None:
                        med_info["code"] = {
                            "code": code_elem.get("code", ""),
                            "codeSystem": code_elem.get("codeSystem", ""),
                            "displayName": code_elem.get("displayName", ""),
                        }

                    # Medication name
                    name_elem = material_elem.find(".//cda:name", self.NAMESPACES)
                    if name_elem is not None and name_elem.text:
                        med_info["name"] = name_elem.text
                    
                    # Pharmaceutical form (formCode) - ENHANCED EXTRACTION
                    form_elem = material_elem.find(".//pharm:formCode", self.NAMESPACES)
                    if form_elem is not None:
                        form_code = form_elem.get("code", "")
                        form_code_system = form_elem.get("codeSystem", "")
                        form_display = form_elem.get("displayName", "")
                        
                        # Try to resolve form code using CTS if displayName is empty
                        if form_code and not form_display:
                            try:
                                translator = TerminologyTranslator()
                                # Pass both code AND codeSystem to CTS for proper resolution
                                resolved_display = translator.resolve_code(form_code, form_code_system)
                                if resolved_display:
                                    form_display = resolved_display
                                    logger.info(f"CTS resolved pharmaceutical form code {form_code} (system: {form_code_system}) to '{form_display}'")
                            except Exception as e:
                                logger.warning(f"Failed to resolve pharmaceutical form code {form_code} via CTS: {e}")
                        
                        med_info["formCode"] = {
                            "code": form_code,
                            "codeSystem": form_code_system,
                            "displayName": form_display,
                        }
                        
                        # Also add for easy access
                        med_info["pharmaceutical_form_code"] = form_code
                        med_info["pharmaceutical_form_code_system"] = form_code_system
                        if form_display:
                            med_info["pharmaceutical_form"] = form_display
                        
                        logger.info(f"Extracted pharmaceutical form: {form_code} - {form_display}")
                    
                    # Also check for alternative form code paths
                    alt_form_elem = material_elem.find(".//cda:formCode", self.NAMESPACES)
                    if alt_form_elem is not None and "formCode" not in med_info:
                        form_code = alt_form_elem.get("code", "")
                        form_display = alt_form_elem.get("displayName", "")
                        
                        if form_code and not form_display:
                            try:
                                translator = TerminologyTranslator()
                                resolved_display = translator.resolve_code(form_code)
                                if resolved_display:
                                    form_display = resolved_display
                                    logger.info(f"CTS resolved alt pharmaceutical form code {form_code} to '{form_display}'")
                            except Exception as e:
                                logger.warning(f"Failed to resolve alt pharmaceutical form code {form_code} via CTS: {e}")
                        
                        med_info["formCode"] = {
                            "code": form_code,
                            "codeSystem": alt_form_elem.get("codeSystem", ""),
                            "displayName": form_display,
                        }
                        med_info["pharmaceutical_form_code"] = form_code
                        if form_display:
                            med_info["pharmaceutical_form"] = form_display

                # Manufacturer
                org_elem = product_elem.find(
                    ".//cda:manufacturerOrganization", self.NAMESPACES
                )
                if org_elem is not None:
                    med_info["manufacturer"] = self._extract_organization(org_elem)

        except Exception as e:
            logger.warning(f"Error parsing medication info: {e}")

        return med_info
    
    def _extract_consumable_structure(self, consumable_elem) -> Dict[str, Any]:
        """Extract complete consumable structure for enhanced processing"""
        consumable_data = {}
        
        try:
            # Manufactured product
            product_elem = consumable_elem.find(".//cda:manufacturedProduct", self.NAMESPACES)
            if product_elem is not None:
                manufactured_product = {}
                
                # Manufactured material
                material_elem = product_elem.find(".//cda:manufacturedMaterial", self.NAMESPACES)
                if material_elem is not None:
                    manufactured_material = {}
                    
                    # Name
                    name_elem = material_elem.find(".//cda:name", self.NAMESPACES)
                    if name_elem is not None and name_elem.text:
                        manufactured_material["name"] = name_elem.text
                    
                    # Form code
                    form_elem = material_elem.find(".//pharm:formCode", self.NAMESPACES)
                    if form_elem is not None:
                        manufactured_material["form_code"] = form_elem.get("code", "")
                        manufactured_material["form_display"] = form_elem.get("displayName", "")
                        manufactured_material["form_system"] = form_elem.get("codeSystem", "")
                    
                    # Alternative form code path
                    alt_form_elem = material_elem.find(".//cda:formCode", self.NAMESPACES)
                    if alt_form_elem is not None and "form_code" not in manufactured_material:
                        manufactured_material["form_code"] = alt_form_elem.get("code", "")
                        manufactured_material["form_display"] = alt_form_elem.get("displayName", "")
                        manufactured_material["form_system"] = alt_form_elem.get("codeSystem", "")
                    
                    # Ingredient information
                    ingredient_elem = material_elem.find(".//pharm:ingredient", self.NAMESPACES)
                    if ingredient_elem is not None:
                        ingredient_data = {}
                        
                        # Ingredient substance
                        substance_elem = ingredient_elem.find(".//pharm:ingredientSubstance", self.NAMESPACES)
                        if substance_elem is not None:
                            ingredient_substance = {}
                            
                            # Code
                            code_elem = substance_elem.find(".//pharm:code", self.NAMESPACES)
                            if code_elem is not None:
                                ingredient_substance["code"] = code_elem.get("code", "")
                                ingredient_substance["display"] = code_elem.get("displayName", "")
                                ingredient_substance["system"] = code_elem.get("codeSystem", "")
                            
                            ingredient_data["ingredient_substance"] = ingredient_substance
                        
                        # Quantity (strength)
                        quantity_elem = ingredient_elem.find(".//pharm:quantity", self.NAMESPACES)
                        if quantity_elem is not None:
                            quantity_data = {}
                            
                            # Numerator
                            num_elem = quantity_elem.find(".//pharm:numerator", self.NAMESPACES)
                            if num_elem is not None:
                                quantity_data["numerator"] = {
                                    "value": num_elem.get("value", ""),
                                    "unit": num_elem.get("unit", "")
                                }
                            
                            # Denominator
                            denom_elem = quantity_elem.find(".//pharm:denominator", self.NAMESPACES)
                            if denom_elem is not None:
                                quantity_data["denominator"] = {
                                    "value": denom_elem.get("value", ""),
                                    "unit": denom_elem.get("unit", "")
                                }
                            
                            ingredient_data["quantity"] = quantity_data
                        
                        manufactured_material["ingredient"] = ingredient_data
                    
                    manufactured_product["manufactured_material"] = manufactured_material
                
                consumable_data["manufactured_product"] = manufactured_product
        
        except Exception as e:
            logger.warning(f"Error extracting consumable structure: {e}")
        
        return consumable_data

    def _parse_supply(self, supply_elem) -> Dict[str, Any]:
        """Parse supply entry"""
        supply = {"type": "supply"}

        try:
            supply["class_code"] = supply_elem.get("classCode", "")
            supply["mood_code"] = supply_elem.get("moodCode", "")

            # Code
            code_elem = supply_elem.find(".//cda:code", self.NAMESPACES)
            if code_elem is not None:
                supply["code"] = {
                    "code": code_elem.get("code", ""),
                    "displayName": code_elem.get("displayName", ""),
                }

            # Quantity
            qty_elem = supply_elem.find(".//cda:quantity", self.NAMESPACES)
            if qty_elem is not None:
                supply["quantity"] = {
                    "value": qty_elem.get("value", ""),
                    "unit": qty_elem.get("unit", ""),
                }

        except Exception as e:
            logger.warning(f"Error parsing supply: {e}")

        return supply

    def _parse_act(self, act_elem) -> Dict[str, Any]:
        """Parse act entry"""
        act = {"type": "act"}

        try:
            act["class_code"] = act_elem.get("classCode", "")
            act["mood_code"] = act_elem.get("moodCode", "")

            # Code
            code_elem = act_elem.find(".//cda:code", self.NAMESPACES)
            if code_elem is not None:
                act["code"] = {
                    "code": code_elem.get("code", ""),
                    "displayName": code_elem.get("displayName", ""),
                }

            # Effective time
            time_elem = act_elem.find(".//cda:effectiveTime", self.NAMESPACES)
            if time_elem is not None:
                act["effective_time"] = self._extract_effective_time(time_elem)

        except Exception as e:
            logger.warning(f"Error parsing act: {e}")

        return act

    def _parse_encounter(self, enc_elem) -> Dict[str, Any]:
        """Parse encounter entry"""
        encounter = {"type": "encounter"}

        try:
            encounter["class_code"] = enc_elem.get("classCode", "")
            encounter["mood_code"] = enc_elem.get("moodCode", "")

            # Code
            code_elem = enc_elem.find(".//cda:code", self.NAMESPACES)
            if code_elem is not None:
                encounter["code"] = {
                    "code": code_elem.get("code", ""),
                    "displayName": code_elem.get("displayName", ""),
                }

            # Effective time
            time_elem = enc_elem.find(".//cda:effectiveTime", self.NAMESPACES)
            if time_elem is not None:
                encounter["effective_time"] = self._extract_effective_time(time_elem)

        except Exception as e:
            logger.warning(f"Error parsing encounter: {e}")

        return encounter

    def _extract_effective_time(self, time_elem) -> Dict[str, Any]:
        """Extract effective time information"""
        time_info = {}

        try:
            # Single time value
            if time_elem.get("value"):
                time_info["value"] = time_elem.get("value")
                time_info["formatted"] = self._format_hl7_datetime(
                    time_elem.get("value")
                )

            # Time interval (low/high)
            low_elem = time_elem.find(".//cda:low", self.NAMESPACES)
            high_elem = time_elem.find(".//cda:high", self.NAMESPACES)

            if low_elem is not None:
                time_info["low"] = low_elem.get("value", "")
                time_info["low_formatted"] = self._format_hl7_datetime(
                    low_elem.get("value", "")
                )

            if high_elem is not None:
                time_info["high"] = high_elem.get("value", "")
                time_info["high_formatted"] = self._format_hl7_datetime(
                    high_elem.get("value", "")
                )

            # Periodic interval
            period_elem = time_elem.find(".//cda:period", self.NAMESPACES)
            if period_elem is not None:
                time_info["period"] = {
                    "value": period_elem.get("value", ""),
                    "unit": period_elem.get("unit", ""),
                }

        except Exception as e:
            logger.warning(f"Error extracting effective time: {e}")

        return time_info

    def _extract_value(self, value_elem) -> Dict[str, Any]:
        """Extract value information"""
        value_info = {}

        try:
            # Physical quantity
            if value_elem.get("value") and value_elem.get("unit"):
                value_info["value"] = value_elem.get("value")
                value_info["unit"] = value_elem.get("unit")
                value_info["type"] = "quantity"

            # Coded value
            elif value_elem.get("code"):
                value_info["code"] = value_elem.get("code")
                value_info["codeSystem"] = value_elem.get("codeSystem", "")
                value_info["displayName"] = value_elem.get("displayName", "")
                value_info["type"] = "coded"

            # String value
            elif value_elem.text:
                value_info["value"] = value_elem.text
                value_info["type"] = "string"

            # Boolean value
            elif value_elem.get("value") in ["true", "false"]:
                value_info["value"] = value_elem.get("value") == "true"
                value_info["type"] = "boolean"

        except Exception as e:
            logger.warning(f"Error extracting value: {e}")

        return value_info

    def _extract_reference_range(self, ref_elem) -> Dict[str, Any]:
        """Extract reference range information"""
        ref_range = {}

        try:
            obs_range = ref_elem.find(".//cda:observationRange", self.NAMESPACES)
            if obs_range is not None:
                # Low value
                low_elem = obs_range.find(".//cda:value/cda:low", self.NAMESPACES)
                if low_elem is not None:
                    ref_range["low"] = {
                        "value": low_elem.get("value", ""),
                        "unit": low_elem.get("unit", ""),
                    }

                # High value
                high_elem = obs_range.find(".//cda:value/cda:high", self.NAMESPACES)
                if high_elem is not None:
                    ref_range["high"] = {
                        "value": high_elem.get("value", ""),
                        "unit": high_elem.get("unit", ""),
                    }

        except Exception as e:
            logger.warning(f"Error extracting reference range: {e}")

        return ref_range

    def _extract_authors(self) -> List[Dict[str, Any]]:
        """Extract document authors"""
        authors = []

        try:
            for author_elem in self.root.findall(".//cda:author", self.NAMESPACES):
                author = {}

                # Time
                time_elem = author_elem.find(".//cda:time", self.NAMESPACES)
                if time_elem is not None:
                    author["time"] = time_elem.get("value", "")

                # Assigned author
                assigned_elem = author_elem.find(
                    ".//cda:assignedAuthor", self.NAMESPACES
                )
                if assigned_elem is not None:
                    # ID
                    id_elem = assigned_elem.find(".//cda:id", self.NAMESPACES)
                    if id_elem is not None:
                        author["id"] = {
                            "root": id_elem.get("root", ""),
                            "extension": id_elem.get("extension", ""),
                        }

                    # Person
                    person_elem = assigned_elem.find(
                        ".//cda:assignedPerson", self.NAMESPACES
                    )
                    if person_elem is not None:
                        name_elem = person_elem.find(".//cda:name", self.NAMESPACES)
                        if name_elem is not None:
                            author["person"] = self._extract_name(name_elem)

                    # Organization
                    org_elem = assigned_elem.find(
                        ".//cda:representedOrganization", self.NAMESPACES
                    )
                    if org_elem is not None:
                        author["organization"] = self._extract_organization(org_elem)

                if author:
                    authors.append(author)

        except Exception as e:
            logger.warning(f"Error extracting authors: {e}")

        return authors

    def _extract_custodian(self) -> Dict[str, Any]:
        """Extract custodian organization"""
        custodian = {}

        try:
            custodian_elem = self.root.find(".//cda:custodian", self.NAMESPACES)
            if custodian_elem is not None:
                org_elem = custodian_elem.find(
                    ".//cda:assignedCustodian/cda:representedCustodianOrganization",
                    self.NAMESPACES,
                )
                if org_elem is not None:
                    custodian = self._extract_organization(org_elem)

        except Exception as e:
            logger.warning(f"Error extracting custodian: {e}")

        return custodian

    def _extract_organization(self, org_elem) -> Dict[str, Any]:
        """Extract organization information"""
        organization = {}

        try:
            # ID
            id_elem = org_elem.find(".//cda:id", self.NAMESPACES)
            if id_elem is not None:
                organization["id"] = {
                    "root": id_elem.get("root", ""),
                    "extension": id_elem.get("extension", ""),
                }

            # Name
            name_elem = org_elem.find(".//cda:name", self.NAMESPACES)
            if name_elem is not None and name_elem.text:
                organization["name"] = name_elem.text

            # Telecom
            organization["telecoms"] = []
            for telecom_elem in org_elem.findall(".//cda:telecom", self.NAMESPACES):
                telecom = self._extract_telecom(telecom_elem)
                if telecom:
                    organization["telecoms"].append(telecom)

            # Address
            organization["addresses"] = []
            for addr_elem in org_elem.findall(".//cda:addr", self.NAMESPACES):
                address = self._extract_address(addr_elem)
                if address:
                    organization["addresses"].append(address)

        except Exception as e:
            logger.warning(f"Error extracting organization: {e}")

        return organization

    def _extract_language_mode(self, lang_elem) -> List[str]:
        """Extract language communication modes"""
        modes = []

        try:
            for mode_elem in lang_elem.findall(".//cda:modeCode", self.NAMESPACES):
                mode_code = mode_elem.get("code", "")
                if mode_code:
                    modes.append(mode_code)

        except Exception as e:
            logger.warning(f"Error extracting language mode: {e}")

        return modes
