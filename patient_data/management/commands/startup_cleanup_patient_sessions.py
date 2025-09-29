"""
Django management command to clean up patient sessions on server startup/restart

This command should be run automatically when the server starts to ensure
no orphaned patient data remains in sessions from previous server instances.
"""

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean up patient session data on server startup/restart"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-sessions",
            action="store_true",
            help="Clean patient data from ALL sessions (including authenticated ones)",
        )
        parser.add_argument(
            "--older-than-hours",
            type=int,
            default=24,
            help="Only clean sessions older than this many hours (default: 24)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompts",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("[TOOL] SERVER STARTUP PATIENT SESSION CLEANUP")
        )
        self.stdout.write("=" * 60)

        # Calculate cutoff time
        cutoff_time = timezone.now() - timezone.timedelta(
            hours=options["older_than_hours"]
        )

        # Analyze sessions
        total_sessions = Session.objects.count()
        old_sessions = Session.objects.filter(expire_date__lt=cutoff_time)

        self.stdout.write(f"[CHART] Total sessions: {total_sessions}")
        self.stdout.write(
            f"[CHART] Sessions older than {options['older_than_hours']} hours: {old_sessions.count()}"
        )

        sessions_with_patient_data = []
        patient_data_count = 0

        # Check which sessions contain patient data
        for session in Session.objects.all():
            try:
                data = session.get_decoded()
                patient_keys = [key for key in data.keys() if "patient" in key.lower()]

                if patient_keys:
                    # Check if session is old enough or if cleaning all sessions
                    is_old_enough = session.expire_date < cutoff_time
                    should_clean = options["all_sessions"] or is_old_enough

                    if should_clean:
                        user_id = data.get("_auth_user_id")
                        user_info = f"User {user_id}" if user_id else "Unauthenticated"

                        sessions_with_patient_data.append(
                            {
                                "session_key": session.session_key,
                                "user_info": user_info,
                                "patient_keys": patient_keys,
                                "expire_date": session.expire_date,
                                "is_authenticated": bool(user_id),
                            }
                        )
                        patient_data_count += len(patient_keys)

            except Exception as e:
                logger.error(f"Error checking session {session.session_key}: {e}")

        self.stdout.write(
            f"⚠️  Sessions with patient data to clean: {len(sessions_with_patient_data)}"
        )
        self.stdout.write(
            f"⚠️  Total patient data items to remove: {patient_data_count}"
        )

        if not sessions_with_patient_data:
            self.stdout.write(
                self.style.SUCCESS("[SUCCESS] No patient session data needs cleanup")
            )
            return

        # Show details
        if options["dry_run"] or not options["force"]:
            self.stdout.write("\n[LIST] Sessions to be cleaned:")
            for session_info in sessions_with_patient_data:
                auth_status = (
                    "🔒 Auth" if session_info["is_authenticated"] else "🔓 Unauth"
                )
                self.stdout.write(
                    f"  {auth_status} {session_info['session_key'][:20]}... "
                    f"({session_info['user_info']}) - {len(session_info['patient_keys'])} items"
                )

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("\n[SEARCH] DRY RUN - No changes made"))
            return

        # Confirmation
        if not options["force"]:
            confirm = input(
                f"\nProceed with cleaning {len(sessions_with_patient_data)} sessions? [y/N]: "
            )
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Cleanup cancelled"))
                return

        # Perform cleanup
        self.stdout.write("\n🧹 Starting cleanup...")
        cleaned_sessions = 0
        cleaned_items = 0
        errors = 0

        for session_info in sessions_with_patient_data:
            try:
                session = Session.objects.get(session_key=session_info["session_key"])
                data = session.get_decoded()

                # Remove patient data keys
                for key in session_info["patient_keys"]:
                    if key in data:
                        del data[key]
                        cleaned_items += 1

                # Save the cleaned session
                session.session_data = Session.objects.encode(data)
                session.save()

                cleaned_sessions += 1
                self.stdout.write(
                    f"  [SUCCESS] Cleaned session {session_info['session_key'][:20]}..."
                )

            except Session.DoesNotExist:
                self.stdout.write(
                    f"  ⚠️  Session {session_info['session_key'][:20]} no longer exists"
                )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    f"  [ERROR] Error cleaning session {session_info['session_key'][:20]}: {e}"
                )
                logger.error(
                    f"Error cleaning session {session_info['session_key']}: {e}"
                )

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🎉 SERVER STARTUP CLEANUP COMPLETE"))
        self.stdout.write(f"[SUCCESS] Sessions cleaned: {cleaned_sessions}")
        self.stdout.write(f"[SUCCESS] Patient data items removed: {cleaned_items}")
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"[ERROR] Errors encountered: {errors}"))

        # Log the cleanup
        logger.info(
            f"Server startup patient session cleanup completed: "
            f"{cleaned_sessions} sessions, {cleaned_items} items removed, {errors} errors"
        )

        self.stdout.write(
            self.style.SUCCESS("\n🔒 Server is now ready with clean patient sessions")
        )
