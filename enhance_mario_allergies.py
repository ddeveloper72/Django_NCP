#!/usr/bin/env python3
"""
Enhanced Mario Borg Allergies Data Generator
Creates realistic medical practitioner-grade allergy data for testing PS Display Guidelines
"""

import os
import sys

import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import json

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session


def create_enhanced_allergy_data():
    """Create comprehensive allergy data following PS Display Guidelines"""
    return {
        "title": "Allergies and adverse reactions Document",
        "section_code": "48765-2",  # LOINC code for allergies
        "has_entries": True,
        "structured_entries": [
            {
                "allergy_type": "Drug Allergy",
                "causative_agent": "Penicillin",
                "manifestation": "Skin rash with urticaria",
                "severity": "moderate",
                "status": "active",
                "recorded_date": "2023-05-15",
                "onset_date": "2023-05-10",
                "allergy_code": "SNOMED-CT:91936005",
                "agent_code": "ATC:J01CA04",
                "atc_code": "J01CA04",
                "manifestation_code": "SNOMED-CT:271807003",
                "notes": "Patient developed widespread skin rash 30 minutes after oral administration. Resolved with antihistamine treatment.",
            },
            {
                "allergy_type": "Environmental Allergy",
                "causative_agent": "House dust mites",
                "manifestation": "Asthma and rhinitis",
                "severity": "mild",
                "status": "active",
                "recorded_date": "2022-03-20",
                "onset_date": "2020-01-01",
                "allergy_code": "SNOMED-CT:232347008",
                "agent_code": "SNOMED-CT:260167003",
                "manifestation_code": "SNOMED-CT:195967001",
                "notes": "Seasonal exacerbation. Managed with inhaled corticosteroids.",
            },
            {
                "allergy_type": "Food Allergy",
                "causative_agent": "Shellfish (Crustaceans)",
                "manifestation": "Anaphylaxis",
                "severity": "severe",
                "status": "active",
                "recorded_date": "2019-08-12",
                "onset_date": "2019-08-12",
                "allergy_code": "SNOMED-CT:91932003",
                "agent_code": "SNOMED-CT:735029006",
                "manifestation_code": "SNOMED-CT:39579001",
                "notes": "CRITICAL: Patient experienced anaphylactic shock requiring emergency epinephrine. Carries EpiPen at all times.",
                "has_anaphylaxis": True,
            },
        ],
        "medical_terminology_count": 3,
        "coded_entries_count": 3,
        "last_updated": "2024-09-30T12:00:00Z",
    }


def enhance_mario_session():
    """Enhance Mario Borg's session with realistic allergy data"""
    session_id = "1454483284"
    session_key = f"patient_match_{session_id}"
    extended_key = f"extended_patient_data_{session_id}"

    print(f"🔍 Enhancing Mario Borg session: {session_id}")

    # Find Mario's session
    all_sessions = Session.objects.all()
    mario_session = None

    for db_session in all_sessions:
        session_data = db_session.get_decoded()
        if session_key in session_data:
            mario_session = db_session
            break

    if not mario_session:
        print(f"❌ Mario's session not found!")
        return False

    # Get session data
    session_data = mario_session.get_decoded()
    match_data = session_data[session_key]

    # Ensure extended data exists
    if extended_key not in session_data:
        session_data[extended_key] = {}

    # Create enhanced processed_sections with our new allergy data
    enhanced_allergy_section = create_enhanced_allergy_data()

    # Update existing processed_sections or create new ones
    processed_sections = [
        enhanced_allergy_section,
        {
            "title": "Problem list - Reported",
            "section_code": "11450-4",
            "has_entries": True,
            "structured_entries": [
                {
                    "problem": "Essential hypertension",
                    "status": "Active",
                    "onset_date": "2020-03-15",
                    "icd10_code": "I10",
                    "notes": "Well controlled with ACE inhibitor",
                },
                {
                    "problem": "Type 2 diabetes mellitus",
                    "status": "Active",
                    "onset_date": "2018-07-22",
                    "icd10_code": "E11",
                    "notes": "Good glycemic control with metformin",
                },
            ],
            "medical_terminology_count": 2,
            "coded_entries_count": 2,
        },
        {
            "title": "History of Procedures Document",
            "section_code": "47519-4",
            "has_entries": True,
            "structured_entries": [
                {
                    "procedure": "Coronary angiography",
                    "date": "2023-02-14",
                    "performer": "Dr. Sarah Johnson",
                    "location": "Malta General Hospital",
                    "notes": "Normal coronary arteries. No significant stenosis.",
                }
            ],
            "medical_terminology_count": 1,
            "coded_entries_count": 1,
        },
        {
            "title": "History of Medication use Narrative",
            "section_code": "10160-0",
            "has_entries": True,
            "structured_entries": [
                {
                    "medication_name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "Once daily",
                    "route": "Oral",
                    "status": "active",
                    "start_date": "2020-03-15",
                    "instructions": "Take with food. Monitor blood pressure weekly.",
                },
                {
                    "medication_name": "Metformin",
                    "dosage": "500mg",
                    "frequency": "Twice daily",
                    "route": "Oral",
                    "status": "active",
                    "start_date": "2018-07-22",
                    "instructions": "Take with meals to reduce GI side effects.",
                },
            ],
            "medical_terminology_count": 2,
            "coded_entries_count": 2,
        },
        {
            "title": "History of medical device use",
            "section_code": "46264-8",
            "has_entries": False,
            "structured_entries": [],
            "medical_terminology_count": 0,
            "coded_entries_count": 0,
        },
    ]

    # Update session data
    session_data[extended_key].update(
        {
            "processed_sections": processed_sections,
            "clinical_summary": f"{len(processed_sections)} clinical sections available",
            "sections_count": len(processed_sections),
            "medical_terms_total": sum(
                s["medical_terminology_count"] for s in processed_sections
            ),
            "coded_sections_total": sum(
                s["coded_entries_count"] for s in processed_sections
            ),
            "last_enhanced": "2024-09-30T12:00:00Z",
        }
    )

    # Save updated session
    from django.contrib.sessions.backends.db import SessionStore

    store = SessionStore(session_key=mario_session.session_key)
    store.update(session_data)
    store.save()

    print(f"✅ Successfully enhanced Mario's session with medical-grade allergy data!")
    print(f"   📊 {len(processed_sections)} clinical sections")
    print(f"   🔥 Critical allergy: Shellfish anaphylaxis")
    print(f"   💊 Drug allergy: Penicillin")
    print(f"   🌿 Environmental: House dust mites")

    return True


if __name__ == "__main__":
    print(
        "🚀 Enhancing Mario Borg's clinical data with PS Display Guidelines compliant allergies..."
    )

    if enhance_mario_session():
        print(
            "\n🎉 Enhancement complete! Mario now has comprehensive allergy data for testing."
        )
        print("🔗 URL: http://127.0.0.1:8000/patients/cda/1454483284/")
    else:
        print("\n❌ Enhancement failed!")
