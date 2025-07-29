"""
Enhanced models for Master Value Set Catalogue (MVC) integration
Extends existing translation models to support EU CTS value sets
"""

import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from translation_manager.models import TerminologySystem


class ValueSetCatalogue(models.Model):
    """
    Master Value Set Catalogue entry
    Represents a value set from the EU Central Terminology Server
    """

    # Value Set Identification
    oid = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(r"^[\d\.]+$", "OID must contain only digits and dots")
        ],
        help_text="Object Identifier (OID) for the value set",
    )

    name = models.CharField(
        max_length=500, help_text="Human-readable name of the value set"
    )

    display_name = models.CharField(
        max_length=500, blank=True, help_text="Display name for UI purposes"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of the value set purpose and content",
    )

    # Versioning and Status
    version = models.CharField(
        max_length=50, default="1.0", help_text="Version number of the value set"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("retired", "Retired"),
            ("unknown", "Unknown"),
        ],
        default="active",
    )

    effective_date = models.DateTimeField(
        null=True, blank=True, help_text="Date when this value set becomes effective"
    )

    expiration_date = models.DateTimeField(
        null=True, blank=True, help_text="Date when this value set expires"
    )

    # Binding Information
    binding_strength = models.CharField(
        max_length=20,
        choices=[
            ("required", "Required"),
            ("extensible", "Extensible"),
            ("preferred", "Preferred"),
            ("example", "Example"),
        ],
        default="required",
        help_text="Strength of binding for this value set",
    )

    # Purpose and Context
    purpose = models.TextField(
        blank=True, help_text="Purpose of this value set in clinical context"
    )

    use_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Clinical contexts where this value set applies",
    )

    # Technical Information
    immutable = models.BooleanField(
        default=False, help_text="Whether this value set definition is immutable"
    )

    experimental = models.BooleanField(
        default=False, help_text="Whether this value set is experimental"
    )

    # Source Information
    publisher = models.CharField(
        max_length=255,
        blank=True,
        help_text="Organization responsible for this value set",
    )

    contact_info = models.JSONField(
        default=dict, blank=True, help_text="Contact information for the publisher"
    )

    copyright = models.TextField(
        blank=True, help_text="Copyright and usage restrictions"
    )

    # CTS Integration
    terminology_system = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name="value_sets",
        help_text="Associated terminology system",
    )

    cts_url = models.URLField(blank=True, help_text="URL to this value set in CTS")

    last_updated_from_cts = models.DateTimeField(
        null=True, blank=True, help_text="Last time this was synchronized with CTS"
    )

    # Local Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_local_only = models.BooleanField(
        default=False, help_text="Whether this value set exists only locally"
    )

    sync_enabled = models.BooleanField(
        default=True, help_text="Whether to sync this value set with CTS"
    )

    class Meta:
        verbose_name = "Value Set Catalogue Entry"
        verbose_name_plural = "Value Set Catalogue Entries"
        indexes = [
            models.Index(fields=["oid"]),
            models.Index(fields=["status", "effective_date"]),
            models.Index(fields=["terminology_system", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.oid})"

    @property
    def is_active(self):
        """Check if value set is currently active"""
        if self.status != "active":
            return False

        now = timezone.now()

        if self.effective_date and self.effective_date > now:
            return False

        if self.expiration_date and self.expiration_date <= now:
            return False

        return True

    @property
    def concept_count(self):
        """Get number of concepts in this value set"""
        return self.concepts.count()


class ValueSetConcept(models.Model):
    """
    Individual concept within a value set
    """

    value_set = models.ForeignKey(
        ValueSetCatalogue, on_delete=models.CASCADE, related_name="concepts"
    )

    # Concept Identification
    code = models.CharField(max_length=255, help_text="Code for this concept")

    display = models.CharField(max_length=500, help_text="Human-readable display text")

    definition = models.TextField(
        blank=True, help_text="Formal definition of this concept"
    )

    # System Information
    code_system = models.CharField(
        max_length=255, help_text="URI of the code system this concept comes from"
    )

    code_system_version = models.CharField(
        max_length=50, blank=True, help_text="Version of the code system"
    )

    # Concept Properties
    properties = models.JSONField(
        default=dict, blank=True, help_text="Additional properties for this concept"
    )

    # Status and Versioning
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("deprecated", "Deprecated"),
        ],
        default="active",
    )

    effective_date = models.DateTimeField(null=True, blank=True)

    # Ordering and Hierarchy
    sort_order = models.IntegerField(
        default=0, help_text="Order for displaying this concept"
    )

    parent_concept = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_concepts",
        help_text="Parent concept for hierarchical value sets",
    )

    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Value Set Concept"
        verbose_name_plural = "Value Set Concepts"
        unique_together = [["value_set", "code", "code_system"]]
        indexes = [
            models.Index(fields=["value_set", "code"]),
            models.Index(fields=["code_system", "code"]),
            models.Index(fields=["status", "effective_date"]),
        ]

    def __str__(self):
        return f"{self.code}: {self.display}"


