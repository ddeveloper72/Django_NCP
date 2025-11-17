# Upload Pregnancy Observations to Azure FHIR
# Run this script to upload the pregnancy data bundle

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Azure FHIR Pregnancy Data Upload Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration from .env
$AZURE_FHIR_BASE_URL = "https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"
$AZURE_FHIR_TENANT_ID = "fc6570ff-7089-4cc9-9ef4-7be53d282a64"
$AZURE_FHIR_RESOURCE = "https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"

Write-Host "`nStep 1: Getting Azure AD access token..." -ForegroundColor Yellow
$tokenResponse = az account get-access-token --resource $AZURE_FHIR_RESOURCE --query accessToken -o tsv

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to get access token. Make sure you're logged in with 'az login'" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Access token acquired" -ForegroundColor Green

Write-Host "`nStep 2: Uploading pregnancy observations bundle..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $tokenResponse"
    "Content-Type" = "application/fhir+json"
}

$bundleJson = Get-Content "azure_pregnancy_observations_bundle.json" -Raw

try {
    $response = Invoke-RestMethod -Uri "$AZURE_FHIR_BASE_URL/" -Method Post -Headers $headers -Body $bundleJson -ErrorAction Stop
    Write-Host "✓ Bundle uploaded successfully!" -ForegroundColor Green
    
    Write-Host "`nUpload Summary:" -ForegroundColor Cyan
    $response.entry | ForEach-Object {
        $status = $_.response.status
        $location = $_.response.location
        if ($status -match "^20") {
            Write-Host "  ✓ $location" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $location (Status: $status)" -ForegroundColor Red
        }
    }
    
    Write-Host "`nTotal observations uploaded: $($response.entry.Count)" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR: Failed to upload bundle" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

Write-Host "`nStep 3: Verifying upload..." -ForegroundColor Yellow

# Query for pregnancy observations
$queryUrl = "$AZURE_FHIR_BASE_URL/Observation?code=82810-3,93857-1,57064-8,11884-4,8339-4,72149-8,73812-0,11778-8,49051-6&subject=Patient/2-1234-W7"

try {
    $verifyResponse = Invoke-RestMethod -Uri $queryUrl -Method Get -Headers $headers -ErrorAction Stop
    $observationCount = $verifyResponse.entry.Count
    
    Write-Host "✓ Found $observationCount pregnancy-related observations in Azure FHIR" -ForegroundColor Green
    
    Write-Host "`nObservation Codes Found:" -ForegroundColor Cyan
    $verifyResponse.entry | ForEach-Object {
        $resource = $_.resource
        $code = $resource.code.coding[0].code
        $display = $resource.code.coding[0].display
        $effectiveDate = $resource.effectiveDateTime
        Write-Host "  • $code - $display ($effectiveDate)" -ForegroundColor White
    }
    
} catch {
    Write-Host "WARNING: Could not verify upload" -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Upload Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Clear Django cache: python quick_clear.py" -ForegroundColor White
Write-Host "2. Restart Django server" -ForegroundColor White
Write-Host "3. Search for patient 2-1234-W7 to see updated pregnancy data" -ForegroundColor White
