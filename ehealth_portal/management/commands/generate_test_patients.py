"""
Generate realistic test patient data that matches each country's ISM configuration.
This creates patient data files in the integration test data structure using
country-specific identification numbers and naming conventions.
"""

from django.core.management.base import BaseCommand
from ehealth_portal.models import Country, InternationalSearchMask
import os
import json
from pathlib import Path


class Command(BaseCommand):
    help = "Generate realistic test patient data matching country ISM configurations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default="patient_data/sample_data/integration",
            help="Output directory for patient data files",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        self.stdout.write(f"Generating patient data in {output_dir}...")

        # Create mapping and patient data
        oid_mapping = {}
        total_patients = 0

        for country in Country.objects.filter(is_available=True):
            try:
                ism = country.search_mask
                country_data = self.generate_country_patients(country, ism)

                if country_data:
                    # Create country directory with a mock OID
                    country_oid = self.get_country_oid(country.code)
                    country_dir = output_dir / country_oid
                    country_dir.mkdir(parents=True, exist_ok=True)

                    # Generate patient files
                    patient_files = []
                    for i, patient in enumerate(country_data["patients"], 1):
                        filename = f"{i}-{patient['id_hash']}-W8.properties"
                        patient_files.append(filename)

                        # Write patient properties file
                        self.write_patient_file(country_dir / filename, patient)

                    # Update OID mapping
                    oid_mapping[country_oid] = {
                        "country_name": f"Country_{country_oid}",
                        "country_code": country.code,
                        "country_display_name": country.name,
                        "patient_count": len(patient_files),
                        "patient_files": patient_files,
                        "ism_version": ism.mask_version,
                    }

                    total_patients += len(patient_files)
                    self.stdout.write(
                        f"✅ {country.name} ({country.code}): {len(patient_files)} patients"
                    )

            except InternationalSearchMask.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  No ISM found for {country.name}")
                )

        # Write OID mapping file
        with open(output_dir / "oid_mapping.json", "w", encoding="utf-8") as f:
            json.dump(oid_mapping, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Generated {total_patients} patients across {len(oid_mapping)} countries"
            )
        )

    def get_country_oid(self, country_code):
        """Generate mock OIDs for countries"""
        oid_mapping = {
            "AT": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.1",  # Austria
            "BE": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.2",  # Belgium
            "DE": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.3",  # Germany
            "FR": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.4",  # France
            "IT": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.5",  # Italy
            "NL": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.6",  # Netherlands
            "ES": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.7",  # Spain
            "PL": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.8",  # Poland
            "CZ": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.9",  # Czech Republic
            "SE": "1.3.6.1.4.1.12559.11.10.1.3.1.1.3.10", # Sweden
        }
        return oid_mapping.get(country_code, f"1.3.6.1.4.1.12559.11.10.1.3.1.1.3.999")

    def generate_country_patients(self, country, ism):
        """Generate realistic patient data for a country"""
        patient_data = self.get_country_patient_templates(country.code)
        return patient_data

    def write_patient_file(self, filepath, patient_data):
        """Write patient data to properties file"""
        with open(filepath, "w", encoding="utf-8") as f:
            for key, value in patient_data.items():
                if key != "id_hash":  # Skip internal fields
                    f.write(f"{key}={value}\n")

    def get_country_patient_templates(self, country_code):
        """Return realistic patient data templates for each country"""
        templates = {
            "AT": {  # Austria
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Müller",
                        "givenName": "Hans",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "svn": "1234 150385",
                        "street": "Mariahilfer Straße 1",
                        "city": "Wien",
                        "postalCode": "1010",
                        "country": "AT",
                        "telephone": "+43 1 12345678",
                        "email": "hans.mueller@example.at",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Wagner",
                        "givenName": "Maria",
                        "administrativeGender": "F",
                        "birthDate.year": "1990",
                        "birthDate.month": "07",
                        "birthDate.day": "22",
                        "svn": "5678 220790",
                        "street": "Salzburger Straße 45",
                        "city": "Linz",
                        "postalCode": "4020",
                        "country": "AT",
                        "telephone": "+43 732 87654321",
                        "email": "maria.wagner@example.at",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Schneider",
                        "givenName": "Franz",
                        "administrativeGender": "M",
                        "birthDate.year": "1978",
                        "birthDate.month": "11",
                        "birthDate.day": "08",
                        "svn": "9012 081178",
                        "street": "Innsbrucker Straße 123",
                        "city": "Innsbruck",
                        "postalCode": "6020",
                        "country": "AT",
                        "telephone": "+43 512 345678",
                        "email": "franz.schneider@example.at",
                    },
                ]
            },
            "BE": {  # Belgium
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Janssen",
                        "givenName": "Jan",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "niss": "85.03.15-123.45",
                        "street": "Grote Markt 1",
                        "city": "Brussels",
                        "postalCode": "1000",
                        "country": "BE",
                        "telephone": "+32 2 1234567",
                        "email": "jan.janssen@example.be",
                        "language": "nl",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Dupont",
                        "givenName": "Marie",
                        "administrativeGender": "F",
                        "birthDate.year": "1992",
                        "birthDate.month": "09",
                        "birthDate.day": "12",
                        "niss": "92.09.12-567.89",
                        "street": "Rue de la Loi 200",
                        "city": "Bruxelles",
                        "postalCode": "1040",
                        "country": "BE",
                        "telephone": "+32 2 7654321",
                        "email": "marie.dupont@example.be",
                        "language": "fr",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Schmidt",
                        "givenName": "Klaus",
                        "administrativeGender": "M",
                        "birthDate.year": "1975",
                        "birthDate.month": "12",
                        "birthDate.day": "03",
                        "niss": "75.12.03-901.23",
                        "street": "Aachener Straße 15",
                        "city": "Eupen",
                        "postalCode": "4700",
                        "country": "BE",
                        "telephone": "+32 87 123456",
                        "email": "klaus.schmidt@example.be",
                        "language": "de",
                    },
                ]
            },
            "DE": {  # Germany
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Schmidt",
                        "givenName": "Hans",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "kvnr": "A123456789",
                        "street": "Unter den Linden 1",
                        "city": "Berlin",
                        "postalCode": "10117",
                        "country": "DE",
                        "telephone": "+49 30 12345678",
                        "email": "hans.schmidt@example.de",
                        "insurance_type": "gkv",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Weber",
                        "givenName": "Anna",
                        "administrativeGender": "F",
                        "birthDate.year": "1990",
                        "birthDate.month": "07",
                        "birthDate.day": "22",
                        "kvnr": "B567890123",
                        "street": "Maximilianstraße 1",
                        "city": "München",
                        "postalCode": "80539",
                        "country": "DE",
                        "telephone": "+49 89 87654321",
                        "email": "anna.weber@example.de",
                        "insurance_type": "pkv",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Fischer",
                        "givenName": "Michael",
                        "administrativeGender": "M",
                        "birthDate.year": "1982",
                        "birthDate.month": "11",
                        "birthDate.day": "05",
                        "kvnr": "C901234567",
                        "street": "Reeperbahn 123",
                        "city": "Hamburg",
                        "postalCode": "20359",
                        "country": "DE",
                        "telephone": "+49 40 345678",
                        "email": "michael.fischer@example.de",
                        "insurance_type": "gkv",
                    },
                ]
            },
            "FR": {  # France
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Martin",
                        "givenName": "Pierre",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "nir": "1 85 03 75 123 456 78",
                        "street": "Champs-Élysées 1",
                        "city": "Paris",
                        "postalCode": "75008",
                        "country": "FR",
                        "telephone": "+33 1 42345678",
                        "email": "pierre.martin@example.fr",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Dubois",
                        "givenName": "Marie",
                        "administrativeGender": "F",
                        "birthDate.year": "1993",
                        "birthDate.month": "08",
                        "birthDate.day": "14",
                        "nir": "2 93 08 69 567 890 12",
                        "street": "Rue de la République 45",
                        "city": "Lyon",
                        "postalCode": "69002",
                        "country": "FR",
                        "telephone": "+33 4 78654321",
                        "email": "marie.dubois@example.fr",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Moreau",
                        "givenName": "Jean",
                        "administrativeGender": "M",
                        "birthDate.year": "1979",
                        "birthDate.month": "12",
                        "birthDate.day": "25",
                        "nir": "1 79 12 13 901 234 56",
                        "street": "Cours Mirabeau 123",
                        "city": "Marseille",
                        "postalCode": "13001",
                        "country": "FR",
                        "telephone": "+33 4 91234567",
                        "email": "jean.moreau@example.fr",
                    },
                ]
            },
            "IT": {  # Italy
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Rossi",
                        "givenName": "Mario",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "codice_fiscale": "RSSMRA85C15H501Z",
                        "birth_place": "Roma",
                        "street": "Via del Corso 1",
                        "city": "Roma",
                        "postalCode": "00187",
                        "country": "IT",
                        "telephone": "+39 06 12345678",
                        "email": "mario.rossi@example.it",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Bianchi",
                        "givenName": "Giulia",
                        "administrativeGender": "F",
                        "birthDate.year": "1991",
                        "birthDate.month": "07",
                        "birthDate.day": "22",
                        "codice_fiscale": "BNCGLI91L62F205X",
                        "birth_place": "Milano",
                        "street": "Via Montenapoleone 45",
                        "city": "Milano",
                        "postalCode": "20121",
                        "country": "IT",
                        "telephone": "+39 02 87654321",
                        "email": "giulia.bianchi@example.it",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Ferrari",
                        "givenName": "Luca",
                        "administrativeGender": "M",
                        "birthDate.year": "1983",
                        "birthDate.month": "10",
                        "birthDate.day": "18",
                        "codice_fiscale": "FRRLCU83R18L219Y",
                        "birth_place": "Napoli",
                        "street": "Via Toledo 123",
                        "city": "Napoli",
                        "postalCode": "80134",
                        "country": "IT",
                        "telephone": "+39 081 345678",
                        "email": "luca.ferrari@example.it",
                    },
                ]
            },
            "NL": {  # Netherlands
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "de Jong",
                        "givenName": "Jan",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "bsn": "123456789",
                        "street": "Damrak 1",
                        "city": "Amsterdam",
                        "postalCode": "1012 LG",
                        "country": "NL",
                        "telephone": "+31 20 1234567",
                        "email": "jan.dejong@example.nl",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "van der Berg",
                        "givenName": "Emma",
                        "administrativeGender": "F",
                        "birthDate.year": "1994",
                        "birthDate.month": "06",
                        "birthDate.day": "12",
                        "bsn": "567890123",
                        "street": "Coolsingel 45",
                        "city": "Rotterdam",
                        "postalCode": "3012 AD",
                        "country": "NL",
                        "telephone": "+31 10 7654321",
                        "email": "emma.vandenberg@example.nl",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Jansen",
                        "givenName": "Pieter",
                        "administrativeGender": "M",
                        "birthDate.year": "1980",
                        "birthDate.month": "09",
                        "birthDate.day": "28",
                        "bsn": "901234567",
                        "street": "Binnenhof 123",
                        "city": "Den Haag",
                        "postalCode": "2513 AA",
                        "country": "NL",
                        "telephone": "+31 70 345678",
                        "email": "pieter.jansen@example.nl",
                    },
                ]
            },
            "ES": {  # Spain
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "García López",
                        "givenName": "Juan",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "dni_nie": "12345678Z",
                        "street": "Gran Vía 1",
                        "city": "Madrid",
                        "postalCode": "28013",
                        "country": "ES",
                        "telephone": "+34 91 1234567",
                        "email": "juan.garcia@example.es",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Martínez Ruiz",
                        "givenName": "Carmen",
                        "administrativeGender": "F",
                        "birthDate.year": "1989",
                        "birthDate.month": "11",
                        "birthDate.day": "03",
                        "dni_nie": "87654321A",
                        "street": "Passeig de Gràcia 45",
                        "city": "Barcelona",
                        "postalCode": "08007",
                        "country": "ES",
                        "telephone": "+34 93 7654321",
                        "email": "carmen.martinez@example.es",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Fernández Silva",
                        "givenName": "Miguel",
                        "administrativeGender": "M",
                        "birthDate.year": "1977",
                        "birthDate.month": "08",
                        "birthDate.day": "19",
                        "dni_nie": "45678912B",
                        "street": "Calle Triana 123",
                        "city": "Sevilla",
                        "postalCode": "41010",
                        "country": "ES",
                        "telephone": "+34 95 4567890",
                        "email": "miguel.fernandez@example.es",
                    },
                ]
            },
            "PL": {  # Poland
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Kowalski",
                        "givenName": "Jan",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "pesel": "85031512345",
                        "street": "ul. Marszałkowska 1",
                        "city": "Warszawa",
                        "postalCode": "00-624",
                        "country": "PL",
                        "telephone": "+48 22 1234567",
                        "email": "jan.kowalski@example.pl",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Nowak",
                        "givenName": "Anna",
                        "administrativeGender": "F",
                        "birthDate.year": "1992",
                        "birthDate.month": "07",
                        "birthDate.day": "22",
                        "pesel": "92072256789",
                        "street": "ul. Floriańska 45",
                        "city": "Kraków",
                        "postalCode": "31-019",
                        "country": "PL",
                        "telephone": "+48 12 7654321",
                        "email": "anna.nowak@example.pl",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Wiśniewski",
                        "givenName": "Piotr",
                        "administrativeGender": "M",
                        "birthDate.year": "1979",
                        "birthDate.month": "12",
                        "birthDate.day": "08",
                        "pesel": "79120890123",
                        "street": "ul. Piotrkowska 123",
                        "city": "Łódź",
                        "postalCode": "90-425",
                        "country": "PL",
                        "telephone": "+48 42 345678",
                        "email": "piotr.wisniewski@example.pl",
                    },
                ]
            },
            "CZ": {  # Czech Republic
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Novák",
                        "givenName": "Jan",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "birth_number": "850315/1234",
                        "street": "Václavské náměstí 1",
                        "city": "Praha",
                        "postalCode": "110 00",
                        "country": "CZ",
                        "telephone": "+420 224 123456",
                        "email": "jan.novak@example.cz",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Svobodová",
                        "givenName": "Marie",
                        "administrativeGender": "F",
                        "birthDate.year": "1990",
                        "birthDate.month": "08",
                        "birthDate.day": "27",
                        "birth_number": "905827/5678",
                        "street": "Masarykova 45",
                        "city": "Brno",
                        "postalCode": "602 00",
                        "country": "CZ",
                        "telephone": "+420 541 765432",
                        "email": "marie.svobodova@example.cz",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Dvořák",
                        "givenName": "Petr",
                        "administrativeGender": "M",
                        "birthDate.year": "1983",
                        "birthDate.month": "11",
                        "birthDate.day": "14",
                        "birth_number": "831114/9012",
                        "street": "Náměstí Míru 123",
                        "city": "Ostrava",
                        "postalCode": "702 00",
                        "country": "CZ",
                        "telephone": "+420 596 123456",
                        "email": "petr.dvorak@example.cz",
                    },
                ]
            },
            "SE": {  # Sweden
                "patients": [
                    {
                        "id_hash": "1234",
                        "familyName": "Andersson",
                        "givenName": "Lars",
                        "administrativeGender": "M",
                        "birthDate.year": "1985",
                        "birthDate.month": "03",
                        "birthDate.day": "15",
                        "personnummer": "850315-1234",
                        "street": "Drottninggatan 1",
                        "city": "Stockholm",
                        "postalCode": "111 51",
                        "country": "SE",
                        "telephone": "+46 8 12345678",
                        "email": "lars.andersson@example.se",
                    },
                    {
                        "id_hash": "5678",
                        "familyName": "Johansson",
                        "givenName": "Emma",
                        "administrativeGender": "F",
                        "birthDate.year": "1991",
                        "birthDate.month": "09",
                        "birthDate.day": "22",
                        "personnummer": "910922-5678",
                        "street": "Avenyn 45",
                        "city": "Göteborg",
                        "postalCode": "411 36",
                        "country": "SE",
                        "telephone": "+46 31 7654321",
                        "email": "emma.johansson@example.se",
                    },
                    {
                        "id_hash": "9012",
                        "familyName": "Lindqvist",
                        "givenName": "Erik",
                        "administrativeGender": "M",
                        "birthDate.year": "1976",
                        "birthDate.month": "05",
                        "birthDate.day": "30",
                        "personnummer": "760530-9012",
                        "street": "Storgatan 123",
                        "city": "Malmö",
                        "postalCode": "211 34",
                        "country": "SE",
                        "telephone": "+46 40 345678",
                        "email": "erik.lindqvist@example.se",
                    },
                ]
            },
        }

        return templates.get(country_code, {"patients": []})
