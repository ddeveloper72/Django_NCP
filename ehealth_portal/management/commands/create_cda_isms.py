"""
Management command to create ISM configurations for CDA test countries
Based on actual eHDSI ISM requirements from MS_ISM_Specific_Parameters.csv
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from ehealth_portal.models import (
    Country,
    InternationalSearchMask,
    SearchField,
    SearchFieldType,
)


class Command(BaseCommand):
    help = "Create ISM configurations for CDA test countries"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Creating ISM configurations for CDA test countries...")
        )

        # Based on your MS_ISM_Specific_Parameters.csv data
        country_ism_configs = {
            "GR": {
                "name": "Greece",
                "patient_id_format": r"\d{11}",
                "patient_id_label": "National Person Identifier",
                "patient_id_description": "Greek National ID Number (11 digits)",
                "patient_id_placeholder": "Enter 11-digit national ID (e.g., 12345678901)",
                "requires_birth_date": True,
                "birth_date_format": "YYYY-MM-DD",
            },
            "IT": {
                "name": "Italy",
                "patient_id_format": r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]",
                "patient_id_label": "Codice Fiscale",
                "patient_id_description": "Italian Tax Code (Codice Fiscale)",
                "patient_id_placeholder": "Enter Italian tax code (e.g., RSSMRA85M01H501Z)",
                "requires_birth_date": False,  # Birth date encoded in Codice Fiscale
                "birth_date_format": None,
            },
            "LU": {
                "name": "Luxembourg",
                "patient_id_format": r"\d{13}",
                "patient_id_label": "National Person Identifier",
                "patient_id_description": "Luxembourg National ID Number",
                "patient_id_placeholder": "Enter Luxembourg national ID",
                "requires_birth_date": True,
                "birth_date_format": "YYYY-MM-DD",
            },
            "LV": {
                "name": "Latvia",
                "patient_id_format": r"\d{6}-\d{5}",
                "patient_id_label": "Personal Code",
                "patient_id_description": "Latvian Personal Code (DDMMYY-NNNNN)",
                "patient_id_placeholder": "Enter personal code (e.g., 123456-12345)",
                "requires_birth_date": False,  # Birth date encoded in personal code
                "birth_date_format": None,
            },
            "MT": {
                "name": "Malta",
                "patient_id_format": r"\d{7}[A-Z]",
                "patient_id_label": "Identity Card Number",
                "patient_id_description": "Maltese Identity Card Number (7 digits + letter)",
                "patient_id_placeholder": "Enter ID card number (e.g., 1234567M)",
                "requires_birth_date": True,
                "birth_date_format": "YYYY-MM-DD",
            },
        }

        # Ensure field types exist
        field_types = self.create_field_types()

        for country_code, config in country_ism_configs.items():
            self.create_country_ism(country_code, config, field_types)

        self.stdout.write(self.style.SUCCESS("Successfully created ISM configurations"))

    def create_field_types(self):
        """Create required search field types"""
        field_types = {}

        type_configs = [
            ("text", "Text Input", "text"),
            ("date", "Date Input", "date"),
            ("select", "Select Dropdown", "select"),
            ("email", "Email Input", "email"),
            ("tel", "Telephone Input", "tel"),
            ("number", "Number Input", "number"),
        ]

        for type_code, display_name, html_type in type_configs:
            field_type, created = SearchFieldType.objects.get_or_create(
                type_code=type_code,
                defaults={
                    "display_name": display_name,
                    "html_input_type": html_type,
                },
            )
            field_types[type_code] = field_type
            if created:
                self.stdout.write(f"Created field type: {display_name}")

        return field_types

    def create_country_ism(self, country_code, config, field_types):
        """Create ISM configuration for a specific country"""

        # Create or update country
        country, created = Country.objects.get_or_create(
            code=country_code,
            defaults={
                "name": config["name"],
                "is_available": True,
                "ncp_url": f"https://ncp.{country_code.lower()}.eu/",
                "smp_url": f"https://smp.{country_code.lower()}.eu/",
                "flag_image": f"flags/{country_code.lower()}.png",
            },
        )

        if created:
            self.stdout.write(f'Created country: {config["name"]} ({country_code})')
        else:
            self.stdout.write(
                f'Using existing country: {config["name"]} ({country_code})'
            )

        # Create or update ISM
        search_mask, created = InternationalSearchMask.objects.get_or_create(
            country=country,
            defaults={
                "mask_name": f'{config["name"]} Patient Search',
                "mask_version": "2025.1",
                "mask_description": f'Official ISM for {config["name"]} based on eHDSI specifications',
                "source_smp_url": country.smp_url,
                "is_active": True,
                "raw_ism_data": {
                    "country_code": country_code,
                    "version": "2025.1",
                    "last_updated": timezone.now().isoformat(),
                    "source": "CDA_TEST_CONFIGURATION",
                    "specifications": config,
                },
            },
        )

        if not created:
            # Update existing ISM
            search_mask.mask_version = "2025.1"
            search_mask.mask_description = (
                f'Official ISM for {config["name"]} based on eHDSI specifications'
            )
            search_mask.raw_ism_data = {
                "country_code": country_code,
                "version": "2025.1",
                "last_updated": timezone.now().isoformat(),
                "source": "CDA_TEST_CONFIGURATION",
                "specifications": config,
            }
            search_mask.save()

        self.stdout.write(
            f'{"Created" if created else "Updated"} ISM for {config["name"]}'
        )

        # Clear existing fields
        SearchField.objects.filter(search_mask=search_mask).delete()

        # Create search fields
        field_order = 0

        # Patient ID field (always required)
        field_order += 1
        SearchField.objects.create(
            search_mask=search_mask,
            field_code="patient_id",
            field_type=field_types["text"],
            label=config["patient_id_label"],
            placeholder=config["patient_id_placeholder"],
            help_text=config["patient_id_description"],
            is_required=True,
            validation_pattern=config["patient_id_format"],
            error_message=f'Please enter a valid {config["patient_id_label"]}',
            field_order=field_order,
            field_group="identification",
        )

        # Birth date field (if required)
        if config["requires_birth_date"]:
            field_order += 1
            SearchField.objects.create(
                search_mask=search_mask,
                field_code="birth_date",
                field_type=field_types["date"],
                label="Date of Birth",
                placeholder="Select date of birth",
                help_text=f'Date format: {config["birth_date_format"]}',
                is_required=True,
                field_order=field_order,
                field_group="identification",
            )

        # Optional family name field (helps with verification)
        field_order += 1
        SearchField.objects.create(
            search_mask=search_mask,
            field_code="family_name",
            field_type=field_types["text"],
            label="Family Name",
            placeholder="Enter family name (optional)",
            help_text="Family name for additional verification",
            is_required=False,
            field_order=field_order,
            field_group="personal",
        )

        # Optional given name field
        field_order += 1
        SearchField.objects.create(
            search_mask=search_mask,
            field_code="given_name",
            field_type=field_types["text"],
            label="Given Name",
            placeholder="Enter given name (optional)",
            help_text="Given name for additional verification",
            is_required=False,
            field_order=field_order,
            field_group="personal",
        )

        # Gender field (optional, for validation)
        field_order += 1
        SearchField.objects.create(
            search_mask=search_mask,
            field_code="gender",
            field_type=field_types["select"],
            label="Gender",
            placeholder="Select gender (optional)",
            help_text="Gender for additional verification",
            is_required=False,
            field_options=[
                {"value": "M", "label": "Male"},
                {"value": "F", "label": "Female"},
                {"value": "UN", "label": "Undisclosed"},
            ],
            field_order=field_order,
            field_group="personal",
        )

        self.stdout.write(f'Created {field_order} search fields for {config["name"]}')

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            help="Create ISM for specific country only (GR, IT, LU, LV, MT)",
        )
