"""
Cleanup Script: Clear Patient Sessions to Remove Old FHIR Data
================================================================

This script clears patient session data to force re-fetching from Azure FHIR.
Old social history observations have generic text like "Social history observation".
New observations (after FHIR converter fix) have proper LOINC display names like
"Tobacco smoking status" or "Alcoholic drinks per day".

The FHIR converter AI agent has been updated to include proper code.text values.
Clearing sessions will force Django NCP to re-fetch with the updated data.

Usage:
    python cleanup_generic_social_history.py [--patient-id PATIENT_ID] [--all]

Options:
    --patient-id   Clear session for specific patient (by Azure patient ID)
    --all          Clear all patient sessions (use with caution)
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.utils import timezone
import argparse
import json


def clear_patient_sessions(patient_id=None, clear_all=False):
    """
    Clear patient session data to force re-fetch from Azure FHIR
    
    Args:
        patient_id: Azure patient ID to clear (e.g., '98ce4472-30a5-43b2-8b37-85c86fc53772')
        clear_all: If True, clear all patient sessions
    """
    print("=" * 80)
    print("Patient Session Cleanup Script")
    print("=" * 80)
    print()
    
    if not patient_id and not clear_all:
        print("❌ Error: Must provide either --patient-id or --all")
        print()
        print("Examples:")
        print("  python cleanup_generic_social_history.py --patient-id 98ce4472-30a5-43b2-8b37-85c86fc53772")
        print("  python cleanup_generic_social_history.py --all")
        print()
        return
    
    # Get all active sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    total_sessions = sessions.count()
    sessions_to_clear = []
    
    if clear_all:
        print(f"⚠️  WARNING: About to clear ALL {total_sessions} active session(s)")
        print()
        response = input("Are you sure? Type 'yes' to confirm: ")
        
        if response.lower() == 'yes':
            count = sessions.delete()[0]
            print()
            print(f"✅ Cleared {count} session(s)")
            print()
            print("Next steps:")
            print("  1. Navigate to patient search in Django NCP")
            print("  2. Search for patient (e.g., Country: Portugal, ID: 2-1234-W7)")
            print("  3. System will re-fetch from Azure FHIR with proper LOINC names")
            print()
        else:
            print()
            print("❌ Cleanup cancelled")
            print()
        return
    
    # Clear specific patient session
    print(f"🔍 Searching for sessions with patient ID: {patient_id}")
    print()
    
    for session in sessions:
        try:
            session_data = session.get_decoded()
            # Check if session contains this patient's data
            if 'patient_summary' in session_data:
                summary = session_data['patient_summary']
                if isinstance(summary, dict):
                    stored_patient_id = summary.get('patient_id')
                    if stored_patient_id == patient_id:
                        sessions_to_clear.append(session)
                        print(f"  Found session: {session.session_key[:20]}...")
        except Exception as e:
            # Skip corrupted sessions
            continue
    
    if not sessions_to_clear:
        print("✅ No sessions found for this patient")
        print("   Patient data may already be cleared or not cached")
        print()
        return
    
    print()
    print(f"Found {len(sessions_to_clear)} session(s) containing patient data")
    print()
    
    response = input(f"Clear {len(sessions_to_clear)} session(s)? (yes/no): ")
    
    if response.lower() == 'yes':
        for session in sessions_to_clear:
            session.delete()
        
        print()
        print(f"✅ Cleared {len(sessions_to_clear)} session(s)")
        print()
        print("Next steps:")
        print("  1. Navigate to patient search in Django NCP")
        print("  2. Search for patient (e.g., Country: Portugal, ID: 2-1234-W7)")
        print("  3. System will re-fetch from Azure FHIR with proper LOINC names:")
        print("     - 'Tobacco smoking status'")
        print("     - 'Alcoholic drinks per day'")
        print("     - etc.")
        print()
    else:
        print()
        print("❌ Cleanup cancelled")
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Clear patient sessions to force re-fetch with updated FHIR data'
    )
    parser.add_argument(
        '--patient-id',
        type=str,
        help='Azure patient ID to clear (e.g., 98ce4472-30a5-43b2-8b37-85c86fc53772)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Clear all patient sessions (use with caution)'
    )
    
    args = parser.parse_args()
    
    clear_patient_sessions(
        patient_id=args.patient_id,
        clear_all=args.all
    )
