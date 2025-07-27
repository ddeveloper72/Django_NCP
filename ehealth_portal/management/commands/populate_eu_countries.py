"""
Management command to populate initial EU country data with real European SMP endpoints
"""

from django.core.management.base import BaseCommand
from ehealth_portal.models import Country
from ehealth_portal.european_smp_client import european_smp_client


class Command(BaseCommand):
    help = "Populate initial EU country data for eHealth portal"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Populating EU country data..."))

        # EU Countries with their SMP configurations
        countries_data = [
            {
                "code": "BE",
                "name": "Belgium",
                "ncp_url": "https://ncp.belgium.eu/",
                "smp_url": f"https://smp-be.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "BG",
                "name": "Bulgaria",
                "ncp_url": "https://ncp.bulgaria.bg/",
                "smp_url": f"https://smp-bg.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "CZ",
                "name": "Czech Republic",
                "ncp_url": "https://ncp.czech.cz/",
                "smp_url": f"https://smp-cz.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "DK",
                "name": "Denmark",
                "ncp_url": "https://ncp.denmark.dk/",
                "smp_url": f"https://smp-dk.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "DE",
                "name": "Germany",
                "ncp_url": "https://ncp.germany.de/",
                "smp_url": f"https://smp-de.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "EE",
                "name": "Estonia",
                "ncp_url": "https://ncp.estonia.ee/",
                "smp_url": f"https://smp-ee.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "IE",
                "name": "Ireland",
                "ncp_url": "https://ncp.ireland.ie/",
                "smp_url": f"https://smp-ie.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "GR",
                "name": "Greece",
                "ncp_url": "https://ncp.greece.gr/",
                "smp_url": f"https://smp-gr.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "ES",
                "name": "Spain",
                "ncp_url": "https://ncp.spain.es/",
                "smp_url": f"https://smp-es.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "FR",
                "name": "France",
                "ncp_url": "https://ncp.france.fr/",
                "smp_url": f"https://smp-fr.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "HR",
                "name": "Croatia",
                "ncp_url": "https://ncp.croatia.hr/",
                "smp_url": f"https://smp-hr.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "IT",
                "name": "Italy",
                "ncp_url": "https://ncp.italy.it/",
                "smp_url": f"https://smp-it.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "CY",
                "name": "Cyprus",
                "ncp_url": "https://ncp.cyprus.cy/",
                "smp_url": f"https://smp-cy.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "LV",
                "name": "Latvia",
                "ncp_url": "https://ncp.latvia.lv/",
                "smp_url": f"https://smp-lv.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "LT",
                "name": "Lithuania",
                "ncp_url": "https://ncp.lithuania.lt/",
                "smp_url": f"https://smp-lt.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "LU",
                "name": "Luxembourg",
                "ncp_url": "https://ncp.luxembourg.lu/",
                "smp_url": f"https://smp-lu.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "HU",
                "name": "Hungary",
                "ncp_url": "https://ncp.hungary.hu/",
                "smp_url": f"https://smp-hu.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "MT",
                "name": "Malta",
                "ncp_url": "https://ncp.malta.mt/",
                "smp_url": f"https://smp-mt.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "NL",
                "name": "Netherlands",
                "ncp_url": "https://ncp.netherlands.nl/",
                "smp_url": f"https://smp-nl.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "AT",
                "name": "Austria",
                "ncp_url": "https://ncp.austria.gv.at/",
                "smp_url": f"https://smp-at.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "PL",
                "name": "Poland",
                "ncp_url": "https://ncp.poland.pl/",
                "smp_url": f"https://smp-pl.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "PT",
                "name": "Portugal",
                "ncp_url": "https://ncp.portugal.pt/",
                "smp_url": f"https://smp-pt.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "RO",
                "name": "Romania",
                "ncp_url": "https://ncp.romania.ro/",
                "smp_url": f"https://smp-ro.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "SI",
                "name": "Slovenia",
                "ncp_url": "https://ncp.slovenia.si/",
                "smp_url": f"https://smp-si.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "SK",
                "name": "Slovakia",
                "ncp_url": "https://ncp.slovakia.sk/",
                "smp_url": f"https://smp-sk.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "FI",
                "name": "Finland",
                "ncp_url": "https://ncp.finland.fi/",
                "smp_url": f"https://smp-fi.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "SE",
                "name": "Sweden",
                "ncp_url": "https://ncp.sweden.se/",
                "smp_url": f"https://smp-se.{european_smp_client.SML_DOMAIN}",
            },
            {
                "code": "EU",
                "name": "European Commission (Test)",
                "ncp_url": european_smp_client.SMP_ADMIN_URL,
                "smp_url": european_smp_client.SMP_ADMIN_URL,
            },
        ]

        created_count = 0
        updated_count = 0

        for country_data in countries_data:
            country, created = Country.objects.get_or_create(
                code=country_data["code"],
                defaults={
                    "name": country_data["name"],
                    "ncp_url": country_data["ncp_url"],
                    "smp_url": country_data["smp_url"],
                    "is_available": True,
                    "is_test_environment": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created country: {country.name} ({country.code})"
                    )
                )
            else:
                # Update existing country with new SMP URLs
                country.smp_url = country_data["smp_url"]
                country.ncp_url = country_data["ncp_url"]
                country.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Updated country: {country.name} ({country.code})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully populated {created_count} new countries and updated {updated_count} existing countries"
            )
        )

        # Test SMP connectivity for a few key countries
        self.stdout.write("\nTesting SMP connectivity for key countries...")
        test_countries = ["IE", "BE", "AT", "EU"]

        for country_code in test_countries:
            try:
                country = Country.objects.get(code=country_code)
                smp_url = european_smp_client.get_country_smp_url(country_code.lower())
                if smp_url:
                    self.stdout.write(f"✅ {country.name}: {smp_url}")
                else:
                    self.stdout.write(f"❌ {country.name}: SMP URL not accessible")
            except Country.DoesNotExist:
                self.stdout.write(f"⚠️  Country {country_code} not found")

        self.stdout.write(
            self.style.SUCCESS("\n🌍 EU country data population completed!")
        )
