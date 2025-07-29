"""
Django management command to import MVC (Master Value Set Catalogue) data
Processes the EU Central Terminology Server MVC Excel file
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from translation_manager.models import (
    TerminologySystem,
    ConceptMapping,
    LanguageTranslation,
)
import pandas as pd
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import MVC (Master Value Set Catalogue) data from Excel file"

    def add_arguments(self, parser):
        parser.add_argument("mvc_file", type=str, help="Path to the MVC Excel file")
        parser.add_argument(
            "--sheet", type=str, help="Specific sheet to import (default: auto-detect)"
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Analyze file without importing data"
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )

    def handle(self, *args, **options):
        mvc_file = options["mvc_file"]
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        if verbose:
            logging.basicConfig(level=logging.INFO)

        # Check if file exists
        if not os.path.exists(mvc_file):
            raise CommandError(f"MVC file not found: {mvc_file}")

        self.stdout.write(f"Processing MVC file: {mvc_file}")

        try:
            # Analyze file structure
            xl_file = pd.ExcelFile(mvc_file)
            self.stdout.write(
                f"Found {len(xl_file.sheet_names)} sheets: {xl_file.sheet_names}"
            )

            # Determine which sheet to process
            target_sheet = options.get("sheet")
            if not target_sheet:
                target_sheet = self.detect_main_sheet(xl_file, mvc_file)
                self.stdout.write(f"Auto-detected main sheet: {target_sheet}")

            # Read the target sheet
            df = pd.read_excel(mvc_file, sheet_name=target_sheet)
            self.stdout.write(
                f'Sheet "{target_sheet}" contains {len(df)} rows and {len(df.columns)} columns'
            )
            self.stdout.write(f"Columns: {list(df.columns)}")

            # Analyze the data structure
            self.analyze_mvc_structure(df, verbose)

            if not dry_run:
                # Import the data
                imported_count = self.import_mvc_data(df, verbose)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported {imported_count} value sets"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING("Dry run mode - no data imported"))

        except Exception as e:
            raise CommandError(f"Error processing MVC file: {e}")

    def detect_main_sheet(self, xl_file, mvc_file):
        """Detect the main value sets sheet"""
        # Try sheets with common names first
        priority_names = ["mvc", "value_sets", "valuesets", "catalogue", "catalog"]

        for sheet_name in xl_file.sheet_names:
            if any(name in sheet_name.lower() for name in priority_names):
                return sheet_name

        # If no obvious sheet found, use the first sheet with substantial data
        for sheet_name in xl_file.sheet_names:
            try:
                df = pd.read_excel(mvc_file, sheet_name=sheet_name)
                if len(df) > 10 and len(df.columns) > 3:  # Has substantial data
                    return sheet_name
            except:
                continue

        # Fallback to first sheet
        return xl_file.sheet_names[0]

    def analyze_mvc_structure(self, df, verbose):
        """Analyze the structure of the MVC data"""
        self.stdout.write("\n=== MVC Data Analysis ===")

        # Show sample data
        self.stdout.write(f"Sample data (first 3 rows):")
        for i, (idx, row) in enumerate(df.head(3).iterrows()):
            self.stdout.write(f"  Row {i+1}: {dict(row)}")

        # Identify key columns
        column_mapping = self.identify_key_columns(df)
        if column_mapping:
            self.stdout.write("\nIdentified column mappings:")
            for key, col in column_mapping.items():
                self.stdout.write(f"  {key}: {col}")

        # Check for OIDs
        oid_columns = [col for col in df.columns if "oid" in col.lower()]
        if oid_columns:
            self.stdout.write(f"\nOID columns found: {oid_columns}")
            for col in oid_columns:
                sample_oids = df[col].dropna().head(3).tolist()
                self.stdout.write(f"  {col} samples: {sample_oids}")

        # Check data quality
        self.stdout.write("\nData quality analysis:")
        self.stdout.write(f"  Total rows: {len(df)}")
        self.stdout.write(f"  Non-empty rows: {df.notna().any(axis=1).sum()}")
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            self.stdout.write(f"  {col}: {non_null_count}/{len(df)} non-null values")

    def identify_key_columns(self, df):
        """Identify key columns in the MVC data"""
        column_mapping = {}

        # Common column name patterns
        patterns = {
            "oid": ["oid", "object_identifier", "identifier"],
            "name": ["name", "title", "display_name", "value_set_name"],
            "description": ["description", "desc", "definition"],
            "version": ["version", "ver", "version_number"],
            "status": ["status", "state", "active"],
            "effective_date": ["effective_date", "date", "created", "effective"],
            "binding_strength": ["binding", "strength", "binding_strength"],
            "purpose": ["purpose", "use", "usage"],
            "concepts": ["concepts", "codes", "values"],
        }

        for key, possible_names in patterns.items():
            for col in df.columns:
                if any(pattern.lower() in col.lower() for pattern in possible_names):
                    column_mapping[key] = col
                    break

        return column_mapping

    def import_mvc_data(self, df, verbose):
        """Import MVC data into Django models"""
        imported_count = 0
        column_mapping = self.identify_key_columns(df)

        with transaction.atomic():
            for idx, row in df.iterrows():
                try:
                    # Extract value set information
                    oid = self.get_value(row, column_mapping, "oid")
                    name = self.get_value(row, column_mapping, "name")
                    description = self.get_value(row, column_mapping, "description", "")

                    if not oid or not name:
                        if verbose:
                            self.stdout.write(
                                f"Skipping row {idx}: missing OID or name"
                            )
                        continue

                    # Create or update TerminologySystem
                    terminology_system, created = (
                        TerminologySystem.objects.get_or_create(
                            oid=oid,
                            defaults={
                                "name": name,
                                "description": description,
                                "version": self.get_value(
                                    row, column_mapping, "version", "1.0"
                                ),
                                "is_active": True,
                            },
                        )
                    )

                    if not created:
                        # Update existing system
                        terminology_system.name = name
                        terminology_system.description = description
                        terminology_system.save()

                    imported_count += 1

                    if verbose and imported_count % 100 == 0:
                        self.stdout.write(f"Imported {imported_count} value sets...")

                except Exception as e:
                    if verbose:
                        self.stdout.write(f"Error importing row {idx}: {e}")
                    continue

        return imported_count

    def get_value(self, row, column_mapping, key, default=None):
        """Get value from row using column mapping"""
        column = column_mapping.get(key)
        if column and column in row:
            value = row[column]
            return value if pd.notna(value) else default
        return default
