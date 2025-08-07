
def prepare_enhanced_section_data(sections, value_set_service=None):
    """
    Pre-process sections for template display
    Handles all value set lookups and field processing in Python
    
    Args:
        sections: Raw sections from enhanced CDA processor
        value_set_service: Optional value set service for terminology lookup
    
    Returns:
        dict: Processed sections ready for simple template display
    """
    processed_sections = []
    
    for section in sections:
        processed_section = {
            'title': section.get('title', 'Unknown Section'),
            'type': section.get('type', 'unknown'),
            'entries': [],
            'has_entries': False,
            'medical_terminology_count': 0,
            'coded_entries_count': 0
        }
        
        # Process entries with proper value set integration
        entries = section.get('entries', [])
        for entry in entries:
            processed_entry = process_entry_for_display(entry, value_set_service)
            processed_section['entries'].append(processed_entry)
            
            # Update metrics
            if processed_entry.get('has_medical_terminology'):
                processed_section['medical_terminology_count'] += 1
            if processed_entry.get('is_coded'):
                processed_section['coded_entries_count'] += 1
        
        processed_section['has_entries'] = len(processed_section['entries']) > 0
        processed_sections.append(processed_section)
    
    return processed_sections

def process_entry_for_display(entry, value_set_service=None):
    """
    Process a single entry for template display
    Handles all field lookups and terminology resolution in Python
    
    Args:
        entry: Raw entry from CDA processor
        value_set_service: Optional value set service
    
    Returns:
        dict: Processed entry with resolved terminology and display fields
    """
    processed_entry = {
        'original_entry': entry,
        'display_fields': {},
        'medical_terminology': {},
        'has_medical_terminology': False,
        'is_coded': False,
        'value_set_matches': [],
        'display_name': 'Unknown Item',
        'code': None,
        'code_system': None
    }
    
    fields = entry.get('fields', {})
    
    # Handle different field lookup patterns based on section type
    section_type = entry.get('section_type', 'unknown')
    
    if section_type in ['allergies', 'allergies_intolerance']:
        processed_entry.update(process_allergy_entry(fields, value_set_service))
    elif section_type in ['medication', 'medications']:
        processed_entry.update(process_medication_entry(fields, value_set_service))
    elif section_type in ['problems', 'active_problems']:
        processed_entry.update(process_problem_entry(fields, value_set_service))
    elif section_type in ['procedures', 'history_procedures']:
        processed_entry.update(process_procedure_entry(fields, value_set_service))
    else:
        processed_entry.update(process_generic_entry(fields, value_set_service))
    
    return processed_entry

def process_allergy_entry(fields, value_set_service=None):
    """Process allergy-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Allergen',
        'reaction': 'Unknown Reaction',
        'severity': 'Unknown Severity',
        'has_medical_terminology': False
    }
    
    # Try multiple field name patterns for allergen
    allergen_patterns = [
        'Allergen DisplayName',
        'Allergen Code',
        'Allergène',
        'Substance',
        'Agent'
    ]
    
    for pattern in allergen_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                # Check if this field has value set information
                if field_data.get('has_valueset') and value_set_service:
                    # Use value set service to get proper medical terminology
                    code = field_data.get('code')
                    code_system = field_data.get('code_system')
                    if code and code_system:
                        terminology = value_set_service.lookup_term(code, code_system)
                        if terminology:
                            result['display_name'] = terminology.get('display_name', result['display_name'])
                            result['has_medical_terminology'] = True
                            break
                else:
                    # Use display name from field data
                    display_name = field_data.get('display_name') or field_data.get('value')
                    if display_name and display_name != 'Unknown':
                        result['display_name'] = display_name
                        break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    # Process reaction information
    reaction_patterns = ['Reaction', 'Adverse Event', 'Manifestation']
    for pattern in reaction_patterns:
        if pattern in fields:
            reaction_data = fields[pattern]
            if isinstance(reaction_data, dict):
                reaction_name = reaction_data.get('display_name') or reaction_data.get('value')
                if reaction_name and reaction_name != 'Unknown':
                    result['reaction'] = reaction_name
                    break
            elif isinstance(reaction_data, str) and reaction_data != 'Unknown':
                result['reaction'] = reaction_data
                break
    
    return result

def process_medication_entry(fields, value_set_service=None):
    """Process medication-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Medication',
        'dosage': 'Unknown Dosage',
        'frequency': 'Unknown Frequency',
        'has_medical_terminology': False
    }
    
    # Try multiple field name patterns for medication
    medication_patterns = [
        'Medication DisplayName',
        'Medication Code',
        'Drug Name',
        'Active Ingredient',
        'Substance'
    ]
    
    for pattern in medication_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset') and value_set_service:
                    code = field_data.get('code')
                    code_system = field_data.get('code_system')
                    if code and code_system:
                        terminology = value_set_service.lookup_term(code, code_system)
                        if terminology:
                            result['display_name'] = terminology.get('display_name', result['display_name'])
                            result['has_medical_terminology'] = True
                            break
                else:
                    display_name = field_data.get('display_name') or field_data.get('value')
                    if display_name and display_name != 'Unknown':
                        result['display_name'] = display_name
                        break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    return result

