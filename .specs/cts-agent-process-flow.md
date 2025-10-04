# CTS Agent Process Flow - International Healthcare Code Translation

## Overview

The Clinical Terminology Service (CTS) Agent provides international healthcare code translation using a **dual-key system** where clinical codes are paired with their Code System OID numbers to ensure accurate terminology resolution across different countries and languages.

## Core Concept: Dual-Key Translation System

### Key-Value Pair Relationship
```
Clinical Code + Code System OID → Localized Display Text
```

**International XML CDA Structure:**
```xml
<code code="420134006" 
      codeSystem="2.16.840.1.113883.6.96" 
      displayName="" />
```

**CTS Agent Resolution:**
- **Combined Key**: `420134006` + `2.16.840.1.113883.6.96` (SNOMED CT)
- **Master Value Catalogue Lookup**: OID-specific terminology database
- **Localized Output**: "Propensity to adverse reactions" (EN) / "Propensão a reações adversas" (PT)

## Process Flow

### 1. Code Extraction Phase
```python
# Extract from CDA
code_value = element.get("code", "")           # e.g., "420134006"
code_system = element.get("codeSystem", "")    # e.g., "2.16.840.1.113883.6.96"
display_name = element.get("displayName", "")  # Often empty in international exchange
```

### 2. CTS Agent Invocation
```python
# Enhanced CDA Processor Integration
if display_name and display_name.strip():
    # Use existing displayName if present
    data["field_display"] = display_name
elif code_value:
    # Invoke CTS agent with dual-key lookup
    cts_result = self._lookup_valueset_term(code_value, field_type)
    if cts_result:
        data["field_display"] = cts_result
    else:
        data["field_display"] = f"Code: {code_value}"
```

### 3. Master Value Catalogue Lookup
```python
# CTS Agent Internal Process
def _lookup_valueset_term(self, code: str, field_label: str) -> str:
    """
    Dual-key lookup: Code + Code System OID → Localized Display
    """
    # 1. Find active concept by code
    concept = ValueSetConcept.objects.filter(
        code=code.strip(),
        status="active"
    ).first()
    
    # 2. Get localized translation for target language/country
    if concept:
        translation = ConceptTranslation.objects.filter(
            concept=concept,
            target_language=self.target_language  # e.g., "en", "pt", "de"
        ).first()
        
        return translation.translated_display if translation else concept.display
```

### 4. Country-Specific Rendering
```python
# Template Rendering with Localized Terminology
{% firstof cell_data.display_value cell_data.value "N/A" %}
```

## Code System OID Registry

### Primary Healthcare Code Systems
- **SNOMED CT**: `2.16.840.1.113883.6.96`
  - Clinical findings, procedures, medications
  - Used for: Allergies, manifestations, reactions
- **LOINC**: `2.16.840.1.113883.6.1`
  - Laboratory tests, clinical observations
  - Used for: Lab results, vital signs
- **ICD-10**: `2.16.840.1.113883.6.3`
  - Diagnoses, conditions
  - Used for: Medical problems, diagnoses
- **RxNorm**: `2.16.840.1.113883.6.88`
  - Medications, pharmaceutical products
  - Used for: Medication codes

## CTS Agent Enhancement Requirements

### Current Implementation
✅ **Single-key lookup**: Code → Display text
✅ **Language support**: Target language configuration
✅ **Fallback logic**: Graceful degradation when lookup fails

### Required Enhancements
🔧 **Dual-key lookup**: Code + Code System OID → Display text
🔧 **OID validation**: Ensure code system matches expected OID
🔧 **Multi-system support**: Handle different code systems appropriately
🔧 **Cache optimization**: Reduce database queries for repeated lookups

