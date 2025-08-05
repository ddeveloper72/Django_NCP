"""
Flexible CDA Element Extractor
Handles different namespace scenarios and provides multiple search strategies
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)


class FlexibleCDAExtractor:
    """Flexible extractor that can handle different namespace scenarios"""

    def __init__(self):
        # Common namespace variations found in CDA documents
        self.namespace_variations = [
            "urn:hl7-org:v3",  # Standard HL7 CDA namespace
            "urn:hl7-org:v3:",  # Sometimes with trailing colon
            "http://hl7.org/cda",  # Alternative HL7 namespace
        ]

        # Common namespace prefixes
        self.common_prefixes = ["a", "cda", "hl7", ""]

    def find_element_flexible(
        self, root: ET.Element, element_path: str
    ) -> Optional[ET.Element]:
        """
        Find element using multiple namespace strategies

        Args:
            root: Root element to search from
            element_path: Path like 'legalAuthenticator/assignedEntity/assignedPerson/name'

        Returns:
            Found element or None
        """
        # Strategy 1: Try with known namespace variations
        for namespace in self.namespace_variations:
            try:
                # Build path with full namespace
                parts = element_path.split("/")
                ns_parts = []
                for part in parts:
                    if part.startswith("."):
                        ns_parts.append(part)
                    else:
                        ns_parts.append(f"{{{namespace}}}{part}")

                if element_path.startswith(".//"):
                    # Keep the .// prefix for descendant search
                    ns_path = f".//{'/'.join(ns_parts[1:])}"
                else:
                    ns_path = "/".join(ns_parts)

                element = root.find(ns_path)
                if element is not None:
                    return element
            except Exception:
                continue

        # Strategy 2: Try without namespace (for documents with default namespace)
        try:
            if not element_path.startswith(".//"):
                element_path = f".//{element_path}"
            element = root.find(element_path)
            if element is not None:
                return element
        except Exception:
            pass

        # Strategy 3: Search by tag name only (last resort)
        try:
            final_element = element_path.split("/")[-1]
            for elem in root.iter():
                # Get local name without namespace
                local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if local_name == final_element:
                    return elem
        except Exception:
            pass

        return None

    def find_elements_flexible(
        self, root: ET.Element, element_path: str
    ) -> List[ET.Element]:
        """Find all elements using flexible namespace strategies"""
        elements = []

        # Strategy 1: Try with known namespace variations
        for namespace in self.namespace_variations:
            try:
                if element_path.startswith(".//"):
                    # Handle descendant search (.//element)
                    element_name = element_path[3:]  # Remove './/'
                    ns_path = f".//{{{namespace}}}{element_name}"
                elif element_path.startswith("./"):
                    # Handle child search (./element)
                    element_name = element_path[2:]  # Remove './'
                    ns_path = f"./{{{namespace}}}{element_name}"
                else:
                    # Handle direct element name or complex path
                    parts = element_path.split("/")
                    ns_parts = []
                    for part in parts:
                        if part in [".", ".."]:
                            ns_parts.append(part)
                        else:
                            ns_parts.append(f"{{{namespace}}}{part}")
                    ns_path = "/".join(ns_parts)

                found_elements = root.findall(ns_path)
                if found_elements:
                    elements.extend(found_elements)
            except Exception:
                continue

        # Strategy 2: Try without namespace (fallback)
        if not elements:
            try:
                found_elements = root.findall(element_path)
                if found_elements:
                    elements.extend(found_elements)
            except Exception:
                pass

        # Remove duplicates while preserving order
        unique_elements = []
        for elem in elements:
            if elem not in unique_elements:
                unique_elements.append(elem)

        return unique_elements

    def extract_legal_authenticator_flexible(self, root: ET.Element) -> Dict[str, Any]:
        """Extract legal authenticator with flexible namespace handling"""

        # Try to find legal authenticator with different strategies
        legal_auth = self.find_element_flexible(root, ".//legalAuthenticator")

        if legal_auth is None:
            logger.info("Legal authenticator not found")
            return {
                "time": None,
                "signature_code": None,
                "family_name": None,  # Direct access for templates
                "given_name": None,  # Direct access for templates
                "full_name": None,  # Direct access for templates
                "person": {"family_name": None, "given_name": None, "full_name": None},
                "organization": {"name": None},
                "id": None,
            }

        logger.info("Legal authenticator found, extracting data...")

        auth_info = {
            "time": None,
            "signature_code": None,
            "family_name": None,
            "given_name": None,
            "full_name": None,
            "person": {"family_name": None, "given_name": None, "full_name": None},
            "organization": {"name": None},
            "id": None,
        }

        # Extract authentication time
        time_elem = self.find_element_flexible(legal_auth, "time")
        if time_elem is not None:
            auth_info["time"] = time_elem.get("value")

        # Extract signature code
        sig_elem = self.find_element_flexible(legal_auth, "signatureCode")
        if sig_elem is not None:
            auth_info["signature_code"] = sig_elem.get("code")

        # Extract assigned entity
        entity_elem = self.find_element_flexible(legal_auth, "assignedEntity")
        if entity_elem is not None:
            # Extract entity ID
            id_elem = self.find_element_flexible(entity_elem, "id")
            if id_elem is not None:
                auth_info["id"] = {
                    "extension": id_elem.get("extension"),
                    "root": id_elem.get("root"),
                }

            # Extract assigned person
            person_elem = self.find_element_flexible(entity_elem, "assignedPerson")
            if person_elem is not None:
                name_elem = self.find_element_flexible(person_elem, "name")
                if name_elem is not None:
                    # Extract name components with flexible approach
                    given_elem = self.find_element_flexible(name_elem, "given")
                    family_elem = self.find_element_flexible(name_elem, "family")

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

                    # Set both direct access and nested structure
                    auth_info["given_name"] = given_name
                    auth_info["family_name"] = family_name
                    auth_info["full_name"] = (
                        f"{given_name or ''} {family_name or ''}".strip() or None
                    )

                    auth_info["person"] = {
                        "given_name": given_name,
                        "family_name": family_name,
                        "full_name": auth_info["full_name"],
                    }

            # Extract represented organization
            org_elem = self.find_element_flexible(
                entity_elem, "representedOrganization"
            )
            if org_elem is not None:
                org_name_elem = self.find_element_flexible(org_elem, "name")
                org_name = (
                    org_name_elem.text.strip()
                    if org_name_elem is not None and org_name_elem.text
                    else None
                )
                auth_info["organization"] = {"name": org_name}

        logger.info(
            f"Legal authenticator extracted: {auth_info['full_name'] or 'Unknown'}"
        )
        return auth_info

    def extract_author_flexible(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract comprehensive author information with flexible namespace handling"""
        authors = []

        # Find all author elements
        author_elements = self.find_elements_flexible(root, ".//author")

        for author_elem in author_elements:
            author_info = {
                "time": None,
                # Direct access fields for templates
                "family_name": None,
                "given_name": None,
                "full_name": None,
                # Original detailed structure preserved
                "person": {"family_name": None, "given_name": None, "full_name": None},
                "organization": {"name": None, "address": {}, "telecoms": []},
                "id": None,
                "code": None,
                "role": None,
            }

            # Extract author time
            time_elem = self.find_element_flexible(author_elem, "time")
            if time_elem is not None:
                author_info["time"] = time_elem.get("value")

            # Extract assigned author
            assigned_author = self.find_element_flexible(author_elem, "assignedAuthor")
            if assigned_author is not None:
                # Extract author ID
                id_elem = self.find_element_flexible(assigned_author, "id")
                if id_elem is not None:
                    author_info["id"] = {
                        "extension": id_elem.get("extension"),
                        "root": id_elem.get("root"),
                        "assigning_authority_name": id_elem.get(
                            "assigningAuthorityName"
                        ),
                    }

                # Extract author code/role (detailed structure)
                code_elem = self.find_element_flexible(assigned_author, "code")
                if code_elem is not None:
                    author_info["code"] = {
                        "code": code_elem.get("code"),
                        "code_system": code_elem.get("codeSystem"),
                        "display_name": code_elem.get("displayName"),
                    }
                    author_info["role"] = code_elem.get(
                        "displayName", "Healthcare Professional"
                    )

                # Extract assigned person
                person_elem = self.find_element_flexible(
                    assigned_author, "assignedPerson"
                )
                if person_elem is not None:
                    name_elem = self.find_element_flexible(person_elem, "name")
                    if name_elem is not None:
                        given_elem = self.find_element_flexible(name_elem, "given")
                        family_elem = self.find_element_flexible(name_elem, "family")

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
                        full_name = (
                            f"{given_name or ''} {family_name or ''}".strip() or None
                        )

                        # Set both direct access and nested structure
                        author_info["given_name"] = given_name
                        author_info["family_name"] = family_name
                        author_info["full_name"] = full_name

                        author_info["person"] = {
                            "given_name": given_name,
                            "family_name": family_name,
                            "full_name": full_name,
                        }

                # Extract represented organization with comprehensive details
                org_elem = self.find_element_flexible(
                    assigned_author, "representedOrganization"
                )
                if org_elem is not None:
                    author_info["organization"] = (
                        self._extract_organization_info_flexible(org_elem)
                    )

            authors.append(author_info)

        return authors

    def _extract_organization_info_flexible(
        self, org_element: ET.Element
    ) -> Dict[str, Any]:
        """Extract comprehensive organization information with flexible namespace handling"""
        if org_element is None:
            return {"id": None, "name": "Unknown", "address": {}, "telecoms": []}

        # Organization ID
        org_id_elem = self.find_element_flexible(org_element, "id")
        org_id = None
        if org_id_elem is not None:
            org_id = {
                "extension": org_id_elem.get("extension"),
                "root": org_id_elem.get("root"),
                "assigning_authority_name": org_id_elem.get("assigningAuthorityName"),
            }

        # Organization Name
        name_elem = self.find_element_flexible(org_element, "name")
        org_name = (
            name_elem.text.strip()
            if name_elem is not None and name_elem.text
            else "Unknown"
        )

        # Organization Address
        addr_elem = self.find_element_flexible(org_element, "addr")
        org_address = self._extract_address_flexible(addr_elem)

        # Organization Telecoms
        telecom_elems = self.find_elements_flexible(org_element, "telecom")
        org_telecoms = [self._extract_telecom_flexible(tel) for tel in telecom_elems]

        return {
            "id": org_id,
            "name": org_name,
            "address": org_address,
            "telecoms": org_telecoms,
        }

    def _extract_address_flexible(self, addr_element: ET.Element) -> Dict[str, Any]:
        """Extract structured address information with flexible namespace handling"""
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

        # Extract address components with flexible namespace handling
        street = self.find_element_flexible(addr_element, "streetAddressLine")
        if street is not None and street.text:
            address["street_address_line"] = street.text.strip()

        city = self.find_element_flexible(addr_element, "city")
        if city is not None and city.text:
            address["city"] = city.text.strip()

        state = self.find_element_flexible(addr_element, "state")
        if state is not None and state.text:
            address["state"] = state.text.strip()

        postal = self.find_element_flexible(addr_element, "postalCode")
        if postal is not None and postal.text:
            address["postal_code"] = postal.text.strip()

        country = self.find_element_flexible(addr_element, "country")
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

    def _extract_telecom_flexible(self, telecom_element: ET.Element) -> Dict[str, Any]:
        """Extract telecom information (phone, email, etc.) with flexible namespace handling"""
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

    def diagnose_namespace_issues(self, root: ET.Element) -> Dict[str, Any]:
        """Diagnose namespace issues in the document"""
        diagnosis = {
            "root_tag": root.tag,
            "root_namespace": None,
            "namespace_declarations": {},
            "legal_auth_found": False,
            "legal_auth_paths": [],
            "author_found": False,
            "author_count": 0,
        }

        # Extract namespace from root tag
        if "}" in root.tag:
            diagnosis["root_namespace"] = root.tag.split("}")[0][1:]

        # Find namespace declarations in root attributes
        for attr, value in root.attrib.items():
            if attr.startswith("xmlns"):
                diagnosis["namespace_declarations"][attr] = value

        # Check for legal authenticator with different approaches
        legal_auth_patterns = [
            ".//legalAuthenticator",
            ".//{urn:hl7-org:v3}legalAuthenticator",
            ".//a:legalAuthenticator",
            ".//cda:legalAuthenticator",
        ]

        for pattern in legal_auth_patterns:
            try:
                elements = root.findall(pattern)
                if elements:
                    diagnosis["legal_auth_found"] = True
                    diagnosis["legal_auth_paths"].append(pattern)
            except:
                pass

        # Search by tag name only as last resort
        for elem in root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local_name == "legalAuthenticator":
                diagnosis["legal_auth_found"] = True
                diagnosis["legal_auth_paths"].append(f"Found by tag name: {elem.tag}")
            elif local_name == "author":
                diagnosis["author_count"] += 1

        if diagnosis["author_count"] > 0:
            diagnosis["author_found"] = True

        return diagnosis
