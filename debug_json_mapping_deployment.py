#!/usr/bin/env python3
"""
Debug JSON Field Mapping Deployment Issues
Identify and fix any errors in the deployment
"""

import os
import sys
import traceback

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

try:
    import django

    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)


def debug_import_issues():
    """Debug import issues with the new components"""

    print("🔍 Debugging Import Issues")
    print("=" * 50)

    # Test each import individually
    components = [
        (
            "Enhanced CDA Field Mapper",
            "patient_data.services.enhanced_cda_field_mapper",
            "EnhancedCDAFieldMapper",
        ),
        (
            "Enhanced CDA Processor with Mapping",
            "patient_data.services.enhanced_cda_processor_with_mapping",
            "EnhancedCDAProcessorWithMapping",
        ),
        (
            "Original Enhanced CDA Processor",
            "patient_data.services.enhanced_cda_processor",
            "EnhancedCDAProcessor",
        ),
    ]

    for name, module_path, class_name in components:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {name}: Import successful")

            # Try to instantiate
            try:
                if "WithMapping" in class_name:
                    instance = cls(target_language="en")
                else:
                    instance = cls(target_language="en")
                print(f"✅ {name}: Instantiation successful")
            except Exception as e:
                print(f"❌ {name}: Instantiation failed - {e}")
                traceback.print_exc()

        except Exception as e:
            print(f"❌ {name}: Import failed - {e}")
            traceback.print_exc()


