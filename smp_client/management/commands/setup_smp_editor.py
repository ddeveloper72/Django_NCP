"""
Sample data setup for SMP Editor
Creates document templates and sample certificates
"""

import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from smp_client.models import (
    DocumentTemplate,
    SigningCertificate,
    DocumentType,
    DocumentTypeScheme,
)


class Command(BaseCommand):
    help = "Setup SMP Editor with sample templates and certificates"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up SMP Editor..."))

        # Create admin user if it doesn't exist
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@localhost")

        if not admin_password:
            self.stdout.write(
                self.style.ERROR(
                    "ADMIN_PASSWORD environment variable not set. Please set it in your .env file."
                )
            )
            return

        admin_user, created = User.objects.get_or_create(
            username=admin_username,
            defaults={
                "email": admin_email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password(admin_password)
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Created admin user: {admin_username}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Admin user {admin_username} already exists")
            )

        # Create sample document templates
        templates_data = [
            {
                "template_name": "eHealth Service Group Template",
                "document_type": "service_group",
                "description": "Standard template for eHealth service groups",
                "xml_template": """<?xml version="1.0" encoding="UTF-8"?>
<ServiceGroup xmlns="http://docs.oasis-open.org/bdxr/ns/SMP/2016/05">
    <ParticipantIdentifier scheme="{participant_scheme}">{participant_id}</ParticipantIdentifier>
    <ServiceMetadataReferenceCollection>
        <!-- Service metadata references will be generated automatically -->
    </ServiceMetadataReferenceCollection>
</ServiceGroup>""",
                "is_default": True,
            },
            {
                "template_name": "eHealth Service Metadata Template",
                "document_type": "service_metadata",
                "description": "Standard template for eHealth service metadata",
                "xml_template": """<?xml version="1.0" encoding="UTF-8"?>
<ServiceMetadata xmlns="http://docs.oasis-open.org/bdxr/ns/SMP/2016/05">
    <ServiceInformation>
        <ParticipantIdentifier scheme="{participant_scheme}">{participant_id}</ParticipantIdentifier>
        <DocumentIdentifier scheme="{document_scheme}">{document_id}</DocumentIdentifier>
        <ProcessList>
            <Process>
                <ProcessIdentifier scheme="{process_scheme}">{process_id}</ProcessIdentifier>
                <ServiceEndpointList>
                    <Endpoint transportProfile="bdxr-transport-ebms3-as4-v1p0">
                        <EndpointURI>{endpoint_url}</EndpointURI>
                        <ServiceDescription>{service_description}</ServiceDescription>
                        <TechnicalContactUrl>{contact_url}</TechnicalContactUrl>
                        <Certificate>{certificate}</Certificate>
                    </Endpoint>
                </ServiceEndpointList>
            </Process>
        </ProcessList>
    </ServiceInformation>
</ServiceMetadata>""",
                "is_default": True,
            },
            {
                "template_name": "eHealth Endpoint Template",
                "document_type": "endpoint",
                "description": "Standard template for eHealth endpoints",
                "xml_template": """<?xml version="1.0" encoding="UTF-8"?>
<Endpoint xmlns="http://docs.oasis-open.org/bdxr/ns/SMP/2016/05" transportProfile="bdxr-transport-ebms3-as4-v1p0">
    <EndpointURI>{endpoint_url}</EndpointURI>
    <ServiceActivationDate>{activation_date}</ServiceActivationDate>
    <ServiceExpirationDate>{expiration_date}</ServiceExpirationDate>
    <Certificate>{certificate}</Certificate>
    <ServiceDescription>{service_description}</ServiceDescription>
    <TechnicalContactUrl>{contact_url}</TechnicalContactUrl>
</Endpoint>""",
                "is_default": True,
            },
        ]

        for template_data in templates_data:
            template, created = DocumentTemplate.objects.get_or_create(
                template_name=template_data["template_name"],
                document_type=template_data["document_type"],
                defaults=template_data,
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created template: {template.template_name}")
                )

        # Create sample signing certificate
        cert_data = {
            "certificate_name": "eHealth Test Certificate",
            "certificate_type": "X.509",
            "subject": "CN=eHealth Test,O=Test Organization,C=EU",
            "issuer": "CN=Test CA,O=Test Authority,C=EU",
            "serial_number": "123456789",
            "fingerprint": "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90",
            "is_default": True,
            "is_active": True,
        }

        certificate, created = SigningCertificate.objects.get_or_create(
            certificate_name=cert_data["certificate_name"], defaults=cert_data
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created certificate: {certificate.certificate_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("SMP Editor setup completed successfully!")
        )
        self.stdout.write(self.style.WARNING("You can now:"))
        self.stdout.write("• Login as admin/admin123")
        self.stdout.write("• Access SMP Editor at /smp/editor/")
        self.stdout.write("• Generate, sign, and upload SMP documents")
        self.stdout.write("• Manage documents at /smp/documents/")
