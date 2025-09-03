"""
Dynamic Column Configuration Management
Allows admin-controlled table customization based on available XML endpoints
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json


class ClinicalSectionConfig(models.Model):
    """Configuration for clinical section table columns"""

    SECTION_CHOICES = [
        ("47519-4", "Clinical Procedures"),
        ("11450-4", "Medical Conditions & Problems"),
        ("48765-2", "Allergies and Adverse Reactions"),
        ("10160-0", "Current & Past Medications"),
        ("30954-2", "Relevant diagnostic tests/laboratory data"),
        ("8716-3", "Vital Signs"),
        ("10157-6", "History of family member diseases"),
        ("10162-6", "History of occupational exposure"),
        ("29762-2", "Social history Narrative"),
    ]

    COLUMN_TYPE_CHOICES = [
        ("text", "Text Display"),
        ("date", "Date/Time"),
        ("status", "Status Badge"),
        ("codes", "Medical Codes"),
        ("numeric", "Numeric Value"),
        ("severity", "Severity Level"),
        ("duration", "Time Duration"),
        ("dosage", "Medication Dosage"),
        ("frequency", "Frequency/Timing"),
    ]

    section_code = models.CharField(
        max_length=20, choices=SECTION_CHOICES, help_text="LOINC section code"
    )
    column_key = models.CharField(max_length=50, help_text="Internal column identifier")
    display_label = models.CharField(
        max_length=100, help_text="User-visible column header"
    )
    column_type = models.CharField(
        max_length=20, choices=COLUMN_TYPE_CHOICES, default="text"
    )
    xpath_patterns = models.JSONField(
        default=list, help_text="XML XPath patterns to extract data", blank=True
    )
    field_mappings = models.JSONField(
        default=list, help_text="CDA field name patterns to search", blank=True
    )
    is_enabled = models.BooleanField(default=True)
    is_primary = models.BooleanField(
        default=False, help_text="Primary column (always shown first)"
    )
    display_order = models.PositiveIntegerField(default=10)
    css_class = models.CharField(
        max_length=100, blank=True, help_text="Additional CSS classes"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_columns"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clinical_section_configs"
        unique_together = [("section_code", "column_key")]
        ordering = ["section_code", "display_order", "display_label"]

    def __str__(self):
        return f"{self.get_section_code_display()} - {self.display_label}"

    def clean(self):
        """Validation for column configuration"""
        if self.is_primary:
            # Ensure only one primary column per section
            existing_primary = ClinicalSectionConfig.objects.filter(
                section_code=self.section_code, is_primary=True
            ).exclude(pk=self.pk)

            if existing_primary.exists():
                raise ValidationError(
                    f"Section {self.section_code} already has a primary column"
                )

        # Validate JSON fields
        if not isinstance(self.xpath_patterns, list):
            raise ValidationError("XPath patterns must be a list")
        if not isinstance(self.field_mappings, list):
            raise ValidationError("Field mappings must be a list")


class ColumnPreset(models.Model):
    """Predefined column configurations for different use cases"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    section_code = models.CharField(
        max_length=20, choices=ClinicalSectionConfig.SECTION_CHOICES
    )
    columns_config = models.JSONField(
        help_text="JSON configuration for all columns in this preset"
    )
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clinical_column_presets"
        ordering = ["section_code", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_section_code_display()})"


class DataExtractionLog(models.Model):
    """Log available XML endpoints for dynamic discovery"""

    patient_id = models.CharField(max_length=100)
    section_code = models.CharField(max_length=20)
    xpath_found = models.TextField(help_text="XPath that contained data")
    field_name = models.CharField(max_length=100)
    sample_value = models.TextField(blank=True)
    value_type = models.CharField(max_length=50)
    frequency_count = models.PositiveIntegerField(default=1)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "data_extraction_logs"
        unique_together = [("section_code", "xpath_found", "field_name")]
        indexes = [
            models.Index(fields=["section_code"]),
            models.Index(fields=["frequency_count"]),
        ]

    def __str__(self):
        return f"{self.section_code}: {self.field_name} ({self.frequency_count}x)"
