# 🔒 Security Guide - EU eHealth NCP Server

## 🚨 Critical Security Checklist

### Before Committing to GitHub

- [ ] **Environment Variables**: All sensitive data moved to `.env` file (never committed)
- [ ] **Certificates**: No real certificates in repository (use `.gitignore`)
- [ ] **Secret Keys**: Django SECRET_KEY in environment variables
- [ ] **Database Credentials**: Never hardcoded in settings.py
- [ ] **Debug Mode**: Set `DEBUG=False` for production
- [ ] **Test Data**: Remove any real patient or healthcare data

### 🔐 Environment Variables Security

**Sensitive Variables (Never Commit):**

```bash
SECRET_KEY=your-actual-secret-key
DB_PASSWORD=your-database-password
EMAIL_HOST_PASSWORD=your-email-password
SSL_PRIVATE_KEY_PATH=/secure/path/to/private.key
SENTRY_DSN=your-monitoring-token
```

**Safe to Include:**

```bash
DEBUG=False
COUNTRY_CODE=IE
ORGANIZATION_NAME=Ireland Health Service Executive
LOG_LEVEL=INFO
```

### 📁 File Security

**Never Commit These Files:**

- `.env` (environment variables)
- `*.pem`, `*.crt`, `*.key` (certificates and private keys)
- `db.sqlite3` (database with real data)
- `logs/*.log` (log files may contain sensitive data)
- `media/certificates/` (uploaded certificates)

**Safe to Commit:**

- `.env.example` (template with placeholder values)
- `*.py` (source code)
- `requirements.txt` (dependencies)
- Documentation files

### 🔧 Production Security Hardening

**1. Django Settings:**

```python
# Production settings
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**2. Certificate Management:**

- Store certificates outside web root
- Use strong passphrases for private keys
- Implement certificate rotation
- Monitor certificate expiration
- Use HSM for production private keys

**3. Database Security:**

- Use strong database passwords
- Enable SSL connections
- Regular security backups
- Audit database access
- Encrypt sensitive data at rest

### 🏥 eHealth Specific Security

**Patient Data Protection:**

- All patient data encrypted in transit and at rest
- Implement GDPR compliance measures
- Audit all access to patient records
- Use anonymization for development/testing
- Secure deletion of expired data

**NCP Security Requirements:**

- Mutual TLS authentication between NCPs
- Digital signatures for all eHealth documents
- Certificate validation according to eIDAS
- Secure key management for signing
- Audit logging for compliance

### 🔍 Security Testing

**Before Deployment:**

```bash
# Check for secrets in code
git log -p | grep -i "password\|secret\|key\|token"

# Scan for sensitive files
find . -name "*.pem" -o -name "*.key" -o -name ".env"

# Test SSL configuration
python manage.py check --deploy

# Run security linting
bandit -r . -f json
```

### 📊 Monitoring and Logging

**Security Events to Monitor:**

- Failed authentication attempts
- Certificate validation failures
- Unauthorized API access
- Data export/download activities
- Configuration changes
- Unusual access patterns

**Audit Logging:**

- All patient data access
- Certificate operations
- Administrative actions
- External NCP communications
- Security configuration changes

### 🚨 Incident Response

**Security Incident Procedures:**

1. **Immediate**: Isolate affected systems
2. **Assess**: Determine scope and impact
3. **Contain**: Prevent further damage
4. **Notify**: Report to relevant authorities
5. **Recover**: Restore secure operations
6. **Learn**: Update security measures

### 📞 Security Contacts

**For Security Issues:**

- **Technical Security**: <ehealth.security@your-domain.com>
- **Data Protection Officer**: <dpo@your-domain.com>
- **Emergency Response**: <security-emergency@your-domain.com>

### 📚 Compliance References

- **GDPR**: General Data Protection Regulation
- **eIDAS**: Electronic Identification and Trust Services
- **ISO 27001**: Information Security Management
- **IHE**: Integrating the Healthcare Enterprise
- **HL7 FHIR Security**: <https://www.hl7.org/fhir/security.html>

---

**⚠️ Remember**: Security is not a one-time setup but an ongoing process. Regular reviews and updates are essential for maintaining a secure eHealth infrastructure.
