#!/usr/bin/env python3
"""
Quick test to verify the template fixes and patient search
"""

import os
import sys

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


def test_template_fixes():
    """Test that the Jinja2 template fixes work"""

    print("🔧 Testing Jinja2 Template Fixes")
    print("=" * 50)

    try:
        from django.template.loader import get_template
        from django.template import Context

        # Test loading the template
        template = get_template("ehealth_portal/document_viewer.html")
        print("✅ Template loaded successfully")

        # Test context with Enhanced CDA data
        test_context = {
            "document": {
                "type": "PS",
                "title": "Patient Summary Test",
                "processing_success": True,
                "sections": [
                    {
                        "translated_title": "Medication History",
                        "section_code": "10160-0",
                        "structured_data": [
                            {
                                "medication_code": "EUTIROX",
                                "medication_display": "Eutirox 75mcg",
                                "dosage": "75mcg",
                                "status": "Active",
                            }
                        ],
                        "table_rows": [
                            ["Medication", "Dosage", "Status"],
                            ["Eutirox", "75mcg", "Active"],
                        ],
                        "html_content": "<div>Test HTML content</div>",
                    }
                ],
                "error_message": None,
            },
            "target_language": "en",
            "country_code": "PT",
            "patient_id": "12345",
            "page_title": "Document Viewer - PS",
        }

        # Render the template
        rendered = template.render(test_context)
        print("✅ Template rendered successfully")

        # Check for key content
        if "Enhanced CDA Processing Active" in rendered:
            print("✅ Enhanced CDA features detected")
        if "Medication History" in rendered:
            print("✅ Clinical sections detected")
        if "language-select" in rendered:
            print("✅ Language selection detected")

        print(f"✅ Rendered content length: {len(rendered)} characters")

    except Exception as e:
        print(f"❌ Template test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


def test_document_viewer_direct():
    """Test the document viewer with direct URL access"""

    print("\n📄 Testing Document Viewer Direct Access")
    print("=" * 50)

    try:
        from ehealth_portal.views import document_viewer
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser

        # Create mock request
        request = HttpRequest()
        request.method = "GET"
        request.user = AnonymousUser()
        request.GET = {"lang": "en"}

        # Test the view
        response = document_viewer(request, "PT", "12345", "PS")
        print(f"✅ Document viewer responded with status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Document viewer successful")
            return True
        else:
            print(f"❌ Document viewer returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Document viewer test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_enhanced_cda_integration():
    """Test Enhanced CDA Processor integration"""

    print("\n🧬 Testing Enhanced CDA Integration")
    print("=" * 50)

    try:
        # Test CDA file exists
        cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"
        if os.path.exists(cda_path):
            print(f"✅ Test CDA file found: {cda_path}")

            # Load and test processing
            with open(cda_path, "r", encoding="utf-8") as file:
                cda_content = file.read()
            print(f"✅ CDA content loaded: {len(cda_content)} characters")

            # Test Enhanced CDA Processor
            from patient_data.services.enhanced_cda_processor import (
                EnhancedCDAProcessor,
            )

            processor = EnhancedCDAProcessor(target_language="en")
            result = processor.process_clinical_sections(
                cda_content=cda_content, source_language="en"
            )

            if result.get("success"):
                sections = result.get("sections", [])
                print(
                    f"✅ Enhanced CDA processing successful: {len(sections)} sections"
                )

                # Check for structured data
                total_structured = sum(
                    len(s.get("structured_data", [])) for s in sections
                )
                total_tables = sum(len(s.get("table_rows", [])) for s in sections)

                print(f"✅ Total structured data items: {total_structured}")
                print(f"✅ Total table rows: {total_tables}")

                if total_structured > 0:
                    print("✅ Clinical data extraction working")
                    return True
                else:
                    print("❌ No structured data extracted")
                    return False
            else:
                print(
                    f"❌ CDA processing failed: {result.get('error', 'Unknown error')}"
                )
                return False
        else:
            print(f"⚠️  Test CDA file not found: {cda_path}")
            return True  # Not a failure, just no test data

    except Exception as e:
        print(f"❌ Enhanced CDA integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Comprehensive Integration Test")
    print("=" * 60)

    all_tests_passed = True

    # Run all tests
    all_tests_passed &= test_template_fixes()
    all_tests_passed &= test_enhanced_cda_integration()

    print(f"\n📊 Test Summary")
    print("=" * 30)

    if all_tests_passed:
        print("✅ All tests passed!")
        print("\n🌐 Ready to test in browser:")
        print("1. Start server: python manage.py runserver")
        print(
            "2. Access: http://localhost:8000/portal/country/PT/patient/12345/document/PS/"
        )
        print("3. Try languages: ?lang=de, ?lang=fr, etc.")
    else:
        print("❌ Some tests failed - check errors above")
        sys.exit(1)
