"""
Custom template tags for patient data
"""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Template filter to look up dictionary values"""
    return dictionary.get(key, [])


@register.filter
def dict_key(dictionary, key):
    """Template filter to access dictionary keys"""
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    return value * arg


@register.filter
def get_item(dictionary, key):
    """Template filter to get item from dictionary by key - equivalent to dictionary[key]"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    elif hasattr(dictionary, "__getitem__"):
        try:
            return dictionary[key]
        except (KeyError, IndexError, TypeError):
            return None
    return None


@register.filter
def dict_items(dictionary):
    """Template filter to get dictionary items - equivalent to dictionary.items()"""
    if isinstance(dictionary, dict):
        return dictionary.items()
    elif hasattr(dictionary, "items"):
        return dictionary.items()
    return []


@register.filter
def subtract(value, arg):
    """Template filter to subtract arg from value - equivalent to value - arg"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def safe_get(data, key):
    """Template filter to safely get a value from dictionary or object, handling missing keys gracefully"""
    if isinstance(data, dict):
        if key in data:
            return data[key]
        # Handle different data structures
        if key == "value" and "count" in data:
            return data["count"]
        elif key == "count" and "value" in data:
            return data["value"]
        return None
    elif hasattr(data, key):
        return getattr(data, key, None)
    return None


@register.filter
def replace(value, args):
    """Template filter to replace strings - equivalent to value.replace(old, new)"""
    if value is None:
        return value

    try:
        # Parse comma-separated arguments
        if isinstance(args, str) and "," in args:
            old, new = args.split(",", 1)
            old = old.strip().strip("\"'")
            new = new.strip().strip("\"'")
        else:
            # Single argument - replace with empty string
            old = str(args).strip("\"'")
            new = ""

        return str(value).replace(old, new)
    except (ValueError, AttributeError):
        return value


@register.filter
def clean_telecom(value):
    """Template filter to clean telecom values by removing mailto: and tel: prefixes"""
    if value is None:
        return value

    cleaned = str(value)
    cleaned = cleaned.replace("mailto:", "")
    cleaned = cleaned.replace("tel:", "")
    return cleaned


@register.filter
def count_contact_items(administrative_data):
    """Count total contact items (addresses + telecoms) from administrative data"""
    if not administrative_data:
        return 0

    contact_info = safe_get(administrative_data, "patient_contact_info")
    if not contact_info:
        return 0

    addresses = safe_get(contact_info, "addresses") or []
    telecoms = safe_get(contact_info, "telecoms") or []

    return len(addresses) + len(telecoms)


@register.filter
def count_healthcare_team(administrative_data):
    """Count healthcare team members from administrative data"""
    if not administrative_data:
        return 0

    count = 0

    # Check author HCP
    author_hcp = safe_get(administrative_data, "author_hcp")
    if author_hcp:
        given_name = safe_get(author_hcp, "given_name") or ""
        family_name = safe_get(author_hcp, "family_name") or ""
        if given_name.strip() or family_name.strip():
            count += 1

    # Check legal authenticator
    legal_auth = safe_get(administrative_data, "legal_authenticator")
    if legal_auth:
        given_name = safe_get(legal_auth, "given_name") or ""
        family_name = safe_get(legal_auth, "family_name") or ""
        if given_name.strip() or family_name.strip():
            count += 1

    # Check custodian organization
    custodian = safe_get(administrative_data, "custodian_organization")
    if custodian:
        name = safe_get(custodian, "name") or ""
        if name.strip():
            count += 1

    return count


@register.filter
def has_administrative_data(administrative_info):
    """
    Check if administrative_info has any meaningful data
    Returns True if any of the key administrative fields have data
    """
    if not administrative_info:
        return False

    # Check for any of the main administrative data fields
    return (
        administrative_info.get("patient_contact")
        or administrative_info.get("legal_authenticator")
        or administrative_info.get("custodian")
        or administrative_info.get("authors")
    )


@register.filter
@register.filter
def basename(path):
    """Extract the basename (filename) from a file path"""
    import os

    if not path:
        return ""
    return os.path.basename(path)


# Clinical Data Cleaning Filters
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
    import re

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
    import re

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
def extract_code(value):
    """Extract just the code from complex data (generic code extractor)"""
    return clean_clinical_value(value, "code")


@register.filter
def extract_problem_code(value):
    """Extract just the problem code from complex data"""
    return clean_clinical_value(value, "code")


@register.filter
def extract_active_ingredient_code(value):
    """Extract just the active ingredient code from complex data"""
    return clean_clinical_value(value, "code")


@register.filter
def extract_medication_code(value):
    """Extract just the medication code from complex data"""
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


@register.filter
def country_flag(country_code):
    """Return flag image path for a given country code"""
    if not country_code:
        return None

    # Convert to uppercase for consistency
    country_code = country_code.upper()

    # Map of all available flag files in static/flags/
    available_flags = {
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "EU",
        "FI",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IS",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "NO",
        "PL",
        "PT",
        "RO",
        "SE",
        "SI",
        "SK",
        "UK",
    }

    # Return flag path if available, otherwise return EU flag as fallback
    if country_code in available_flags:
        return f"flags/{country_code}.webp"
    else:
        return "flags/EU.webp"


@register.filter
def country_name(country_code):
    """Return full country name for a given country code"""
    if not country_code:
        return "Unknown"

    # Map of country codes to full names
    country_names = {
        "AT": "Austria",
        "BE": "Belgium",
        "BG": "Bulgaria",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DE": "Germany",
        "DK": "Denmark",
        "EE": "Estonia",
        "ES": "Spain",
        "EU": "European Union",
        "FI": "Finland",
        "FR": "France",
        "GR": "Greece",
        "HR": "Croatia",
        "HU": "Hungary",
        "IE": "Ireland",
        "IS": "Iceland",
        "IT": "Italy",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "LV": "Latvia",
        "MT": "Malta",
        "NL": "Netherlands",
        "NO": "Norway",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "SE": "Sweden",
        "SI": "Slovenia",
        "SK": "Slovakia",
        "UK": "United Kingdom",
    }

    return country_names.get(country_code.upper(), country_code.upper())
