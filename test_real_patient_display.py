#!/usr/bin/env python
"""
Test real patient display in Django application
"""
import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.models import PatientData, PatientIdentifier
from patient_data.services.patient_search_service import EUPatientSearchService


def test_real_patient_display():
    """Test how real patients from database are displayed"""
    print("=== Real Patient Display Test ===")

    # Check if we have any actual patients in database
    patient_count = PatientData.objects.count()
    identifier_count = PatientIdentifier.objects.count()

    print(
        f"Database contains {patient_count} patients and {identifier_count} identifiers"
    )

    if patient_count > 0:
        # Get first few patients
        patients = PatientData.objects.all()[:3]

        for patient in patients:
            print(f"\nPatient: {patient.given_name} {patient.family_name}")
            print(f"  Database ID: {patient.id}")
            print(f"  Birth Date: {patient.birth_date}")

            # Check patient identifier
            if patient.patient_identifier:
                print(f"  Patient Identifier: {patient.patient_identifier.patient_id}")
                print(
                    f"  Home Member State: {patient.patient_identifier.home_member_state}"
                )
                print(f"  ID Extension: {patient.patient_identifier.id_extension}")
                print(f"  ID Root: {patient.patient_identifier.id_root}")

    # Check what we actually have in terms of identifiers
    print("\n=== All Patient Identifiers ===")
    identifiers = PatientIdentifier.objects.all()
    for identifier in identifiers:
        print(
            f"ID: {identifier.patient_id}, Root: {identifier.id_root}, Extension: {identifier.id_extension}"
        )

    print("\n=== Template Context Test ===")
    # Test how a patient would appear in template context
    if patient_count > 0:
        patient = PatientData.objects.first()
        print(f"Patient for template: {patient.given_name} {patient.family_name}")
        print(f"  Internal ID: {patient.id}")

        # Simulate template context like it's done in views.py
        patient_context = {
            "id": patient.id,
            "given_name": patient.given_name,
            "family_name": patient.family_name,
            "birth_date": patient.birth_date,
            "patient_identifiers": [],
        }

        if patient.patient_identifier:
            identifier_info = {
                "extension": patient.patient_identifier.id_extension
                or patient.patient_identifier.patient_id,
                "root": patient.patient_identifier.id_root,
                "assigningAuthorityName": (
                    patient.patient_identifier.home_member_state.country_name
                    if patient.patient_identifier.home_member_state
                    else ""
                ),
                "displayable": "true",
            }
            patient_context["patient_identifiers"].append(identifier_info)

        print(f"  Template Context: {patient_context}")

        # Test template logic
        if patient_context["patient_identifiers"]:
            for identifier in patient_context["patient_identifiers"]:
                if identifier.get("assigningAuthorityName"):
                    display_text = f"{identifier['assigningAuthorityName']}: {identifier['extension']}"
                else:
                    display_text = (
                        f"Patient ID ({identifier['root']}): {identifier['extension']}"
                    )
                print(f"  Template would show: {display_text}")
        else:
            print(f"  Template would show: ID: {patient_context['id']}")

    return True

    return True


if __name__ == "__main__":
    test_real_patient_display()
