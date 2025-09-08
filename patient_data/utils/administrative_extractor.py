"""
Enhanced Administrative Data Extraction Methods
Comprehensive extraction of contact information, addresses, and organizational data
"""

from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class CDAContactExtractor:
    """Extract contact information from CDA documents"""

    @staticmethod
    def extract_address(addr_element: ET.Element) -> Dict[str, Any]:
        """Extract structured address information"""
        if addr_element is None:
            return {}

        address = {
            "use": addr_element.get("use", "unknown"),
            "street_address_line": None,
            "city": None,
            "state": None,
            "postal_code": None,
            "country": None,
            "full_address": None,
        }

        # Extract address components
        street = addr_element.find("{urn:hl7-org:v3}streetAddressLine")
        if street is not None and street.text:
            address["street_address_line"] = street.text.strip()

        city = addr_element.find("{urn:hl7-org:v3}city")
        if city is not None and city.text:
            address["city"] = city.text.strip()

        state = addr_element.find("{urn:hl7-org:v3}state")
        if state is not None and state.text:
            address["state"] = state.text.strip()

        postal = addr_element.find("{urn:hl7-org:v3}postalCode")
        if postal is not None and postal.text:
            address["postal_code"] = postal.text.strip()

        country = addr_element.find("{urn:hl7-org:v3}country")
        if country is not None and country.text:
            address["country"] = country.text.strip()

        # Build full address for display
        parts = []
        if address["street_address_line"]:
            parts.append(address["street_address_line"])
        if address["city"]:
            parts.append(address["city"])
        if address["state"]:
            parts.append(address["state"])
        if address["postal_code"]:
            parts.append(address["postal_code"])
        if address["country"]:
            parts.append(address["country"])

        address["full_address"] = ", ".join(parts) if parts else "No address available"

        return address

    @staticmethod
    def extract_telecom(telecom_element: ET.Element) -> Dict[str, Any]:
        """Extract telecom information (phone, email, etc.)"""
        if telecom_element is None:
            return {}

        telecom = {
            "use": telecom_element.get("use", "unknown"),
            "value": telecom_element.get("value", ""),
            "type": "unknown",
            "display_value": "",
        }

        # Determine telecom type from value
        value = telecom["value"].lower()
        if value.startswith("tel:"):
            telecom["type"] = "phone"
            telecom["display_value"] = telecom["value"][4:]  # Remove "tel:" prefix
        elif value.startswith("mailto:"):
            telecom["type"] = "email"
            telecom["display_value"] = telecom["value"][7:]  # Remove "mailto:" prefix
        elif value.startswith("fax:"):
            telecom["type"] = "fax"
            telecom["display_value"] = telecom["value"][4:]  # Remove "fax:" prefix
        elif value.startswith("http"):
            telecom["type"] = "website"
            telecom["display_value"] = telecom["value"]
        else:
            telecom["display_value"] = telecom["value"]

        return telecom

    @staticmethod
    def extract_person_name(name_element: ET.Element) -> Dict[str, str]:
        """Extract person name components"""
        if name_element is None:
            return {
                "family_name": "Unknown",
                "given_name": "Unknown",
                "full_name": "Unknown",
            }

        family = name_element.find("{urn:hl7-org:v3}family")
        given = name_element.find("{urn:hl7-org:v3}given")

        family_name = (
            family.text.strip() if family is not None and family.text else "Unknown"
        )
        given_name = (
            given.text.strip() if given is not None and given.text else "Unknown"
        )

        return {
            "family_name": family_name,
            "given_name": given_name,
            "full_name": (
                f"{given_name} {family_name}"
                if family_name != "Unknown" and given_name != "Unknown"
                else "Unknown"
            ),
        }

    @staticmethod
    def extract_organization_info(org_element: ET.Element) -> Dict[str, Any]:
        """Extract organization information"""
        if org_element is None:
            return {"id": None, "name": "Unknown", "address": {}, "telecoms": []}

        # Organization ID
        org_id_elem = org_element.find("{urn:hl7-org:v3}id")
        org_id = None
        if org_id_elem is not None:
            org_id = {
                "extension": org_id_elem.get("extension"),
                "root": org_id_elem.get("root"),
                "assigning_authority_name": org_id_elem.get("assigningAuthorityName"),
            }

        # Organization Name
        name_elem = org_element.find("{urn:hl7-org:v3}name")
        org_name = (
            name_elem.text.strip()
            if name_elem is not None and name_elem.text
            else "Unknown"
        )

        # Organization Address
        addr_elem = org_element.find("{urn:hl7-org:v3}addr")
        org_address = CDAContactExtractor.extract_address(addr_elem)

        # Organization Telecoms
        telecom_elems = org_element.findall("{urn:hl7-org:v3}telecom")
        org_telecoms = [
            CDAContactExtractor.extract_telecom(tel) for tel in telecom_elems
        ]

        return {
            "id": org_id,
            "name": org_name,
            "address": org_address,
            "telecoms": org_telecoms,
        }


