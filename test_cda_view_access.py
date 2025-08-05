#!/usr/bin/env python
"""
Quick test to validate CDA view works with database patients
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_cda_view_access():
    """Test accessing CDA view directly"""

    # Create test client
    client = Client()

    # Create test user and login
    try:
        user = User.objects.get(username="testuser")
    except User.DoesNotExist:
        user = User.objects.create_user("testuser", "test@example.com", "testpass")

    client.login(username="testuser", password="testpass")

    # Try to access CDA view for patient 796212
    url = "/patients/cda/796212/"
    print(f"Testing URL: {url}")

    response = client.get(url)

    print(f"Response status: {response.status_code}")
    print(f"Response location: {response.get('Location', 'None')}")

    if response.status_code == 302:
        print("❌ CDA view redirected (not displaying)")
        print("This means there's still an issue with session data or patient lookup")
    elif response.status_code == 200:
        print("✅ CDA view displayed successfully!")
        print("Content length:", len(response.content))
    else:
        print(f"❓ Unexpected status code: {response.status_code}")

    return response.status_code == 200


if __name__ == "__main__":
    print("Testing CDA view access...")
    success = test_cda_view_access()

    if success:
        print("\n🎉 CDA view is now accessible!")
    else:
        print("\n🔧 CDA view still needs debugging")
        print("Check the logs for specific error messages")

    sys.exit(0 if success else 1)
