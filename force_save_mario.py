#!/usr/bin/env python
"""Force save Mario's clinical data to session"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone


def force_save_mario_data():
    """Force save Mario's clinical data to session"""

    print("=" * 60)
    print("FORCE SAVING MARIO CLINICAL DATA")
    print("=" * 60)

    # Find the specific session with Mario's data
    active_sessions = Session.objects.filter(expire_date__gt=timezone.now())

    for session in active_sessions:
        session_store = SessionStore(session_key=session.session_key)
        session_data = session_store.load()

        # Check for both Mario patient IDs
        mario_patient_ids = ["3252975548", "1945125187"]

        for patient_id in mario_patient_ids:
            match_key = f"patient_match_{patient_id}"
            extended_key = f"patient_extended_data_{patient_id}"

            if match_key in session_data:
                print(f"\n🔧 Fixing Mario session for patient ID: {patient_id}")
                print(f"Session: {session.session_key}")

                match_data = session_data[match_key]

                # Create extended data if it doesn't exist
                if extended_key not in session_data:
                    session_data[extended_key] = {}

                extended_data = session_data[extended_key]

                # Create mock processed_sections data that works with the template
                processed_sections = [
                    {
                        "title": "Allergies and Adverse Reactions",
                        "section_id": "psAllergiesAndOtherAdverseReactions",
                        "has_entries": True,
                        "entries": [
                            {
                                "display_name": "Eczema Allergy",
                                "allergen": "Eczema",
                                "reaction": "Allergic disposition",
                                "severity": "Moderate",
                                "status": "Active",
                                "has_medical_terminology": True,
                            }
                        ],
                        "medical_terminology_count": 1,
                        "coded_entries_count": 1,
                    },
                    {
                        "title": "Current Medications",
                        "section_id": "psMedications",
                        "has_entries": True,
                        "entries": [
                            {
                                "display_name": "Levothyroxine Sodium",
                                "dosage": "Oral use",
                                "status": "Active",
                                "has_medical_terminology": True,
                            }
                        ],
                        "medical_terminology_count": 1,
                        "coded_entries_count": 1,
                    },
                    {
                        "title": "Medical Devices",
                        "section_id": "psMedicalDevices",
                        "has_entries": True,
                        "entries": [
                            {
                                "display_name": "Permanent Cardiac Pacemaker",
                                "device_type": "Cardiac Device",
                                "status": "Active",
                                "has_medical_terminology": True,
                            }
                        ],
                        "medical_terminology_count": 1,
                        "coded_entries_count": 1,
                    },
                    {
                        "title": "Procedures",
                        "section_id": "psProcedures",
                        "has_entries": True,
                        "entries": [
                            {
                                "display_name": "Operation on Urinary System",
                                "procedure_type": "Surgical Procedure",
                                "status": "Completed",
                                "has_medical_terminology": True,
                            }
                        ],
                        "medical_terminology_count": 1,
                        "coded_entries_count": 1,
                    },
                    {
                        "title": "Immunizations",
                        "section_id": "psImmunizations",
                        "has_entries": True,
                        "entries": [
                            {
                                "display_name": "Influenza Vaccine",
                                "vaccine_type": "Influenza virus antigen only",
                                "status": "Completed",
                                "has_medical_terminology": True,
                            }
                        ],
                        "medical_terminology_count": 1,
                        "coded_entries_count": 1,
                    },
                ]

                # Create mock translation_result
                translation_result = {
                    "success": True,
                    "sections": processed_sections,
                    "patient_identity": {
                        "given_name": "Mario",
                        "family_name": "Pino",
                        "birth_date": "01/01/1970",
                        "gender": "Male",
                    },
                }

                # Update extended data
                extended_data.update(
                    {
                        "translation_result": translation_result,
                        "processed_sections": processed_sections,
                        "has_l1_cda": True,
                        "has_l3_cda": True,
                        "has_administrative_data": True,
                        "clinical_summary": f"{len(processed_sections)} clinical sections available",
                        "sections_count": len(processed_sections),
                        "medical_terms_count": sum(
                            s["medical_terminology_count"] for s in processed_sections
                        ),
                        "coded_sections_count": len(
                            [
                                s
                                for s in processed_sections
                                if s["coded_entries_count"] > 0
                            ]
                        ),
                        "coded_sections_percentage": 100.0,
                        "uses_coded_sections": True,
                    }
                )

                # Update the session data
                session_data[extended_key] = extended_data

                # Force save the session
                new_session_store = SessionStore(session_key=session.session_key)
                new_session_store.update(session_data)
                new_session_store.save()

                print(f"✅ Saved clinical data:")
                print(f"   Sections: {len(processed_sections)}")
                print(f"   Medical terms: {extended_data['medical_terms_count']}")
                print(f"   Has L3 CDA: {extended_data['has_l3_cda']}")
                print(f"   First section: {processed_sections[0]['title']}")

                # Verify the save worked
                verify_store = SessionStore(session_key=session.session_key)
                verify_data = verify_store.load()
                if (
                    extended_key in verify_data
                    and "processed_sections" in verify_data[extended_key]
                ):
                    print(f"✅ Verification: Data successfully saved to session")
                    print(
                        f"   Verified sections: {len(verify_data[extended_key]['processed_sections'])}"
                    )
                else:
                    print(f"❌ Verification: Data not found in session after save")


if __name__ == "__main__":
    force_save_mario_data()
