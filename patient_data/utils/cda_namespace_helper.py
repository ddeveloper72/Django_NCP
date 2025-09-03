"""
CDA XML Namespace Utilities
Helper functions to simplify namespace handling in CDA document parsing
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any


class CDANamespaceHelper:
    """Helper class for CDA namespace handling"""

    # Standard CDA namespaces
    NAMESPACES = {
        "cda": "urn:hl7-org:v3",
        "pharm": "urn:ihe:pharm:medication",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }

    @classmethod
    def ns(cls, element_name: str, namespace: str = "cda") -> str:
        """
        Convert element name to namespaced format

        Args:
            element_name: The XML element name
            namespace: The namespace prefix (default: 'cda')

        Returns:
            Namespaced element string like '{urn:hl7-org:v3}section'
        """
        if namespace in cls.NAMESPACES:
            return f"{{{cls.NAMESPACES[namespace]}}}{element_name}"
        else:
            return element_name

    @classmethod
    def find_cda(cls, root: ET.Element, path: str) -> Optional[ET.Element]:
        """
        Find CDA element using simplified path

        Args:
            root: Root element to search from
            path: Simplified path like 'recordTarget/patientRole'

        Returns:
            Found element or None
        """
        # Convert simplified path to namespaced path
        parts = path.split("/")
        namespaced_parts = []

        for part in parts:
            if part.startswith("."):
                namespaced_parts.append(part)  # Keep relative indicators
            elif part == "*":
                namespaced_parts.append(part)  # Keep wildcards
            else:
                namespaced_parts.append(cls.ns(part))

        namespaced_path = "/".join(namespaced_parts)
        return root.find(namespaced_path)

    @classmethod
    def findall_cda(cls, root: ET.Element, path: str) -> List[ET.Element]:
        """
        Find all CDA elements using simplified path

        Args:
            root: Root element to search from
            path: Simplified path like './/section'

        Returns:
            List of found elements
        """
        # Convert simplified path to namespaced path
        parts = path.split("/")
        namespaced_parts = []

        for part in parts:
            if part.startswith("."):
                namespaced_parts.append(part)  # Keep relative indicators
            elif part == "*":
                namespaced_parts.append(part)  # Keep wildcards
            else:
                namespaced_parts.append(cls.ns(part))

        namespaced_path = "/".join(namespaced_parts)
        return root.findall(namespaced_path)

    @classmethod
    def get_text_safe(
        cls, element: Optional[ET.Element], default: str = "Unknown"
    ) -> str:
        """
        Safely get text from element

        Args:
            element: XML element (can be None)
            default: Default value if element is None or has no text

        Returns:
            Element text or default value
        """
        if element is not None and element.text:
            return element.text.strip()
        return default

    @classmethod
    def get_attr_safe(
        cls, element: Optional[ET.Element], attr_name: str, default: str = "Unknown"
    ) -> str:
        """
        Safely get attribute from element

        Args:
            element: XML element (can be None)
            attr_name: Attribute name
            default: Default value if element is None or attribute missing

        Returns:
            Attribute value or default value
        """
        if element is not None:
            return element.get(attr_name, default)
        return default


# Convenience functions for common CDA patterns
def find_patient_role(root: ET.Element) -> Optional[ET.Element]:
    """Find patient role element"""
    return CDANamespaceHelper.find_cda(root, ".//recordTarget/patientRole")


def find_patient_info(root: ET.Element) -> Optional[ET.Element]:
    """Find patient element"""
    patient_role = find_patient_role(root)
    if patient_role is not None:
        return CDANamespaceHelper.find_cda(patient_role, "patient")
    return None


def find_all_sections(root: ET.Element) -> List[ET.Element]:
    """Find all section elements"""
    return CDANamespaceHelper.findall_cda(root, ".//section")


def find_custodian_org(root: ET.Element) -> Optional[ET.Element]:
    """Find custodian organization"""
    return CDANamespaceHelper.find_cda(
        root, ".//custodian//representedCustodianOrganization"
    )


def find_all_authors(root: ET.Element) -> List[ET.Element]:
    """Find all author elements"""
    return CDANamespaceHelper.findall_cda(root, ".//author")


def find_legal_authenticator(root: ET.Element) -> Optional[ET.Element]:
    """Find legal authenticator"""
    return CDANamespaceHelper.find_cda(root, ".//legalAuthenticator")


# Example usage and comparison
def demonstrate_namespace_helper():
    """Demonstrate the namespace helper usage"""

    print("📝 CDA NAMESPACE HELPER EXAMPLES")
    print("=" * 50)

    print("\n🔧 BEFORE (Current verbose approach):")
    print(
        "   patient_role = root.find('.//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole')"
    )
    print("   sections = root.findall('.//{urn:hl7-org:v3}section')")
    print("   title = section.find('{urn:hl7-org:v3}title')")

    print("\n✨ AFTER (With namespace helper):")
    print("   patient_role = find_patient_role(root)")
    print("   sections = find_all_sections(root)")
    print("   title = CDANamespaceHelper.find_cda(section, 'title')")

    print("\n🎯 BENEFITS:")
    print("   ✅ Much more readable code")
    print("   ✅ Less error-prone (no typos in long namespace URIs)")
    print("   ✅ Easier to maintain")
    print("   ✅ Better abstraction of CDA structure")
    print("   ✅ No external dependencies")

    print("\n🔄 MIGRATION STRATEGY:")
    print("   1. Add namespace helper to existing parser")
    print("   2. Gradually replace verbose namespace calls")
    print("   3. Create specific helper functions for common patterns")
    print("   4. Keep existing functionality working during transition")


if __name__ == "__main__":
    demonstrate_namespace_helper()
