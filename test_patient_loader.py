"""
Test script to verify patient data loading functionality
"""

import os
import sys
import django

# Setup Django environment
sys.path.append("C:/Users/Duncan/VS_Code_Projects/django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from patient_data.patient_loader import patient_loader
from patient_data.models import MemberState


def test_patient_loader():
    print("Testing Patient Data Loader...")
    print("=" * 50)

    # Test available OIDs
    oids = patient_loader.get_available_oids()
    print(f"Available OIDs: {oids}")

    for oid in oids:
        print(f"\nTesting OID: {oid}")
        print("-" * 30)

        # Get patients for this OID
        patients = patient_loader.get_patients_for_oid(oid)
        print(f"Available patients: {patients}")

        # Test loading first patient
        if patients:
            patient_id = patients[0]
            patient_info = patient_loader.load_patient_data(oid, patient_id)

            if patient_info:
                print(f"Patient loaded successfully:")
                print(f"  Name: {patient_info.full_name}")
                print(f"  Birth Date: {patient_info.birth_date_formatted}")
                print(f"  Gender: {patient_info.administrative_gender}")
                print(f"  Country: {patient_info.country}")
                print(f"  Address: {patient_info.street}, {patient_info.city}")

                # Test patient search
                found, info, message = patient_loader.search_patient(
                    oid, patient_id, patient_info.birth_date_formatted
                )
                print(f"  Search test: {message} (Found: {found})")
            else:
                print(f"  Failed to load patient data")

    print("\nTesting Member State Integration...")
    print("-" * 40)

    # Test member state integration
    member_states = MemberState.objects.filter(sample_data_oid__isnull=False)
    for state in member_states:
        print(f"Member State: {state.country_name}")
        print(f"  Country Code: {state.country_code}")
        print(f"  Sample OID: {state.sample_data_oid}")

        if state.sample_data_oid:
            patients = patient_loader.get_patients_for_oid(state.sample_data_oid)
            print(f"  Available patients: {len(patients)}")


if __name__ == "__main__":
    test_patient_loader()
