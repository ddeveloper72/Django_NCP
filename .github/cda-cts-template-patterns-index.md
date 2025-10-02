# CDA → CTS → Template Data Flow Patterns

This document catalogs the essential data flow patterns used throughout the Django_NCP healthcare interoperability system for processing European CDA documents through Clinical Terminology Service (CTS) resolution to Django template rendering.

## Core Patterns

### 1. Pharmaceutical Form Extraction
- **File**: [pharmaceutical-form-extraction-data-flow.md](pharmaceutical-form-extraction-data-flow.md)
- **Pattern**: CDA pharm:formCode → CTS resolution → Template variables
- **Key Learning**: Both code AND codeSystem must be passed to CTS for proper European healthcare terminology resolution

### 2. ATC Code Resolution
- **Pattern**: CDA medication codes → CTS ATC lookup → Active ingredient display
- **Implementation**: Enhanced CDA processor with proper CTS integration
- **Note**: Removed hardcoded brand→ingredient mappings in favor of CTS resolution

### 3. Dosage Schedule Processing
- **Pattern**: CDA timing events → CTS timing code resolution → Human-readable schedules
- **Examples**: 
  - `ACM` → "before breakfast (from lat. ante cibus matutinus)"
  - `ACV` → "before dinner"
  - `PCM` → "after breakfast"

## Anti-Patterns (Removed)

### ❌ Hardcoded Clinical Mappings
```python
# REMOVED: Hardcoded brand to ingredient mapping
brand_to_ingredient_mapping = {
    'Tresiba': 'A10BH05',
    'Eutirox': 'H03AA01',
    # ... hundreds of hardcoded mappings
}
```

### ❌ Pattern-Based Fallbacks
```python
# REMOVED: Hardcoded condition patterns
condition_patterns = {
    'diabetes': 'Diabetes mellitus',
    'hypertension': 'Hypertensive disorder',
    # ... pattern matching instead of CTS
}
```

## Best Practices

### 1. CTS Integration
- Always pass both `code` and `codeSystem` to CTS
- Implement proper fallback hierarchy
- Log all CTS resolution attempts
- Cache resolved terms appropriately

### 2. Data Structure Preservation
- Maintain complete code context through pipeline
- Preserve original CDA structure for audit trails
- Map to multiple template variables for flexibility

### 3. Error Handling
- Graceful degradation when CTS resolution fails
- Comprehensive logging for debugging
- Fallback to original displayName if available

## Template Variable Hierarchy

Standard pattern for clinical terminology in templates:
```django
{% if med.data.pharmaceutical_form %}
    {{ med.data.pharmaceutical_form }}
{% elif med.pharmaceutical_form %}
    {{ med.pharmaceutical_form }}
{% elif med.form.display_name %}
    {{ med.form.display_name }}
{% else %}
    {{ med|smart_dose_form }}
{% endif %}
```

## Related Files

- [Testing and Modular Code Standards](testing-and-modular-code-standards.md)
- [SCSS Standards Index](scss-standards-index.md)
- [European Healthcare Compliance](../docs/european-healthcare-compliance.md)

---

**Purpose**: Central reference for CDA processing patterns  
**Audience**: Django_NCP development team  
**Maintenance**: Update when new CTS patterns are implemented