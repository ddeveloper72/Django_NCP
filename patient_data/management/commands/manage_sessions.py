#!/usr/bin/env python3
"""
Management command for session operations during development
"""

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError

from patient_data.session_management import DevelopmentSessionManager


class Command(BaseCommand):
    help = "Manage sessions for development and debugging"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["list", "create", "delete", "clean"],
            help="Action to perform",
        )
        parser.add_argument("--patient-id", help="Patient ID for create operations")
        parser.add_argument("--session-key", help="Session key for specific operations")
        parser.add_argument(
            "--force", action="store_true", help="Force operations without confirmation"
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Session management commands are only available in DEBUG mode"
            )

        action = options["action"]

        if action == "list":
            self.list_sessions()
        elif action == "create":
            self.create_session(options.get("patient_id"))
        elif action == "delete":
            self.delete_session(options.get("session_key"), options.get("force"))
        elif action == "clean":
            self.clean_sessions(options.get("force"))

    def list_sessions(self):
        """List all available sessions"""
        sessions = DevelopmentSessionManager.list_available_sessions()

        if not sessions:
            self.stdout.write(self.style.WARNING("No patient sessions found"))
            return

        self.stdout.write(f"\n📋 Found {len(sessions)} patient sessions:")
        self.stdout.write("=" * 80)

        for session_key, info in sessions.items():
            self.stdout.write(f"\n🔑 Session: {session_key}")
            self.stdout.write(f"   📅 Expires: {info['expiry']}")
            self.stdout.write(f"   👥 Patients: {', '.join(info['patients'])}")

            # Show URL examples for each patient
            for patient_id in info["patients"]:
                self.stdout.write(
                    f"   🔗 Simplified view URL: /patients/cda/simplified/{patient_id}/"
                )
                self.stdout.write(
                    f"   🔗 Session view URL: /patients/cda/{patient_id}/"
                )

    def create_session(self, patient_id):
        """Create a new test session"""
        if not patient_id:
            raise CommandError("--patient-id is required for create action")

        self.stdout.write(f"🔧 Creating test session for patient: {patient_id}")

        try:
            session_key = (
                DevelopmentSessionManager.create_test_session_with_patient_data(
                    patient_id
                )
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Created session: {session_key}"))
            self.stdout.write(f"🔗 Test URLs:")
            self.stdout.write(
                f"   Simplified view: /patients/cda/simplified/{patient_id}/"
            )
            self.stdout.write(f"   Session view: /patients/cda/{patient_id}/")
            self.stdout.write(
                f"   Debug clinical: /patients/debug/clinical/{patient_id}/"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create session: {e}"))

    def delete_session(self, session_key, force):
        """Delete a specific session"""
        if not session_key:
            raise CommandError("--session-key is required for delete action")

        try:
            session = Session.objects.get(session_key=session_key)

            if not force:
                session_data = session.get_decoded()
                patient_keys = [
                    k for k in session_data.keys() if k.startswith("patient_match_")
                ]

                self.stdout.write(f"⚠️  About to delete session: {session_key}")
                if patient_keys:
                    patients = [k.replace("patient_match_", "") for k in patient_keys]
                    self.stdout.write(
                        f"   This will remove access to patients: {', '.join(patients)}"
                    )

                confirm = input("Are you sure? (y/N): ")
                if confirm.lower() != "y":
                    self.stdout.write("❌ Deletion cancelled")
                    return

            session.delete()
            self.stdout.write(self.style.SUCCESS(f"✅ Deleted session: {session_key}"))

        except Session.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Session not found: {session_key}"))

    def clean_sessions(self, force):
        """Clean expired sessions"""
        from django.utils import timezone

        expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired_sessions.count()

        if count == 0:
            self.stdout.write("✅ No expired sessions to clean")
            return

        if not force:
            self.stdout.write(f"⚠️  Found {count} expired sessions")
            confirm = input(f"Delete {count} expired sessions? (y/N): ")
            if confirm.lower() != "y":
                self.stdout.write("❌ Cleanup cancelled")
                return

        expired_sessions.delete()
        self.stdout.write(self.style.SUCCESS(f"✅ Cleaned {count} expired sessions"))
