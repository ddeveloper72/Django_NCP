#!/usr/bin/env python
"""Search all sessions for patient data"""
import os
import sys

import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import json

from django.contrib.sessions.models import Session

print("=== SEARCHING ALL SESSIONS FOR PATIENT DATA ===")

found_patients = {}
sessions_with_data = 0

for session in Session.objects.all():
    try:
        session_data = session.get_decoded()

        # Look for different patient data keys
        patient_keys = [
            "patient_id",
            "current_patient_data",
            "patient_match_117302",
            "patient_data",
        ]

        has_patient_data = False
        session_info = {
            "session_key": session.session_key,
            "expire_date": session.expire_date,
            "patients": [],
        }

        for key, value in session_data.items():
            if "patient" in key.lower() or "clinical" in key.lower():
                has_patient_data = True

                if key == "current_patient_data" and isinstance(value, dict):
                    personal_info = value.get("personal_info", {})
                    name = personal_info.get("name", "Unknown")
                    patient_id = personal_info.get("patient_id", "Unknown")
                    session_info["patients"].append(
                        {"name": name, "patient_id": patient_id, "data_key": key}
                    )
                elif key.startswith("patient_match_") and isinstance(value, dict):
                    # Extract patient ID from key
                    patient_id = key.replace("patient_match_", "")
                    personal_info = value.get("personal_info", {})
                    name = personal_info.get("name", "Unknown")
                    session_info["patients"].append(
                        {"name": name, "patient_id": patient_id, "data_key": key}
                    )

        if has_patient_data:
            sessions_with_data += 1
            print(f"\n📋 Session: {session.session_key}")
            print(f"   Expires: {session.expire_date}")
            for patient in session_info["patients"]:
                print(f"   👤 Patient: {patient['name']} (ID: {patient['patient_id']})")
                print(f"      Data key: {patient['data_key']}")

                # If this is patient 117302 (our working patient), show the session URL
                if patient["patient_id"] == "117302":
                    print(
                        f"      🔗 Session URL: /patients/cda/{session.session_key}/L3/"
                    )

    except Exception as e:
        print(f"Error processing session {session.session_key}: {e}")
        continue

print(f"\n📊 Summary:")
print(f"   Total sessions: {Session.objects.count()}")
print(f"   Sessions with patient data: {sessions_with_data}")
print(f"\n💡 Note: Session 2264861458 from your URL doesn't exist in the database.")
print(f"   The enhanced display works by searching ALL sessions for the patient ID.")