class ValueSetTranslation(models.Model):
    """
    Translations for value set names and descriptions
    """

    value_set = models.ForeignKey(
        ValueSetCatalogue, on_delete=models.CASCADE, related_name="translations"
    )

    language_code = models.CharField(
        max_length=10, help_text="ISO language code (e.g., 'en', 'fr', 'de')"
    )

    translated_name = models.CharField(
        max_length=500, help_text="Translated name of the value set"
    )

    translated_description = models.TextField(
        blank=True, help_text="Translated description"
    )

    # Quality and Source
    translation_quality = models.CharField(
        max_length=20,
        choices=[
            ("official", "Official Translation"),
            ("professional", "Professional Translation"),
            ("community", "Community Translation"),
            ("machine", "Machine Translation"),
        ],
        default="official",
    )

    source = models.CharField(
        max_length=100, default="CTS", help_text="Source of this translation"
    )

    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Value Set Translation"
        verbose_name_plural = "Value Set Translations"
        unique_together = [["value_set", "language_code"]]

    def __str__(self):
        return f"{self.value_set.name} ({self.language_code}): {self.translated_name}"


class ConceptTranslation(models.Model):
    """
    Translations for individual concepts within value sets
    """

    concept = models.ForeignKey(
        ValueSetConcept, on_delete=models.CASCADE, related_name="translations"
    )

    language_code = models.CharField(max_length=10, help_text="ISO language code")

    translated_display = models.CharField(
        max_length=500, help_text="Translated display text for the concept"
    )

    translated_definition = models.TextField(
        blank=True, help_text="Translated definition"
    )

    # Quality and Source
    translation_quality = models.CharField(
        max_length=20,
        choices=[
            ("official", "Official Translation"),
            ("professional", "Professional Translation"),
            ("community", "Community Translation"),
            ("machine", "Machine Translation"),
        ],
        default="official",
    )

    source = models.CharField(
        max_length=100, default="CTS", help_text="Source of this translation"
    )

    # Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Concept Translation"
        verbose_name_plural = "Concept Translations"
        unique_together = [["concept", "language_code"]]

    def __str__(self):
        return f"{self.concept.code} ({self.language_code}): {self.translated_display}"


class MVCSyncLog(models.Model):
    """
    Log of MVC synchronization activities
    """

    sync_type = models.CharField(
        max_length=20,
        choices=[
            ("full_sync", "Full Synchronization"),
            ("incremental", "Incremental Sync"),
            ("single_vs", "Single Value Set"),
            ("error_recovery", "Error Recovery"),
        ],
    )

    source = models.CharField(
        max_length=50,
        choices=[
            ("cts_training", "CTS Training"),
            ("cts_acceptance", "CTS Acceptance"),
            ("cts_production", "CTS Production"),
            ("local_file", "Local File Import"),
            ("manual", "Manual Entry"),
        ],
    )

    # Sync Details
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    # Results
    value_sets_processed = models.IntegerField(default=0)
    value_sets_created = models.IntegerField(default=0)
    value_sets_updated = models.IntegerField(default=0)
    concepts_processed = models.IntegerField(default=0)
    translations_processed = models.IntegerField(default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("partial", "Partially Completed"),
        ],
    )

    error_message = models.TextField(blank=True)
    sync_details = models.JSONField(default=dict, blank=True)

    # Management
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "MVC Sync Log"
        verbose_name_plural = "MVC Sync Logs"
        indexes = [
            models.Index(fields=["started_at", "status"]),
            models.Index(fields=["source", "sync_type"]),
        ]

    def __str__(self):
        return f"{self.sync_type} from {self.source} at {self.started_at}"

    @property
    def duration(self):
        """Get sync duration if completed"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class ImportTask(models.Model):
    """Track import task progress"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, help_text="User who started the import"
    )
    task_type = models.CharField(max_length=50, default="mvc_import")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress_percentage = models.IntegerField(default=0)
    progress_message = models.TextField(blank=True)
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)

    # Results
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_details = models.JSONField(default=list, blank=True)

    # File info
    filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Import Task"
        verbose_name_plural = "Import Tasks"

    def __str__(self):
        return f"{self.task_type} - {self.status} ({self.progress_percentage}%)"

    @property
    def is_finished(self):
        return self.status in ["completed", "failed"]

    def update_progress(self, processed_items=None, message=None):
        """Update task progress"""
        if processed_items is not None:
            self.processed_items = processed_items
            if self.total_items > 0:
                self.progress_percentage = min(
                    100, int((processed_items / self.total_items) * 100)
                )

        if message:
            self.progress_message = message

        self.save()
