# Azure FHIR Authentication Setup Guide

This guide explains how to configure authentication for Azure FHIR service in Django_NCP.

## Authentication Methods

The application supports **three authentication methods** in priority order:

### 1. Service Principal (Recommended for Production)
Best for: Production environments, CI/CD, unattended operation

**Pros:**
- ✅ No interactive login required
- ✅ Works in automated/background processes
- ✅ Secure credential rotation
- ✅ Fine-grained access control

**Setup Steps:**

#### Step 1: Create Service Principal
```powershell
# Login to Azure
az login

# Create a Service Principal for your FHIR service
az ad sp create-for-rbac --name "django-ncp-fhir-client" --role "FHIR Data Contributor" --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE/fhirservices/YOUR_FHIR_SERVICE"
```

This command will output:
```json
{
  "appId": "12345678-1234-1234-1234-123456789abc",
  "displayName": "django-ncp-fhir-client",
  "password": "your-secret-here",
  "tenant": "your-tenant-id"
}
```

#### Step 2: Add to .env File
```env
AZURE_FHIR_CLIENT_ID=12345678-1234-1234-1234-123456789abc
AZURE_FHIR_CLIENT_SECRET=your-secret-here
```

#### Step 3: Verify Access
```powershell
# Test with your new credentials
python test_azure_connection.py
```

### 2. Managed Identity (Recommended for Azure-Hosted Apps)
Best for: Azure VM, App Service, Container Instances, AKS

**Pros:**
- ✅ No credentials to manage
- ✅ Automatic credential rotation
- ✅ Most secure option
- ✅ Zero configuration in code

**Setup Steps:**

#### Step 1: Enable Managed Identity
```powershell
# For Azure App Service
az webapp identity assign --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP

# For Azure VM
az vm identity assign --name YOUR_VM_NAME --resource-group YOUR_RESOURCE_GROUP
```

#### Step 2: Grant FHIR Access
```powershell
# Get the managed identity's principal ID
$principalId = (az webapp identity show --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP --query principalId -o tsv)

# Assign FHIR Data Contributor role
az role assignment create --assignee $principalId --role "FHIR Data Contributor" --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE/fhirservices/YOUR_FHIR_SERVICE"
```

#### Step 3: Deploy Application
No .env configuration needed - authentication happens automatically!

### 3. Azure CLI (Development Only)
Best for: Local development, testing

**Pros:**
- ✅ Quick to set up
- ✅ Uses your personal Azure credentials
- ✅ Good for development/debugging

**Cons:**
- ❌ Requires interactive login
- ❌ Not suitable for production
- ❌ Session expires after ~90 days

**Setup Steps:**

```powershell
# Login to Azure
az login

# Test connection
python test_azure_connection.py
```

## Configuration Priority

The application tries authentication methods in this order:
1. **Service Principal** (if `AZURE_FHIR_CLIENT_ID` and `AZURE_FHIR_CLIENT_SECRET` are set)
2. **Managed Identity** (if running on Azure with managed identity enabled)
3. **Azure CLI** (if `az login` has been run)

## Required Azure Roles

Your authentication principal (Service Principal, Managed Identity, or user) needs one of these roles:

- **FHIR Data Contributor** - Read/Write access (recommended)
- **FHIR Data Reader** - Read-only access
- **FHIR Data Writer** - Write-only access

### Assign Roles

```powershell
# For Service Principal
az role assignment create \
  --assignee YOUR_CLIENT_ID \
  --role "FHIR Data Contributor" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE/fhirservices/YOUR_FHIR_SERVICE"

# For Managed Identity (use principalId)
az role assignment create \
  --assignee YOUR_PRINCIPAL_ID \
  --role "FHIR Data Contributor" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE/fhirservices/YOUR_FHIR_SERVICE"

# For your user account
az role assignment create \
  --assignee YOUR_EMAIL@DOMAIN.COM \
  --role "FHIR Data Contributor" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/YOUR_RESOURCE_GROUP/providers/Microsoft.HealthcareApis/workspaces/YOUR_WORKSPACE/fhirservices/YOUR_FHIR_SERVICE"
```

