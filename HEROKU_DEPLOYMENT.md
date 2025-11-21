# Heroku Deployment Guide with Azure SQL Database

This guide walks you through deploying Django_NCP to Heroku using Azure SQL Database.

## Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Azure SQL Database**: Your existing database `eHealth` on server `myfreesqldbserver72`
4. **Git**: Ensure you're on the `main` branch with latest changes

## Azure SQL Database Setup

### 1. Configure Azure SQL Firewall Rules

Allow Heroku to access your Azure SQL Database:

```bash
# Login to Azure CLI
az login

# Add Heroku IP ranges (you'll need to add these in Azure Portal)
# Go to: Azure Portal → SQL Server → Networking → Firewall rules
# Add rule: "Heroku" with range 0.0.0.0 - 0.0.0.0 (allows all - restrict later)
```

Or via Azure Portal:
1. Navigate to your SQL Server: `myfreesqldbserver72`
2. Go to **Security** → **Networking**
3. Add firewall rule:
   - **Name**: Heroku
   - **Start IP**: 0.0.0.0
   - **End IP**: 0.0.0.0
4. Check **"Allow Azure services and resources to access this server"**
5. Click **Save**

### 2. Get Connection String

Your Azure SQL connection string format:
```
mssql://username:password@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30
```

Replace:
- `username` with your Azure SQL admin username
- `password` with your Azure SQL admin password

## Heroku Setup

### 1. Create Heroku App

```bash
# Login to Heroku
heroku login

# Create new Heroku app
heroku create your-app-name

# Or if you have an existing app
heroku git:remote -a your-app-name
```

### 2. Set Environment Variables

```bash
# Django Configuration
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=".herokuapp.com,your-custom-domain.com"

# Azure SQL Database Connection
heroku config:set DATABASE_URL="mssql://username:password@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

# Alternative: Set individual Azure SQL variables (if not using DATABASE_URL)
heroku config:set AZURE_SQL_SERVER="myfreesqldbserver72.database.windows.net"
heroku config:set AZURE_SQL_DATABASE="eHealth"
heroku config:set AZURE_SQL_USER="your_admin_username"
heroku config:set AZURE_SQL_PASSWORD="your_admin_password"

# eHealth Services Configuration
heroku config:set COUNTRY_CODE=IE
heroku config:set NCP_IDENTIFIER=ie-ncp-01
heroku config:set ORGANIZATION_NAME="Ireland Health Service Executive"
heroku config:set ORGANIZATION_ID=ie-hse

# FHIR Configuration
heroku config:set FHIR_PROVIDER=AZURE
heroku config:set AZURE_FHIR_BASE_URL="https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"
heroku config:set AZURE_FHIR_TENANT_ID="your-tenant-id"
heroku config:set AZURE_FHIR_CLIENT_ID="your-client-id"
heroku config:set AZURE_FHIR_CLIENT_SECRET="your-client-secret"

# CTS Integration
heroku config:set CTS_BASE_URL="https://cts.nlm.nih.gov/fhir"
heroku config:set CTS_USERNAME=""
heroku config:set CTS_PASSWORD=""
```

### 3. Add Buildpacks (for ODBC Driver)

Heroku doesn't include SQL Server ODBC drivers by default. Add buildpack:

```bash
# Add apt buildpack for installing system packages
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt

# Add Python buildpack
heroku buildpacks:add --index 2 heroku/python
```

Create `Aptfile` in project root:
```bash
unixodbc
unixodbc-dev
freetds-dev
freetds-bin
tdsodbc
```

### 4. Deploy to Heroku

```bash
# Ensure you're on main branch with latest changes
git status

# Commit any pending changes
git add .
git commit -m "feat: add Heroku deployment configuration with Azure SQL"

# Push to Heroku
git push heroku main

# Run database migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Collect static files (if not done automatically)
heroku run python manage.py collectstatic --noinput
```

### 5. Open Your App

```bash
heroku open
```

## Local Development with Azure SQL

To test locally before deploying:

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Edit `.env` with your Azure SQL details

