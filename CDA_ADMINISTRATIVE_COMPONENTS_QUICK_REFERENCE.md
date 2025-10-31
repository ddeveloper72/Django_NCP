# CDA Administrative Components - Quick Reference

## Component File Locations

All components are located in: `templates/patient_data/components/administrative/`

```
administrative/
├── assigned_author.html          # CDA <author> - Medical doctor
├── custodian.html                # CDA <custodian> - Document custodian org
├── legal_authenticator.html      # CDA <legalAuthenticator> - Document signer
├── participant.html              # CDA <participant> - Contact persons
└── documentation_of.html         # CDA <documentationOf> - Service events
```

## Quick Include Reference

### In Parent Templates

```django
{# Include all administrative components #}
{% include 'patient_data/components/administrative/assigned_author.html' %}
{% include 'patient_data/components/administrative/custodian.html' %}
{% include 'patient_data/components/administrative/legal_authenticator.html' %}
{% include 'patient_data/components/administrative/participant.html' %}
{% include 'patient_data/components/administrative/documentation_of.html' %}
```

### With Custom Context

```django
{# Include specific component with context #}
{% include 'patient_data/components/administrative/assigned_author.html' with author_hcp=custom_author %}
```

## Context Requirements

### 1. Assigned Author Component

**Context Variable**: `author_hcp` (DotDict)

**Required Fields**:
- `full_name` (string)

**Optional Fields**:
- `given_name`, `family_name` (strings)
- `role` (string)
- `contact_info.addresses[]` (list of address dicts)
- `contact_info.telecoms[]` (list of telecom dicts)
- `organization.name` (string)
- `organization.contact_info.addresses[]`, `organization.contact_info.telecoms[]`
- `organization.identifiers[]` (list)
- `timestamp` (string)

**Example**:
```python
context['author_hcp'] = {
    'full_name': 'António Pereira',
    'role': 'Author',
    'contact_info': {
        'addresses': [{'street': 'Rua...', 'city': 'Lisboa', 'postal_code': '1169-050'}],
        'telecoms': [{'value': 'tel:+351214000000', 'use': 'work'}]
    },
    'organization': {
        'name': 'Centro Hospitalar de Lisboa Central',
        'contact_info': {...},
        'identifiers': [{'root': '2.16.840...', 'extension': 'CHLC'}]
    },
    'timestamp': '20100701000000-0200'
}
```

### 2. Custodian Component

**Context Variable**: `custodian_organization` (DotDict)

**Required Fields**:
- `name` (string)

**Optional Fields**:
- `contact_info.addresses[]` (list)
- `contact_info.telecoms[]` (list)
- `identifiers[]` (list with root/extension)

**Example**:
```python
context['custodian_organization'] = {
    'name': 'Centro Hospitalar de Lisboa Central',
    'contact_info': {
        'addresses': [...],
        'telecoms': [...]
    },
    'identifiers': [{'root': '...', 'extension': '...'}]
}
```

### 3. Legal Authenticator Component

**Context Variable**: `legal_authenticator` (DotDict)

**Structure**: Same as `author_hcp` with additional `timestamp` for authentication time

**Required Fields**:
- `full_name` (string)

**Example**:
```python
context['legal_authenticator'] = {
    'full_name': 'António Pereira',
    'role': 'Legal Authenticator',
    'timestamp': '20100701000000-0200',
    'contact_info': {...},
    'organization': {...}
}
```

### 4. Participant Component

**Context Variable**: `participants` (List of DotDict)

**Required Fields per Participant**:
- `full_name` (string)

**Optional Fields**:
- `relationship_code` (string, e.g., 'WIFE', 'SON')
- `relationship_display` (string, e.g., 'Wife', 'Son')
- `contact_info.addresses[]`, `contact_info.telecoms[]`
- `organization` (dict, optional associated organization)
- `time` (string, when contact was designated)

**Example**:
```python
context['participants'] = [
    {
        'full_name': 'Vitória Silva',
        'relationship_code': 'WIFE',
        'relationship_display': 'Wife',
        'contact_info': {
            'addresses': [...],
            'telecoms': [
                {'value': 'tel:+351966123456', 'use': 'mobile'},
                {'value': 'mailto:vitoria@email.com'}
            ]
        },
        'organization': None,  # Optional
        'time': '20100701'
    }
]
```

### 5. Documentation Of Component

**Context Variable**: `documentation_of` (DotDict)

**Optional Fields** (all optional, component checks for presence):
- `effective_time.low`, `effective_time.high` (strings)
- `performers[]` (list of performer dicts)
- `code`, `code_system` (strings)

