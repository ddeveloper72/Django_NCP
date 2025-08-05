"""
Administrative Data Template Filters
Template filters for displaying contact information and organizational data
"""

from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter
def format_address(address_dict):
    """Format address dictionary for display"""
    if not address_dict or not isinstance(address_dict, dict):
        return "No address available"

    return address_dict.get("full_address", "No address available")


@register.filter
def format_telecom(telecom_dict):
    """Format telecom dictionary for display"""
    if not telecom_dict or not isinstance(telecom_dict, dict):
        return "No contact available"

    display_value = telecom_dict.get("display_value", "")
    telecom_type = telecom_dict.get("type", "contact")
    use = telecom_dict.get("use", "")

    # Format based on type
    if telecom_type == "phone":
        icon = "📞"
    elif telecom_type == "email":
        icon = "📧"
    elif telecom_type == "fax":
        icon = "📠"
    elif telecom_type == "website":
        icon = "🌐"
    else:
        icon = "📋"

    formatted = f"{icon} {display_value}"
    if use and use != "unknown":
        formatted += f" ({use})"

    return formatted


@register.filter
def format_telecom_list(telecoms_list):
    """Format list of telecoms for display"""
    if not telecoms_list or not isinstance(telecoms_list, list):
        return "No contacts available"

    formatted_telecoms = []
    for telecom in telecoms_list:
        formatted = format_telecom(telecom)
        if formatted != "No contact available":
            formatted_telecoms.append(formatted)

    return (
        " | ".join(formatted_telecoms)
        if formatted_telecoms
        else "No contacts available"
    )


@register.filter
def get_primary_contact(patient_contact_info, contact_type):
    """Get primary contact of specified type (address, phone, email)"""
    if not patient_contact_info or not isinstance(patient_contact_info, dict):
        return None

    primary_key = f"primary_{contact_type}"
    return patient_contact_info.get(primary_key)


@register.filter
def format_organization_name(org_dict):
    """Format organization name with ID if available"""
    if not org_dict or not isinstance(org_dict, dict):
        return "Unknown Organization"

    name = org_dict.get("name", "Unknown Organization")
    org_id = org_dict.get("id")

    if org_id and isinstance(org_id, dict):
        extension = org_id.get("extension")
        if extension:
            return f"{name} (ID: {extension})"

    return name


@register.filter
def format_author_summary(author_dict):
    """Format author information for display"""
    if not author_dict or not isinstance(author_dict, dict):
        return "Unknown Author"

    person = author_dict.get("person", {})
    organization = author_dict.get("organization", {})
    role = author_dict.get("role", "Healthcare Professional")

    name = person.get("full_name", "Unknown")
    org_name = organization.get("name", "")

    if org_name:
        return f"{name} ({role}) - {org_name}"
    else:
        return f"{name} ({role})"


@register.filter
def has_contact_info(patient_contact_info):
    """Check if patient has any contact information"""
    if not patient_contact_info or not isinstance(patient_contact_info, dict):
        return False

    addresses = patient_contact_info.get("addresses", [])
    telecoms = patient_contact_info.get("telecoms", [])

    return len(addresses) > 0 or len(telecoms) > 0


@register.filter
def contact_summary_badge(patient_contact_info):
    """Create a summary badge for patient contact info"""
    if not patient_contact_info or not isinstance(patient_contact_info, dict):
        return mark_safe('<span class="badge badge-secondary">No Contact Info</span>')

    addresses = patient_contact_info.get("addresses", [])
    telecoms = patient_contact_info.get("telecoms", [])

    total_contacts = len(addresses) + len(telecoms)

    if total_contacts == 0:
        return mark_safe('<span class="badge badge-secondary">No Contact Info</span>')
    elif total_contacts <= 2:
        return mark_safe(
            f'<span class="badge badge-warning">{total_contacts} Contacts</span>'
        )
    else:
        return mark_safe(
            f'<span class="badge badge-success">{total_contacts} Contacts</span>'
        )


@register.filter
def organization_address_summary(org_dict):
    """Get organization address summary"""
    if not org_dict or not isinstance(org_dict, dict):
        return "No address"

    address = org_dict.get("address", {})
    if not address:
        return "No address"

    # Prioritize country and state for international context
    country = address.get("country", "")
    state = address.get("state", "")

    if country and state:
        return f"{state}, {country}"
    elif country:
        return country
    elif state:
        return state
    else:
        return address.get("full_address", "No address")


@register.simple_tag
def render_contact_card(contact_info, title="Contact Information"):
    """Render a complete contact information card"""
    if not contact_info or not isinstance(contact_info, dict):
        return f"""
        <div class="contact-card">
            <h6>{title}</h6>
            <p class="text-muted">No contact information available</p>
        </div>
        """

    addresses = contact_info.get("addresses", [])
    telecoms = contact_info.get("telecoms", [])

    html_parts = [f'<div class="contact-card"><h6>{title}</h6>']

    # Render addresses
    if addresses:
        html_parts.append('<div class="contact-section"><strong>Addresses:</strong>')
        for addr in addresses:
            use = addr.get("use", "unknown")
            full_address = addr.get("full_address", "No address")
            html_parts.append(
                f'<div class="contact-item">📍 {full_address} ({use})</div>'
            )
        html_parts.append("</div>")

    # Render telecoms
    if telecoms:
        html_parts.append(
            '<div class="contact-section"><strong>Contact Methods:</strong>'
        )
        for tel in telecoms:
            formatted_tel = format_telecom(tel)
            html_parts.append(f'<div class="contact-item">{formatted_tel}</div>')
        html_parts.append("</div>")

    if not addresses and not telecoms:
        html_parts.append('<p class="text-muted">No contact information available</p>')

    html_parts.append("</div>")

    return mark_safe("".join(html_parts))


@register.filter
def telecom_by_type(telecoms_list, telecom_type):
    """Filter telecoms by type (phone, email, fax, website)"""
    if not telecoms_list or not isinstance(telecoms_list, list):
        return []

    return [tel for tel in telecoms_list if tel.get("type") == telecom_type]


@register.filter
def first_telecom_by_type(telecoms_list, telecom_type):
    """Get first telecom of specified type"""
    filtered = telecom_by_type(telecoms_list, telecom_type)
    return filtered[0] if filtered else None
