"""
Django management command to populate member states with sample patient data OIDs
"""

from django.core.management.base import BaseCommand
from patient_data.models import MemberState
from patient_data.patient_loader import patient_loader


class Command(BaseCommand):
    help = "Populate member states with sample patient data OIDs"

    def handle(self, *args, **options):
        self.stdout.write("Populating member states with sample data OIDs...")

        # Get available OIDs from sample data
        available_oids = patient_loader.get_available_oids()

        # OID to member state mapping
        oid_mappings = {
            "1.3.6.1.4.1.48336": {
                "country_code": "PT",
                "country_name": "Portugal",
                "language_code": "pt-PT",
                "ncp_endpoint": "https://ncp.spms.min-saude.pt/",
            },
            "2.16.17.710.813.1000.990.1": {
                "country_code": "IE",
                "country_name": "Ireland",
                "language_code": "en-IE",
                "ncp_endpoint": "https://ncp.hse.ie/",
            },
        }

        created_count = 0
        updated_count = 0

        for oid in available_oids:
            if oid in oid_mappings:
                mapping = oid_mappings[oid]

                # Get or create member state
                member_state, created = MemberState.objects.get_or_create(
                    country_code=mapping["country_code"],
                    defaults={
                        "country_name": mapping["country_name"],
                        "language_code": mapping["language_code"],
                        "ncp_endpoint": mapping["ncp_endpoint"],
                        "home_community_id": oid,
                        "sample_data_oid": oid,
                        "is_active": True,
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created member state: {mapping['country_name']} (OID: {oid})"
                        )
                    )
                else:
                    # Update existing member state with sample data OID
                    if member_state.sample_data_oid != oid:
                        member_state.sample_data_oid = oid
                        member_state.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Updated member state: {mapping['country_name']} with OID: {oid}"
                            )
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(f"No mapping found for OID: {oid}")
                )

        # List all patients for each OID
        self.stdout.write("\nAvailable sample patients:")
        for oid in available_oids:
            patients = patient_loader.get_patients_for_oid(oid)
            country_name = patient_loader.get_country_for_oid(oid)
            self.stdout.write(f"\n{country_name} (OID: {oid}):")
            for patient_id in patients:
                patient_info = patient_loader.load_patient_data(oid, patient_id)
                if patient_info:
                    self.stdout.write(
                        f"  - {patient_id}: {patient_info.full_name} "
                        f"({patient_info.birth_date_formatted})"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Created {created_count}, updated {updated_count} member states."
            )
        )
