"""
CDA Administrative Information Extractor
Extracts comprehensive administrative data from European L1/L3 CDA documents
including contact information, healthcare providers, legal authenticators, etc.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import re
from dataclasses import dataclass


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
    organization_type: str = ""

    def __post_init__(self):
        if self.addresses is None:
            self.addresses = []
        if self.telecoms is None:
            self.telecoms = []


@dataclass
class PersonInfo:
    """Represents person information (HCP, legal authenticator, etc.)"""

    family_name: str = ""
    given_name: str = ""
    title: str = ""
    role: str = ""
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
                return self._extract_from_xml(root)
            else:
                # HTML format - try to extract what we can
                return self._extract_from_html(cda_content)

        except Exception as e:
            print(f"Error extracting administrative data: {e}")
            return AdministrativeData()

    def _extract_from_xml(self, root: ET.Element) -> AdministrativeData:
        """Extract administrative data from CDA XML"""
        admin_data = AdministrativeData()

        # Extract patient contact information
        admin_data.patient_contact_info = self._extract_patient_contact_info(root)

        # Extract author (HCP) information
        admin_data.author_hcp = self._extract_author_info(root)

        # Extract legal authenticator
        admin_data.legal_authenticator = self._extract_legal_authenticator(root)

        # Extract custodian organization
        admin_data.custodian_organization = self._extract_custodian_info(root)

        # Extract guardian information
        admin_data.guardian = self._extract_guardian_info(root)

        # Extract preferred HCP organization (Cabinet Medicale)
        admin_data.preferred_hcp = self._extract_preferred_hcp(root)

        # Extract other contacts
        admin_data.other_contacts = self._extract_other_contacts(root)

        return admin_data

    def _extract_patient_contact_info(self, root: ET.Element) -> ContactInfo:
        """Extract patient contact information"""
        contact_info = ContactInfo()

        # Look for patient role section
        patient_role = root.find(".//recordTarget/patientRole", self.namespaces)
        if patient_role is not None:
            # Extract addresses
            addresses = patient_role.findall(".//addr", self.namespaces)
            for addr in addresses:
                address_info = self._parse_address(addr)
                if address_info:
                    contact_info.addresses.append(address_info)

            # Extract telecom information
            telecoms = patient_role.findall(".//telecom", self.namespaces)
            for telecom in telecoms:
                telecom_info = self._parse_telecom(telecom)
                if telecom_info:
                    contact_info.telecoms.append(telecom_info)

        return contact_info

    def _extract_author_info(self, root: ET.Element) -> PersonInfo:
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

            # Extract organization
            org = author.find(".//representedOrganization", self.namespaces)
            if org is not None:
                person_info.organization = self._extract_organization_info(org)

            # Extract contact information
            assigned_author = author.find(".//assignedAuthor", self.namespaces)
            if assigned_author is not None:
                person_info.contact_info = self._extract_contact_from_element(
                    assigned_author
                )

        return person_info

    def _extract_legal_authenticator(self, root: ET.Element) -> PersonInfo:
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
                person_info.organization = self._extract_organization_info(org)

            # Extract contact information
            assigned_entity = auth.find(".//assignedEntity", self.namespaces)
            if assigned_entity is not None:
                person_info.contact_info = self._extract_contact_from_element(
                    assigned_entity
                )

        return person_info

    def _extract_custodian_info(self, root: ET.Element) -> OrganizationInfo:
        """Extract custodian organization information"""
        org_info = OrganizationInfo()
        org_info.organization_type = "Custodian"

        # Look for custodian section
        custodian = root.find(
            ".//custodian/assignedCustodian/representedCustodianOrganization",
            self.namespaces,
        )
        if custodian is not None:
            org_info = self._extract_organization_info(custodian)
            org_info.organization_type = "Custodian"

        return org_info

    def _extract_guardian_info(self, root: ET.Element) -> PersonInfo:
        """Extract guardian information"""
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
            person_info.contact_info = self._extract_contact_from_element(guardian)

        return person_info

    def _extract_preferred_hcp(self, root: ET.Element) -> OrganizationInfo:
        """Extract preferred healthcare provider (Cabinet Medicale) information"""
        org_info = OrganizationInfo()
        org_info.organization_type = "Preferred HCP Organization"

        # Look for participant with type code PPRF (primary performer)
        participants = root.findall('.//participant[@typeCode="PPRF"]', self.namespaces)
        for participant in participants:
            org = participant.find(".//scopingOrganization", self.namespaces)
            if org is not None:
                org_info = self._extract_organization_info(org)
                org_info.organization_type = "Cabinet Medicale"
                break

        return org_info

    def _extract_other_contacts(self, root: ET.Element) -> List[PersonInfo]:
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
                        assigned_entity
                    )

                contacts.append(person_info)

        return contacts

    def _extract_organization_info(self, org_element: ET.Element) -> OrganizationInfo:
        """Extract organization information from XML element"""
        org_info = OrganizationInfo()

        # Extract organization name
        name_elem = org_element.find(".//name", self.namespaces)
        if name_elem is not None and name_elem.text:
            org_info.name = name_elem.text.strip()

        # Extract contact information
        contact_info = self._extract_contact_from_element(org_element)
        org_info.addresses = contact_info.addresses
        org_info.telecoms = contact_info.telecoms

        return org_info

    def _extract_contact_from_element(self, element: ET.Element) -> ContactInfo:
        """Extract contact information from any XML element"""
        contact_info = ContactInfo()

        # Extract addresses
        addresses = element.findall(".//addr", self.namespaces)
        for addr in addresses:
            address_info = self._parse_address(addr)
            if address_info:
                contact_info.addresses.append(address_info)

        # Extract telecom information
        telecoms = element.findall(".//telecom", self.namespaces)
        for telecom in telecoms:
            telecom_info = self._parse_telecom(telecom)
            if telecom_info:
                contact_info.telecoms.append(telecom_info)

        return contact_info

    def _parse_address(self, addr_element: ET.Element) -> Optional[Dict]:
        """Parse address information from XML element"""
        address = {}

        # Extract address components
        street_lines = []
        street_addrs = addr_element.findall(".//streetAddressLine", self.namespaces)
        for street in street_addrs:
            if street.text:
                street_lines.append(street.text.strip())

        if street_lines:
            address["street"] = ", ".join(street_lines)

        # Extract city
        city_elem = addr_element.find(".//city", self.namespaces)
        if city_elem is not None and city_elem.text:
            address["city"] = city_elem.text.strip()

        # Extract postal code
        postal_elem = addr_element.find(".//postalCode", self.namespaces)
        if postal_elem is not None and postal_elem.text:
            address["postalCode"] = postal_elem.text.strip()

        # Extract country
        country_elem = addr_element.find(".//country", self.namespaces)
        if country_elem is not None and country_elem.text:
            address["country"] = country_elem.text.strip()

        # Extract use code
        use_attr = addr_element.get("use")
        if use_attr:
            address["use"] = use_attr

        return address if address else None

    def _parse_telecom(self, telecom_element: ET.Element) -> Optional[Dict]:
        """Parse telecom information from XML element"""
        telecom = {}

        # Extract value
        value_attr = telecom_element.get("value")
        if value_attr:
            telecom["value"] = value_attr

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

    def _get_name_part(self, name_element: ET.Element, part_type: str) -> str:
        """Extract specific part of a name (family, given, prefix)"""
        part_elem = name_element.find(f".//{part_type}", self.namespaces)
        if part_elem is not None and part_elem.text:
            return part_elem.text.strip()
        return ""

    def _extract_from_html(self, html_content: str) -> AdministrativeData:
        """Extract what administrative data we can from HTML format"""
        # For HTML format, we have limited extraction capabilities
        # This is a fallback for when we don't have proper XML structure
        admin_data = AdministrativeData()

        # Try to extract basic information from HTML tables or text
        # This would need to be enhanced based on the specific HTML structure
        # For now, return empty structure

        return admin_data