**Performer Structure** (within `performers[]`):
- `full_name` (string)
- `role`, `function_code` (strings)
- `time.low`, `time.high` (strings)
- `contact_info.addresses[]`, `contact_info.telecoms[]`
- `organization` (dict, similar to author organization)

**Example**:
```python
context['documentation_of'] = {
    'effective_time': {
        'low': '20100101',
        'high': '20101231'
    },
    'performers': [
        {
            'full_name': 'António Pereira',
            'role': 'Primary Performer',
            'function_code': 'PRF',
            'time': {'low': '20100101', 'high': '20101231'},
            'contact_info': {...},
            'organization': {
                'name': 'Centro Hospitalar...',
                'contact_info': {...},
                'identifiers': [...]
            }
        }
    ],
    'code': 'PCPR',
    'code_system': '2.16.840.1.113883.5.4'
}
```

## Color Coding Reference

Each component uses a specific Bootstrap color scheme:

| Component | Color | Bootstrap Class | Semantic Meaning |
|-----------|-------|----------------|------------------|
| Assigned Author | Blue | `border-primary`, `bg-primary` | Primary document creator |
| Custodian | Blue | `border-info`, `bg-info` | Informational, document management |
| Legal Authenticator | Green | `border-success`, `bg-success` | Legal validation, authenticated |
| Participant | Yellow/Orange | `border-warning`, `bg-warning` | Important contact, attention needed |
| Documentation Of | Gray | `border-secondary`, `bg-secondary` | Metadata, supporting information |

## Icon Reference

Common FontAwesome icons used in components:

### People
- `fa-user-md`, `fa-user-doctor` - Medical professionals
- `fa-user-shield` - Legal authenticator
- `fa-user-group` - Contact persons/participants
- `fa-user-check` - Performer/validated person

### Organizations
- `fa-hospital` - Healthcare organization
- `fa-building` - General organization
- `fa-shield` - Custodian (protection)

### Contact Information
- `fa-location-dot` - Address
- `fa-phone` - Phone number
- `fa-envelope` - Email address
- `fa-address-card` - Contact section header
- `fa-address-book` - Organization contact

### Document/Legal
- `fa-certificate` - Legal authentication
- `fa-file-medical` - Medical documentation
- `fa-calendar-check` - Authentication timestamp
- `fa-clock` - General timestamp
- `fa-calendar-days`, `fa-calendar-plus`, `fa-calendar-minus` - Date ranges

### Identifiers
- `fa-id-card` - Organization IDs
- `fa-code` - System codes

## Conditional Rendering

All components use safe conditional rendering:

```django
{# Component only renders if required data exists #}
{% if author_hcp %}
    {# Main component structure #}
    
    {# Nested sections also check for data #}
    {% if author_hcp.full_name %}
        {# Display name #}
    {% endif %}
    
    {# Lists are safely looped #}
    {% if author_hcp.contact_info.addresses %}
        {% for address in author_hcp.contact_info.addresses %}
            {# Display address #}
        {% endfor %}
    {% endif %}
{% endif %}
```

**Result**: Components gracefully handle missing data without breaking layout.

## Context Builder Integration

Components automatically receive context from `context_builders.py`:

```python
# In context_builders.py add_administrative_data() method

# Extract and convert dataclass to dict
author_hcp = getattr(admin_data, 'author_hcp', None)
if author_hcp and is_dataclass(author_hcp):
    context['author_hcp'] = asdict(author_hcp)  # Convert to dict for template

# Components automatically access this context
```

**No Manual Context Required** - Just include the component template, and it will access the appropriate context variables.

## Testing Components

### Quick Test Template

Create a test template to verify component rendering:

```django
{% extends 'base.html' %}

{% block content %}
<div class="container mt-4">
    <h2>Administrative Components Test</h2>
    
    {# Test each component individually #}
    <h3>1. Assigned Author</h3>
    {% include 'patient_data/components/administrative/assigned_author.html' %}
    
    <h3>2. Custodian</h3>
    {% include 'patient_data/components/administrative/custodian.html' %}
    
    <h3>3. Legal Authenticator</h3>
    {% include 'patient_data/components/administrative/legal_authenticator.html' %}
    
    <h3>4. Participants</h3>
    {% include 'patient_data/components/administrative/participant.html' %}
    
    <h3>5. Documentation Of</h3>
    {% include 'patient_data/components/administrative/documentation_of.html' %}
</div>
{% endblock %}
```

### Test with Django Shell

