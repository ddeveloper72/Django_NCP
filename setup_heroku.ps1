# Heroku Deployment Setup Script (PowerShell)
# This script helps configure Heroku environment variables for Azure SQL Database

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Django_NCP Heroku Deployment Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Heroku CLI is installed
try {
    $null = heroku --version
} catch {
    Write-Host "ERROR: Heroku CLI is not installed." -ForegroundColor Red
    Write-Host "Please install from: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged into Heroku
try {
    $null = heroku auth:whoami 2>$null
} catch {
    Write-Host "Please login to Heroku:" -ForegroundColor Yellow
    heroku login
}

Write-Host ""
$AppName = Read-Host "Enter your Heroku app name (or press Enter to create new)"

if ([string]::IsNullOrWhiteSpace($AppName)) {
    Write-Host "Creating new Heroku app..." -ForegroundColor Yellow
    heroku create
} else {
    Write-Host "Using existing app: $AppName" -ForegroundColor Green
    heroku git:remote -a $AppName
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 1: Azure SQL Database Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your Azure SQL Server: myfreesqldbserver72.database.windows.net" -ForegroundColor White
Write-Host "Your Database: eHealth" -ForegroundColor White
Write-Host ""

$AzureUser = Read-Host "Enter Azure SQL admin username"
$AzurePasswordSecure = Read-Host "Enter Azure SQL admin password" -AsSecureString
$AzurePassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AzurePasswordSecure))

# Construct DATABASE_URL
$DatabaseUrl = "mssql://$($AzureUser):$($AzurePassword)@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

Write-Host ""
Write-Host "Setting DATABASE_URL..." -ForegroundColor Yellow
heroku config:set "DATABASE_URL=$DatabaseUrl"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 2: Django Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Generate SECRET_KEY
Write-Host "Generating Django SECRET_KEY..." -ForegroundColor Yellow
$SecretKey = python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
heroku config:set "SECRET_KEY=$SecretKey"

# Set DEBUG and ALLOWED_HOSTS
heroku config:set "DEBUG=False"
$AppInfo = heroku info -s | Out-String
$AppDomain = ($AppInfo -split "`n" | Where-Object { $_ -match "web_url=" }) -replace "web_url=https://", "" -replace "/", ""
heroku config:set "ALLOWED_HOSTS=.herokuapp.com,$AppDomain"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 3: eHealth Services Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

heroku config:set "COUNTRY_CODE=IE"
heroku config:set "NCP_IDENTIFIER=ie-ncp-01"
heroku config:set "ORGANIZATION_NAME=Ireland Health Service Executive"
heroku config:set "ORGANIZATION_ID=ie-hse"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 4: Azure FHIR Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your FHIR Server: healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com" -ForegroundColor White
Write-Host ""

$FhirTenantId = Read-Host "Enter Azure FHIR Tenant ID"
$FhirClientId = Read-Host "Enter Azure FHIR Client ID"
$FhirClientSecretSecure = Read-Host "Enter Azure FHIR Client Secret" -AsSecureString
$FhirClientSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($FhirClientSecretSecure))

heroku config:set "FHIR_PROVIDER=AZURE"
heroku config:set "AZURE_FHIR_BASE_URL=https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"
heroku config:set "AZURE_FHIR_TENANT_ID=$FhirTenantId"
heroku config:set "AZURE_FHIR_CLIENT_ID=$FhirClientId"
heroku config:set "AZURE_FHIR_CLIENT_SECRET=$FhirClientSecret"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 5: Add Buildpacks" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure Azure SQL firewall rules (see HEROKU_DEPLOYMENT.md)" -ForegroundColor White
Write-Host "2. Commit and push your code:" -ForegroundColor White
Write-Host "   git add ." -ForegroundColor Cyan
Write-Host "   git commit -m 'feat: add Heroku deployment configuration'" -ForegroundColor Cyan
Write-Host "   git push heroku main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Run migrations:" -ForegroundColor White
Write-Host "   heroku run python manage.py migrate" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Create superuser:" -ForegroundColor White
Write-Host "   heroku run python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Open your app:" -ForegroundColor White
Write-Host "   heroku open" -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed instructions, see: HEROKU_DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""
