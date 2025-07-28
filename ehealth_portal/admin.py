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
    list_display = ["code", "name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["code", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(InternationalSearchMask)
class InternationalSearchMaskAdmin(admin.ModelAdmin):
    list_display = ["country", "name", "created_at"]
    list_filter = ["country"]
    search_fields = ["name", "country__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(SearchFieldType)
class SearchFieldTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(SearchField)
class SearchFieldAdmin(admin.ModelAdmin):
    list_display = ["mask", "field_type", "label", "required", "created_at"]
    list_filter = ["field_type", "required", "mask__country"]
    search_fields = ["label", "mask__country__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PatientSearchResult)
class PatientSearchResultAdmin(admin.ModelAdmin):
    list_display = ["patient_id", "country", "created_at"]
    list_filter = ["country", "created_at"]
    search_fields = ["patient_id"]
    readonly_fields = ["created_at", "search_data"]


# Alternative registration method in case decorator doesn't work
try:
    from .models import SMPSourceConfiguration

    if not hasattr(admin.site._registry, SMPSourceConfiguration):
        admin.site.register(SMPSourceConfiguration, SMPSourceConfigurationAdmin)
except:
    pass
