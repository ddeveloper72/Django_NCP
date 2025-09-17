# UI Labels Utility for Dynamic Template Content
# This module provides UI labels for internationalization and dynamic content

def get_ui_labels(language="en"):
    """
    Returns UI labels structure for internationalization and dynamic content
    
    Args:
        language (str): Language code for labels (default: "en")
        
    Returns:
        dict: Nested dictionary containing sections, fields, and labels
    """
    
    # English labels (default)
    if language == "en":
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
                "effective_period": "Effective Period",
                "next_of_kin_since": "Next of Kin Since",
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
    
    # Add more languages here as needed
    elif language == "fr":
        return {
            "sections": {
                "contact_information": "Informations de Contact",
                "patient_languages": "Langues du Patient", 
                "guardian": "Tuteur / Proche Parent",
                "other_contacts": "Autres Contacts",
                "emergency_contacts": "Contacts d'Urgence"
            },
            "fields": {
                "address": "Adresse",
                "contact_name": "Nom du Contact",
                "guardian_name": "Nom du Tuteur", 
                "communication_languages": "Langues de Communication",
                "relationship": "Relation",
                "contact_type": "Type de Contact",
                "specialty": "Spécialité",
                "effective_period": "Période d'Efficacité",
                "next_of_kin_since": "Proche Parent Depuis",
                "phone": "Téléphone",
                "email": "Courriel",
                "mobile": "Mobile",
                "work": "Travail",
                "home": "Domicile"
            },
            "labels": {
                "primary": "Principal",
                "secondary": "Secondaire",
                "emergency": "Urgence",
                "work": "Travail",
                "home": "Domicile",
                "mobile": "Mobile"
            }
        }
    
    # Default to English if language not supported
    else:
        return get_ui_labels("en")

# Usage Example:
# In your view function (e.g., enhanced_cda_display), add:
#
# from .ui_labels_example import get_ui_labels
#
# context = {
#     'patient_data': patient_data,
#     'administrative_data': administrative_data,
#     'contact_data': contact_data,
#     'ui_labels': get_ui_labels(target_language),  # Add this line
#     # ... other context variables
# }

# Benefits:
# 1. Easy internationalization - just change the language parameter
# 2. Consistent UI text across all templates  
# 3. Central location for all UI strings
# 4. Easy to maintain and update
# 5. Template defaults ensure graceful fallback if labels missing