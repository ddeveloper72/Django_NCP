# CDA Template-View Mapping Documentation

## Overview

This document provides comprehensive mapping between the 4-tool CDA parsing pipeline output and HTML template variables, with proper nullFlavor handling according to HL7 CDA specifications.

## 4-Tool CDA Parsing Architecture

### Tool Pipeline

1. **Enhanced_Cda_Xml_Parser**: Primary CDA document parser
2. **Ps_Table_Renderer**: Clinical table formatting service
3. **Cda_Parser_Service**: Core clinical data extraction service
4. **Structured_Cda_Extractor**: Structured clinical entry processor

### Data Flow

```
CDA XML → Enhanced_Cda_Xml_Parser → Structured_Cda_Extractor → Template Context
       ↘ Ps_Table_Renderer → Clinical Tables → Template Context
       ↘ Cda_Parser_Service → Clinical Sections → Template Context
```

## Template Context Structure

### Primary Context Variables (from views.py)

```python
context = {
    "patient_identity": {
        "given_name": str,
        "family_name": str,
        "birth_date": str,
        "gender": str,
        "patient_id": str,
        "patient_identifiers": [
            {
                "extension": str,
                "root": str,
                "assigningAuthorityName": str,
                "nullFlavor": str  # CDA spec compliance
            }
        ]
    },
    "processed_sections": [
        {
            "section_id": str,  # e.g., "psMedicationSummary"
            "title": str,       # e.g., "Medication Summary"
            "display_name": str,
            "structured_entries": [
                {
                    "entry_type": str,        # e.g., "substanceAdministration"
                    "display_name": str,      # e.g., "LEVOTHYROXINE SODIUM 0.112MG"
                    "status_code": str,       # e.g., "completed"
                    "effective_time": str,    # e.g., "20230315"
                    "value": str,
                    "unit": str,
                    "result": str,
                    "text_content": str,
                    "dosage_instruction": str,
                    "participant_substances": [str],
                    "entry_relationships": [
                        {
                            "type": str,
                            "target": str,
                            "nullFlavor": str
                        }
                    ],
                    "clinical_codes": [
                        {
                            "code": str,
                            "system": str,
                            "displayName": str,
                            "display": str,
                            "version": str,
                            "nullFlavor": str  # CDA spec compliance
                        }
                    ]
                }
            ],
            "clinical_codes": [],     # Section-level codes
            "narrative_text": str     # Original CDA narrative
        }
    ]
}
```

## Template Filter Usage Examples

### 1. NullFlavor-Aware Clinical Display

#### Basic Usage

```html
<!-- OLD: Basic fallback with no nullFlavor handling -->
{{ entry.display_name|default:"Clinical Entry" }}

<!-- NEW: CDA spec-compliant nullFlavor handling -->
{{ entry|safe_clinical_display:"display_name" }}
```

#### Advanced Usage with Context

```html
<!-- Patient name with nullFlavor support -->
{{ patient_identity|safe_clinical_display:"given_name" }}
{{ patient_identity|safe_clinical_display:"family_name" }}

<!-- Clinical entry display with fallback hierarchy -->
{{ entry|safe_clinical_display:"display_name" }}
<!-- Will check: entry.display_name → entry.code_display → nullFlavor → "Unknown" -->
```

### 2. Clinical Value Formatting

#### Numeric Values with Units

```html
<!-- OLD: Manual unit handling -->
{{ entry.value|default:entry.result }}
{% if entry.unit %}{{ entry.unit }}{% endif %}

<!-- NEW: Integrated numeric formatting -->
{{ entry|format_clinical_value:"numeric" }}
<!-- Handles: value + unit, nullFlavor codes, missing data -->
```

#### Date/Time Values

```html
<!-- OLD: Direct display -->
{{ entry.effective_time }}

<!-- NEW: Date formatting with nullFlavor -->
{{ entry.effective_time|format_clinical_value:"date" }}
<!-- Converts: "20230315" → "15/03/2023", handles nullFlavor -->
```

#### Clinical Codes

