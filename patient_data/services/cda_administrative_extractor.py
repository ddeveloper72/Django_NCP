"""
CDA Administrative Information Extractor
Extracts comprehensive administrative data from European L1/L3 CDA documents
including contact information, healthcare providers, legal authenticators, etc.
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Represents contact information (address, telecom)"""

    addresses: List[Dict] = None
    telecoms: List[Dict] = None

    def __post_init__(self):
        if self.addresses is None:
            self.addresses = []
        if self.telecoms is None:
            self.telecoms = []


@dataclass
class OrganizationInfo:
    """Represents organization information"""

    name: str = ""
    addresses: List[Dict] = None
    telecoms: List[Dict] = None
    identifiers: List[Dict] = None
    organization_type: str = ""

    def __post_init__(self):
        if self.addresses is None:
            self.addresses = []
        if self.telecoms is None:
            self.telecoms = []
        if self.identifiers is None:
            self.identifiers = []


@dataclass
@dataclass
class PersonInfo:
    """Represents person information (HCP, legal authenticator, etc.)"""

    family_name: str = ""
    given_name: str = ""
    title: str = ""
    role: str = ""
    relationship: str = ""  # Guardian/contact relationship type
    specialty: str = ""
    organization: OrganizationInfo = None
    contact_info: ContactInfo = None

    def __post_init__(self):
        if self.organization is None:
            self.organization = OrganizationInfo()
        if self.contact_info is None:
            self.contact_info = ContactInfo()


@dataclass
class AdministrativeData:
    """Complete administrative data extracted from CDA"""

    patient_contact_info: ContactInfo = None
    author_hcp: PersonInfo = None
    legal_authenticator: PersonInfo = None
    custodian_organization: OrganizationInfo = None
    guardian: PersonInfo = None
    other_contacts: List[PersonInfo] = None
    preferred_hcp: OrganizationInfo = None  # Cabinet Medicale
    patient_languages: List[str] = None  # Language communication preferences

    # Document metadata
    document_creation_date: str = ""
    document_last_update_date: str = ""
    document_version_number: str = ""
    document_set_id: str = ""

    def __post_init__(self):
        if self.patient_contact_info is None:
            self.patient_contact_info = ContactInfo()
        if self.author_hcp is None:
            self.author_hcp = PersonInfo()
        if self.legal_authenticator is None:
            self.legal_authenticator = PersonInfo()
        if self.custodian_organization is None:
            self.custodian_organization = OrganizationInfo()
        if self.guardian is None:
            self.guardian = PersonInfo()
        if self.other_contacts is None:
            self.other_contacts = []
        if self.preferred_hcp is None:
            self.preferred_hcp = OrganizationInfo()
        if self.patient_languages is None:
            self.patient_languages = []


