#!/usr/bin/env python3
"""
Template Logic Refactor Script
Moves complex data processing from template back to Python view
Following proper MVC separation of concerns
"""

import os
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_template_processing_logic():
    """
    Analyzes the bloated template to extract processing logic patterns
    that should be moved to Python view
    """

    template_path = Path("templates/patient_data/enhanced_patient_cda.html")

    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        return None

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Extract complex logic patterns that belong in Python
    patterns = {
        "value_set_checks": [],
        "field_lookups": [],
        "conditional_processing": [],
        "medical_term_logic": [],
        "section_specific_logic": [],
    }

    # Find complex field lookups like entry.fields.get('Allergen DisplayName', entry.fields.get('Allergen Code', ...
    field_lookup_pattern = r"(\w+\.fields\.get\([^}]+}[^}]*}\))"
    patterns["field_lookups"] = re.findall(field_lookup_pattern, template_content)

    # Find value set conditional logic
    valueset_pattern = r"(has_valueset[^%]+%})"
    patterns["value_set_checks"] = re.findall(valueset_pattern, template_content)

    # Find complex conditional blocks
    conditional_pattern = r"({%\s*if[^%]+%}[^{]*{%\s*endif\s*%})"
    patterns["conditional_processing"] = re.findall(
        conditional_pattern, template_content
    )

    # Find medical terminology specific logic
    medical_term_pattern = r"(medical_terms[^}]+})"
    patterns["medical_term_logic"] = re.findall(medical_term_pattern, template_content)

    return patterns


def create_enhanced_view_processor():
    """
    Creates Python functions to handle data processing that was in template
    """

    processor_code = '''
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
'''

    return processor_code


