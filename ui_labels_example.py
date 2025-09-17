# UI Labels Structure for Dynamic Template Content
# Add this to your view context to replace hardcoded strings

def get_ui_labels():
    """
    Returns UI labels structure for internationalization and dynamic content
    """
    return {
        "sections": {
            "contact_information": "Contact Information",
            "patient_languages": "Patient Languages", 
            "guardian": "Guardian / Next of Kin",
            "other_contacts": "Other Contacts",
            "emergency_contacts": "Emergency Contacts"
        },
        "fields": {
            "address": "Address",
            "contact_name": "Contact Name",
            "guardian_name": "Guardian Name", 
            "communication_languages": "Communication Languages",
            "relationship": "Relationship",
            "contact_type": "Contact Type",
            "specialty": "Specialty",
            "phone": "Phone",
            "email": "Email",
            "mobile": "Mobile",
            "work": "Work",
            "home": "Home"
        },
        "labels": {
            "primary": "Primary",
            "secondary": "Secondary",
            "emergency": "Emergency",
            "work": "Work",
            "home": "Home",
            "mobile": "Mobile"
        }
    }

# Example of how to add to view context:
"""
In your view function (e.g., enhanced_patient_cda_view), add:

context = {
    'patient_data': patient_data,
    'administrative_data': administrative_data,
    'contact_data': contact_data,
    'ui_labels': get_ui_labels(),  # Add this line
    # ... other context variables
}
"""

# Benefits:
# 1. Easy internationalization - just change the return values
# 2. Consistent UI text across all templates  
# 3. Central location for all UI strings
# 4. Easy to maintain and update
# 5. Template defaults ensure graceful fallback if labels missing