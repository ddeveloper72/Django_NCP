#!/usr/bin/env python3
"""
Simple diagnostic script to check what data is actually being sent to template
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def diagnostic_template_data():
    """Check what data is being sent to the template"""
    print("🔍 Template Data Diagnostic")
    print("=" * 60)

    # Import after Django setup
    from patient_data.models import Patient
    from patient_data.views import patient_cda_view
    from django.test import RequestFactory
    from django.contrib.sessions.backends.db import SessionStore

    try:
        # Find Portuguese patient
        portuguese_patient = Patient.objects.filter(
            first_name__icontains="Diana", last_name__icontains="Ferreira"
        ).first()

        if not portuguese_patient:
            print("❌ Portuguese patient Diana Ferreira not found")
            return False

        print(
            f"✅ Found Portuguese patient: {portuguese_patient.first_name} {portuguese_patient.last_name}"
        )

        # Create mock request
        factory = RequestFactory()
        request = factory.get(f"/patient/{portuguese_patient.id}/cda/")
        request.session = SessionStore()

        # Store patient in session (simulate search result)
        request.session["temp_patient"] = {
            "id": f"temp_{portuguese_patient.id}",
            "first_name": portuguese_patient.first_name,
            "last_name": portuguese_patient.last_name,
            "birth_date": str(portuguese_patient.birth_date),
            "gender": portuguese_patient.gender,
            "source": "database",
            "database_id": portuguese_patient.id,
        }
        request.session.save()

        print("\n🔍 Calling patient_cda_view...")

        # Call the view and catch the context being sent to template
        try:
            # Since we can't easily intercept the render call, let's check if the view completes
            response = patient_cda_view(request, portuguese_patient.id)

            if hasattr(response, "context_data"):
                context = response.context_data
                print("✅ Got context data from response")
            else:
                print("❌ No context data in response")
                return False

        except Exception as e:
            print(f"❌ Error calling view: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Analyze the context data
        print("\n🔍 Context Data Analysis:")
        print("-" * 40)

        if "translation_result" in context:
            translation_result = context["translation_result"]
            sections = translation_result.get("sections", [])

            print(f"Found {len(sections)} sections in translation_result")

            for i, section in enumerate(sections):
                title = section.get("title", "Unknown")
                section_code = section.get("section_code", "Unknown")

                print(f"\nSection {i+1}: {title} ({section_code})")

                # Check if this is allergies section
                if section_code == "48765-2":
                    print("  🚨 ALLERGY SECTION DETECTED")

                    # Check content structure
                    content = section.get("content", {})
                    if isinstance(content, dict):
                        if "original" in content and "translated" in content:
                            print("    ✅ Dual language structure detected")
                            print(f"    Original: {str(content['original'])[:100]}...")
                            print(
                                f"    Translated: {str(content['translated'])[:100]}..."
                            )
                        else:
                            print(f"    Content: {str(content)[:100]}...")
                    else:
                        print(f"    Content: {str(content)[:100]}...")

                    # Check PS table
                    ps_table = section.get("ps_table_html", "")
                    if ps_table:
                        print(f"    PS Table (first 200 chars): {ps_table[:200]}...")

                        # Look for vaccination terms in allergy PS table
                        vaccination_terms = [
                            "vaccination",
                            "vaccine",
                            "immunization",
                            "hepatitis",
                            "influenza",
                        ]
                        found_vaccination = [
                            term
                            for term in vaccination_terms
                            if term.lower() in ps_table.lower()
                        ]

                        if found_vaccination:
                            print(
                                f"    ❌ VACCINATION TERMS IN ALLERGY TABLE: {found_vaccination}"
                            )
                        else:
                            print(f"    ✅ No vaccination terms in allergy table")

                # Check if this is immunizations section
                elif section_code == "10157-6":
                    print("  🚨 IMMUNIZATION SECTION DETECTED")

                    # Check content structure
                    content = section.get("content", {})
                    ps_table = section.get("ps_table_html", "")

                    if ps_table:
                        print(f"    PS Table (first 200 chars): {ps_table[:200]}...")

                        # Look for allergy terms in immunization PS table
                        allergy_terms = [
                            "allergy",
                            "allergic",
                            "intolerance",
                            "adverse",
                            "anaphylaxis",
                        ]
                        found_allergy = [
                            term
                            for term in allergy_terms
                            if term.lower() in ps_table.lower()
                        ]

                        if found_allergy:
                            print(
                                f"    ❌ ALLERGY TERMS IN IMMUNIZATION TABLE: {found_allergy}"
                            )
                        else:
                            print(f"    ✅ No allergy terms in immunization table")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the diagnostic"""
    print("🚀 Template Data Diagnostic")
    print("Checking what data is being sent to the template")
    print()

    success = diagnostic_template_data()

    print("\n📋 Diagnostic Summary")
    print("=" * 60)

    if success:
        print("✅ Diagnostic completed - check analysis above")
    else:
        print("❌ Diagnostic failed - check error messages")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
