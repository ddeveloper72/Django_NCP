"""
Django Management Command: Build CDA Document Index

This command scans the test_data directory and builds an index of all
available CDA documents for demonstration purposes.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from patient_data.services.cda_document_index import get_cda_indexer


class Command(BaseCommand):
    help = "Build or refresh the CDA document index for test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force rebuild of the index even if it exists",
        )
        parser.add_argument(
            "--list-patients",
            action="store_true",
            help="List all indexed patients after building",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Building CDA document index..."))

        # Get the indexer
        indexer = get_cda_indexer()

        # Build the index
        start_time = timezone.now()

        if options["force"]:
            self.stdout.write("Force rebuilding index...")
            index = indexer.refresh_index()
        else:
            index = indexer.build_index()

        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()

        # Report results
        total_patients = len(index)
        total_documents = sum(len(docs) for docs in index.values())

        self.stdout.write(
            self.style.SUCCESS(
                f"Index built successfully in {duration:.2f} seconds:\\n"
                f"  • {total_patients} patients indexed\\n"
                f"  • {total_documents} CDA documents found"
            )
        )

        # List patients if requested
        if options["list_patients"]:
            self.stdout.write("\\n" + self.style.WARNING("Indexed Patients:"))
            patients = indexer.get_all_patients()

            for patient in patients:
                doc_types = ", ".join(patient["cda_types"])
                self.stdout.write(
                    f'  • {patient["given_name"]} {patient["family_name"]} '
                    f'({patient["patient_id"]}) - {patient["country_code"]} '
                    f'[{doc_types}] - {patient["document_count"]} docs'
                )

        # Show index file location
        self.stdout.write(f"\\nIndex saved to: {indexer.index_file}")
