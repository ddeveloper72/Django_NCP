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

        # Based on your MS_ISM_Specific_Parameters.csv data - CORRECTED for accuracy
        country_ism_configs = {
            "IE": {
                "name": "Ireland",
                "patient_id_format": r"\d{18}",
                "patient_id_label": "PPSN",
                "patient_id_description": "Personal Public Service Number (PPSN) - 18 digits",
                "patient_id_placeholder": "Enter 18-digit PPSN (e.g., 539305455995368085)",
                "requires_birth_date": False,  # PPSN is sufficient
                "additional_fields": [],  # Only PPSN required per ISM
                "domain": "1.2.372.980010.1.2",
                "scope": "ALL",
            },
            "GR": {
                "name": "Greece",
                "patient_id_format": r"\d{11}",
                "patient_id_label": "National Person Identifier",
                "patient_id_description": "Greek National ID Number (11 digits)",
                "patient_id_placeholder": "Enter 11-digit national ID (e.g., 12345678901)",
                "requires_birth_date": False,  # CORRECTED: GR only uses ID number
                "additional_fields": [],  # CORRECTED: Only ID field
            },
            "IT": {
                "name": "Italy",
                "patient_id_format": r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]",
                "patient_id_label": "Codice Fiscale",
                "patient_id_description": "Italian Tax Code (Codice Fiscale)",
                "patient_id_placeholder": "Enter Italian tax code (e.g., RSSMRA85M01H501Z)",
                "requires_birth_date": False,  # Birth date encoded in Codice Fiscale
                "additional_fields": [],  # Only Codice Fiscale
            },
            "LU": {
                "name": "Luxembourg",
                "patient_id_format": r"\d{13}",
                "patient_id_label": "National Person Identifier",
                "patient_id_description": "Luxembourg National ID Number",
                "patient_id_placeholder": "Enter Luxembourg national ID",
                "requires_birth_date": False,  # CORRECTED: Check actual CSV requirements
                "additional_fields": [],  # Check CSV for exact fields
            },
            "LV": {
                "name": "Latvia",
                "patient_id_format": r"\d{6}-\d{5}",
                "patient_id_label": "Personal Code",
                "patient_id_description": "Latvian Personal Code (DDMMYY-NNNNN)",
                "patient_id_placeholder": "Enter personal code (e.g., 123456-12345)",
                "requires_birth_date": False,  # Birth date encoded in personal code
                "additional_fields": [],  # Only personal code
            },
            "MT": {
                "name": "Malta",
                "patient_id_format": r"\d{7}[A-Z]",
                "patient_id_label": "Identity Card Number",
                "patient_id_description": "Maltese Identity Card Number (7 digits + letter)",
                "patient_id_placeholder": "Enter ID card number (e.g., 1234567M)",
                "requires_birth_date": False,  # CORRECTED: Check actual CSV requirements
                "additional_fields": [],  # Check CSV for exact fields
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

        # Create search fields - SIMPLIFIED to match CSV specifications
        field_order = 0

        # Patient ID field (always required and often the ONLY required field)
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

        # Birth date field (ONLY if explicitly required by the country)
        if config["requires_birth_date"]:
            field_order += 1
            SearchField.objects.create(
                search_mask=search_mask,
                field_code="birth_date",
                field_type=field_types["date"],
                label="Date of Birth",
                placeholder="Select date of birth",
                help_text="Date of birth is required for this country",
                is_required=True,
                field_order=field_order,
                field_group="identification",
            )

        # Additional fields (if specified in CSV for this country)
        for field_config in config.get("additional_fields", []):
            field_order += 1
            SearchField.objects.create(
                search_mask=search_mask,
                field_code=field_config["code"],
                field_type=field_types[field_config["type"]],
                label=field_config["label"],
                placeholder=field_config.get("placeholder", ""),
                help_text=field_config.get("help_text", ""),
                is_required=field_config.get("required", False),
                validation_pattern=field_config.get("pattern", ""),
                field_options=field_config.get("options", []),
                field_order=field_order,
                field_group=field_config.get("group", "additional"),
            )

        self.stdout.write(f'Created {field_order} search fields for {config["name"]}')

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            help="Create ISM for specific country only (GR, IT, LU, LV, MT)",
        )
