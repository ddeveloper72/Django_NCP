"""
Contact Card Template Filters
Standardized contact card rendering for all administrative contacts
"""

from django import template
from typing import Dict, Any, List, Optional

register = template.Library()


@register.inclusion_tag("patient_data/contact_card.html")
def contact_card(
    contact_data: Dict[str, Any],
    card_title: str = "Contact",
    card_type: str = "default",
):
    """
    Render a standardized contact card for any type of contact

    Args:
        contact_data: Contact information dictionary
        card_title: Title to display on the card
        card_type: Type of card for styling (patient, legal_auth, custodian, author)
    """

    # Normalize contact data to standard format
    normalized = normalize_contact_data(contact_data)

    return {
        "contact": normalized,
        "card_title": card_title,
        "card_type": card_type,
        "has_name": bool(normalized.get("full_name")),
        "has_organization": bool(normalized.get("organization", {}).get("name")),
        "has_address": bool(normalized.get("address", {}).get("full_address")),
        "has_contact_info": bool(normalized.get("telecoms")),
        "has_role": bool(normalized.get("role")),
        "has_id": bool(normalized.get("id")),
        "has_time": bool(normalized.get("time")),
    }


@register.inclusion_tag("patient_data/contact_card_list.html")
def contact_card_list(
    contacts: List[Dict[str, Any]],
    list_title: str = "Contacts",
    card_type: str = "default",
):
    """
    Render a list of contact cards

    Args:
        contacts: List of contact dictionaries
        list_title: Title for the contact list
        card_type: Type of cards for styling
    """

    normalized_contacts = [normalize_contact_data(contact) for contact in contacts]

    return {
        "contacts": normalized_contacts,
        "list_title": list_title,
        "card_type": card_type,
        "contact_count": len(normalized_contacts),
    }


def normalize_contact_data(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize contact data to a standard format for template rendering
    """
    if not contact_data:
        return {}

    # Handle both direct access and nested person structures
    normalized = {
        # Name information (try direct access first, then nested)
        "full_name": contact_data.get("full_name")
        or contact_data.get("person", {}).get("full_name"),
        "given_name": contact_data.get("given_name")
        or contact_data.get("person", {}).get("given_name"),
        "family_name": contact_data.get("family_name")
        or contact_data.get("person", {}).get("family_name"),
        # Role/title information
        "role": contact_data.get("role") or contact_data.get("title"),
        "signature_code": contact_data.get("signature_code"),
        # Time information
        "time": contact_data.get("time"),
        # ID information
        "id": normalize_id_data(contact_data.get("id")),
        # Organization information
        "organization": normalize_organization_data(
            contact_data.get("organization", {})
        ),
        # Address information (can be at contact level or organization level)
        "address": normalize_address_data(
            contact_data.get("address")
            or contact_data.get("organization", {}).get("address", {})
        ),
        # Telecom information (can be at contact level or organization level)
        "telecoms": normalize_telecoms_data(
            contact_data.get("telecoms", [])
            or contact_data.get("organization", {}).get("telecoms", [])
        ),
        # Code information
        "code": contact_data.get("code"),
    }

    # Clean up None values
    return {k: v for k, v in normalized.items() if v is not None}


def normalize_id_data(id_data: Any) -> Optional[Dict[str, Any]]:
    """Normalize ID data"""
    if not id_data:
        return None

    if isinstance(id_data, dict):
        return {
            "extension": id_data.get("extension"),
            "root": id_data.get("root"),
            "assigning_authority_name": id_data.get("assigning_authority_name"),
            "display": format_id_display(id_data),
        }

    return {"display": str(id_data)}


def normalize_organization_data(org_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize organization data"""
    if not org_data:
        return {}

    return {
        "name": org_data.get("name"),
        "id": normalize_id_data(org_data.get("id")),
        "address": normalize_address_data(org_data.get("address", {})),
        "telecoms": normalize_telecoms_data(org_data.get("telecoms", [])),
    }


def normalize_address_data(addr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize address data"""
    if not addr_data:
        return {}

    return {
        "full_address": addr_data.get("full_address"),
        "street_address_line": addr_data.get("street_address_line"),
        "city": addr_data.get("city"),
        "state": addr_data.get("state"),
        "postal_code": addr_data.get("postal_code"),
        "country": addr_data.get("country"),
        "use": addr_data.get("use"),
    }


def normalize_telecoms_data(
    telecoms_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Normalize telecoms data"""
    if not telecoms_data:
        return []

    normalized = []
    for telecom in telecoms_data:
        if telecom:
            normalized.append(
                {
                    "type": telecom.get("type", "unknown"),
                    "value": telecom.get("value", ""),
                    "display_value": telecom.get(
                        "display_value", telecom.get("value", "")
                    ),
                    "use": telecom.get("use", "unknown"),
                    "icon": get_telecom_icon(telecom.get("type", "unknown")),
                }
            )

    return normalized


def format_id_display(id_data: Dict[str, Any]) -> str:
    """Format ID for display"""
    parts = []

    if id_data.get("extension"):
        parts.append(f"ID: {id_data['extension']}")

    if id_data.get("assigning_authority_name"):
        parts.append(f"Authority: {id_data['assigning_authority_name']}")

    if id_data.get("root"):
        parts.append(f"Root: {id_data['root']}")

    return " | ".join(parts) if parts else "Unknown ID"


def get_telecom_icon(telecom_type: str) -> str:
    """Get icon class for telecom type"""
    icons = {
        "phone": "fas fa-phone",
        "email": "fas fa-envelope",
        "fax": "fas fa-fax",
        "website": "fas fa-globe",
        "unknown": "fas fa-question",
    }
    return icons.get(telecom_type, icons["unknown"])


# Template filters for individual field access
@register.filter
def get_contact_name(contact_data: Dict[str, Any]) -> str:
    """Get contact name with fallback"""
    normalized = normalize_contact_data(contact_data)
    return normalized.get("full_name") or "Unknown"


@register.filter
def get_contact_role(contact_data: Dict[str, Any]) -> str:
    """Get contact role with fallback"""
    normalized = normalize_contact_data(contact_data)
    return normalized.get("role") or "Unknown Role"


@register.filter
def get_organization_name(contact_data: Dict[str, Any]) -> str:
    """Get organization name with fallback"""
    normalized = normalize_contact_data(contact_data)
    return normalized.get("organization", {}).get("name") or "Unknown Organization"


@register.filter
def get_primary_phone(contact_data: Dict[str, Any]) -> str:
    """Get primary phone number"""
    normalized = normalize_contact_data(contact_data)
    telecoms = normalized.get("telecoms", [])

    for telecom in telecoms:
        if telecom.get("type") == "phone":
            return telecom.get("display_value", "")

    return ""


@register.filter
def get_primary_email(contact_data: Dict[str, Any]) -> str:
    """Get primary email address"""
    normalized = normalize_contact_data(contact_data)
    telecoms = normalized.get("telecoms", [])

    for telecom in telecoms:
        if telecom.get("type") == "email":
            return telecom.get("display_value", "")

    return ""
