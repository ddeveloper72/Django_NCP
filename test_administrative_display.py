#!/usr/bin/env python
"""
Test Administrative Data Display
Tests the complete administrative data display in Django view
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append(".")

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from patient_data.models import PatientData, MemberState
from patient_data.services.cda_translation_service import CDATranslationService


def test_administrative_display():
    """Test administrative data display in Django view"""
    print("=== ADMINISTRATIVE DATA DISPLAY TEST ===")

    try:
        # Create test client
        client = Client()

        # Create or get existing member state and patient
        malta, created = MemberState.objects.get_or_create(
            country_code="MT", defaults={"country_name": "Malta"}
        )

        # Find or create patient for testing
        patient = PatientData.objects.filter(family_name="Borg").first()

        if not patient:
            print("No test patient found - creating mock patient")
            # You would create a patient here if needed
            return

        print(
            f"Testing with patient: {patient.given_name} {patient.family_name} (ID: {patient.id})"
        )

        # Test with actual Malta CDA document
        cda_file = "test_data/eu_member_states/MT/Mario_Borg_9999002M.xml"

        if not os.path.exists(cda_file):
            print(f"ERROR: Test file not found: {cda_file}")
            return

        # Read the CDA file
        with open(cda_file, "r", encoding="utf-8") as f:
            cda_content = f.read()

        # Test the translation service directly
        translation_service = CDATranslationService(target_language="en")
        admin_data = translation_service.extract_administrative_data(cda_content)

        print("\n--- TRANSLATION SERVICE RESULTS ---")
        print(
            f"Patient Contact Addresses: {len(admin_data.patient_contact_info.addresses)}"
        )
        print(
            f"Patient Contact Telecoms: {len(admin_data.patient_contact_info.telecoms)}"
        )
        print(
            f"Author HCP: '{admin_data.author_hcp.given_name}' '{admin_data.author_hcp.family_name}'"
        )
        print(f"Author Organization: '{admin_data.author_hcp.organization.name}'")
        print(f"Custodian: '{admin_data.custodian_organization.name}'")

        # Check if we have data
        has_admin_data = bool(
            admin_data.patient_contact_info.addresses
            or admin_data.author_hcp.family_name
            or admin_data.legal_authenticator.family_name
            or admin_data.custodian_organization.name
        )

        print(f"\nHas administrative data: {has_admin_data}")

        if has_admin_data:
            print("✅ Administrative data extraction successful!")

            # Create a mock session with our CDA data for testing the view
            session_data = {
                f"patient_match_{patient.id}": {
                    "file_path": cda_file,
                    "country_code": "MT",
                    "confidence_score": 0.95,
                    "cda_content": cda_content,
                    "l3_cda_content": cda_content,
                    "l1_cda_content": "",
                    "preferred_cda_type": "L3",
                    "has_l1": False,
                    "has_l3": True,
                }
            }

            # Add session data
            session = client.session
            session.update(session_data)
            session.save()

            print("\n--- TESTING DJANGO VIEW ---")
            response = client.get(f"/patient_data/patient/{patient.id}/cda/")

            if response.status_code == 200:
                print("✅ Django view responds successfully!")

                # Check if administrative section is in the response
                content = response.content.decode("utf-8")

                if (
                    "administrative-section" in content
                    or "admin-contact-card" in content
                ):
                    print("✅ Administrative section found in HTML!")
                else:
                    print("⚠️  Administrative section not found in HTML")

                if "Administrative Information" in content:
                    print("✅ Administrative Information section title found!")
                else:
                    print("⚠️  Administrative Information section title not found")

                # Check for specific administrative data
                if admin_data.patient_contact_info.addresses:
                    first_addr = admin_data.patient_contact_info.addresses[0]
                    if first_addr.get("city") and first_addr["city"] in content:
                        print(f"✅ Patient city '{first_addr['city']}' found in HTML!")
                    else:
                        print(
                            f"⚠️  Patient city '{first_addr.get('city')}' not found in HTML"
                        )

                if (
                    admin_data.custodian_organization.name
                    and admin_data.custodian_organization.name in content
                ):
                    print(
                        f"✅ Custodian organization '{admin_data.custodian_organization.name}' found in HTML!"
                    )
                else:
                    print(
                        f"⚠️  Custodian organization '{admin_data.custodian_organization.name}' not found in HTML"
                    )

            else:
                print(f"❌ Django view failed with status: {response.status_code}")
                print(f"Response content: {response.content.decode('utf-8')[:500]}")
        else:
            print("⚠️  No administrative data found - extraction may need debugging")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_administrative_display()
