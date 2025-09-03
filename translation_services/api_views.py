"""
API Views for MVC Import Progress Tracking
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from .services.async_mvc_importer import ImportTaskService, AsyncMVCImporter


@staff_member_required
@require_http_methods(["GET"])
def import_task_status(request, task_id):
    """Get the status of an import task"""
    task_status = ImportTaskService.get_task_status(task_id)

    if task_status is None:
        return JsonResponse({"error": "Task not found"}, status=404)

    return JsonResponse(task_status)


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(csrf_exempt, name="dispatch")
class AsyncMVCImportView(View):
    """Handle asynchronous MVC file imports"""

    def post(self, request):
        """Start an asynchronous MVC import"""
        try:
            # Parse form data
            mvc_file = request.FILES.get("mvc_file")
            import_mode = request.POST.get("import_mode", "full")
            selected_sheets = request.POST.get("selected_sheets", "")
            overwrite_existing = request.POST.get("overwrite_existing") == "on"
            dry_run = request.POST.get("dry_run") == "on"

            if not mvc_file:
                return JsonResponse({"error": "No file uploaded"}, status=400)

            # Start async import
            importer = AsyncMVCImporter()
            task_id = importer.start_import(
                mvc_file=mvc_file,
                import_mode=import_mode,
                selected_sheets=selected_sheets,
                overwrite_existing=overwrite_existing,
                dry_run=dry_run,
                user=request.user,
            )

            return JsonResponse(
                {
                    "task_id": task_id,
                    "message": "Import started successfully",
                    "status_url": f"/admin/translation_services/import-status/{task_id}/",
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
