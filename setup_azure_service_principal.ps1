# Azure FHIR Service Principal Setup Script
# This script creates a Service Principal with FHIR Data Contributor access
# and updates your .env file with the credentials

Write-Host "`n=== Azure FHIR Service Principal Setup ===" -ForegroundColor Cyan
Write-Host "This script will create a Service Principal for unattended Azure FHIR access`n"

# Load existing .env values
$envFile = ".env"
if (Test-Path $envFile) {
    Write-Host "✓ Found .env file" -ForegroundColor Green
    
    # Parse current values
    $envContent = Get-Content $envFile -Raw
    
    # Extract Azure FHIR configuration
    if ($envContent -match 'AZURE_FHIR_SUBSCRIPTION_ID=([^\r\n]+)') {
        $subscriptionId = $matches[1].Trim()
        Write-Host "  Subscription ID: $subscriptionId"
    }
    
    if ($envContent -match 'AZURE_FHIR_RESOURCE_GROUP=([^\r\n]+)') {
        $resourceGroup = $matches[1].Trim()
        Write-Host "  Resource Group: $resourceGroup"
    }
    
    if ($envContent -match 'AZURE_FHIR_WORKSPACE=([^\r\n]+)') {
        $workspace = $matches[1].Trim()
        Write-Host "  Workspace: $workspace"
    }
    
    if ($envContent -match 'AZURE_FHIR_SERVICE_NAME=([^\r\n]+)') {
        $serviceName = $matches[1].Trim()
        Write-Host "  FHIR Service: $serviceName"
    }
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "  Please create .env file from .env.example first"
    exit 1
}

# Validate required values
if (-not $subscriptionId -or -not $resourceGroup -or -not $workspace -or -not $serviceName) {
    Write-Host "`n✗ Missing Azure FHIR configuration in .env file" -ForegroundColor Red
    Write-Host "  Please ensure these variables are set:" -ForegroundColor Yellow
    Write-Host "    - AZURE_FHIR_SUBSCRIPTION_ID"
    Write-Host "    - AZURE_FHIR_RESOURCE_GROUP"
    Write-Host "    - AZURE_FHIR_WORKSPACE"
    Write-Host "    - AZURE_FHIR_SERVICE_NAME"
    exit 1
}

# Build FHIR service scope
$fhirScope = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.HealthcareApis/workspaces/$workspace/fhirservices/$serviceName"

Write-Host "`n--- Configuration ---" -ForegroundColor Yellow
Write-Host "FHIR Service Scope: $fhirScope"
Write-Host "Role: FHIR Data Contributor`n"

