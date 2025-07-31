"""
Management command to generate realistic International Search Mask (ISM) configurations
for EU member states based on their actual national eHealth infrastructure requirements.

Each country has different patient identification systems and search requirements:
- Some use national ID numbers, others use social security numbers
- Different date formats and validation patterns
- Varying required vs optional fields
- Country-specific healthcare identifiers

This generates test data that reflects real-world diversity without requiring
access to the actual European SMP infrastructure.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from ehealth_portal.models import (
    Country,
    InternationalSearchMask,
    SearchField,
    SearchFieldType,
)
import json


class Command(BaseCommand):
    help = "Generate realistic ISM configurations for EU member states"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing ISMs instead of creating new ones",
        )

    def handle(self, *args, **options):
        self.stdout.write("Generating realistic ISM configurations...")

        # Ensure all required field types exist
        self.create_field_types()

        # Generate ISMs for each country
        countries_configured = 0
        for country_config in self.get_country_ism_configs():
            try:
                country = Country.objects.get(code=country_config["code"])
                self.create_or_update_ism(country, country_config, options["update"])
                countries_configured += 1
                self.stdout.write(
                    f"✅ {country.name} ({country.code}): {len(country_config['fields'])} fields"
                )
            except Country.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Country {country_config['code']} not found in database"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Successfully configured {countries_configured} country ISMs"
            )
        )

    def create_field_types(self):
        """Ensure all required field types exist"""
        field_types = [
            ("text", "Text Input", "text"),
            ("date", "Date Input", "date"),
            ("select", "Dropdown Select", "select"),
            ("ssn", "Social Security Number", "text"),
            ("id_card", "ID Card Number", "text"),
            ("passport", "Passport Number", "text"),
            ("number", "Number Input", "number"),
            ("email", "Email Input", "email"),
            ("phone", "Phone Input", "tel"),
        ]

        for type_code, display_name, html_type in field_types:
            SearchFieldType.objects.get_or_create(
                type_code=type_code,
                defaults={
                    "display_name": display_name,
                    "html_input_type": html_type,
                },
            )

    def create_or_update_ism(self, country, config, update_existing):
        """Create or update ISM for a country"""
        if update_existing:
            ism, created = InternationalSearchMask.objects.update_or_create(
                country=country,
                defaults={
                    "mask_name": config["mask_name"],
                    "mask_version": config["version"],
                    "mask_description": config["description"],
                    "source_smp_url": f"https://smp-{country.code.lower()}.ehealth.eu/",
                    "raw_ism_data": config,
                    "last_synchronized": timezone.now(),
                },
            )
        else:
            try:
                ism = country.search_mask
                if not update_existing:
                    return  # Skip if exists and not updating
            except InternationalSearchMask.DoesNotExist:
                ism = InternationalSearchMask.objects.create(
                    country=country,
                    mask_name=config["mask_name"],
                    mask_version=config["version"],
                    mask_description=config["description"],
                    source_smp_url=f"https://smp-{country.code.lower()}.ehealth.eu/",
                    raw_ism_data=config,
                    last_synchronized=timezone.now(),
                )

        # Clear existing fields and recreate
        SearchField.objects.filter(search_mask=ism).delete()

        # Create search fields
        for order, field_config in enumerate(config["fields"]):
            field_type = SearchFieldType.objects.get(
                type_code=field_config["type"]
            )

            SearchField.objects.create(
                search_mask=ism,
                field_code=field_config["code"],
                field_type=field_type,
                label=field_config["label"],
                placeholder=field_config.get("placeholder", ""),
                help_text=field_config.get("help_text", ""),
                is_required=field_config.get("required", False),
                validation_pattern=field_config.get("validation_pattern", ""),
                field_options=field_config.get("options", []),
                default_value=field_config.get("default_value", ""),
                field_order=order,
                field_group=field_config.get("group", "main"),
            )

    def get_country_ism_configs(self):
        """Return realistic ISM configurations for EU member states"""
        return [
            # Austria - Simple but comprehensive
            {
                "code": "AT",
                "mask_name": "Austrian Patient Search System",
                "version": "2.1",
                "description": "Austria uses ELGA (Elektronische Gesundheitsakte) with SVN identification",
                "fields": [
                    {
                        "code": "svn",
                        "type": "ssn",
                        "label": "Sozialversicherungsnummer (SVN)",
                        "placeholder": "1234 010170",
                        "required": True,
                        "validation_pattern": r"^\d{4} \d{6}$",
                        "help_text": "Austrian social security number (VVVV TTMMJJ)",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Vorname",
                        "placeholder": "Max",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Nachname",
                        "placeholder": "Mustermann",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Geburtsdatum",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Belgium - Comprehensive with NISS
            {
                "code": "BE",
                "mask_name": "Belgian Patient Identification System",
                "version": "1.8",
                "description": "Belgium uses NISS (Numéro d'identification de sécurité sociale) for patient identification",
                "fields": [
                    {
                        "code": "niss",
                        "type": "ssn",
                        "label": "NISS / INSZ",
                        "placeholder": "85.03.15-123.45",
                        "required": True,
                        "validation_pattern": r"^\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2}$",
                        "help_text": "Numéro d'identification de sécurité sociale",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Prénom / Voornaam",
                        "placeholder": "Jean / Jan",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Nom / Achternaam",
                        "placeholder": "Dupont / Janssen",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Date de naissance / Geboortedatum",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "language",
                        "type": "select",
                        "label": "Langue préférée / Voorkeurstaal",
                        "options": [
                            {"value": "fr", "label": "Français"},
                            {"value": "nl", "label": "Nederlands"},
                            {"value": "de", "label": "Deutsch"},
                        ],
                        "required": False,
                        "group": "preferences",
                    },
                ],
            },
            # Germany - Complex with insurance number
            {
                "code": "DE",
                "mask_name": "German Healthcare Search Portal",
                "version": "3.2",
                "description": "Germany uses Krankenversichertennummer for patient identification within the gematik infrastructure",
                "fields": [
                    {
                        "code": "kvnr",
                        "type": "id_card",
                        "label": "Krankenversichertennummer (KVNR)",
                        "placeholder": "A123456789",
                        "required": True,
                        "validation_pattern": r"^[A-Z]\d{9}$",
                        "help_text": "10-stellige Krankenversichertennummer auf der eGK",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Vorname",
                        "placeholder": "Hans",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Nachname",
                        "placeholder": "Müller",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Geburtsdatum",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "insurance_type",
                        "type": "select",
                        "label": "Versicherungsart",
                        "options": [
                            {"value": "gkv", "label": "Gesetzliche Krankenversicherung"},
                            {"value": "pkv", "label": "Private Krankenversicherung"},
                            {"value": "beihilfe", "label": "Beihilfe"},
                        ],
                        "required": False,
                        "group": "insurance",
                    },
                ],
            },
            # France - Carte Vitale system
            {
                "code": "FR",
                "mask_name": "French Healthcare Search System",
                "version": "2.5",
                "description": "France uses NIR (Numéro d'Inscription au Répertoire) from Carte Vitale",
                "fields": [
                    {
                        "code": "nir",
                        "type": "ssn",
                        "label": "Numéro de Sécurité Sociale (NIR)",
                        "placeholder": "1 85 03 75 123 456 78",
                        "required": True,
                        "validation_pattern": r"^\d \d{2} \d{2} \d{2} \d{3} \d{3} \d{2}$",
                        "help_text": "Numéro d'Inscription au Répertoire (15 chiffres)",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Prénom",
                        "placeholder": "Pierre",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Nom de famille",
                        "placeholder": "Martin",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Date de naissance",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Italy - Codice Fiscale
            {
                "code": "IT",
                "mask_name": "Italian Healthcare Patient Search",
                "version": "1.9",
                "description": "Italy uses Codice Fiscale for patient identification in the Fascicolo Sanitario Elettronico",
                "fields": [
                    {
                        "code": "codice_fiscale",
                        "type": "id_card",
                        "label": "Codice Fiscale",
                        "placeholder": "RSSMRA85C15H501Z",
                        "required": True,
                        "validation_pattern": r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$",
                        "help_text": "Codice fiscale italiano (16 caratteri)",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Nome",
                        "placeholder": "Mario",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Cognome",
                        "placeholder": "Rossi",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Data di nascita",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_place",
                        "type": "text",
                        "label": "Luogo di nascita",
                        "placeholder": "Roma",
                        "required": False,
                        "group": "identity",
                    },
                ],
            },
            # Netherlands - BSN
            {
                "code": "NL",
                "mask_name": "Dutch Patient Identification System",
                "version": "2.3",
                "description": "Netherlands uses BSN (Burgerservicenummer) for patient identification",
                "fields": [
                    {
                        "code": "bsn",
                        "type": "ssn",
                        "label": "Burgerservicenummer (BSN)",
                        "placeholder": "123456789",
                        "required": True,
                        "validation_pattern": r"^\d{9}$",
                        "help_text": "9-cijferig burgerservicenummer",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Voornaam",
                        "placeholder": "Jan",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Achternaam",
                        "placeholder": "de Jong",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Geboortedatum",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Spain - NIE/DNI
            {
                "code": "ES",
                "mask_name": "Spanish Healthcare Patient Search",
                "version": "1.7",
                "description": "Spain uses DNI/NIE for patient identification in the Sistema Nacional de Salud",
                "fields": [
                    {
                        "code": "dni_nie",
                        "type": "id_card",
                        "label": "DNI / NIE",
                        "placeholder": "12345678Z",
                        "required": True,
                        "validation_pattern": r"^(\d{8}[A-Z]|[XYZ]\d{7}[A-Z])$",
                        "help_text": "Documento Nacional de Identidad o Número de Identidad de Extranjero",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Nombre",
                        "placeholder": "Juan",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Apellidos",
                        "placeholder": "García López",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Fecha de nacimiento",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Poland - PESEL
            {
                "code": "PL",
                "mask_name": "Polish Healthcare Patient Search",
                "version": "1.4",
                "description": "Poland uses PESEL for patient identification in the national healthcare system",
                "fields": [
                    {
                        "code": "pesel",
                        "type": "ssn",
                        "label": "PESEL",
                        "placeholder": "85031512345",
                        "required": True,
                        "validation_pattern": r"^\d{11}$",
                        "help_text": "Powszechny Elektroniczny System Ewidencji Ludności (11 cyfr)",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Imię",
                        "placeholder": "Jan",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Nazwisko",
                        "placeholder": "Kowalski",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Data urodzenia",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Czech Republic - Birth Number
            {
                "code": "CZ",
                "mask_name": "Czech Patient Search System",
                "version": "2.0",
                "description": "Czech Republic uses birth number (rodné číslo) for patient identification",
                "fields": [
                    {
                        "code": "birth_number",
                        "type": "ssn",
                        "label": "Rodné číslo",
                        "placeholder": "850315/1234",
                        "required": True,
                        "validation_pattern": r"^\d{6}/\d{4}$",
                        "help_text": "Czech birth number in format YYMMDD/XXXX",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Jméno",
                        "placeholder": "Jan",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Příjmení",
                        "placeholder": "Novák",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Datum narození",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
            # Sweden - Personal Number
            {
                "code": "SE",
                "mask_name": "Swedish Patient Search Portal",
                "version": "1.6",
                "description": "Sweden uses personnummer for patient identification in the national health system",
                "fields": [
                    {
                        "code": "personnummer",
                        "type": "ssn",
                        "label": "Personnummer",
                        "placeholder": "850315-1234",
                        "required": True,
                        "validation_pattern": r"^\d{6}-\d{4}$",
                        "help_text": "Swedish personal number in format YYMMDD-XXXX",
                        "group": "identity",
                    },
                    {
                        "code": "first_name",
                        "type": "text",
                        "label": "Förnamn",
                        "placeholder": "Lars",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "last_name",
                        "type": "text",
                        "label": "Efternamn",
                        "placeholder": "Andersson",
                        "required": True,
                        "group": "identity",
                    },
                    {
                        "code": "birth_date",
                        "type": "date",
                        "label": "Födelsedatum",
                        "required": True,
                        "group": "identity",
                    },
                ],
            },
        ]