def process_problem_entry(fields, value_set_service=None):
    """Process problem/condition-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Condition',
        'status': 'Unknown Status',
        'onset': 'Unknown Onset',
        'has_medical_terminology': False
    }
    
    # Try multiple field name patterns for problems/conditions
    problem_patterns = [
        'Problem DisplayName',
        'Problem Code',
        'Condition',
        'Diagnosis',
        'Clinical Finding'
    ]
    
    for pattern in problem_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset') and value_set_service:
                    code = field_data.get('code')
                    code_system = field_data.get('code_system')
                    if code and code_system:
                        terminology = value_set_service.lookup_term(code, code_system)
                        if terminology:
                            result['display_name'] = terminology.get('display_name', result['display_name'])
                            result['has_medical_terminology'] = True
                            break
                else:
                    display_name = field_data.get('display_name') or field_data.get('value')
                    if display_name and display_name != 'Unknown':
                        result['display_name'] = display_name
                        break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    return result

def process_procedure_entry(fields, value_set_service=None):
    """Process procedure-specific fields with proper terminology lookup"""
    result = {
        'display_name': 'Unknown Procedure',
        'date': 'Unknown Date',
        'status': 'Unknown Status',
        'has_medical_terminology': False
    }
    
    # Try multiple field name patterns for procedures
    procedure_patterns = [
        'Procedure DisplayName',
        'Procedure Code',
        'Intervention',
        'Treatment',
        'Surgery'
    ]
    
    for pattern in procedure_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                if field_data.get('has_valueset') and value_set_service:
                    code = field_data.get('code')
                    code_system = field_data.get('code_system')
                    if code and code_system:
                        terminology = value_set_service.lookup_term(code, code_system)
                        if terminology:
                            result['display_name'] = terminology.get('display_name', result['display_name'])
                            result['has_medical_terminology'] = True
                            break
                else:
                    display_name = field_data.get('display_name') or field_data.get('value')
                    if display_name and display_name != 'Unknown':
                        result['display_name'] = display_name
                        break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    return result

def process_generic_entry(fields, value_set_service=None):
    """Process generic entry fields with basic terminology lookup"""
    result = {
        'display_name': 'Unknown Item',
        'has_medical_terminology': False
    }
    
    # Try common field patterns
    common_patterns = [
        'DisplayName',
        'Name',
        'Title',
        'Description',
        'Value'
    ]
    
    for pattern in common_patterns:
        if pattern in fields:
            field_data = fields[pattern]
            if isinstance(field_data, dict):
                display_name = field_data.get('display_name') or field_data.get('value')
                if display_name and display_name != 'Unknown':
                    result['display_name'] = display_name
                    break
            elif isinstance(field_data, str) and field_data != 'Unknown':
                result['display_name'] = field_data
                break
    
    return result
