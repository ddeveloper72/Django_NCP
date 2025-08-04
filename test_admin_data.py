#!/usr/bin/env python
"""Test administrative data extraction"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.cda_translation_service import CDATranslationService


def test_admin_extraction():
    """Test administrative data extraction"""

    # Initialize the service
    service = CDATranslationService()

    # Test with sample CDA content that matches the view structure
    sample_cda = """<ClinicalDocument xmlns="urn:hl7-org:v3">
        <recordTarget>
            <patientRole>
                <addr use="HP">
                    <streetAddressLine>123 Rue de la Paix</streetAddressLine>
                    <city>Luxembourg</city>
                    <postalCode>1234</postalCode>
                    <country>LU</country>
                </addr>
                <telecom value="tel:+352123456789" use="HP"/>
                <telecom value="mailto:patient@example.lu" use="HP"/>
            </patientRole>
        </recordTarget>
        <author>
            <assignedAuthor>
                <assignedPerson>
                    <name>
                        <prefix>Dr.</prefix>
                        <given>Marie</given>
                        <family>Dubois</family>
                    </name>
                </assignedPerson>
                <representedOrganization>
                    <name>Centre Hospitalier de Luxembourg</name>
                    <addr>
                        <streetAddressLine>4 Rue Nicolas Ernest Barblé</streetAddressLine>
                        <city>Luxembourg</city>
                        <postalCode>1210</postalCode>
                        <country>LU</country>
                    </addr>
                    <telecom value="tel:+35244111" use="WP"/>
                </representedOrganization>
            </assignedAuthor>
        </author>
        <custodian>
            <assignedCustodian>
                <representedCustodianOrganization>
                    <name>Direction de la Santé - Luxembourg</name>
                    <addr>
                        <streetAddressLine>Villa Louvigny, Allée Marconi</streetAddressLine>
                        <city>Luxembourg</city>
                        <postalCode>2120</postalCode>
                        <country>LU</country>
                    </addr>
                </representedCustodianOrganization>
            </assignedCustodian>
        </custodian>
        <legalAuthenticator>
            <assignedEntity>
                <assignedPerson>
                    <name>
                        <prefix>Dr.</prefix>
                        <given>Jean</given>
                        <family>Mueller</family>
                    </name>
                </assignedPerson>
            </assignedEntity>
        </legalAuthenticator>
    </ClinicalDocument>"""

    # Extract administrative data
    print("Testing administrative data extraction...")
    admin_data = service.extract_administrative_data(sample_cda)

    # Print what we get
    print(f"Admin data extracted:")
    print(
        f"Patient contact addresses: {len(admin_data.patient_contact_info.addresses)}"
    )
    print(f"Author HCP name: {admin_data.author_hcp.family_name}")
    print(f"Custodian: {admin_data.custodian_organization.name}")
    print(
        f"Has data: {bool(admin_data.patient_contact_info.addresses or admin_data.author_hcp.family_name)}"
    )

    # Print addresses if any
    if admin_data.patient_contact_info.addresses:
        for i, addr in enumerate(admin_data.patient_contact_info.addresses):
            print(f'  Address {i+1}: {addr.get("street", "")}, {addr.get("city", "")}')

    # Print telecoms if any
    if admin_data.patient_contact_info.telecoms:
        for i, tel in enumerate(admin_data.patient_contact_info.telecoms):
            print(f'  Telecom {i+1}: {tel.get("value", "")} ({tel.get("use", "")})')


if __name__ == "__main__":
    test_admin_extraction()
