#!/usr/bin/env python
"""
Django management command to show which sessions contain your PT test data
and help identify the correct session IDs for testing
"""
import hashlib

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show which sessions contain Portuguese test patient data"

    def handle(self, *args, **options):
        self.stdout.write("🇵🇹 PORTUGUESE TEST PATIENT SESSION FINDER")
        self.stdout.write("=" * 50)

        # Hash of our known good Portuguese files
        pt_file_hashes = {
            "2-1234-W7.xml": "57cab66500a5",  # Rich António Pereira data (first 12 chars)
            "2-5678-W7.xml": "unknown",  # We need to check this
        }

        # Check all sessions for Portuguese patient data
        all_sessions = Session.objects.all()
        pt_sessions = []

        for db_session in all_sessions:
            try:
                decoded_data = db_session.get_decoded()

                for key, value in decoded_data.items():
                    if key.startswith("patient_match_") and isinstance(value, dict):
                        # Check if this is Portuguese data
                        country_code = value.get("country_code", "").upper()
                        file_path = value.get("file_path", "")

                        if country_code == "PT" or "PT" in file_path:
                            cda_content = (
                                value.get("l3_cda_content")
                                or value.get("l1_cda_content")
                                or value.get("cda_content")
                            )

                            if cda_content:
                                session_id = key.replace("patient_match_", "")
                                content_hash = hashlib.md5(
                                    cda_content.encode()
                                ).hexdigest()
                                patient_data = value.get("patient_data", {})

                                pt_sessions.append(
                                    {
                                        "session_id": session_id,
                                        "country_code": country_code,
                                        "file_path": file_path,
                                        "content_length": len(cda_content),
                                        "content_hash": content_hash,
                                        "patient_name": f"{patient_data.get('given_name', '')} {patient_data.get('family_name', '')}".strip(),
                                        "patient_id": patient_data.get(
                                            "patient_id", "Unknown"
                                        ),
                                    }
                                )

            except Exception:
                continue

        if not pt_sessions:
            self.stdout.write("❌ No Portuguese sessions found!")
            self.stdout.write(
                "   You may need to search for Portuguese patients first."
            )
            return

        self.stdout.write(f"✅ Found {len(pt_sessions)} Portuguese patient sessions:")
        self.stdout.write()

        for i, session in enumerate(pt_sessions, 1):
            self.stdout.write(f"📋 Session {i}: {session['session_id']}")
            self.stdout.write(
                f"   Patient: {session['patient_name']} (ID: {session['patient_id']})"
            )
            self.stdout.write(f"   Country: {session['country_code']}")
            self.stdout.write(f"   File: {session['file_path']}")
            self.stdout.write(f"   Length: {session['content_length']:,} characters")
            self.stdout.write(f"   Hash: {session['content_hash'][:12]}...")

            # Check if this matches our known files
            if session["content_hash"].startswith("57cab66500a5"):
                self.stdout.write(
                    "   🎯 *** THIS IS THE RICH ANTÓNIO PEREIRA DATA! ***"
                )
                self.stdout.write("   🎯 *** USE THIS SESSION ID FOR TESTING! ***")

            self.stdout.write()

        self.stdout.write("🔗 DIRECT ACCESS URLS:")
        self.stdout.write("-" * 30)
        for session in pt_sessions:
            if session["content_hash"].startswith("57cab66500a5"):
                self.stdout.write(f"✅ Rich Healthcare Data Session:")
                self.stdout.write(
                    f"   Patient View: /patient_data/patient/{session['session_id']}/"
                )
                self.stdout.write(
                    f"   Healthcare Team: /patient_data/patient/{session['session_id']}/?tab=healthcare"
                )
                self.stdout.write(
                    f"   Clinical Info: /patient_data/patient/{session['session_id']}/?tab=clinical_information"
                )
                self.stdout.write(
                    f"   Debugger: /patient_data/clinical_data_debugger/?patient_id={session['session_id']}"
                )

        self.stdout.write("\n🧪 TESTING INSTRUCTIONS:")
        self.stdout.write("-" * 30)
        self.stdout.write("1. Use the session ID marked with 🎯 above")
        self.stdout.write("2. Go to the Healthcare Team tab URL")
        self.stdout.write(
            "3. Check if you see António Pereira and Centro Hospitalar data"
        )
        self.stdout.write("4. If not, the template mapping might still have issues")

        # Show the expected healthcare data
        self.stdout.write("\n🩺 EXPECTED HEALTHCARE DATA:")
        self.stdout.write("-" * 30)
        self.stdout.write("   Author: António Pereira + organization details")
        self.stdout.write(
            "   Custodian: Centro Hospitalar de Lisboa Central + addresses/telecoms"
        )
        self.stdout.write(
            "   Legal Authenticator: António Pereira + organization details"
        )
