"""
Patient Data Models
Django models for managing patient data retrieved from other EU member states
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class MemberState(models.Model):
    """EU Member State information for patient data exchange"""

    country_code = models.CharField(
        max_length=2,
        unique=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., 'DE', 'FR', 'IT')",
    )
    country_name = models.CharField(
        max_length=100,
        help_text="Full country name (e.g., 'Germany', 'France', 'Italy')",
    )
    language_code = models.CharField(
        max_length=10,
        help_text="ISO 639 language code (e.g., 'de-DE', 'fr-FR', 'it-IT')",
    )
    ncp_endpoint = models.URLField(help_text="National Contact Point endpoint URL")
    home_community_id = models.CharField(
        max_length=100, help_text="OID for the home community identifier"
    )
    sample_data_oid = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="OID for sample patient data (used for testing/demo)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Member State"
        verbose_name_plural = "Member States"
        ordering = ["country_name"]

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class PatientIdentifier(models.Model):
    """Patient identifier from another member state"""

    patient_id = models.CharField(
        max_length=100, help_text="Patient ID in the home member state"
    )
    home_member_state = models.ForeignKey(
        MemberState, on_delete=models.CASCADE, related_name="patient_identifiers"
    )
    id_extension = models.CharField(
        max_length=100, blank=True, help_text="Extension part of the patient ID"
    )
    id_root = models.CharField(max_length=100, help_text="Root OID for the patient ID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["patient_id", "home_member_state", "id_root"]
        verbose_name = "Patient Identifier"
        verbose_name_plural = "Patient Identifiers"

    def __str__(self):
        return f"{self.patient_id} ({self.home_member_state.country_code})"


class PatientData(models.Model):
    """Patient data retrieved from another member state"""

    # Patient identification
    patient_identifier = models.ForeignKey(
        PatientIdentifier, on_delete=models.CASCADE, related_name="patient_data_records"
    )

    # Basic demographics
    given_name = models.CharField(max_length=100, blank=True)
    family_name = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other"), ("U", "Unknown")],
        blank=True,
    )

    # Contact information
    address_line = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Consent and access control
    consent_given = models.BooleanField(default=False)
    consent_timestamp = models.DateTimeField(null=True, blank=True)
    consent_given_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_consents_given",
    )

    # Break glass scenario
    break_glass_access = models.BooleanField(
        default=False, help_text="Emergency access without patient consent"
    )
    break_glass_reason = models.TextField(
        blank=True, help_text="Reason for emergency access"
    )
    break_glass_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="break_glass_accesses",
    )
    break_glass_timestamp = models.DateTimeField(null=True, blank=True)

    # Data access tracking
    accessed_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="accessed_patient_data"
    )
    access_timestamp = models.DateTimeField(auto_now_add=True)

    # Raw data storage
    raw_patient_summary = models.TextField(
        blank=True, help_text="Raw XML patient summary from source NCP"
    )
    raw_eprescription = models.TextField(
        blank=True, help_text="Raw XML ePrescription data from source NCP"
    )

    class Meta:
        verbose_name = "Patient Data"
        verbose_name_plural = "Patient Data Records"
        ordering = ["-access_timestamp"]

    def __str__(self):
        name = f"{self.given_name} {self.family_name}".strip()
        if not name:
            name = str(self.patient_identifier)
        return f"{name} - {self.access_timestamp.strftime('%Y-%m-%d %H:%M')}"

    def get_access_type(self):
        """Return the type of access used"""
        if self.break_glass_access:
            return "Break Glass"
        elif self.consent_given:
            return "With Consent"
        else:
            return "No Access"


class AvailableService(models.Model):
    """Services available from a member state's NCP"""

    SERVICE_TYPES = [
        ("PS", "Patient Summary"),
        ("EP", "ePrescription"),
        ("ED", "eDispensation"),
        ("LR", "Laboratory Results"),
        ("MR", "Medical Reports"),
        ("DI", "Diagnostic Images"),
        ("VR", "Vaccination Records"),
    ]

    member_state = models.ForeignKey(
        MemberState, on_delete=models.CASCADE, related_name="available_services"
    )
    service_type = models.CharField(max_length=2, choices=SERVICE_TYPES)
    service_name = models.CharField(max_length=200)
    service_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["member_state", "service_type"]
        verbose_name = "Available Service"
        verbose_name_plural = "Available Services"

    def __str__(self):
        return f"{self.service_name} ({self.member_state.country_code})"


