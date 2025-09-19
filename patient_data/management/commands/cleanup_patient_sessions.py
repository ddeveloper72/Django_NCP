"""
Management command to clean up patient session data for security compliance.

This command removes patient data from sessions that are:
1. Not authenticated (no logged-in user)
2. Expired
3. Contains patient data without proper authentication
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Clean up patient session data for security compliance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force deletion of all patient data sessions",
        )
        parser.add_argument(
            "--expired-only",
            action="store_true",
            help="Only clean expired sessions",
        )
        parser.add_argument(
            "--unauthenticated-only",
            action="store_true",
            help="Only clean sessions without authentication",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        expired_only = options["expired_only"]
        unauthenticated_only = options["unauthenticated_only"]

        self.stdout.write(self.style.WARNING("🔒 PATIENT SESSION DATA CLEANUP UTILITY"))
        self.stdout.write(self.style.WARNING("=" * 50))

        # Get all sessions
        total_sessions = Session.objects.count()
        sessions_with_patient_data = 0
        unauthenticated_with_patient_data = 0
        expired_with_patient_data = 0
        sessions_to_clean = []

        self.stdout.write(f"📊 Analyzing {total_sessions} sessions...")

        for session in Session.objects.all():
            data = session.get_decoded()

            # Check for patient data
            patient_keys = [key for key in data.keys() if "patient" in key.lower()]
            if not patient_keys:
                continue

            sessions_with_patient_data += 1

            # Check authentication
            is_authenticated = "_auth_user_id" in data
            auth_user = None
            if is_authenticated:
                try:
                    auth_user = User.objects.get(id=data["_auth_user_id"])
                except User.DoesNotExist:
                    is_authenticated = False

            # Check expiration
            is_expired = session.expire_date < timezone.now()

            # Determine if this session should be cleaned
            should_clean = False
            reason = []

            if force:
                should_clean = True
                reason.append("force flag")
            elif expired_only and is_expired:
                should_clean = True
                reason.append("expired")
                expired_with_patient_data += 1
            elif unauthenticated_only and not is_authenticated:
                should_clean = True
                reason.append("unauthenticated")
                unauthenticated_with_patient_data += 1
            elif not expired_only and not unauthenticated_only:
                # Default behavior: clean unauthenticated or expired
                if not is_authenticated:
                    should_clean = True
                    reason.append("unauthenticated")
                    unauthenticated_with_patient_data += 1
                elif is_expired:
                    should_clean = True
                    reason.append("expired")
                    expired_with_patient_data += 1

            if not is_authenticated:
                unauthenticated_with_patient_data += 1
            if is_expired:
                expired_with_patient_data += 1

            if should_clean:
                sessions_to_clean.append(
                    {
                        "session": session,
                        "patient_keys": patient_keys,
                        "is_authenticated": is_authenticated,
                        "auth_user": auth_user.username if auth_user else None,
                        "is_expired": is_expired,
                        "reason": reason,
                    }
                )

        # Display summary
        self.stdout.write("")
        self.stdout.write("📋 SESSION ANALYSIS SUMMARY:")
        self.stdout.write(f"   Total Sessions: {total_sessions}")
        self.stdout.write(
            f"   Sessions with Patient Data: {sessions_with_patient_data}"
        )
        self.stdout.write(
            f"   Unauthenticated with Patient Data: {unauthenticated_with_patient_data}"
        )
        self.stdout.write(f"   Expired with Patient Data: {expired_with_patient_data}")
        self.stdout.write(f"   Sessions to Clean: {len(sessions_to_clean)}")

        if sessions_with_patient_data > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"⚠️  SECURITY RISK: {sessions_with_patient_data} sessions contain patient data!"
                )
            )

        if not sessions_to_clean:
            self.stdout.write(self.style.SUCCESS("✅ No sessions need cleaning."))
            return

        # Show what would be cleaned
        if dry_run or not force:
            self.stdout.write("")
            self.stdout.write("🔍 SESSIONS TO BE CLEANED:")
            for i, item in enumerate(sessions_to_clean[:10]):  # Show first 10
                session = item["session"]
                session_key = getattr(session, "session_key", "unknown")
                self.stdout.write(
                    f"   {i+1}. {session_key[:20] if session_key != 'unknown' else 'unknown'}... "
                    f"({len(item['patient_keys'])} patient keys, "
                    f"auth: {item['is_authenticated']}, "
                    f"expired: {item['is_expired']}, "
                    f"reason: {', '.join(item['reason'])})"
                )

            if len(sessions_to_clean) > 10:
                self.stdout.write(f"   ... and {len(sessions_to_clean) - 10} more")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("🔥 DRY RUN: No actual changes made."))
            self.stdout.write("Run with --force to actually clean the sessions.")
            return

        # Perform cleanup
        if not force:
            confirm = input(
                f"\\n⚠️  Are you sure you want to clean {len(sessions_to_clean)} sessions? [y/N]: "
            )
            if confirm.lower() != "y":
                self.stdout.write("❌ Cleanup cancelled.")
                return

        self.stdout.write("")
        self.stdout.write("🧹 CLEANING SESSIONS...")

        cleaned_sessions = 0
        total_patient_keys_removed = 0

        for item in sessions_to_clean:
            session = item["session"]
            session_key = getattr(session, "session_key", "unknown")
            try:
                # For unauthenticated sessions with patient data, delete the entire session
                if not item["is_authenticated"]:
                    session.delete()
                    cleaned_sessions += 1
                    total_patient_keys_removed += len(item["patient_keys"])
                    self.stdout.write(
                        f"   ✅ Deleted session {session_key[:20] if session_key != 'unknown' else 'unknown'}..."
                    )
                else:
                    # For authenticated sessions, just remove patient data
                    data = session.get_decoded()
                    patient_keys_removed = 0
                    for key in item["patient_keys"]:
                        if key in data:
                            del data[key]
                            patient_keys_removed += 1

                    # Save the modified session
                    session_store = session.get_session_store_class()(session_key)
                    for key, value in data.items():
                        session_store[key] = value
                    session_store.save()

                    cleaned_sessions += 1
                    total_patient_keys_removed += patient_keys_removed
                    self.stdout.write(
                        f"   ✅ Cleaned {patient_keys_removed} patient keys from "
                        f"session {session_key[:20] if session_key != 'unknown' else 'unknown'}..."
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"   ❌ Error cleaning session {session_key[:20] if session_key != 'unknown' else 'unknown'}: {e}"
                    )
                )

        # Final summary
        self.stdout.write("")
        self.stdout.write("🎉 CLEANUP COMPLETE!")
        self.stdout.write(f"   Sessions Processed: {cleaned_sessions}")
        self.stdout.write(
            f"   Patient Data Items Removed: {total_patient_keys_removed}"
        )

        if cleaned_sessions > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Patient session data successfully cleaned for security compliance."
                )
            )

        # Check remaining sessions
        remaining_patient_sessions = 0
        for session in Session.objects.all():
            data = session.get_decoded()
            patient_keys = [key for key in data.keys() if "patient" in key.lower()]
            if patient_keys:
                remaining_patient_sessions += 1

        if remaining_patient_sessions > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {remaining_patient_sessions} sessions still contain patient data "
                    "(likely authenticated sessions)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "🔒 All unauthorized patient session data has been cleared!"
                )
            )
