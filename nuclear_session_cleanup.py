"""
Nuclear option: Delete ALL sessions and force browser refresh
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from patient_data.models import PatientSession
from django.core.cache import cache

print("=" * 80)
print("NUCLEAR CLEANUP: PURGING ALL SESSIONS")
print("=" * 80)

# 1. Delete ALL PatientSession records
count = PatientSession.objects.all().count()
if count > 0:
    PatientSession.objects.all().delete()
    print(f"\n✅ Deleted ALL {count} PatientSession records")

# 2. Delete ALL Django sessions
count = Session.objects.all().count()
if count > 0:
    Session.objects.all().delete()
    print(f"✅ Deleted ALL {count} Django session records")

# 3. Clear all cache
cache.clear()
print(f"✅ Cleared Django cache")

print("\n" + "=" * 80)
print("CLEANUP COMPLETE")
print("=" * 80)

print("\n📋 NEXT STEPS:")
print("   1. Close ALL browser windows")
print("   2. Open a NEW incognito/private window")
print("   3. Go to: http://127.0.0.1:9000")
print("   4. Login and search for Diana (PT, 2-1234-W7)")
print("   5. This will fetch FRESH data with all 5 pregnancy observations")
print("\n⚠️  CRITICAL: Use incognito window to avoid browser cache!")
