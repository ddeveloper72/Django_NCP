"""
Django management command to setup initial EU eHealth NCP data
Based on ehealth-3 project requirements
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ncp_gateway.models import Country, Organization, HealthcareProfessional, Patient
from datetime import date, datetime
import logging

logger = logging.getLogger("ehealth")


class Command(BaseCommand):
    help = "Setup initial EU eHealth NCP countries, organizations, and test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset all data before setup",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting all NCP data..."))
            Country.objects.all().delete()
            Organization.objects.all().delete()
            Patient.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("Setting up EU eHealth NCP infrastructure...")
        )

        # Setup EU Countries and NCP endpoints
        countries_data = [
            {
                "code": "IE",
                "name": "Ireland",
                "ncp_endpoint": "http://localhost:8001",
                "is_active": True,
            },
            {
                "code": "BE",
                "name": "Belgium",
                "ncp_endpoint": "https://be-ncp.ehealth.be",
                "is_active": True,
            },
            {
                "code": "AT",
                "name": "Austria",
                "ncp_endpoint": "https://at-ncp.ehealth.at",
                "is_active": True,
            },
            {
                "code": "HU",
                "name": "Hungary",
                "ncp_endpoint": "https://hu-ncp.ehealth.hu",
                "is_active": True,
            },
            {
                "code": "EU",
                "name": "European Commission",
                "ncp_endpoint": "https://ec-ncp.europa.eu",
                "is_active": True,
            },
        ]

        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                code=country_data["code"],
                defaults={
                    "name": country_data["name"],
                    "ncp_endpoint": country_data["ncp_endpoint"],
                    "is_active": country_data["is_active"],
                },
            )
            if created:
                self.stdout.write(f"Created country: {country.name}")
            else:
                self.stdout.write(f"Country exists: {country.name}")

        # Setup Ireland Health Service Executive
        ireland = Country.objects.get(code="IE")
        hse, created = Organization.objects.get_or_create(
            identifier="ie-hse",
            defaults={
                "name": "Health Service Executive",
                "country": ireland,
                "organization_type": "primary_care",
                "contact_email": "ncp@hse.ie",
                "address": "Dr. Steevens Hospital, Dublin 8, Ireland",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write("Created HSE organization")

        # Setup test healthcare professional
        admin_user = User.objects.get(username="admin")
        hcp, created = HealthcareProfessional.objects.get_or_create(
            user=admin_user,
            defaults={
                "professional_id": "IE-NCP-001",
                "license_number": "IE-NCP-001",
                "speciality": "Digital Health",
                "organization": hse,
                "is_active": True,
                "is_authorized_cross_border": True,
                "authorization_level": "full_access",
            },
        )
        if created:
            self.stdout.write("Created test healthcare professional")

        # Setup test patients for each country
        test_patients = [
            {
                "national_id": "IE-12345678",
                "european_id": "EU-IE-12345678",
                "first_name": "Sean",
                "last_name": "Murphy",
                "birth_date": date(1985, 3, 15),
                "gender": "M",
                "country_of_origin": ireland,
                "insurance_number": "HSE-001",
                "cross_border_consent": True,
                "consent_date": datetime.now(),
            },
            {
                "national_id": "IE-87654321",
                "european_id": "EU-IE-87654321",
                "first_name": "Áine",
                "last_name": "O'Brien",
                "birth_date": date(1992, 7, 22),
                "gender": "F",
                "country_of_origin": ireland,
                "insurance_number": "HSE-002",
                "cross_border_consent": True,
                "consent_date": datetime.now(),
            },
        ]

        for patient_data in test_patients:
            patient, created = Patient.objects.get_or_create(
                national_id=patient_data["national_id"], defaults=patient_data
            )
            if created:
                self.stdout.write(
                    f"Created test patient: {patient.first_name} {patient.last_name}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully setup EU eHealth NCP infrastructure!\n"
                "You can now:\n"
                "1. Access Django Admin to manage countries and patients\n"
                "2. Test cross-border patient lookup\n"
                "3. Configure FHIR services\n"
                "4. Review audit logs"
            )
        )
