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
