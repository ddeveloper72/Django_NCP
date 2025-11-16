"""
Custom template tags for patient data
"""

from django import template

register = template.Library()


# Import extended filters implemented for Jinja-style rendering and expose them to Django templates
try:
    # normalize_display coerces dict/list values into readable strings
    from patient_data.template_filters import normalize_display as _normalize_display
except Exception:  # pragma: no cover - graceful fallback if module path changes
    _normalize_display = None


@register.filter(name="normalize_display")
def normalize_display_filter(value):
    """Normalize complex values (dict/list) into a human-friendly display string.

    Delegates to patient_data.template_filters.normalize_display when available.
    """
    if _normalize_display is None:
        # Fallback: basic stringify to avoid TemplateSyntaxError
        return "" if value is None else (", ".join(map(str, value)) if isinstance(value, list) else str(value))
    return _normalize_display(value)


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

    # Handle CDA date format (YYYYMMDD) - convert to DD/MM/YYYY
    if re.match(r"^\d{8}$", date_str):
        try:
            from datetime import datetime
            parsed_date = datetime.strptime(date_str, "%Y%m%d")
            return parsed_date.strftime("%d/%m/%Y")
        except:
            pass

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
    """Return flag image HTML for a given country code"""
    from django.templatetags.static import static
    from django.utils.safestring import mark_safe

    if not country_code:
        return ""

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

    # Get flag path
    if country_code in available_flags:
        flag_path = f"flags/{country_code}.webp"
    else:
        flag_path = "flags/EU.webp"

    # Get full country name for alt text
    country_name = country_names.get(country_code, country_code)

    # Return proper HTML img tag with CSS class instead of inline styles
    static_path = static(flag_path)
    html = f'<img src="{static_path}" alt="{country_name}" class="flag-img" width="20" height="15">'
    return mark_safe(html)


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


@register.filter
def handle_null_flavor(value, null_flavor=None):
    """
    Handle nullFlavor values according to HL7 CDA specification.

    HL7 CDA nullFlavor codes:
    - UNK: Unknown - information is not available
    - NA: Not Applicable - information is not relevant
    - NI: No Information - no information whatsoever can be inferred
    - NINF: Negative Infinity - value is exceptionally low
    - PINF: Positive Infinity - value is exceptionally high
    - OTH: Other - information is available but not represented
    - ASKU: Asked but Unknown - information was sought but not found
    - NAV: Not Available - information is not available at this time
    - MSK: Masked - information is available but has been suppressed
    - NP: Not Present - value is not present
    - TRC: Trace - value is below the limit of detection
    """
    # If value exists and is not empty/None, return it
    if value and str(value).strip():
        return value

    # Handle nullFlavor parameter or check if value itself contains nullFlavor info
    flavor = null_flavor
    if hasattr(value, "get") and isinstance(value, dict):
        flavor = value.get("nullFlavor", flavor)
    elif isinstance(value, str) and value.strip() == "":
        flavor = flavor or "UNK"

    # Return human-readable text for nullFlavor codes
    null_flavor_mappings = {
        "UNK": "Unknown",
        "NA": "Not Applicable",
        "NI": "No Information",
        "NINF": "Very Low",
        "PINF": "Very High",
        "OTH": "Other",
        "ASKU": "Unknown (Asked)",
        "NAV": "Not Available",
        "MSK": "Masked",
        "NP": "Not Present",
        "TRC": "Trace Amount",
    }

    if flavor and flavor in null_flavor_mappings:
        return null_flavor_mappings[flavor]

    # Default fallback for empty/None values
    return "Unknown" if not value else value


@register.filter
def extract_null_flavor(data):
    """
    Extract nullFlavor from complex data structures (dict, object with null_flavor attribute).
    Used in combination with handle_null_flavor filter.
    """
    if isinstance(data, dict):
        return data.get("nullFlavor") or data.get("null_flavor")
    elif hasattr(data, "null_flavor"):
        return getattr(data, "null_flavor")
    elif hasattr(data, "nullFlavor"):
        return getattr(data, "nullFlavor")
    return None


