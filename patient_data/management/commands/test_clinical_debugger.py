#!/usr/bin/env python
"""
Django management command to test clinical debugger session access
"""
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.test import RequestFactory

from patient_data.clinical_data_debugger import clinical_data_debugger


class Command(BaseCommand):
    help = "Test clinical debugger access for specific session ID"

    def add_arguments(self, parser):
        parser.add_argument("session_id", type=str, help="Session ID to test")

    def handle(self, *args, **options):
        session_id = options["session_id"]

        self.stdout.write(
            f"🔍 TESTING CLINICAL DEBUGGER ACCESS FOR SESSION: {session_id}"
        )
        self.stdout.write("=" * 60)

        # Step 1: Check if session exists in database
        session_key = f"patient_match_{session_id}"
        self.stdout.write(f"\n1. Checking for session key: {session_key}")

        found_sessions = []
        all_sessions = Session.objects.all()

        for db_session in all_sessions:
            try:
                db_session_data = db_session.get_decoded()
                if session_key in db_session_data:
                    match_data = db_session_data[session_key]
                    found_sessions.append(
                        {
                            "django_session_key": db_session.session_key,
                            "patient_match_key": session_key,
                            "match_data": match_data,
                        }
                    )
                    break
            except Exception as e:
                continue

        if found_sessions:
            self.stdout.write("✅ Session found in database!")
            session_info = found_sessions[0]
            match_data = session_info["match_data"]

            self.stdout.write(
                f"   Django session key: {session_info['django_session_key']}"
            )
            self.stdout.write(
                f"   Patient match key: {session_info['patient_match_key']}"
            )

            # Show what data is available
            patient_data = match_data.get("patient_data", {})
            self.stdout.write(
                f"   Patient: {patient_data.get('given_name', '')} {patient_data.get('family_name', '')}"
            )
            self.stdout.write(
                f"   Country: {match_data.get('country_code', 'Unknown')}"
            )
            self.stdout.write(f"   File path: {match_data.get('file_path', 'Unknown')}")

            # Check CDA content
            cda_content = (
                match_data.get("l3_cda_content")
                or match_data.get("l1_cda_content")
                or match_data.get("cda_content")
            )

            if cda_content:
                self.stdout.write(f"   CDA content: {len(cda_content):,} characters")
            else:
                self.stdout.write("   ❌ No CDA content found!")
                return

        else:
            self.stdout.write("❌ Session not found in database!")
            self.stdout.write("   Checking for any sessions containing this ID...")

            # Search more broadly
            for db_session in all_sessions:
                try:
                    db_session_data = db_session.get_decoded()
                    for key, value in db_session_data.items():
                        if session_id in str(key) or session_id in str(value):
                            self.stdout.write(
                                f"   Found reference in session {db_session.session_key}: {key}"
                            )
                except Exception:
                    continue
            return

        # Step 2: Test the clinical debugger logic directly
        self.stdout.write(f"\n2. Testing clinical debugger view logic...")

        # Create a mock request
        factory = RequestFactory()
        request = factory.get(f"/debug/clinical/{session_id}/")

        # Create an empty session (since we're testing database session lookup)
        from django.contrib.sessions.backends.db import SessionStore

        request.session = SessionStore()

        try:
            response = clinical_data_debugger(request, session_id)

            if hasattr(response, "content"):
                import json

                content = json.loads(response.content.decode())

                if "error" in content:
                    self.stdout.write(
                        f"❌ Clinical debugger returned error: {content['error']}"
                    )
                else:
                    self.stdout.write("✅ Clinical debugger executed successfully!")

                    # Show what was extracted
                    if "comprehensive_debug_data" in content:
                        debug_data = content["comprehensive_debug_data"]
                        self.stdout.write(
                            f"   Healthcare data keys: {list(debug_data.get('healthcare_data', {}).keys())}"
                        )

                        healthcare = debug_data.get("healthcare_data", {})
                        if healthcare:
                            author = healthcare.get("author", {})
                            custodian = healthcare.get("custodian", {})
                            legal_auth = healthcare.get("legal_authenticator", {})

                            self.stdout.write(
                                f"   Author fields: {len(author)} - {list(author.keys())[:3]}"
                            )
                            self.stdout.write(
                                f"   Custodian fields: {len(custodian)} - {list(custodian.keys())[:3]}"
                            )
                            self.stdout.write(
                                f"   Legal auth fields: {len(legal_auth)} - {list(legal_auth.keys())[:3]}"
                            )

                            if author.get("name"):
                                self.stdout.write(
                                    f"   ✅ Author name: {author.get('name')}"
                                )
                            if custodian.get("name"):
                                self.stdout.write(
                                    f"   ✅ Custodian name: {custodian.get('name')}"
                                )
                        else:
                            self.stdout.write("   ❌ No healthcare data extracted")
                    else:
                        self.stdout.write(
                            "   ❌ No comprehensive debug data in response"
                        )
            else:
                self.stdout.write(f"❌ Response has no content: {type(response)}")

        except Exception as e:
            self.stdout.write(f"❌ Clinical debugger failed with exception: {e}")
            import traceback

            traceback.print_exc()

        # Step 3: Show correct URLs
        self.stdout.write(f"\n3. CORRECT URLS TO TEST:")
        self.stdout.write("-" * 30)
        self.stdout.write(
            f"   Clinical Debugger: http://127.0.0.1:8000/patient_data/debug/clinical/{session_id}/"
        )
        self.stdout.write(
            f"   Clinical API: http://127.0.0.1:8000/patient_data/api/clinical/{session_id}/"
        )
        self.stdout.write(
            f"   Patient View: http://127.0.0.1:8000/patient_data/patient/{session_id}/"
        )

        self.stdout.write(f"\n📝 Test complete!")