```python
from patient_data.services.cda_header_extractor import CDAHeaderExtractor
from dataclasses import asdict
import lxml.etree as ET

# Load CDA document
tree = ET.parse('path/to/cda.xml')
root = tree.getroot()

# Extract administrative data
extractor = CDAHeaderExtractor()
admin_data = extractor.extract_administrative_data(root)

# Convert to dict for template
context = {}
if admin_data.author_hcp:
    context['author_hcp'] = asdict(admin_data.author_hcp)

# Check what data is available
print(f"Author: {context['author_hcp']['full_name']}")
print(f"Organization: {context['author_hcp']['organization']['name']}")
```

## Common Issues & Solutions

### Issue: Component Not Displaying

**Cause**: Missing required context variable

**Solution**: Check that context contains the expected variable name:
```python
# In view or context_builders.py
print(f"Context keys: {context.keys()}")
print(f"author_hcp present: {'author_hcp' in context}")
```

### Issue: Nested Fields Not Accessible

**Cause**: Dataclass not converted to dict

**Solution**: Use `asdict()` in context_builders.py:
```python
from dataclasses import asdict, is_dataclass

if is_dataclass(author_hcp):
    context['author_hcp'] = asdict(author_hcp)
```

### Issue: List Items Not Displaying

**Cause**: List contains dataclass objects instead of dicts

**Solution**: Convert list items:
```python
participants_list = getattr(admin_data, 'participants', []) or []
context['participants'] = [
    asdict(p) if is_dataclass(p) else p for p in participants_list
]
```

### Issue: Organization Details Missing

**Cause**: Organization is nested dataclass not converted

**Solution**: `asdict()` recursively converts nested dataclasses:
```python
# This converts organization automatically
context['author_hcp'] = asdict(author_hcp)

# author_hcp.organization becomes a dict too
```

## Performance Considerations

### Component Rendering

- Each component is a separate include = separate template parse
- For pages with many administrative sections, consider:
  - Template fragment caching
  - Lazy loading for less critical components
  - Conditional includes based on user role

### Dataclass Conversion

- `asdict()` is recursive and can be expensive for deeply nested structures
- Convert once in context_builders.py, not in template
- Consider caching converted administrative data for session

### Example Caching

```python
# In context_builders.py or view processor
from django.core.cache import cache

cache_key = f"admin_data_{session_id}"
admin_dict = cache.get(cache_key)

if not admin_dict:
    admin_dict = asdict(admin_data)
    cache.set(cache_key, admin_dict, timeout=3600)  # 1 hour

context['author_hcp'] = admin_dict.get('author_hcp')
```

## Customization Examples

### Adding Custom Styling

```django
{# Include with custom CSS class #}
<div class="my-custom-wrapper">
    {% include 'patient_data/components/administrative/assigned_author.html' %}
</div>

{# Or override component colors inline #}
<style>
.assigned-author-section .card-header {
    background-color: #custom-color !important;
}
</style>
```

### Filtering Displayed Fields

```django
{# Include only if specific condition met #}
{% if author_hcp and author_hcp.role == 'Consultant' %}
    {% include 'patient_data/components/administrative/assigned_author.html' %}
{% endif %}
```

### Reusing in Different Contexts

```django
{# In a different template, use same component with different data source #}
{% with author_hcp=fhir_practitioner %}
    {% include 'patient_data/components/administrative/assigned_author.html' %}
{% endwith %}
```

## Component File Sizes

Reference for component complexity:

| Component | Lines | Complexity |
|-----------|-------|-----------|
| assigned_author.html | 165 | High - Multiple sections with organization |
| custodian.html | 85 | Low - Single organization display |
| legal_authenticator.html | 150+ | High - Similar to assigned author |
| participant.html | 165+ | Medium-High - Loop with optional organization |
| documentation_of.html | 200+ | High - Nested loops for performers |

## Maintenance Checklist

When updating components:

- [ ] Update component template file
- [ ] Check context requirements in component comments
- [ ] Update this quick reference if context changes
- [ ] Test with sample data
- [ ] Check conditional rendering for edge cases
- [ ] Verify Bootstrap classes are current version
- [ ] Test responsive design (mobile/tablet/desktop)
- [ ] Run accessibility checks
- [ ] Update unit tests
- [ ] Document changes in git commit

## Related Documentation

- **Full Refactoring Summary**: `CDA_ADMINISTRATIVE_COMPONENTS_REFACTORING.md`
- **Context Builders**: `patient_data/view_processors/context_builders.py`
- **CDA Header Extractor**: `patient_data/services/cda_header_extractor.py`
- **Parent Template**: `templates/patient_data/components/healthcare_team_content.html`
- **SCSS Standards**: `.specs/scss-standards-index.md`
- **Testing Standards**: `.specs/testing-and-modular-code-standards.md`
