#!/usr/bin/env python
"""
Debug session data for Mario PINO to see what identifiers are stored
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

from django.contrib.sessions.models import Session
from patient_data.models import PatientData
import json


def debug_mario_session_data():
    """Debug session data for Mario PINO"""
    print("=== Mario PINO Session Data Debug ===")
    print()

    # Get Mario PINO from database
    mario_patients = PatientData.objects.filter(given_name="Mario", family_name="PINO")

    if not mario_patients.exists():
        print("❌ No Mario PINO patients found in database")
        return False

    mario = mario_patients.first()
    print(f"✅ Found Mario PINO (DB ID: {mario.id})")
    print(f"   Name: {mario.given_name} {mario.family_name}")
    print(f"   Birth Date: {mario.birth_date}")

    # Look for session data with Mario's ID
    session_key = f"patient_match_{mario.id}"
    print(f"\n🔍 Looking for session key: {session_key}")

    # Check all sessions for this key
    sessions = Session.objects.all()
    found_session = False

    for session in sessions:
        session_data = session.get_decoded()
        if session_key in session_data:
            found_session = True
            print(f"✅ Found session data!")
            print(f"   Session ID: {session.session_key}")
            print(f"   Expire Date: {session.expire_date}")

            match_data = session_data[session_key]
            print(f"\n📊 Session Match Data Structure:")
            print(f"   Keys: {list(match_data.keys())}")

            if "patient_data" in match_data:
                patient_data = match_data["patient_data"]
                print(f"\n👤 Patient Data:")
                print(
                    f"   primary_patient_id: {patient_data.get('primary_patient_id', 'NOT_SET')}"
                )
                print(
                    f"   secondary_patient_id: {patient_data.get('secondary_patient_id', 'NOT_SET')}"
                )
                print(
                    f"   patient_identifiers: {patient_data.get('patient_identifiers', 'NOT_SET')}"
                )

                if patient_data.get("patient_identifiers"):
                    print(f"\n🆔 Patient Identifiers Detail:")
                    for idx, identifier in enumerate(
                        patient_data["patient_identifiers"]
                    ):
                        print(
                            f"   [{idx}] Extension: {identifier.get('extension', 'N/A')}"
                        )
                        print(f"       Root: {identifier.get('root', 'N/A')}")
                        print(
                            f"       Authority: {identifier.get('assigningAuthorityName', 'N/A')}"
                        )
                        print(
                            f"       Displayable: {identifier.get('displayable', 'N/A')}"
                        )
                        print(f"       Type: {identifier.get('type', 'N/A')}")
                        print()

            if "cda_content" in match_data:
                cda_length = len(match_data["cda_content"])
                print(f"\n📄 CDA Content: {cda_length} characters")

                # Check if the CDA contains the expected identifiers
                cda_content = match_data["cda_content"]
                if "NCPNPH80A01H501K" in cda_content:
                    print("   ✅ Contains NCPNPH80A01H501K identifier")
                else:
                    print("   ❌ Does NOT contain NCPNPH80A01H501K identifier")

                if "Ministero Economia e Finanze" in cda_content:
                    print("   ✅ Contains 'Ministero Economia e Finanze' authority")
                else:
                    print(
                        "   ❌ Does NOT contain 'Ministero Economia e Finanze' authority"
                    )

            break

    if not found_session:
        print("❌ No session data found for Mario PINO")
        print("\n💡 Available session keys:")
        all_keys = set()
        for session in sessions:
            session_data = session.get_decoded()
            all_keys.update(session_data.keys())

        for key in sorted(all_keys):
            if "patient_match" in key:
                print(f"   {key}")

    return found_session


if __name__ == "__main__":
    debug_mario_session_data()
