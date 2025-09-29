#!/usr/bin/env python3
"""
Test Patient URLs
Get available patient session IDs to test healthcare provider fix
"""

import os
import sys
from pathlib import Path

import django

# Setup Django environment
project_root = Path(__file__).parent
sys.path.append(str(project_root))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.models import PatientData, PatientSession


def get_available_patients():
    """Get available patient sessions for testing"""
    print("=== Available Patient Sessions ===")

    try:
        sessions = PatientSession.objects.all()[:5]  # Get first 5 sessions
        print(f"Found {sessions.count()} total sessions, showing first 5:")

        for session in sessions:
            print(f"Session ID: {session.session_id}")
            print(f"User: {session.user}")
            print(f"Status: {session.status}")
            print(f"Created: {session.created_at}")
            print(f"URL: http://localhost:8000/patient/{session.session_id}/")
            print("-" * 50)

    except Exception as e:
        print(f"Error getting sessions: {e}")

    print("\n=== Available Patient Data ===")
    try:
        patients = PatientData.objects.all()[:5]  # Get first 5 patients
        print(f"Found {patients.count()} total patient records, showing first 5:")

        for patient in patients:
            print(f"Patient ID: {patient.patient_id}")
            print(f"National ID: {patient.national_id}")
            print(f"Family Name: {patient.family_name}")
            print(f"Given Name: {patient.given_name}")
            print(f"URL: http://localhost:8000/patient/{patient.patient_id}/")
            print("-" * 50)

    except Exception as e:
        print(f"Error getting patient data: {e}")


if __name__ == "__main__":
    get_available_patients()
