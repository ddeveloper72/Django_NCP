#!/usr/bin/env python
"""Setup Mario session for clinical data debugger testing"""

import os

import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.utils import timezone


def setup_mario_session():
    """Setup Mario's session data for clinical data debugger"""

    session_id = "1215081612"

    print(f"Setting up session for ID: {session_id}")

    # Read Mario's CDA content
    cda_file_path = "test_data/eu_member_states_backup/MT/2025-03-18T15-09-34.313665Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.0.0)_NOT-TESTED.xml"

    try:
        with open(cda_file_path, "r", encoding="utf-8") as f:
            mario_cda_content = f.read()
        print(f"✅ Loaded CDA file: {cda_file_path}")
    except FileNotFoundError:
        print(f"❌ CDA file not found: {cda_file_path}")
        return False

    # Create a new session
    session_store = SessionStore()

    # Set up the session data structure expected by clinical_data_debugger
    session_key = f"patient_match_{session_id}"

    session_data = {
        session_key: {
            "patient_data": {
                "patient_id": "9999002M",  # Mario's actual patient ID
                "url_patient_id": session_id,  # Session ID for URL routing
                "given_name": "Mario",
                "family_name": "Borg",
                "country_code": "MT",
            },
            "l3_cda_content": mario_cda_content,  # Store the CDA content
            "country_code": "MT",
            "confidence_score": 95,
            "has_l1": False,
            "has_l3": True,
            "extraction_timestamp": "2024-12-19T10:30:00Z",
        }
    }

    # Save to session
    session_store.update(session_data)
    session_store.save()

    print(f"✅ Session created with key: {session_store.session_key}")
    print(f"📋 Patient match key: {session_key}")
    print(
        f"🌐 Access URL: http://127.0.0.1:8000/patient_data/debug/clinical/{session_id}/"
    )

    # Also save with the specific session key if different
    if session_store.session_key != session_id:
        # Try to force the session key to match what we want
        print(f"🔄 Session key differs, creating with exact ID...")

        # Create session in database with specific key
        session_obj = Session(
            session_key=session_id,
            session_data=session_store.encode(session_data),
            expire_date=timezone.now() + timezone.timedelta(days=1),
        )
        try:
            session_obj.save()
            print(f"✅ Forced session with exact key: {session_id}")
        except Exception as e:
            print(f"⚠️ Could not force exact session key: {e}")

    return True


if __name__ == "__main__":
    if setup_mario_session():
        print("\n🎉 Mario session setup complete!")
        print("You can now access the clinical data debugger.")
    else:
        print("\n❌ Failed to setup Mario session.")
