"""
Certificate validation utilities for SMP signing certificates
Validates X.509 certificates for appropriate use in SMP document signing
"""

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CertificateValidator:
    """Validates certificates for SMP signing purposes"""

    def __init__(self, certificate_data):
        """
        Initialize validator with certificate data
        
        Args:
            certificate_data: Bytes or file-like object containing certificate
        """
        if hasattr(certificate_data, 'read'):
            certificate_data = certificate_data.read()
        
        # Ensure we have bytes
        if isinstance(certificate_data, str):
            certificate_data = certificate_data.encode('utf-8')
        
        # Clean up common PEM formatting issues
        certificate_data = self._clean_pem_data(certificate_data)
        
        try:
            # Try PEM format first
            self.certificate = x509.load_pem_x509_certificate(certificate_data)
        except Exception as pem_error:
            try:
                # Try DER format
                self.certificate = x509.load_der_x509_certificate(certificate_data)
            except Exception as der_error:
                # Provide helpful error message
                error_msg = f"Invalid certificate format. PEM error: {str(pem_error)}. DER error: {str(der_error)}"
                if "MalformedFraming" in str(pem_error):
                    error_msg += "\n\nPEM file formatting tips:\n"
                    error_msg += "- Ensure file starts with '-----BEGIN CERTIFICATE-----'\n"
                    error_msg += "- Ensure file ends with '-----END CERTIFICATE-----'\n"
                    error_msg += "- No extra spaces or characters before/after headers\n"
                    error_msg += "- Each line should be exactly 64 characters (except last line)\n"
                    error_msg += "- Use Unix line endings (LF, not CRLF)"
                raise ValidationError(error_msg)

    def _clean_pem_data(self, data):
        """Clean up common PEM formatting issues"""
        if not data:
            return data
            
        # Convert to string for processing
        if isinstance(data, bytes):
            try:
                data_str = data.decode('utf-8')
            except UnicodeDecodeError:
                # If it's not UTF-8, assume it's binary (DER)
                return data
        else:
            data_str = data
        
        # Remove any BOM
        data_str = data_str.lstrip('\ufeff')
        
        # Normalize line endings to Unix style
        data_str = data_str.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove any leading/trailing whitespace
        data_str = data_str.strip()
        
        # Check if it looks like PEM
        if '-----BEGIN' in data_str and '-----END' in data_str:
            lines = data_str.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # Remove trailing whitespace but preserve the line structure
                line = line.rstrip()
                if line:  # Skip empty lines
                    cleaned_lines.append(line)
            
            # Ensure proper line endings
            data_str = '\n'.join(cleaned_lines) + '\n'
        
        return data_str.encode('utf-8')

    def validate_for_smp_signing(self):
        """
        Comprehensive validation for SMP signing certificates
        
        Returns:
            dict: Validation results with certificate information
        
        Raises:
            ValidationError: If certificate is not suitable for SMP signing
        """
        errors = []
        warnings = []
        info = {}

        # Basic certificate information
        info.update(self._extract_certificate_info())

        # Validation checks
        self._validate_not_expired(errors)
        self._validate_key_usage(errors, warnings)
        self._validate_key_algorithm(errors, warnings)
        self._validate_key_size(errors, warnings)
        self._validate_extensions(warnings)

        if errors:
            raise ValidationError(
                f"Certificate validation failed: {'; '.join(errors)}"
            )

        return {
            'info': info,
            'warnings': warnings,
            'is_valid': True
        }

    def _extract_certificate_info(self):
        """Extract basic certificate information"""
        subject_parts = []
        for attribute in self.certificate.subject:
            subject_parts.append(f"{attribute.oid._name}={attribute.value}")
        
        issuer_parts = []
        for attribute in self.certificate.issuer:
            issuer_parts.append(f"{attribute.oid._name}={attribute.value}")

        # Get fingerprint
        fingerprint = self.certificate.fingerprint(hashes.SHA256()).hex()

        return {
            'subject': ', '.join(subject_parts),
            'issuer': ', '.join(issuer_parts),
            'serial_number': str(self.certificate.serial_number),
            'fingerprint': fingerprint,
            'valid_from': self.certificate.not_valid_before,
            'valid_to': self.certificate.not_valid_after,
            'version': self.certificate.version.name,
            'signature_algorithm': self.certificate.signature_algorithm_oid._name,
        }

    def _validate_not_expired(self, errors):
        """Check if certificate is currently valid (not expired)"""
        now = datetime.now()
        
        if self.certificate.not_valid_before > now:
            errors.append("Certificate is not yet valid")
        
        if self.certificate.not_valid_after < now:
            errors.append("Certificate has expired")

    def _validate_key_usage(self, errors, warnings):
        """Validate key usage extensions for signing"""
        try:
            key_usage = self.certificate.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.KEY_USAGE
            ).value

            if not key_usage.digital_signature:
                errors.append("Certificate does not allow digital signatures")
            
            if not key_usage.key_cert_sign:
                warnings.append("Certificate does not have key_cert_sign usage (may be acceptable for document signing)")

        except x509.ExtensionNotFound:
            warnings.append("No Key Usage extension found")

    def _validate_key_algorithm(self, errors, warnings):
        """Validate key algorithm is appropriate for signing"""
        public_key = self.certificate.public_key()
        
        if isinstance(public_key, rsa.RSAPublicKey):
            # RSA is good for signing
            pass
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            # EC is also good for signing
            pass
        else:
            warnings.append(f"Unusual key algorithm: {type(public_key).__name__}")

    def _validate_key_size(self, errors, warnings):
        """Validate key size is sufficient"""
        public_key = self.certificate.public_key()
        
        if isinstance(public_key, rsa.RSAPublicKey):
            key_size = public_key.key_size
            if key_size < 2048:
                errors.append(f"RSA key size {key_size} is too small (minimum 2048)")
            elif key_size < 3072:
                warnings.append(f"RSA key size {key_size} is acceptable but 3072+ recommended")
                
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            curve_name = public_key.curve.name
            if curve_name not in ['secp256r1', 'secp384r1', 'secp521r1']:
                warnings.append(f"Elliptic curve {curve_name} may not be widely supported")

    def _validate_extensions(self, warnings):
        """Check for important certificate extensions"""
        extensions_found = [ext.oid._name for ext in self.certificate.extensions]
        
        recommended_extensions = [
            'keyUsage',
            'basicConstraints',
            'subjectKeyIdentifier',
            'authorityKeyIdentifier'
        ]
        
        missing_extensions = set(recommended_extensions) - set(extensions_found)
        if missing_extensions:
            warnings.append(f"Missing recommended extensions: {', '.join(missing_extensions)}")


