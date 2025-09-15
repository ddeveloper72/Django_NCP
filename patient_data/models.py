"""
Patient Data Models
Django models for managing patient data retrieved from other EU member states
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
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


# ==============================================================================
# Session Management Models
# ==============================================================================


class PatientSessionManager(models.Manager):
    """Custom manager for PatientSession with security-focused queries."""

    def get_active_session(self, session_id: str):
        """Get active session by ID, returning None if expired or invalid."""
        try:
            session = self.get(session_id=session_id, is_active=True)
            if session.is_expired():
                session.mark_expired()
                return None
            return session
        except PatientSession.DoesNotExist:
            return None

    def cleanup_expired_sessions(self):
        """Clean up expired sessions and return count."""
        expired_sessions = self.filter(expires_at__lt=timezone.now(), is_active=True)
        count = expired_sessions.count()
        expired_sessions.update(is_active=False, status="expired")
        return count

    def get_user_sessions(self, user, active_only=True):
        """Get all sessions for a user."""
        queryset = self.filter(user=user)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by("-created_at")


class PatientSession(models.Model):
    """
    Secure patient data access session.

    Manages access to patient data with encryption, audit logging,
    and automatic expiration for healthcare data protection.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
        ("suspended", "Suspended"),
    ]

    # Primary identifiers
    session_id = models.CharField(max_length=64, unique=True, primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="patient_sessions"
    )

    # Session lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Encryption metadata
    encryption_key_version = models.PositiveIntegerField(
        help_text="Version of encryption key used"
    )

    # Session state
    is_active = models.BooleanField(default=True)

    # Healthcare context
    country_code = models.CharField(
        max_length=3, help_text="ISO country code for healthcare system"
    )
    search_criteria_hash = models.CharField(
        max_length=64, help_text="Hash of original search criteria"
    )

    # Session data - encrypted
    encrypted_patient_data = models.TextField(
        blank=True, help_text="Encrypted patient identifiers and metadata"
    )
    cda_content_hash = models.CharField(
        max_length=64, blank=True, help_text="Hash of CDA content for integrity"
    )

    # Audit and compliance
    access_count = models.PositiveIntegerField(default=0)
    last_action = models.CharField(
        max_length=255, blank=True, help_text="Last action performed in session"
    )
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)

    # Security flags
    requires_rotation = models.BooleanField(
        default=False, help_text="Session should be rotated on next access"
    )
    security_flags = models.JSONField(
        default=dict, help_text="Security-related flags and metadata"
    )

    objects = PatientSessionManager()

    class Meta:
        db_table = "patient_sessions"
        indexes = [
            models.Index(fields=["user", "country_code"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_active"]),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Override save to set expiration and validate data."""
        if not self.expires_at:
            # Default session expiration - configurable by settings
            from django.conf import settings
            from datetime import timedelta

            session_duration = getattr(
                settings, "PATIENT_SESSION_DURATION", timedelta(hours=8)
            )
            self.expires_at = timezone.now() + session_duration

        # Validate expiration is in the future
        if self.expires_at <= timezone.now():
            from django.core.exceptions import ValidationError

            raise ValidationError("Session expiration must be in the future")

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at or not self.is_active

    def mark_expired(self):
        """Mark session as expired and inactive."""
        self.is_active = False
        self.status = "expired"
        self.save(update_fields=["is_active", "status"])

    def record_access(
        self, action: str = "", client_ip: str = "", user_agent: str = ""
    ):
        """Record session access for audit trail."""
        self.access_count += 1
        self.last_accessed = timezone.now()
        if action:
            self.last_action = action
        if client_ip:
            self.client_ip = client_ip
        if user_agent:
            import hashlib

            self.user_agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()
        self.save(
            update_fields=[
                "access_count",
                "last_accessed",
                "last_action",
                "client_ip",
                "user_agent_hash",
            ]
        )

    def rotate_session(self) -> str:
        """Rotate session ID for security."""
        import secrets

        old_session_id = self.session_id
        self.session_id = secrets.token_urlsafe(32)
        self.requires_rotation = False
        self.save(update_fields=["session_id", "requires_rotation"])

        # Log the rotation
        SessionAuditLog.log_action(
            session=self,
            action="session_rotated",
            metadata={"old_session_id": old_session_id},
        )

        return self.session_id

    def encrypt_patient_data(self, data: dict):
        """Encrypt and store patient data."""
        from patient_data.security.session_security import session_security

        encrypted_data, key_version = session_security.encrypt_patient_data(data)
        self.encrypted_patient_data = encrypted_data.decode("utf-8")
        self.encryption_key_version = key_version
        self.save(update_fields=["encrypted_patient_data", "encryption_key_version"])

    def decrypt_patient_data(self) -> dict:
        """Decrypt and return patient data."""
        if not self.encrypted_patient_data:
            return {}

        from patient_data.security.session_security import session_security

        encrypted_bytes = self.encrypted_patient_data.encode("utf-8")
        return session_security.decrypt_patient_data(
            encrypted_bytes, self.encryption_key_version
        )

    def get_recent_access_count(self, minutes: int = 60) -> int:
        """Get access count in recent time window."""
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return SessionAuditLog.objects.filter(
            session=self, timestamp__gte=cutoff_time
        ).count()

    def __str__(self):
        return f"Session {self.session_id[:8]}... ({self.user.username})"


class PatientDataCache(models.Model):
    """
    Encrypted cache for patient data to reduce API calls.

    Temporarily stores patient data with automatic expiration
    and encryption for performance optimization.
    """

    # Cache identifiers
    cache_key = models.CharField(max_length=255, unique=True)
    session = models.ForeignKey(
        PatientSession, on_delete=models.CASCADE, related_name="cached_data"
    )

    # Cache content
    data_type = models.CharField(
        max_length=50,
        help_text="Type of cached data (patient_summary, cda_document, etc.)",
    )
    encrypted_content = models.TextField(help_text="Encrypted cached data")
    content_hash = models.CharField(
        max_length=64, help_text="Hash for integrity verification"
    )

    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)

    # Encryption metadata
    encryption_key_version = models.PositiveIntegerField()

    class Meta:
        db_table = "patient_data_cache"
        indexes = [
            models.Index(fields=["cache_key"]),
            models.Index(fields=["session", "data_type"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_expired(self):
        """Check if cache entry has expired."""
        return timezone.now() > self.expires_at

    def get_cached_data(self) -> dict:
        """Decrypt and return cached data."""
        if self.is_expired:
            return None

        from patient_data.security.session_security import session_security

        # Update access tracking
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=["access_count", "last_accessed"])

        # Decrypt and return data
        encrypted_bytes = self.encrypted_content.encode("utf-8")
        return session_security.decrypt_patient_data(
            encrypted_bytes, self.encryption_key_version
        )

    def store_data(self, data: dict, ttl_minutes: int = 60):
        """Encrypt and store data in cache."""
        from patient_data.security.session_security import session_security
        import hashlib
        import json
        from datetime import timedelta

        # Encrypt data
        encrypted_data, key_version = session_security.encrypt_patient_data(data)

        # Generate content hash
        content_json = json.dumps(data, sort_keys=True, default=str)
        content_hash = hashlib.sha256(content_json.encode()).hexdigest()

        # Store encrypted data
        self.encrypted_content = encrypted_data.decode("utf-8")
        self.encryption_key_version = key_version
        self.content_hash = content_hash
        self.expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        self.save()

    @classmethod
    def get_or_create_cache(
        cls, session: PatientSession, cache_key: str, data_type: str
    ):
        """Get existing cache entry or create new one."""
        cache_entry, created = cls.objects.get_or_create(
            cache_key=cache_key,
            session=session,
            defaults={
                "data_type": data_type,
                "encryption_key_version": 1,
                "expires_at": timezone.now() + timedelta(hours=1),
            },
        )
        return cache_entry

    def __str__(self):
        return f"Cache {self.cache_key} ({self.data_type})"


class SessionAuditLog(models.Model):
    """
    Comprehensive audit log for patient session activities.

    Records all session-related activities for compliance,
    security monitoring, and forensic analysis.
    """

    # Audit identifiers
    session = models.ForeignKey(
        PatientSession,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    # Action details
    action = models.CharField(max_length=100, help_text="Action performed")
    success = models.BooleanField(
        default=True, help_text="Whether action was successful"
    )
    resource = models.CharField(
        max_length=255, blank=True, help_text="Resource accessed or modified"
    )

    # Request details
    method = models.CharField(max_length=10, blank=True, help_text="HTTP method")
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent_hash = models.CharField(max_length=64, blank=True)

    # Performance metrics
    duration_ms = models.PositiveIntegerField(
        null=True, blank=True, help_text="Request duration in milliseconds"
    )
    response_status = models.PositiveIntegerField(
        null=True, blank=True, help_text="HTTP response status code"
    )
    content_length = models.PositiveIntegerField(
        null=True, blank=True, help_text="Response content length in bytes"
    )

    # Error handling
    error_message = models.TextField(
        blank=True, help_text="Error message if action failed"
    )
    error_code = models.CharField(
        max_length=50, blank=True, help_text="Error code for categorization"
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict, help_text="Additional contextual information"
    )

    class Meta:
        db_table = "session_audit_logs"
        indexes = [
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["success", "timestamp"]),
            models.Index(fields=["client_ip", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    @classmethod
    def log_action(cls, session=None, action="", success=True, **kwargs):
        """Create audit log entry with provided details."""
        return cls.objects.create(
            session=session, action=action, success=success, **kwargs
        )

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        session_id = self.session.session_id[:8] if self.session else "NO-SESSION"
        return f"[{status}] {self.action} - {session_id}... ({self.timestamp})"
