# Azure FHIR RBAC Permission Setup

## Issue

You're getting a **403 Forbidden** error when uploading to Azure FHIR:
```
"Authorization failed."
```

This means your user account **duncan.niamh@gmail.com** doesn't have the required permissions to write data to the FHIR service.

## Solution: Assign FHIR Data Contributor Role

You need the **FHIR Data Contributor** role assigned to your FHIR service.

### Option 1: Azure Portal (Recommended)

1. **Go to Azure Portal**: https://portal.azure.com

2. **Navigate to your FHIR Service**:
   - Search for "healtthdata" workspace
   - Or go to: Resource Groups → fhir-resource-group → healtthdata → dev-fhir-service

3. **Open Access Control (IAM)**:
   - Click on "Access control (IAM)" in the left menu

4. **Add Role Assignment**:
   - Click "+ Add" → "Add role assignment"
   - Search for "FHIR Data Contributor"
   - Click "FHIR Data Contributor" → Click "Next"

5. **Select Members**:
   - Click "+ Select members"
   - Search for your email: **duncan.niamh@gmail.com**
   - Select your account
   - Click "Select"

6. **Review + Assign**:
   - Click "Review + assign"
   - Click "Review + assign" again to confirm

7. **Wait 2-3 minutes** for permissions to propagate

### Option 2: Azure CLI (If you have Owner/Contributor role)

First, get your object ID:

```powershell
# Get your user object ID
$userId = az ad user show --id "duncan.niamh@gmail.com" --query id --output tsv

# Assign FHIR Data Contributor role
az role assignment create `
  --role "FHIR Data Contributor" `
  --assignee $userId `
  --scope "/subscriptions/bf2baefd-7a32-405d-8593-d39825c09525/resourceGroups/fhir-resource-group/providers/Microsoft.HealthcareApis/workspaces/healtthdata/fhirservices/dev-fhir-service"
```

### Option 3: Ask Azure Subscription Owner

If you don't have permission to assign roles:

1. Contact your Azure subscription owner
2. Ask them to assign **FHIR Data Contributor** role to **duncan.niamh@gmail.com**
3. Provide them with:
   - **Subscription**: Dev Subscription (bf2baefd-7a32-405d-8593-d39825c09525)
   - **Resource Group**: fhir-resource-group
   - **FHIR Service**: healtthdata/dev-fhir-service
   - **Role**: FHIR Data Contributor
   - **User**: duncan.niamh@gmail.com

## Available FHIR Roles

| Role | Permissions | Use Case |
|------|------------|----------|
| **FHIR Data Reader** | Read-only access to FHIR data | Query patients, view records |
| **FHIR Data Writer** | Write access to FHIR data | Upload new resources |
| **FHIR Data Contributor** | Full read/write access | Upload bundles, modify data |
| **FHIR Data Exporter** | Export FHIR data | Bulk data export |

**Recommended**: **FHIR Data Contributor** (full read/write)

## Verify Role Assignment

After assigning the role, verify it worked:

```powershell
# Check your role assignments on the FHIR service
az role assignment list `
  --scope "/subscriptions/bf2baefd-7a32-405d-8593-d39825c09525/resourceGroups/fhir-resource-group/providers/Microsoft.HealthcareApis/workspaces/healtthdata/fhirservices/dev-fhir-service" `
  --query "[].{Role:roleDefinitionName, Principal:principalName}" `
  --output table
```

Expected output:
```
Role                    Principal
----------------------  ------------------------
FHIR Data Contributor   duncan.niamh@gmail.com
```

## Test Upload After Role Assignment

Once the role is assigned and permissions have propagated (2-3 minutes):

```powershell
# Retry the upload
.venv\Scripts\python.exe upload_patient_to_azure_fhir.py
```

Expected output:
```
[STEP 6] Uploading transaction bundle to Azure FHIR Service
  Status Code: 200
  Result: SUCCESS
  Resources Created: 43
  Resources Updated: 1
```

## Troubleshooting

### "Authorization failed" persists
- **Wait 5 minutes** - Role assignments can take time to propagate
- **Re-login to Azure**: `az logout` then `az login --tenant fc6570ff-7089-4cc9-9ef4-7be53d282a64`
- **Get fresh token**: Close terminal, open new one, run script again

### "Cannot find user or service principal"
- Use Azure Portal method (Option 1) instead
- Your account may not have Microsoft Graph API permissions

### "Access denied" when assigning role
- You don't have Owner/Contributor role on the subscription
- Ask subscription owner to assign the role (Option 3)

### Check current subscription
```powershell
az account show --query "{Name:name, SubscriptionId:id}" --output table
```

Should show:
```
Name              SubscriptionId
----------------  ------------------------------------
Dev Subscription  bf2baefd-7a32-405d-8593-d39825c09525
```

## Next Steps

1. ✅ **Assign FHIR Data Contributor role** (via Azure Portal)
2. ⏳ **Wait 2-3 minutes** for permissions to propagate
3. 🔄 **Retry upload**: `.venv\Scripts\python.exe upload_patient_to_azure_fhir.py`
4. ✅ **Verify patient**: Check Azure FHIR for patient 2-1234-W7
5. 🎉 **Test Django app**: Search for Diana Ferreira with deduplicated medications

## Security Note

The **FHIR Data Contributor** role gives you full read/write access to all FHIR data in the service. This is appropriate for:
- ✅ Development environments
- ✅ Testing and debugging
- ✅ Administrative tasks

For production, consider:
- Use service principals with specific scopes
- Implement Azure AD authentication in Django app
- Use more restrictive roles where possible