def create_simplified_template():
    """
    Creates a simplified template that uses pre-processed data from Python
    """

    simplified_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced CDA Display - {{ patient_identity.given_name }} {{ patient_identity.family_name }}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* Clean, focused styles */
        .medical-section {
            border: 1px solid #dee2e6;
            border-radius: 0.375rem;
            margin-bottom: 1.5rem;
        }
        
        .medical-entry {
            padding: 0.75rem;
            border-bottom: 1px solid #f8f9fa;
        }
        
        .medical-entry:last-child {
            border-bottom: none;
        }
        
        .terminology-badge {
            background-color: #e8f5e8;
            color: #2d5a2d;
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
        }
        
        .unknown-item {
            color: #6c757d;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <!-- Patient Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h2 class="mb-0">
                            <i class="fas fa-user-injured me-2"></i>
                            {{ patient_identity.given_name }} {{ patient_identity.family_name }}
                        </h2>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Birth Date:</strong> {{ patient_identity.birth_date or 'Unknown' }}</p>
                                <p><strong>Gender:</strong> {{ patient_identity.gender or 'Unknown' }}</p>
                                <p><strong>Patient ID:</strong> {{ patient_identity.patient_id }}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Source Country:</strong> {{ source_country }}</p>
                                <p><strong>CDA Type:</strong> {{ cda_type }}</p>
                                <p><strong>Translation Quality:</strong> 
                                    <span class="badge bg-success">{{ translation_quality }}</span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Medical Sections -->
        {% if processed_sections %}
            {% for section in processed_sections %}
                <div class="medical-section">
                    <div class="card">
                        <div class="card-header">
                            <h4 class="mb-0">
                                {{ section.title }}
                                {% if section.medical_terminology_count > 0 %}
                                    <span class="terminology-badge ms-2">
                                        {{ section.medical_terminology_count }} medical terms resolved
                                    </span>
                                {% endif %}
                            </h4>
                        </div>
                        
                        {% if section.has_entries %}
                            <div class="card-body p-0">
                                {% for entry in section.entries %}
                                    <div class="medical-entry">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <h6 class="mb-1 {% if entry.display_name == 'Unknown Item' or entry.display_name == 'Unknown Condition' or entry.display_name == 'Unknown Procedure' or entry.display_name == 'Unknown Medication' or entry.display_name == 'Unknown Allergen' %}unknown-item{% endif %}">
                                                    {{ entry.display_name }}
                                                </h6>
                                                {% if entry.get('reaction') %}
                                                    <p class="mb-1"><strong>Reaction:</strong> {{ entry.reaction }}</p>
                                                {% endif %}
                                                {% if entry.get('dosage') %}
                                                    <p class="mb-1"><strong>Dosage:</strong> {{ entry.dosage }}</p>
                                                {% endif %}
                                                {% if entry.get('status') %}
                                                    <p class="mb-1"><strong>Status:</strong> {{ entry.status }}</p>
                                                {% endif %}
                                            </div>
                                            <div class="col-md-4 text-end">
                                                {% if entry.has_medical_terminology %}
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check"></i> Medical Term
                                                    </span>
                                                {% else %}
                                                    <span class="badge bg-secondary">
                                                        <i class="fas fa-question"></i> Basic Text
                                                    </span>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                        {% else %}
                            <div class="card-body">
                                <p class="text-muted mb-0">No entries found in this section.</p>
                            </div>
                        {% endif %}
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <div class="alert alert-warning">
                <h4>No Medical Data Available</h4>
                <p>No clinical sections could be processed from the CDA document.</p>
            </div>
        {% endif %}

        <!-- Summary Stats -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h4>Processing Summary</h4>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-md-3">
                                <div class="h2 text-primary">{{ sections_count }}</div>
                                <div>Total Sections</div>
                            </div>
                            <div class="col-md-3">
                                <div class="h2 text-success">{{ medical_terms_count }}</div>
                                <div>Medical Terms</div>
                            </div>
                            <div class="col-md-3">
                                <div class="h2 text-info">{{ coded_sections_count }}</div>
                                <div>Coded Sections</div>
                            </div>
                            <div class="col-md-3">
                                <div class="h2 text-warning">{{ coded_sections_percentage|round }}%</div>
                                <div>Terminology Coverage</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

    return simplified_template


def main():
    """
    Main refactoring process
    """
    logger.info("Starting template logic refactoring process...")

    # Step 1: Analyze current template complexity
    logger.info("Analyzing current template complexity...")
    patterns = extract_template_processing_logic()

    if patterns:
        logger.info("Found complex processing patterns:")
        for pattern_type, items in patterns.items():
            logger.info(f"  - {pattern_type}: {len(items)} instances")

    # Step 2: Create enhanced view processor functions
    logger.info("Creating enhanced view processor functions...")
    processor_code = create_enhanced_view_processor()

    with open("enhanced_view_processor.py", "w", encoding="utf-8") as f:
        f.write(processor_code)

    logger.info("Created enhanced_view_processor.py with data processing functions")

    # Step 3: Create simplified template
    logger.info("Creating simplified template...")
    simplified_template = create_simplified_template()

    with open("simplified_patient_cda.html", "w", encoding="utf-8") as f:
        f.write(simplified_template)

    logger.info("Created simplified_patient_cda.html template")

    # Step 4: Create integration instructions
    integration_instructions = """
# Template Logic Refactor - Integration Instructions

## Overview
This refactor moves complex data processing from the Jinja2 template back to Python,
following proper MVC separation of concerns.

## Files Created
1. `enhanced_view_processor.py` - Data processing functions for Python view
2. `simplified_patient_cda.html` - Clean template with minimal logic

## Integration Steps

### Step 1: Add processor functions to your view
Copy the functions from `enhanced_view_processor.py` into your `patient_data/views.py` file
or import them as a separate module.

### Step 2: Update your view context preparation
In your `patient_cda_view` function, before rendering the template, add:

```python
# Process sections for template display (move complex logic from template to Python)
if translation_result and translation_result.get('sections'):
    from .services.value_set_service import ValueSetService  # Optional
    value_set_service = ValueSetService()  # Optional for terminology lookup
    
    processed_sections = prepare_enhanced_section_data(
        translation_result.get('sections', []),
        value_set_service=value_set_service
    )
    
    # Add processed data to context
    context['processed_sections'] = processed_sections
else:
    context['processed_sections'] = []
```

### Step 3: Replace template
Replace the bloated `enhanced_patient_cda.html` with `simplified_patient_cda.html`

### Step 4: Test functionality
Verify that:
- Medical terminology still displays correctly
- "Unknown" labels are properly replaced
- Template renders quickly without complex processing
- All value set integration works correctly

## Benefits of This Refactor
- ✅ Proper MVC separation of concerns
- ✅ Complex logic in Python where it belongs
- ✅ Simple, maintainable template
- ✅ Better performance (no template-side processing)
- ✅ Easier testing and debugging
- ✅ Clean repository suitable for GitHub commits

## Architecture
- **Python View**: Handles all data processing, field lookups, value set integration
- **Template**: Only displays pre-processed data with minimal conditionals
- **Result**: Same functionality with proper architectural separation
"""

    with open("REFACTOR_INTEGRATION.md", "w", encoding="utf-8") as f:
        f.write(integration_instructions)

    logger.info("Created REFACTOR_INTEGRATION.md with integration instructions")

    logger.info("✅ Template logic refactoring complete!")
    logger.info("Next steps:")
    logger.info("1. Review the generated files")
    logger.info("2. Follow REFACTOR_INTEGRATION.md to implement the changes")
    logger.info("3. Test the functionality")
    logger.info("4. Remove the bloated template once confirmed working")


if __name__ == "__main__":
    main()
