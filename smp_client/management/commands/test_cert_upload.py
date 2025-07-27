from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from smp_client.models import SigningCertificate
import os


class Command(BaseCommand):
    help = "Test certificate upload functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test", action="store_true", help="Create a test certificate entry"
        )
        parser.add_argument("--list", action="store_true", help="List all certificates")
        parser.add_argument(
            "--clear", action="store_true", help="Clear all certificates"
        )

    def handle(self, *args, **options):
        if options["list"]:
            self.list_certificates()
        elif options["clear"]:
            self.clear_certificates()
        elif options["test"]:
            self.create_test_certificate()
        else:
            self.stdout.write("Use --list, --clear, or --test")

    def list_certificates(self):
        certs = SigningCertificate.objects.all()
        self.stdout.write(f"Found {certs.count()} certificates:")
        for cert in certs:
            self.stdout.write(f"  - {cert.certificate_name}")
            self.stdout.write(f"    File: {cert.certificate_file}")
            self.stdout.write(f"    Active: {cert.is_active}")
            self.stdout.write(
                f'    Valid: {cert.is_valid if cert.valid_from and cert.valid_to else "Unknown"}'
            )
            self.stdout.write("---")

    def clear_certificates(self):
        count = SigningCertificate.objects.count()
        SigningCertificate.objects.all().delete()
        self.stdout.write(f"Deleted {count} certificates")

    def create_test_certificate(self):
        # Create a dummy certificate content (this is just for testing upload)
        test_cert_content = """-----BEGIN CERTIFICATE-----
MIICdTCCAV0CAQAwDQYJKoZIhvcNAQEEBQAwPTELMAkGA1UEBhMCVVMxCzAJBgNV
BAgTAlVTMQswCQYDVQQKEwJVUzEUMBIGA1UEAxMLVGVzdCBDZXJ0Q0EwHhcNMjQw
MTAxMDAwMDAwWhcNMjUwMTAxMDAwMDAwWjA9MQswCQYDVQQGEwJVUzELMAkGA1UE
CBMCVVMxCzAJBgNVBAoTAlVTMRQwEgYDVQQDEwtUZXN0IENlcnRDQTCBnzANBgkq
hkiG9w0BAQEFAAOBjQAwgYkCgYEAtest
-----END CERTIFICATE-----"""

        # Create a test certificate
        cert_file = ContentFile(test_cert_content.encode(), name="test_certificate.pem")

        cert = SigningCertificate.objects.create(
            certificate_name="Test Certificate Upload",
            certificate_type="X.509",
            certificate_file=cert_file,
            subject="CN=Test Certificate, O=Test Org, C=US",
            issuer="CN=Test CA, O=Test Org, C=US",
            serial_number="123456789",
            is_active=True,
            is_default=False,
        )

        self.stdout.write(f"Created test certificate: {cert.certificate_name}")
        self.stdout.write(f"File path: {cert.certificate_file.path}")
        self.stdout.write(f"File exists: {os.path.exists(cert.certificate_file.path)}")
