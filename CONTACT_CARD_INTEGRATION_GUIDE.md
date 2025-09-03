# Contact Card System Integration Guide

## Overview

The contact card system provides standardized templates for displaying all administrative contacts with consistent layouts and responsive design.

## Quick Setup

### 1. Load Template Tags

Add to the top of any template where you want to use contact cards:

```django
{% load contact_cards %}
```

### 2. Include CSS

Add to your base template's `<head>` section:

```html
<link rel="stylesheet" href="{% static 'patient_data/css/contact_cards.css' %}">
```

### 3. Basic Usage

#### Single Contact Card

```django
{% contact_card legal_authenticator 'Legal Authenticator' 'legal_auth' %}
{% contact_card custodian 'Document Custodian' 'custodian' %}
{% contact_card patient_contact 'Patient Contact' 'patient' %}
```

#### Multiple Contact Cards (Authors)

```django
{% contact_card_list authors 'Document Authors' 'author' %}
```

## Template Integration Examples

### Replace Existing Legal Authenticator Display

**Before:**

```html
<div class="legal-authenticator">
    <h3>Legal Authenticator</h3>
    <p>{{ legal_authenticator.title }} {{ legal_authenticator.given_name }} {{ legal_authenticator.family_name }}</p>
    <!-- Complex nested access patterns -->
</div>
```

**After:**

```django
{% load contact_cards %}
{% contact_card legal_authenticator 'Legal Authenticator' 'legal_auth' %}
```

### Complete Administrative Section

```django
{% load contact_cards %}

<div class="administrative-section">
    <h2>Administrative Information</h2>
    
    {% if legal_authenticator %}
        {% contact_card legal_authenticator 'Legal Authenticator' 'legal_auth' %}
    {% endif %}
    
    {% if custodian %}
        {% contact_card custodian 'Document Custodian' 'custodian' %}
    {% endif %}
    
    {% if patient_contact %}
        {% contact_card patient_contact 'Patient Contact' 'patient' %}
    {% endif %}
    
    {% if authors %}
        {% contact_card_list authors 'Document Authors' 'author' %}
    {% endif %}
</div>
```

## Template Filters

Use these filters for simple text extraction:

```django
{{ legal_authenticator|get_contact_name }}
{{ legal_authenticator|get_organization_name }}
{{ legal_authenticator|get_contact_address }}
{{ legal_authenticator|get_contact_phone }}
{{ legal_authenticator|get_contact_email }}
```

## Card Types and Styling

The system supports different card types with color-coded headers:

- `patient` - Blue header for patient contacts
- `legal_auth` - Green header for legal authenticators  
- `custodian` - Orange header for custodians
- `author` - Purple header for document authors

## Responsive Design

Cards automatically adapt to screen size:

- **Desktop:** Side-by-side layout for multiple cards
- **Tablet:** Stacked cards with comfortable spacing
- **Mobile:** Full-width single column

## Error Handling

The system gracefully handles missing data:

- Empty fields are hidden automatically
- Missing contacts show appropriate empty states
- Malformed data is normalized safely

## Customization

### Custom Card Types

Add new card types in `contact_cards.css`:

```css
.contact-card.specialist .card-header {
    background: linear-gradient(135deg, #e91e63, #f06292);
}
```

### Template Overrides

Override the base template by creating:
`patient_data/templates/patient_data/contact_card.html`

## Testing

Run the test script to verify integration:

```bash
python test_contact_card_system.py
```

## Troubleshooting

### Common Issues

1. **Template tag not found:**
   - Ensure `{% load contact_cards %}` is at the top
   - Check that `patient_data` is in `INSTALLED_APPS`

2. **Styling not applied:**
   - Verify CSS file is included in base template
   - Check static files are served correctly

3. **Missing data:**
   - Use template filters to debug: `{{ contact|get_contact_name }}`
   - Check that administrative extraction is working

4. **Layout issues:**
   - Ensure parent container has appropriate CSS
   - Check for CSS conflicts with existing styles

## Migration from Old Templates

1. **Identify existing contact displays** in your templates
2. **Replace with contact card tags** using the examples above
3. **Remove old CSS** for contact styling
4. **Include new CSS** for contact cards
5. **Test responsive behavior** on different screen sizes

## Performance Notes

- Template tags use efficient data normalization
- CSS uses modern layout methods (Grid/Flexbox)
- No JavaScript dependencies required
- Cards lazy-load missing data gracefully
