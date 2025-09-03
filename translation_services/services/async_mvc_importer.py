"""
Enhanced MVC Import with Async Support and Progress Tracking
"""

import os
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any
import pandas as pd
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile

from ..models import ValueSetCatalogue, ValueSetConcept, ImportTask
from ..services.async_task_service import AsyncTaskService
from translation_manager.models import TerminologySystem
from eu_mvc_parser import EUMVCParser


class AsyncMVCImporter:
    """Handles asynchronous MVC file imports with progress tracking"""

    def __init__(self):
        self.parser = EUMVCParser()

    def start_import(
        self,
        mvc_file: UploadedFile,
        import_mode: str,
        selected_sheets: str = "",
        overwrite_existing: bool = True,
        dry_run: bool = False,
        user=None,
    ) -> str:
        """Start an asynchronous MVC import and return task ID"""

        # Create import task
        task = ImportTask.objects.create(
            user=user,
            task_type="mvc_import",
            filename=mvc_file.name,
            file_size=mvc_file.size,
            status="pending",
            progress_message="Preparing import...",
        )

        # Save uploaded file temporarily
        temp_file_path = f"/tmp/mvc_import_{task.id}.xlsx"

        try:
            with open(temp_file_path, "wb") as temp_file:
                for chunk in mvc_file.chunks():
                    temp_file.write(chunk)
        except Exception as e:
            task.status = "failed"
            task.progress_message = f"Failed to save uploaded file: {str(e)}"
            task.save()
            raise

        # Start async import
        AsyncTaskService.run_async_import_task(
            task_id=str(task.id),
            import_function=self._process_import_async,
            import_kwargs={
                "temp_file_path": temp_file_path,
                "import_mode": import_mode,
                "selected_sheets": selected_sheets,
                "overwrite_existing": overwrite_existing,
                "dry_run": dry_run,
                "task_id": str(task.id),
            },
        )

        return str(task.id)

    def _process_import_async(
        self,
        temp_file_path: str,
        import_mode: str,
        selected_sheets: str,
        overwrite_existing: bool,
        dry_run: bool,
        task_id: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Process MVC import asynchronously with progress tracking"""

        results = {
            "total_value_sets": 0,
            "total_concepts": 0,
            "success_count": 0,
            "error_count": 0,
            "sheets_processed": [],
            "errors": [],
            "message": "",
        }

        try:
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

            total_sheets = len(sheets_to_process)

            if progress_callback:
                progress_callback(
                    0, total_sheets, f"Processing {total_sheets} sheets..."
                )

            # Process each sheet
            for sheet_idx, sheet_name in enumerate(sheets_to_process):
                try:
                    if progress_callback:
                        progress_callback(
                            sheet_idx, total_sheets, f"Processing sheet: {sheet_name}"
                        )

                    # Parse the sheet
                    result = self.parser.parse_mvc_sheet(temp_file_path, sheet_name)

                    if "error" in result:
                        results["errors"].append(
                            f"Sheet {sheet_name}: {result['error']}"
                        )
                        results["error_count"] += 1
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
                        results["success_count"] += 1
                    else:
                        sheet_result["concepts_imported"] = len(concepts)
                        results["total_concepts"] += len(concepts)
                        results["success_count"] += 1

                    results["sheets_processed"].append(sheet_result)
                    results["total_value_sets"] += 1

                except Exception as e:
                    error_msg = f"Sheet {sheet_name}: {str(e)}"
                    results["errors"].append(error_msg)
                    results["error_count"] += 1

                # Update progress
                if progress_callback:
                    progress_callback(
                        sheet_idx + 1,
                        total_sheets,
                        f"Completed {sheet_idx + 1} of {total_sheets} sheets",
                    )

            # Final results
            if dry_run:
                results["message"] = (
                    f'Dry run completed: {results["success_count"]} sheets analyzed, {results["total_concepts"]} concepts found'
                )
            else:
                results["message"] = (
                    f'Import completed: {results["success_count"]} value sets imported, {results["total_concepts"]} concepts imported'
                )

            if results["error_count"] > 0:
                results["message"] += f', {results["error_count"]} errors'

            return results

        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass  # Ignore cleanup errors

    def _import_value_set(self, vs_info, concepts, overwrite_existing):
        """Import a single value set with its concepts"""
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


class ImportTaskService:
    """Service for managing import tasks"""

    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict]:
        """Get the current status of an import task"""
        try:
            task = ImportTask.objects.get(id=task_id)
            return {
                "id": str(task.id),
                "status": task.status,
                "progress_percentage": task.progress_percentage,
                "progress_message": task.progress_message,
                "total_items": task.total_items,
                "processed_items": task.processed_items,
                "success_count": task.success_count,
                "error_count": task.error_count,
                "error_details": task.error_details,
                "filename": task.filename,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
                "is_finished": task.is_finished,
            }
        except ImportTask.DoesNotExist:
            return None
