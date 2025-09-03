"""
Management command to populate initial EU member state data
"""

from django.core.management.base import BaseCommand
from patient_data.models import MemberState, AvailableService


class Command(BaseCommand):
    help = "Populate initial EU member state and service data"

    def handle(self, *args, **options):
        self.stdout.write("Populating EU member state data...")

        # EU Member States with basic eHealth NCP information
        member_states_data = [
            {
                "country_code": "DE",
                "country_name": "Germany",
                "language_code": "de-DE",
                "ncp_endpoint": "https://ncp.germany.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.276",
            },
            {
                "country_code": "FR",
                "country_name": "France",
                "language_code": "fr-FR",
                "ncp_endpoint": "https://ncp.france.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.250",
            },
            {
                "country_code": "IT",
                "country_name": "Italy",
                "language_code": "it-IT",
                "ncp_endpoint": "https://ncp.italy.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.380",
            },
            {
                "country_code": "ES",
                "country_name": "Spain",
                "language_code": "es-ES",
                "ncp_endpoint": "https://ncp.spain.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.724",
            },
            {
                "country_code": "NL",
                "country_name": "Netherlands",
                "language_code": "nl-NL",
                "ncp_endpoint": "https://ncp.netherlands.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.528",
            },
            {
                "country_code": "BE",
                "country_name": "Belgium",
                "language_code": "fr-BE",
                "ncp_endpoint": "https://ncp.belgium.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.056",
            },
            {
                "country_code": "AT",
                "country_name": "Austria",
                "language_code": "de-AT",
                "ncp_endpoint": "https://ncp.austria.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.040",
            },
            {
                "country_code": "PT",
                "country_name": "Portugal",
                "language_code": "pt-PT",
                "ncp_endpoint": "https://ncp.portugal.eu/ehealth",
                "home_community_id": "2.16.17.710.820.1000.990.1.620",
            },
        ]

        # Services typically available from EU NCPs
        services_data = [
            {
                "service_type": "PS",
                "service_name": "Patient Summary",
                "service_description": "Essential health information about a patient including allergies, current medication, and major health problems.",
            },
            {
                "service_type": "EP",
                "service_name": "ePrescription",
                "service_description": "Electronic prescriptions issued by healthcare providers in the patient's home country.",
            },
            {
                "service_type": "LR",
                "service_name": "Laboratory Results",
                "service_description": "Recent laboratory test results and diagnostic reports.",
            },
            {
                "service_type": "VR",
                "service_name": "Vaccination Records",
                "service_description": "Immunization history and vaccination certificates.",
            },
        ]

        created_states = 0
        created_services = 0

        # Create member states
        for state_data in member_states_data:
            state, created = MemberState.objects.get_or_create(
                country_code=state_data["country_code"], defaults=state_data
            )
            if created:
                created_states += 1
                self.stdout.write(f"Created member state: {state.country_name}")

                # Add services for each member state
                for service_data in services_data:
                    service, service_created = AvailableService.objects.get_or_create(
                        member_state=state,
                        service_type=service_data["service_type"],
                        defaults={
                            "service_name": service_data["service_name"],
                            "service_description": service_data["service_description"],
                        },
                    )
                    if service_created:
                        created_services += 1
            else:
                self.stdout.write(f"Member state already exists: {state.country_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_states} member states and {created_services} services"
            )
        )
