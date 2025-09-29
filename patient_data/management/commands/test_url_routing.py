#!/usr/bin/env python
"""
Django management command to test URL routing for clinical debugger
"""
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from django.test import Client
from django.urls import resolve, reverse


class Command(BaseCommand):
    help = "Test URL routing for clinical debugger"

    def add_arguments(self, parser):
        parser.add_argument("session_id", type=str, help="Session ID to test")

    def handle(self, *args, **options):
        session_id = options["session_id"]

        self.stdout.write(f"🔍 TESTING URL ROUTING FOR SESSION: {session_id}")
        self.stdout.write("=" * 50)

        # Test URL patterns
        self.stdout.write("\n1. TESTING URL PATTERNS:")
        self.stdout.write("-" * 30)

        # Test reverse URL lookup
        try:
            url = reverse(
                "patient_data:clinical_data_debugger", kwargs={"session_id": session_id}
            )
            self.stdout.write(f"✅ Reverse URL: {url}")
        except Exception as e:
            self.stdout.write(f"❌ Reverse URL failed: {e}")

        # Test different URL patterns
        test_urls = [
            f"/patients/debug/clinical/{session_id}/",
            f"/patient_data/debug/clinical/{session_id}/",
            f"/debug/clinical/{session_id}/",
        ]

        self.stdout.write("\n2. TESTING URL RESOLUTION:")
        self.stdout.write("-" * 30)

        for test_url in test_urls:
            try:
                match = resolve(test_url)
                self.stdout.write(
                    f"✅ {test_url} -> {match.view_name} ({match.func.__name__})"
                )
            except Exception as e:
                self.stdout.write(f"❌ {test_url} -> {e}")

        # Test with Django test client
        self.stdout.write("\n3. TESTING WITH CLIENT:")
        self.stdout.write("-" * 30)

        client = Client()

        for test_url in test_urls:
            try:
                response = client.get(test_url)
                self.stdout.write(f"📊 {test_url}:")
                self.stdout.write(f"   Status: {response.status_code}")

                if response.status_code == 302:
                    redirect_url = response.get("Location", "Unknown")
                    self.stdout.write(f"   Redirect to: {redirect_url}")
                elif response.status_code == 200:
                    content_length = len(response.content)
                    self.stdout.write(f"   Content length: {content_length} bytes")

                    # Check if it's JSON
                    try:
                        import json

                        content = json.loads(response.content)
                        if "error" in content:
                            self.stdout.write(f"   Error: {content['error']}")
                        else:
                            self.stdout.write(
                                f"   ✅ Valid JSON response with keys: {list(content.keys())}"
                            )
                    except:
                        self.stdout.write(
                            f"   Content type: {response.get('Content-Type', 'Unknown')}"
                        )

            except Exception as e:
                self.stdout.write(f"❌ {test_url} -> Exception: {e}")

        # Show what URL should be used
        self.stdout.write("\n4. RECOMMENDED URLS TO TRY:")
        self.stdout.write("-" * 30)

        try:
            correct_url = reverse(
                "patient_data:clinical_data_debugger", kwargs={"session_id": session_id}
            )
            full_url = f"http://127.0.0.1:8000{correct_url}"
            self.stdout.write(f"✅ Correct URL: {full_url}")
        except:
            self.stdout.write(
                f"✅ Try: http://127.0.0.1:8000/patients/debug/clinical/{session_id}/"
            )

        self.stdout.write(f"\n📝 Test complete!")
