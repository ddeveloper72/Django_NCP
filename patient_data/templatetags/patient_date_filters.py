"""
Django template filters for patient date formatting
"""

from django import template
from django.utils.safestring import mark_safe
from patient_data.utils.date_formatter import (
    format_birth_date,
    format_document_date,
    format_birth_date_with_age,
    default_formatter,
)

register = template.Library()


@register.filter
def patient_birth_date(value):
    """
    Format a patient's birth date for consistent display.

    Usage in template:
    {{ patient.birth_date|patient_birth_date }}

    Input: "19700101" or "1970-01-01" or datetime object
    Output: "01/01/1970" (European format)
    """
    return format_birth_date(value)


@register.filter
def patient_birth_date_with_age(value):
    """
    Format a patient's birth date with calculated age.

    Usage in template:
    {{ patient.birth_date|patient_birth_date_with_age }}

    Input: "19700101"
    Output: "01/01/1970 (54 years old)"
    """
    return format_birth_date_with_age(value)


@register.filter
def document_date(value):
    """
    Format a document date (creation, effective time, etc.).

    Usage in template:
    {{ document.creation_date|document_date }}

    Input: "20080728130000+0100"
    Output: "28/07/2008 13:00"
    """
    return format_document_date(value)


@register.filter
def patient_age(value):
    """
    Calculate and display patient age from birth date.

    Usage in template:
    {{ patient.birth_date|patient_age }}

    Input: "19700101"
    Output: "54"
    """
    age = default_formatter.get_age_from_birth_date(value)
    return str(age) if age is not None else "Unknown"


@register.simple_tag
def format_date_range(start_date, end_date=None):
    """
    Format a date range for display.

    Usage in template:
    {% format_date_range treatment.start_date treatment.end_date %}

    Output: "01/01/2020 - 31/12/2020" or "01/01/2020 - ongoing"
    """
    start_formatted = format_document_date(start_date)

    if end_date:
        end_formatted = format_document_date(end_date)
        return mark_safe(f"{start_formatted} - {end_formatted}")
    else:
        return mark_safe(f"{start_formatted} - ongoing")


@register.inclusion_tag("patient_data/partials/patient_age_badge.html")
def patient_age_badge(birth_date, css_class="age-badge"):
    """
    Render a patient age badge with styling.

    Usage in template:
    {% patient_age_badge patient.birth_date %}
    {% patient_age_badge patient.birth_date "custom-age-class" %}
    """
    age = default_formatter.get_age_from_birth_date(birth_date)
    formatted_date = format_birth_date(birth_date)

    return {
        "age": age,
        "birth_date": formatted_date,
        "css_class": css_class,
        "has_age": age is not None,
    }
