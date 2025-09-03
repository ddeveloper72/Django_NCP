# Certificate Upload Guide

## Enhanced Certificate Management System

The SMP client now includes a comprehensive certificate management system with advanced validation and error handling.

## Features

### ✅ What's Working

- **Certificate Upload**: Upload X.509 certificates through the Django admin interface
- **Format Support**: Supports both PEM (.pem, .crt, .cer, .cert) and DER (.der) formats
- **Automatic Validation**: Validates certificates for SMP signing compatibility
- **Error Handling**: Provides detailed error messages for troubleshooting
- **Format Cleaning**: Automatically handles common formatting issues

### 🔧 Recent Improvements

- **Enhanced PEM Parsing**: Handles malformed PEM files with better error messages
- **Format Cleaning**: Removes Windows line endings, extra whitespace, and BOM markers
- **Fallback Logic**: Attempts PEM parsing first, then falls back to DER format
- **Detailed Errors**: Specific guidance on certificate format requirements

## How to Upload a Certificate

1. **Access Admin Interface**: Go to Django admin → SMP Client → Signing Certificates
2. **Add New Certificate**: Click "Add Signing Certificate"
3. **Upload File**: Select your certificate file (.pem, .crt, .cer, .der)
4. **Automatic Validation**: The system will validate the certificate automatically
5. **Review Status**: Check the validation status and any error messages

## Supported File Formats

### PEM Format (Recommended)

```
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
...certificate data...
-----END CERTIFICATE-----
```

### DER Format

Binary format - system will auto-detect and handle

## Common Issues and Solutions

### ValidationError: MalformedFraming

**Problem**: Certificate file has formatting issues
**Solution**: The system now automatically cleans common formatting problems including:

- Windows line endings (`\r\n`)
- Extra whitespace and empty lines
- Byte Order Mark (BOM) characters

### Invalid File Extension

**Problem**: File doesn't have a recognized certificate extension
**Solution**: Rename your file to use: `.pem`, `.crt`, `.cer`, `.cert`, or `.der`

### Certificate Not Valid for SMP Signing

**Problem**: Certificate lacks required properties for SMP signing
**Solution**: Ensure your certificate has:

- Valid digital signature capability
- Appropriate key usage extensions
- Current validity period (not expired)

## Certificate Requirements for SMP

For a certificate to be valid for SMP signing, it must:

1. **Be properly formatted** as X.509
2. **Have digital signature capability**
3. **Be within validity period** (not expired)
4. **Have appropriate key usage** for signing
5. **Be issued by a trusted authority** (recommended)

## Admin Interface Features

### Status Indicators

- 🟢 **Valid**: Certificate passed all validation checks
- 🟡 **Warning**: Certificate has minor issues but may work
- 🔴 **Invalid**: Certificate failed validation
- ⚪ **Pending**: Validation not yet completed

### Bulk Actions

- Validate multiple certificates at once
- Export certificate information
- Bulk delete invalid certificates

## Troubleshooting

If you encounter issues:

1. **Check the error message** - The system provides detailed feedback
2. **Verify file format** - Ensure it's a valid X.509 certificate
3. **Try PEM format** - Convert DER to PEM if needed
4. **Check file size** - Maximum 10MB per file
5. **Contact support** - Include the specific error message

## Technical Details

The certificate validation system uses:

- **Python cryptography library** for X.509 parsing
- **Django file upload handling** for secure file processing
- **Custom validation logic** for SMP-specific requirements
- **Enhanced error handling** for better user experience

---

**Last Updated**: Certificate validation system enhanced with improved PEM format handling and detailed error messages.
