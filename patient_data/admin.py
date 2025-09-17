"""
Patient Data Admin Interface
Django admin configuration for patient data management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.forms import JSONField
from django import forms
import json

from .models import (
    MemberState,
    PatientIdentifier,
    PatientData,
    AvailableService,
    PatientServiceRequest,
    ClinicalSectionConfig,
    ColumnPreset,
    DataExtractionLog,
    Tooltip,
)

# from . import test_data_views  # Temporarily disabled - needs fixing


@admin.register(MemberState)
class MemberStateAdmin(admin.ModelAdmin):
    list_display = [
        "country_name",
        "country_code",
        "language_code",
        "home_community_id",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "language_code", "created_at"]
    search_fields = ["country_name", "country_code", "home_community_id"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("country_code", "country_name", "language_code")},
        ),
        (
            "NCP Configuration",
            {"fields": ("ncp_endpoint", "home_community_id", "is_active")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(AvailableService)
class AvailableServiceAdmin(admin.ModelAdmin):
    list_display = ["service_name", "service_type", "member_state", "is_active"]
    list_filter = ["service_type", "is_active", "member_state"]
    search_fields = ["service_name", "service_description"]

    fieldsets = (
        (
            "Service Information",
            {"fields": ("service_name", "service_type", "service_description")},
        ),
        ("Configuration", {"fields": ("member_state", "is_active")}),
    )


class AvailableServiceInline(admin.TabularInline):
    model = AvailableService
    extra = 1
    fields = ["service_type", "service_name", "is_active"]


@admin.register(PatientIdentifier)
class PatientIdentifierAdmin(admin.ModelAdmin):
    list_display = ["patient_id", "home_member_state", "id_root", "created_at"]
    list_filter = ["home_member_state", "created_at"]
    search_fields = ["patient_id", "id_extension", "id_root"]
    readonly_fields = ["created_at"]

    fieldsets = (
        (
            "Patient Identification",
            {"fields": ("patient_id", "id_extension", "id_root")},
        ),
        ("Source Information", {"fields": ("home_member_state",)}),
        ("Metadata", {"fields": ("created_at",), "classes": ("collapse",)}),
    )


@admin.register(PatientData)
class PatientDataAdmin(admin.ModelAdmin):
    list_display = [
        "get_patient_name",
        "patient_identifier",
        "birth_date",
        "gender",
        "get_access_type",
        "accessed_by",
        "access_timestamp",
    ]
    list_filter = [
        "gender",
        "consent_given",
        "break_glass_access",
        "access_timestamp",
        "patient_identifier__home_member_state",
    ]
    search_fields = [
        "given_name",
        "family_name",
        "patient_identifier__patient_id",
        "accessed_by__username",
    ]
    readonly_fields = ["access_timestamp", "consent_timestamp", "break_glass_timestamp"]

    fieldsets = (
        (
            "Patient Information",
            {
                "fields": (
                    "patient_identifier",
                    "given_name",
                    "family_name",
                    "birth_date",
                    "gender",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": ("address_line", "city", "postal_code", "country"),
                "classes": ("collapse",),
            },
        ),
        (
            "Consent Management",
            {"fields": ("consent_given", "consent_timestamp", "consent_given_by")},
        ),
        (
            "Break Glass Access",
            {
                "fields": (
                    "break_glass_access",
                    "break_glass_reason",
                    "break_glass_by",
                    "break_glass_timestamp",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Access Tracking", {"fields": ("accessed_by", "access_timestamp")}),
        (
            "Raw Data",
            {
                "fields": ("raw_patient_summary", "raw_eprescription"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_urls(self):
        """Add custom URLs for test data management."""
        urls = super().get_urls()
        # custom_urls = [  # Temporarily disabled - needs fixing
        #     path(
        #         "test-data/dashboard/",
        #         self.admin_site.admin_view(test_data_views.test_data_dashboard),
        #         name="patient_data_test_data_dashboard",
        #     ),
        #     path(
        #         "test-data/list/",
        #         self.admin_site.admin_view(test_data_views.test_data_list),
        #         name="patient_data_test_data_list",
        #     ),
        #     path(
        #         "test-data/patient/<int:patient_data_id>/",
        #         self.admin_site.admin_view(test_data_views.test_data_patient_view),
        #         name="patient_data_test_data_patient_view",
        #     ),
        # ]
        # return custom_urls + urls  # Temporarily disabled
        return urls

    def get_patient_name(self, obj):
        name = f"{obj.given_name} {obj.family_name}".strip()
        return name if name else "Unknown"

    get_patient_name.short_description = "Patient Name"

    def get_access_type(self, obj):
        access_type = obj.get_access_type()
        if access_type == "Break Glass":
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>', access_type
            )
        elif access_type == "With Consent":
            return format_html('<span style="color: green;">{}</span>', access_type)
        else:
            return format_html('<span style="color: orange;">{}</span>', access_type)

    get_access_type.short_description = "Access Type"


@admin.register(PatientServiceRequest)
class PatientServiceRequestAdmin(admin.ModelAdmin):
    list_display = [
        "request_id",
        "get_patient_info",
        "requested_service",
        "status",
        "consent_method",
        "requested_by",
        "request_timestamp",
    ]
    list_filter = [
        "status",
        "consent_method",
        "consent_required",
        "consent_obtained",
        "request_timestamp",
        "requested_service__service_type",
    ]
    search_fields = [
        "request_id",
        "patient_identifier__patient_id",
        "requested_by__username",
        "error_message",
    ]
    readonly_fields = ["request_id", "request_timestamp", "response_timestamp"]

    fieldsets = (
        (
            "Request Information",
            {
                "fields": (
                    "request_id",
                    "patient_identifier",
                    "requested_service",
                    "requested_by",
                    "request_timestamp",
                )
            },
        ),
        (
            "Status and Consent",
            {
                "fields": (
                    "status",
                    "consent_required",
                    "consent_obtained",
                    "consent_method",
                )
            },
        ),
        (
            "Response Data",
            {
                "fields": ("response_data", "response_timestamp", "error_message"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_patient_info(self, obj):
        return f"{obj.patient_identifier.patient_id} ({obj.patient_identifier.home_member_state.country_code})"

    get_patient_info.short_description = "Patient"

    actions = ["mark_as_completed", "mark_as_failed"]

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status="COMPLETED", response_timestamp=timezone.now())
        self.message_user(request, f"{updated} requests marked as completed.")

    mark_as_completed.short_description = "Mark selected requests as completed"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="FAILED")
        self.message_user(request, f"{updated} requests marked as failed.")

    mark_as_failed.short_description = "Mark selected requests as failed"


# Custom Admin Site Extension for Test Data Management
class PatientDataAdminSite(admin.AdminSite):
    site_header = "EU NCP Patient Data Administration"
    site_title = "EU NCP Admin"
    index_title = "Patient Data Management"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "test-data/dashboard/",
                self.admin_view(test_data_views.test_data_dashboard),
                name="patient_data_test_data_dashboard",
            ),
            path(
                "test-data/list/",
                self.admin_view(test_data_views.test_data_list),
                name="patient_data_test_data_list",
            ),
            path(
                "test-data/patient/<int:patient_data_id>/",
                self.admin_view(test_data_views.test_data_patient_view),
                name="patient_data_test_data_patient_view",
            ),
            path(
                "test-data/document/<int:document_id>/",
                self.admin_view(test_data_views.test_data_document_view),
                name="patient_data_test_data_document_view",
            ),
            path(
                "test-data/document/<int:document_id>/pdf/",
                self.admin_view(test_data_views.test_data_document_pdf),
                name="patient_data_test_data_document_pdf",
            ),
            path(
                "test-data/document/<int:document_id>/translated/",
                self.admin_view(test_data_views.test_data_translated_view),
                name="patient_data_test_data_translated_view",
            ),
            path(
                "test-data/import/",
                self.admin_view(test_data_views.import_external_test_data),
                name="patient_data_import_external_test_data",
            ),
            path(
                "test-data/api/stats/",
                self.admin_view(test_data_views.test_data_stats_api),
                name="patient_data_test_data_stats_api",
            ),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """
        Customized admin index with test data management links
        """
        extra_context = extra_context or {}

        # Add test data statistics
        try:
            test_data_count = PatientData.objects.filter(source="EU_TEST_DATA").count()
            extra_context["test_data_count"] = test_data_count
        except:
            extra_context["test_data_count"] = 0

        return super().index(request, extra_context)


# Create custom admin site instance
patient_admin_site = PatientDataAdminSite(name="patient_admin")

# Register models with custom admin site
patient_admin_site.register(MemberState, MemberStateAdmin)
patient_admin_site.register(AvailableService, AvailableServiceAdmin)
patient_admin_site.register(PatientIdentifier, PatientIdentifierAdmin)


# Column Configuration Admin Classes
class ClinicalSectionConfigForm(forms.ModelForm):
    """Custom form for column configuration"""

    xpath_patterns = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "cols": 80}),
        help_text="Enter XPath patterns as JSON list, e.g., ['.//hl7:code/@code', './/hl7:value/@displayName']",
        required=False,
    )

    field_mappings = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "cols": 80}),
        help_text="Enter field name patterns as JSON list, e.g., ['Problem DisplayName', 'Condition', 'problem']",
        required=False,
    )

    class Meta:
        model = ClinicalSectionConfig
        fields = "__all__"

    def clean_xpath_patterns(self):
        """Validate XPath patterns JSON"""
        data = self.cleaned_data["xpath_patterns"]
        if not data:
            return []
        try:
            patterns = json.loads(data)
            if not isinstance(patterns, list):
                raise forms.ValidationError("XPath patterns must be a JSON list")
            return patterns
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format for XPath patterns")

    def clean_field_mappings(self):
        """Validate field mappings JSON"""
        data = self.cleaned_data["field_mappings"]
        if not data:
            return []
        try:
            mappings = json.loads(data)
            if not isinstance(mappings, list):
                raise forms.ValidationError("Field mappings must be a JSON list")
            return mappings
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format for field mappings")


@admin.register(ClinicalSectionConfig)
class ClinicalSectionConfigAdmin(admin.ModelAdmin):
    """Admin interface for clinical section column configuration"""

    form = ClinicalSectionConfigForm
    list_display = [
        "section_code",
        "display_label",
        "column_type",
        "is_enabled",
        "is_primary",
        "display_order",
        "created_by",
    ]
    list_filter = [
        "section_code",
        "column_type",
        "is_enabled",
        "is_primary",
        "created_by",
    ]
    search_fields = ["display_label", "column_key", "section_code"]
    ordering = ["section_code", "display_order", "display_label"]

    fieldsets = (
        (
            "Basic Configuration",
            {"fields": ("section_code", "column_key", "display_label", "column_type")},
        ),
        (
            "Display Settings",
            {"fields": ("is_enabled", "is_primary", "display_order", "css_class")},
        ),
        (
            "Data Extraction",
            {
                "fields": ("xpath_patterns", "field_mappings"),
                "description": "Configure how data is extracted from CDA XML",
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by to current user"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ColumnPreset)
class ColumnPresetAdmin(admin.ModelAdmin):
    """Admin interface for column presets"""

    list_display = ["name", "section_code", "is_default", "created_by", "created_at"]
    list_filter = ["section_code", "is_default", "created_by"]
    search_fields = ["name", "description"]

    fieldsets = (
        (
            "Preset Information",
            {"fields": ("name", "description", "section_code", "is_default")},
        ),
        (
            "Column Configuration",
            {
                "fields": ("columns_config",),
                "description": "JSON configuration for all columns in this preset",
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DataExtractionLog)
class DataExtractionLogAdmin(admin.ModelAdmin):
    """Admin interface for data extraction discovery logs"""

    list_display = [
        "section_code",
        "field_name",
        "frequency_count",
        "value_type",
        "last_seen",
    ]
    list_filter = ["section_code", "value_type", "first_seen", "last_seen"]
    search_fields = ["field_name", "xpath_found", "sample_value"]
    readonly_fields = ["first_seen", "last_seen"]
    ordering = ["-frequency_count", "section_code", "field_name"]

    fieldsets = (
        (
            "Extraction Details",
            {"fields": ("patient_id", "section_code", "field_name", "xpath_found")},
        ),
        (
            "Value Information",
            {"fields": ("sample_value", "value_type", "frequency_count")},
        ),
        ("Timestamps", {"fields": ("first_seen", "last_seen")}),
    )

    def has_add_permission(self, request):
        """Logs are created automatically, no manual additions"""
        return False


patient_admin_site.register(PatientData, PatientDataAdmin)
patient_admin_site.register(PatientServiceRequest, PatientServiceRequestAdmin)


# Enhance MemberState admin with services inline
MemberStateAdmin.inlines = [AvailableServiceInline]


@admin.register(Tooltip)
class TooltipAdmin(admin.ModelAdmin):
    """
    Admin interface for managing tooltips
    Provides easy editing and organization of tooltip content
    """
    
    list_display = [
        'key',
        'title',
        'category',
        'target_audience', 
        'is_active_display',
        'placement',
        'updated_at'
    ]
    
    list_filter = [
        'category',
        'target_audience',
        'is_active',
        'placement',
        'created_at'
    ]
    
    search_fields = [
        'key',
        'title',
        'content'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        (
            "Tooltip Identification",
            {
                'fields': ('key', 'title', 'category', 'target_audience')
            }
        ),
        (
            "Content",
            {
                'fields': ('content',),
                'description': 'The tooltip text that will be displayed to users'
            }
        ),
        (
            "Display Settings",
            {
                'fields': ('placement', 'is_active'),
                'description': 'Control how and when the tooltip appears'
            }
        ),
        (
            "Metadata",
            {
                'fields': ('created_by', 'created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ),
    )
    
    actions = [
        'make_active',
        'make_inactive',
        'duplicate_tooltip'
    ]
    
    def is_active_display(self, obj):
        """Display active status with color coding"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Inactive</span>'
            )
    is_active_display.short_description = 'Status'
    
    def make_active(self, request, queryset):
        """Bulk action to activate tooltips"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{count} tooltip(s) have been activated.'
        )
    make_active.short_description = "Activate selected tooltips"
    
    def make_inactive(self, request, queryset):
        """Bulk action to deactivate tooltips"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{count} tooltip(s) have been deactivated.'
        )
    make_inactive.short_description = "Deactivate selected tooltips"
    
    def duplicate_tooltip(self, request, queryset):
        """Bulk action to duplicate tooltips for different audiences"""
        count = 0
        for tooltip in queryset:
            # Create a copy with modified key
            new_key = f"{tooltip.key}_copy"
            if not Tooltip.objects.filter(key=new_key).exists():
                Tooltip.objects.create(
                    key=new_key,
                    title=f"{tooltip.title} (Copy)",
                    content=tooltip.content,
                    category=tooltip.category,
                    target_audience=tooltip.target_audience,
                    placement=tooltip.placement,
                    is_active=False,  # Start inactive for review
                    created_by=request.user
                )
                count += 1
        
        self.message_user(
            request,
            f'{count} tooltip(s) have been duplicated for editing.'
        )
    duplicate_tooltip.short_description = "Duplicate selected tooltips"
    
    def save_model(self, request, obj, form, change):
        """Auto-assign created_by when creating new tooltips"""
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