### Enhanced CTS Agent Architecture
```python
def _lookup_valueset_term_enhanced(self, code: str, code_system: str, field_label: str) -> str:
    """
    Enhanced dual-key CTS lookup with OID validation
    
    Args:
        code: Clinical code (e.g., "420134006")
        code_system: Code system OID (e.g., "2.16.840.1.113883.6.96")
        field_label: Context label for logging
    
    Returns:
        Localized display text or fallback
    """
    # 1. Validate code system OID
    if not self._is_supported_code_system(code_system):
        logger.warning(f"Unsupported code system: {code_system}")
        return f"Code: {code}"
    
    # 2. Dual-key lookup
    concept = ValueSetConcept.objects.filter(
        code=code.strip(),
        code_system=code_system,  # NEW: OID-specific lookup
        status="active"
    ).first()
    
    # 3. Country/language-specific translation
    if concept:
        translation = ConceptTranslation.objects.filter(
            concept=concept,
            target_language=self.target_language,
            target_country=self.target_country  # NEW: Country-specific
        ).first()
        
        if translation:
            return translation.translated_display
        else:
            # Fallback to default display
            return concept.display
    
    # 4. Graceful fallback
    return f"Code: {code} (System: {self._get_code_system_name(code_system)})"
```

## Clinical Section Analysis

### ✅ Currently CTS-Enabled Sections

#### Allergies & Intolerances
- **Reaction Type**: `420134006` + SNOMED CT → "Propensity to adverse reactions"
- **Agent/Allergen**: `260176001` + SNOMED CT → "Kiwi fruit"
- **Manifestation**: `43116000` + SNOMED CT → "Eczema"

### 🔧 Sections Requiring CTS Integration

#### 1. Medical Problems
**Current State**: Basic code extraction without CTS lookup
**Required Enhancement**:
```python
# Problem condition codes
condition_code = problem.get("condition_code", "")
condition_system = problem.get("condition_system", "")
# Need: CTS lookup for ICD-10/SNOMED CT condition codes
```

#### 2. Medications
**Current State**: Limited terminology resolution
**Required Enhancement**:
```python
# Medication codes (RxNorm, SNOMED CT)
medication_code = med.get("medication_code", "")
# Route codes (SNOMED CT)
route_code = med.get("route_code", "")
# Form codes (pharmaceutical forms)
form_code = med.get("form_code", "")
# Need: Multi-system CTS lookup
```

#### 3. Procedures
**Current State**: No CTS integration
**Required Enhancement**:
```python
# Procedure codes (SNOMED CT, ICD-10-PCS)
procedure_code = procedure.get("procedure_code", "")
# Need: CTS lookup for procedure terminology
```

#### 4. Vital Signs
**Current State**: Limited code resolution
**Required Enhancement**:
```python
# Vital sign codes (LOINC)
vital_code = vital.get("vital_code", "")
# Unit codes (UCUM)
unit_code = vital.get("unit_code", "")
# Need: LOINC-specific CTS lookup
```

#### 5. Laboratory Results
**Current State**: Not yet implemented
**Required Enhancement**:
```python
# Lab test codes (LOINC)
test_code = lab.get("test_code", "")
# Result interpretation codes
interpretation_code = lab.get("interpretation_code", "")
# Need: LOINC CTS integration
```

## Implementation Priority

### Phase 1: CTS Agent Enhancement
1. **Dual-key lookup**: Implement Code + OID system
2. **OID validation**: Add code system validation
3. **Multi-system support**: Handle SNOMED CT, LOINC, ICD-10, RxNorm
4. **Performance optimization**: Add caching layer

### Phase 2: Clinical Section Integration
1. **Medical Problems**: ICD-10/SNOMED CT condition codes
2. **Medications**: RxNorm/SNOMED CT medication, route, form codes
3. **Procedures**: SNOMED CT/ICD-10-PCS procedure codes
4. **Vital Signs**: LOINC codes and UCUM units

### Phase 3: Advanced Features
1. **Country-specific translations**: Regional terminology variants
2. **Synonym support**: Multiple display options per code
3. **Historical versioning**: Code system version management
4. **Validation rules**: Clinical code appropriateness checking

## Benefits of Enhanced CTS Integration

### For Healthcare Professionals
- **Consistent Terminology**: Same codes display identical meanings across countries
- **Language Localization**: Clinical terms in native language
- **Professional Standards**: Proper medical terminology instead of codes

### For International Interoperability
- **Standards Compliance**: Full HL7 CDA and FHIR compatibility
- **Cross-Border Exchange**: Seamless data sharing between EU member states
- **Quality Assurance**: Validated terminology prevents misinterpretation

### For System Maintainability
- **Centralized Management**: Single point for terminology updates
- **Scalable Architecture**: Easy addition of new code systems
- **Performance Optimization**: Cached lookups reduce database load

This documentation provides the foundation for implementing comprehensive CTS integration across all clinical sections in the Django_NCP system.