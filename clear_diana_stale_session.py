"""
Clear Diana's stale session that has old FHIR bundle
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from django.contrib.sessions.models import Session
from patient_data.models import PatientSession

print("=" * 80)
print("CLEARING DIANA'S STALE SESSIONS")
print("=" * 80)

# Clear PatientSession records
patient_sessions = PatientSession.objects.filter(country_code='PT')
count = patient_sessions.count()
if count > 0:
    patient_sessions.delete()
    print(f"\n✅ Deleted {count} PatientSession records for Portugal")
else:
    print("\n  No PatientSession records to delete")

# Clear Django sessions with Diana's data
from django.utils import timezone
active_sessions = Session.objects.filter(expire_date__gte=timezone.now())

deleted_count = 0
for session in active_sessions:
    try:
        session_data = session.get_decoded()
        for key in list(session_data.keys()):
            if key.startswith('patient_match_'):
                value = session_data[key]
                if isinstance(value, dict):
                    patient_info = value.get('patient_data', {})
                    name = patient_info.get('name', '')
                    if 'Diana' in name or 'Ferreira' in name:
                        print(f"\n  Deleting session: {key}")
                        print(f"  Session Key: {session.session_key}")
                        session.delete()
                        deleted_count += 1
                        break
    except Exception as e:
        continue

if deleted_count > 0:
    print(f"\n✅ Deleted {deleted_count} Django sessions with Diana's data")
else:
    print("\n  No Diana sessions found in Django session storage")

print("\n" + "=" * 80)
print("SESSION CLEANUP COMPLETE")
print("=" * 80)

print("\n📋 NEXT STEPS:")
print("   1. Search for Diana again in the UI")
print("   2. This will fetch FRESH FHIR data from Azure")
print("   3. The new FHIR bundle should have all 5 pregnancy observations")
print("   4. Parser will create 3 past pregnancies (1 Termination + 2 Livebirth placeholders)")
