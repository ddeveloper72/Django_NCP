"""
Template filters for cleaning clinical data display
Remove technical clutter and show only medically relevant information
"""

import re

from django import template

register = template.Library()


@register.filter
def clean_clinical_value(value, field_type=None):
    """
    Extract clean clinical value based on field type
    Args:
        value: The raw field data (could be dict or string)
        field_type: The type of field (code, description, date, status)
    """
    if not value:
        return "N/A"

    # If it's a dict with clinical data
    if isinstance(value, dict):
        # For code fields, get the actual code
        if field_type == "code":
            return value.get("code", value.get("value", "N/A"))

        # For description fields, get the display name or value
        elif field_type == "description":
            return value.get(
                "display_name", value.get("displayName", value.get("value", "N/A"))
            )

        # For date fields, get the value
        elif field_type == "date":
            date_val = value.get("value", value.get("effectiveTime", "N/A"))
            if date_val and date_val != "N/A":
                # Clean up date format if needed
                return clean_date_format(date_val)
            return date_val

        # For status fields, get the status code or value
        elif field_type == "status":
            return value.get(
                "status_code", value.get("statusCode", value.get("value", "N/A"))
            )

        # Default: get the most meaningful value
        else:
            return value.get(
                "display_name", value.get("displayName", value.get("value", str(value)))
            )

    # If it's just a string, return it cleaned
    elif isinstance(value, str):
        return clean_string_value(value)

    # Fallback
    return str(value) if value else "N/A"


@register.filter
def clean_string_value(value):
    """Clean up string values by removing technical artifacts"""
    if not value or value == "N/A":
        return value

    # Remove common technical prefixes/suffixes
    value = str(value).strip()

    # Remove XPath references
    value = re.sub(r"XPath:\s*[^\s]+", "", value)

    # Remove Section references
    value = re.sub(r"Section:\s*[^\s]+", "", value)

    # Remove Type references when not wanted
    value = re.sub(r"Type:\s*[^\s]+", "", value)

    # Remove "Translation needed" text
    value = re.sub(r"Translation needed", "", value)

    # Remove "Coded value available" text
    value = re.sub(r"Coded value available", "", value)

    # Clean up extra whitespace
    value = re.sub(r"\s+", " ", value).strip()

    return value if value else "N/A"


@register.filter
def clean_date_format(date_value):
    """Clean up date formatting"""
    if not date_value:
        return "N/A"

    date_str = str(date_value).strip()

    # If it already looks like a clean date, return it
    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_str):
        return date_str

    # If it's in ISO format, convert it
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
        try:
            from datetime import datetime

            parsed_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return parsed_date.strftime("%d/%m/%Y")
        except:
            pass

    # If it's in another format, try to extract just the date part
    date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", date_str)
    if date_match:
        return date_match.group(1)

    return date_str


@register.filter
def extract_procedure_code(value):
    """Extract just the procedure code from complex data"""
    return clean_clinical_value(value, "code")


@register.filter
def extract_procedure_description(value):
    """Extract just the procedure description from complex data"""
    return clean_clinical_value(value, "description")


@register.filter
def extract_date(value):
    """Extract just the date from complex data"""
    return clean_clinical_value(value, "date")


@register.filter
def extract_status(value):
    """Extract just the status from complex data"""
    return clean_clinical_value(value, "status")
