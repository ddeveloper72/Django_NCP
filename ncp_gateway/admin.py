from django.contrib import admin
from .models import (
    Country,
    Organization,
    HealthcareProfessional,
    Patient,
    CrossBorderRequest,
    AuditLog,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "ncp_endpoint"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "country", "organization_type", "is_active"]
    list_filter = ["country", "organization_type", "is_active"]
    search_fields = ["name", "identifier"]


@admin.register(HealthcareProfessional)
class HealthcareProfessionalAdmin(admin.ModelAdmin):
    list_display = ["user", "license_number", "speciality", "organization", "is_active"]
    list_filter = [
        "speciality",
        "organization",
        "is_active",
        "is_authorized_cross_border",
    ]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "license_number",
    ]


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        "national_id",
        "first_name",
        "last_name",
        "birth_date",
        "country_of_origin",
        "cross_border_consent",
    ]
    list_filter = ["country_of_origin", "gender", "cross_border_consent", "created_at"]
    search_fields = ["national_id", "european_id", "first_name", "last_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "national_id",
                    "european_id",
                    "first_name",
                    "last_name",
                    "birth_date",
                    "gender",
                )
            },
        ),
        (
            "Location & Contact",
            {"fields": ("country_of_origin", "address", "email", "phone")},
        ),
        ("Insurance & Identification", {"fields": ("insurance_number",)}),
        (
            "Privacy & Consent",
            {
                "fields": (
                    "cross_border_consent",
                    "consent_date",
                    "data_sharing_restrictions",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": ("created_at", "updated_at", "is_active"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CrossBorderRequest)
class CrossBorderRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "patient",
        "service_type",
        "requesting_country",
        "target_country",
        "status",
        "created_at",
    ]
    list_filter = [
        "service_type",
        "status",
        "requesting_country",
        "target_country",
        "created_at",
    ]
    search_fields = [
        "patient__national_id",
        "patient__first_name",
        "patient__last_name",
    ]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "processed_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "event_type", "user", "patient", "source_ip"]
    list_filter = ["event_type", "timestamp"]
    search_fields = ["user__username", "patient__national_id", "source_ip", "details"]
    ordering = ["-timestamp"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        # Audit logs should only be created by the system
        return False

    def has_delete_permission(self, request, obj=None):
        # Audit logs should not be deleted for compliance
        return False