@register.filter
def safe_clinical_display(entry, field_name="display_name"):
    """
    Safely extract clinical display values with nullFlavor handling.
    Used for clinical entries that might have missing data.

    Usage: {{ entry|safe_clinical_display:"display_name" }}
    """
    if not entry:
        return handle_null_flavor(None)

    # Try to get the field value
    if isinstance(entry, dict):
        value = entry.get(field_name)
        null_flavor = extract_null_flavor(entry)
    else:
        value = getattr(entry, field_name, None)
        null_flavor = extract_null_flavor(entry)

    return handle_null_flavor(value, null_flavor)


@register.filter
def format_clinical_value(value, value_type="text"):
    """
    Format clinical values with proper nullFlavor handling and type-specific formatting.

    value_type options:
    - 'text': Standard text display
    - 'date': Date formatting
    - 'numeric': Numeric with units
    - 'code': Clinical code display
    """
    if not value:
        return handle_null_flavor(value)

    # Handle different value types
    if value_type == "date":
        # Handle date values
        if hasattr(value, "get") and isinstance(value, dict):
            date_val = value.get("value", value.get("date"))
            if date_val:
                return date_val
        return handle_null_flavor(value)

    elif value_type == "numeric":
        # Handle numeric values with units
        if hasattr(value, "get") and isinstance(value, dict):
            num_val = value.get("value")
            unit = value.get("unit", "")
            if num_val is not None:
                return f"{num_val} {unit}".strip()
        return handle_null_flavor(value)

    elif value_type == "code":
        # Handle clinical codes
        if hasattr(value, "get") and isinstance(value, dict):
            display = value.get("displayName", value.get("display"))
            code = value.get("code")
            if display:
                return display
            elif code:
                return f"Code: {code}"
        return handle_null_flavor(value)

    # Default text handling
    return handle_null_flavor(value)


@register.filter
def extract_section_title(title_data, prefer="translated"):
    """
    Extract section title from dictionary structure or return string directly

    Args:
        title_data: Either a string or dict with keys: coded, translated, original
        prefer: Which version to prefer ('translated', 'coded', 'original')

    Returns:
        Clean section title string (marked as safe if HTML content detected)
    """
    from django.utils.safestring import mark_safe
    
    if not title_data:
        return "Clinical Section"

    # If it's already a string, check if it's HTML and mark as safe if needed
    if isinstance(title_data, str):
        if '<div' in title_data and 'table-cell-enhanced' in title_data:
            return mark_safe(title_data)
        return title_data

    # If it's a dictionary, extract the preferred version
    if isinstance(title_data, dict):
        result = None
        
        # Try preferred version first
        if prefer in title_data and title_data[prefer]:
            result = str(title_data[prefer])
        else:
            # Fallback order: translated -> coded -> original -> any available
            for key in ["translated", "coded", "original"]:
                if key in title_data and title_data[key]:
                    result = str(title_data[key])
                    break
            
            # If none of the standard keys work, try any available key
            if not result:
                for key, value in title_data.items():
                    if value:
                        result = str(value)
                        break
        
        # Check if result contains HTML and mark as safe if needed
        if result and '<div' in result and 'table-cell-enhanced' in result:
            return mark_safe(result)
        elif result:
            return result

    # Final fallback
    return "Clinical Section"


@register.filter
def extract_display_name(data, prefer="translated"):
    """
    Extract display name from various data structures

    Args:
        data: Could be string, dict, or object with display_name/title attributes
        prefer: Which version to prefer for dictionaries

    Returns:
        Clean display name string
    """
    if not data:
        return "Unknown Item"

    # If it's already a string, return it
    if isinstance(data, str):
        return data

    # If it's a dictionary, try to extract title/display_name
    if isinstance(data, dict):
        # Check for common title fields
        for field in ["display_name", "title", "name"]:
            if field in data:
                field_data = data[field]
                if isinstance(field_data, dict):
                    # Use extract_section_title for nested dictionaries
                    return extract_section_title(field_data, prefer)
                elif field_data:
                    return str(field_data)

        # If it's a translation dictionary, extract using section title logic
        if any(key in data for key in ["coded", "translated", "original"]):
            return extract_section_title(data, prefer)

    # If it's an object with attributes, try common attribute names
    if hasattr(data, "display_name"):
        return str(data.display_name)
    elif hasattr(data, "title"):
        return str(data.title)
    elif hasattr(data, "name"):
        return str(data.name)

    # Final fallback
    return "Unknown Item"


