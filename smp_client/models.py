"""
SMP Client Models - Service Metadata Publishing
Based on OASIS BDXR SMP v1.0 specification and DomiSMP implementation
Integrates with European test SMP server: https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu/
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
import xml.etree.ElementTree as ET
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
import datetime
import logging

logger = logging.getLogger(__name__)


def validate_certificate_file(uploaded_file):
    """
    Comprehensive certificate validation for uploaded certificate files
    Ensures only valid X.509 certificates are accepted
    """
    try:
        # Read the uploaded file content
        uploaded_file.seek(0)
        cert_data = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer

        # Try to parse as PEM format first
        try:
            certificate = x509.load_pem_x509_certificate(cert_data)
        except ValueError:
            # Try DER format
            try:
                certificate = x509.load_der_x509_certificate(cert_data)
            except ValueError:
                raise ValidationError(
                    "Invalid certificate format. Only PEM (.pem, .crt) and DER (.der, .cer) formats are supported."
                )

        # Validate certificate type
        if not isinstance(certificate, x509.Certificate):
            raise ValidationError("Uploaded file is not a valid X.509 certificate.")

        # Check certificate validity dates
        now = datetime.datetime.now(datetime.timezone.utc)

        if certificate.not_valid_before > now:
            raise ValidationError(
                f"Certificate is not yet valid. Valid from: {certificate.not_valid_before}"
            )

        if certificate.not_valid_after < now:
            raise ValidationError(
                f"Certificate has expired. Valid until: {certificate.not_valid_after}"
            )

        # Check if certificate will expire soon (within 30 days)
        thirty_days = datetime.timedelta(days=30)
        if certificate.not_valid_after < (now + thirty_days):
            logger.warning(f"Certificate expires soon: {certificate.not_valid_after}")

        # Validate key usage for signing certificates
        try:
            key_usage = certificate.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.KEY_USAGE
            ).value

            if not (key_usage.digital_signature or key_usage.key_cert_sign):
                raise ValidationError(
                    "Certificate must have Digital Signature or Certificate Sign key usage for SMP signing."
                )
        except x509.ExtensionNotFound:
            logger.warning("Certificate does not have Key Usage extension")

        # Validate key strength
        public_key = certificate.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            if public_key.key_size < 2048:
                raise ValidationError(
                    f"RSA key size {public_key.key_size} is too weak. Minimum 2048 bits required."
                )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            if public_key.curve.key_size < 256:
                raise ValidationError(
                    f"Elliptic curve key size {public_key.curve.key_size} is too weak. Minimum 256 bits required."
                )
        else:
            logger.warning(f"Unknown key type: {type(public_key)}")

        # Check for required subject attributes
        subject = certificate.subject
        subject_cn = None
        subject_o = None

        for attribute in subject:
            if attribute.oid == x509.oid.NameOID.COMMON_NAME:
                subject_cn = attribute.value
            elif attribute.oid == x509.oid.NameOID.ORGANIZATION_NAME:
                subject_o = attribute.value

        if not subject_cn:
            logger.warning("Certificate does not have a Common Name (CN)")

        # Validate signature algorithm
        if isinstance(
            certificate.signature_algorithm_oid,
            type(x509.oid.SignatureAlgorithmOID.SHA1_WITH_RSA),
        ):
            if (
                certificate.signature_algorithm_oid
                == x509.oid.SignatureAlgorithmOID.SHA1_WITH_RSA
            ):
                raise ValidationError(
                    "SHA-1 signature algorithm is deprecated and not secure. Use SHA-256 or better."
                )

        logger.info(
            f"Certificate validation successful: CN={subject_cn}, O={subject_o}"
        )
        return certificate

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Certificate validation error: {str(e)}")
        raise ValidationError(f"Certificate validation failed: {str(e)}")


def validate_private_key_file(uploaded_file):
    """
    Validate uploaded private key files
    Ensures private keys are in correct format and have adequate strength
    """
    try:
        # Read the uploaded file content
        uploaded_file.seek(0)
        key_data = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer

        # Try to parse as PEM format
        try:
            private_key = serialization.load_pem_private_key(key_data, password=None)
        except ValueError:
            # Try with password (we'll need to handle this in the admin)
            try:
                private_key = serialization.load_der_private_key(
                    key_data, password=None
                )
            except ValueError:
                raise ValidationError(
                    "Invalid private key format. Only PEM and DER formats are supported. "
                    "Password-protected keys are not currently supported."
                )

        # Validate key type and strength
        if isinstance(private_key, rsa.RSAPrivateKey):
            if private_key.key_size < 2048:
                raise ValidationError(
                    f"RSA private key size {private_key.key_size} is too weak. Minimum 2048 bits required."
                )
        elif isinstance(private_key, ec.EllipticCurvePrivateKey):
            if private_key.curve.key_size < 256:
                raise ValidationError(
                    f"Elliptic curve private key size {private_key.curve.key_size} is too weak. Minimum 256 bits required."
                )
        else:
            raise ValidationError(f"Unsupported private key type: {type(private_key)}")

        logger.info(f"Private key validation successful: {type(private_key).__name__}")
        return private_key

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Private key validation error: {str(e)}")
        raise ValidationError(f"Private key validation failed: {str(e)}")


def validate_certificate_key_pair(certificate, private_key):
    """
    Validate that a certificate and private key are a matching pair
    """
    try:
        cert_public_key = certificate.public_key()
        private_public_key = private_key.public_key()

        # Compare public key components
        if isinstance(cert_public_key, rsa.RSAPublicKey) and isinstance(
            private_public_key, rsa.RSAPublicKey
        ):
            cert_numbers = cert_public_key.public_numbers()
            private_numbers = private_public_key.public_numbers()

            if (
                cert_numbers.n != private_numbers.n
                or cert_numbers.e != private_numbers.e
            ):
                raise ValidationError(
                    "Certificate and private key do not match. The public key in the certificate "
                    "does not correspond to the uploaded private key."
                )
        elif isinstance(cert_public_key, ec.EllipticCurvePublicKey) and isinstance(
            private_public_key, ec.EllipticCurvePublicKey
        ):
            cert_numbers = cert_public_key.public_numbers()
            private_numbers = private_public_key.public_numbers()

            if (
                cert_numbers.x != private_numbers.x
                or cert_numbers.y != private_numbers.y
            ):
                raise ValidationError(
                    "Certificate and private key do not match. The public key in the certificate "
                    "does not correspond to the uploaded private key."
                )
        else:
            raise ValidationError(
                "Certificate and private key types do not match or are not supported."
            )

        logger.info(
            "Certificate and private key validation successful - they are a matching pair"
        )
        return True

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Certificate-key pair validation error: {str(e)}")
        raise ValidationError(f"Certificate-key pair validation failed: {str(e)}")


class Domain(models.Model):
    """SMP Domain - represents a SML/SMP domain"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain_code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Domain identifier (e.g., ehealth-actorid-qns)",
    )
    domain_name = models.CharField(max_length=200)
    sml_subdomain = models.CharField(
        max_length=100, help_text="SML subdomain for DNS lookups"
    )

    # SMP Configuration
    smp_url = models.URLField(help_text="Base SMP server URL")
    is_test_domain = models.BooleanField(
        default=True, help_text="Whether this is a test/training domain"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["domain_name"]

    def __str__(self):
        return f"{self.domain_name} ({self.domain_code})"


class ParticipantIdentifierScheme(models.Model):
    """Participant identifier schemes (e.g., iso6523-actorid-upis)"""

    scheme_id = models.CharField(max_length=100, unique=True)
    scheme_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Validation rules
    validation_pattern = models.CharField(
        max_length=500, blank=True, help_text="Regex pattern for validation"
    )
    example_value = models.CharField(max_length=200, blank=True)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scheme_name} ({self.scheme_id})"


