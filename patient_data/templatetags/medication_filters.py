"""
Enhanced Medication Template Filters
Smart extraction and display of medication dose form and dose quantity data
"""

import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def extract_strength(medication_name):
    """Extract strength information from medication name"""
    if not medication_name:
        return ""
    
    # Patterns to match strength information
    strength_patterns = [
        r"(\d+\.?\d*)\s*(mg|mcg|µg|g|IU|units?|ml|mL)(?:/\s*(ml|mL|unit))?",
        r"(\d+\.?\d*)\s*\[?(IU|units?)\]?",
        r"(\d+\.?\d*)\s*(microgram|milligram|gram)",
    ]
    
    for pattern in strength_patterns:
        match = re.search(pattern, medication_name, re.IGNORECASE)
        if match:
            value = match.group(1)
            unit = match.group(2)
            per_unit = match.group(3) if len(match.groups()) > 2 and match.group(3) else ""
            
            if per_unit:
                return f"{value} {unit}/{per_unit}"
            else:
                return f"{value} {unit}"
    
    return ""


@register.filter
def extract_brand_name(medication_name):
    """Extract brand name from medication name"""
    if not medication_name:
        return ""
    
    # For simple medication names, return the name as the brand
    medication_name = medication_name.strip()
    
    # Known brand medications - return as-is since they're already brand names
    known_brands = {
        'eutirox': 'Eutirox',
        'triapin': 'Triapin',
        'tresiba': 'Tresiba',
        'augmentin': 'Augmentin',
        'combivent': 'Combivent',
        'lantus': 'Lantus',
        'novolog': 'NovoLog',
        'humalog': 'Humalog'
    }
    
    name_lower = medication_name.lower()
    for brand_key, brand_name in known_brands.items():
        if brand_key in name_lower:
            return brand_name
    
    # Pattern to extract brand name before colon or first word if all caps
    brand_patterns = [
        r"^([A-Z][a-zA-Z]+)\s*:",  # "Eutirox :"
        r"^([A-Z][A-Z]+)(?:\s|$)",  # "VIREAD"
        r"^([A-Z][a-zA-Z]+)(?=\s+[a-z])",  # "Lantus insulin"
    ]
    
    for pattern in brand_patterns:
        match = re.search(pattern, medication_name.strip())
        if match:
            return match.group(1)
    
    return ""


@register.filter
def extract_active_ingredient(medication_name):
    """Extract active ingredient from known medication names"""
    if not medication_name:
        return ""
    
    # Known medication active ingredients
    active_ingredients = {
        'eutirox': 'Levothyroxine sodium',
        'triapin': 'Ramipril + Felodipine', 
        'tresiba': 'Insulin degludec',
        'augmentin': 'Amoxicillin + Clavulanic acid',
        'combivent': 'Ipratropium bromide + Salbutamol',
        'lantus': 'Insulin glargine',
        'novolog': 'Insulin aspart',
        'humalog': 'Insulin lispro'
    }
    
    name_lower = medication_name.lower().strip()
    
    # Check for exact matches
    for med_name, ingredient in active_ingredients.items():
        if med_name in name_lower:
            return ingredient
    
    # If no match found, return empty string
    return ""


@register.filter
def extract_active_ingredient(medication_name):
    """Extract active ingredient from medication name"""
    if not medication_name:
        return ""
    
    # If there's a colon, everything after it is usually the active ingredient
    if ":" in medication_name:
        parts = medication_name.split(":", 1)
        if len(parts) > 1:
            ingredient = parts[1].strip()
            # Remove strength information from ingredient
            ingredient = re.sub(r"\d+\.?\d*\s*(mg|mcg|µg|g|IU|units?|ml|mL).*$", "", ingredient, flags=re.IGNORECASE)
            return ingredient.strip()
    
    return ""


