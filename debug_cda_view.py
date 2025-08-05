#!/usr/bin/env python
"""
Direct CDA view debug test to identify the exact error
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.conf import settings

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_direct_cda_access():
    """Test what happens when we call the CDA view directly"""

    # Import Django components
    from django.http import HttpRequest
    from django.contrib.auth.models import AnonymousUser, User
    from django.contrib.sessions.backends.db import SessionStore
    from django.contrib.messages.storage.fallback import FallbackStorage
    from patient_data.views import patient_cda_view

    print("🔧 Testing direct CDA view access...")

    try:
        # Create a test user
        try:
            user = User.objects.get(username="testuser")
        except User.DoesNotExist:
            user = User.objects.create_user("testuser", "test@example.com", "testpass")

        # Create a mock request
        request = HttpRequest()
        request.user = user
        request.method = "GET"
        request.path = "/patients/cda/289292/"

        # Add session support
        session = SessionStore()
        session.save()
        request.session = session

        # Add messages support
        messages = FallbackStorage(request)
        request._messages = messages

        print(f"📋 Request setup complete")
        print(f"   - User: {request.user}")
        print(f"   - Session key: {request.session.session_key}")
        print(f"   - Path: {request.path}")

        # Call the view directly
        print("🚀 Calling patient_cda_view directly...")
        response = patient_cda_view(request, patient_id="289292")

        print(f"✅ View executed successfully!")
        print(f"   - Response type: {type(response).__name__}")
        print(f"   - Status code: {getattr(response, 'status_code', 'N/A')}")

        if hasattr(response, "url"):
            print(f"   - Redirect URL: {response.url}")

        if hasattr(response, "content"):
            content_length = len(response.content) if response.content else 0
            print(f"   - Content length: {content_length}")

        return True

    except Exception as e:
        print(f"❌ Error calling CDA view: {e}")
        import traceback

        print(f"📋 Full traceback:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_direct_cda_access()

    if success:
        print("\n🎉 Direct view call succeeded!")
        print("The issue might be authentication, middleware, or URL routing.")
    else:
        print("\n🔧 Direct view call failed!")
        print("This shows the exact error that's causing the redirect.")
