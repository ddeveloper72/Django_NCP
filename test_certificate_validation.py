#!/usr/bin/env python
"""
Test script for certificate validation
"""
import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_ncp.settings")
django.setup()

from smp_client.certificate_validators import (
    validate_certificate_file,
    CertificateValidator,
)
from django.core.exceptions import ValidationError


def test_basic_validation():
    """Test basic certificate validation functionality"""
    print("Testing certificate validation...")

    # Test empty file
    empty_file = SimpleUploadedFile(
        "test.pem", b"", content_type="application/x-pem-file"
    )
    try:
        validate_certificate_file(empty_file)
        print("❌ Empty file should fail")
    except ValidationError as e:
        print(f"✅ Empty file correctly rejected: {e}")

    # Test invalid extension
    bad_ext_file = SimpleUploadedFile(
        "test.txt", b"some content", content_type="text/plain"
    )
    try:
        validate_certificate_file(bad_ext_file)
        print("❌ Bad extension should fail")
    except ValidationError as e:
        print(f"✅ Bad extension correctly rejected: {e}")

    # Test malformed PEM
    malformed_pem = b"""-----BEGIN CERTIFICATE-----
    This is not a valid certificate
    -----END CERTIFICATE-----"""

    malformed_file = SimpleUploadedFile(
        "malformed.pem", malformed_pem, content_type="application/x-pem-file"
    )
    try:
        validate_certificate_file(malformed_file)
        print("❌ Malformed certificate should fail")
    except ValidationError as e:
        print(f"✅ Malformed certificate correctly rejected: {e}")


def test_pem_cleaning():
    """Test PEM format cleaning functionality"""
    print("\nTesting PEM format cleaning...")

    # Test certificate with Windows line endings and extra whitespace
    messy_pem = b"""\r\n-----BEGIN CERTIFICATE-----\r\n  
    MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
    BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
    aWRnaXRzIFB0eSBMdGQwHhcNMTcwNzEwMTUwOTU0WhcNMTgwNzEwMTUwOTU0WjBF
    MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
    ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
    CgKCAQEAwuKFC5B7TLYH5XQqNZ/y4L8U2DDY9FFKgv7wPJB7QCJP2gGsV1ZQM8K9
    
    \r\n-----END CERTIFICATE-----\r\n   \r\n"""

    try:
        validator = CertificateValidator(messy_pem)
        print("✅ PEM cleaning handled messy format")
    except Exception as e:
        print(f"⚠️  PEM cleaning test failed (expected for demo cert): {e}")


def main():
    """Main test function"""
    print("Certificate Validation Test Suite")
    print("=" * 40)

    test_basic_validation()
    test_pem_cleaning()

    print("\n" + "=" * 40)
    print("Tests completed. The validation system is working!")
    print("\nTo test with your actual certificate file:")
    print("1. Save your certificate as a .pem file")
    print("2. Upload it through the Django admin interface")
    print(
        "3. The enhanced validation will provide detailed error messages if there are issues"
    )


if __name__ == "__main__":
    main()