@register.filter
def smart_dose_form(medication, route=None):
    """Intelligently determine dose form from medication data"""
    if not medication:
        return "Form not specified"
    
    medication_name = getattr(medication, 'name', '') or ''
    route_name = ""
    
    if route and hasattr(route, 'displayName'):
        route_name = route.displayName or ''
    
    # Check medication name for dose form clues
    name_lower = medication_name.lower()
    
    # Map known medication names to likely dose forms
    medication_dose_forms = {
        'eutirox': 'Tablet',
        'triapin': 'Tablet', 
        'tresiba': 'Pre-filled pen',
        'augmentin': 'Tablet',
        'combivent': 'Nebuliser solution',
        'insulin': 'Solution for injection',
        'lantus': 'Pre-filled pen',
        'novolog': 'Pre-filled pen',
        'humalog': 'Pre-filled pen',
    }
    
    # Check for exact matches first
    for med_name, dose_form in medication_dose_forms.items():
        if med_name in name_lower:
            return dose_form
    
    # Check medication name for dose form clues
    if any(word in name_lower for word in ['pen', 'injection', 'injectable']):
        if 'pen' in name_lower or 'pre-filled' in name_lower:
            return "Pre-filled pen"
        else:
            return "Solution for injection"
    
    # Tablet forms
    if any(word in name_lower for word in ['tablet', 'tab']):
        if 'film-coated' in name_lower or 'coated' in name_lower:
            return "Film-coated tablet"
        elif 'prolonged-release' in name_lower or 'extended-release' in name_lower:
            return "Prolonged-release tablet"
        elif 'modified-release' in name_lower:
            return "Modified-release tablet"
        else:
            return "Tablet"
    
    # Capsule forms
    if 'capsule' in name_lower:
        return "Capsule"
    
    # Solution forms
    if any(word in name_lower for word in ['solution', 'liquid', 'syrup']):
        if 'nebuliser' in name_lower or 'nebulizer' in name_lower:
            return "Nebuliser solution"
        else:
            return "Oral solution"
    
    # Check route for additional clues
    if route_name:
        route_lower = route_name.lower()
        if 'subcutaneous' in route_lower or 'injection' in route_lower:
            return "Solution for injection"
        elif 'oral' in route_lower:
            return "Tablet"  # Default for oral use
        elif 'inhalation' in route_lower:
            return "Inhalation solution"
    
    return "Form not specified"


@register.filter
def smart_dose_quantity(dose, medication=""):
    """Display dose quantity contextually based on dose data and medication"""
    if not dose:
        return "Quantity not specified"
    
    # Get dose value and unit
    dose_value = getattr(dose, 'value', '') or ''
    dose_unit = getattr(dose, 'unit', '') or ''
    
    if not dose_value:
        return "Quantity not specified"
    
    # Get medication name for context
    medication_name = ""
    if hasattr(medication, 'name'):
        medication_name = medication.name.lower()
    elif isinstance(medication, str):
        medication_name = medication.lower()
    
    # Handle known medication-specific dose contexts
    if 'tresiba' in medication_name or 'insulin' in medication_name:
        # Insulin doses are typically in IU/units
        if dose_unit == '1':  # Unit code for IU
            return f"{dose_value} IU"
        else:
            return f"{dose_value} units"
    
    if 'eutirox' in medication_name:
        # Thyroid medications typically in micrograms
        return f"{dose_value} tablet(s)"
    
    if 'triapin' in medication_name:
        # Blood pressure medication - typically tablets
        return f"{dose_value} tablet(s)"
    
    if 'augmentin' in medication_name:
        # Antibiotic - typically tablets or suspension
        return f"{dose_value} tablet(s)"
    
    if 'combivent' in medication_name:
        # Respiratory medication - nebulizer solution
        if dose_unit == '1':
            return f"{dose_value} vial(s)"
        else:
            return f"{dose_value} {dose_unit}"
    
    # Default formatting based on unit
    if dose_unit:
        # Clean up common unit variations
        unit_clean = dose_unit.replace('[', '').replace(']', '')
        
        # Map unit codes to readable units
        unit_mapping = {
            '1': 'unit(s)',
            'tablet': 'tablet(s)',
            'capsule': 'capsule(s)',
            'ml': 'mL',
            'mg': 'mg',
            'mcg': 'mcg',
            'iu': 'IU'
        }
        
        readable_unit = unit_mapping.get(unit_clean.lower(), unit_clean)
        return f"{dose_value} {readable_unit}"
    
    # Fallback
    return f"{dose_value} unit(s)"