class DocumentTypeScheme(models.Model):
    """Document type identifier schemes"""

    scheme_id = models.CharField(max_length=100, unique=True)
    scheme_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Document type categories
    CATEGORY_CHOICES = [
        ("ehealth", "eHealth"),
        ("eprocurement", "eProcurement"),
        ("einvoicing", "eInvoicing"),
        ("customs", "Customs"),
        ("other", "Other"),
    ]
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="ehealth"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scheme_name} ({self.scheme_id})"


class Participant(models.Model):
    """SMP Participant - represents a participant in the network"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Participant Identity
    participant_identifier = models.CharField(
        max_length=500, help_text="Participant identifier value"
    )
    participant_scheme = models.ForeignKey(
        ParticipantIdentifierScheme, on_delete=models.CASCADE
    )
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)

    # Participant Details
    participant_name = models.CharField(max_length=200, blank=True)
    country_code = models.CharField(
        max_length=3, blank=True, help_text="ISO 3166-1 alpha-2"
    )
    organization_type = models.CharField(max_length=100, blank=True)

    # Contact Information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Technical Details
    certificate_subject_dn = models.TextField(
        blank=True, help_text="Certificate subject distinguished name"
    )
    certificate_serial = models.CharField(max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["participant_identifier", "participant_scheme", "domain"]
        indexes = [
            models.Index(fields=["participant_identifier", "participant_scheme"]),
            models.Index(fields=["country_code", "domain"]),
        ]

    def __str__(self):
        return f"{self.participant_identifier} ({self.participant_scheme.scheme_id})"

    @property
    def full_participant_id(self):
        """Returns the full participant ID in SMP format"""
        return f"{self.participant_scheme.scheme_id}::{self.participant_identifier}"


class DocumentType(models.Model):
    """Document types supported by participants"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Document Type Identity
    document_type_identifier = models.CharField(max_length=500)
    document_scheme = models.ForeignKey(DocumentTypeScheme, on_delete=models.CASCADE)

    # Document Details
    document_name = models.CharField(max_length=200)
    document_version = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    # eHealth specific fields
    profile_id = models.CharField(
        max_length=200, blank=True, help_text="eHealth profile identifier"
    )
    customization_id = models.CharField(
        max_length=200, blank=True, help_text="Document customization"
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["document_type_identifier", "document_scheme"]

    def __str__(self):
        return f"{self.document_name} ({self.document_type_identifier})"


class ServiceGroup(models.Model):
    """SMP Service Group - groups services for a participant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.OneToOneField(
        Participant, on_delete=models.CASCADE, related_name="service_group"
    )

    # Service Group Metadata
    extension_data = models.JSONField(
        blank=True, default=dict, help_text="Additional extension data"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ServiceGroup for {self.participant}"

    def to_xml(self):
        """Generate OASIS BDXR SMP v1.0 compliant ServiceGroup XML"""
        root = ET.Element("ServiceGroup")
        root.set("xmlns", "http://docs.oasis-open.org/bdxr/ns/SMP/2016/05")

        # Participant Identifier
        participant_id = ET.SubElement(root, "ParticipantIdentifier")
        participant_id.set("scheme", self.participant.participant_scheme.scheme_id)
        participant_id.text = self.participant.participant_identifier

        # Service Metadata References
        service_metadata_refs = ET.SubElement(
            root, "ServiceMetadataReferenceCollection"
        )

        for service in self.servicemetadata_set.filter(is_active=True):
            smp_ref = ET.SubElement(service_metadata_refs, "ServiceMetadataReference")
            smp_ref.set(
                "href",
                f"/{self.participant.participant_scheme.scheme_id}::{self.participant.participant_identifier}/services/{service.document_type.type_id}",
            )

        return ET.tostring(root, encoding="unicode")


class ServiceMetadata(models.Model):
    """SMP Service Metadata - defines how to reach a service"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_group = models.ForeignKey(
        ServiceGroup, on_delete=models.CASCADE, related_name="services"
    )
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)

    # Service Information
    service_description = models.TextField(blank=True)

    # Technical Details
    technical_contact_url = models.URLField(blank=True)
    technical_information_url = models.URLField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["service_group", "document_type"]

    def __str__(self):
        return f"{self.document_type} service for {self.service_group.participant}"

    def to_xml(self):
        """Generate OASIS BDXR SMP v1.0 compliant ServiceMetadata XML"""
        root = ET.Element("ServiceMetadata")
        root.set("xmlns", "http://docs.oasis-open.org/bdxr/ns/SMP/2016/05")

        # Service Information
        service_info = ET.SubElement(root, "ServiceInformation")

        # Participant Identifier
        participant_id = ET.SubElement(service_info, "ParticipantIdentifier")
        participant_id.set(
            "scheme", self.service_group.participant.participant_scheme.scheme_id
        )
        participant_id.text = self.service_group.participant.participant_identifier

        # Document Identifier
        doc_id = ET.SubElement(service_info, "DocumentIdentifier")
        doc_id.set("scheme", self.document_type.scheme.scheme_id)
        doc_id.text = self.document_type.type_id

        # Process List
        process_list = ET.SubElement(service_info, "ProcessList")

        for endpoint in self.endpoints.filter(is_active=True):
            process_elem = ET.SubElement(process_list, "Process")

            # Process Identifier
            process_id = ET.SubElement(process_elem, "ProcessIdentifier")
            process_id.set("scheme", endpoint.process.process_scheme)
            process_id.text = endpoint.process.process_identifier

            # Service Endpoint List
            endpoint_list = ET.SubElement(process_elem, "ServiceEndpointList")
            endpoint_elem = ET.SubElement(endpoint_list, "Endpoint")
            endpoint_elem.set("transportProfile", endpoint.transport_profile)

            # Endpoint URL
            endpoint_url = ET.SubElement(endpoint_elem, "EndpointURI")
            endpoint_url.text = endpoint.endpoint_url

            # Service dates
            if endpoint.service_activation_date:
                activation = ET.SubElement(endpoint_elem, "ServiceActivationDate")
                activation.text = endpoint.service_activation_date.isoformat()

            if endpoint.service_expiration_date:
                expiration = ET.SubElement(endpoint_elem, "ServiceExpirationDate")
                expiration.text = endpoint.service_expiration_date.isoformat()

            # Certificate
            if endpoint.certificate:
                cert = ET.SubElement(endpoint_elem, "Certificate")
                cert.text = endpoint.certificate

            # Service description
            if endpoint.service_description:
                desc = ET.SubElement(endpoint_elem, "ServiceDescription")
                desc.text = endpoint.service_description

            # Technical contact
            if endpoint.technical_contact_url:
                contact = ET.SubElement(endpoint_elem, "TechnicalContactUrl")
                contact.text = endpoint.technical_contact_url

        return ET.tostring(root, encoding="unicode")


