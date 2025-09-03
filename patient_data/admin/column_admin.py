"""
Django Admin Configuration for Dynamic Clinical Tables
Provides admin interface for managing column configurations
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.forms import JSONField
from django import forms
import json

# Import models - will create these in patient_data/models.py
from patient_data.models import ClinicalSectionConfig, ColumnPreset, DataExtractionLog


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
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Filter columns based on user permissions"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see their own column configs
            qs = qs.filter(created_by=request.user)
        return qs


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


# Custom admin actions
def duplicate_column_config(modeladmin, request, queryset):
    """Action to duplicate column configurations"""
    for config in queryset:
        config.pk = None  # Create new instance
        config.column_key = f"{config.column_key}_copy"
        config.display_label = f"{config.display_label} (Copy)"
        config.created_by = request.user
        config.save()


duplicate_column_config.short_description = "Duplicate selected column configurations"


def create_preset_from_configs(modeladmin, request, queryset):
    """Create a preset from selected column configurations"""
    if not queryset.exists():
        return

    # Group by section_code
    sections = {}
    for config in queryset:
        if config.section_code not in sections:
            sections[config.section_code] = []
        sections[config.section_code].append(
            {
                "key": config.column_key,
                "label": config.display_label,
                "type": config.column_type,
                "primary": config.is_primary,
                "order": config.display_order,
                "xpath_patterns": config.xpath_patterns,
                "field_mappings": config.field_mappings,
            }
        )

    # Create presets for each section
    for section_code, columns in sections.items():
        preset_name = f"Custom Preset - {section_code}"
        ColumnPreset.objects.create(
            name=preset_name,
            description=f"Auto-generated preset from {len(columns)} columns",
            section_code=section_code,
            columns_config=columns,
            created_by=request.user,
        )


create_preset_from_configs.short_description = (
    "Create presets from selected configurations"
)

# Add actions to admin
ClinicalSectionConfigAdmin.actions = [
    duplicate_column_config,
    create_preset_from_configs,
]