class CDAAdministrativeExtractor:
    """Extracts administrative information from European CDA documents"""

    def __init__(self):
        """Initialize the administrative data extractor"""
        self.namespaces = {
            "hl7": "urn:hl7-org:v3",
            "": "urn:hl7-org:v3",  # Default namespace
        }

    def extract_administrative_data(self, cda_content: str) -> AdministrativeData:
        """
        Extract comprehensive administrative data from CDA XML content

        Args:
            cda_content: Raw CDA XML content

        Returns:
            AdministrativeData object containing all extracted information
        """
        try:
            # Parse XML content
            if cda_content.strip().startswith("<"):
                # XML format
                root = ET.fromstring(cda_content)

                # Detect source country to optimize parsing strategy
                source_country = self._detect_source_country(root)

                return self._extract_from_xml(root, source_country)
            else:
                # HTML format - try to extract what we can
                return self._extract_from_html(cda_content)

        except Exception as e:
            print(f"Error extracting administrative data: {e}")
            return AdministrativeData()

    def _detect_source_country(self, root: ET.Element) -> str:
        """
        Detect the source country of the CDA document to optimize parsing

        Returns:
            Country code (e.g., 'IE', 'PT', 'LU') or 'UNKNOWN'
        """
        try:
            # Check language code first
            language_code = root.get("languageCode")
            if language_code:
                country_mapping = {
                    "en-IE": "IE",
                    "pt-PT": "PT",
                    "fr-LU": "LU",
                    "de-LU": "LU",
                    "en-GB": "GB",
                    "fr-FR": "FR",
                    "de-DE": "DE",
                    "it-IT": "IT",
                    "es-ES": "ES",
                }
                if language_code in country_mapping:
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
                    return "IE"
                elif "portugal" in custodian_name or "portuguese" in custodian_name:
                    return "PT"
                elif (
                    "luxembourg" in custodian_name or "luxembourgish" in custodian_name
                ):
                    return "LU"

            # Check address country codes
            patient_country = root.find(
                ".//recordTarget/patientRole/addr/country", self.namespaces
            )
            if patient_country is not None and patient_country.text:
                return patient_country.text.upper()

            return "UNKNOWN"

        except Exception as e:
            print(f"Error detecting source country: {e}")
            return "UNKNOWN"

    def _extract_from_xml(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> AdministrativeData:
        """
        Extract administrative data from CDA XML with country-specific optimizations

        Args:
            root: XML root element
            source_country: Detected source country code
        """
        admin_data = AdministrativeData()

        # Extract document metadata first
        admin_data.document_creation_date = self._extract_document_creation_date(root)
        admin_data.document_last_update_date = self._extract_document_last_update_date(
            root
        )
        admin_data.document_version_number = self._extract_document_version_number(root)
        admin_data.document_set_id = self._extract_document_set_id(root)

        # Extract patient contact information with country-specific handling
        admin_data.patient_contact_info = self._extract_patient_contact_info(
            root, source_country
        )

        # Extract patient language communication preferences
        admin_data.patient_languages = self._extract_patient_languages(root)

        # Extract author (HCP) information
        admin_data.author_hcp = self._extract_author_info(root, source_country)

        # Extract legal authenticator
        admin_data.legal_authenticator = self._extract_legal_authenticator(
            root, source_country
        )

        # Extract custodian organization
        admin_data.custodian_organization = self._extract_custodian_info(
            root, source_country
        )

        # Extract guardian information
        admin_data.guardian = self._extract_guardian_info(root, source_country)

        # Extract preferred HCP organization (Cabinet Medicale)
        admin_data.preferred_hcp = self._extract_preferred_hcp(root, source_country)

        # Extract other contacts
        admin_data.other_contacts = self._extract_other_contacts(root, source_country)

        # Extract participant information (emergency contacts, next of kin, dependencies)
        participants = self._extract_participants(root)
        admin_data.other_contacts.extend(participants)

        return admin_data

    def _extract_patient_contact_info(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> ContactInfo:
        """
        Extract patient contact information with country-specific optimizations

        Args:
            root: XML root element
            source_country: Source country code for optimized parsing

        Note: Patient and guardian may legitimately share the same contact information
        (e.g., parent and child, spouse and patient living together). This is not
        considered duplication but valid shared contact data.
        """
        contact_info = ContactInfo()

        # Look for patient role section
        patient_role = root.find(".//recordTarget/patientRole", self.namespaces)
        if patient_role is not None:
            # Extract addresses - only direct children, not guardian addresses
            addresses = patient_role.findall("addr", self.namespaces)
            for addr in addresses:
                address_info = self._parse_address(addr, source_country)
                if address_info:
                    contact_info.addresses.append(address_info)

            # Extract telecom information - only direct children, not guardian telecoms
            telecoms = patient_role.findall("telecom", self.namespaces)
            for telecom in telecoms:
                telecom_info = self._parse_telecom(telecom, source_country)
                if telecom_info:
                    contact_info.telecoms.append(telecom_info)

        return contact_info

    def _extract_patient_languages(self, root: ET.Element) -> List[str]:
        """Extract patient language communication preferences"""
        languages = []

        # Look for language communication in patient section
        lang_elements = root.findall(
            ".//recordTarget/patientRole/patient/languageCommunication/languageCode",
            self.namespaces,
        )

        for lang_elem in lang_elements:
            lang_code = lang_elem.get("code")
            if lang_code:
                languages.append(lang_code)

        return languages

    def _extract_author_info(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> PersonInfo:
        """Extract author (Healthcare Professional) information"""
        person_info = PersonInfo()
        person_info.role = "Author (HCP)"

        # Look for author section
        author = root.find(".//author", self.namespaces)
        if author is not None:
            # Extract person name
            person_name = author.find(".//assignedPerson/name", self.namespaces)
            if person_name is not None:
                person_info.family_name = self._get_name_part(person_name, "family")
                person_info.given_name = self._get_name_part(person_name, "given")
                person_info.title = self._get_name_part(person_name, "prefix")
            else:
                # Check for authoring device (system author instead of person)
                device = author.find(".//assignedAuthoringDevice", self.namespaces)
                if device is not None:
                    software_name = device.find("softwareName", self.namespaces)
                    if software_name is not None and software_name.text:
                        # Use software name as author identifier
                        person_info.family_name = "System"
                        person_info.given_name = software_name.text.strip()
                        person_info.role = "Authoring System"

            # Extract organization
            org = author.find(".//representedOrganization", self.namespaces)
            if org is not None:
                person_info.organization = self._extract_organization_info(
                    org, source_country
                )

            # Extract contact information
            assigned_author = author.find(".//assignedAuthor", self.namespaces)
            if assigned_author is not None:
                person_info.contact_info = self._extract_contact_from_element(
                    assigned_author, source_country
                )

        return person_info

    def _extract_legal_authenticator(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> PersonInfo:
        """Extract legal authenticator information"""
        person_info = PersonInfo()
        person_info.role = "Legal Authenticator"

        # Look for legal authenticator section
        auth = root.find(".//legalAuthenticator", self.namespaces)
        if auth is not None:
            # Extract person name
            person_name = auth.find(".//assignedPerson/name", self.namespaces)
            if person_name is not None:
                person_info.family_name = self._get_name_part(person_name, "family")
                person_info.given_name = self._get_name_part(person_name, "given")
                person_info.title = self._get_name_part(person_name, "prefix")

            # Extract organization
            org = auth.find(".//representedOrganization", self.namespaces)
            if org is not None:
                person_info.organization = self._extract_organization_info(
                    org, source_country
                )

            # Extract contact information
            assigned_entity = auth.find(".//assignedEntity", self.namespaces)
            if assigned_entity is not None:
                person_info.contact_info = self._extract_contact_from_element(
                    assigned_entity, source_country
                )

        return person_info

    def _extract_custodian_info(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> OrganizationInfo:
        """Extract custodian organization information"""
        org_info = OrganizationInfo()
        org_info.organization_type = "Custodian"

        # Look for custodian section
        custodian = root.find(
            ".//custodian/assignedCustodian/representedCustodianOrganization",
            self.namespaces,
        )
        if custodian is not None:
            org_info = self._extract_organization_info(custodian, source_country)
            org_info.organization_type = "Custodian"

        return org_info

    def _extract_guardian_info(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> PersonInfo:
        """
        Extract guardian information

        Note: Guardian contact information may be identical to patient contact
        information in valid scenarios (e.g., parent and minor child, spouse
        caregivers). Both sets of data should be preserved and displayed
        separately to maintain clinical context and relationship clarity.
        """
        person_info = PersonInfo()
        person_info.role = "Guardian"

        # Look for guardian section
        guardian = root.find(".//guardian", self.namespaces)
        if guardian is not None:
            # Extract person name
            person_name = guardian.find(".//guardianPerson/name", self.namespaces)
            if person_name is not None:
                person_info.family_name = self._get_name_part(person_name, "family")
                person_info.given_name = self._get_name_part(person_name, "given")

            # Extract contact information
            person_info.contact_info = self._extract_contact_from_element(
                guardian, source_country
            )

        return person_info

    def _extract_preferred_hcp(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> OrganizationInfo:
        """Extract preferred healthcare provider (Cabinet Medicale) information"""
        org_info = OrganizationInfo()
        org_info.organization_type = "Preferred HCP Organization"

        # Look for participant with type code PPRF (primary performer)
        participants = root.findall('.//participant[@typeCode="PPRF"]', self.namespaces)
        for participant in participants:
            org = participant.find(".//scopingOrganization", self.namespaces)
            if org is not None:
                org_info = self._extract_organization_info(org, source_country)
                org_info.organization_type = "Cabinet Medicale"
                break

        return org_info

    def _extract_other_contacts(
        self, root: ET.Element, source_country: str = "UNKNOWN"
    ) -> List[PersonInfo]:
        """Extract other contact information"""
        contacts = []

        # Look for informants, participants, etc.
        informants = root.findall(".//informant", self.namespaces)
        for informant in informants:
            person_info = PersonInfo()
            person_info.role = "Informant"

            # Extract person name
            person_name = informant.find(".//assignedPerson/name", self.namespaces)
            if person_name is not None:
                person_info.family_name = self._get_name_part(person_name, "family")
                person_info.given_name = self._get_name_part(person_name, "given")

                # Extract contact information
                assigned_entity = informant.find(".//assignedEntity", self.namespaces)
                if assigned_entity is not None:
                    person_info.contact_info = self._extract_contact_from_element(
                        assigned_entity, source_country
                    )

                contacts.append(person_info)

        return contacts

    def _extract_organization_info(
        self, org_element: ET.Element, source_country: str = "UNKNOWN"
    ) -> OrganizationInfo:
        """Extract organization information from XML element"""
        org_info = OrganizationInfo()

        # Extract organization name
        name_elem = org_element.find(".//name", self.namespaces)
        if name_elem is not None and name_elem.text:
            org_info.name = name_elem.text.strip()

        # Extract organization identifiers
        id_elements = org_element.findall(".//id", self.namespaces)
        for id_elem in id_elements:
            identifier = self._parse_identifier(id_elem)
            if identifier:
                org_info.identifiers.append(identifier)

        # Extract contact information
        contact_info = self._extract_contact_from_element(org_element, source_country)
        org_info.addresses = contact_info.addresses
        org_info.telecoms = contact_info.telecoms

        return org_info

    def _extract_contact_from_element(
        self, element: ET.Element, source_country: str = "UNKNOWN"
    ) -> ContactInfo:
        """Extract contact information from any XML element"""
        contact_info = ContactInfo()

        # Extract addresses
        addresses = element.findall(".//addr", self.namespaces)
        for addr in addresses:
            address_info = self._parse_address(addr, source_country)
            if address_info:
                contact_info.addresses.append(address_info)

        # Extract telecom information
        telecoms = element.findall(".//telecom", self.namespaces)
        for telecom in telecoms:
            telecom_info = self._parse_telecom(telecom, source_country)
            if telecom_info:
                contact_info.telecoms.append(telecom_info)

        return contact_info

    def _parse_address(
        self, addr_element: ET.Element, source_country: str = "UNKNOWN"
    ) -> Optional[Dict]:
        """
        Parse address information from XML element with country-specific optimizations

        Args:
            addr_element: XML address element
            source_country: Source country code for optimized parsing
        """
        address = {}

        # Extract address components - handle both streetAddressLine and individual components
        street_lines = []
        
        # Method 1: Extract streetAddressLine elements
        street_addrs = addr_element.findall(".//streetAddressLine", self.namespaces)
        for street in street_addrs:
            if street.text and street.text.strip():
                street_lines.append(street.text.strip())

        # Method 2: If no streetAddressLine, try individual street components
        if not street_lines:
            # Try alternative street element names
            for street_tag in ["street", "streetName", "houseNumber"]:
                street_elem = addr_element.find(f".//{street_tag}", self.namespaces)
                if street_elem is not None and street_elem.text and street_elem.text.strip():
                    street_lines.append(street_elem.text.strip())

        if street_lines:
            address["street_lines"] = street_lines
            address["street"] = ", ".join(street_lines)  # Keep for backward compatibility

        # Extract city
        city_elem = addr_element.find(".//city", self.namespaces)
        if city_elem is not None and city_elem.text:
            address["city"] = city_elem.text.strip()

        # Extract postal code (handle country-specific formats)
        postal_elem = addr_element.find(".//postalCode", self.namespaces)
        if postal_elem is not None and postal_elem.text:
            postal_code = postal_elem.text.strip()

            # Country-specific postal code validation/formatting
            if source_country == "IE":
                # Irish Eircode format (e.g., D02 XY45, W91 XP83)
                postal_code = postal_code.upper()
            elif source_country == "PT":
                # Portuguese format (e.g., 1250-141)
                pass  # Use as-is
            elif source_country == "LU":
                # Luxembourg format (e.g., 9160)
                pass  # Use as-is

            address["postal_code"] = postal_code
            address["postalCode"] = postal_code  # Keep for backward compatibility

        # Extract state/county (particularly important for Ireland)
        state_elem = addr_element.find(".//state", self.namespaces)
        if state_elem is not None and state_elem.text:
            address["state"] = state_elem.text.strip()

        # Extract country
        country_elem = addr_element.find(".//country", self.namespaces)
        if country_elem is not None and country_elem.text:
            address["country"] = country_elem.text.strip()

        # Extract use code
        use_attr = addr_element.get("use")
        if use_attr:
            address["use"] = use_attr

        # Return None if address is effectively empty (only has use attribute)
        essential_fields = ["street", "city", "postalCode", "state", "country"]
        if not any(address.get(field) for field in essential_fields):
            return None

        return address

    def _parse_telecom(
        self, telecom_element: ET.Element, source_country: str = "UNKNOWN"
    ) -> Optional[Dict]:
        """
        Parse telecom information from XML element with country-specific optimizations

        Args:
            telecom_element: XML telecom element
            source_country: Source country code for optimized parsing
        """
        telecom = {}

        # Extract value
        value_attr = telecom_element.get("value")
        if value_attr:
            # Validate telecom value - filter out invalid/empty telecoms
            if self._is_invalid_telecom(value_attr):
                return None
                
            telecom["value"] = value_attr

            # Country-specific telecom formatting and validation
            if source_country == "IE" and "tel:" in value_attr:
                # Irish phone number format (+353)
                phone_num = value_attr.replace("tel:", "")
                if not phone_num.startswith("+353") and phone_num.startswith("353"):
                    phone_num = "+" + phone_num
                telecom["value"] = f"tel:{phone_num}"
            elif source_country == "PT" and "tel:" in value_attr:
                # Portuguese phone number format (+351)
                phone_num = value_attr.replace("tel:", "")
                if not phone_num.startswith("+351") and phone_num.startswith("351"):
                    phone_num = "+" + phone_num
                telecom["value"] = f"tel:{phone_num}"

            # Determine type from value prefix
            if value_attr.startswith("tel:"):
                telecom["type"] = "phone"
                telecom["display_value"] = value_attr.replace("tel:", "")
            elif value_attr.startswith("mailto:"):
                telecom["type"] = "email"
                telecom["display_value"] = value_attr.replace("mailto:", "")
            elif value_attr.startswith("fax:"):
                telecom["type"] = "fax"
                telecom["display_value"] = value_attr.replace("fax:", "")
            else:
                telecom["type"] = "other"
                telecom["display_value"] = value_attr

        # Extract use code
        use_attr = telecom_element.get("use")
        if use_attr:
            telecom["use"] = use_attr

        return telecom if telecom else None

    def _is_invalid_telecom(self, value: str) -> bool:
        """
        Check if telecom value is invalid/empty and should be filtered out
        
        Returns True if telecom should be excluded from results
        """
        if not value or not value.strip():
            return True
            
        # Remove protocol prefix for validation
        clean_value = value
        if value.startswith(("tel:", "fax:", "mailto:")):
            clean_value = value.split(":", 1)[1] if ":" in value else ""
        
        # Filter out invalid/empty values
        invalid_patterns = [
            "",           # Empty after prefix removal
            "0",          # Just "0" (common invalid placeholder)
            "0 ()",       # "0 ()" pattern
            "()",         # Empty parentheses
            " ()",        # Space with empty parentheses
        ]
        
        return clean_value.strip() in invalid_patterns

    def _parse_identifier(self, id_element: ET.Element) -> Optional[Dict]:
        """
        Parse identifier information from XML element
        
        Args:
            id_element: XML id element
            
        Returns:
            Dictionary with identifier information or None if invalid
        """
        identifier = {}
        
        # Extract root (namespace/system)
        root_attr = id_element.get("root")
        if root_attr:
            identifier["system"] = root_attr
            
        # Extract extension (the actual ID value)
        extension_attr = id_element.get("extension")
        if extension_attr:
            identifier["value"] = extension_attr
            
        # Extract assigningAuthorityName if present
        authority_name = id_element.get("assigningAuthorityName")
        if authority_name:
            identifier["assigning_authority"] = authority_name
            
        # Return only if we have at least a system or value
        if identifier.get("system") or identifier.get("value"):
            return identifier
            
        return None

    def _get_name_part(self, name_element: ET.Element, part_type: str) -> str:
        """Extract specific part of a name (family, given, prefix)"""
        part_elem = name_element.find(f".//{part_type}", self.namespaces)
        if part_elem is not None and part_elem.text:
            return part_elem.text.strip()
        return ""

    def _extract_document_creation_date(self, root: ET.Element) -> str:
        """Extract document creation date from CDA header"""
        # Look for effectiveTime in the CDA header
        effective_time = root.find(".//effectiveTime[@value]", self.namespaces)
        if effective_time is not None and effective_time.get("value"):
            return self._format_cda_datetime(effective_time.get("value"))

        # Alternative path: look for creationTime
        creation_time = root.find(".//creationTime[@value]", self.namespaces)
        if creation_time is not None and creation_time.get("value"):
            return self._format_cda_datetime(creation_time.get("value"))

        return ""

    def _extract_document_last_update_date(self, root: ET.Element) -> str:
        """
        Extract document last update date from CDA header.
        This is critical for healthcare professionals to understand data currency.
        """
        # Priority 1: Look for explicit update/revision time in document header
        update_time = root.find(
            ".//documentationOf/serviceEvent/effectiveTime/high[@value]",
            self.namespaces,
        )
        if update_time is not None and update_time.get("value"):
            return self._format_cda_datetime(update_time.get("value"))

        # Priority 2: Look for revision history or version-specific time
        version_elem = root.find(".//versionNumber", self.namespaces)
        if version_elem is not None:
            # Look for associated time element in same parent
            time_elem = version_elem.find("../effectiveTime[@value]", self.namespaces)
            if time_elem is not None and time_elem.get("value"):
                return self._format_cda_datetime(time_elem.get("value"))

        # Priority 3: Look for any modification/update timestamp
        modification_time = root.find(".//lastModified[@value]", self.namespaces)
        if modification_time is not None and modification_time.get("value"):
            return self._format_cda_datetime(modification_time.get("value"))

        # Priority 4: Look for participant time (author time can indicate updates)
        participant_time = root.find(".//participant/time[@value]", self.namespaces)
        if participant_time is not None and participant_time.get("value"):
            return self._format_cda_datetime(participant_time.get("value"))

        # Fallback: Use creation date (indicates no updates since creation)
        creation_date = self._extract_document_creation_date(root)
        return creation_date if creation_date else "Unknown"

    def _extract_document_version_number(self, root: ET.Element) -> str:
        """Extract document version number from CDA header"""
        version_elem = root.find(".//versionNumber[@value]", self.namespaces)
        if version_elem is not None and version_elem.get("value"):
            return version_elem.get("value")
        return ""

    def _extract_document_set_id(self, root: ET.Element) -> str:
        """Extract document set ID from CDA header"""
        set_id_elem = root.find(".//setId[@root]", self.namespaces)
        if set_id_elem is not None and set_id_elem.get("root"):
            extension = set_id_elem.get("extension", "")
            root_id = set_id_elem.get("root")
            return f"{root_id}" + (f".{extension}" if extension else "")
        return ""

    def _format_cda_datetime(self, cda_datetime: str) -> str:
        """Format CDA datetime string to human-readable format with timezone support"""
        if not cda_datetime:
            return ""

        try:
            # Handle timezone-aware format: YYYYMMDDHHMMSS+ZZZZ or YYYYMMDD+ZZZZ
            timezone_info = ""
            core_datetime = cda_datetime

            # Extract timezone if present (+ZZZZ or -ZZZZ)
            if "+" in cda_datetime or (cda_datetime.count("-") > 2):
                # Find timezone offset
                for i, char in enumerate(cda_datetime):
                    if char in ["+", "-"] and i >= 8:  # Timezone starts after date
                        core_datetime = cda_datetime[:i]
                        timezone_info = cda_datetime[i:]
                        break

            # Parse core datetime
            if len(core_datetime) >= 14:
                year = core_datetime[:4]
                month = core_datetime[4:6]
                day = core_datetime[6:8]
                hour = core_datetime[8:10]
                minute = core_datetime[10:12]
                second = core_datetime[12:14]

                formatted = f"{year}-{month}-{day} {hour}:{minute}:{second}"

                # Add timezone if present
                if timezone_info:
                    if timezone_info == "+0000":
                        formatted += " (UTC)"
                    elif timezone_info.startswith("+"):
                        formatted += f" (UTC{timezone_info})"
                    elif timezone_info.startswith("-"):
                        formatted += f" (UTC{timezone_info})"
                    else:
                        formatted += f" ({timezone_info})"

                return formatted
            elif len(core_datetime) >= 8:
                # Date only format
                year = core_datetime[:4]
                month = core_datetime[4:6]
                day = core_datetime[6:8]
                formatted = f"{year}-{month}-{day}"

                # Add timezone if present
                if timezone_info:
                    if timezone_info == "+0000":
                        formatted += " (UTC)"
                    else:
                        formatted += f" ({timezone_info})"

                return formatted
        except (ValueError, IndexError) as e:
            logger.warning(f"Error formatting CDA datetime '{cda_datetime}': {e}")

        return cda_datetime  # Return as-is if parsing fails

    def _extract_from_html(self, html_content: str) -> AdministrativeData:
        """Extract what administrative data we can from HTML format"""
        # For HTML format, we have limited extraction capabilities
        # This is a fallback for when we don't have proper XML structure
        admin_data = AdministrativeData()

        # Try to extract basic information from HTML tables or text
        # This would need to be enhanced based on the specific HTML structure
        # For now, return empty structure

        return admin_data

    def _extract_participants(self, root: ET.Element) -> List[PersonInfo]:
        """Extract participant information including emergency contacts, next of kin, dependencies"""
        participants = []

        # Find all participant elements
        participant_elements = root.findall(".//participant", self.namespaces)

        for participant in participant_elements:
            person_info = self._extract_participant_info(participant)
            if person_info and (
                person_info.family_name or person_info.given_name or person_info.role
            ):
                participants.append(person_info)

        return participants

    def _extract_participant_info(
        self, participant_element: ET.Element
    ) -> Optional[PersonInfo]:
        """Extract information from a single participant element"""
        person_info = PersonInfo()

        # Get participant type code for context
        type_code = participant_element.get("typeCode", "")

        # Extract associated entity
        associated_entity = participant_element.find(
            ".//associatedEntity", self.namespaces
        )
        if associated_entity is None:
            return None

        # Get class code to determine type
        class_code = associated_entity.get("classCode", "")

        # Determine role based on function code and class code
        function_code_elem = participant_element.find(
            ".//functionCode", self.namespaces
        )
        if function_code_elem is not None:
            function_code = function_code_elem.get("code", "")
            if function_code == "PCP":
                person_info.role = "Primary Care Provider"
            else:
                person_info.role = function_code
        elif class_code == "ECON":
            # Emergency contact
            person_info.role = "Emergency Contact"

            # Check for specific relationship code
            code_elem = associated_entity.find(".//code", self.namespaces)
            if code_elem is not None:
                relationship_code = code_elem.get("displayName", "")
                if relationship_code:
                    person_info.role = f"Emergency Contact ({relationship_code})"
        elif type_code == "IND" and class_code == "PRS":
            # Individual participant with personal class - typically preferred contact
            person_info.role = "Preferred Health Professional"
        elif type_code == "IND":
            # Individual participant - general contact person
            person_info.role = "Contact Person"
        elif class_code == "PRS":
            # Personal relationship
            person_info.role = "Personal Contact"
        else:
            person_info.role = f"Contact ({type_code})"

        # Extract person name
        person_name = associated_entity.find(
            ".//associatedPerson/name", self.namespaces
        )
        if person_name is not None:
            person_info.family_name = self._get_name_part(person_name, "family")
            person_info.given_name = self._get_name_part(person_name, "given")

        # Extract contact information
        person_info.contact_info = self._extract_contact_from_element(
            associated_entity, "UNKNOWN"
        )

        # Extract time period if available
        time_elem = participant_element.find(".//time", self.namespaces)
        if time_elem is not None:
            # Extract effective date range
            low_elem = time_elem.find(".//low", self.namespaces)
            if low_elem is not None and low_elem.get("value"):
                person_info.specialty = (
                    f"From: {self._format_cda_datetime(low_elem.get('value'))}"
                )

            high_elem = time_elem.find(".//high", self.namespaces)
            if high_elem is not None and high_elem.get("value"):
                if person_info.specialty:
                    person_info.specialty += (
                        f" To: {self._format_cda_datetime(high_elem.get('value'))}"
                    )
                else:
                    person_info.specialty = (
                        f"To: {self._format_cda_datetime(high_elem.get('value'))}"
                    )

        # Extract organization information if available
        scoping_org = associated_entity.find(".//scopingOrganization", self.namespaces)
        if scoping_org is not None:
            org_name = scoping_org.find(".//name", self.namespaces)
            if org_name is not None and org_name.text:
                person_info.organization.name = org_name.text.strip()
                person_info.organization.organization_type = person_info.role

                # Extract organization contact info
                org_contact = self._extract_contact_from_element(scoping_org, "UNKNOWN")
                person_info.organization.addresses = org_contact.addresses
                person_info.organization.telecoms = org_contact.telecoms

        return person_info
