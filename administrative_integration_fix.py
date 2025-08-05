#!/usr/bin/env python3
"""
Administrative Data Integration Fix
Create an enhanced parser wrapper that properly transforms administrative data
for contact card compatibility and fills the gaps identified in the analysis
"""

import os
import sys
import django
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


class ContactCardCompatibleParser:
    """
    Enhanced CDA parser wrapper that transforms administrative data
    to be compatible with contact card templates and fills data gaps
    """

    def __init__(self):
        self.base_parser = EnhancedCDAXMLParser()

    def parse_cda_content(self, xml_content: str) -> Dict[str, Any]:
        """Parse CDA content and transform for contact card compatibility"""

        # Get base parser results
        result = self.base_parser.parse_cda_content(xml_content)

        # Transform administrative_data to administrative_info
        admin_data = result.get("administrative_data", {})
        result["administrative_info"] = self._transform_administrative_data(admin_data)

        return result

    def _transform_administrative_data(
        self, admin_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform administrative_data to contact card compatible format"""

        transformed = {}

        # Transform patient contact
        patient_contact = self._transform_patient_contact(
            admin_data.get("patient_contact_info", {})
        )
        if patient_contact:
            transformed["patient_contact"] = patient_contact

        # Transform legal authenticator
        legal_auth = self._transform_legal_authenticator(
            admin_data.get("legal_authenticator", {})
        )
        if legal_auth:
            transformed["legal_authenticator"] = legal_auth

        # Transform custodian
        custodian = self._transform_custodian(
            admin_data.get("custodian_organization", {})
        )
        if custodian:
            transformed["custodian"] = custodian

        # Transform authors
        authors = self._transform_authors(admin_data.get("author_information", []))
        if authors:
            transformed["authors"] = authors

        return transformed

    def _transform_patient_contact(
        self, patient_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform patient contact info"""
        if not patient_data:
            return None

        return {
            "full_name": patient_data.get("full_name", ""),
            "given_name": patient_data.get("given_name", ""),
            "family_name": patient_data.get("family_name", ""),
            "birth_date": patient_data.get("birth_date", ""),
            "gender": patient_data.get("gender", ""),
            "patient_id": patient_data.get("patient_id", ""),
            "id_authority": patient_data.get("id_authority", ""),
            "id_root": patient_data.get("id_root", ""),
            "address": self._get_primary_address(patient_data.get("addresses", [])),
            "addresses": patient_data.get("addresses", []),
            "telecoms": patient_data.get("telecoms", []),
            "phone": self._extract_phone(patient_data.get("telecoms", [])),
            "email": self._extract_email(patient_data.get("telecoms", [])),
        }

    def _transform_legal_authenticator(
        self, legal_auth_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform legal authenticator info"""
        if not legal_auth_data:
            return None

        person = legal_auth_data.get("person", {})
        org = legal_auth_data.get("organization", {})

        return {
            "full_name": person.get("full_name", ""),
            "given_name": person.get("given_name", ""),
            "family_name": person.get("family_name", ""),
            "title": person.get("title", ""),
            "role": legal_auth_data.get("role", ""),
            "signature_code": legal_auth_data.get("signature_code", ""),
            "time": legal_auth_data.get("time", ""),
            "organization": {
                "name": org.get("name", ""),
                "id": org.get("id", ""),
                "address": self._get_primary_address(org.get("addresses", [])),
                "addresses": org.get("addresses", []),
                "telecoms": org.get("telecoms", []),
            },
            "organization_name": org.get("name", ""),
            "organization_id": org.get("id", ""),
            "address": self._get_primary_address(legal_auth_data.get("addresses", [])),
            "addresses": legal_auth_data.get("addresses", []),
            "telecoms": legal_auth_data.get("telecoms", []),
            "phone": self._extract_phone(legal_auth_data.get("telecoms", [])),
            "email": self._extract_email(legal_auth_data.get("telecoms", [])),
        }

    def _transform_custodian(
        self, custodian_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Transform custodian info"""
        if not custodian_data:
            return None

        return {
            "organization_name": custodian_data.get("name", ""),
            "organization_id": custodian_data.get("id", ""),
            "organization": {
                "name": custodian_data.get("name", ""),
                "id": custodian_data.get("id", ""),
                "address": self._get_primary_address(
                    custodian_data.get("addresses", [])
                ),
                "addresses": custodian_data.get("addresses", []),
                "telecoms": custodian_data.get("telecoms", []),
            },
            "address": self._get_primary_address(custodian_data.get("addresses", [])),
            "addresses": custodian_data.get("addresses", []),
            "telecoms": custodian_data.get("telecoms", []),
            "phone": self._extract_phone(custodian_data.get("telecoms", [])),
            "email": self._extract_email(custodian_data.get("telecoms", [])),
        }

    def _transform_authors(
        self, authors_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform authors info"""
        if not authors_data:
            return []

        transformed_authors = []

        for author in authors_data:
            person = author.get("person", {})
            org = author.get("organization", {})

            transformed_author = {
                "full_name": person.get("full_name", ""),
                "given_name": person.get("given_name", ""),
                "family_name": person.get("family_name", ""),
                "title": person.get("title", ""),
                "role": author.get("role", ""),
                "time": author.get("time", ""),
                "author_type": author.get("author_type", ""),
                "organization": {
                    "name": org.get("name", ""),
                    "id": org.get("id", ""),
                    "address": self._get_primary_address(org.get("addresses", [])),
                    "addresses": org.get("addresses", []),
                    "telecoms": org.get("telecoms", []),
                },
                "organization_name": org.get("name", ""),
                "organization_id": org.get("id", ""),
                "address": self._get_primary_address(author.get("addresses", [])),
                "addresses": author.get("addresses", []),
                "telecoms": author.get("telecoms", []),
                "phone": self._extract_phone(author.get("telecoms", [])),
                "email": self._extract_email(author.get("telecoms", [])),
            }
            transformed_authors.append(transformed_author)

        return transformed_authors

    def _get_primary_address(self, addresses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get the primary address from a list of addresses"""
        if not addresses:
            return {}

        # Try to find 'primary' or 'home' address first
        for addr in addresses:
            use = addr.get("use", "").lower()
            if use in ["h", "home", "primary"]:
                return addr

        # Return first address if no primary found
        return addresses[0] if addresses else {}

    def _extract_phone(self, telecoms: List[Dict[str, Any]]) -> str:
        """Extract phone number from telecoms"""
        for telecom in telecoms:
            value = telecom.get("value", "")
            if value.startswith("tel:"):
                return value.replace("tel:", "")
        return ""

    def _extract_email(self, telecoms: List[Dict[str, Any]]) -> str:
        """Extract email from telecoms"""
        for telecom in telecoms:
            value = telecom.get("value", "")
            if value.startswith("mailto:"):
                return value.replace("mailto:", "")
        return ""


def test_integration_fix():
    """Test the integration fix with the Italian file"""

    print("🔧 TESTING ADMINISTRATIVE INTEGRATION FIX")
    print("=" * 60)

    # Use Italian file as example
    test_file = Path(
        "test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"
    )

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print(f"📄 Testing: {test_file.name}")

    # Test with our new compatible parser
    parser = ContactCardCompatibleParser()

    try:
        result = parser.parse_cda_content(xml_content)

        print(f"\n✅ PARSER INTEGRATION SUCCESS")

        # Check administrative_info structure
        admin_info = result.get("administrative_info", {})
        print(f"\n📊 ADMINISTRATIVE_INFO STRUCTURE:")
        print(f"  Total sections: {len(admin_info)}")

        for section_name, section_data in admin_info.items():
            if isinstance(section_data, list):
                print(f"  {section_name}: {len(section_data)} items")
            elif isinstance(section_data, dict):
                non_empty_fields = sum(1 for v in section_data.values() if v)
                print(f"  {section_name}: {non_empty_fields} populated fields")
            else:
                print(f"  {section_name}: {type(section_data).__name__}")

        # Test contact card compatibility
        print(f"\n🎴 CONTACT CARD COMPATIBILITY TEST:")
        test_with_contact_cards(admin_info)

        print(f"\n📈 FIELD COVERAGE ANALYSIS:")
        analyze_field_coverage(admin_info)

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()


def test_with_contact_cards(admin_info):
    """Test the transformed data with contact card templates"""

    from patient_data.templatetags.contact_cards import normalize_contact_data

    contact_types = {
        "patient_contact": "Patient Contact",
        "legal_authenticator": "Legal Authenticator",
        "custodian": "Custodian",
        "authors": "Authors",
    }

    for contact_type, display_name in contact_types.items():
        contact_data = admin_info.get(contact_type)

        if contact_type == "authors":
            if contact_data and isinstance(contact_data, list):
                print(f"  ✅ {display_name}: {len(contact_data)} available")
                try:
                    normalized = normalize_contact_data(contact_data[0])
                    name = normalized.get("full_name", "N/A")
                    org = normalized.get("organization", {}).get("name", "N/A")
                    print(f"    Template ready: {name} ({org})")
                except Exception as e:
                    print(f"    ❌ Template error: {e}")
            else:
                print(f"  ❌ {display_name}: No data available")
        else:
            if contact_data:
                print(f"  ✅ {display_name}: Available")
                try:
                    normalized = normalize_contact_data(contact_data)
                    name = normalized.get("full_name", "N/A")
                    org_name = normalized.get("organization", {}).get(
                        "name", ""
                    ) or normalized.get("organization_name", "N/A")
                    print(f"    Template ready: {name} ({org_name})")
                except Exception as e:
                    print(f"    ❌ Template error: {e}")
            else:
                print(f"  ❌ {display_name}: No data available")


def analyze_field_coverage(admin_info):
    """Analyze field coverage for the contact card requirements"""

    expected_fields = {
        "patient_contact": ["full_name", "patient_id", "address", "phone", "email"],
        "legal_authenticator": [
            "full_name",
            "organization_name",
            "signature_code",
            "time",
        ],
        "custodian": ["organization_name", "address", "phone"],
        "authors": ["full_name", "organization_name", "role", "time"],
    }

    for section_name, fields in expected_fields.items():
        section_data = admin_info.get(section_name)
        print(f"\n  {section_name.upper()} FIELD COVERAGE:")

        if section_name == "authors":
            if section_data and isinstance(section_data, list) and section_data:
                for field in fields:
                    value = section_data[0].get(field, "")
                    status = "✅" if value else "❌"
                    print(f"    {status} {field}: {'Present' if value else 'Missing'}")
            else:
                for field in fields:
                    print(f"    ❌ {field}: No authors available")
        else:
            if section_data:
                for field in fields:
                    value = section_data.get(field, "")
                    status = "✅" if value else "❌"
                    display_value = (
                        str(value)[:30] + "..." if len(str(value)) > 30 else str(value)
                    )
                    print(
                        f"    {status} {field}: {display_value if value else 'Missing'}"
                    )
            else:
                for field in fields:
                    print(f"    ❌ {field}: Section not available")


if __name__ == "__main__":
    test_integration_fix()
