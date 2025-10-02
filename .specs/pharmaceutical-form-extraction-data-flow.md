# Pharmaceutical Form Extraction Data Flow

**Document**: Technical Architecture Guide  
**Date**: October 2, 2025  
**Context**: Django_NCP European Healthcare Interoperability System  
**Scope**: CDA → CTS → Template Data Flow for Pharmaceutical Form Codes

## Overview

This document describes the complete data flow for pharmaceutical form extraction from European CDA documents through the Clinical Terminology Service (CTS) to Django template rendering. This pattern ensures proper healthcare terminology resolution without hardcoded clinical data.

## Critical Requirements

### European Healthcare Standards Compliance
- **CDA Document Architecture**: European healthcare interoperability standard
- **FHIR R4 Compatibility**: Modern healthcare data exchange format
- **CTS Integration**: Clinical Terminology Service for code resolution
- **GDPR Compliance**: Patient data privacy and audit trails

### Data Integrity Principles
- **No Hardcoded Clinical Data**: All clinical codes must come from authoritative sources
- **Proper Code System Context**: Both code AND codeSystem must be passed to CTS
- **Fallback Handling**: Graceful degradation when terminology resolution fails
- **Audit Logging**: Complete traceability of code resolution processes

## Complete Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CDA XML DOCUMENT                           │
├─────────────────────────────────────────────────────────────────┤
│ <pharm:formCode code="50060200"                                 │
│                 codeSystem="0.4.0.127.0.16.1.1.2.1"           │
│                 displayName="" />                               │
│ <!-- displayName often empty in European CDA documents -->     │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                CDA PARSER SERVICE                               │
│              (cda_parser_service.py)                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Extract pharmaceutical form elements:                       │
│    form_code = form_elem.get("code", "")                      │
│    form_code_system = form_elem.get("codeSystem", "")         │
│    form_display = form_elem.get("displayName", "")            │
│                                                                │
│ 2. CTS Resolution (if displayName empty):                     │
│    translator = TerminologyTranslator()                       │
│    resolved_display = translator.resolve_code(                │
│        form_code, form_code_system) ✅                        │
│                                                                │
│ 3. Structure medication data:                                 │
│    med_info["formCode"] = {                                   │
│        "code": form_code,                                     │
│        "codeSystem": form_code_system,                        │
│        "displayName": resolved_display                        │
│    }                                                          │
│    med_info["pharmaceutical_form_code"] = form_code           │
│    med_info["pharmaceutical_form_code_system"] = form_code_system │
│    med_info["pharmaceutical_form"] = resolved_display         │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│            COMPREHENSIVE CLINICAL DATA SERVICE                 │
│        (comprehensive_clinical_data_service.py)                │
├─────────────────────────────────────────────────────────────────┤
│ 1. Extract formCode structure:                                │
│    if 'formCode' in cda_medication:                           │
│        form_code_data = cda_medication['formCode']            │
│        fields_for_conversion['pharmaceutical_form_code'] =    │
│            form_code_data.get('code', '')                     │
│        fields_for_conversion['pharmaceutical_form_code_system'] = │
│            form_code_data.get('codeSystem', '')               │
│                                                                │
│ 2. CTS Resolution with codeSystem:                            │
│    form_display = self.terminology_service.resolve_code(      │
│        form_code, form_code_system) ✅                        │
│                                                                │
│ 3. Map to template variables:                                 │
│    medication_data['pharmaceutical_form'] = form_display      │
│    medication_data['pharmaceutical_form_code'] = form_code    │
│    medication_data['form'] = {                                │
│        'code': form_code,                                     │
│        'display_name': form_display                           │
│    }                                                          │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              CLINICAL TERMINOLOGY SERVICE                      │
│              (terminology_translator.py)                       │
├─────────────────────────────────────────────────────────────────┤
│ def resolve_code(self, code: str, code_system: str = None):    │
│                                                                │
│ 1. Cache lookup:                                              │
│    cache_key = f"code_resolution_{code_system}_{code}_{lang}" │
│                                                                │
│ 2. Database query with code_system context:                   │
│    if code_system:                                            │
│        query_filters['code_system'] = code_system             │
│        concept = ValueSetConcept.objects.filter(**filters)    │
│                                                                │
│ 3. Fallback to OID matching:                                  │
│    concept = ValueSetConcept.objects.filter(                  │
│        code=code, value_set__oid=code_system)                 │
│                                                                │
│ 4. Translation resolution:                                    │
│    ConceptTranslation.objects.filter(                         │
│        concept=concept, language_code=target_language)        │
│                                                                │
│ Returns: "Solution for injection in pre-filled pen"           │
└─────────────────────────────────────┬───────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DJANGO TEMPLATE RENDERING                      │
│              (clinical_information_content.html)               │
├─────────────────────────────────────────────────────────────────┤
│ Template variable hierarchy (checked in order):               │
│                                                                │
│ 1. med.data.pharmaceutical_form ✅                            │
│    {% if med.data.pharmaceutical_form %}                      │
│        {{ med.data.pharmaceutical_form }}                     │
│                                                                │
│ 2. med.pharmaceutical_form ✅                                 │
│    {% elif med.pharmaceutical_form %}                         │
│        {{ med.pharmaceutical_form }}                          │
│                                                                │
│ 3. med.form.display_name ✅                                   │
│    {% elif med.form.display_name %}                           │
│        {{ med.form.display_name }}                            │
│                                                                │
│ 4. Template filter fallback:                                  │
│    {% else %}                                                  │
│        {{ med|smart_dose_form }}                              │
│    {% endif %}                                                │
│                                                                │
│ Result: "Solution for injection in pre-filled pen"            │
└─────────────────────────────────────────────────────────────────┘
```

## Code System Examples

### European Pharmaceutical Form Codes
- **Code System**: `0.4.0.127.0.16.1.1.2.1`
- **Authority**: European Medicines Agency (EMA)
- **Examples**:
  - `50060200` → "Solution for injection in pre-filled pen"
  - `10219000` → "Tablet"
  - `50068000` → "Film-coated tablet"

### SNOMED CT Pharmaceutical Forms
- **Code System**: `2.16.840.1.113883.6.96`
- **Authority**: SNOMED International
- **Examples**:
  - `421026006` → "Film-coated tablet"
  - `385219001` → "Solution for injection"
  - `426684005` → "Prolonged-release tablet"

## Implementation Details

### CDA Parser Service Enhancement
```python
# Before (BROKEN): Only passed code
resolved_display = translator.resolve_code(form_code)

