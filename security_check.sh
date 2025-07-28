#!/bin/bash
#
# Pre-Deployment Security Check Script
# Run this before pushing to GitHub or deploying to production
#

echo "🔒 EU eHealth NCP Server - Security Check"
echo "=========================================="

# Check for sensitive files
echo "📁 Checking for sensitive files..."
SENSITIVE_FILES=$(find . -name "*.pem" -o -name "*.key" -o -name "*.p12" -o -name ".env" -not -path "./.env.example" -not -path "./.env.secure.example")
if [ -n "$SENSITIVE_FILES" ]; then
    echo "❌ WARNING: Sensitive files found:"
    echo "$SENSITIVE_FILES"
    echo "   These files should NOT be committed to version control!"
else
    echo "✅ No sensitive certificate or key files found"
fi

# Check for hardcoded secrets
echo ""
echo "🔍 Scanning for potential secrets in code..."
SECRET_PATTERNS="password|secret|key|token|api_key"
SECRETS_FOUND=$(git log --all -p | grep -iE "$SECRET_PATTERNS" | grep -v "SECRET_KEY.*=.*os.getenv" | grep -v "example" | grep -v "placeholder" | head -5)
if [ -n "$SECRETS_FOUND" ]; then
    echo "⚠️  Potential secrets found in git history:"
    echo "$SECRETS_FOUND"
    echo "   Review these matches to ensure no real secrets are committed"
else
    echo "✅ No obvious secrets found in git history"
fi

# Check environment configuration
echo ""
echo "🌍 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "❌ WARNING: .env file exists and may contain secrets"
    echo "   Ensure .env is in .gitignore and contains no production secrets"
else
    echo "✅ No .env file found in repository"
fi

if [ -f ".env.secure.example" ]; then
    echo "✅ Secure environment template found"
else
    echo "⚠️  No environment template found"
fi

# Check Django settings
echo ""
echo "⚙️  Checking Django configuration..."
if grep -q "DEBUG.*=.*True" eu_ncp_server/settings.py; then
    echo "⚠️  DEBUG=True found in settings.py - ensure this uses environment variables"
else
    echo "✅ No hardcoded DEBUG=True found"
fi

if grep -q "SECRET_KEY.*=.*django-insecure" eu_ncp_server/settings.py; then
    echo "❌ WARNING: Default Django secret key found - this MUST be changed for production"
else
    echo "✅ No default secret key found"
fi

# Check gitignore
echo ""
echo "🚫 Checking .gitignore coverage..."
GITIGNORE_CHECKS=(".env" "*.pem" "*.key" "certificates/" "db.sqlite3")
for pattern in "${GITIGNORE_CHECKS[@]}"; do
    if grep -q "$pattern" .gitignore; then
        echo "✅ $pattern is ignored"
    else
        echo "⚠️  $pattern not found in .gitignore"
    fi
done

# Summary
echo ""
echo "📋 Security Check Summary"
echo "========================"
echo "Before pushing to GitHub:"
echo "1. ✅ Review all warnings above"
echo "2. ✅ Ensure no real certificates in repository"
echo "3. ✅ Verify environment variables are secure"
echo "4. ✅ Test with production-like settings"
echo "5. ✅ Update documentation if needed"
echo ""
echo "🚀 If all checks pass, you're ready to push to GitHub!"
echo ""
echo "Deployment checklist:"
echo "• Set DEBUG=False in production"
echo "• Use strong SECRET_KEY"
echo "• Configure proper ALLOWED_HOSTS"
echo "• Set up SSL certificates"
echo "• Enable audit logging"
echo "• Monitor security events"
