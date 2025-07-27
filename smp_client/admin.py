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
    list_display = [
        "certificate_name",
        "common_name_display",
        "key_info_display",
        "valid_status",
        "expires_warning",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "certificate_type",
        "key_algorithm",
        "is_default",
        "is_active",
        "valid_from",
        "valid_to",
    ]
    search_fields = [
        "certificate_name",
        "subject",
        "issuer",
        "serial_number",
        "fingerprint",
    ]
    readonly_fields = [
        "id",
        "subject",
        "issuer",
        "serial_number",
        "fingerprint",
        "valid_from",
        "valid_to",
        "key_algorithm",
        "key_size",
        "signature_algorithm",
        "created_at",
        "updated_at",
        "certificate_details_display",
    ]

    fieldsets = (
        (
            "Certificate Information",
            {"fields": ("certificate_name", "certificate_type")},
        ),
        (
            "Certificate Files",
            {
                "fields": ("certificate_file", "private_key_file"),
                "description": "Upload X.509 certificate and private key files. "
                "Only PEM (.pem, .crt) and DER (.der, .cer) formats are supported. "
                "Files will be validated for security and compatibility.",
            },
        ),
        (
            "Auto-Populated Certificate Details",
            {
                "fields": (
                    "certificate_details_display",
                    "subject",
                    "issuer",
                    "serial_number",
                    "fingerprint",
                ),
                "classes": ("collapse",),
                "description": "These fields are automatically populated from the uploaded certificate.",
            },
        ),
        (
            "Validity Information",
            {
                "fields": ("valid_from", "valid_to"),
                "description": "Certificate validity period (auto-populated from certificate).",
            },
        ),
        (
            "Key Information",
            {
                "fields": ("key_algorithm", "key_size", "signature_algorithm"),
                "classes": ("collapse",),
                "description": "Public key and signature algorithm details (auto-populated).",
            },
        ),
        ("Configuration", {"fields": ("is_default", "is_active")}),
        (
            "Metadata",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to provide better help text"""
        form = super().get_form(request, obj, **kwargs)

        # Add custom help text for file fields
        if "certificate_file" in form.base_fields:
            form.base_fields["certificate_file"].help_text = (
                "Upload X.509 certificate in PEM (.pem, .crt) or DER (.der, .cer) format. "
                "Certificate will be validated for: format, validity dates, key strength, "
                "signature algorithm, and key usage."
            )

        if "private_key_file" in form.base_fields:
            form.base_fields["private_key_file"].help_text = (
                "Upload private key in PEM or DER format (optional). "
                "If provided, will be validated to match the certificate. "
                "Password-protected keys are not currently supported."
            )

        return form

    def common_name_display(self, obj):
        """Display the certificate's Common Name"""
        cn = obj.common_name
        if cn:
            return format_html('<span title="{}">{}</span>', obj.subject, cn)
        return format_html(
            '<span style="color: gray;" title="{}">No CN</span>',
            obj.subject or "No subject",
        )

    common_name_display.short_description = "Common Name"

    def key_info_display(self, obj):
        """Display key algorithm and size"""
        if obj.key_algorithm and obj.key_size:
            color = "green" if obj.key_size >= 2048 else "orange"
            return format_html(
                '<span style="color: {};">{} {}-bit</span>',
                color,
                obj.key_algorithm,
                obj.key_size,
            )
        return format_html('<span style="color: gray;">Unknown</span>')

    key_info_display.short_description = "Key Info"

    def valid_status(self, obj):
        """Display certificate validity status with colors"""
        if obj.is_valid:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        elif obj.valid_to and obj.valid_to < timezone.now():
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Expired</span>'
            )
        elif obj.valid_from and obj.valid_from > timezone.now():
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Not Yet Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: gray; font-weight: bold;">? Unknown</span>'
            )

    valid_status.short_description = "Validity"

    def expires_warning(self, obj):
        """Show warning if certificate expires soon"""
        if obj.expires_soon:
            return format_html(
                '<span style="color: orange; font-weight: bold;" title="Expires: {}">⚠ Expires Soon</span>',
                obj.valid_to.strftime("%Y-%m-%d") if obj.valid_to else "Unknown",
            )
        return ""

    expires_warning.short_description = "Expiry Warning"

    def certificate_details_display(self, obj):
        """Display formatted certificate details"""
        if not obj.certificate_file:
            return format_html(
                '<span style="color: gray;">No certificate uploaded</span>'
            )

        details = obj.get_certificate_details()

        html = []
        html.append('<div style="font-family: monospace; font-size: 12px;">')

        # Validity status
        if details["is_valid"]:
            html.append(
                '<div style="color: green; font-weight: bold;">✓ Certificate is currently valid</div>'
            )
        else:
            html.append(
                '<div style="color: red; font-weight: bold;">✗ Certificate is invalid or expired</div>'
            )

        if details["expires_soon"]:
            html.append(
                '<div style="color: orange; font-weight: bold;">⚠ Certificate expires within 30 days</div>'
            )

        html.append("<br>")

        # Key details
        html.append(
            f"<strong>Subject:</strong> {details.get('subject', 'Unknown')}<br>"
        )
        html.append(f"<strong>Issuer:</strong> {details.get('issuer', 'Unknown')}<br>")
        html.append(
            f"<strong>Serial:</strong> {details.get('serial_number', 'Unknown')}<br>"
        )
        html.append(
            f"<strong>Fingerprint:</strong> {details.get('fingerprint', 'Unknown')}<br>"
        )
        html.append(
            f"<strong>Valid From:</strong> {details.get('valid_from', 'Unknown')}<br>"
        )
        html.append(
            f"<strong>Valid To:</strong> {details.get('valid_to', 'Unknown')}<br>"
        )
        html.append(
            f"<strong>Key:</strong> {details.get('key_algorithm', 'Unknown')} {details.get('key_size', 'Unknown')}-bit<br>"
        )
        html.append(
            f"<strong>Signature:</strong> {details.get('signature_algorithm', 'Unknown')}<br>"
        )

        html.append("</div>")

        return format_html("".join(html))

    certificate_details_display.short_description = "Certificate Details"

    def save_model(self, request, obj, form, change):
        """Enhanced save with validation feedback"""
        try:
            # Ensure only one default certificate
            if obj.is_default:
                SigningCertificate.objects.filter(is_default=True).exclude(
                    id=obj.id
                ).update(is_default=False)

            super().save_model(request, obj, form, change)

            # Provide success feedback with certificate details
            if obj.certificate_file:
                self.message_user(
                    request,
                    format_html(
                        'Certificate "{}" uploaded and validated successfully. '
                        "Subject: {} | Valid until: {} | Key: {} {}-bit",
                        obj.certificate_name,
                        obj.common_name or "Unknown",
                        (
                            obj.valid_to.strftime("%Y-%m-%d")
                            if obj.valid_to
                            else "Unknown"
                        ),
                        obj.key_algorithm or "Unknown",
                        obj.key_size or "Unknown",
                    ),
                )

                if obj.expires_soon:
                    self.message_user(
                        request,
                        format_html(
                            'Warning: Certificate "{}" expires within 30 days ({})',
                            obj.certificate_name,
                            (
                                obj.valid_to.strftime("%Y-%m-%d")
                                if obj.valid_to
                                else "Unknown"
                            ),
                        ),
                        level="WARNING",
                    )

        except Exception as e:
            self.message_user(
                request, f"Error saving certificate: {str(e)}", level="ERROR"
            )
