"""
Clinical Document Models
Models for handling clinical documents (CDA and FHIR) from member states
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models import PatientData, MemberState
import uuid
import base64
import json


class ClinicalDocumentRequest(models.Model):
    """Request for clinical document from another member state"""

    CONSENT_CHOICES = [
        ("EXPLICIT", "Explicit Consent"),
        ("BREAK_GLASS", "Break the Glass"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_data = models.ForeignKey(PatientData, on_delete=models.CASCADE)
    document_type = models.CharField(
        max_length=50, help_text="Type of document requested (PS, EP, etc.)"
    )
    requesting_user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True
    )

    consent_method = models.CharField(max_length=20, choices=CONSENT_CHOICES)
    purpose_of_use = models.CharField(max_length=50, default="TREATMENT")
    requesting_organization = models.CharField(max_length=200, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    request_date = models.DateTimeField(auto_now_add=True)
    response_timestamp = models.DateTimeField(blank=True, null=True)

    # NCP Request/Response details
    message_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    correlation_id = models.CharField(max_length=100, blank=True, null=True)

    # Error handling
    error_code = models.CharField(max_length=50, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Clinical Document Request"
        verbose_name_plural = "Clinical Document Requests"
        ordering = ["-request_date"]

    def __str__(self):
        return f"Request {self.message_id} for {self.patient_data.patient_identifier.patient_id}"


class ClinicalDocument(models.Model):
    """Clinical document retrieved from member state (CDA or FHIR)"""

    DOCUMENT_TYPE_CHOICES = [
        ("CDA_L3", "CDA Level 3"),
        ("CDA_L1", "CDA Level 1"),
        ("FHIR_BUNDLE", "FHIR Bundle"),
        ("PDF", "PDF Document"),
        ("OTHER", "Other Format"),
    ]

    DOCUMENT_SERVICE_CHOICES = [
        ("PS", "Patient Summary"),
        ("EP", "ePrescription"),
        ("LR", "Laboratory Report"),
        ("MR", "Medical Report"),
        ("DI", "Diagnostic Imaging"),
        ("VR", "Vaccination Record"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        ClinicalDocumentRequest, on_delete=models.CASCADE, related_name="documents"
    )

    # Document metadata
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    service_type = models.CharField(max_length=10, choices=DOCUMENT_SERVICE_CHOICES)
    document_id = models.CharField(max_length=200)
    document_title = models.CharField(max_length=300)
    creation_date = models.DateTimeField()
    author_institution = models.CharField(max_length=200, blank=True, null=True)

    # Document content
    raw_document = models.TextField(help_text="Base64 encoded or raw document content")
    document_size = models.PositiveIntegerField(help_text="Size in bytes")
    mime_type = models.CharField(max_length=100, default="application/xml")

    # Processing metadata
    received_timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processing_errors = models.TextField(blank=True, null=True)

    # Rendered content
    html_rendering = models.TextField(
        blank=True, null=True, help_text="HTML rendering of the document"
    )
    pdf_content = models.TextField(
        blank=True, null=True, help_text="Base64 encoded PDF if available"
    )

    # Enhanced processing fields
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
        ("es", "Spanish"),
        ("it", "Italian"),
    ]

    target_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default="en",
        help_text="Target language for translation and processing",
    )
    include_sections = models.JSONField(
        default=dict, help_text="Selected sections to include in patient summary"
    )
    patient_summary = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured patient summary data extracted from document",
    )
    html_content = models.TextField(
        blank=True, help_text="Generated HTML patient summary"
    )

    # Enhanced processing status
    PROCESSING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default="pending",
        help_text="Enhanced processing status for patient summary generation",
    )
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)

    # User tracking
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="created_clinical_documents",
        help_text="User who initiated the document processing",
    )

    class Meta:
        verbose_name = "Clinical Document"
        verbose_name_plural = "Clinical Documents"
        ordering = ["-received_timestamp"]

    def __str__(self):
        return f"{self.document_title} ({self.document_type})"

    def get_decoded_content(self):
        """Get decoded document content"""
        try:
            if self.is_base64_encoded():
                return base64.b64decode(self.raw_document).decode("utf-8")
            return self.raw_document
        except Exception:
            return None

    def is_base64_encoded(self):
        """Check if content is base64 encoded"""
        try:
            if isinstance(self.raw_document, str):
                base64.b64decode(self.raw_document, validate=True)
                return True
        except Exception:
            pass
        return False

    def get_file_extension(self):
        """Get appropriate file extension for download"""
        type_extensions = {
            "CDA_L3": "xml",
            "CDA_L1": "xml",
            "FHIR_BUNDLE": "json",
            "PDF": "pdf",
        }
        return type_extensions.get(self.document_type, "txt")

    @property
    def is_processed(self):
        """Check if document has been successfully processed for patient summary"""
        return (
            self.processing_status == "completed" and self.patient_summary is not None
        )

    @property
    def has_pdf(self):
        """Check if PDF content is available"""
        return self.pdf_content is not None and len(self.pdf_content) > 0

    @property
    def processing_duration(self):
        """Calculate processing duration if available"""
        if self.processing_started and self.processing_completed:
            return self.processing_completed - self.processing_started
        return None

    def get_document_format_display(self):
        """Get user-friendly document format display"""
        if self.document_type == "FHIR_BUNDLE":
            return "FHIR Bundle"
        elif self.document_type in ["CDA_L3", "CDA_L1"]:
            return "Clinical Document Architecture"
        else:
            return self.get_document_type_display()


class DocumentTranslation(models.Model):
    """Translation of clinical document terminologies"""

    document = models.ForeignKey(
        ClinicalDocument, on_delete=models.CASCADE, related_name="translations"
    )
    target_language = models.CharField(
        max_length=10, help_text="Target language code (e.g., 'en', 'de', 'fr')"
    )

    # Translation metadata
    translated_content = models.TextField(help_text="Translated document content")
    translation_timestamp = models.DateTimeField(auto_now_add=True)
    translation_status = models.CharField(max_length=20, default="COMPLETED")

    # Translation quality metrics
    concepts_translated = models.PositiveIntegerField(default=0)
    concepts_not_found = models.PositiveIntegerField(default=0)
    translation_confidence = models.FloatField(
        default=0.0, help_text="Average confidence score"
    )

    class Meta:
        verbose_name = "Document Translation"
        verbose_name_plural = "Document Translations"
        unique_together = ["document", "target_language"]
        ordering = ["-translation_timestamp"]

    def __str__(self):
        return (
            f"Translation of {self.document.document_title} to {self.target_language}"
        )
