#!/usr/bin/env python
"""
Enhanced allergies data for Diana Ferreira (Portuguese patient)
Session ID: 1703022298
Patient ID: 2-1234-W7
"""
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from datetime import datetime

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session


def enhance_diana_session():
    """Add enhanced allergies data to Diana's session"""
    session_id = "1703022298"
    session_key = f"patient_match_{session_id}"

    print(f"=== ADDING ENHANCED ALLERGIES TO DIANA SESSION ({session_id}) ===")

    # Find the session
    found_session = None
    for session in Session.objects.all():
        try:
            session_store = SessionStore(session_key=session.session_key)
            session_data = session_store.load()
            if session_key in session_data:
                found_session = session_store
                print(f"Found Diana's session: {session.session_key[:20]}...")
                break
        except Exception:
            continue

    if not found_session:
        print("No session found for Diana!")
        return

    # Get match data
    match_data = found_session[session_key]
    print(f"Session keys: {list(match_data.keys())}")

    # Add comprehensive Portuguese allergies data following PS Display Guidelines
    enhanced_allergies = [
        {
            "substance": "Aspirin",
            "code": "387207008",
            "coding_system": "SNOMED-CT",
            "atc_code": "N02BA01",
            "severity": "severe",
            "severity_code": "24484000",
            "manifestation": ["Asthma bronchiale", "Angioedema"],
            "manifestation_codes": ["195967001", "41291007"],
            "onset_date": "2019-06-10",
            "last_occurrence": "2023-11-15",
            "status": "active",
            "certainty": "confirmed",
            "source": "patient_reported",
            "ps_guidelines_compliant": True,
            "loinc_section": "48765-2",
            "notes": "Patient experienced severe bronchospasm after taking aspirin",
        },
        {
            "substance": "Latex",
            "code": "111088007",
            "coding_system": "SNOMED-CT",
            "severity": "moderate",
            "severity_code": "6736007",
            "manifestation": ["Contact dermatitis", "Urticaria"],
            "manifestation_codes": ["40275004", "126485001"],
            "onset_date": "2020-01-22",
            "last_occurrence": "2024-03-08",
            "status": "active",
            "certainty": "confirmed",
            "source": "clinician_verified",
            "ps_guidelines_compliant": True,
            "loinc_section": "48765-2",
            "notes": "Occupational exposure as healthcare worker",
        },
        {
            "substance": "Peanuts",
            "code": "762952008",
            "coding_system": "SNOMED-CT",
            "severity": "severe",
            "severity_code": "24484000",
            "manifestation": ["Anaphylaxis", "Swelling of throat"],
            "manifestation_codes": ["39579001", "162305006"],
            "onset_date": "1995-08-14",
            "last_occurrence": "2021-12-20",
            "status": "active",
            "certainty": "confirmed",
            "source": "allergy_test",
            "emergency_intervention": "EpiPen required",
            "ps_guidelines_compliant": True,
            "loinc_section": "48765-2",
            "notes": "Childhood onset, confirmed by allergy testing",
        },
        {
            "substance": "Iodine contrast",
            "code": "293586001",
            "coding_system": "SNOMED-CT",
            "severity": "mild",
            "severity_code": "255604002",
            "manifestation": ["Nausea", "Skin rash"],
            "manifestation_codes": ["422587007", "271807003"],
            "onset_date": "2022-04-18",
            "last_occurrence": "2022-04-18",
            "status": "active",
            "certainty": "probable",
            "source": "clinician_observed",
            "ps_guidelines_compliant": True,
            "loinc_section": "48765-2",
            "notes": "Occurred during CT scan with contrast",
        },
    ]

    # Add enhanced allergies to match data
    match_data["enhanced_allergies"] = enhanced_allergies
    match_data["enhanced_allergies_added"] = datetime.now().isoformat()
    match_data["enhanced_allergies_country"] = "PT"
    match_data["enhanced_allergies_patient"] = "Diana Ferreira"

    # Save back to session
    found_session[session_key] = match_data
    found_session.save()

    print(f"Added {len(enhanced_allergies)} enhanced allergies:")
    for allergy in enhanced_allergies:
        print(
            f"  - {allergy['substance']} ({allergy['severity']}) - {allergy['notes']}"
        )
    print("Enhanced allergies data saved to Diana's session!")

    return True


if __name__ == "__main__":
    enhance_diana_session()
