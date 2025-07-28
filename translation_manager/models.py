"""
Translation Manager Models
Django models for managing medical terminology translations and mappings
"""

from django.db import models
from django.utils import timezone
from patient_data.models import MemberState


class TerminologySystem(models.Model):
    """Medical terminology systems (ICD-10, SNOMED CT, LOINC, etc.)"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the terminology system (e.g., 'ICD-10', 'SNOMED CT')"
    )
    oid = models.CharField(
        max_length=100,
        unique=True,
        help_text="Object identifier for the terminology system"
    )
    description = models.TextField(blank=True)
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Version of the terminology system"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Terminology System"
        verbose_name_plural = "Terminology Systems"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (OID: {self.oid})"


class ConceptMapping(models.Model):
    """Mapping between concepts in different terminology systems"""
    
    # Source concept
    source_system = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name='source_mappings'
    )
    source_code = models.CharField(max_length=100)
    source_display_name = models.CharField(max_length=500)
    
    # Target concept
    target_system = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name='target_mappings'
    )
    target_code = models.CharField(max_length=100)
    target_display_name = models.CharField(max_length=500)
    
    # Mapping metadata
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('EQUIVALENT', 'Equivalent'),
            ('WIDER', 'Wider'),
            ('NARROWER', 'Narrower'),
            ('RELATED', 'Related'),
            ('INEXACT', 'Inexact'),
        ],
        default='EQUIVALENT'
    )
    confidence_score = models.FloatField(
        default=1.0,
        help_text="Confidence score from 0.0 to 1.0"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['source_system', 'source_code', 'target_system', 'target_code']
        verbose_name = "Concept Mapping"
        verbose_name_plural = "Concept Mappings"
        indexes = [
            models.Index(fields=['source_system', 'source_code']),
            models.Index(fields=['target_system', 'target_code']),
        ]
    
    def __str__(self):
        return f"{self.source_code} -> {self.target_code} ({self.mapping_type})"


class LanguageTranslation(models.Model):
    """Language-specific translations for medical terms"""
    
    # Reference to the concept
    terminology_system = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    concept_code = models.CharField(max_length=100)
    
    # Language and translation
    language_code = models.CharField(
        max_length=10,
        help_text="ISO 639 language code (e.g., 'en-GB', 'de-DE', 'fr-FR')"
    )
    translated_name = models.CharField(
        max_length=500,
        help_text="Translated term in the specified language"
    )
    
    # Translation metadata
    is_preferred = models.BooleanField(
        default=False,
        help_text="Whether this is the preferred translation"
    )
    translation_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Source of the translation (e.g., official dictionary, expert)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['terminology_system', 'concept_code', 'language_code', 'translated_name']
        verbose_name = "Language Translation"
        verbose_name_plural = "Language Translations"
        indexes = [
            models.Index(fields=['terminology_system', 'concept_code', 'language_code']),
        ]
    
    def __str__(self):
        return f"{self.concept_code} ({self.language_code}): {self.translated_name}"


class CountrySpecificMapping(models.Model):
    """Country-specific mappings for medical concepts"""
    
    member_state = models.ForeignKey(
        MemberState,
        on_delete=models.CASCADE,
        related_name='concept_mappings'
    )
    
    # Source concept (from member state)
    source_terminology = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name='country_source_mappings'
    )
    source_code = models.CharField(max_length=100)
    source_display_name = models.CharField(max_length=500)
    
    # Target concept (Irish/English equivalent)
    target_terminology = models.ForeignKey(
        TerminologySystem,
        on_delete=models.CASCADE,
        related_name='country_target_mappings'
    )
    target_code = models.CharField(max_length=100)
    target_display_name = models.CharField(max_length=500)
    
    # Mapping quality and usage
    mapping_quality = models.CharField(
        max_length=20,
        choices=[
            ('HIGH', 'High Quality'),
            ('MEDIUM', 'Medium Quality'),
            ('LOW', 'Low Quality'),
            ('MANUAL', 'Requires Manual Review'),
        ],
        default='MEDIUM'
    )
    usage_frequency = models.IntegerField(
        default=0,
        help_text="How often this mapping has been used"
    )
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['member_state', 'source_terminology', 'source_code', 'target_terminology', 'target_code']
        verbose_name = "Country-Specific Mapping"
        verbose_name_plural = "Country-Specific Mappings"
    
    def __str__(self):
        return f"{self.member_state.country_code}: {self.source_code} -> {self.target_code}"


class TranslationService(models.Model):
    """Configuration for translation services"""
    
    SERVICE_TYPES = [
        ('TERMINOLOGY', 'Medical Terminology Translation'),
        ('TEXT', 'Free Text Translation'),
        ('HYBRID', 'Hybrid (Terminology + Text)'),
    ]
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES
    )
    endpoint_url = models.URLField(
        help_text="URL of the translation service endpoint"
    )
    api_key = models.CharField(
        max_length=200,
        blank=True,
        help_text="API key for authentication (if required)"
    )
    supported_languages = models.TextField(
        help_text="Comma-separated list of supported language codes"
    )
    
    # Service configuration
    timeout_seconds = models.IntegerField(default=30)
    max_retries = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    
    # Usage statistics
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Translation Service"
        verbose_name_plural = "Translation Services"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.service_type})"
    
    def get_success_rate(self):
        """Calculate success rate as percentage"""
        if self.total_requests == 0:
            return 0
        return (self.successful_requests / self.total_requests) * 100


class TranslationCache(models.Model):
    """Cache for translated content to improve performance"""
    
    # Source content
    source_language = models.CharField(max_length=10)
    source_text = models.TextField()
    source_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of source text for quick lookup"
    )
    
    # Target content
    target_language = models.CharField(max_length=10)
    translated_text = models.TextField()
    
    # Translation metadata
    translation_service = models.ForeignKey(
        TranslationService,
        on_delete=models.CASCADE,
        related_name='cached_translations'
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score from translation service"
    )
    
    # Cache management
    usage_count = models.IntegerField(default=1)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration time for cache entry"
    )
    
    class Meta:
        unique_together = ['source_hash', 'source_language', 'target_language']
        verbose_name = "Translation Cache"
        verbose_name_plural = "Translation Cache Entries"
        indexes = [
            models.Index(fields=['source_hash', 'source_language', 'target_language']),
            models.Index(fields=['last_accessed']),
        ]
    
    def __str__(self):
        preview = self.source_text[:50] + "..." if len(self.source_text) > 50 else self.source_text
        return f"{self.source_language} -> {self.target_language}: {preview}"
    
    def is_expired(self):
        """Check if cache entry has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
