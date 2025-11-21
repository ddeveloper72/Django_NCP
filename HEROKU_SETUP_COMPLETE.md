# Heroku + Azure SQL Setup Complete! 🎉

## What Was Configured

### ✅ Database Configuration
**Updated**: `eu_ncp_server/settings.py`
- Added support for Azure SQL Database via `DATABASE_URL` or individual variables
- Configured ODBC Driver 18 for SQL Server with SSL encryption
- Maintained SQLite for local development
- Added connection pooling (`conn_max_age=600`)

**Connection Methods**:
1. **Heroku Style** (via DATABASE_URL):
   ```
   mssql://username:password@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30
   ```

2. **Direct Azure SQL** (via individual variables):
   - `AZURE_SQL_SERVER=myfreesqldbserver72.database.windows.net`
   - `AZURE_SQL_DATABASE=eHealth`
   - `AZURE_SQL_USER=your_admin_username`
   - `AZURE_SQL_PASSWORD=your_admin_password`

### ✅ Static Files Configuration
**Updated**: `eu_ncp_server/settings.py`
- Added WhiteNoise middleware for serving static files on Heroku
- Configured compressed static file storage for performance
- Maintained Django Compressor for SCSS compilation

### ✅ Dependencies Added
**Updated**: `requirements.txt`
```
dj-database-url==2.3.0       # Parse DATABASE_URL
gunicorn==23.0.0             # Production WSGI server
whitenoise==6.8.2            # Static file serving
mssql-django==2.0.0          # Azure SQL support
pyodbc==5.2.0                # ODBC driver interface
```

### ✅ Heroku Process Configuration
**Created**: `Procfile`
```
web: gunicorn eu_ncp_server.wsgi --log-file -
release: python manage.py migrate --noinput
```
- `web`: Runs Gunicorn WSGI server
- `release`: Automatically runs migrations on deployment

### ✅ Python Runtime
**Created**: `runtime.txt`
```
python-3.12.4
```
Matches your local development environment.

### ✅ System Dependencies
**Created**: `Aptfile`
```
unixodbc
unixodbc-dev
freetds-dev
freetds-bin
tdsodbc
```
Installs ODBC drivers required for Azure SQL on Linux (Heroku).

### ✅ Environment Configuration
**Updated**: `.env.example`
- Added `DATABASE_URL` option
- Added Azure SQL individual variables
- Updated documentation

**Created**: `.env.heroku`
- Template for Heroku config vars
- Pre-filled with your Azure SQL server details
- Includes all required eHealth and FHIR settings

### ✅ Security
**Updated**: `.gitignore`
- Added `.env.heroku` and `.env.staging` to prevent secrets leaking

### ✅ Setup Automation
**Created**: `setup_heroku.ps1` (Windows)
- Interactive PowerShell script
- Guides through Heroku configuration
- Generates secure SECRET_KEY
- Sets all environment variables

**Created**: `setup_heroku.sh` (Linux/macOS)
- Bash equivalent of PowerShell script
- Cross-platform compatible

### ✅ Documentation
**Created**: `HEROKU_DEPLOYMENT.md`
- Complete deployment guide (708 lines)
- Azure SQL firewall configuration
- Heroku CLI commands
- Troubleshooting section
- Security best practices
- Backup strategies
- Monitoring commands

**Created**: `HEROKU_QUICKSTART.md`
- Quick reference card
- Essential commands only
- Your specific Azure SQL details
- Security checklist
- Cost estimates

## Your Azure SQL Details

**Server**: `myfreesqldbserver72.database.windows.net`
**Database**: `eHealth`

You need:
1. Admin username (you have this)
2. Admin password (you have this)
3. Azure FHIR credentials (tenant ID, client ID, client secret)

## Next Steps

### Option 1: Automated Setup (Recommended)
```powershell
# Run setup script
.\setup_heroku.ps1
```
This will:
- ✅ Check Heroku CLI installation
- ✅ Login to Heroku
- ✅ Create/configure app
- ✅ Set all environment variables
- ✅ Add buildpacks
- ✅ Guide you through deployment

