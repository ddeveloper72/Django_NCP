# CSS Architecture Guide - Phase 6 Consolidated System

## Overview

This document explains the consolidated CSS architecture implemented in September 2025 to address confusion around multiple overlapping stylesheets.

## Architecture Principles

### Single Source of Truth

- **ONE** compiled CSS file: `static/css/main.css` (259KB, 11,730 lines)
- **THREE** external dependencies: Bootstrap, FontAwesome, main.css
- **SASS-based** compilation system for maintainability

### File Structure

```
static/
├── css/
│   └── main.css              # ← SINGLE compiled output
├── scss/
│   ├── main.scss             # ← Main compilation entry point
│   ├── utils/
│   │   ├── variables.scss    # ← Global variables
│   │   └── mixins.scss       # ← Reusable mixins
│   ├── base/
│   │   ├── reset.scss
│   │   ├── typography.scss
│   │   ├── _irish_healthcare_theme.scss  # ← Consolidated theme
│   │   └── _accessibility.scss           # ← Accessibility features
│   ├── components/
│   │   ├── _bootstrap_overrides.scss     # ← Bootstrap customizations
│   │   ├── _buttons.scss
│   │   ├── _forms.scss
│   │   ├── _cards.scss
│   │   ├── _tables.scss
│   │   ├── _smp_dashboard.scss           # ← SMP client styles
│   │   └── ...
│   ├── layouts/
│   │   ├── _grid.scss
│   │   ├── _header.scss
│   │   └── ...
│   └── pages/
│       ├── _home.scss
│       ├── _dashboard.scss
│       └── ...
```

## What Changed

### Before (Confusing)

```html
<!-- OLD: 6 separate CSS files -->
<link href="bootstrap.min.css" rel="stylesheet">
<link href="fontawesome.min.css" rel="stylesheet">
<link href="irish-healthcare-theme.css" rel="stylesheet">
<link href="accessibility.css" rel="stylesheet">
<link href="bootstrap-components.css" rel="stylesheet">
<link href="main.css" rel="stylesheet">
```

### After (Clean)

```html
<!-- NEW: 3 files total -->
<link href="bootstrap.min.css" rel="stylesheet">
<link href="fontawesome.min.css" rel="stylesheet">
<link href="main.css" rel="stylesheet">          <!-- ← Contains everything -->
```

## Compilation Process

### Development

```bash
# Watch mode for development
sass --watch static/scss:static/css

# OR use VS Code task: "Compile SASS"
```

### Production

```bash
# One-time compilation
sass static/scss:static/css

# OR use VS Code task: "Compile SASS (One-time)"
```

## Consolidated Components

The main.css now includes all styles from:

1. **Irish Healthcare Theme** (2,391 lines) - HSE colors, medical styling
2. **Accessibility Features** (338 lines) - WCAG compliance, screen readers
3. **Bootstrap Overrides** (61 lines) - Custom Bootstrap modifications
4. **SMP Dashboard Styles** (682 lines) - Service Metadata Publishing interface
5. **All Component Styles** - Buttons, forms, tables, cards, etc.
6. **All Layout Styles** - Grid, header, footer, sidebar
7. **All Page-specific Styles** - Home, dashboard, admin, patient views

## Testing and Validation

### Template Testing Workflow

We have established a comprehensive testing methodology to verify template rendering and CSS loading:

#### 1. Template Syntax Testing

```bash
# Test all major URLs for template errors
python manage.py test_urls --save-responses

# Test specific URLs
python quick_template_test.py
```

#### 2. CSS Loading Verification

- **HTML Source Inspection**: Check rendered pages to ensure only 3 CSS files load:
  - `/static/vendor/bootstrap/bootstrap.min.css`
  - `/static/vendor/fontawesome/fontawesome.min.css`
  - `/static/css/main.css` (consolidated)
- **Style Validation**: Verify consolidated styles are present in main.css
- **Performance Check**: Single 254KB CSS file instead of multiple smaller files

#### 3. Current Test Results (September 20, 2025)

```
✅ / (Status: 200, Size: 12,088 bytes)
✅ /patients/ (Status: 200, Size: 14,570 bytes)
✅ /smp/ (Status: 200, Size: 9,538 bytes)
✅ /admin/ (Status: 200, Size: 4,496 bytes)
✅ /smp/editor/ (Status: 200, Size: 9,545 bytes)
✅ /smp/documents/ (Status: 200, Size: 9,548 bytes)
✅ /smp/participants/ (Status: 200, Size: 9,551 bytes)
```

All templates render successfully with consolidated CSS architecture.

### Issues Resolved

- **Template Syntax Error**: Fixed unclosed `{% block %}` tag in `patient_form.html`
- **CSS Consolidation**: Successfully merged 3 standalone CSS files into SASS partials
- **SMP Integration**: All Phase 6 SMP templates working with consolidated CSS

## Benefits

1. **Reduced Confusion**: Single CSS source instead of multiple overlapping files
2. **Better Maintenance**: SASS structure with partials and variables
3. **Improved Performance**: Fewer HTTP requests (6 → 3 files)
4. **Consistent Styling**: Single compilation prevents style conflicts
5. **Modern Architecture**: Industry-standard SASS workflow

## Usage Guidelines

### Adding New Styles

1. Create appropriate SASS partial in relevant directory
2. Import in `main.scss`
3. Compile to update `main.css`

### Modifying Existing Styles

1. Edit the SASS partial (NOT the compiled CSS)
2. Recompile to update `main.css`

### Variables and Mixins

- Use existing variables from `utils/variables.scss`
- Add new reusable patterns to `utils/mixins.scss`

## Files Removed

- `static/css/irish-healthcare-theme.css` → Moved to `static/scss/base/_irish_healthcare_theme.scss`
- `static/css/accessibility.css` → Moved to `static/scss/base/_accessibility.scss`
- `static/css/bootstrap-components.css` → Moved to `static/scss/components/_bootstrap_overrides.scss`

---

*Document created: September 20, 2025*
*Last updated: Phase 6 CSS Consolidation*
