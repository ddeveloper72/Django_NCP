#!/usr/bin/env python
"""Detailed inspection of L3 CDA Mario Pino session data"""

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
import json


def inspect_l3_mario_session():
    """Detailed inspection of session data for L3 CDA Mario Pino"""

    target_patient_id = "1845729621"  # L3 CDA Mario from screenshot URL

    print("=" * 70)
    print(f"DETAILED INSPECTION: L3 CDA MARIO PINO (Patient ID: {target_patient_id})")
    print("=" * 70)

    # Get all active sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())

    for session in sessions:
        store = SessionStore(session_key=session.session_key)
        session_data = store.load()

        # Check for any keys related to our target patient ID
        relevant_keys = []
        for key in session_data.keys():
            if target_patient_id in key:
                relevant_keys.append(key)

        if relevant_keys:
            print(f"\n🔍 Session: {session.session_key}")
            print(f"Relevant keys found: {relevant_keys}")

            for key in relevant_keys:
                print(f"\n📋 Content of '{key}':")
                data = session_data[key]
                if isinstance(data, dict):
                    print(json.dumps(data, indent=2, default=str))
                else:
                    print(f"Type: {type(data)}, Value: {data}")


if __name__ == "__main__":
    inspect_l3_mario_session()
