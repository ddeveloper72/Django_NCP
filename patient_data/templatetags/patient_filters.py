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
def basename(path):
    """Extract the basename (filename) from a file path"""
    import os

    if not path:
        return ""
    return os.path.basename(path)
