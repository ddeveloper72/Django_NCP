"""
Custom admin forms for certificate management
Provides enhanced UI for certificate upload and validation
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import SigningCertificate
from .certificate_validators import validate_certificate_file, validate_private_key_file


class SigningCertificateAdminForm(forms.ModelForm):
    """Enhanced form for certificate administration"""
    
    class Meta:
        model = SigningCertificate
        fields = '__all__'
        widgets = {
            'certificate_file': forms.FileInput(attrs={
                'accept': '.pem,.crt,.cer,.der',
                'class': 'form-control'
            }),
            'private_key_file': forms.FileInput(attrs={
                'accept': '.pem,.key,.der',
                'class': 'form-control'
            }),
            'validation_warnings': forms.Textarea(attrs={
                'rows': 4,
                'readonly': True,
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels and help text
        self.fields['certificate_name'].help_text = "A descriptive name for this certificate"
        self.fields['certificate_file'].help_text = (
            "Upload X.509 certificate file. Supported formats: PEM (.pem, .crt, .cer) or DER (.der). "
            "Maximum file size: 10MB."
        )
        self.fields['private_key_file'].help_text = (
            "Optional: Upload corresponding private key file. Required for signing operations. "
            "Supported formats: PEM (.pem, .key) or DER (.der). Maximum file size: 10MB."
        )
        
        # Make auto-populated fields readonly in form
        readonly_fields = [
            'subject', 'issuer', 'serial_number', 'fingerprint', 
            'signature_algorithm', 'valid_from', 'valid_to',
            'validation_status', 'validation_warnings'
        ]
        
        for field_name in readonly_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['readonly'] = True
                self.fields[field_name].help_text = "Auto-populated from certificate"

    def clean_certificate_file(self):
        """Validate certificate file upload"""
        certificate_file = self.cleaned_data.get('certificate_file')
        
        if certificate_file:
            try:
                # This will validate and extract certificate info
                validate_certificate_file(certificate_file)
                # Reset file pointer for later use
                certificate_file.seek(0)
            except ValidationError as e:
                raise forms.ValidationError(f"Certificate validation failed: {e}")
        
        return certificate_file

    def clean_private_key_file(self):
        """Validate private key file upload"""
        private_key_file = self.cleaned_data.get('private_key_file')
        
        if private_key_file:
            try:
                validate_private_key_file(private_key_file)
                # Reset file pointer for later use
                private_key_file.seek(0)
            except ValidationError as e:
                raise forms.ValidationError(f"Private key validation failed: {e}")
        
        return private_key_file

    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        certificate_file = cleaned_data.get('certificate_file')
        is_default = cleaned_data.get('is_default')
        
        # If setting as default, ensure certificate is valid
        if is_default and certificate_file:
            try:
                from .certificate_validators import CertificateValidator
                validator = CertificateValidator(certificate_file)
                result = validator.validate_for_smp_signing()
                
                # Reset file pointer
                certificate_file.seek(0)
                
                # Check if certificate has any critical issues
                if not result.get('is_valid', False):
                    raise forms.ValidationError(
                        "Cannot set an invalid certificate as default. "
                        "Please resolve validation issues first."
                    )
            except Exception as e:
                raise forms.ValidationError(f"Cannot validate certificate for default use: {e}")
        
        return cleaned_data
