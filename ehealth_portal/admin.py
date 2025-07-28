from django.contrib import admin
from .models import (
    Country,
    InternationalSearchMask,
    SMPSourceConfiguration,
    SearchFieldType,
    SearchField,
    PatientSearchResult,
)


@admin.register(SMPSourceConfiguration)
class SMPSourceConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "is_active", "updated_at")
    list_filter = ("source_type", "is_active")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Basic Configuration", {"fields": ("name", "source_type", "is_active")}),
        (
            "European SMP URLs",
            {
                "fields": ("european_smp_api_url", "european_smp_ui_url"),
                "description": "European Commission test SMP configuration",
            },
        ),
        (
            "Local SMP URLs",
            {
                "fields": ("localhost_smp_api_url", "localhost_smp_ui_url"),
                "description": "Local DomiSMP server configuration",
            },
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the default configuration
        if obj and obj.name == "default":
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request):
        # Only superusers can add SMP configurations
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Only superusers can modify SMP configurations
        return request.user.is_superuser

    def get_queryset(self, request):
        # Show all configurations to superusers, none to others
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.none()
        return qs


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_available", "created_at"]
    list_filter = ["is_available", "is_test_environment"]
    search_fields = ["code", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(InternationalSearchMask)
class InternationalSearchMaskAdmin(admin.ModelAdmin):
    list_display = ["country", "mask_name", "mask_version", "is_active", "created_at"]
    list_filter = ["country", "is_active"]
    search_fields = ["mask_name", "country__name"]
    readonly_fields = ["created_at", "updated_at", "last_synchronized"]


@admin.register(PatientSearchResult)
class PatientSearchResultAdmin(admin.ModelAdmin):
    list_display = ["country", "searched_by", "patient_found", "search_timestamp"]
    list_filter = ["country", "patient_found", "search_timestamp"]
    search_fields = ["searched_by__username", "country__name"]
    readonly_fields = ["search_timestamp", "search_fields", "patient_data"]


@admin.register(SearchFieldType)
class SearchFieldTypeAdmin(admin.ModelAdmin):
    list_display = ["type_code", "display_name", "html_input_type"]
    search_fields = ["type_code", "display_name", "description"]
    readonly_fields = []


@admin.register(SearchField)
class SearchFieldAdmin(admin.ModelAdmin):
    list_display = ["search_mask", "field_type", "label", "is_required", "field_order"]
    list_filter = ["field_type", "is_required", "search_mask__country"]
    search_fields = ["label", "search_mask__country__name"]
    readonly_fields = []
