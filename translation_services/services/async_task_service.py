import threading
import logging
from datetime import datetime
from typing import Optional, Callable, Any
from django.utils import timezone
from django.db import transaction
from translation_services.models import ImportTask

logger = logging.getLogger(__name__)


class AsyncTaskService:
    """Service for running background tasks with progress tracking"""

    @staticmethod
    def run_async_import_task(
        task_id: str,
        import_function: Callable,
        import_kwargs: dict,
        progress_callback: Optional[Callable] = None,
    ):
        """Run an import task asynchronously in a separate thread"""

        def _run_task():
            try:
                # Get task from database
                task = ImportTask.objects.get(id=task_id)

                # Update task status
                task.status = "processing"
                task.started_at = timezone.now()
                task.progress_message = "Starting import..."
                task.save()

                # Define progress callback for the import function
                def update_progress(processed: int, total: int, message: str = ""):
                    with transaction.atomic():
                        task.refresh_from_db()
                        task.total_items = total
                        task.processed_items = processed
                        task.progress_percentage = (
                            min(100, int((processed / total) * 100)) if total > 0 else 0
                        )
                        task.progress_message = (
                            message or f"Processed {processed} of {total} items"
                        )
                        task.save()

                # Add progress callback to import kwargs
                import_kwargs["progress_callback"] = update_progress

                # Run the import function
                logger.info(f"Starting async task {task_id}")
                result = import_function(**import_kwargs)

                # Update task completion
                with transaction.atomic():
                    task.refresh_from_db()
                    task.status = "completed"
                    task.completed_at = timezone.now()
                    task.progress_percentage = 100

                    # Extract results from import result
                    if isinstance(result, dict):
                        task.success_count = result.get("success_count", 0)
                        task.error_count = result.get("error_count", 0)
                        task.error_details = result.get("errors", [])
                        task.progress_message = result.get(
                            "message", "Import completed successfully"
                        )
                    else:
                        task.progress_message = "Import completed successfully"

                    task.save()

                logger.info(f"Completed async task {task_id}")

            except Exception as e:
                logger.error(f"Error in async task {task_id}: {str(e)}", exc_info=True)

                try:
                    task = ImportTask.objects.get(id=task_id)
                    task.status = "failed"
                    task.completed_at = timezone.now()
                    task.progress_message = f"Import failed: {str(e)}"
                    task.error_details = [
                        {"error": str(e), "timestamp": timezone.now().isoformat()}
                    ]
                    task.save()
                except Exception as save_error:
                    logger.error(f"Failed to update task status: {save_error}")

        # Start the thread
        thread = threading.Thread(target=_run_task, daemon=True)
        thread.start()

        return task_id


class ProgressTracker:
    """Helper class for tracking import progress"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.task = None

    def __enter__(self):
        try:
            self.task = ImportTask.objects.get(id=self.task_id)
        except ImportTask.DoesNotExist:
            logger.error(f"Task {self.task_id} not found")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and self.task:
            self.task.status = "failed"
            self.task.progress_message = f"Import failed: {str(exc_val)}"
            self.task.save()

    def update(self, processed: int, total: int, message: str = ""):
        """Update progress"""
        if self.task:
            self.task.update_progress(processed, message)
