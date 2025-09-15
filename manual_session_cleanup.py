#!/usr/bin/env python3
"""
Manual cleanup of specific patient data from authenticated sessions
"""
import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User


def clear_patient_data_from_session(session_key):
    """Clear patient data from a specific session"""
    try:
        session = Session.objects.get(session_key=session_key)
        data = session.get_decoded()

        # Get user info
        user_id = data.get("_auth_user_id")
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                print(f"📋 Session belongs to user: {user.username} (ID: {user.id})")
            except User.DoesNotExist:
                print(f"⚠️  User ID {user_id} not found")

        # Find and remove patient-related keys
        patient_keys = []
        for key in list(data.keys()):
            if any(
                pattern in key.lower()
                for pattern in ["patient", "mario", "borg", "cda"]
            ):
                patient_keys.append(key)

        if patient_keys:
            print(f"🧹 Removing {len(patient_keys)} patient data keys:")
            for key in patient_keys:
                print(f"   - {key}")
                del data[key]

            # Save the session
            session.session_data = Session.objects.encode(data)
            session.save()

            print(f"✅ Patient data cleared from session {session_key[:20]}...")
            return True
        else:
            print(f"ℹ️  No patient data found in session {session_key[:20]}...")
            return False

    except Session.DoesNotExist:
        print(f"❌ Session {session_key} not found")
        return False
    except Exception as e:
        print(f"❌ Error processing session {session_key}: {e}")
        return False


def main():
    """Main cleanup function"""
    print("🔒 MANUAL PATIENT DATA CLEANUP")
    print("=" * 50)

    # Target the specific session with Mario Borg
    target_session = "p4myrkjery4mzutbmxl2emedkiu2ssfv"

    print(f"🎯 Targeting session: {target_session}")
    success = clear_patient_data_from_session(target_session)

    if success:
        print("\n✅ Manual cleanup completed successfully!")
        print("🔒 Mario Borg data should now be removed from the session")
    else:
        print("\n❌ Manual cleanup failed")

    return success


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
