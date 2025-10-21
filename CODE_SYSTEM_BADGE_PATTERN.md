# Code System Badge Template Pattern

## Current Implementation
The medication_section.html template now uses the pattern:

```html
<span class="badge bg-secondary text-white small">ATC:</span> {{ code_value }}
```

## Extending for Other Code Systems

### 1. For ICD10 Diagnosis Codes:
```html
{% if item.diagnosis_code_system == "ICD10" %}
    <span class="badge bg-secondary text-white small">ICD10:</span> {{ item.diagnosis_code }}
{% elif item.diagnosis_code_system == "SNOMED" %}
    <span class="badge bg-secondary text-white small">SNOMED:</span> {{ item.diagnosis_code }}
{% endif %}
```

### 2. For Problem List Codes:
```html
{% if item.problem.code_system == "SNOMED-CT" %}
    <span class="badge bg-secondary text-white small">SNOMED:</span> {{ item.problem.code }}
{% elif item.problem.code_system == "ICD10" %}
    <span class="badge bg-secondary text-white small">ICD10:</span> {{ item.problem.code }}
{% endif %}
```

### 3. For Laboratory Results (LOINC):
```html
{% if item.lab_code_system == "LOINC" %}
    <span class="badge bg-secondary text-white small">LOINC:</span> {{ item.lab_code }}
{% endif %}
```

### 4. For Procedure Codes:
```html
{% if item.procedure.code_system == "CPT" %}
    <span class="badge bg-secondary text-white small">CPT:</span> {{ item.procedure.code }}
{% elif item.procedure.code_system == "SNOMED-CT" %}
    <span class="badge bg-secondary text-white small">SNOMED:</span> {{ item.procedure.code }}
{% endif %}
```

## Dynamic Code System Detection

For fully dynamic detection, you could create a template filter:

```python
# In templatetags/code_filters.py
@register.filter
def get_code_system_name(code_system_uri):
    """Convert code system URI to display name"""
    mapping = {
        'http://www.whocc.no/atc': 'ATC',
        'http://hl7.org/fhir/sid/icd-10': 'ICD10',
        'http://snomed.info/sct': 'SNOMED',
        'http://loinc.org': 'LOINC',
        'http://www.ama-assn.org/go/cpt': 'CPT'
    }
    return mapping.get(code_system_uri, 'CODE')
```

Then in template:
```html
<span class="badge bg-secondary text-white small">{{ item.code_system|get_code_system_name }}:</span> {{ item.code }}
```

## Current Status

✅ **ATC codes**: Implemented with "ATC:" badge labels
🔄 **Next**: Extend to other clinical sections (problems, procedures, lab results)
📋 **Future**: Implement dynamic code system detection based on data structure
