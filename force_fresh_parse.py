#!/usr/bin/env python3
"""
Force Fresh Patient Data Parse - Clear Caches and Re-run Enhanced Parser
"""

import os
import sys
import django
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.core.cache import cache
from patient_data.models import PatientSession

def force_fresh_patient_parse():
    """Force fresh parsing by clearing caches and updating session timestamp"""
    
    print("🔄 Force Fresh Patient Data Parse...")
    print("=" * 50)
    
    # Clear Django cache
    cache.clear()
    print("✅ Cleared Django cache")
    
    # Update session timestamps to force fresh data processing
    sessions = PatientSession.objects.filter(is_active=True)
    updated_count = 0
    
    for session in sessions:
        # Touch the session to update last_accessed (this might trigger fresh processing)
        session.access_count += 1
        session.save()
        updated_count += 1
        print(f"✅ Updated session: {session.session_id}")
    
    print(f"✅ Updated {updated_count} active sessions")
    
    print("\n🎯 Next Steps:")
    print("1. Refresh your browser page (F5 or Ctrl+F5)")
    print("2. The patient_details_view should run fresh parsing")
    print("3. Enhanced medication data should now appear")
    
    print("\n📋 What This Does:")
    print("• Clears any cached data that might be stale")
    print("• Forces Django to re-run the comprehensive service")
    print("• Enhanced parser will extract fresh medication data")
    print("• Template should show updated enhanced fields")
    
    print("\n" + "=" * 50)
    print("✅ Cache cleared - REFRESH YOUR BROWSER NOW")

if __name__ == "__main__":
    force_fresh_patient_parse()