```html
<!-- OLD: Manual display logic -->
{% if code.display %}
  {{ code.display }}
{% elif code.displayName %}
  {{ code.displayName }}
{% elif code.code %}
  Code: {{ code.code }}
{% endif %}

<!-- NEW: Standardized code display -->
{{ code|format_clinical_value:"code" }}
<!-- Handles: displayName → display → "Code: {code}" → nullFlavor -->
```

### 3. NullFlavor Handling

#### Direct Value Handling

```html
<!-- Status codes with nullFlavor support -->
{{ entry.status_code|handle_null_flavor }}

<!-- Clinical relationships -->
{{ relationship.type|handle_null_flavor|title }}
{{ relationship.target|handle_null_flavor }}
```

#### Complex Data Extraction

```html
<!-- Extract nullFlavor from nested structures -->
{% with null_flavor=entry|extract_null_flavor %}
  {{ entry.some_field|handle_null_flavor:null_flavor }}
{% endwith %}
```

## Template-to-JSON Mapping Examples

### Medication Section Example

#### JSON Structure (from debug data)

```json
{
  "section_id": "psMedicationSummary",
  "title": "Medication Summary",
  "structured_entries": [
    {
      "entry_type": "substanceAdministration",
      "display_name": "LEVOTHYROXINE SODIUM 0.112MG oral tablet",
      "status_code": "completed",
      "effective_time": "20230315",
      "dosage_instruction": "Take once daily",
      "clinical_codes": [
        {
          "code": "18414-5",
          "system": "http://loinc.org",
          "displayName": "Medication summary Document"
        }
      ]
    }
  ]
}
```

#### Template Usage

```html
<!-- Section Header -->
<h5>{{ section.title|handle_null_flavor }}</h5>

<!-- Entry Loop -->
{% for entry in section.structured_entries %}
<div class="medication-entry">
  <!-- Medication Name -->
  <h6>{{ entry|safe_clinical_display:"display_name" }}</h6>

  <!-- Status Badge -->
  <span class="badge bg-success">
    {{ entry.status_code|handle_null_flavor|title }}
  </span>

  <!-- Effective Date -->
  <p><strong>Started:</strong>
    {{ entry.effective_time|format_clinical_value:"date" }}
  </p>

  <!-- Dosage Instructions -->
  {% if entry.dosage_instruction %}
  <p><strong>Dosage:</strong>
    {{ entry.dosage_instruction|handle_null_flavor }}
  </p>
  {% endif %}

  <!-- Clinical Codes -->
  {% for code in entry.clinical_codes %}
  <span class="code-badge">
    {{ code.code|handle_null_flavor }}
    <small>({{ code|format_clinical_value:"code" }})</small>
  </span>
  {% endfor %}
</div>
{% endfor %}
```

### Laboratory Results Example

#### JSON Structure

```json
{
  "section_id": "psCodedResults",
  "title": "Laboratory Results",
  "structured_entries": [
    {
      "entry_type": "observation",
      "display_name": "Hemoglobin A1c",
      "value": "7.2",
      "unit": "%",
      "status_code": "completed",
      "clinical_codes": [
        {
          "code": "4548-4",
          "system": "http://loinc.org",
          "displayName": "Hemoglobin A1c/Hemoglobin.total in Blood"
        }
      ]
    }
  ]
}
```

#### Template Usage

```html
<!-- Lab Results Display -->
{% for entry in section.structured_entries %}
<div class="lab-result">
  <!-- Test Name -->
  <h6>{{ entry|safe_clinical_display:"display_name" }}</h6>

  <!-- Result Value with Unit -->
  <div class="result-value">
    <strong>Result:</strong>
    {{ entry|format_clinical_value:"numeric" }}
  </div>

  <!-- Status -->
  <span class="badge">{{ entry.status_code|handle_null_flavor|title }}</span>

  <!-- LOINC Code -->
  {% for code in entry.clinical_codes %}
  <div class="loinc-code">
    <strong>LOINC:</strong> {{ code|format_clinical_value:"code" }}
  </div>
  {% endfor %}
</div>
{% endfor %}
```

## NullFlavor Specification Compliance

### HL7 CDA NullFlavor Codes

