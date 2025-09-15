# Django Template Best Practices

## Handling Complex Conditions

### Problem

Django templates don't handle multi-line conditions well. This causes syntax errors:

```django
<!-- ❌ AVOID: Multi-line conditions -->
{% if not data.field1 and not data.field2 and not
data.field3 and not data.field4 %}
    <!-- Content -->
{% endif %}
```

### Solutions

#### 1. Custom Template Filters (RECOMMENDED)

Create reusable filters for complex logic:

```python
# In templatetags/app_filters.py
@register.filter
def has_administrative_data(administrative_info):
    """Check if administrative_info has any meaningful data"""
    if not administrative_info:
        return False

    return (
        administrative_info.get('patient_contact') or
        administrative_info.get('legal_authenticator') or
        administrative_info.get('custodian') or
        administrative_info.get('authors')
    )
```

```django
<!-- ✅ GOOD: Using custom filter -->
{% load app_filters %}
{% if not administrative_info|has_administrative_data %}
    <div class="empty-state">No data available</div>
{% endif %}
```

#### 2. Template Variables with `with` Tag

For simpler cases, use template variables:

```django
<!-- ✅ GOOD: Using with statement -->
{% with has_data=administrative_info.patient_contact %}
{% if not has_data %}
    <div class="empty-state">No data available</div>
{% endif %}
{% endwith %}
```

#### 3. View-Level Processing

Handle complex logic in views and pass simple boolean flags:

```python
# In views.py
context = {
    'has_administrative_data': bool(
        admin_info.get('patient_contact') or
        admin_info.get('legal_authenticator') or
        admin_info.get('custodian') or
        admin_info.get('authors')
    )
}
```

```django
<!-- ✅ GOOD: Simple boolean from view -->
{% if not has_administrative_data %}
    <div class="empty-state">No data available</div>
{% endif %}
```

## Template Filter Benefits

1. **Reusability**: Use the same logic across multiple templates
2. **Testability**: Can unit test the filter logic separately
3. **Readability**: Template becomes more semantic and readable
4. **Maintainability**: Logic changes in one place
5. **Performance**: Complex logic runs in Python, not template engine

## When to Use Each Approach

- **Custom Filters**: Complex, reusable logic used in multiple templates
- **Template Variables**: Simple conditions used only in one template
- **View Processing**: Very complex logic or when you need database queries

## Example Filter Implementation

```python
from django import template

register = template.Library()

@register.filter
def has_administrative_data(administrative_info):
    """Check if administrative_info has any meaningful data"""
    if not administrative_info:
        return False

    return (
        administrative_info.get('patient_contact') or
        administrative_info.get('legal_authenticator') or
        administrative_info.get('custodian') or
        administrative_info.get('authors')
    )

@register.filter
def is_empty_or_none(value):
    """Check if value is None, empty string, empty list, etc."""
    if value is None:
        return True
    if hasattr(value, '__len__'):
        return len(value) == 0
    return not bool(value)
```

## Template Usage

```django
{% load patient_filters %}

<!-- Check for administrative data -->
{% if administrative_info|has_administrative_data %}
    {% include 'admin_section.html' %}
{% else %}
    <div class="alert alert-info">No administrative information available</div>
{% endif %}

<!-- Check for empty values -->
{% if not patient.allergies|is_empty_or_none %}
    <div class="allergies-section">
        <!-- Render allergies -->
    </div>
{% endif %}
```
