"""
Django models for NCP Gateway - Core NCP functionality
Based on analysis of DomiSMP and OpenNCP implementations
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Country(models.Model):
    """EU Member State countries participating in eHealth network"""

    code = models.CharField(
        max_length=3, unique=True, help_text="ISO 3166-1 alpha-2 country code"
    )
    name = models.CharField(max_length=100)
    ncp_endpoint = models.URLField(help_text="National Contact Point endpoint URL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Organization(models.Model):
    """Healthcare organizations (hospitals, clinics, pharmacies)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    identifier = models.CharField(max_length=100, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    organization_type = models.CharField(
        max_length=50,
        choices=[
            ("hospital", "Hospital"),
            ("clinic", "Clinic"),
            ("pharmacy", "Pharmacy"),
            ("laboratory", "Laboratory"),
            ("radiology", "Radiology Center"),
            ("primary_care", "Primary Care"),
        ],
    )
    contact_email = models.EmailField()
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.country.code})"


class Patient(models.Model):
    """Patient records for cross-border healthcare"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Patient identification
    national_id = models.CharField(
        max_length=50, help_text="National patient identifier"
    )
    european_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="European patient identifier",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(
        max_length=10,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
    )

    # Administrative
    country_of_origin = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="patients"
    )
    insurance_number = models.CharField(max_length=100, null=True, blank=True)

    # Contact information
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    # Consent and privacy
    cross_border_consent = models.BooleanField(
        default=False, help_text="Consent for cross-border data sharing"
    )
    consent_date = models.DateTimeField(null=True, blank=True)
    data_sharing_restrictions = models.TextField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["national_id", "country_of_origin"]),
            models.Index(fields=["european_id"]),
            models.Index(fields=["last_name", "first_name", "birth_date"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.national_id})"


class HealthcareProfessional(models.Model):
    """Healthcare professionals authorized for cross-border access"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    professional_id = models.CharField(max_length=100, unique=True)
    license_number = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    speciality = models.CharField(max_length=100)

    # Professional status
    is_authorized_cross_border = models.BooleanField(default=False)
    authorization_level = models.CharField(
        max_length=20,
        choices=[
            ("read_only", "Read Only"),
            ("full_access", "Full Access"),
            ("emergency_only", "Emergency Only"),
        ],
        default="read_only",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.organization.name}"


class CrossBorderRequest(models.Model):
    """Cross-border patient data requests between NCPs"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Request details
    requesting_country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="outgoing_requests"
    )
    target_country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="incoming_requests"
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    requesting_professional = models.ForeignKey(
        HealthcareProfessional, on_delete=models.CASCADE
    )

    # Request type
    service_type = models.CharField(
        max_length=50,
        choices=[
            ("patient_summary", "Patient Summary"),
            ("eprescription", "ePrescription"),
            ("edispensation", "eDispensation"),
            ("laboratory_results", "Laboratory Results"),
            ("hospital_discharge", "Hospital Discharge Report"),
            ("medical_imaging", "Medical Imaging"),
        ],
    )

    # Request status
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("denied", "Denied"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("expired", "Expired"),
        ],
        default="pending",
    )

    # Purpose and justification
    purpose = models.CharField(
        max_length=50,
        choices=[
            ("treatment", "Treatment"),
            ("emergency", "Emergency Care"),
            ("prescription", "Prescription"),
            ("continuation_care", "Continuation of Care"),
        ],
    )
    justification = models.TextField()

    # Technical details
    request_data = models.JSONField(help_text="FHIR request payload")
    response_data = models.JSONField(
        null=True, blank=True, help_text="FHIR response payload"
    )
    error_message = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="Request expiration time")

    # Audit trail
    source_ip = models.GenericIPAddressField()
    user_agent = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["patient", "service_type"]),
            models.Index(fields=["requesting_country", "target_country"]),
        ]

    def __str__(self):
        return f"{self.service_type} - {self.patient} ({self.status})"


class AuditLog(models.Model):
    """Comprehensive audit logging for GDPR compliance"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event details
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("patient_lookup", "Patient Lookup"),
            ("data_access", "Data Access"),
            ("data_share", "Data Sharing"),
            ("consent_change", "Consent Change"),
            ("login", "User Login"),
            ("logout", "User Logout"),
            ("system_error", "System Error"),
            ("config_change", "Configuration Change"),
        ],
    )

    # Actors
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    professional = models.ForeignKey(
        HealthcareProfessional, on_delete=models.SET_NULL, null=True, blank=True
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Event data
    description = models.TextField()
    data_accessed = models.TextField(
        null=True, blank=True, help_text="Description of data accessed"
    )
    legal_basis = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Legal basis for data processing",
    )

    # Technical details
    source_ip = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)

    # Cross-border context
    cross_border_request = models.ForeignKey(
        CrossBorderRequest, on_delete=models.SET_NULL, null=True, blank=True
    )
    source_country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        related_name="audit_logs_source",
        null=True,
        blank=True,
    )
    target_country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        related_name="audit_logs_target",
        null=True,
        blank=True,
    )

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(
        max_length=20,
        choices=[
            ("info", "Information"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        default="info",
    )

    class Meta:
        indexes = [
            models.Index(fields=["timestamp", "event_type"]),
            models.Index(fields=["patient", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["source_ip", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.timestamp} - {self.user or 'System'}"
