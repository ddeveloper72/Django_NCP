# Django Template Commenting Standards

**Version:** 1.0
**Status:** Active
**Owner:** Development Team
**Last Updated:** 2025-09-22

## Overview

This specification defines commenting standards for Django templates to ensure template integrity, maintainability, and consistent code quality across the Django_NCP project.

## Requirements

### 1. Django Template Comments vs HTML Comments

**Use Django template comments for template-specific documentation:**

```django
{# This template renders clinical data with smart pagination #}
{% if section.has_data %}
    {# Display primary clinical information #}
    <div class="clinical-data">
        {{ section.data }}
    </div>
{% endif %}
```

**Use HTML comments only for final rendered output documentation:**

```html
<!-- Clinical data section starts here -->
<div class="clinical-section">
    <!-- Content rendered by Django -->
</div>
<!-- Clinical data section ends here -->
```

### 2. Inline Comment Prohibition

**❌ NEVER mix comments with Django template tags on the same line:**

```django
{# BAD: Inline comments can corrupt template parsing #}
{% endwith %} <!-- This causes template corruption -->
{% if condition %} <!-- This breaks template compilation -->
```

**✅ ALWAYS place comments on separate lines:**

```django
{# GOOD: Comment explains the following template logic #}
{% endwith %}

{# Close medical coverage context #}
{% if condition %}
    {# Handle specific condition case #}
{% endif %}
```

### 3. Comment Placement Standards

**Template logic comments go ABOVE the relevant code:**

```django
{# Smart medical code display strategy based on coverage percentage #}
{% if medical_coverage >= 75 %}
    {# High coverage: show prominent medical codes #}
    {% with show_codes_prominent=True %}

{# Medium coverage: collapse codes by default #}
{% elif medical_coverage >= 25 %}
    {% with show_codes_collapsed=True %}

{# Low coverage: hide codes unless requested #}
{% else %}
    {% with hide_codes=True %}
{% endif %}
```

**Closing tag comments explain what's being closed:**

```django
{# End of clinical data processing loop #}
{% endfor %}

{# Close medical coverage context variables #}
{% endwith %}

{# End conditional medical code display #}
{% endif %}
```

### 4. Comment Content Guidelines

**Be descriptive and purposeful:**

```django
{# Render mobile-optimized clinical cards with smart pagination #}
{# Show first 3 entries for large datasets (16+ entries) #}
{# Apply medical terminology badges based on data quality #}
```

**Avoid obvious comments:**

```django
{# BAD: Obvious and adds no value #}
{% if user.is_authenticated %} {# Check if user is authenticated #}

{# GOOD: Explains business logic #}
{% if user.is_authenticated %} {# Only authenticated users can view clinical data #}
```

### 5. Template Section Documentation

**Document major template sections:**

```django
{# =============================================== #}
{# MOBILE CARD LAYOUT - Hidden on desktop #}
{# =============================================== #}
<div class="d-block d-md-none">

{# =============================================== #}
{# DESKTOP TABLE LAYOUT - Hidden on mobile #}
{# =============================================== #}
<div class="d-none d-md-block">
```

## Security Considerations

- Never include patient names, IDs, or sensitive data in comments
- Avoid exposing internal system architecture details
- Comments should not reveal security-sensitive logic

## Maintainability Requirements

- Comments should explain WHY, not WHAT
- Update comments when template logic changes
- Remove outdated or incorrect comments immediately
- Use consistent terminology across all templates

## Testing Requirements

- Template comments must not affect rendered output
- Comments should not break template compilation
- All templates with comments must pass Django template validation

## Implementation Checklist

- [ ] Remove all inline HTML comments from Django template tags
- [ ] Convert template logic explanations to Django template comments
- [ ] Place all comments on separate lines above relevant code
- [ ] Document major template sections with descriptive headers
- [ ] Validate all templates compile correctly after comment updates
- [ ] Test rendered output remains unchanged

## Examples

### Before (Problematic)

```django
{% endwith %} <!-- Close medical coverage context -->
{% if entry_count > 15 %} <!-- Large datasets -->
<div class="pagination"> <!-- Pagination controls -->
```

### After (Compliant)

```django
{# Close medical coverage context variables #}
{% endwith %}

{# Handle large datasets with smart pagination #}
{% if entry_count > 15 %}
    {# Pagination controls for datasets with 16+ entries #}
    <div class="pagination">
```

## Enforcement

- All new templates must follow these standards
- Existing templates should be updated during maintenance
- Code reviews must verify comment compliance
- Automated tests should catch template compilation errors

---

**References:**

- [Django Template Language Documentation](https://docs.djangoproject.com/en/stable/ref/templates/language/)
- [Django_NCP Coding Standards](../CODING_STANDARDS.md)
- [Template Security Guidelines](../SECURITY_GUIDELINES.md)
