#!/bin/bash
# Heroku Deployment Setup Script
# This script helps configure Heroku environment variables for Azure SQL Database

echo "=========================================="
echo "Django_NCP Heroku Deployment Setup"
echo "=========================================="
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "ERROR: Heroku CLI is not installed."
    echo "Please install from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged into Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "Please login to Heroku:"
    heroku login
fi

echo ""
echo "Enter your Heroku app name (or press Enter to create new):"
read -r APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "Creating new Heroku app..."
    heroku create
else
    echo "Using existing app: $APP_NAME"
    heroku git:remote -a "$APP_NAME"
fi

echo ""
echo "=========================================="
echo "Step 1: Azure SQL Database Configuration"
echo "=========================================="
echo ""
echo "Your Azure SQL Server: myfreesqldbserver72.database.windows.net"
echo "Your Database: eHealth"
echo ""
read -p "Enter Azure SQL admin username: " AZURE_USER
read -sp "Enter Azure SQL admin password: " AZURE_PASSWORD
echo ""

# Construct DATABASE_URL
DATABASE_URL="mssql://${AZURE_USER}:${AZURE_PASSWORD}@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

echo ""
echo "Setting DATABASE_URL..."
heroku config:set DATABASE_URL="$DATABASE_URL"

echo ""
echo "=========================================="
echo "Step 2: Django Configuration"
echo "=========================================="
echo ""

# Generate SECRET_KEY
echo "Generating Django SECRET_KEY..."
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set SECRET_KEY="$SECRET_KEY"

# Set DEBUG, DEVELOPMENT, and ALLOWED_HOSTS
heroku config:set DEBUG=False
heroku config:set DEVELOPMENT=False
APP_DOMAIN=$(heroku info -s | grep web_url | cut -d= -f2 | sed 's~https://~~' | sed 's~/~~')
heroku config:set ALLOWED_HOSTS=".herokuapp.com,$APP_DOMAIN"

echo ""
echo "=========================================="
echo "Step 3: eHealth Services Configuration"
echo "=========================================="
echo ""

heroku config:set COUNTRY_CODE=IE
heroku config:set NCP_IDENTIFIER=ie-ncp-01
heroku config:set ORGANIZATION_NAME="Ireland Health Service Executive"
heroku config:set ORGANIZATION_ID=ie-hse

echo ""
echo "=========================================="
echo "Step 4: Azure FHIR Configuration"
echo "=========================================="
echo ""
echo "Your FHIR Server: healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"
echo ""
read -p "Enter Azure FHIR Tenant ID: " FHIR_TENANT_ID
read -p "Enter Azure FHIR Client ID: " FHIR_CLIENT_ID
read -sp "Enter Azure FHIR Client Secret: " FHIR_CLIENT_SECRET
echo ""

heroku config:set FHIR_PROVIDER=AZURE
heroku config:set AZURE_FHIR_BASE_URL="https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"
heroku config:set AZURE_FHIR_TENANT_ID="$FHIR_TENANT_ID"
heroku config:set AZURE_FHIR_CLIENT_ID="$FHIR_CLIENT_ID"
heroku config:set AZURE_FHIR_CLIENT_SECRET="$FHIR_CLIENT_SECRET"

echo ""
echo "=========================================="
echo "Step 5: Add Buildpacks"
echo "=========================================="
echo ""

heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure Azure SQL firewall rules (see HEROKU_DEPLOYMENT.md)"
echo "2. Commit and push your code:"
echo "   git add ."
echo "   git commit -m 'feat: add Heroku deployment configuration'"
echo "   git push heroku main"
echo ""
echo "3. Run migrations:"
echo "   heroku run python manage.py migrate"
echo ""
echo "4. Create superuser:"
echo "   heroku run python manage.py createsuperuser"
echo ""
echo "5. Open your app:"
echo "   heroku open"
echo ""
echo "For detailed instructions, see: HEROKU_DEPLOYMENT.md"
echo ""
