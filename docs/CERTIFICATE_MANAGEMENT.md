# SMP Certificate Management System

## Overview

The Django NCP application now includes a comprehensive certificate management system for uploading, validating, and managing X.509 certificates used for SMP (Service Metadata Publisher) document signing.

## Features

### 🔒 Certificate Upload & Validation

- **Automatic validation** of uploaded certificates for SMP signing compatibility
- **Format support**: PEM (.pem, .crt, .cer) and DER (.der) formats
- **Information extraction**: Automatically extracts certificate details (subject, issuer, validity dates, etc.)
- **Security checks**: Validates key algorithms, sizes, and usage extensions

### 📊 Enhanced Admin Interface

- **Visual status indicators** for certificate validity
- **Validation warnings** for certificates with non-critical issues
- **Bulk actions** for re-validation and setting default certificates
- **Improved UI** with custom styling and help text

### 🛡️ Security Validation

The system performs comprehensive validation checks:

#### ✅ Required Validations

- **Expiration check**: Certificate must be currently valid (not expired)
- **Key usage**: Must allow digital signatures
- **Key algorithm**: RSA or ECDSA supported
- **Key size**: RSA minimum 2048 bits, ECDSA with standard curves

#### ⚠️ Warning Validations

- **Key size recommendations**: RSA 3072+ bits recommended
- **Missing extensions**: Warns about missing recommended extensions
- **Unusual algorithms**: Flags non-standard key algorithms

## Usage Guide

### Uploading a New Certificate

1. **Navigate to Admin**: Go to `/admin/smp_client/signingcertificate/`
2. **Add Certificate**: Click "ADD SIGNING CERTIFICATE +"
3. **Fill Details**:
   - **Certificate Name**: Descriptive name for the certificate
   - **Certificate Type**: Usually "X.509" (default)
   - **Certificate File**: Upload your .pem/.crt/.cer/.der certificate file
   - **Private Key File**: Optional - upload corresponding private key

4. **Automatic Validation**: Upon upload, the system will:
   - Validate certificate format and content
   - Extract certificate information automatically
   - Check compatibility for SMP signing
   - Set validation status

5. **Review Results**: Check the validation status and any warnings

### Certificate Status Types

| Status | Description | Actions Available |
|--------|-------------|-------------------|
| ✅ **Valid** | Certificate passes all validation checks | Can set as default |
| ⚠️ **Valid (Warnings)** | Minor issues but usable for signing | Can set as default |
| ❌ **Invalid** | Failed critical validation checks | Cannot set as default |
| ⏰ **Expired** | Certificate has expired | Cannot set as default |

### Setting Default Certificate

Only one certificate can be set as the default signing certificate:

1. **Method 1**: Check "Is default" when uploading/editing a certificate
2. **Method 2**: Use the "Set as default certificate" bulk action
3. **Requirement**: Certificate must have "Valid" or "Valid (Warnings)" status

### Admin Actions

- **Re-validate certificates**: Re-runs validation on selected certificates
- **Set as default certificate**: Sets a single valid certificate as default

## File Requirements

### Certificate Files

- **Formats**: PEM (.pem, .crt, .cer) or DER (.der)
- **Max size**: 10MB
- **Content**: Valid X.509 certificate
- **Key requirements**: RSA 2048+ bits or ECDSA with standard curves

### Private Key Files

- **Formats**: PEM (.pem, .key) or DER (.der)
- **Max size**: 10MB
- **Requirement**: Optional but needed for actual signing operations
- **Security**: Stored in `certificates/private/` directory

## Validation Details

### Critical Checks (Must Pass)

1. **Valid certificate format** (PEM or DER)
2. **Currently valid** (not expired)
3. **Digital signature capability** (Key Usage extension)
4. **Adequate key size** (RSA ≥2048 bits, ECDSA standard curves)

### Warning Checks (Recommended)

1. **Key cert sign usage** (may not be required for document signing)
2. **Recommended extensions** (basicConstraints, keyIdentifier, etc.)
3. **Key size recommendations** (RSA ≥3072 bits)
4. **Standard algorithms** (widely supported curves/algorithms)

## Troubleshooting

### Common Issues

**"Certificate validation failed: Invalid certificate format"**

- Check file format (must be PEM or DER)
- Verify file is not corrupted
- Ensure file contains a valid X.509 certificate

**"Certificate has expired"**

- Certificate validity period has passed
- Upload a current, valid certificate

**"RSA key size X is too small (minimum 2048)"**

- Certificate uses weak RSA key
- Generate new certificate with RSA 2048+ bits

**"Certificate does not allow digital signatures"**

- Key Usage extension doesn't include digitalSignature
- Certificate may not be suitable for document signing

### Getting Help

1. **Check validation warnings** in the admin interface
2. **Review certificate details** in the collapsed sections
3. **Verify certificate with external tools** (openssl, etc.)
4. **Contact system administrator** for certificate generation assistance

## API Integration

The certificate validation system integrates with:

- **SMP client operations** for document signing
- **Django admin interface** for management
- **Validation APIs** for programmatic certificate checking

## Security Notes

- **Private keys** are stored securely in `certificates/private/`
- **File uploads** are validated for size and format
- **Certificate content** is parsed safely using cryptography library
- **Access control** through Django admin permissions

---

For technical support or certificate generation assistance, please contact your system administrator.