def validate_certificate_file(certificate_file):
    """
    Django field validator for certificate files
    
    Args:
        certificate_file: Django UploadedFile
        
    Raises:
        ValidationError: If certificate is invalid
    """
    if not certificate_file:
        raise ValidationError("Certificate file is required")
    
    # Check file size (max 10MB)
    if certificate_file.size > 10 * 1024 * 1024:
        raise ValidationError("Certificate file is too large (max 10MB)")
    
    # Check file extension
    allowed_extensions = ['.pem', '.crt', '.cer', '.der', '.cert']
    file_extension = None
    if hasattr(certificate_file, 'name') and certificate_file.name:
        file_extension = '.' + certificate_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Invalid file extension '{file_extension}'. Allowed: {', '.join(allowed_extensions)}"
            )
    
    # Read file content
    try:
        certificate_file.seek(0)  # Ensure we're at the beginning
        file_content = certificate_file.read()
        certificate_file.seek(0)  # Reset for later use
        
        if not file_content:
            raise ValidationError("Certificate file is empty")
            
    except Exception as e:
        raise ValidationError(f"Error reading certificate file: {str(e)}")
    
    # Validate certificate content
    try:
        validator = CertificateValidator(file_content)
        result = validator.validate_for_smp_signing()
        return result
    except ValidationError as e:
        # Re-raise validation errors as-is
        raise e
    except Exception as e:
        raise ValidationError(f"Certificate validation failed: {str(e)}")


def validate_private_key_file(private_key_file):
    """
    Django field validator for private key files
    
    Args:
        private_key_file: Django UploadedFile
        
    Raises:
        ValidationError: If private key is invalid
    """
    if not private_key_file:
        return  # Private key is optional
    
    # Check file size (max 10MB)
    if private_key_file.size > 10 * 1024 * 1024:
        raise ValidationError("Private key file is too large (max 10MB)")
    
    # Check file extension
    allowed_extensions = ['.pem', '.key', '.der']
    if hasattr(private_key_file, 'name') and private_key_file.name:
        file_extension = '.' + private_key_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Invalid private key file extension. Allowed: {', '.join(allowed_extensions)}"
            )
    
    # Try to load private key
    try:
        key_data = private_key_file.read()
        private_key_file.seek(0)  # Reset file pointer
        
        try:
            # Try PEM format
            serialization.load_pem_private_key(key_data, password=None)
        except ValueError:
            try:
                # Try DER format
                serialization.load_der_private_key(key_data, password=None)
            except ValueError:
                raise ValidationError("Invalid private key format (PEM or DER required)")
                
    except Exception as e:
        raise ValidationError(f"Private key validation failed: {str(e)}")
