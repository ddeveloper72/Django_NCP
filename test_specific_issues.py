#!/usr/bin/env python3
"""
Test the specific URL that's causing issues
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


def test_problem_url():
    """Test the specific URL that's failing"""

    print("🔍 Testing Problem URL")
    print("URL: /portal/country/PT/patient/12345/document/PS/")
    print("=" * 60)

    try:
        from django.test import Client
        from django.contrib.auth.models import User

        # Create test client
        client = Client()

        # Create test user
        user, created = User.objects.get_or_create(
            username="testuser", defaults={"email": "test@example.com"}
        )
        if created:
            user.set_password("testpass")
            user.save()

        # Login the user
        client.force_login(user)

        # Test the problematic URL
        response = client.get("/portal/country/PT/patient/12345/document/PS/")

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            print("✅ URL working successfully!")
            print("✅ Template syntax errors fixed!")

            # Check response content
            content = response.content.decode("utf-8")

            if "Enhanced CDA Processing" in content:
                print("✅ Enhanced CDA Processing detected")
            if "Language & Processing Options" in content:
                print("✅ Language options detected")
            if "Document Viewer" in content:
                print("✅ Document viewer loaded")

        elif response.status_code == 500:
            print("❌ Server error (500)")
            print("This suggests there may still be template syntax issues")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ URL test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_patient_search_mock():
    """Test the patient search functionality"""

    print("\n👤 Testing Patient Search")
    print("=" * 40)

    try:
        from ehealth_portal.models import Country
        from ehealth_portal.views import perform_patient_search
        from django.contrib.auth.models import User

        # Get or create Portugal
        country, created = Country.objects.get_or_create(
            code="PT",
            defaults={
                "name": "Portugal",
                "ncp_url": "https://ncp.portugal.pt/",
                "smp_url": "https://smp.portugal.pt/",
                "is_available": True,
            },
        )

        # Get test user
        user = User.objects.get(username="testuser")

        # Test search with Portuguese Wave 7 patient ID
        search_fields = {
            "patient_id": "2-1234-W7",
            "family_name": "Ferreira",
            "given_name": "Diana",
        }

        result = perform_patient_search(country, search_fields, user)

        print(f"Search result - Patient found: {result.patient_found}")
        if result.patient_found:
            print(f"✅ Patient search successful")
            print(f"Patient data: {result.patient_data}")
            print(f"Available documents: {len(result.available_documents)} documents")
        else:
            print(f"❌ Patient search failed: {result.error_message}")

        return result.patient_found

    except Exception as e:
        print(f"❌ Patient search test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing Specific Issues")
    print("=" * 50)

    # Test the problematic URL
    url_success = test_problem_url()

    # Test patient search
    search_success = test_patient_search_mock()

    print(f"\n📊 Results Summary")
    print("=" * 30)
    print(f"URL Test: {'✅ PASS' if url_success else '❌ FAIL'}")
    print(f"Patient Search: {'✅ PASS' if search_success else '❌ FAIL'}")

    if url_success and search_success:
        print("\n🎉 All issues resolved!")
        print("The template syntax errors have been fixed.")
        print("You can now test the application in your browser.")
    else:
        print("\n⚠️  Some issues remain - check the details above.")