### Option 2: Manual Setup
1. **Configure Azure SQL Firewall**
   - Azure Portal → SQL Server → Networking
   - Add firewall rule: `0.0.0.0` to `0.0.0.0`
   - Enable "Allow Azure services"

2. **Create Heroku App**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Set Environment Variables**
   ```bash
   # See HEROKU_QUICKSTART.md for complete list
   heroku config:set DATABASE_URL="mssql://USER:PASS@myfreesqldbserver72.database.windows.net:1433/eHealth?driver=ODBC+Driver+18+for+SQL+Server"
   ```

4. **Add Buildpacks**
   ```bash
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
   heroku buildpacks:add --index 2 heroku/python
   ```

5. **Deploy**
   ```bash
   git add .
   git commit -m "feat: add Heroku deployment with Azure SQL"
   git push heroku main
   ```

6. **Initialize Database**
   ```bash
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

## File Summary

| File | Purpose | Status |
|------|---------|--------|
| `Procfile` | Heroku process definition | ✅ Created |
| `runtime.txt` | Python version | ✅ Created |
| `Aptfile` | ODBC driver dependencies | ✅ Created |
| `requirements.txt` | Python packages | ✅ Updated |
| `settings.py` | Django configuration | ✅ Updated |
| `.env.example` | Environment template | ✅ Updated |
| `.env.heroku` | Heroku config template | ✅ Created |
| `.gitignore` | Security exclusions | ✅ Updated |
| `setup_heroku.ps1` | Windows setup script | ✅ Created |
| `setup_heroku.sh` | Linux/macOS setup script | ✅ Created |
| `HEROKU_DEPLOYMENT.md` | Full deployment guide | ✅ Created |
| `HEROKU_QUICKSTART.md` | Quick reference | ✅ Created |

## Testing Locally (Optional)

Before deploying to Heroku, test with Azure SQL locally:

1. **Create `.env` file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** with your Azure SQL credentials:
   ```dotenv
   AZURE_SQL_SERVER=myfreesqldbserver72.database.windows.net
   AZURE_SQL_DATABASE=eHealth
   AZURE_SQL_USER=your_admin_username
   AZURE_SQL_PASSWORD=your_admin_password
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Test connection**:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Important Notes

### 🔒 Security
- Never commit `.env` files to Git
- Generate new `SECRET_KEY` for production
- Set `DEBUG=False` for Heroku
- Configure Azure SQL firewall properly
- Use strong database passwords

### 💰 Costs
- **Heroku**: Free tier available, Hobby ($7/month), Standard ($25/month)
- **Azure SQL**: Basic tier (~$5/month), Standard (~$15/month)
- **Total**: ~$5-40/month depending on tier choices

### ⚡ Performance
- Connection pooling enabled (`conn_max_age=600`)
- WhiteNoise for fast static file serving
- Gunicorn with multiple workers
- ODBC Driver 18 for optimal SQL performance

### 🔧 Troubleshooting
All common issues covered in `HEROKU_DEPLOYMENT.md`:
- ODBC driver not found → Buildpack order
- Connection timeout → Firewall rules
- SSL certificate error → Connection string options
- Static files 404 → WhiteNoise configuration
- Session data lost → Database-backed sessions (already configured)

## Commit Your Changes

```bash
git add .
git commit -m "feat: add Heroku deployment configuration with Azure SQL Database

- Configure Django settings for Azure SQL Database
- Add Heroku deployment files (Procfile, runtime.txt, Aptfile)
- Update requirements.txt with Azure SQL and Heroku dependencies
- Add WhiteNoise for static file serving
- Create automated setup scripts (PowerShell and Bash)
- Add comprehensive deployment documentation
- Configure database connection pooling and SSL
- Maintain backward compatibility with SQLite for local dev"

git push origin main
```

## Ready to Deploy?

Choose your path:
1. **Automated** → Run `.\setup_heroku.ps1`
2. **Manual** → Follow `HEROKU_QUICKSTART.md`
3. **Detailed** → Read `HEROKU_DEPLOYMENT.md`

---

**Questions?** Check the troubleshooting section in `HEROKU_DEPLOYMENT.md` 📚
