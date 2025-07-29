"""
Django management command for CTS synchronization
Synchronizes MVC and MTC with Central Terminology Server
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from translation_services.cts_integration import CTSAPIClient, CTSTranslationService
import json


class Command(BaseCommand):
    """
    Management command to synchronize with Central Terminology Server (CTS)
    Usage: python manage.py sync_cts --environment training --languages en,fr,de
    """

    help = "Synchronize MVC and MTC with Central Terminology Server (CTS)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--environment",
            type=str,
            default="training",
            choices=["training", "acceptance", "production"],
            help="CTS environment to synchronize with",
        )

        parser.add_argument(
            "--languages",
            type=str,
            default="en",
            help="Comma-separated list of language codes to synchronize (e.g., en,fr,de)",
        )

        parser.add_argument(
            "--mvc-only",
            action="store_true",
            help="Synchronize only Master Value Set Catalogue (MVC)",
        )

        parser.add_argument(
            "--mtc-only",
            action="store_true",
            help="Synchronize only Master Terminology Catalogue (MTC)",
        )

        parser.add_argument(
            "--force-full-sync",
            action="store_true",
            help="Force a complete synchronization (overrides incremental sync)",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without making changes",
        )

    def handle(self, *args, **options):
        """
        Main command execution
        """
        self.stdout.write(self.style.SUCCESS(f"Starting CTS synchronization..."))

        try:
            # Parse language list
            languages = [lang.strip() for lang in options["languages"].split(",")]

            # Initialize CTS client and translation service
            cts_client = CTSAPIClient(environment=options["environment"])
            cts_service = CTSTranslationService(cts_client)

            # Log configuration
            self.stdout.write(f"Environment: {options['environment']}")
            self.stdout.write(f"Base URL: {cts_client.base_url}")
            self.stdout.write(f"Country Code: {cts_client.country_code}")
            self.stdout.write(f"Languages: {', '.join(languages)}")
            self.stdout.write(f"Force Full Sync: {options['force_full_sync']}")
            self.stdout.write(f"Dry Run: {options['dry_run']}")

            if options["dry_run"]:
                self.stdout.write(
                    self.style.WARNING("DRY RUN MODE - No changes will be made")
                )
                self._perform_dry_run(cts_client, languages)
                return

            # Determine what to synchronize
            sync_mvc = not options["mtc_only"]
            sync_mtc = not options["mvc_only"]

            if sync_mvc and sync_mtc:
                # Full synchronization
                self.stdout.write("Performing full MVC and MTC synchronization...")
                results = cts_service.sync_all(languages=languages)
                self._display_full_results(results)

            elif sync_mvc:
                # MVC only
                self.stdout.write("Performing MVC synchronization only...")
                results = cts_service.mvc_manager.sync_value_sets(languages=languages)
                self._display_mvc_results(results)

            elif sync_mtc:
                # MTC only
                self.stdout.write("Performing MTC synchronization only...")
                results = cts_service.mtc_manager.sync_concept_mappings()
                self._display_mtc_results(results)

            self.stdout.write(self.style.SUCCESS("CTS synchronization completed!"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during CTS synchronization: {str(e)}")
            )
            raise

    def _perform_dry_run(self, cts_client: CTSAPIClient, languages: list):
        """
        Perform a dry run to test connectivity and show what would be synchronized
        """
        self.stdout.write("Testing CTS connectivity...")

        # Test basic connectivity
        try:
            sync_status = cts_client.get_sync_status()
            if "error" not in sync_status:
                self.stdout.write(self.style.SUCCESS("✓ CTS connectivity successful"))
                self.stdout.write(
                    f"Current sync status: {sync_status.get('status', 'unknown')}"
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ CTS connectivity failed: {sync_status["error"]}'
                    )
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ CTS connectivity test failed: {str(e)}")
            )
            return

        # Test value sets retrieval
        for language in languages:
            self.stdout.write(f"Testing value sets retrieval for {language}...")
            try:
                value_sets = cts_client.get_value_sets(language=language)
                if "error" not in value_sets:
                    count = len(value_sets.get("value_sets", []))
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Found {count} value sets for {language}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Value sets retrieval failed for {language}: {value_sets["error"]}'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Value sets test failed for {language}: {str(e)}"
                    )
                )

        # Test concept mappings retrieval
        self.stdout.write("Testing concept mappings retrieval...")
        try:
            # Use a common terminology system OID for testing
            test_oid = "2.16.840.1.113883.6.1"  # LOINC
            mappings = cts_client.get_concept_mappings(source_code_system=test_oid)
            if "error" not in mappings:
                count = len(mappings.get("mappings", []))
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Found {count} mappings for test system")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Mappings retrieval test failed: {mappings["error"]}'
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠ Mappings test failed: {str(e)}"))

    def _display_full_results(self, results: dict):
        """Display results from full synchronization"""
        self.stdout.write("\n=== SYNCHRONIZATION RESULTS ===")

        # MVC Results
        if "mvc_sync" in results:
            self._display_mvc_results(results["mvc_sync"], prefix="MVC: ")

        # MTC Results
        if "mtc_sync" in results:
            self._display_mtc_results(results["mtc_sync"], prefix="MTC: ")

        # Overall status
        if results.get("overall_success"):
            self.stdout.write(
                self.style.SUCCESS("\n✓ Overall synchronization: SUCCESS")
            )
        else:
            self.stdout.write(self.style.ERROR("\n✗ Overall synchronization: FAILED"))

    def _display_mvc_results(self, results: dict, prefix: str = ""):
        """Display MVC synchronization results"""
        if results.get("success"):
            self.stdout.write(
                self.style.SUCCESS(f"\n{prefix}✓ MVC Synchronization: SUCCESS")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"\n{prefix}✗ MVC Synchronization: FAILED")
            )

        self.stdout.write(
            f"{prefix}Languages processed: {len(results.get('languages_processed', []))}"
        )
        self.stdout.write(
            f"{prefix}Value sets updated: {results.get('value_sets_updated', 0)}"
        )
        self.stdout.write(
            f"{prefix}Translations added: {results.get('translations_added', 0)}"
        )

        if results.get("errors"):
            self.stdout.write(f"{prefix}Errors:")
            for error in results["errors"]:
                self.stdout.write(self.style.ERROR(f"{prefix}  - {error}"))

    def _display_mtc_results(self, results: dict, prefix: str = ""):
        """Display MTC synchronization results"""
        if results.get("success"):
            self.stdout.write(
                self.style.SUCCESS(f"\n{prefix}✓ MTC Synchronization: SUCCESS")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"\n{prefix}✗ MTC Synchronization: FAILED")
            )

        self.stdout.write(
            f"{prefix}Systems processed: {len(results.get('systems_processed', []))}"
        )
        self.stdout.write(
            f"{prefix}Mappings updated: {results.get('mappings_updated', 0)}"
        )

        if results.get("errors"):
            self.stdout.write(f"{prefix}Errors:")
            for error in results["errors"]:
                self.stdout.write(self.style.ERROR(f"{prefix}  - {error}"))
