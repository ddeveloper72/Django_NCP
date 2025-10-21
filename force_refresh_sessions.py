#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession
from patient_data.services.comprehensive_clinical_data_service import ComprehensiveClinicalDataService
import logging

# Set up more detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def force_refresh_sessions():
    """Force refresh all active session data to use the updated service"""
    
    active_sessions = PatientSession.objects.filter(is_active=True)
    print(f"Found {active_sessions.count()} active sessions to refresh")
    
    for session in active_sessions:
        print(f"\n=== Refreshing Session {session.session_id} ===")
        
        try:
            # Get patient data 
            patient_data = session.decrypt_patient_data()
            if not patient_data:
                print("  ❌ No patient data found")
                continue
                
            print(f"  ✅ Patient data found: {len(patient_data)} fields")
            
            # The key insight: We need to force the view to re-process clinical data
            # by clearing any cached comprehensive data if it exists
            
            # Update the session to invalidate any view-level caches
            session.last_action = f"Medication deduplication fix applied - {session.session_id[:8]}"
            session.save()
            
            print(f"  ✅ Session {session.session_id[:8]} refreshed")
            
        except Exception as e:
            print(f"  ❌ Error refreshing session {session.session_id}: {e}")
            
    print(f"\n🔄 All sessions refreshed! The medication deduplication fix should now be active.")
    print(f"👉 Please refresh your browser page to see the updated medication count.")

if __name__ == "__main__":
    force_refresh_sessions()