# Azure FHIR Security Configuration

## Overview

All Azure FHIR credentials are now stored securely in the `.env` file, which is **automatically excluded from version control** via `.gitignore`.

## Security Changes Made

### 1. Environment Variables Created

Add these to your `.env` file:

```bash
# FHIR Provider
FHIR_PROVIDER=AZURE

# Azure FHIR Service Configuration
AZURE_FHIR_BASE_URL=https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com
AZURE_FHIR_TENANT_ID=fc6570ff-7089-4cc9-9ef4-7be53d282a64
AZURE_FHIR_SUBSCRIPTION_ID=bf2baefd-7a32-405d-8593-d39825c09525
AZURE_FHIR_RESOURCE_GROUP=fhir-resource-group
AZURE_FHIR_WORKSPACE=healtthdata
AZURE_FHIR_SERVICE_NAME=dev-fhir-service
```

### 2. Files Modified

**✅ `azure_fhir_config.py`:**
- Now loads credentials from environment variables
- No hardcoded secrets
- Validates configuration on import

**✅ `eu_ncp_server/services/azure_fhir_integration.py`:**
- Uses `os.getenv()` for all Azure credentials
- Includes validation to ensure credentials are set
- Raises clear error if .env is missing

**✅ `.env.example`:**
- Updated with Azure FHIR placeholder values
- Documents all required variables
- Safe to commit (contains no real credentials)

**✅ `.env.azure` (NEW):**
- Temporary file with your actual Azure credentials
- **Copy to `.env` and then DELETE this file**
- Already in `.gitignore` for safety

### 3. Security Verification

**✅ Protected Files:**
```
.env              ← Your actual secrets (gitignored)
.env.local        ← Alternative secrets location (gitignored)
.env.production   ← Production secrets (gitignored)
.env.azure        ← Temporary Azure secrets (gitignored)
```

**✅ Safe Files (can be committed):**
```
.env.example      ← Template with placeholders
.env.secure.example ← Additional template
```

**✅ `.gitignore` Already Configured:**
```gitignore
# Environment Variables
.env
.env.local
.env.development
.env.test
.env.production
```

## Setup Instructions

### Step 1: Create Your .env File

```powershell
# Copy the template
Copy-Item .env.example .env

# Or if you have .env.azure
Copy-Item .env.azure .env
```

### Step 2: Add Azure FHIR Credentials

Edit `.env` and add:

```bash
FHIR_PROVIDER=AZURE
AZURE_FHIR_BASE_URL=https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com
AZURE_FHIR_TENANT_ID=fc6570ff-7089-4cc9-9ef4-7be53d282a64
AZURE_FHIR_SUBSCRIPTION_ID=bf2baefd-7a32-405d-8593-d39825c09525
AZURE_FHIR_RESOURCE_GROUP=fhir-resource-group
AZURE_FHIR_WORKSPACE=healtthdata
AZURE_FHIR_SERVICE_NAME=dev-fhir-service
```

### Step 3: Verify Git Ignore

```powershell
# Check that .env is NOT tracked
git status

# If .env appears, it should say "Untracked" or not appear at all
# If it says "Changes not staged", you need to remove it:
git rm --cached .env
```

### Step 4: Delete Temporary Files

```powershell
# After copying to .env, delete the temporary file
Remove-Item .env.azure
```

### Step 5: Test Configuration

```powershell
# Run Django shell to verify
python manage.py shell

# In shell:
from eu_ncp_server.services.azure_fhir_integration import AzureFHIRIntegrationService
service = AzureFHIRIntegrationService()
print(f"Base URL: {service.base_url}")
print(f"Tenant ID: {service.tenant_id[:8]}...")  # Only show first 8 chars
```

## Security Best Practices

### ✅ DO:
- Store all secrets in `.env` file
- Keep `.env` in `.gitignore`
- Use different `.env` files for dev/staging/production
- Rotate credentials regularly
- Use Azure Key Vault for production deployments
- Review `.gitignore` before committing
- Use `git status` to verify no secrets are staged

### ❌ DON'T:
- Hardcode credentials in Python files
- Commit `.env` to version control
- Share `.env` files via email/chat
- Store `.env` in cloud sync folders (Dropbox, OneDrive)
- Use production credentials in development
- Log full credentials (only log first few characters)

## Azure Authentication Methods

### Current: Azure CLI (Development)
```powershell
az login
az account set --subscription bf2baefd-7a32-405d-8593-d39825c09525
```

**Pros:**
- Simple for local development
- No credential management needed
- Uses your Azure identity

**Cons:**
- Requires Azure CLI installed
- Not suitable for production
- Manual login required

### Production: Service Principal (Recommended)

For production, use a Service Principal with client credentials:

1. **Create Service Principal:**
```powershell
az ad sp create-for-rbac --name "Django-NCP-FHIR-Access" \
  --role "FHIR Data Contributor" \
  --scopes /subscriptions/bf2baefd-7a32-405d-8593-d39825c09525/resourceGroups/fhir-resource-group
```

2. **Add to .env:**
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=fc6570ff-7089-4cc9-9ef4-7be53d282a64
```

3. **Update Service to Use Client Credentials:**
```python
# In azure_fhir_integration.py
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=os.getenv('AZURE_TENANT_ID'),
    client_id=os.getenv('AZURE_CLIENT_ID'),
    client_secret=os.getenv('AZURE_CLIENT_SECRET')
)
```

## Credential Rotation

### When to Rotate:
- Every 90 days (recommended)
- After team member departure
- If credentials potentially exposed
- Before production deployment

### How to Rotate:
1. Generate new Service Principal credentials in Azure Portal
2. Update `.env` file with new values
3. Test with new credentials
4. Delete old credentials from Azure

## Emergency: Credential Exposure

If credentials are accidentally committed:

1. **Immediately rotate credentials in Azure Portal**
2. **Remove from Git history:**
```powershell
# Use BFG Repo-Cleaner or git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

3. **Force push to remote:**
```powershell
git push origin --force --all
git push origin --force --tags
```

4. **Notify team to re-clone repository**

## Verification Checklist

- [ ] `.env` file created with Azure credentials
- [ ] `.env` is in `.gitignore`
- [ ] `git status` shows `.env` as untracked
- [ ] No hardcoded credentials in Python files
- [ ] Azure FHIR service accessible with credentials
- [ ] `.env.azure` deleted after copying
- [ ] Django shell test passes
- [ ] Ready to upload patient bundles

## Support

For Azure FHIR access issues:
- Check Azure Portal → Healthcare APIs → Access Control (IAM)
- Verify "FHIR Data Contributor" role assigned
- Ensure Public Network Access is enabled
- Check Azure AD authentication logs

For Django configuration issues:
- Verify `.env` file exists in project root
- Check `dotenv` package installed: `pip show python-dotenv`
- Ensure `load_dotenv()` called before accessing variables
- Test with `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AZURE_FHIR_BASE_URL'))"`