| Code | Meaning | Template Output |
|------|---------|----------------|
| UNK | Unknown | "Unknown" |
| NA | Not Applicable | "Not Applicable" |
| NI | No Information | "No Information" |
| ASKU | Asked but Unknown | "Unknown (Asked)" |
| NAV | Not Available | "Not Available" |
| MSK | Masked | "Masked" |
| NP | Not Present | "Not Present" |
| TRC | Trace | "Trace Amount" |

### Template Implementation

```html
<!-- Comprehensive nullFlavor handling -->
<div class="patient-data">
  <!-- Patient identifiers with nullFlavor support -->
  {% for identifier in patient_identity.patient_identifiers %}
  <p>
    <strong>{{ identifier.assigningAuthorityName|handle_null_flavor }}:</strong>
    {{ identifier.extension|handle_null_flavor }}
    {% if identifier.nullFlavor %}
      <small class="text-muted">({{ identifier.nullFlavor }})</small>
    {% endif %}
  </p>
  {% endfor %}

  <!-- Clinical values with automatic nullFlavor detection -->
  <p><strong>Birth Date:</strong>
    {{ patient_identity.birth_date|format_clinical_value:"date" }}
  </p>

  <p><strong>Gender:</strong>
    {{ patient_identity.gender|handle_null_flavor }}
  </p>
</div>
```

## Performance Considerations

### Filter Usage Best Practices

1. **Cache Complex Operations**

   ```html
   <!-- Cache nullFlavor extraction for reuse -->
   {% with entry_null_flavor=entry|extract_null_flavor %}
     {{ entry.field1|handle_null_flavor:entry_null_flavor }}
     {{ entry.field2|handle_null_flavor:entry_null_flavor }}
   {% endwith %}
   ```

2. **Optimize Loop Processing**

   ```html
   <!-- Pre-filter sections with data -->
   {% for section in processed_sections %}
     {% if section.structured_entries %}
       <!-- Process section -->
     {% endif %}
   {% endfor %}
   ```

3. **Minimize Filter Calls**

   ```html
   <!-- Good: Single filter call -->
   {{ entry|safe_clinical_display:"display_name" }}

   <!-- Avoid: Multiple filter calls for same data -->
   {{ entry.display_name|handle_null_flavor|default:"Unknown" }}
   ```

## Error Handling

### Template Error Prevention

```html
<!-- Safe clinical code access -->
{% for code in entry.clinical_codes|default:empty_list %}
  <span class="code">{{ code|format_clinical_value:"code" }}</span>
{% endfor %}

<!-- Defensive programming for nested structures -->
{% if entry.entry_relationships %}
  {% for rel in entry.entry_relationships %}
    {{ rel.type|handle_null_flavor:"UNK" }}
  {% endfor %}
{% endif %}
```

### Debug Information

```html
<!-- Development mode debug info -->
{% if debug %}
<div class="debug-info">
  <small>Entry type: {{ entry.entry_type|default:"Unknown" }}</small><br>
  <small>Has nullFlavor: {{ entry|extract_null_flavor|default:"None" }}</small><br>
  <small>Clinical codes: {{ entry.clinical_codes|length|default:0 }}</small>
</div>
{% endif %}
```

## Migration Guide

### Converting Existing Templates

1. **Replace Basic Defaults**

   ```html
   <!-- Before -->
   {{ field|default:"Unknown" }}

   <!-- After -->
   {{ field|handle_null_flavor }}
   ```

2. **Update Clinical Displays**

   ```html
   <!-- Before -->
   {% if entry.display_name %}
     {{ entry.display_name }}
   {% else %}
     Clinical Entry
   {% endif %}

   <!-- After -->
   {{ entry|safe_clinical_display:"display_name" }}
   ```

3. **Standardize Value Formatting**

   ```html
   <!-- Before -->
   {{ entry.value }}{% if entry.unit %} {{ entry.unit }}{% endif %}

   <!-- After -->
   {{ entry|format_clinical_value:"numeric" }}
   ```

This documentation provides a complete reference for implementing proper CDA template-view mapping with nullFlavor specification compliance.