## Environment Variables

### Required (All Methods)
```env
FHIR_PROVIDER=AZURE
AZURE_FHIR_BASE_URL=https://your-fhir-service.fhir.azurehealthcareapis.com
AZURE_FHIR_TENANT_ID=your-azure-tenant-id
```

### Optional (Service Principal)
```env
AZURE_FHIR_CLIENT_ID=your-service-principal-client-id
AZURE_FHIR_CLIENT_SECRET=your-service-principal-secret
```

### Optional (Metadata)
```env
AZURE_FHIR_SUBSCRIPTION_ID=your-azure-subscription-id
AZURE_FHIR_RESOURCE_GROUP=your-resource-group
AZURE_FHIR_WORKSPACE=your-workspace-name
AZURE_FHIR_SERVICE_NAME=your-fhir-service-name
```

## Testing Authentication

Use the test script to verify your authentication setup:

```powershell
python test_azure_connection.py
```

Expected output:
```
=== Testing FHIR Connection ===

FHIR Provider: AZURE
Using service: AzureFHIRIntegrationService
Azure AD token acquired via Service Principal

2. Testing Patient Search:
   ✅ Connection successful!
   Found 1 patients

3. Testing Patient Document Search:
   ✅ Found 2 documents
```

## Troubleshooting

### "Azure authentication failed"
**Cause:** No authentication method succeeded
**Solution:** Configure at least one method (Service Principal recommended)

### "Service Principal auth failed: 401"
**Cause:** Invalid client ID or secret
**Solution:** Verify credentials in .env match Azure portal

### "AADSTS700016: Application not found"
**Cause:** Service Principal doesn't exist or was deleted
**Solution:** Recreate Service Principal using steps above

### "Managed Identity not available"
**Cause:** Not running on Azure or managed identity not enabled
**Solution:** Enable managed identity on your Azure resource

### "Azure CLI failed: Please run 'az login'"
**Cause:** Not logged in to Azure CLI
**Solution:** Run `az login` or configure Service Principal instead

### "Forbidden: User does not have permission"
**Cause:** Missing FHIR role assignment
**Solution:** Assign "FHIR Data Contributor" role to your principal

## Security Best Practices

1. **Production:** Always use Service Principal or Managed Identity
2. **Secrets:** Store `AZURE_FHIR_CLIENT_SECRET` in Azure Key Vault
3. **Rotation:** Rotate Service Principal secrets regularly (90-180 days)
4. **Permissions:** Use least privilege (FHIR Data Reader if read-only)
5. **Monitoring:** Enable Azure AD audit logs for authentication events

## Quick Setup for Production

```powershell
# 1. Create Service Principal
$sp = az ad sp create-for-rbac --name "django-ncp-fhir" --role "FHIR Data Contributor" --scopes "/subscriptions/bf2baefd-7a32-405d-8593-d39825c09525/resourceGroups/fhir-resource-group/providers/Microsoft.HealthcareApis/workspaces/healtthdata/fhirservices/dev-fhir-service" | ConvertFrom-Json

# 2. Update .env file
@"
AZURE_FHIR_CLIENT_ID=$($sp.appId)
AZURE_FHIR_CLIENT_SECRET=$($sp.password)
"@ | Add-Content .env

# 3. Test connection
python test_azure_connection.py

# 4. Save credentials securely
Write-Host "⚠️ SAVE THESE CREDENTIALS SECURELY:"
Write-Host "Client ID: $($sp.appId)"
Write-Host "Secret: $($sp.password)"
Write-Host "You won't be able to retrieve the secret again!"
```

## Reference

- [Azure FHIR Service Authentication](https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/get-started-with-fhir)
- [Service Principal Best Practices](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal)
- [Managed Identity Overview](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
