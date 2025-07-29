"""
Translation Services Admin Interface
Django admin configuration for MVC data and terminology management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import (
    ValueSetCatalogue,
    ValueSetConcept,
    ValueSetTranslation,
    ConceptTranslation,
    MVCSyncLog,
)
from .admin_forms import MVCImportForm


@admin.register(ValueSetCatalogue)
class ValueSetCatalogueAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "oid",
        "version",
        "status",
        "concept_count",
        "publisher",
        "effective_date",
        "last_updated_from_cts",
        "sync_status",
    ]
    list_filter = [
        "status",
        "publisher",
        "effective_date",
        "last_updated_from_cts",
        "sync_enabled",
        "is_local_only",
    ]
    search_fields = ["name", "oid", "description", "publisher"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "last_updated_from_cts",
        "concept_count",
    ]

    fieldsets = (
        (
            "Value Set Information",
            {
                "fields": (
                    "name",
                    "display_name",
                    "oid",
                    "description",
                    "version",
                    "status",
                )
            },
        ),
        (
            "Publishing Information",
            {
                "fields": (
                    "publisher",
                    "contact_info",
                    "copyright",
                    "effective_date",
                    "expiration_date",
                )
            },
        ),
        (
            "Binding and Usage",
            {
                "fields": (
                    "binding_strength",
                    "purpose",
                    "use_context",
                    "immutable",
                    "experimental",
                )
            },
        ),
        (
            "CTS Integration",
            {
                "fields": (
                    "terminology_system",
                    "cts_url",
                    "last_updated_from_cts",
                    "sync_enabled",
                    "is_local_only",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def concept_count(self, obj):
        """Display number of concepts in this value set"""
        count = obj.concepts.count()
        url = reverse("admin:translation_services_valuesetconcept_changelist")
        return format_html(
            '<a href="{}?value_set__id__exact={}">{} concepts</a>',
            url,
            obj.id,
            count,
        )

    concept_count.short_description = "Concepts"

    def sync_status(self, obj):
        """Display CTS synchronization status"""
        if obj.is_local_only:
            return format_html('<span style="color: orange;">Local Only</span>')
        elif obj.last_updated_from_cts:
            return format_html(
                '<span style="color: green;">Synced: {}</span>',
                obj.last_updated_from_cts.strftime("%Y-%m-%d"),
            )
        else:
            return format_html('<span style="color: red;">Never Synced</span>')

    sync_status.short_description = "Sync Status"

    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-mvc/",
                self.admin_site.admin_view(self.import_mvc_view),
                name="translation_services_valuesetcatalogue_import_mvc",
            ),
            path(
                "import-progress/<str:task_id>/",
                self.admin_site.admin_view(self.import_progress_view),
                name="mvc_import_progress",
            ),
            path(
                "import-status/<str:task_id>/",
                self.admin_site.admin_view(self.import_status_api),
                name="mvc_import_status",
            ),
            path(
                "sync-cts/",
                self.admin_site.admin_view(self.sync_cts_view),
                name="translation_services_valuesetcatalogue_sync_cts",
            ),
        ]
        return custom_urls + urls

    def import_mvc_view(self, request):
        """Custom view for MVC file import with async support"""
        if request.method == "POST":
            # Check if this is an async import request
            if request.POST.get("async_import"):
                from .services.async_mvc_importer import AsyncMVCImporter

                form = MVCImportForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        # Start async import
                        importer = AsyncMVCImporter()
                        task_id = importer.start_import(
                            mvc_file=form.cleaned_data["mvc_file"],
                            import_mode=form.cleaned_data["import_mode"],
                            selected_sheets=form.cleaned_data.get(
                                "selected_sheets", ""
                            ),
                            overwrite_existing=form.cleaned_data["overwrite_existing"],
                            dry_run=form.cleaned_data["dry_run"],
                            user=request.user,
                        )

                        messages.success(
                            request,
                            f"Import started successfully! Task ID: {task_id}. You can safely navigate away from this page.",
                        )

                        # Redirect to progress page
                        from django.urls import reverse

                        progress_url = reverse(
                            "admin:mvc_import_progress", args=[task_id]
                        )
                        return redirect(progress_url)

                    except Exception as e:
                        messages.error(request, f"Failed to start import: {str(e)}")

            else:
                # Synchronous import (original behavior)
                form = MVCImportForm(request.POST, request.FILES)
                if form.is_valid():
                    try:
                        # Process the import
                        result = form.process_import()

                        messages.success(
                            request,
                            f"Successfully imported {result['total_value_sets']} value sets "
                            f"with {result['total_concepts']} concepts from MVC file.",
                        )

                        # Log the import
                        MVCSyncLog.objects.create(
                            sync_type="full_sync",
                            source="local_file",
                            started_at=timezone.now(),
                            completed_at=timezone.now(),
                            status="completed",
                            value_sets_processed=result["total_value_sets"],
                            concepts_processed=result["total_concepts"],
                            sync_details={"import_summary": result},
                        )

                        return redirect(
                            "admin:translation_services_valuesetcatalogue_changelist"
                        )

                    except Exception as e:
                        messages.error(request, f"Import failed: {str(e)}")
        else:
            form = MVCImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Import MVC File",
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/translation_services/import_mvc.html", context)

    def sync_cts_view(self, request):
        """Custom view for CTS synchronization"""
        if request.method == "POST":
            # TODO: Implement CTS sync logic
            messages.info(request, "CTS synchronization feature coming soon!")
            return redirect("admin:translation_services_valuesetcatalogue_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "Sync with CTS",
            "opts": self.model._meta,
        }
        return render(request, "admin/translation_services/sync_cts.html", context)

    def import_progress_view(self, request, task_id):
        """Progress tracking page for MVC imports"""
        from .services.async_mvc_importer import ImportTaskService

        task_status = ImportTaskService.get_task_status(task_id)
        if not task_status:
            messages.error(request, f"Import task {task_id} not found.")
            return redirect("admin:translation_services_valuesetcatalogue_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": "MVC Import Progress",
            "task_id": task_id,
            "task_status": task_status,
            "opts": self.model._meta,
        }
        return render(
            request, "admin/translation_services/import_progress.html", context
        )

    def import_status_api(self, request, task_id):
        """API endpoint for import status"""
        from django.http import JsonResponse
        from .services.async_mvc_importer import ImportTaskService

        task_status = ImportTaskService.get_task_status(task_id)
        if not task_status:
            return JsonResponse({"error": "Task not found"}, status=404)

        return JsonResponse(task_status)


@admin.register(ValueSetConcept)
class ValueSetConceptAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "display",
        "value_set_name",
        "code_system",
        "status",
        "created_at",
    ]
    list_filter = [
        "status",
        "code_system",
        "value_set__name",
        "created_at",
    ]
    search_fields = [
        "code",
        "display",
        "definition",
        "value_set__name",
        "code_system",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Concept Information",
            {
                "fields": (
                    "value_set",
                    "code",
                    "display",
                    "definition",
                    "status",
                )
            },
        ),
        (
            "Code System Information",
            {
                "fields": (
                    "code_system",
                    "code_system_version",
                )
            },
        ),
        (
            "Additional Properties",
            {
                "fields": ("properties",),
                "classes": ("collapse",),
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def value_set_name(self, obj):
        """Display value set name with link"""
        url = reverse(
            "admin:translation_services_valuesetcatalogue_change",
            args=[obj.value_set.id],
        )
        return format_html('<a href="{}">{}</a>', url, obj.value_set.name)

    value_set_name.short_description = "Value Set"


@admin.register(ValueSetTranslation)
class ValueSetTranslationAdmin(admin.ModelAdmin):
    list_display = [
        "value_set",
        "language_code",
        "translated_name",
        "translation_quality",
        "created_at",
    ]
    list_filter = ["language_code", "translation_quality", "created_at"]
    search_fields = [
        "value_set__name",
        "translated_name",
        "translated_description",
        "language_code",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ConceptTranslation)
class ConceptTranslationAdmin(admin.ModelAdmin):
    list_display = [
        "concept",
        "language_code",
        "translated_display",
        "translation_quality",
        "created_at",
    ]
    list_filter = ["language_code", "translation_quality", "created_at"]
    search_fields = [
        "concept__code",
        "concept__display",
        "translated_display",
        "translated_definition",
        "language_code",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(MVCSyncLog)
class MVCSyncLogAdmin(admin.ModelAdmin):
    list_display = [
        "sync_type",
        "source",
        "status",
        "started_at",
        "duration_display",
        "value_sets_processed",
        "concepts_processed",
    ]
    list_filter = [
        "sync_type",
        "source",
        "status",
        "started_at",
    ]
    search_fields = ["error_message", "sync_details"]
    readonly_fields = [
        "started_at",
        "completed_at",
        "duration_display",
        "created_at",
    ]

    fieldsets = (
        (
            "Sync Information",
            {
                "fields": (
                    "sync_type",
                    "source",
                    "started_at",
                    "completed_at",
                    "duration_display",
                    "status",
                )
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "value_sets_processed",
                    "value_sets_created",
                    "value_sets_updated",
                    "concepts_processed",
                    "translations_processed",
                )
            },
        ),
        (
            "Details",
            {
                "fields": ("error_message", "sync_details"),
                "classes": ("collapse",),
            },
        ),
    )

    def duration_display(self, obj):
        """Display sync duration in a readable format"""
        if obj.duration:
            total_seconds = int(obj.duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"

    duration_display.short_description = "Duration"

    def has_add_permission(self, request):
        """Sync logs are auto-created, no manual adding"""
        return False
