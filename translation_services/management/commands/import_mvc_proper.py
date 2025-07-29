"""
Django management command to properly import MVC data using the EU MVC Parser
Each sheet represents one value set with concepts
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from translation_services.mvc_models import (
    ValueSetCatalogue,
    ValueSetConcept,
    MVCSyncLog,
)
import pandas as pd
import os
import sys
from datetime import datetime
import json

# Add the project root to Python path to import our parser
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from eu_mvc_parser import EUMVCParser


class Command(BaseCommand):
    help = "Import MVC data properly - each sheet as a value set with concepts"

    def add_arguments(self, parser):
        parser.add_argument("mvc_file", type=str, help="Path to the MVC Excel file")
        parser.add_argument(
            "--dry-run", action="store_true", help="Analyze file without importing data"
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )
        parser.add_argument(
            "--sheets", nargs="*", help="Specific sheets to process (default: all)"
        )
        parser.add_argument(
            "--report", type=str, help="Path to save detailed import report"
        )

    def handle(self, *args, **options):
        mvc_file = options["mvc_file"]
        dry_run = options["dry_run"]
        verbose = options["verbose"]
        target_sheets = options.get("sheets")
        report_path = options.get("report")

        # Check if file exists
        if not os.path.exists(mvc_file):
            raise CommandError(f"MVC file not found: {mvc_file}")

        self.stdout.write(f"Processing MVC file: {mvc_file}")

        # Create report structure
        report = {
            "timestamp": datetime.now().isoformat(),
            "file_path": mvc_file,
            "dry_run": dry_run,
            "sheets_processed": [],
            "total_value_sets": 0,
            "total_concepts": 0,
            "errors": [],
        }

        try:
            # Get list of sheets
            xl_file = pd.ExcelFile(mvc_file)
            all_sheets = xl_file.sheet_names

            # Determine which sheets to process
            if target_sheets:
                sheets_to_process = [s for s in target_sheets if s in all_sheets]
                if not sheets_to_process:
                    raise CommandError(
                        f"None of the specified sheets found: {target_sheets}"
                    )
            else:
                sheets_to_process = all_sheets

            self.stdout.write(f"Found {len(all_sheets)} total sheets")
            self.stdout.write(f"Processing {len(sheets_to_process)} sheets")

            if verbose:
                self.stdout.write(f"Sheets to process: {sheets_to_process}")

            # Initialize parser
            parser = EUMVCParser()

            # Process each sheet
            for sheet_name in sheets_to_process:
                sheet_report = self.process_sheet(
                    parser, mvc_file, sheet_name, dry_run, verbose
                )
                report["sheets_processed"].append(sheet_report)

                if "error" not in sheet_report:
                    report["total_value_sets"] += 1
                    report["total_concepts"] += sheet_report.get("concepts_imported", 0)
                else:
                    report["errors"].append(
                        f"Sheet {sheet_name}: {sheet_report['error']}"
                    )

            # Summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("IMPORT SUMMARY")
            self.stdout.write("=" * 60)
            self.stdout.write(
                f"Total sheets processed: {len(report['sheets_processed'])}"
            )
            self.stdout.write(f"Value sets imported: {report['total_value_sets']}")
            self.stdout.write(f"Total concepts imported: {report['total_concepts']}")
            self.stdout.write(f"Errors: {len(report['errors'])}")

            if report["errors"]:
                self.stdout.write("\nErrors encountered:")
                for error in report["errors"]:
                    self.stdout.write(f"  - {error}")

            # Save report if requested
            if report_path:
                with open(report_path, "w") as f:
                    json.dump(report, f, indent=2)
                self.stdout.write(f"\nDetailed report saved to: {report_path}")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING("\nDRY RUN MODE - No data was actually imported")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"\nImport completed successfully!")
                )

        except Exception as e:
            report["errors"].append(str(e))
            if report_path:
                with open(report_path, "w") as f:
                    json.dump(report, f, indent=2)
            raise CommandError(f"Error processing MVC file: {e}")

    def process_sheet(self, parser, mvc_file, sheet_name, dry_run, verbose):
        """Process a single sheet (value set)"""
        sheet_report = {
            "sheet_name": sheet_name,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if verbose:
                self.stdout.write(f"\nProcessing sheet: {sheet_name}")

            # Parse the sheet
            result = parser.parse_mvc_sheet(mvc_file, sheet_name)

            if "error" in result:
                sheet_report["error"] = result["error"]
                return sheet_report

            vs_info = result["value_set_info"]
            concepts = result["concepts"]

            sheet_report.update(
                {
                    "value_set_name": vs_info.get("name"),
                    "oid": vs_info.get("oid"),
                    "canonical_url": vs_info.get("canonical_url"),
                    "concepts_found": len(concepts),
                    "concepts_imported": 0,
                }
            )

            if verbose:
                self.stdout.write(f"  Value Set: {vs_info.get('name')}")
                self.stdout.write(f"  OID: {vs_info.get('oid')}")
                self.stdout.write(f"  Concepts found: {len(concepts)}")

            if not dry_run:
                # Import the data
                imported_count = self.import_value_set(vs_info, concepts, verbose)
                sheet_report["concepts_imported"] = imported_count

                if verbose:
                    self.stdout.write(f"  Concepts imported: {imported_count}")

        except Exception as e:
            sheet_report["error"] = str(e)
            if verbose:
                self.stdout.write(f"  Error: {e}")

        return sheet_report

    def import_value_set(self, vs_info, concepts, verbose):
        """Import a single value set with its concepts"""
        imported_count = 0

        with transaction.atomic():
            # First ensure we have a terminology system
            oid = vs_info.get("oid")
            if not oid:
                raise ValueError("Value set must have an OID")

            # Create a simple terminology system for the value set if needed
            from translation_manager.models import TerminologySystem

            terminology_system, created = TerminologySystem.objects.get_or_create(
                oid=oid,
                defaults={
                    "name": vs_info.get("name", "Unknown"),
                    "description": f"Terminology system for {vs_info.get('name', 'Unknown')} value set",
                    "version": vs_info.get("version", "9.0.0"),
                    "is_active": True,
                },
            )

            # Create or update the value set catalogue
            cts_url = vs_info.get("canonical_url")
            catalogue, created = ValueSetCatalogue.objects.get_or_create(
                oid=oid,
                defaults={
                    "name": vs_info.get("name", "Unknown"),
                    "description": vs_info.get("description")
                    or f"Value set for {vs_info.get('name', 'Unknown')}",
                    "version": vs_info.get("version", "9.0.0"),
                    "status": "active",
                    "terminology_system": terminology_system,
                    "cts_url": cts_url if cts_url else "",
                    "publisher": "EU Central Terminology Server",
                },
            )

            if not created:
                # Update existing catalogue
                catalogue.name = vs_info.get("name", catalogue.name)
                catalogue.description = (
                    vs_info.get("description")
                    or catalogue.description
                    or f"Value set for {catalogue.name}"
                )
                catalogue.version = vs_info.get("version", catalogue.version)
                if cts_url:
                    catalogue.cts_url = cts_url
                catalogue.save()

            # Clear existing concepts for this value set
            ValueSetConcept.objects.filter(value_set=catalogue).delete()

            # Import concepts
            for concept_data in concepts:
                if not concept_data.get("concept_code"):
                    continue

                try:
                    ValueSetConcept.objects.create(
                        value_set=catalogue,
                        code=concept_data.get("concept_code", ""),
                        display=concept_data.get("description", ""),
                        definition=concept_data.get("description", ""),
                        code_system=concept_data.get("code_system_id", ""),
                        code_system_version=concept_data.get("code_system_version", ""),
                        status="active",
                    )
                    imported_count += 1

                except Exception as e:
                    if verbose:
                        self.stdout.write(
                            f"    Warning: Failed to import concept {concept_data.get('concept_code')}: {e}"
                        )
                    continue

            # Log the sync
            MVCSyncLog.objects.create(
                sync_type="single_vs",
                source="local_file",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="completed",
                value_sets_processed=1,
                concepts_processed=imported_count,
                sync_details={
                    "import_details": f"Imported {imported_count} concepts for value set {vs_info.get('name')}"
                },
            )

        return imported_count
