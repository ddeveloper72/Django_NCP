# CDA Document Badge System Documentation

## Overview

The Django NCP application implements a comprehensive badge system to provide visual indicators for medical code systems in CDA (Clinical Document Architecture) documents. This system enhances clinical data readability by displaying standardized medical terminology codes alongside their translated content.

## Architecture

### 1. Badge Generation (Python Backend)

#### Primary Service: `PSTableRenderer`

**File**: `patient_data/services/ps_table_renderer.py`

The badge system is entirely Python-driven, generating HTML spans with CSS classes that are then styled by the frontend.

#### Key Methods

##### `_add_code_system_badge(text, code_system, code)`

**Location**: Lines 86-112

```python
def _add_code_system_badge(self, text: str, code_system: str = None, code: str = None) -> str:
    """
    Add code system badge to translated text for NCP developer verification.
    
    Args:
        text: The translated text
        code_system: The code system (LOINC, SNOMED, ICD10, ATC, etc.)
        code: The specific code value
    
    Returns:
        Text with code system badge HTML appended
    """
    if not text or not code_system:
        return text
    
    # Generate CSS class from code system name
    system_class = code_system.lower().replace("-", "").replace(" ", "")
    badge_text = f"{code_system.upper()}"
    if code:
        badge_text += f": {code}"
    
    # Generate HTML span with CSS classes
    badge_html = f'<span class="code-system-badge {system_class}">{badge_text}</span>'
    return f"{text}{badge_html}"
```

##### `_detect_code_system(term)`

**Location**: Lines 117-270

Automatically detects the appropriate code system for medical terms using pattern matching:

**Supported Code Systems:**

- **ATC** (Anatomical Therapeutic Chemical): Medication classifications
- **SNOMED-CT**: Clinical terminology (routes, dosage forms, conditions)
- **UCUM**: Units of measurement (mg, ml, etc.)
- **ICD-10**: Disease classifications
- **NDC**: National Drug Codes
- **LOINC**: Laboratory data identifiers

**Pattern Examples:**

```python
medication_patterns = {
    "retrovir": ("ATC", "J05AF01"),     # Zidovudine
    "viread": ("ATC", "J05AF07"),       # Tenofovir disoproxil
    "viramune": ("ATC", "J05AG01"),     # Nevirapine
}

route_patterns = {
    "oral": ("SNOMED", "26643006"),     # Oral route
    "intravenous": ("SNOMED", "47625008"), # IV route
}

dosage_unit_patterns = {
    "mg": ("UCUM", "mg"),               # Milligram
    "ml": ("UCUM", "ml"),               # Milliliter
}
```

### 2. Application in Tables

#### Medication Table Rendering

**Location**: `_render_medication_table()` around line 1459

```python
# Apply badges to medication names
code_system, code = self._detect_code_system(med_name)
med_name_with_badge = self._add_code_system_badge(med_name, code_system, code)

# Apply badges to active ingredients
if active_ingredient and active_ingredient != med_name:
    ing_code_system, ing_code = self._detect_code_system(active_ingredient)
    active_ingredient = self._add_code_system_badge(active_ingredient, ing_code_system, ing_code)
```

### 3. Generated HTML Structure

The Python code generates HTML like:

```html
<!-- Medication with ATC code -->
RETROVIR<span class="code-system-badge atc">ATC: J05AF01</span>

<!-- Dosage with UCUM unit -->
300 mg par 12 Heure<span class="code-system-badge ucum">UCUM: 300 MG</span>

<!-- Route with SNOMED code -->
oral<span class="code-system-badge snomed">SNOMED: 26643006</span>
```

### 4. CSS Styling (Frontend)

#### Primary Stylesheet: `static/scss/pages/_patient_cda.scss`

```scss
.code-system-badge {
  display: inline-block !important;
  padding: 0.0625rem 0.1875rem !important; // 1px 3px
  border-radius: 3px !important;
  font-size: 0.5rem !important;            // 8px
  font-weight: 400 !important;
  font-family: 'Courier New', monospace !important;
  margin: 0.0625rem 0.125rem 0 0 !important; // 1px 2px 0 0
  white-space: nowrap;
  max-height: 0.875rem !important;         // 14px
  line-height: 1 !important;
  vertical-align: baseline;
  text-transform: uppercase;
  letter-spacing: 0.025em;

  // Color coding by system
  &.atc     { background: #f8f0fa; color: #7b1fa2; border-color: #c48bd1; }
  &.snomed  { background: #fffbf0; color: #856404; border-color: #e6cc80; }
  &.ucum    { background: #f0fff0; color: #228b22; border-color: #90ee90; }
  &.icd10   { background: #f0f7ff; color: #085a9f; border-color: #66b3ff; }
  &.ndc     { background: #fff0f5; color: #6b2c91; border-color: #ba68c8; }
  &.loinc   { background: #f0f8f0; color: #2d5a27; border-color: #4a7c59; }
}
```

#### Table Cell Enhancements

```scss
.patient-summary-table,
.ps-table {
  td, .ps-td {
    vertical-align: top;
    padding: 0.375rem 0.5rem;
    
    .badge-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.0625rem 0.125rem;
      margin-top: 0.125rem;
      align-items: flex-start;
    }
  }
}
```

## Usage Flow

1. **CDA Document Processing**: Patient data is extracted from CDA XML
2. **Table Rendering**: `PSTableRenderer` processes medical terms
3. **Code Detection**: Each term is analyzed for medical code systems
4. **Badge Generation**: HTML spans are created with appropriate CSS classes
5. **Template Rendering**: Django template renders the enhanced HTML
6. **CSS Styling**: Browser applies compact badge styles

## Supported Medical Standards

- **PS Display Guidelines**: Patient Summary display compliance
- **HL7 CDA R2/R3**: Clinical Document Architecture
- **IHE**: Integrating the Healthcare Enterprise profiles
- **EU NCP**: European Network of Competent Authorities requirements

## Benefits

1. **Clinical Accuracy**: Visual verification of medical code mappings
2. **Developer Support**: Clear indication of terminology systems in use
3. **Compliance**: Meets European healthcare interoperability requirements
4. **User Experience**: Compact, unobtrusive design that doesn't disrupt reading flow

## File Dependencies

- **Backend**: `patient_data/services/ps_table_renderer.py`
- **Styling**: `static/scss/pages/_patient_cda.scss`
- **Compiled CSS**: `static/css/patient_cda_ps_guidelines.css`, `static/css/main.css`
- **Templates**: `templates/jinja2/patient_data/patient_details.html`

## Maintenance Notes

- Badge patterns are manually maintained in `_detect_code_system()` method
- New medical terms require pattern updates
- CSS compilation needed after SCSS changes
- Django static files collection required for deployment
