#!/usr/bin/env python
"""
Test script for real-time certificate parsing AJAX endpoint
"""
import os
import sys
import django

# Add the project to Python path
sys.path.append("/c/Users/Duncan/VS_Code_Projects/django_ncp")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


def test_ajax_endpoint():
    """Test the AJAX certificate parsing endpoint"""
    print("Testing AJAX Certificate Parsing Endpoint")
    print("=" * 50)

    # Create test client
    client = Client()

    # Create or get admin user for authentication
    try:
        admin_user = User.objects.get(username="admin")
    except User.DoesNotExist:
        admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "admin123"
        )

    # Login as admin
    client.force_login(admin_user)

    # Create a test certificate file
    test_cert_content = b"""-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTcwNzEwMTUwOTU0WhcNMTgwNzEwMTUwOTU0WjBF
-----END CERTIFICATE-----"""

    test_file = SimpleUploadedFile(
        "test_cert.pem", test_cert_content, content_type="application/x-pem-file"
    )

    # Test the AJAX endpoint
    print("📤 Sending certificate to AJAX endpoint...")
    response = client.post(
        "/smp_client/ajax/parse-certificate/", {"certificate_file": test_file}
    )

    print(f"📥 Response status: {response.status_code}")

    if response.status_code == 200:
        import json

        data = json.loads(response.content)
        print(f"✅ Success: {data.get('success', False)}")

        if data.get("success"):
            print("📋 Certificate Information Extracted:")
            info = data.get("info", {})
            for key, value in info.items():
                print(f"   {key}: {value}")

            warnings = data.get("warnings", [])
            if warnings:
                print(f"⚠️  Warnings: {warnings}")
            else:
                print("✅ No warnings")
        else:
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

    print("\n" + "=" * 50)
    print("🎯 AJAX Endpoint Test Complete!")
    print("\n🚀 Ready for Real-Time Certificate Parsing!")
    print("   • Open: http://127.0.0.1:8000/admin/smp_client/signingcertificate/add/")
    print("   • Select a certificate file")
    print("   • Watch fields populate instantly!")


if __name__ == "__main__":
    test_ajax_endpoint()