class EnhancedAdministrativeExtractor:
    """Enhanced extraction of administrative data from CDA documents"""

    def __init__(self, date_formatter=None):
        self.date_formatter = date_formatter

    def extract_patient_contact_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract comprehensive patient contact information"""
        patient_role = root.find(
            ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
        )

        default_patient = {
            "addresses": [],
            "telecoms": [],
            "primary_address": None,
            "primary_phone": None,
            "primary_email": None,
            "full_name": None,
            "given_name": None,
            "family_name": None,
            "patient_id": None,
            "id_authority": None,
            "id_root": None,
            "birth_date": None,
            "gender": None,
        }

        if patient_role is None:
            return default_patient

        # Extract patient ID
        id_elem = patient_role.find("{urn:hl7-org:v3}id")
        if id_elem is not None:
            default_patient["patient_id"] = id_elem.get("extension")
            default_patient["id_authority"] = id_elem.get("assigningAuthorityName")
            default_patient["id_root"] = id_elem.get("root")

        # Extract addresses
        addresses = []
        addr_elements = patient_role.findall("{urn:hl7-org:v3}addr")
        for addr_elem in addr_elements:
            address = CDAContactExtractor.extract_address(addr_elem)
            if address:
                addresses.append(address)

        # Extract telecoms
        telecoms = []
        telecom_elements = patient_role.findall("{urn:hl7-org:v3}telecom")
        for tel_elem in telecom_elements:
            telecom = CDAContactExtractor.extract_telecom(tel_elem)
            if telecom:
                telecoms.append(telecom)

        # Extract patient details
        patient_elem = patient_role.find("{urn:hl7-org:v3}patient")
        if patient_elem is not None:
            # Extract name
            name_elem = patient_elem.find("{urn:hl7-org:v3}name")
            if name_elem is not None:
                given_elem = name_elem.find("{urn:hl7-org:v3}given")
                family_elem = name_elem.find("{urn:hl7-org:v3}family")

                given_name = (
                    given_elem.text.strip()
                    if given_elem is not None and given_elem.text
                    else None
                )
                family_name = (
                    family_elem.text.strip()
                    if family_elem is not None and family_elem.text
                    else None
                )
                full_name = f"{given_name or ''} {family_name or ''}".strip() or None

                default_patient["given_name"] = given_name
                default_patient["family_name"] = family_name
                default_patient["name"] = full_name  # Add this for compatibility
                default_patient["full_name"] = full_name

            # Extract birth date
            birth_elem = patient_elem.find("{urn:hl7-org:v3}birthTime")
            if birth_elem is not None:
                birth_date = birth_elem.get("value")
                if birth_date and self.date_formatter:
                    default_patient["birth_date"] = (
                        self.date_formatter.format_document_date(birth_date)
                    )
                else:
                    default_patient["birth_date"] = birth_date

            # Extract gender
            gender_elem = patient_elem.find("{urn:hl7-org:v3}administrativeGenderCode")
            if gender_elem is not None:
                default_patient["gender"] = gender_elem.get(
                    "displayName", gender_elem.get("code")
                )

        # Identify primary contacts
        primary_address = None
        primary_phone = None
        primary_email = None

        # Find primary address (home use or first available)
        for addr in addresses:
            if addr.get("use") == "HP" or primary_address is None:
                primary_address = addr
                if addr.get("use") == "HP":
                    break

        # Find primary phone and email
        for tel in telecoms:
            if tel.get("type") == "phone" and primary_phone is None:
                primary_phone = tel
            elif tel.get("type") == "email" and primary_email is None:
                primary_email = tel

        # Update with extracted data
        default_patient.update(
            {
                "addresses": addresses,
                "telecoms": telecoms,
                "primary_address": primary_address,
                "primary_phone": primary_phone,
                "primary_email": primary_email,
            }
        )

        return default_patient

    def extract_author_information(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract comprehensive author information with flexible namespace handling"""
        # Import flexible extractor
        from .flexible_cda_extractor import FlexibleCDAExtractor

        flexible_extractor = FlexibleCDAExtractor()

        # Use flexible extraction which provides both nested and direct access
        authors = flexible_extractor.extract_author_flexible(root)

        # Format times if date formatter is available
        for author in authors:
            if author.get("time") and self.date_formatter:
                author["time"] = self.date_formatter.format_clinical_datetime(
                    author["time"]
                )
                # Add display_time for better template labeling
                author["display_time"] = author["time"]

        logger.info(f"Authors extracted: {len(authors)} found")
        return authors

    def extract_custodian_information(self, root: ET.Element) -> Dict[str, Any]:
        """Extract comprehensive custodian information"""
        custodian = root.find(".//{urn:hl7-org:v3}custodian")

        default_custodian = {
            "organization": {
                "name": "Unknown",
                "id": None,
                "address": {},
                "telecoms": [],
            }
        }

        if custodian is None:
            return default_custodian

        org_elem = custodian.find(".//{urn:hl7-org:v3}representedCustodianOrganization")
        if org_elem is not None:
            return {
                "organization": CDAContactExtractor.extract_organization_info(org_elem)
            }

        return default_custodian

    def extract_legal_authenticator(self, root: ET.Element) -> Dict[str, Any]:
        """Extract legal authenticator information with flexible namespace handling"""
        # Import flexible extractor
        from .flexible_cda_extractor import FlexibleCDAExtractor

        flexible_extractor = FlexibleCDAExtractor()

        # Use flexible extraction which provides both nested and direct access
        auth_info = flexible_extractor.extract_legal_authenticator_flexible(root)

        # Format time if date formatter is available
        if auth_info.get("time") and self.date_formatter:
            auth_info["authentication_time"] = (
                self.date_formatter.format_clinical_datetime(auth_info["time"])
            )
            # Keep the original time field for compatibility
            auth_info["time"] = auth_info["authentication_time"]

        logger.info(
            f"Legal authenticator extracted: {auth_info.get('full_name') or 'Unknown'}"
        )
        return auth_info

    def extract_administrative_section(self, root: ET.Element) -> Dict[str, Any]:
        """Extract complete administrative section including all contact information"""
        try:
            # Extract all administrative components
            patient_info = self.extract_patient_contact_info(root)
            authors = self.extract_author_information(root)
            custodian = self.extract_custodian_information(root)
            legal_auth = self.extract_legal_authenticator(root)

            return {
                "patient": patient_info,
                "authors": authors,
                "custodians": [custodian] if custodian.get("organization") else [],
                "legal_authenticators": (
                    [legal_auth] if legal_auth.get("full_name") else []
                ),
            }
        except Exception as e:
            logger.error(f"Error extracting administrative section: {str(e)}")
            return {
                "patient": {},
                "authors": [],
                "custodians": [],
                "legal_authenticators": [],
            }