# Confirm
$confirm = Read-Host "Create Service Principal? Enter yes or no"
if ($confirm -ne "yes") {
    Write-Host "Operation cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n--- Creating Service Principal ---" -ForegroundColor Cyan

try {
    # Check if Azure CLI is installed
    $azVersion = az --version 2>$null
    if (-not $azVersion) {
        Write-Host "✗ Azure CLI not found!" -ForegroundColor Red
        Write-Host "  Please install Azure CLI from: https://aka.ms/azure-cli"
        exit 1
    }
    
    Write-Host "✓ Azure CLI detected" -ForegroundColor Green
    
    # Check if logged in
    Write-Host "Checking Azure CLI login status..."
    $account = az account show 2>$null | ConvertFrom-Json
    
    if (-not $account) {
        Write-Host "Not logged in to Azure. Running 'az login'..."
        az login
        
        $account = az account show 2>$null | ConvertFrom-Json
        if (-not $account) {
            Write-Host "✗ Azure login failed" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host "✓ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "  Subscription: $($account.name)"
    
    # Set active subscription
    Write-Host "`nSetting active subscription..."
    az account set --subscription $subscriptionId
    
    # Create Service Principal
    Write-Host "`nCreating Service Principal with FHIR Data Contributor role..."
    $spName = "django-ncp-fhir-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    $spJson = az ad sp create-for-rbac `
        --name $spName `
        --role "FHIR Data Contributor" `
        --scopes $fhirScope `
        2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Service Principal creation failed!" -ForegroundColor Red
        Write-Host $spJson
        exit 1
    }
    
    $sp = $spJson | ConvertFrom-Json
    
    Write-Host "✓ Service Principal created successfully!" -ForegroundColor Green
    Write-Host "  Name: $spName"
    Write-Host "  Client ID: $($sp.appId)"
    Write-Host "  Tenant ID: $($sp.tenant)"
    
    # Update .env file
    Write-Host "`n--- Updating .env File ---" -ForegroundColor Cyan
    
    # Read current .env content
    $envLines = Get-Content $envFile
    
    # Check if credentials already exist
    $hasClientId = $envLines | Where-Object { $_ -match '^AZURE_FHIR_CLIENT_ID=' }
    $hasClientSecret = $envLines | Where-Object { $_ -match '^AZURE_FHIR_CLIENT_SECRET=' }
    
    if ($hasClientId -or $hasClientSecret) {
        Write-Host "⚠️  Existing credentials found in .env file" -ForegroundColor Yellow
        $overwrite = Read-Host "Overwrite existing credentials? (yes/no)"
        
        if ($overwrite -ne "yes") {
            Write-Host "`nService Principal created but .env not updated"
            Write-Host "Manually add these credentials to your .env file:" -ForegroundColor Yellow
            Write-Host "AZURE_FHIR_CLIENT_ID=$($sp.appId)"
            Write-Host "AZURE_FHIR_CLIENT_SECRET=$($sp.password)"
            exit 0
        }
        
        # Remove existing credentials
        $envLines = $envLines | Where-Object { 
            $_ -notmatch '^AZURE_FHIR_CLIENT_ID=' -and 
            $_ -notmatch '^AZURE_FHIR_CLIENT_SECRET=' 
        }
    }
    
    # Find insertion point (after AZURE_FHIR_SERVICE_NAME)
    $insertIndex = -1
    for ($i = 0; $i -lt $envLines.Count; $i++) {
        if ($envLines[$i] -match '^AZURE_FHIR_SERVICE_NAME=') {
            $insertIndex = $i + 1
            break
        }
    }
    
    # Add credentials
    if ($insertIndex -ge 0) {
        # Insert after service name
        $newLines = @()
        $newLines += $envLines[0..($insertIndex-1)]
        $newLines += ""
        $newLines += "# Service Principal Authentication (generated $(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
        $newLines += "AZURE_FHIR_CLIENT_ID=$($sp.appId)"
        $newLines += "AZURE_FHIR_CLIENT_SECRET=$($sp.password)"
        
        if ($insertIndex -lt $envLines.Count) {
            $newLines += $envLines[$insertIndex..($envLines.Count-1)]
        }
        
        $envLines = $newLines
    } else {
        # Append to end
        $envLines += ""
        $envLines += "# Service Principal Authentication (generated $(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
        $envLines += "AZURE_FHIR_CLIENT_ID=$($sp.appId)"
        $envLines += "AZURE_FHIR_CLIENT_SECRET=$($sp.password)"
    }
    
    # Write updated .env file
    $envLines | Set-Content $envFile -Encoding UTF8
    
    Write-Host "✓ Credentials added to .env file" -ForegroundColor Green
    
    # Test connection
    Write-Host "`n--- Testing Connection ---" -ForegroundColor Cyan
    $test = Read-Host "Test FHIR connection now? (yes/no)"
    
    if ($test -eq "yes") {
        Write-Host "Running connection test..."
        & .venv\Scripts\python.exe test_azure_connection.py
    }
    
    # Success summary
    Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
    Write-Host "✓ Service Principal created: $spName"
    Write-Host "✓ FHIR Data Contributor role assigned"
    Write-Host "✓ Credentials saved to .env file"
    Write-Host "`n⚠️  IMPORTANT: Save these credentials securely!" -ForegroundColor Yellow
    Write-Host "   Client ID: $($sp.appId)"
    Write-Host "   Tenant ID: $($sp.tenant)"
    Write-Host "   You won't be able to retrieve the secret again!`n"
    
    # Security reminder
    Write-Host "Security Reminders:" -ForegroundColor Yellow
    Write-Host "  • Rotate credentials every 90-180 days"
    Write-Host "  • Never commit .env file to git"
    Write-Host "  • Consider using Azure Key Vault for production"
    Write-Host "  • Monitor authentication logs in Azure AD`n"
    
} catch {
    Write-Host "`n✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