class ProcessIdentifier(models.Model):
    """Process identifiers for services"""

    process_identifier = models.CharField(max_length=500)
    process_scheme = models.CharField(max_length=200, default="cenbii-procid-ubl")
    process_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # eHealth specific
    is_ehealth_process = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.process_name} ({self.process_identifier})"


class Endpoint(models.Model):
    """Service endpoints - actual connection details"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_metadata = models.ForeignKey(
        ServiceMetadata, on_delete=models.CASCADE, related_name="endpoints"
    )
    process = models.ForeignKey(ProcessIdentifier, on_delete=models.CASCADE)

    # Endpoint Details
    endpoint_url = models.URLField(help_text="Service endpoint URL")
    transport_profile = models.CharField(
        max_length=200,
        default="bdxr-transport-ebms3-as4-v1p0",
        help_text="Transport profile identifier",
    )

    # Security
    requires_business_level_signature = models.BooleanField(default=False)
    minimum_authentication_level = models.CharField(max_length=100, blank=True)

    # Certificate Information
    certificate = models.TextField(help_text="Base64 encoded certificate")
    service_activation_date = models.DateTimeField(null=True, blank=True)
    service_expiration_date = models.DateTimeField(null=True, blank=True)

    # Technical Contact
    technical_contact_url = models.URLField(blank=True)
    service_description = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.process} endpoint: {self.endpoint_url}"

    def is_valid(self):
        """Check if endpoint is currently valid"""
        now = timezone.now()
        if self.service_expiration_date and now > self.service_expiration_date:
            return False
        if self.service_activation_date and now < self.service_activation_date:
            return False
        return self.is_active

    def to_xml(self):
        """Generate OASIS BDXR SMP v1.0 compliant Endpoint XML"""
        root = ET.Element("Endpoint")
        root.set("xmlns", "http://docs.oasis-open.org/bdxr/ns/SMP/2016/05")
        root.set("transportProfile", self.transport_profile)

        # Endpoint URL
        endpoint_url_elem = ET.SubElement(root, "EndpointURI")
        endpoint_url_elem.text = self.endpoint_url

        # Service activation date
        if self.service_activation_date:
            activation_elem = ET.SubElement(root, "ServiceActivationDate")
            activation_elem.text = self.service_activation_date.isoformat()

        # Service expiration date
        if self.service_expiration_date:
            expiration_elem = ET.SubElement(root, "ServiceExpirationDate")
            expiration_elem.text = self.service_expiration_date.isoformat()

        # Certificate
        if self.certificate:
            cert_elem = ET.SubElement(root, "Certificate")
            cert_elem.text = self.certificate

        # Service description
        if self.service_description:
            desc_elem = ET.SubElement(root, "ServiceDescription")
            desc_elem.text = self.service_description

        # Technical contact
        if self.technical_contact_url:
            contact_elem = ET.SubElement(root, "TechnicalContactUrl")
            contact_elem.text = self.technical_contact_url

        return ET.tostring(root, encoding="unicode")


class SMPQuery(models.Model):
    """Track SMP queries for analytics and debugging"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Query Details
    participant_id = models.CharField(max_length=500)
    participant_scheme = models.CharField(max_length=200)
    document_type_id = models.CharField(max_length=500, blank=True)
    document_scheme = models.CharField(max_length=200, blank=True)

    # Query Context
    source_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    query_type = models.CharField(
        max_length=50,
        choices=[
            ("service_group", "Service Group Lookup"),
            ("service_metadata", "Service Metadata Lookup"),
            ("participant_list", "Participant List"),
            ("domain_list", "Domain List"),
        ],
    )

    # Response
    response_status = models.CharField(max_length=20, default="success")
    response_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp", "query_type"]),
            models.Index(fields=["participant_id", "participant_scheme"]),
        ]

    def __str__(self):
        return f"{self.query_type} query for {self.participant_id} at {self.timestamp}"


