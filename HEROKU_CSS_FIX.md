# Heroku CSS Update Fix

## Problem
CSS changes (flag sizing fixes) are not appearing on Heroku after deployment because:
1. The release phase command wasn't running `compile_scss` and `collectstatic`
2. WhiteNoise cached the old CSS files

## Solution - Run These Commands

### Option 1: Force Release Phase (Recommended)
```bash
# Trigger a new release that will run compile_scss + collectstatic
heroku releases --app your-app-name
heroku releases:retry v123  # Use the version number from above command
```

### Option 2: Manual Build (Quick Fix)
```bash
# SSH into Heroku and manually rebuild CSS
heroku run bash --app your-app-name
python manage.py compile_scss
python manage.py collectstatic --noinput
exit
```

### Option 3: Force New Deployment
```bash
# Make a trivial change to trigger deployment
git commit --allow-empty -m "Force Heroku CSS rebuild"
git push heroku main
```

## Verify Fix
1. Check Heroku logs for successful CSS compilation:
   ```bash
   heroku logs --tail --app your-app-name
   ```
   Look for: `✓ Successfully compiled SCSS to CSS`

2. Visit your Heroku app URL
3. Hard refresh browser: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
4. Check flag sizes:
   - Breadcrumb flags: 20px × 13px
   - Header flags: 48px × 32px

## What Changed
- **Procfile**: Added `compile_scss` and `collectstatic` to release phase
- **compile_scss.py**: New Django management command using libsass
- **settings.py**: Updated to use `CompressedManifestStaticFilesStorage`

## Future Deployments
All future deployments will automatically:
1. Compile SCSS → CSS
2. Collect static files with content hashing
3. Generate manifest for cache-busting
4. Run database migrations