def debug_json_mapping():
    """Debug JSON mapping file loading"""

    print("\n📄 Debugging JSON Mapping File")
    print("=" * 40)

    try:
        from patient_data.services.enhanced_cda_field_mapper import (
            EnhancedCDAFieldMapper,
        )

        # Try to load mapper
        mapper = EnhancedCDAFieldMapper()
        print("✅ JSON mapping file loaded successfully")

        # Check mapping summary
        summary = mapper.get_mapping_summary()
        print(
            f"✅ Mapping summary: {summary['total_sections']} sections, {summary['total_fields']} fields"
        )

        # Test with a simple XPath
        import xml.etree.ElementTree as ET

        simple_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <recordTarget>
                <patientRole>
                    <patient>
                        <name>
                            <given>Test</given>
                            <family>Patient</family>
                        </name>
                    </patient>
                </patientRole>
            </recordTarget>
        </ClinicalDocument>"""

        root = ET.fromstring(simple_xml)
        namespaces = {"hl7": "urn:hl7-org:v3"}

        # Test patient mapping
        patient_data = mapper.map_patient_data(root, namespaces)
        print(f"✅ Patient mapping test: {len(patient_data)} fields mapped")

        for field, info in patient_data.items():
            if info.get("value"):
                print(f"   ✅ {field}: {info['value']}")

    except Exception as e:
        print(f"❌ JSON mapping debug failed: {e}")
        traceback.print_exc()


def debug_view_integration():
    """Debug Django view integration"""

    print("\n🌐 Debugging Django View Integration")
    print("=" * 45)

    try:
        # Test the patient_cda_view function directly
        from patient_data.views import patient_cda_view
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        from patient_data.models import PatientData

        # Create a test request
        factory = RequestFactory()
        request = factory.get("/patient/1/")

        # Create a test user
        try:
            user = User.objects.get(username="testuser")
        except User.DoesNotExist:
            user = User.objects.create_user("testuser", "test@example.com", "password")
        request.user = user

        # Add session
        from django.contrib.sessions.backends.db import SessionStore

        session = SessionStore()
        session.create()
        request.session = session

        # Test if we can at least import and inspect the view
        import inspect

        source_lines = inspect.getsourcelines(patient_cda_view)[0]

        # Check for our new imports
        has_mapping_import = any(
            "EnhancedCDAProcessorWithMapping" in line for line in source_lines
        )
        has_mapping_instantiation = any(
            "EnhancedCDAProcessorWithMapping(" in line for line in source_lines
        )
        has_mapping_method = any(
            "process_clinical_document" in line for line in source_lines
        )

        print(f"✅ View function accessible")
        print(f"✅ Mapping import: {'Yes' if has_mapping_import else 'No'}")
        print(
            f"✅ Mapping instantiation: {'Yes' if has_mapping_instantiation else 'No'}"
        )
        print(f"✅ Mapping method: {'Yes' if has_mapping_method else 'No'}")

        if not all([has_mapping_import, has_mapping_instantiation, has_mapping_method]):
            print("❌ View integration incomplete - some elements missing")
        else:
            print("✅ View integration appears complete")

    except Exception as e:
        print(f"❌ View integration debug failed: {e}")
        traceback.print_exc()


def debug_specific_patient():
    """Debug processing of a specific patient"""

    print("\n👤 Debugging Specific Patient Processing")
    print("=" * 45)

    # Use the LU patient we know exists
    cda_path = "test_data/eu_member_states/LU/CELESTINA_DOE-CALLA_38430827_3.xml"

    if os.path.exists(cda_path):
        try:
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()
            print(f"✅ Loaded CDA: {len(cda_content)} characters")

            # Test with the new processor
            from patient_data.services.enhanced_cda_processor_with_mapping import (
                EnhancedCDAProcessorWithMapping,
            )

            processor = EnhancedCDAProcessorWithMapping(target_language="en")
            print("✅ Processor instantiated")

            # Process the document
            result = processor.process_clinical_document(
                cda_content=cda_content, source_language="en"
            )

            if result.get("success"):
                print("✅ Processing successful")
                print(
                    f"   Clinical sections: {len(result.get('clinical_sections', []))}"
                )
                print(f"   Mapped sections: {len(result.get('mapped_sections', {}))}")
                print(f"   Patient data fields: {len(result.get('patient_data', {}))}")
            else:
                print(f"❌ Processing failed: {result.get('error')}")

        except Exception as e:
            print(f"❌ Patient processing failed: {e}")
            traceback.print_exc()
    else:
        print(f"❌ Patient CDA not found: {cda_path}")


def debug_server_error():
    """Try to reproduce the server error"""

    print("\n🚨 Debugging Server Error Reproduction")
    print("=" * 45)

    try:
        # Simulate what happens when a patient is loaded in the web interface
        from patient_data.models import PatientData
        from django.contrib.sessions.backends.db import SessionStore

        # Check if there are any patients in the database
        patients = PatientData.objects.all()[:5]
        print(f"✅ Found {len(patients)} patients in database")

        if patients:
            patient = patients[0]
            print(
                f"✅ Testing with patient: {patient.given_name} {patient.family_name}"
            )

            # Simulate session data that might be used
            session = SessionStore()
            session.create()

            match_data = {
                "patient_id": patient.id,
                "country_code": "LU",
                "confidence_score": 1.0,
                "cda_content": "",  # This might be the issue - empty CDA content
                "patient_data": {
                    "given_name": patient.given_name,
                    "family_name": patient.family_name,
                    "birth_date": str(patient.birth_date) if patient.birth_date else "",
                    "gender": patient.gender,
                },
            }

            session[f"patient_match_{patient.id}"] = match_data
            session.save()

            print("✅ Session data simulated")
            print(f"   CDA content length: {len(match_data.get('cda_content', ''))}")

            if not match_data.get("cda_content"):
                print("❌ FOUND ISSUE: Empty CDA content in session data")
                print("   This would cause the 'Failed' translation status")

    except Exception as e:
        print(f"❌ Server error debug failed: {e}")
        traceback.print_exc()


def main():
    """Run comprehensive debugging"""

    print("🐛 JSON Field Mapping Deployment Debugging")
    print("=" * 70)

    # Run all debug tests
    debug_import_issues()
    debug_json_mapping()
    debug_view_integration()
    debug_specific_patient()
    debug_server_error()

    print("\n🎯 Debugging Summary:")
    print("=" * 25)
    print("Check the output above for any ❌ errors")
    print("Focus on fixing the first error found")
    print("The 'Failed' status likely indicates empty CDA content or import issues")


if __name__ == "__main__":
    main()
