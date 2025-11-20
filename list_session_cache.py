#!/usr/bin/env python
"""List all cached data types in the session"""

import os
import sys
import django

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from patient_data.models import PatientSession

print("=" * 80)
print("CHECKING SESSION CACHE CONTENTS")
print("=" * 80)

# Get most recent session
sessions = PatientSession.objects.filter(status='active').order_by('-created_at')

if sessions.exists():
    session = sessions.first()
    print(f"\n✅ Session: {session.session_id}")
    print(f"   Created: {session.created_at}")
    
    # List all cached data
    cache_entries = session.cached_data.all()
    print(f"\n📦 Cached data entries: {cache_entries.count()}")
    
    for entry in cache_entries:
        print(f"\n  Type: {entry.data_type}")
        print(f"  Size: {len(entry.encrypted_content)} bytes")
        print(f"  Expires: {entry.expires_at}")
        print(f"  Accessed: {entry.access_count} times")
        
        # Try to get data
        try:
            data = entry.get_cached_data()
            if data:
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())}")
                    
                    # If it's pregnancy data, show counts
                    if 'pregnancy_history' in data:
                        preg_hist = data['pregnancy_history']
                        print(f"  Pregnancy records: {len(preg_hist)}")
                else:
                    print(f"  Data type: {type(data)}")
        except Exception as e:
            print(f"  Error getting data: {e}")
else:
    print("\n❌ No active sessions found")

print("\n" + "=" * 80)