@register.filter
def safe_title_text(title_data):
    """
    Safely extract title text for string operations like 'in' checks
    Returns a safe lowercase string for text matching
    """
    if not title_data:
        return ""

    # Extract clean title first
    clean_title = extract_section_title(title_data)

    # Return lowercase for safe matching
    return clean_title.lower() if clean_title else ""


@register.filter
def count_allergy_observations(allergies):
    """
    Count total allergy observations for badge display.
    For Enhanced CDA format: counts total rows across all clinical tables
    For Legacy format: counts allergy entries
    """
    if not allergies:
        return 0
    
    # Check if we have Enhanced CDA format (clinical_table structure)
    if allergies and hasattr(allergies[0], 'get') and allergies[0].get('clinical_table'):
        total_rows = 0
        for allergy in allergies:
            if hasattr(allergy, 'get') and allergy.get('clinical_table'):
                rows = allergy['clinical_table'].get('rows', [])
                total_rows += len(rows)
        return total_rows
    else:
        # Legacy format: count allergy entries
        return len(allergies)


@register.filter
def count_procedure_observations(procedures):
    """
    Count total procedure observations for badge display.
    For Enhanced CDA format: counts total rows across all clinical tables
    For Legacy format: counts procedure entries
    """
    if not procedures:
        return 0
    
    # Check if we have Enhanced CDA format (clinical_table structure)
    if procedures and hasattr(procedures[0], 'get') and procedures[0].get('clinical_table'):
        total_rows = 0
        for procedure in procedures:
            if hasattr(procedure, 'get') and procedure.get('clinical_table'):
                rows = procedure['clinical_table'].get('rows', [])
                total_rows += len(rows)
        return total_rows
    else:
        # Legacy format: count procedure entries
        return len(procedures)


@register.filter
def count_medical_device_observations(medical_devices):
    """
    Count total medical device observations for badge display.
    For Enhanced CDA format: counts total rows across all clinical tables
    For Legacy format: counts device entries
    """
    if not medical_devices:
        return 0
    
    # Check if we have Enhanced CDA format (clinical_table structure)
    if medical_devices and hasattr(medical_devices[0], 'get') and medical_devices[0].get('clinical_table'):
        total_rows = 0
        for device in medical_devices:
            if hasattr(device, 'get') and device.get('clinical_table'):
                rows = device['clinical_table'].get('rows', [])
                total_rows += len(rows)
        return total_rows
    else:
        # Legacy format: count device entries
        return len(medical_devices)


@register.filter
def total_documents(patients):
    """Calculate total document count for a list of patients"""
    if not patients:
        return 0
    
    total = 0
    for patient in patients:
        if hasattr(patient, 'get'):
            # Dictionary-style access
            l1_count = patient.get('l1_count', 0) or 0
            l3_count = patient.get('l3_count', 0) or 0
        else:
            # Object-style access
            l1_count = getattr(patient, 'l1_count', 0) or 0
            l3_count = getattr(patient, 'l3_count', 0) or 0
        
        total += l1_count + l3_count
    
    return total


@register.filter  
def total_l1_documents(patients):
    """Calculate total L1 document count for a list of patients"""
    if not patients:
        return 0
    
    total = 0
    for patient in patients:
        if hasattr(patient, 'get'):
            l1_count = patient.get('l1_count', 0) or 0
        else:
            l1_count = getattr(patient, 'l1_count', 0) or 0
        total += l1_count
    
    return total


@register.filter
def total_l3_documents(patients):
    """Calculate total L3 document count for a list of patients"""
    if not patients:
        return 0
    
    total = 0
    for patient in patients:
        if hasattr(patient, 'get'):
            l3_count = patient.get('l3_count', 0) or 0
        else:
            l3_count = getattr(patient, 'l3_count', 0) or 0
        total += l3_count
    
    return total
