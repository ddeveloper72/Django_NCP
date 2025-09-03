"""
Translation Manager Admin Interface
Django admin configuration for translation and terminology management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    TerminologySystem,
    ConceptMapping,
    LanguageTranslation,
    CountrySpecificMapping,
    TranslationService,
    TranslationCache,
)


@admin.register(TerminologySystem)
class TerminologySystemAdmin(admin.ModelAdmin):
    list_display = ["name", "oid", "version", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "oid", "description"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("System Information", {"fields": ("name", "oid", "version")}),
        ("Description", {"fields": ("description",)}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ConceptMapping)
class ConceptMappingAdmin(admin.ModelAdmin):
    list_display = [
        "source_code",
        "source_system",
        "target_code",
        "target_system",
        "mapping_type",
        "confidence_score",
        "is_active",
    ]
    list_filter = [
        "mapping_type",
        "is_active",
        "source_system",
        "target_system",
        "confidence_score",
    ]
    search_fields = [
        "source_code",
        "source_display_name",
        "target_code",
        "target_display_name",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Source Concept",
            {"fields": ("source_system", "source_code", "source_display_name")},
        ),
        (
            "Target Concept",
            {"fields": ("target_system", "target_code", "target_display_name")},
        ),
        (
            "Mapping Details",
            {"fields": ("mapping_type", "confidence_score", "is_active")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_confidence_display(self, obj):
        confidence = obj.confidence_score
        if confidence >= 0.9:
            color = "green"
        elif confidence >= 0.7:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            confidence,
        )

    get_confidence_display.short_description = "Confidence"


@admin.register(LanguageTranslation)
class LanguageTranslationAdmin(admin.ModelAdmin):
    list_display = [
        "concept_code",
        "terminology_system",
        "language_code",
        "translated_name",
        "is_preferred",
        "is_active",
    ]
    list_filter = ["language_code", "is_preferred", "is_active", "terminology_system"]
    search_fields = ["concept_code", "translated_name", "translation_source"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Concept Reference", {"fields": ("terminology_system", "concept_code")}),
        (
            "Translation",
            {"fields": ("language_code", "translated_name", "is_preferred")},
        ),
        ("Metadata", {"fields": ("translation_source", "is_active")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(CountrySpecificMapping)
class CountrySpecificMappingAdmin(admin.ModelAdmin):
    list_display = [
        "member_state",
        "source_code",
        "source_terminology",
        "target_code",
        "target_terminology",
        "mapping_quality",
        "usage_frequency",
    ]
    list_filter = [
        "member_state",
        "mapping_quality",
        "is_active",
        "source_terminology",
        "target_terminology",
    ]
    search_fields = [
        "source_code",
        "source_display_name",
        "target_code",
        "target_display_name",
    ]
    readonly_fields = ["usage_frequency", "last_used", "created_at", "updated_at"]

    fieldsets = (
        ("Country Information", {"fields": ("member_state",)}),
        (
            "Source Concept",
            {"fields": ("source_terminology", "source_code", "source_display_name")},
        ),
        (
            "Target Concept",
            {"fields": ("target_terminology", "target_code", "target_display_name")},
        ),
        ("Mapping Quality", {"fields": ("mapping_quality", "is_active")}),
        (
            "Usage Statistics",
            {"fields": ("usage_frequency", "last_used"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_quality_display(self, obj):
        quality_colors = {
            "HIGH": "green",
            "MEDIUM": "orange",
            "LOW": "red",
            "MANUAL": "blue",
        }
        color = quality_colors.get(obj.mapping_quality, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_mapping_quality_display(),
        )

    get_quality_display.short_description = "Quality"


@admin.register(TranslationService)
class TranslationServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "service_type",
        "get_success_rate_display",
        "total_requests",
        "is_active",
        "last_used",
    ]
    list_filter = ["service_type", "is_active", "last_used"]
    search_fields = ["name", "endpoint_url", "supported_languages"]
    readonly_fields = [
        "total_requests",
        "successful_requests",
        "last_used",
        "created_at",
        "updated_at",
        "get_success_rate",
    ]

    fieldsets = (
        ("Service Information", {"fields": ("name", "service_type", "endpoint_url")}),
        (
            "Configuration",
            {
                "fields": (
                    "api_key",
                    "supported_languages",
                    "timeout_seconds",
                    "max_retries",
                    "is_active",
                )
            },
        ),
        (
            "Usage Statistics",
            {
                "fields": (
                    "total_requests",
                    "successful_requests",
                    "get_success_rate",
                    "last_used",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_success_rate_display(self, obj):
        rate = obj.get_success_rate()
        if rate >= 95:
            color = "green"
        elif rate >= 80:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, rate
        )

    get_success_rate_display.short_description = "Success Rate"


@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    list_display = [
        "get_source_preview",
        "source_language",
        "target_language",
        "translation_service",
        "usage_count",
        "last_accessed",
        "is_expired",
    ]
    list_filter = [
        "source_language",
        "target_language",
        "translation_service",
        "last_accessed",
        "expires_at",
    ]
    search_fields = ["source_text", "translated_text", "source_hash"]
    readonly_fields = ["source_hash", "usage_count", "last_accessed", "created_at"]

    fieldsets = (
        (
            "Source Content",
            {"fields": ("source_language", "source_text", "source_hash")},
        ),
        (
            "Translation",
            {
                "fields": (
                    "target_language",
                    "translated_text",
                    "translation_service",
                    "confidence_score",
                )
            },
        ),
        (
            "Cache Management",
            {"fields": ("usage_count", "last_accessed", "expires_at")},
        ),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def get_source_preview(self, obj):
        preview = (
            obj.source_text[:100] + "..."
            if len(obj.source_text) > 100
            else obj.source_text
        )
        return preview

    get_source_preview.short_description = "Source Text Preview"

    actions = ["clear_expired_cache", "reset_usage_count"]

    def clear_expired_cache(self, request, queryset):
        from django.utils import timezone

        expired_entries = queryset.filter(expires_at__lte=timezone.now())
        count = expired_entries.count()
        expired_entries.delete()
        self.message_user(request, f"{count} expired cache entries cleared.")

    clear_expired_cache.short_description = "Clear expired cache entries"

    def reset_usage_count(self, request, queryset):
        updated = queryset.update(usage_count=0)
        self.message_user(request, f"{updated} usage counts reset.")

    reset_usage_count.short_description = "Reset usage count to 0"
