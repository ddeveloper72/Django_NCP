#!/usr/bin/env python3
"""Management command to test session data access."""

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand

from patient_data.simplified_clinical_view import (
    SimplifiedClinicalDataView,
    SimplifiedDataExtractor,
)


class Command(BaseCommand):
    help = "Test session data access"

    def handle(self, *args, **options):
        # Get session with most CDA content
        session_key = "l9w1vnqpwohq5ddjsf36u7lozl1oe7o7"

        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()

            self.stdout.write(f"✅ Found session: {session_key}")

            # Look for patient match data
            patient_keys = [
                key for key in session_data.keys() if key.startswith("patient_match_")
            ]
            self.stdout.write(f"Patient match keys: {patient_keys}")

            if patient_keys:
                patient_key = patient_keys[0]
                patient_id = patient_key.replace("patient_match_", "")
                patient_data = session_data[patient_key]

                self.stdout.write(f"✅ Found patient data for ID: {patient_id}")

                # Check patient name
                patient_info = patient_data.get("patient_data", {})
                given_name = patient_info.get("given_name", "Unknown")
                family_name = patient_info.get("family_name", "Unknown")
                self.stdout.write(f"Patient name: {given_name} {family_name}")

                # Check for CDA content
                if "l3_cda_content" in patient_data:
                    self.stdout.write("✅ L3 CDA content found!")

                    # Create extractor to test data processing
                    extractor = SimplifiedDataExtractor()

                    # Test extracting CDA content
                    cda_content = patient_data["l3_cda_content"]
                    self.stdout.write(
                        f"CDA content length: {len(cda_content)} characters"
                    )

                    # Try to extract sections using extractor
                    try:
                        sections = extractor.extract_sections(cda_content)
                        self.stdout.write(f"✅ Extracted {len(sections)} sections:")

                        for i, section in enumerate(sections):
                            title = section.get("title", "Unknown")
                            self.stdout.write(f"  Section {i+1}: {title}")

                            items = section.get("items", [])
                            self.stdout.write(f"    Items: {len(items)}")

                            # Show sample items
                            for j, item in enumerate(items[:2]):  # Show first 2 items
                                if isinstance(item, dict):
                                    item_keys = list(item.keys())
                                    self.stdout.write(
                                        f"      Item {j+1} keys: {item_keys}"
                                    )
                                else:
                                    item_str = (
                                        str(item)[:50] + "..."
                                        if len(str(item)) > 50
                                        else str(item)
                                    )
                                    self.stdout.write(f"      Item {j+1}: {item_str}")

                        self.stdout.write(
                            self.style.SUCCESS(
                                "✅ Successfully extracted and processed CDA sections!"
                            )
                        )

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error extracting sections: {str(e)}")
                        )
                        import traceback

                        traceback.print_exc()
                else:
                    self.stdout.write("❌ No L3 CDA content found")
            else:
                self.stdout.write("❌ No patient match keys found")

        except Session.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Session {session_key} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback

            traceback.print_exc()