```dotenv
# Django Configuration
SECRET_KEY=your-local-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Azure SQL Database
AZURE_SQL_SERVER=myfreesqldbserver72.database.windows.net
AZURE_SQL_DATABASE=eHealth
AZURE_SQL_USER=your_admin_username
AZURE_SQL_PASSWORD=your_admin_password
AZURE_SQL_PORT=1433

# Or use DATABASE_URL format
# DATABASE_URL=mssql://username:password@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server

# FHIR Configuration
FHIR_PROVIDER=AZURE
AZURE_FHIR_BASE_URL=https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com
AZURE_FHIR_TENANT_ID=your-tenant-id
AZURE_FHIR_CLIENT_ID=your-client-id
AZURE_FHIR_CLIENT_SECRET=your-client-secret
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Test Locally

```bash
python manage.py runserver
```

## Troubleshooting

### Issue: ODBC Driver Not Found

**Solution**: Ensure buildpacks are added in correct order:
```bash
heroku buildpacks
=== your-app-name Buildpack URLs
1. https://github.com/heroku/heroku-buildpack-apt
2. heroku/python
```

### Issue: Database Connection Timeout

**Solution**: Check Azure SQL firewall rules allow Heroku IPs:
1. Azure Portal → SQL Server → Networking
2. Ensure "Allow Azure services" is enabled
3. Add firewall rule for IP range 0.0.0.0 - 0.0.0.0 (temporary - restrict later)

### Issue: SSL Certificate Error

**Solution**: Ensure connection string includes:
```
?Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30
```

### Issue: Static Files Not Loading

**Solution**: Run collectstatic manually:
```bash
heroku run python manage.py collectstatic --noinput
```

Check WhiteNoise is configured:
```python
# settings.py should have:
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Issue: Session Data Lost

**Solution**: Configure database-backed sessions (already set in `patient_data/session_management.py`):
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

Run migrations to create session table:
```bash
heroku run python manage.py migrate
```

## Monitoring

### View Logs

```bash
# Real-time logs
heroku logs --tail

# Last 1000 lines
heroku logs -n 1000

# Filter by dyno
heroku logs --dyno web

# Filter by source
heroku logs --source app
```

### Database Access

```bash
# Open database shell
heroku run python manage.py dbshell

# Run Django shell
heroku run python manage.py shell
```

### App Information

```bash
# Check app status
heroku ps

# Check config vars
heroku config

# Check buildpacks
heroku buildpacks

# Check releases
heroku releases
```

## Security Best Practices

### 1. Restrict Azure SQL Firewall

After deployment, restrict IP ranges:
1. Get Heroku static IPs (requires paid dyno)
2. Update Azure SQL firewall rules with specific IPs
3. Remove 0.0.0.0/0 rule

### 2. Use Heroku Config for Secrets

Never commit secrets to Git:
```bash
# Good - use config vars
heroku config:set SECRET_KEY="..."

# Bad - don't add to .env in Git
echo "SECRET_KEY=..." >> .env
git add .env  # DON'T DO THIS
```

### 3. Enable HTTPS Only

```python
# settings.py for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### 4. Set Strong SECRET_KEY

```python
# Generate strong secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Scaling

### Upgrade Dyno Type

```bash
# Upgrade to Hobby dyno (7/month)
heroku ps:scale web=1:hobby

# Upgrade to Standard dyno (25/month)
heroku ps:scale web=1:standard-1x
```

### Add Workers

```bash
# Scale web dynos
heroku ps:scale web=2

# Add background worker (if needed)
heroku ps:scale worker=1
```

## Backup Strategy

### 1. Azure SQL Backups

Azure SQL automatically creates:
- Point-in-time backups (7-35 days retention)
- Long-term backups (up to 10 years)

### 2. Manual Database Dump

```bash
# From local machine with Azure CLI
az sql db export \
  --resource-group your-resource-group \
  --server myfreesqldbserver72 \
  --name eHealth \
  --admin-user your-admin \
  --admin-password your-password \
  --storage-key-type StorageAccessKey \
  --storage-key "your-storage-key" \
  --storage-uri "https://yourstorage.blob.core.windows.net/backups/ehealth.bacpac"
```

## Next Steps

1. ✅ Configure Azure SQL firewall rules
2. ✅ Set Heroku environment variables
3. ✅ Add buildpacks for ODBC driver
4. ✅ Deploy application
5. ✅ Run migrations
6. ✅ Create superuser
7. ✅ Test application
8. ✅ Monitor logs
9. ✅ Configure custom domain (optional)
10. ✅ Set up SSL certificate (automatic with Heroku)

## Support

For issues:
- **Heroku**: [help.heroku.com](https://help.heroku.com)
- **Azure SQL**: [docs.microsoft.com/azure/sql-database](https://docs.microsoft.com/azure/sql-database)
- **Django**: [docs.djangoproject.com](https://docs.djangoproject.com)
