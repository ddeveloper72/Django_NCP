#!/usr/bin/env python
"""
Clear Session Data for Patient 1678261269

Force refresh the session data to apply our deduplication fix.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'eu_ncp_server.settings'
django.setup()

from django.contrib.sessions.models import Session

def clear_patient_session():
    """Clear session data for patient 1678261269 to force refresh."""
    print("🔄 Clearing Patient Session Data")
    print("=" * 60)
    
    try:
        session_key = "patient_match_1678261269"
        sessions_cleared = 0
        
        # Find and clear sessions containing our patient data
        sessions = Session.objects.all()
        print(f"📊 Checking {len(sessions)} sessions...")
        
        for session in sessions:
            try:
                session_data = session.get_decoded()
                if session_key in session_data:
                    print(f"✅ Found patient session: {session.session_key}")
                    
                    # Clear the patient data but keep the session
                    del session_data[session_key]
                    session.save()
                    sessions_cleared += 1
                    print(f"🗑️ Cleared patient data from session")
                    
            except Exception as e:
                print(f"❌ Error processing session: {e}")
                continue
        
        print(f"\n📈 Summary:")
        print(f"   Sessions processed: {len(sessions)}")
        print(f"   Patient sessions cleared: {sessions_cleared}")
        
        if sessions_cleared > 0:
            print("\n✅ Session data cleared! Next visit will use updated logic.")
        else:
            print("\n⚠️ No patient sessions found to clear.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_patient_session()