class SMPConfiguration(models.Model):
    """SMP Configuration settings"""

    # European SMP Integration
    european_smp_url = models.URLField(
        default="https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu",
        help_text="European test SMP server URL",
    )
    sync_enabled = models.BooleanField(
        default=True, help_text="Enable sync with European SMP"
    )
    sync_interval_hours = models.IntegerField(
        default=24, help_text="Sync interval in hours"
    )
    last_sync = models.DateTimeField(null=True, blank=True)

    # Local SMP Settings
    local_smp_enabled = models.BooleanField(default=True)
    local_domain_code = models.CharField(max_length=100, default="ehealth-actorid-qns")

    # API Settings
    api_enabled = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True)

    # Certificate Settings
    default_certificate = models.TextField(
        blank=True, help_text="Default certificate for new endpoints"
    )

    class Meta:
        verbose_name = "SMP Configuration"
        verbose_name_plural = "SMP Configuration"


class SMPDocument(models.Model):
    """SMP Document - manages generated, signed, and uploaded SMP documents"""

    DOCUMENT_TYPES = [
        ("service_group", "Service Group"),
        ("service_metadata", "Service Metadata"),
        ("endpoint", "Endpoint"),
        ("search_mask", "Search Mask"),
        ("certificate", "Certificate"),
    ]

    DOCUMENT_STATUS = [
        ("draft", "Draft"),
        ("generated", "Generated"),
        ("downloaded", "Downloaded"),
        ("signed", "Signed"),
        ("uploaded", "Uploaded to SMP"),
        ("synchronized", "Synchronized"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Document metadata
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=200)
    document_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default="draft")

    # File management
    original_file = models.FileField(
        upload_to="smp_documents/original/", blank=True, null=True
    )
    signed_file = models.FileField(
        upload_to="smp_documents/signed/", blank=True, null=True
    )

    # Content
    xml_content = models.TextField(blank=True, help_text="Generated XML content")
    signature_data = models.TextField(
        blank=True, help_text="Digital signature information"
    )

    # Relationships
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, null=True, blank=True
    )
    service_group = models.ForeignKey(
        ServiceGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    service_metadata = models.ForeignKey(
        ServiceMetadata, on_delete=models.CASCADE, null=True, blank=True
    )
    endpoint = models.ForeignKey(
        Endpoint, on_delete=models.CASCADE, null=True, blank=True
    )

    # SMP Upload tracking
    smp_server_url = models.URLField(
        blank=True, help_text="SMP server where document was uploaded"
    )
    smp_upload_timestamp = models.DateTimeField(null=True, blank=True)
    smp_response = models.TextField(blank=True, help_text="Server response from upload")

    # Digital signing
    certificate_fingerprint = models.CharField(max_length=100, blank=True)
    signature_timestamp = models.DateTimeField(null=True, blank=True)
    signer_info = models.CharField(max_length=200, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document_name} ({self.status})"

    def generate_xml_content(self):
        """Generate XML content based on document type"""
        if self.document_type == "service_group" and self.service_group:
            return self.service_group.to_xml()
        elif self.document_type == "service_metadata" and self.service_metadata:
            return self.service_metadata.to_xml()
        elif self.document_type == "endpoint" and self.endpoint:
            return self.endpoint.to_xml()
        return ""

    def save_generated_file(self):
        """Save generated XML content to file"""
        if self.xml_content:
            filename = f"{self.document_name}_{self.id}.xml"
            file_content = ContentFile(self.xml_content.encode("utf-8"))
            self.original_file.save(filename, file_content, save=False)

    def mark_as_signed(self, signature_data, certificate_info=None):
        """Mark document as signed with signature information"""
        self.status = "signed"
        self.signature_data = signature_data
        self.signature_timestamp = timezone.now()
        if certificate_info:
            self.certificate_fingerprint = certificate_info.get("fingerprint", "")
            self.signer_info = certificate_info.get("signer", "")
        self.save()

    def upload_to_smp(self, smp_url):
        """Upload signed document to SMP server"""
        try:
            # Implementation would depend on SMP server API
            # This is a placeholder for the actual upload logic
            self.smp_server_url = smp_url
            self.smp_upload_timestamp = timezone.now()
            self.status = "uploaded"
            self.save()
            return True
        except Exception as e:
            self.status = "error"
            self.smp_response = str(e)
            self.save()
            return False


class DocumentTemplate(models.Model):
    """Templates for generating SMP documents"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Template metadata
    template_name = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=SMPDocument.DOCUMENT_TYPES)
    description = models.TextField(blank=True)

    # Template content
    xml_template = models.TextField(help_text="XML template with placeholders")
    default_values = models.JSONField(
        default=dict, help_text="Default values for template fields"
    )

    # Configuration
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["template_name"]
        unique_together = ["document_type", "is_default"]

    def __str__(self):
        return f"{self.template_name} ({self.document_type})"


class SigningCertificate(models.Model):
    """Digital certificates for signing SMP documents with comprehensive validation"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Certificate metadata
    certificate_name = models.CharField(max_length=200)
    certificate_type = models.CharField(max_length=50, default="X.509")

    # Certificate data with validation
    certificate_file = models.FileField(
        upload_to="certificates/",
        validators=[validate_certificate_file],
        help_text="Upload X.509 certificate in PEM (.pem, .crt) or DER (.der, .cer) format",
    )
    private_key_file = models.FileField(
        upload_to="certificates/private/",
        blank=True,
        null=True,
        validators=[validate_private_key_file],
        help_text="Upload private key in PEM or DER format (optional, password-protected keys not supported)",
    )

    # Certificate information (auto-populated from certificate)
    subject = models.CharField(
        max_length=500, blank=True, help_text="Certificate subject DN"
    )
    issuer = models.CharField(
        max_length=500, blank=True, help_text="Certificate issuer DN"
    )
    serial_number = models.CharField(
        max_length=100, blank=True, help_text="Certificate serial number"
    )
    fingerprint = models.CharField(
        max_length=100, blank=True, help_text="SHA-256 fingerprint"
    )

    # Validity (auto-populated from certificate)
    valid_from = models.DateTimeField(
        null=True, blank=True, help_text="Certificate valid from date"
    )
    valid_to = models.DateTimeField(
        null=True, blank=True, help_text="Certificate valid until date"
    )

    # Key information
    key_algorithm = models.CharField(
        max_length=50, blank=True, help_text="Public key algorithm"
    )
    key_size = models.IntegerField(null=True, blank=True, help_text="Key size in bits")
    signature_algorithm = models.CharField(
        max_length=100, blank=True, help_text="Signature algorithm"
    )

    # Configuration
    is_default = models.BooleanField(
        default=False, help_text="Use as default signing certificate"
    )
    is_active = models.BooleanField(
        default=True, help_text="Certificate is active for use"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["certificate_name"]

    def __str__(self):
        return f"{self.certificate_name}"

    def clean(self):
        """Custom validation for the entire model"""
        super().clean()

        # Extract certificate information if file is provided
        if self.certificate_file:
            try:
                certificate = self._parse_certificate()
                self._populate_certificate_info(certificate)

                # If private key is also provided, validate they match
                if self.private_key_file:
                    private_key = self._parse_private_key()
                    validate_certificate_key_pair(certificate, private_key)

            except Exception as e:
                raise ValidationError(f"Certificate validation failed: {str(e)}")

    def save(self, *args, **kwargs):
        """Override save to ensure only one default certificate"""
        if self.is_default:
            # Unset other default certificates
            SigningCertificate.objects.filter(is_default=True).update(is_default=False)

        # Populate certificate information before saving
        if self.certificate_file:
            try:
                certificate = self._parse_certificate()
                self._populate_certificate_info(certificate)
            except Exception as e:
                logger.error(f"Failed to parse certificate during save: {str(e)}")

        super().save(*args, **kwargs)

    def _parse_certificate(self):
        """Parse the uploaded certificate file"""
        if not self.certificate_file:
            return None

        self.certificate_file.seek(0)
        cert_data = self.certificate_file.read()
        self.certificate_file.seek(0)

        try:
            # Try PEM format first
            return x509.load_pem_x509_certificate(cert_data)
        except ValueError:
            # Try DER format
            return x509.load_der_x509_certificate(cert_data)

    def _parse_private_key(self):
        """Parse the uploaded private key file"""
        if not self.private_key_file:
            return None

        self.private_key_file.seek(0)
        key_data = self.private_key_file.read()
        self.private_key_file.seek(0)

        try:
            # Try PEM format first
            return serialization.load_pem_private_key(key_data, password=None)
        except ValueError:
            # Try DER format
            return serialization.load_der_private_key(key_data, password=None)

    def _populate_certificate_info(self, certificate):
        """Populate model fields from parsed certificate"""
        # Subject and issuer
        self.subject = certificate.subject.rfc4514_string()
        self.issuer = certificate.issuer.rfc4514_string()

        # Serial number
        self.serial_number = str(certificate.serial_number)

        # Validity dates
        self.valid_from = certificate.not_valid_before
        self.valid_to = certificate.not_valid_after

        # Fingerprint (SHA-256)
        fingerprint = certificate.fingerprint(hashes.SHA256())
        self.fingerprint = fingerprint.hex().upper()

        # Key information
        public_key = certificate.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            self.key_algorithm = "RSA"
            self.key_size = public_key.key_size
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            self.key_algorithm = "EC"
            self.key_size = public_key.curve.key_size

        # Signature algorithm
        self.signature_algorithm = certificate.signature_algorithm_oid._name

    @property
    def is_valid(self):
        """Check if certificate is currently valid"""
        if not self.valid_from or not self.valid_to:
            return False

        now = timezone.now()
        return self.valid_from <= now <= self.valid_to

    @property
    def expires_soon(self):
        """Check if certificate expires within 30 days"""
        if not self.valid_to:
            return False

        thirty_days = datetime.timedelta(days=30)
        return self.valid_to <= (timezone.now() + thirty_days)

    @property
    def common_name(self):
        """Extract Common Name from certificate subject"""
        if not self.subject:
            return None

        # Parse the subject DN to extract CN
        for part in self.subject.split(","):
            part = part.strip()
            if part.startswith("CN="):
                return part[3:]
        return None

    def get_certificate_details(self):
        """Get detailed certificate information"""
        return {
            "subject": self.subject,
            "issuer": self.issuer,
            "serial_number": self.serial_number,
            "fingerprint": self.fingerprint,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "key_algorithm": self.key_algorithm,
            "key_size": self.key_size,
            "signature_algorithm": self.signature_algorithm,
            "is_valid": self.is_valid,
            "expires_soon": self.expires_soon,
            "common_name": self.common_name,
        }

    def __str__(self):
        return "SMP Configuration"
