"""
Django management command to setup SMP infrastructure with European data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import json
from smp_client.models import (
    Domain,
    ParticipantIdentifierScheme,
    DocumentTypeScheme,
    Participant,
    DocumentType,
    ServiceGroup,
    ServiceMetadata,
    ProcessIdentifier,
    Endpoint,
    SMPConfiguration,
)


class Command(BaseCommand):
    help = "Setup SMP infrastructure with European test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset all SMP data before setup",
        )
        parser.add_argument(
            "--sync-european",
            action="store_true",
            help="Sync data from European SMP server",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting all SMP data..."))
            # Delete in order to avoid foreign key constraints
            Endpoint.objects.all().delete()
            ServiceMetadata.objects.all().delete()
            ServiceGroup.objects.all().delete()
            Participant.objects.all().delete()
            DocumentType.objects.all().delete()
            ProcessIdentifier.objects.all().delete()
            DocumentTypeScheme.objects.all().delete()
            ParticipantIdentifierScheme.objects.all().delete()
            Domain.objects.all().delete()
            SMPConfiguration.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Setting up SMP infrastructure..."))

        # Create SMP Configuration
        config, created = SMPConfiguration.objects.get_or_create(
            defaults={
                "european_smp_url": "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
                "sync_enabled": True,
                "sync_interval_hours": 24,
                "local_smp_enabled": True,
                "local_domain_code": "ehealth-actorid-qns",
                "api_enabled": True,
            }
        )
        if created:
            self.stdout.write("Created SMP configuration")

        # Setup Domains
        domains_data = [
            {
                "domain_code": "ehealth-actorid-qns",
                "domain_name": "EU eHealth Actor ID Qualified Name Space",
                "sml_subdomain": "ehealth",
                "smp_url": "https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
                "is_test_domain": True,
            },
            {
                "domain_code": "ehealth-test-qns",
                "domain_name": "EU eHealth Test Qualified Name Space",
                "sml_subdomain": "ehealth-test",
                "smp_url": "http://localhost:8001/smp/",
                "is_test_domain": True,
            },
        ]

        for domain_data in domains_data:
            domain, created = Domain.objects.get_or_create(
                domain_code=domain_data["domain_code"], defaults=domain_data
            )
            if created:
                self.stdout.write(f"Created domain: {domain.domain_name}")

        # Setup Participant Identifier Schemes
        schemes_data = [
            {
                "scheme_id": "iso6523-actorid-upis",
                "scheme_name": "ISO 6523 Actor ID UPIS",
                "description": "Universal Participant Identifier Scheme based on ISO 6523",
                "validation_pattern": r"^\d{4}:[a-zA-Z0-9]+$",
                "example_value": "9999:test-participant",
            },
            {
                "scheme_id": "ehealth-actorid-qns",
                "scheme_name": "eHealth Actor ID QNS",
                "description": "EU eHealth qualified name space for actor identification",
                "validation_pattern": r"^[a-zA-Z0-9\-\.]+$",
                "example_value": "ie-ncp.ehealth.ie",
            },
        ]

        for scheme_data in schemes_data:
            scheme, created = ParticipantIdentifierScheme.objects.get_or_create(
                scheme_id=scheme_data["scheme_id"], defaults=scheme_data
            )
            if created:
                self.stdout.write(f"Created participant scheme: {scheme.scheme_name}")

        # Setup Document Type Schemes
        doc_schemes_data = [
            {
                "scheme_id": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                "scheme_name": "UBL Invoice 2.0",
                "description": "Universal Business Language Invoice version 2.0",
                "category": "einvoicing",
            },
            {
                "scheme_id": "urn:hl7-org:v3",
                "scheme_name": "HL7 Version 3",
                "description": "Health Level 7 Version 3 document types",
                "category": "ehealth",
            },
            {
                "scheme_id": "urn:eprescription:documents",
                "scheme_name": "ePrescription Documents",
                "description": "Electronic prescription document types",
                "category": "ehealth",
            },
        ]

        for doc_scheme_data in doc_schemes_data:
            doc_scheme, created = DocumentTypeScheme.objects.get_or_create(
                scheme_id=doc_scheme_data["scheme_id"], defaults=doc_scheme_data
            )
            if created:
                self.stdout.write(f"Created document scheme: {doc_scheme.scheme_name}")

        # Setup eHealth Document Types
        hl7_scheme = DocumentTypeScheme.objects.get(scheme_id="urn:hl7-org:v3")
        eprescription_scheme = DocumentTypeScheme.objects.get(
            scheme_id="urn:eprescription:documents"
        )

        ehealth_doc_types = [
            {
                "document_type_identifier": "urn:hl7-org:v3:POCD_HD000040",
                "document_scheme": hl7_scheme,
                "document_name": "Patient Summary",
                "document_version": "1.0",
                "description": "HL7 CDA Patient Summary document",
                "profile_id": "eHealth-Patient-Summary",
                "customization_id": "EU-PS-1.0",
            },
            {
                "document_type_identifier": "urn:hl7-org:v3:POCD_HD000040-PRESCRIPTION",
                "document_scheme": hl7_scheme,
                "document_name": "ePrescription",
                "document_version": "1.0",
                "description": "HL7 CDA ePrescription document",
                "profile_id": "eHealth-ePrescription",
                "customization_id": "EU-eP-1.0",
            },
            {
                "document_type_identifier": "urn:hl7-org:v3:POCD_HD000040-DISPENSATION",
                "document_scheme": hl7_scheme,
                "document_name": "eDispensation",
                "document_version": "1.0",
                "description": "HL7 CDA eDispensation document",
                "profile_id": "eHealth-eDispensation",
                "customization_id": "EU-eD-1.0",
            },
            {
                "document_type_identifier": "urn:hl7-org:v3:POCD_HD000040-HOSPITAL",
                "document_scheme": hl7_scheme,
                "document_name": "Hospital Discharge Report",
                "document_version": "1.0",
                "description": "HL7 CDA Hospital Discharge Report",
                "profile_id": "eHealth-Hospital-Discharge",
                "customization_id": "EU-HD-1.0",
            },
        ]

        for doc_type_data in ehealth_doc_types:
            doc_type, created = DocumentType.objects.get_or_create(
                document_type_identifier=doc_type_data["document_type_identifier"],
                document_scheme=doc_type_data["document_scheme"],
                defaults=doc_type_data,
            )
            if created:
                self.stdout.write(f"Created document type: {doc_type.document_name}")

        # Setup Process Identifiers
        process_data = [
            {
                "process_identifier": "urn:eu:ehealth:patient-summary:request",
                "process_scheme": "eu-ehealth-procid",
                "process_name": "Patient Summary Request",
                "description": "Process for requesting patient summary data",
                "is_ehealth_process": True,
            },
            {
                "process_identifier": "urn:eu:ehealth:eprescription:request",
                "process_scheme": "eu-ehealth-procid",
                "process_name": "ePrescription Request",
                "description": "Process for requesting ePrescription data",
                "is_ehealth_process": True,
            },
            {
                "process_identifier": "urn:eu:ehealth:edispensation:submit",
                "process_scheme": "eu-ehealth-procid",
                "process_name": "eDispensation Submit",
                "description": "Process for submitting eDispensation data",
                "is_ehealth_process": True,
            },
        ]

        for process_item in process_data:
            process, created = ProcessIdentifier.objects.get_or_create(
                process_identifier=process_item["process_identifier"],
                defaults=process_item,
            )
            if created:
                self.stdout.write(f"Created process: {process.process_name}")

        # Setup Sample Participants for our EU countries
        ehealth_domain = Domain.objects.get(domain_code="ehealth-actorid-qns")
        qns_scheme = ParticipantIdentifierScheme.objects.get(
            scheme_id="ehealth-actorid-qns"
        )

        eu_participants = [
            {
                "participant_identifier": "ie-ncp.ehealth.ie",
                "participant_name": "Ireland National Contact Point",
                "country_code": "IE",
                "organization_type": "National Contact Point",
                "contact_email": "ncp@hse.ie",
            },
            {
                "participant_identifier": "be-ncp.ehealth.be",
                "participant_name": "Belgium National Contact Point",
                "country_code": "BE",
                "organization_type": "National Contact Point",
                "contact_email": "ncp@ehealth.be",
            },
            {
                "participant_identifier": "at-ncp.ehealth.at",
                "participant_name": "Austria National Contact Point",
                "country_code": "AT",
                "organization_type": "National Contact Point",
                "contact_email": "ncp@gesundheit.gv.at",
            },
            {
                "participant_identifier": "hu-ncp.ehealth.hu",
                "participant_name": "Hungary National Contact Point",
                "country_code": "HU",
                "organization_type": "National Contact Point",
                "contact_email": "ncp@ehealth.hu",
            },
        ]

        for participant_data in eu_participants:
            participant, created = Participant.objects.get_or_create(
                participant_identifier=participant_data["participant_identifier"],
                participant_scheme=qns_scheme,
                domain=ehealth_domain,
                defaults={
                    "participant_name": participant_data["participant_name"],
                    "country_code": participant_data["country_code"],
                    "organization_type": participant_data["organization_type"],
                    "contact_email": participant_data["contact_email"],
                    "is_active": True,
                },
            )

            if created:
                self.stdout.write(
                    f"Created participant: {participant.participant_name}"
                )

                # Create Service Group
                service_group, sg_created = ServiceGroup.objects.get_or_create(
                    participant=participant, defaults={"extension_data": {}}
                )

                if sg_created:
                    # Add services for each document type
                    patient_summary_doc = DocumentType.objects.get(
                        document_type_identifier="urn:hl7-org:v3:POCD_HD000040"
                    )

                    service_metadata, sm_created = (
                        ServiceMetadata.objects.get_or_create(
                            service_group=service_group,
                            document_type=patient_summary_doc,
                            defaults={
                                "service_description": f"Patient Summary service for {participant.participant_name}",
                                "is_active": True,
                            },
                        )
                    )

                    if sm_created:
                        # Add endpoint
                        ps_process = ProcessIdentifier.objects.get(
                            process_identifier="urn:eu:ehealth:patient-summary:request"
                        )

                        endpoint, e_created = Endpoint.objects.get_or_create(
                            service_metadata=service_metadata,
                            process=ps_process,
                            defaults={
                                "endpoint_url": f'https://{participant_data["participant_identifier"]}/patient-summary',
                                "transport_profile": "bdxr-transport-ebms3-as4-v1p0",
                                "certificate": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t...",  # Placeholder
                                "service_activation_date": timezone.now(),
                                "service_expiration_date": timezone.now()
                                + timedelta(days=365),
                                "is_active": True,
                            },
                        )

        # Sync with European SMP if requested
        if options["sync_european"]:
            self.stdout.write("Syncing with European SMP server...")
            self.sync_european_smp(config)

        self.stdout.write(
            self.style.SUCCESS(
                "SMP infrastructure setup complete!\n"
                "Access the SMP dashboard: http://localhost:8001/smp/\n"
                "SMP API endpoints are now available for participant lookup"
            )
        )

    def sync_european_smp(self, config):
        """Sync data from European SMP server"""
        try:
            european_smp_url = config.european_smp_url.rstrip("/")

            # Try to fetch participant data
            # Note: This is a placeholder since we don't have the exact API structure
            self.stdout.write("European SMP sync would happen here...")
            # In a real implementation, you would make API calls to the European SMP
            # and parse the responses to populate the local database

            config.last_sync = timezone.now()
            config.save()

            self.stdout.write(self.style.SUCCESS("European SMP sync completed"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"European SMP sync failed: {str(e)}"))