@register.filter
def medication_strength_display(medication_name):
    """Display strength information in a user-friendly format"""
    strength = extract_strength(medication_name)
    if not strength:
        return mark_safe('<em class="text-muted">Strength not specified</em>')
    
    # Add appropriate badges/styling
    if any(unit in strength for unit in ['IU', 'units']):
        return mark_safe(f'<span class="strength-badge insulin-strength">{strength}</span>')
    elif 'mg' in strength:
        return mark_safe(f'<span class="strength-badge standard-strength">{strength}</span>')
    else:
        return mark_safe(f'<span class="strength-badge">{strength}</span>')


@register.filter
def format_medication_name(medication_name):
    """Format medication name to separate brand and generic components"""
    if not medication_name:
        return ""
    
    brand = extract_brand_name(medication_name)
    ingredient = extract_active_ingredient(medication_name)
    
    if brand and ingredient:
        return mark_safe(f'<strong class="brand-name">{brand}</strong> <span class="generic-name">({ingredient})</span>')
    elif brand:
        return mark_safe(f'<strong class="brand-name">{brand}</strong>')
    else:
        return medication_name


@register.filter
def dosage_schedule_smart(medication):
    """Smart dosage schedule extraction from medication data"""
    if not medication:
        return "Schedule not specified"
    
    medication_name = getattr(medication, 'name', '') or ''
    
    # Extract schedule patterns from medication name
    schedule_patterns = [
        (r"(\d+)\s*per\s*day", lambda m: f"{m.group(1)} per day"),
        (r"every\s*(\d+)\s*(hour|hours|h)", lambda m: f"Every {m.group(1)} {m.group(2)}"),
        (r"(\d+)\s*times?\s*daily", lambda m: f"{m.group(1)} times daily"),
        (r"once\s*daily", lambda m: "Once daily"),
        (r"twice\s*daily", lambda m: "Twice daily"),
    ]
    
    name_lower = medication_name.lower()
    for pattern, formatter in schedule_patterns:
        match = re.search(pattern, name_lower)
        if match:
            return formatter(match)
    
    # Check for effective time information
    if hasattr(medication, 'effective_time') and medication.effective_time:
        if hasattr(medication.effective_time, 'low_formatted') and medication.effective_time.low_formatted:
            return "As prescribed by healthcare provider"
    
    return "As prescribed"


@register.filter
def route_display_name(route):
    """Enhanced route display with user-friendly formatting"""
    if not route or not hasattr(route, 'displayName'):
        return "Route not specified"
    
    route_name = route.displayName or ""
    
    # Clean up common route names
    route_mapping = {
        "oral use": "Oral",
        "subcutaneous use": "Subcutaneous injection",
        "intravenous use": "Intravenous",
        "intramuscular use": "Intramuscular injection",
        "topical use": "Topical application",
        "inhalation use": "Inhalation",
    }
    
    route_lower = route_name.lower()
    for original, friendly in route_mapping.items():
        if original in route_lower:
            return friendly
    
    return route_name


@register.filter
def medical_reason_extract(medication):
    """Extract medical reason/indication from medication data"""
    if not medication:
        return "Indication not specified"
    
    # This would need to be enhanced based on actual CDA structure
    # For now, return a placeholder
    return "As prescribed by healthcare provider"