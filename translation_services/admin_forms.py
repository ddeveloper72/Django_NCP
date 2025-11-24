"""
Custom admin forms for MVC import and terminology management
Provides enhanced UI for MVC file upload and processing
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import pandas as pd
import os
import sys
from datetime import datetime

# Add the project root to Python path to import our parser
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from eu_mvc_parser import EUMVCParser
from .models import ValueSetCatalogue, ValueSetConcept, MVCSyncLog


class MVCImportForm(forms.Form):
    """Enhanced form for MVC file import"""

    mvc_file = forms.FileField(
        label="MVC Excel File",
        help_text=(
            "Upload the Master Value Set Catalogue (MVC) Excel file from the EU Central Terminology Server. "
            "Expected format: MVC_X.X.X.xlsx with multiple sheets representing value sets. "
            "Maximum file size: 100MB."
        ),
        widget=forms.FileInput(attrs={"accept": ".xlsx,.xls", "class": "form-control"}),
    )

    import_mode = forms.ChoiceField(
        label="Import Mode",
        choices=[
            ("full", "Full Import - All Sheets"),
            ("selective", "Selective Import - Choose Sheets"),
            ("sample", "Sample Import - First 5 Sheets Only"),
        ],
        initial="sample",
        help_text="Choose how to import the MVC data. Sample import is recommended for testing.",
        widget=forms.RadioSelect,
    )

    selected_sheets = forms.CharField(
        label="Selected Sheets (Optional)",
        required=False,
        help_text=(
            "For selective import, enter sheet names separated by commas. "
            "Example: eHDSICountry, eHDSILanguage, eHDSIAdministrativeGender"
        ),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "class": "form-control",
                "placeholder": "eHDSICountry, eHDSILanguage, eHDSIAdministrativeGender, ...",
            }
        ),
    )

    overwrite_existing = forms.BooleanField(
        label="Overwrite Existing Value Sets",
        required=False,
        initial=True,
        help_text="If checked, existing value sets with the same OID will be updated. Otherwise, they will be skipped.",
    )

    dry_run = forms.BooleanField(
        label="Dry Run (Preview Only)",
        required=False,
        initial=False,
        help_text="If checked, the file will be analyzed but no data will be imported.",
    )

    def clean_mvc_file(self):
        """Validate MVC file upload"""
        mvc_file = self.cleaned_data.get("mvc_file")

        if mvc_file:
            # Check file size (100MB limit)
            if mvc_file.size > 100 * 1024 * 1024:
                raise ValidationError(
                    "File size too large. Maximum allowed size is 100MB."
                )

            # Check file extension
            if not mvc_file.name.lower().endswith((".xlsx", ".xls")):
                raise ValidationError(
                    "Invalid file type. Please upload an Excel file (.xlsx or .xls)."
                )

            # Try to read the Excel file to validate it
            try:
                xl_file = pd.ExcelFile(mvc_file)
                if len(xl_file.sheet_names) == 0:
                    raise ValidationError("Excel file contains no sheets.")

                # Reset file pointer for later use
                mvc_file.seek(0)

            except Exception as e:
                raise ValidationError(f"Invalid Excel file: {str(e)}")

        return mvc_file

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        import_mode = cleaned_data.get("import_mode")
        selected_sheets = cleaned_data.get("selected_sheets")

        # If selective import, ensure sheets are specified
        if import_mode == "selective" and not selected_sheets:
            raise ValidationError(
                {
                    "selected_sheets": "Please specify which sheets to import for selective mode."
                }
            )

        return cleaned_data

    def process_import(self):
        """Process the MVC file import"""
        mvc_file = self.cleaned_data["mvc_file"]
        import_mode = self.cleaned_data["import_mode"]
        selected_sheets = self.cleaned_data.get("selected_sheets", "")
        overwrite_existing = self.cleaned_data["overwrite_existing"]
        dry_run = self.cleaned_data["dry_run"]

        # Save uploaded file temporarily
        temp_file_path = (
            f"/tmp/mvc_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        try:
            with open(temp_file_path, "wb") as temp_file:
                for chunk in mvc_file.chunks():
                    temp_file.write(chunk)

            # Get list of sheets to process
            xl_file = pd.ExcelFile(temp_file_path)
            all_sheets = xl_file.sheet_names

            if import_mode == "full":
                sheets_to_process = all_sheets
            elif import_mode == "selective":
                sheet_names = [name.strip() for name in selected_sheets.split(",")]
                sheets_to_process = [s for s in sheet_names if s in all_sheets]
            else:  # sample
                sheets_to_process = all_sheets[:5]

            # Initialize parser and process sheets
            parser = EUMVCParser()
            results = {
                "total_value_sets": 0,
                "total_concepts": 0,
                "sheets_processed": [],
                "errors": [],
            }

            from django.db import transaction
            from translation_manager.models import TerminologySystem

            for sheet_name in sheets_to_process:
                try:
                    # Parse the sheet
                    result = parser.parse_mvc_sheet(temp_file_path, sheet_name)

                    if "error" in result:
                        results["errors"].append(
                            f"Sheet {sheet_name}: {result['error']}"
                        )
                        continue

                    vs_info = result["value_set_info"]
                    concepts = result["concepts"]

                    sheet_result = {
                        "sheet_name": sheet_name,
                        "value_set_name": vs_info.get("name"),
                        "oid": vs_info.get("oid"),
                        "concepts_found": len(concepts),
                        "concepts_imported": 0,
                    }

                    if not dry_run:
                        # Import the data
                        imported_count = self._import_value_set(
                            vs_info, concepts, overwrite_existing
                        )
                        sheet_result["concepts_imported"] = imported_count
                        results["total_concepts"] += imported_count
                    else:
                        sheet_result["concepts_imported"] = len(concepts)
                        results["total_concepts"] += len(concepts)

                    results["sheets_processed"].append(sheet_result)
                    results["total_value_sets"] += 1

                except Exception as e:
                    results["errors"].append(f"Sheet {sheet_name}: {str(e)}")

            return results

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _import_value_set(self, vs_info, concepts, overwrite_existing):
        """Import a single value set with its concepts"""
        from django.db import transaction
        from translation_manager.models import TerminologySystem

        imported_count = 0
        oid = vs_info.get("oid")

        if not oid:
            raise ValueError("Value set must have an OID")

        with transaction.atomic():
            # Check if value set already exists
            if (
                not overwrite_existing
                and ValueSetCatalogue.objects.filter(oid=oid).exists()
            ):
                return 0  # Skip existing

            # Create terminology system if needed
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

            if not created and overwrite_existing:
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

            # Clear existing concepts if overwriting
            if overwrite_existing:
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

                except Exception:
                    # Skip concepts that fail to import
                    continue

        return imported_count


class CTSSyncForm(forms.Form):
    """Form for CTS synchronization settings"""

    environment = forms.ChoiceField(
        label="CTS Environment",
        choices=[
            ("training", "Training Environment"),
            ("acceptance", "Acceptance Environment"),
            ("production", "Production Environment"),
        ],
        initial="training",
        help_text="Choose which CTS environment to synchronize with.",
    )

    sync_type = forms.ChoiceField(
        label="Synchronization Type",
        choices=[
            ("full", "Full Sync - All Value Sets"),
            ("incremental", "Incremental Sync - Updated Only"),
            ("selective", "Selective Sync - Choose Value Sets"),
        ],
        initial="incremental",
        help_text="Choose how to synchronize with CTS.",
    )

    languages = forms.MultipleChoiceField(
        label="Languages",
        choices=[
            ("en", "English"),
            ("de", "German"),
            ("fr", "French"),
            ("it", "Italian"),
            ("es", "Spanish"),
            ("pt", "Portuguese"),
            ("nl", "Dutch"),
            ("da", "Danish"),
            ("sv", "Swedish"),
            ("fi", "Finnish"),
        ],
        initial=["en", "de"],
        help_text="Select languages to include in synchronization.",
        widget=forms.CheckboxSelectMultiple,
    )
