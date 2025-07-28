"""
SMP Client Admin Interface
Django admin configuration for SMP service metadata management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    Domain,
    ParticipantIdentifierScheme,
    DocumentTypeScheme,
    Participant,
    DocumentType,
    ServiceGroup,
    ServiceMetadata,
    ProcessIdentifier,
    Endpoint,
    SMPQuery,
    SMPConfiguration,
    SMPDocument,
    DocumentTemplate,
    SigningCertificate,
)
from .admin_forms import SigningCertificateAdminForm


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = [
        "domain_name",
        "domain_code",
        "sml_subdomain",
        "is_test_domain",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_test_domain", "is_active", "created_at"]
    search_fields = ["domain_name", "domain_code", "sml_subdomain"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Domain Information",
            {"fields": ("domain_code", "domain_name", "sml_subdomain")},
        ),
        ("SMP Configuration", {"fields": ("smp_url", "is_test_domain", "is_active")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParticipantIdentifierScheme)
class ParticipantIdentifierSchemeAdmin(admin.ModelAdmin):
    list_display = ["scheme_name", "scheme_id", "example_value", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["scheme_name", "scheme_id", "description"]
    readonly_fields = ["created_at"]


@admin.register(DocumentTypeScheme)
class DocumentTypeSchemeAdmin(admin.ModelAdmin):
    list_display = ["scheme_name", "scheme_id", "category", "is_active"]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["scheme_name", "scheme_id", "description"]
    readonly_fields = ["created_at"]


class ServiceGroupInline(admin.StackedInline):
    model = ServiceGroup
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        "participant_name",
        "participant_identifier",
        "participant_scheme",
        "country_code",
        "domain",
        "is_active",
    ]
    list_filter = [
        "participant_scheme",
        "domain",
        "country_code",
        "is_active",
        "created_at",
    ]
    search_fields = ["participant_name", "participant_identifier", "contact_email"]
    readonly_fields = ["created_at", "last_updated"]
    inlines = [ServiceGroupInline]

    fieldsets = (
        (
            "Participant Identity",
            {"fields": ("participant_identifier", "participant_scheme", "domain")},
        ),
        (
            "Participant Details",
            {"fields": ("participant_name", "country_code", "organization_type")},
        ),
        ("Contact Information", {"fields": ("contact_email", "contact_phone")}),
        (
            "Certificate Details",
            {
                "fields": ("certificate_subject_dn", "certificate_serial"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status & Timestamps",
            {
                "fields": ("is_active", "created_at", "last_updated"),
                "classes": ("collapse",),
            },
        ),
    )

    def full_participant_id(self, obj):
        return obj.full_participant_id

    full_participant_id.short_description = "Full Participant ID"


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = [
        "document_name",
        "document_type_identifier",
        "document_scheme",
        "document_version",
        "is_active",
    ]
    list_filter = ["document_scheme", "is_active", "created_at"]
    search_fields = ["document_name", "document_type_identifier", "profile_id"]
    readonly_fields = ["created_at"]

    fieldsets = (
        (
            "Document Type Identity",
            {"fields": ("document_type_identifier", "document_scheme")},
        ),
        (
            "Document Details",
            {"fields": ("document_name", "document_version", "description")},
        ),
        (
            "eHealth Specific",
            {"fields": ("profile_id", "customization_id"), "classes": ("collapse",)},
        ),
        ("Status", {"fields": ("is_active", "created_at")}),
    )


class ServiceMetadataInline(admin.TabularInline):
    model = ServiceMetadata
    extra = 0
    readonly_fields = ["created_at", "updated_at"]


@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = ["participant", "service_count", "created_at", "updated_at"]
    search_fields = [
        "participant__participant_name",
        "participant__participant_identifier",
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ServiceMetadataInline]

    def service_count(self, obj):
        return obj.services.count()

    service_count.short_description = "Services"


class EndpointInline(admin.TabularInline):
    model = Endpoint
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fields = ["process", "endpoint_url", "transport_profile", "is_active"]


@admin.register(ServiceMetadata)
class ServiceMetadataAdmin(admin.ModelAdmin):
    list_display = [
        "service_group",
        "document_type",
        "endpoint_count",
        "is_active",
        "updated_at",
    ]
    list_filter = ["document_type__document_scheme", "is_active", "created_at"]
    search_fields = [
        "service_group__participant__participant_name",
        "document_type__document_name",
    ]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [EndpointInline]

    def endpoint_count(self, obj):
        return obj.endpoints.count()

    endpoint_count.short_description = "Endpoints"


@admin.register(ProcessIdentifier)
class ProcessIdentifierAdmin(admin.ModelAdmin):
    list_display = [
        "process_name",
        "process_identifier",
        "process_scheme",
        "is_ehealth_process",
    ]
    list_filter = ["process_scheme", "is_ehealth_process"]
    search_fields = ["process_name", "process_identifier", "description"]


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = [
        "service_metadata",
        "process",
        "endpoint_url",
        "transport_profile",
        "is_valid_status",
        "is_active",
    ]
    list_filter = [
        "transport_profile",
        "is_active",
        "service_metadata__document_type__document_scheme",
    ]
    search_fields = [
        "endpoint_url",
        "service_description",
        "service_metadata__service_group__participant__participant_name",
    ]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Endpoint Identity", {"fields": ("service_metadata", "process")}),
        ("Connection Details", {"fields": ("endpoint_url", "transport_profile")}),
        (
            "Security",
            {
                "fields": (
                    "requires_business_level_signature",
                    "minimum_authentication_level",
                    "certificate",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Service Dates",
            {"fields": ("service_activation_date", "service_expiration_date")},
        ),
        (
            "Technical Information",
            {
                "fields": ("technical_contact_url", "service_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "Status & Timestamps",
            {
                "fields": ("is_active", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def is_valid_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Invalid</span>')

    is_valid_status.short_description = "Status"


@admin.register(SMPQuery)
class SMPQueryAdmin(admin.ModelAdmin):
    list_display = [
        "timestamp",
        "query_type",
        "participant_id",
        "participant_scheme",
        "response_status",
        "response_time_ms",
    ]
    list_filter = ["query_type", "response_status", "timestamp"]
    search_fields = ["participant_id", "participant_scheme", "source_ip"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"

    fieldsets = (
        (
            "Query Details",
            {
                "fields": (
                    "timestamp",
                    "query_type",
                    "participant_id",
                    "participant_scheme",
                    "document_type_id",
                    "document_scheme",
                )
            },
        ),
        (
            "Request Context",
            {"fields": ("source_ip", "user_agent"), "classes": ("collapse",)},
        ),
        (
            "Response",
            {"fields": ("response_status", "response_time_ms", "error_message")},
        ),
    )

    def has_add_permission(self, request):
        # SMP queries are logged automatically
        return False


@admin.register(SMPConfiguration)
class SMPConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        "european_smp_url",
        "sync_enabled",
        "local_smp_enabled",
        "last_sync",
    ]
    readonly_fields = ["last_sync"]

    fieldsets = (
        (
            "European SMP Integration",
            {
                "fields": (
                    "european_smp_url",
                    "sync_enabled",
                    "sync_interval_hours",
                    "last_sync",
                )
            },
        ),
        ("Local SMP Settings", {"fields": ("local_smp_enabled", "local_domain_code")}),
        (
            "API Configuration",
            {"fields": ("api_enabled", "api_key"), "classes": ("collapse",)},
        ),
        (
            "Default Certificate",
            {"fields": ("default_certificate",), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not SMPConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of configuration
        return False


@admin.register(SMPDocument)
class SMPDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "document_name",
        "document_type",
        "status",
        "participant",
        "has_signed_file",
        "smp_server_url",
        "created_by",
        "created_at",
    ]
    list_filter = ["document_type", "status", "created_at", "smp_upload_timestamp"]
    search_fields = [
        "document_name",
        "document_description",
        "participant__participant_identifier",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "signature_timestamp",
        "smp_upload_timestamp",
    ]
    raw_id_fields = [
        "participant",
        "service_group",
        "service_metadata",
        "endpoint",
        "created_by",
    ]

    fieldsets = (
        (
            "Document Information",
            {
                "fields": (
                    "document_name",
                    "document_type",
                    "document_description",
                    "status",
                )
            },
        ),
        (
            "Content",
            {
                "fields": ("xml_content", "original_file", "signed_file"),
                "classes": ("collapse",),
            },
        ),
        (
            "Relationships",
            {
                "fields": (
                    "participant",
                    "service_group",
                    "service_metadata",
                    "endpoint",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Digital Signature",
            {
                "fields": (
                    "signature_data",
                    "certificate_fingerprint",
                    "signature_timestamp",
                    "signer_info",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "SMP Upload",
            {
                "fields": ("smp_server_url", "smp_upload_timestamp", "smp_response"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_by", "created_at", "updated_at", "is_active"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_signed_file(self, obj):
        return bool(obj.signed_file)

    has_signed_file.boolean = True
    has_signed_file.short_description = "Signed"

    actions = ["generate_xml", "mark_as_signed", "mark_as_uploaded"]

    def generate_xml(self, request, queryset):
        count = 0
        for document in queryset:
            if document.generate_xml_content():
                document.xml_content = document.generate_xml_content()
                document.status = "generated"
                document.save()
                count += 1
        self.message_user(request, f"Generated XML for {count} documents.")

    generate_xml.short_description = "Generate XML content"

    def mark_as_signed(self, request, queryset):
        count = queryset.update(status="signed", signature_timestamp=timezone.now())
        self.message_user(request, f"Marked {count} documents as signed.")

    mark_as_signed.short_description = "Mark as signed"

    def mark_as_uploaded(self, request, queryset):
        count = queryset.update(status="uploaded", smp_upload_timestamp=timezone.now())
        self.message_user(request, f"Marked {count} documents as uploaded.")

    mark_as_uploaded.short_description = "Mark as uploaded"


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "template_name",
        "document_type",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = ["document_type", "is_default", "is_active", "created_at"]
    search_fields = ["template_name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Template Information",
            {"fields": ("template_name", "document_type", "description")},
        ),
        ("Template Content", {"fields": ("xml_template", "default_values")}),
        ("Configuration", {"fields": ("is_default", "is_active")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        # Ensure only one default template per document type
        if obj.is_default:
            DocumentTemplate.objects.filter(
                document_type=obj.document_type, is_default=True
            ).exclude(id=obj.id).update(is_default=False)
        super().save_model(request, obj, form, change)


@admin.register(SigningCertificate)
class SigningCertificateAdmin(admin.ModelAdmin):
    form = SigningCertificateAdminForm
    
    list_display = [
        "certificate_name",
        "certificate_type", 
        "subject_short",
        "valid_status",
        "validation_status",
        "is_default",
        "is_active",
        "valid_to",
        "created_at",
    ]
    list_filter = [
        "certificate_type",
        "validation_status",
        "is_default",
        "is_active", 
        "valid_from",
        "valid_to",
    ]
    search_fields = ["certificate_name", "subject", "issuer", "serial_number"]
    readonly_fields = [
        "id", 
        "subject", 
        "issuer", 
        "serial_number", 
        "fingerprint",
        "signature_algorithm",
        "valid_from", 
        "valid_to",
        "validation_status",
        "validation_warnings",
        "created_at", 
        "updated_at"
    ]

    fieldsets = (
        (
            "Certificate Upload",
            {
                "fields": ("certificate_name", "certificate_type", "certificate_file", "private_key_file"),
                "description": "Upload certificate and private key files. Certificate information will be automatically extracted and validated."
            },
        ),
        (
            "Certificate Information", 
            {
                "fields": ("subject", "issuer", "serial_number", "fingerprint", "signature_algorithm"),
                "classes": ("collapse",),
                "description": "Auto-populated from uploaded certificate"
            },
        ),
        (
            "Validity Period",
            {
                "fields": ("valid_from", "valid_to"),
                "description": "Auto-populated from certificate"
            },
        ),
        (
            "Validation Status",
            {
                "fields": ("validation_status", "validation_warnings"),
                "description": "Certificate validation results"
            },
        ),
        (
            "Configuration", 
            {
                "fields": ("is_default", "is_active"),
                "description": "Only one certificate can be set as default"
            }
        ),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def subject_short(self, obj):
        """Display shortened subject for list view"""
        if obj.subject:
            # Extract CN (Common Name) if available
            parts = obj.subject.split(',')
            for part in parts:
                if part.strip().startswith('CN='):
                    return part.strip()[3:]  # Remove 'CN='
            # If no CN, return first 50 characters
            return obj.subject[:50] + '...' if len(obj.subject) > 50 else obj.subject
        return '-'
    subject_short.short_description = "Subject (CN)"

    def valid_status(self, obj):
        """Display validity status with color coding"""
        if obj.is_valid:
            return format_html('<span style="color: green; font-weight: bold;">✓ Valid</span>')
        elif obj.validation_status == 'expired':
            return format_html('<span style="color: orange; font-weight: bold;">⏰ Expired</span>')
        elif obj.validation_status == 'warning':
            return format_html('<span style="color: #ff9800; font-weight: bold;">⚠ Valid (Warnings)</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Invalid</span>')
    valid_status.short_description = "Status"

    def save_model(self, request, obj, form, change):
        """Enhanced save with validation feedback"""
        try:
            super().save_model(request, obj, form, change)
            
            # Add success message with validation info
            if obj.validation_status == 'valid':
                self.message_user(request, f"Certificate '{obj.certificate_name}' uploaded and validated successfully.", level='SUCCESS')
            elif obj.validation_status == 'warning':
                self.message_user(request, f"Certificate '{obj.certificate_name}' uploaded with warnings: {obj.validation_warnings}", level='WARNING')
                
        except Exception as e:
            self.message_user(request, f"Certificate validation failed: {str(e)}", level='ERROR')
            raise

    def get_form(self, request, obj=None, **kwargs):
        """Customize form for better UX"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for file fields
        if 'certificate_file' in form.base_fields:
            form.base_fields['certificate_file'].help_text = (
                "Upload X.509 certificate file (.pem, .crt, .cer, .der). "
                "Certificate will be validated for SMP signing compatibility."
            )
        
        if 'private_key_file' in form.base_fields:
            form.base_fields['private_key_file'].help_text = (
                "Optional: Upload private key file (.pem, .key, .der). "
                "Required for signing operations."
            )
            
        return form

    def get_readonly_fields(self, request, obj=None):
        """Make validation fields readonly after creation"""
        readonly = list(self.readonly_fields)
        
        # If editing existing object, make more fields readonly
        if obj:
            readonly.extend(['certificate_type'])
            
        return readonly

    actions = ['validate_certificates', 'set_as_default']

    def validate_certificates(self, request, queryset):
        """Re-validate selected certificates"""
        validated_count = 0
        for cert in queryset:
            try:
                cert.full_clean()
                cert.save()
                validated_count += 1
            except Exception as e:
                self.message_user(request, f"Failed to validate {cert.certificate_name}: {str(e)}", level='ERROR')
        
        if validated_count:
            self.message_user(request, f"Successfully re-validated {validated_count} certificate(s).", level='SUCCESS')
    
    validate_certificates.short_description = "Re-validate selected certificates"

    def set_as_default(self, request, queryset):
        """Set a certificate as default"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one certificate to set as default.", level='ERROR')
            return
        
        cert = queryset.first()
        if not cert.is_valid:
            self.message_user(request, "Cannot set invalid/expired certificate as default.", level='ERROR')
            return
        
        # Clear existing default
        SigningCertificate.objects.filter(is_default=True).update(is_default=False)
        cert.is_default = True
        cert.save()
        
        self.message_user(request, f"'{cert.certificate_name}' set as default signing certificate.", level='SUCCESS')
    
    set_as_default.short_description = "Set as default certificate"