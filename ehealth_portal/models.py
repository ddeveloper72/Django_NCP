"""
eHealth Portal Models - Dynamic International Search Mask (ISM) Configuration
Supports country-specific search forms based on SMP-provided ISM data
"""

from django.db import models
from django.contrib.auth.models import User
import json


class SMPSourceConfiguration(models.Model):
    """Global SMP source configuration for the application"""

    SMP_SOURCE_CHOICES = [
        ("european", "European Commission Test SMP"),
        ("localhost", "Local DomiSMP Server"),
    ]

    name = models.CharField(max_length=100, unique=True, default="default")
    source_type = models.CharField(
        max_length=20,
        choices=SMP_SOURCE_CHOICES,
        default="european",
        help_text="Select which SMP server to use as primary source",
    )

    # European SMP Configuration
    european_smp_api_url = models.URLField(
        default="https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
        help_text="European Commission test SMP API base URL (for backend operations)",
    )
    european_smp_ui_url = models.URLField(
        default="https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/ui/index.html",
        help_text="European Commission test SMP UI URL (for user display)",
    )

    # Local SMP Configuration
    localhost_smp_api_url = models.URLField(
        default="http://localhost:8290/smp",
        help_text="Local DomiSMP API base URL (for backend operations)",
    )
    localhost_smp_ui_url = models.URLField(
        default="http://localhost:8290/smp",
        help_text="Local DomiSMP UI URL (for user display)",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMP Source Configuration"
        verbose_name_plural = "SMP Source Configurations"

    def __str__(self):
        return f"{self.name} - {self.get_source_type_display()}"

    def get_active_smp_api_url(self):
        """Get the currently active SMP API URL for backend operations"""
        if self.source_type == "european":
            return self.european_smp_api_url
        else:
            return self.localhost_smp_api_url

    def get_active_smp_ui_url(self):
        """Get the currently active SMP UI URL for user display"""
        if self.source_type == "european":
            return self.european_smp_ui_url
        else:
            return self.localhost_smp_ui_url

    def get_active_smp_name(self):
        """Get a friendly name for the active SMP"""
        return self.get_source_type_display()

    @classmethod
    def get_current_config(cls):
        """Get the current active SMP configuration"""
        config, created = cls.objects.get_or_create(
            name="default", defaults={"source_type": "european", "is_active": True}
        )
        return config

    @classmethod
    def get_default_config(cls):
        """Get or create the default SMP configuration"""
        config, created = cls.objects.get_or_create(
            name="default", defaults={"source_type": "european", "is_active": True}
        )
        return config


class Country(models.Model):
    """EU Member State configuration"""

    code = models.CharField(
        max_length=2, primary_key=True, help_text="ISO 3166-1 alpha-2 country code"
    )
    name = models.CharField(max_length=100)
    flag_image = models.CharField(max_length=200, default="flags/{code}.png")

    # NCP Configuration
    ncp_url = models.URLField(blank=True, help_text="Country's NCP endpoint URL")
    smp_url = models.URLField(blank=True, help_text="Country's SMP server URL")

    # ISM Configuration
    ism_last_updated = models.DateTimeField(null=True, blank=True)
    ism_configuration = models.JSONField(
        default=dict, help_text="Current ISM configuration from SMP"
    )

    # Status
    is_available = models.BooleanField(default=True)
    is_test_environment = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class SearchFieldType(models.Model):
    """Types of search fields that can appear in ISM"""

    FIELD_TYPES = [
        ("text", "Text Input"),
        ("date", "Date Input"),
        ("select", "Dropdown Select"),
        ("radio", "Radio Buttons"),
        ("checkbox", "Checkbox"),
        ("number", "Number Input"),
        ("email", "Email Input"),
        ("phone", "Phone Input"),
        ("ssn", "Social Security Number"),
        ("id_card", "ID Card Number"),
        ("passport", "Passport Number"),
    ]

    type_code = models.CharField(max_length=20, choices=FIELD_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    validation_pattern = models.CharField(
        max_length=500, blank=True, help_text="Regex pattern for validation"
    )
    html_input_type = models.CharField(max_length=20, default="text")

    def __str__(self):
        return self.display_name


class InternationalSearchMask(models.Model):
    """International Search Mask configuration per country"""

    country = models.OneToOneField(
        Country, on_delete=models.CASCADE, related_name="search_mask"
    )

    # Mask Metadata
    mask_name = models.CharField(max_length=200)
    mask_version = models.CharField(max_length=20, default="1.0")
    mask_description = models.TextField(blank=True)

    # Source Information
    source_smp_url = models.URLField(help_text="SMP URL where this mask was retrieved")
    last_synchronized = models.DateTimeField(auto_now=True)

    # Configuration
    is_active = models.BooleanField(default=True)
    requires_authentication = models.BooleanField(default=True)

    # Raw Data
    raw_ism_data = models.JSONField(default=dict, help_text="Raw ISM data from SMP")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ISM for {self.country.name} v{self.mask_version}"


class SearchField(models.Model):
    """Individual search fields in an ISM"""

    search_mask = models.ForeignKey(
        InternationalSearchMask, on_delete=models.CASCADE, related_name="fields"
    )

    # Field Definition
    field_code = models.CharField(max_length=50, help_text="Unique field identifier")
    field_type = models.ForeignKey(SearchFieldType, on_delete=models.CASCADE)

    # Display Properties
    label = models.CharField(max_length=200)
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)

    # Validation
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    validation_pattern = models.CharField(max_length=500, blank=True)
    error_message = models.CharField(max_length=300, blank=True)

    # Options for select/radio fields
    field_options = models.JSONField(
        default=list, help_text="Options for select/radio fields"
    )
    default_value = models.CharField(max_length=200, blank=True)

    # Layout
    field_order = models.IntegerField(default=0)
    field_group = models.CharField(
        max_length=100, blank=True, help_text="Group fields together"
    )
    css_classes = models.CharField(max_length=200, blank=True)

    # Conditional Logic
    depends_on_field = models.CharField(
        max_length=50, blank=True, help_text="Field code this depends on"
    )
    dependency_condition = models.JSONField(
        default=dict, help_text="Condition for showing this field"
    )

    class Meta:
        ordering = ["field_order", "field_code"]
        unique_together = ["search_mask", "field_code"]

    def __str__(self):
        return f"{self.label} ({self.field_code})"


class PatientSearchResult(models.Model):
    """Store patient search results and history"""

    # Search Context
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    searched_by = models.ForeignKey(User, on_delete=models.CASCADE)
    search_timestamp = models.DateTimeField(auto_now_add=True)

    # Search Parameters
    search_fields = models.JSONField(help_text="Fields and values used in search")
    search_mask_version = models.CharField(max_length=20)

    # Results
    patient_found = models.BooleanField(default=False)
    patient_data = models.JSONField(default=dict, help_text="Patient data if found")
    available_documents = models.JSONField(
        default=list, help_text="Available documents for patient"
    )

    # NCP Response
    ncp_response_time = models.FloatField(
        null=True, help_text="Response time in seconds"
    )
    ncp_status_code = models.CharField(max_length=10, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-search_timestamp"]

    def __str__(self):
        return f"Search in {self.country.code} by {self.searched_by.username}"
