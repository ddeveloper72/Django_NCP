#!/usr/bin/env python
"""
Django management command to create a fresh session with Portuguese test data
"""
import hashlib
import json
from pathlib import Path

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a fresh session with Portuguese test patient data"

    def handle(self, *args, **options):
        self.stdout.write("🇵🇹 CREATING FRESH PORTUGUESE TEST SESSION")
        self.stdout.write("=" * 50)

        # Load the Portuguese test file
        test_file = Path("test_data/eu_member_states/PT/2-1234-W7.xml")

        if not test_file.exists():
            self.stdout.write(f"❌ Test file not found: {test_file}")
            return

        # Read the CDA content
        with open(test_file, "r", encoding="utf-8") as f:
            cda_content = f.read()

        content_hash = hashlib.md5(cda_content.encode()).hexdigest()

        self.stdout.write(f"✅ Loaded test file: {test_file}")
        self.stdout.write(f"   Content length: {len(cda_content):,} characters")
        self.stdout.write(f"   Content hash: {content_hash[:12]}...")

        # Create a new session
        session = SessionStore()
        session.create()

        # Create session ID from file content hash (first 10 chars)
        session_id = content_hash[:10]

        # Create patient match data structure
        patient_match_data = {
            "file_path": str(test_file.absolute()),
            "country_code": "PT",
            "confidence_score": 1.0,
            "patient_data": {
                "given_name": "Diana",
                "family_name": "Ferreira",
                "patient_id": "2-1234-W7",
                "birth_date": "19690505",
                "gender": "F",
            },
            "l3_cda_content": cda_content,
            "cda_content": cda_content,  # Fallback
        }

        # Store in session
        session_key = f"patient_match_{session_id}"
        session[session_key] = patient_match_data
        session.save()

        self.stdout.write(f"\n✅ Created new session!")
        self.stdout.write(f"   Django Session Key: {session.session_key}")
        self.stdout.write(f"   Patient Match Key: {session_key}")
        self.stdout.write(f"   Session ID: {session_id}")

        # Show patient info
        patient = patient_match_data["patient_data"]
        self.stdout.write(
            f"   Patient: {patient['given_name']} {patient['family_name']}"
        )
        self.stdout.write(f"   Patient ID: {patient['patient_id']}")

        # Test Enhanced CDA Parser on this content
        self.stdout.write(f"\n🧪 TESTING ENHANCED CDA PARSER:")
        try:
            from patient_data.services.enhanced_cda_xml_parser import (
                EnhancedCDAXMLParser,
            )

            parser = EnhancedCDAXMLParser()
            parsed_result = parser.parse_cda_content(cda_content)

            if parsed_result:
                admin_data = parsed_result.get("administrative_data", {})
                author = admin_data.get("author_hcp", {})
                custodian = admin_data.get("custodian_organization", {})
                legal_auth = admin_data.get("legal_authenticator", {})

                self.stdout.write(f"   ✅ Enhanced CDA Parser worked!")
                self.stdout.write(f"   Author HCP: {len(author)} fields")
                self.stdout.write(f"   Custodian: {len(custodian)} fields")
                self.stdout.write(f"   Legal Auth: {len(legal_auth)} fields")

                if author.get("name"):
                    self.stdout.write(f"   👨‍⚕️ Author: {author.get('name')}")
                if custodian.get("name"):
                    self.stdout.write(f"   🏥 Custodian: {custodian.get('name')}")
            else:
                self.stdout.write("   ❌ Enhanced CDA Parser returned no data")

        except Exception as e:
            self.stdout.write(f"   ❌ Enhanced CDA Parser error: {e}")

        # Show test URLs
        self.stdout.write(f"\n🔗 TEST URLS:")
        self.stdout.write("-" * 30)
        self.stdout.write(f"✅ Clinical Debugger:")
        self.stdout.write(
            f"   http://127.0.0.1:8000/patient_data/debug/clinical/{session_id}/"
        )
        self.stdout.write(f"✅ Clinical API:")
        self.stdout.write(
            f"   http://127.0.0.1:8000/patient_data/api/clinical/{session_id}/"
        )
        self.stdout.write(f"✅ Patient View:")
        self.stdout.write(
            f"   http://127.0.0.1:8000/patient_data/patient/{session_id}/"
        )

        self.stdout.write(f"\n📝 Session created successfully!")
