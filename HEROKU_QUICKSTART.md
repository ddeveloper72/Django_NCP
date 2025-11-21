# Quick Start: Heroku Deployment with Azure SQL

## Your Azure SQL Details
- **Server**: `myfreesqldbserver72.database.windows.net`
- **Database**: `eHealth`
- **Username**: [Your admin username]
- **Password**: [Your admin password]

## Essential Setup Commands

### 1. Install Heroku CLI (if not installed)
```bash
# Windows (using PowerShell)
winget install Heroku.HerokuCLI

# Or download from: https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login and Create App
```bash
# Login to Heroku
heroku login

# Create new app (or use existing)
heroku create your-app-name
```

### 3. Configure Azure SQL Firewall
**Azure Portal Steps:**
1. Go to: [Azure Portal](https://portal.azure.com)
2. Navigate: **SQL databases** → **myfreesqldbserver72** → **Networking**
3. Add firewall rule:
   - Name: `Heroku`
   - Start IP: `0.0.0.0`
   - End IP: `0.0.0.0`
4. Check: ☑️ **Allow Azure services and resources to access this server**
5. Click: **Save**

### 4. Set Environment Variables

```bash
# Generate SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set Django configuration
heroku config:set SECRET_KEY="[generated-key-from-above]"
heroku config:set DEBUG=False
heroku config:set DEVELOPMENT=False
heroku config:set ALLOWED_HOSTS=".herokuapp.com"

# Set Azure SQL connection (replace USERNAME and PASSWORD)
heroku config:set DATABASE_URL="mssql://USERNAME:PASSWORD@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

# Set eHealth configuration
heroku config:set COUNTRY_CODE=IE
heroku config:set FHIR_PROVIDER=AZURE
heroku config:set AZURE_FHIR_BASE_URL="https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com"

# Set Azure FHIR authentication (get from Azure Portal)
heroku config:set AZURE_FHIR_TENANT_ID="your-tenant-id"
heroku config:set AZURE_FHIR_CLIENT_ID="your-client-id"
heroku config:set AZURE_FHIR_CLIENT_SECRET="your-client-secret"
```

### 5. Add Buildpacks
```bash
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
heroku buildpacks:add --index 2 heroku/python
```

### 6. Deploy Application
```bash
# Commit changes
git add .
git commit -m "feat: add Heroku deployment configuration"

# Push to Heroku
git push heroku main
```

### 7. Initialize Database
```bash
# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Collect static files (if needed)
heroku run python manage.py collectstatic --noinput
```

### 8. Open Application
```bash
heroku open
```

## Quick Troubleshooting

### Check Logs
```bash
heroku logs --tail
```

### Test Database Connection
```bash
heroku run python manage.py dbshell
```

### View Config
```bash
heroku config
```

### Restart App
```bash
heroku restart
```

## Automated Setup (Recommended)

Run the setup script for guided configuration:

```powershell
# Windows PowerShell
.\setup_heroku.ps1
```

```bash
# Git Bash / Linux / macOS
bash setup_heroku.sh
```

## Important Files Created

- ✅ `Procfile` - Heroku process configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `Aptfile` - System dependencies (ODBC driver)
- ✅ `requirements.txt` - Updated with Azure SQL and Heroku packages
- ✅ `settings.py` - Database configuration with Azure SQL support
- ✅ `HEROKU_DEPLOYMENT.md` - Complete deployment guide
- ✅ `.env.heroku` - Environment variables template

## Need Help?

See detailed instructions in: **[HEROKU_DEPLOYMENT.md](./HEROKU_DEPLOYMENT.md)**

## Security Checklist

- [ ] Changed `SECRET_KEY` from default
- [ ] Set `DEBUG=False` for production
- [ ] Configured Azure SQL firewall rules
- [ ] Restricted `ALLOWED_HOSTS` to your domain
- [ ] Never committed `.env` files to Git
- [ ] Used strong database password
- [ ] Configured HTTPS redirects (automatic on Heroku)
- [ ] Set up SSL for Azure SQL (automatic with connection string)

## Cost Estimate

**Heroku:**
- Free tier: Limited hours, sleeps after inactivity
- Hobby ($7/month): Always on, custom domains
- Standard ($25/month): Better performance, metrics

**Azure SQL:**
- Basic tier: ~$5/month (current setup)
- Standard tier: ~$15/month (recommended for production)

## Next Steps After Deployment

1. ✅ Test patient data upload to Azure FHIR
2. ✅ Verify CDA document processing
3. ✅ Test cross-border healthcare queries
4. ✅ Configure custom domain (optional)
5. ✅ Set up monitoring and alerts
6. ✅ Configure backups and disaster recovery
7. ✅ Implement CI/CD pipeline (optional)

---

**Ready to deploy?** Run `.\setup_heroku.ps1` to get started! 🚀
