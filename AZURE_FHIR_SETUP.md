# Azure FHIR Service Integration Guide

## Overview

Switching from HAPI FHIR to your Azure Healthcare APIs FHIR service:
- **Service**: `healtthdata/dev-fhir-service`
- **Location**: West Europe
- **FHIR Version**: R4
- **Endpoint**: `https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com`

## Setup Steps

### 1. Install Azure CLI

**Windows PowerShell (Run as Administrator):**
```powershell
# Option A: Using Windows Package Manager
winget install -e --id Microsoft.AzureCLI

# Option B: Using MSI Installer
# Download from: https://aka.ms/installazurecliwindows
# Then run the installer
```

**Verify Installation:**
```powershell
az --version
```

### 2. Authenticate with Azure

```powershell
# Login to Azure
az login

# Set your subscription
az account set --subscription bf2baefd-7a32-405d-8593-d39825c09525

# Verify you're on the correct subscription
az account show
```

### 3. Upload Diana Ferreira Patient Bundle

```powershell
# From your Django project directory
.venv\Scripts\python.exe upload_patient_to_azure_fhir.py
```

This script will:
- Authenticate with Azure
- Load the Diana Ferreira bundle (44 resources)
- Update patient ID to `2-1234-W7`
- Upload to Azure FHIR service
- Verify the upload

### 4. Update Django Configuration

The following files have been created:

**Configuration:**
- `azure_fhir_config.py` - Azure FHIR connection details
- `eu_ncp_server/services/azure_fhir_integration.py` - Azure FHIR service class

**To switch Django to use Azure FHIR:**

1. Update `eu_ncp_server/settings.py`:
```python
# FHIR Configuration
FHIR_PROVIDER = 'AZURE'  # Changed from 'HAPI'
AZURE_FHIR_BASE_URL = 'https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com'
AZURE_FHIR_TENANT_ID = 'fc6570ff-7089-4cc9-9ef4-7be53d282a64'
```

2. Update service imports where needed to use `AzureFHIRIntegrationService` instead of `HAPIFHIRIntegrationService`

## Key Differences: HAPI vs Azure FHIR

| Feature | HAPI FHIR | Azure FHIR |
|---------|-----------|------------|
| **Authentication** | None (public test server) | Azure AD OAuth2 (required) |
| **Access Token** | Not needed | Required for every request |
| **Performance** | Slow/unreliable (public) | Fast/reliable (private) |
| **Data Persistence** | May be reset | Persistent |
| **Cost** | Free | Pay-per-use |
| **Security** | Public test server | Enterprise-grade security |

## Benefits of Azure FHIR

1. **Reliability**: No more timeouts or server resets
2. **Performance**: Faster response times, West Europe region
3. **Security**: OAuth2 authentication, private data
4. **Persistence**: Your patient data stays available
5. **GDPR Compliance**: EU data residency (West Europe)
6. **Integration**: Native Azure ecosystem integration

## Testing After Upload

Once the Diana Ferreira bundle is uploaded:

1. **Test Patient Search** in Django app:
   - Patient ID: `2-1234-W7`
   - Expected: Diana Ferreira patient record
   - Medications: ~5 unique (deduplicated from FHIR data)
   - All medications use CTS agent resolved names

2. **Verify Deduplication**:
   - Should see "Levothyroxine" (not both "Levothyroxine" AND "Eutirox")
   - Should see "Ipratropium and Salbutamol (combination)" (not duplicates)

3. **Check Clinical Data**:
   - Allergies, Conditions, Observations, Procedures, Immunizations
   - All should display with proper ATC code-based deduplication

## Troubleshooting

**If Azure CLI login fails:**
```powershell
# Clear cached credentials
az account clear

# Try interactive browser login
az login --use-device-code
```

**If token errors occur:**
```powershell
# Get fresh token manually
az account get-access-token --resource https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com
```

**If FHIR service is not accessible:**
- Verify "Public Network Access" is "Enabled" in Azure Portal
- Check firewall rules if IP restrictions are configured
- Verify your account has proper RBAC roles (FHIR Data Contributor)

## Next Steps

1. Install Azure CLI
2. Run `az login`
3. Upload Diana Ferreira bundle
4. Update Django configuration to use Azure FHIR
5. Test patient search with deduplicated, CTS-resolved medication names

All the code changes for deduplication and CTS agent priority are already implemented and will work with Azure FHIR!