# After (FIXED): Passes both code and codeSystem
resolved_display = translator.resolve_code(form_code, form_code_system)
```

### Comprehensive Service Enhancement
```python
# Before (BROKEN): Only extracted code
fields_for_conversion['pharmaceutical_form_code'] = form_code_data.get('code', '')

# After (FIXED): Extracts both code and codeSystem
fields_for_conversion['pharmaceutical_form_code'] = form_code_data.get('code', '')
fields_for_conversion['pharmaceutical_form_code_system'] = form_code_data.get('codeSystem', '')

# CTS call enhancement
form_display = self.terminology_service.resolve_code(form_code, form_code_system)
```

## Error Handling & Logging

### CTS Resolution Logging
```python
logger.info(f"CTS resolved pharmaceutical form code {form_code} (system: {form_code_system}) to '{form_display}'")
```

### Fallback Strategy
1. **Primary**: CTS resolution with code + codeSystem
2. **Secondary**: CTS resolution with code only (for globally unique codes)
3. **Tertiary**: Original displayName from CDA (if present)
4. **Fallback**: Template filter with pattern matching

## Validation & Testing

### Test Case: European Form Code
```python
code = "50060200"
code_system = "0.4.0.127.0.16.1.1.2.1"
expected = "Solution for injection in pre-filled pen"

result = translator.resolve_code(code, code_system)
assert result == expected
```

### Integration Test
```python
def test_pharmaceutical_form_extraction():
    # Mock CDA data with formCode
    cda_medication = {
        'formCode': {
            'code': '50060200',
            'codeSystem': '0.4.0.127.0.16.1.1.2.1',
            'displayName': ''
        }
    }
    
    # Process through comprehensive service
    result = service._convert_valueset_fields_to_medication_data(cda_medication)
    
    # Verify template variables are set
    assert result['pharmaceutical_form'] == "Solution for injection in pre-filled pen"
    assert result['form']['display_name'] == "Solution for injection in pre-filled pen"
```

## Benefits of This Architecture

### Healthcare Standards Compliance
- ✅ **FHIR R4 Compatible**: Uses standard terminology resolution patterns
- ✅ **European Interoperability**: Supports EMA pharmaceutical form codes
- ✅ **GDPR Compliant**: No hardcoded clinical data, full audit trails

### Data Integrity
- ✅ **Authoritative Sources**: All codes resolved through CTS master catalog
- ✅ **Context Preservation**: Code system provides proper terminology context
- ✅ **Fallback Strategy**: Graceful degradation for unknown codes

### Maintainability
- ✅ **No Hardcoded Data**: Easy to update terminology without code changes
- ✅ **Centralized Resolution**: Single CTS service for all terminology
- ✅ **Comprehensive Logging**: Full traceability for debugging

## Related Documentation

- [CTS Integration Guide](../docs/cts-integration-guide.md)
- [European Healthcare Compliance](../docs/european-healthcare-compliance.md)
- [FHIR R4 Medication Mapping](../docs/fhir-medication-mapping.md)
- [Testing Standards](../.specs/testing-and-modular-code-standards.md)

---

**Last Updated**: October 2, 2025  
**Reviewed By**: AI Coding Agent  
**Version**: 1.0  
**Status**: Active Implementation