class PatientServiceRequest(models.Model):
    """Request for patient data from a specific service"""

    REQUEST_STATUS = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    request_id = models.UUIDField(default=uuid.uuid4, unique=True)
    patient_identifier = models.ForeignKey(
        PatientIdentifier, on_delete=models.CASCADE, related_name="service_requests"
    )
    requested_service = models.ForeignKey(
        AvailableService, on_delete=models.CASCADE, related_name="service_requests"
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patient_service_requests"
    )
    request_timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default="PENDING")

    # Consent tracking for this specific request
    consent_required = models.BooleanField(default=True)
    consent_obtained = models.BooleanField(default=False)
    consent_method = models.CharField(
        max_length=50,
        choices=[
            ("EXPLICIT", "Explicit Consent"),
            ("BREAK_GLASS", "Break Glass"),
            ("PRESUMED", "Presumed Consent"),
        ],
        blank=True,
    )

    # Response data
    response_data = models.TextField(
        blank=True, help_text="Raw response data from the service"
    )
    response_timestamp = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Patient Service Request"
        verbose_name_plural = "Patient Service Requests"
        ordering = ["-request_timestamp"]

    def __str__(self):
        return f"{self.requested_service.service_name} for {self.patient_identifier} - {self.status}"


# Column Configuration Models for Dynamic Clinical Tables
class ClinicalSectionConfig(models.Model):
    """Configuration for dynamic column management in clinical tables"""

    SECTION_CHOICES = [
        ("11450-4", "Problem List"),
        ("47519-4", "History of Procedures"),
        ("10160-0", "Medication History"),
        ("30954-2", "Relevant Diagnostic Tests"),
        ("8716-3", "Vital Signs"),
        ("47420-5", "Functional Status"),
        ("29762-2", "Social History"),
        ("10157-6", "Family History"),
        ("48765-2", "Allergies and Adverse Reactions"),
    ]

    COLUMN_TYPES = [
        ("code", "Medical Code"),
        ("text", "Free Text"),
        ("date", "Date/Time"),
        ("numeric", "Numeric Value"),
        ("status", "Status/State"),
        ("reference", "Reference/Link"),
        ("coded_text", "Coded Text"),
        ("composite", "Composite Field"),
        ("custom", "Custom Processing"),
    ]

    section_code = models.CharField(max_length=20, choices=SECTION_CHOICES)
    column_key = models.CharField(
        max_length=100, help_text="Unique key for this column"
    )
    display_label = models.CharField(
        max_length=200, help_text="Label shown in table header"
    )
    column_type = models.CharField(max_length=20, choices=COLUMN_TYPES)

    # Data extraction configuration
    xpath_patterns = models.JSONField(
        default=list, blank=True, help_text="XPath patterns to extract data from XML"
    )
    field_mappings = models.JSONField(
        default=list,
        blank=True,
        help_text="Field name patterns to match in parsed data",
    )

    # Display configuration
    is_enabled = models.BooleanField(default=True)
    is_primary = models.BooleanField(
        default=False, help_text="Primary identifying column"
    )
    display_order = models.IntegerField(default=0, help_text="Column display order")
    css_class = models.CharField(
        max_length=100, blank=True, help_text="CSS class for styling"
    )

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["section_code", "column_key"]
        ordering = ["section_code", "display_order", "display_label"]
        verbose_name = "Clinical Section Column Configuration"
        verbose_name_plural = "Clinical Section Column Configurations"

    def __str__(self):
        return f"{self.get_section_code_display()} - {self.display_label}"


class ColumnPreset(models.Model):
    """Predefined column sets for different clinical scenarios"""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    section_code = models.CharField(
        max_length=20, choices=ClinicalSectionConfig.SECTION_CHOICES
    )

    # Preset configuration
    columns_config = models.JSONField(
        help_text="Complete column configuration for this preset"
    )
    is_default = models.BooleanField(
        default=False, help_text="Default preset for this section"
    )

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["section_code", "name"]
        verbose_name = "Column Configuration Preset"
        verbose_name_plural = "Column Configuration Presets"

    def __str__(self):
        return f"{self.name} ({self.get_section_code_display()})"


class DataExtractionLog(models.Model):
    """Log discovered data endpoints for admin configuration"""

    VALUE_TYPES = [
        ("text", "Text Content"),
        ("code", "Medical Code"),
        ("date", "Date/Time"),
        ("numeric", "Numeric Value"),
        ("boolean", "Boolean"),
        ("reference", "Reference/ID"),
        ("unknown", "Unknown Type"),
    ]

    patient_id = models.CharField(max_length=200, help_text="Patient identifier")
    section_code = models.CharField(max_length=20, help_text="Clinical section code")
    field_name = models.CharField(max_length=200, help_text="Discovered field name")
    xpath_found = models.TextField(help_text="XPath where data was found")
    sample_value = models.TextField(blank=True, help_text="Sample value for reference")
    value_type = models.CharField(max_length=20, choices=VALUE_TYPES, default="unknown")
    frequency_count = models.IntegerField(
        default=1, help_text="How often this endpoint appears"
    )

    # Timestamps
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["section_code", "field_name", "xpath_found"]
        ordering = ["-frequency_count", "section_code", "field_name"]
        verbose_name = "Data Extraction Discovery Log"
        verbose_name_plural = "Data Extraction Discovery Logs"

    def __str__(self):
        return f"{self.section_code}: {self.field_name} ({self.frequency_count}x)"
