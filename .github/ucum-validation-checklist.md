# UCUM Pharmaceutical Quantity Validation Checklist

## 📝 Decision Log Entry: UCUM Units in `<pharm:quantity>`

**Context**: Encountered `<pharm:quantity>` with numerator and denominator expressed as PQ (Physical Quantity) values.

**Example**:
```xml
<pharm:quantity>
  <numerator xsi:type="PQ" value="100" unit="ug" />
  <denominator xsi:type="PQ" value="1" unit="1" />
</pharm:quantity>
```

## 🎯 Decision

- All unit attributes in PQ elements must conform to UCUM (Unified Code for Units of Measure)
- "ug" is the UCUM code for microgram
- "1" is the UCUM code for dimensionless unit (used when expressing "per 1 unit")
- This encoding represents 100 micrograms per 1 unit of product

## 📋 Rationale

- **UCUM is mandated** by HL7 CDA R2 and FHIR for unambiguous unit representation
- **Ensures semantic interoperability** across systems (e.g., dosage calculations, decision support)
- **Prevents ambiguity** from local abbreviations (e.g., "mcg" vs "µg")

## 📚 References

- HL7 CDA R2 Pharmacy Templates (SubstanceAdministration / quantity)
- [UCUM Specification: UCUM Online Browser](https://ucum.org/ucum.html)

## ✅ Compliance Checklist: UCUM in PQ Elements

### Validation Requirements
- [ ] **Verify UCUM compliance**: Every unit attribute in `<PQ>` must be a valid UCUM code
- [ ] **Numerator meaning**: Represents the amount of active ingredient (e.g., 100 ug)
- [ ] **Denominator meaning**: Represents the basis (e.g., 1 = per unit, mL = per volume)
- [ ] **No local codes**: Reject or flag non-UCUM abbreviations (e.g., "mcg" instead of "ug")
- [ ] **Semantic validation**: Confirm numerator/denominator combination expresses a valid strength (e.g., mg/mL, ug/1)
- [ ] **Documentation**: Record UCUM validation in decision logs for traceability

### Common UCUM Codes for Pharmaceuticals

| UCUM Code | Meaning | Example Usage |
|-----------|---------|---------------|
| `ug` | microgram | Hormone doses, vitamins |
| `mg` | milligram | Standard tablet doses |
| `g` | gram | Large dose medications |
| `mL` | milliliter | Liquid formulations |
| `L` | liter | IV fluid volumes |
| `1` | dimensionless unit | Per unit (tablets, capsules) |
| `min` | minute | Time-based dosing |
| `h` | hour | Extended release timing |
| `d` | day | Daily dosing schedules |

### Implementation Guidelines

#### CDA Parser Service Integration
```python
def extract_pharmaceutical_quantity(quantity_element):
    """Extract UCUM-compliant pharmaceutical quantities from CDA XML"""
    
    numerator = quantity_element.find('.//numerator[@xsi:type="PQ"]')
    denominator = quantity_element.find('.//denominator[@xsi:type="PQ"]')
    
    if numerator is not None and denominator is not None:
        # Validate UCUM codes
        num_unit = numerator.get('unit')
        den_unit = denominator.get('unit')
        
        if not is_valid_ucum_code(num_unit):
            logger.warning(f"Invalid UCUM code in numerator: {num_unit}")
            
        if not is_valid_ucum_code(den_unit):
            logger.warning(f"Invalid UCUM code in denominator: {den_unit}")
            
        return {
            'numerator_value': numerator.get('value'),
            'numerator_unit': num_unit,
            'denominator_value': denominator.get('value'), 
            'denominator_unit': den_unit,
            'strength_display': f"{numerator.get('value')} {num_unit}"
        }
```

#### CTS Integration
```python
def resolve_ucum_display_name(ucum_code):
    """Get human-readable display name for UCUM codes"""
    
    ucum_mappings = {
        'ug': 'microgram',
        'mg': 'milligram',
        'g': 'gram',
        'mL': 'milliliter',
        '1': 'unit'
    }
    
    return ucum_mappings.get(ucum_code, ucum_code)
```

### Testing Requirements

#### Unit Test Examples
```python
def test_ucum_quantity_extraction():
    """Test extraction of UCUM-compliant pharmaceutical quantities"""
    
    cda_xml = """
    <pharm:quantity>
        <numerator xsi:type="PQ" value="100" unit="ug" />
        <denominator xsi:type="PQ" value="1" unit="1" />
    </pharm:quantity>
    """
    
    result = extract_pharmaceutical_quantity(parse_xml(cda_xml))
    
    assert result['numerator_value'] == '100'
    assert result['numerator_unit'] == 'ug'
    assert result['denominator_value'] == '1'
    assert result['denominator_unit'] == '1'
    assert result['strength_display'] == '100 ug'

def test_invalid_ucum_code_handling():
    """Test handling of invalid UCUM codes"""
    
    cda_xml = """
    <pharm:quantity>
        <numerator xsi:type="PQ" value="100" unit="mcg" />
        <denominator xsi:type="PQ" value="1" unit="1" />
    </pharm:quantity>
    """
    
    # Should log warning for "mcg" (should be "ug")
    with pytest.warns(UserWarning):
        result = extract_pharmaceutical_quantity(parse_xml(cda_xml))
```

## 🚨 Common Pitfalls to Avoid

1. **Using local abbreviations**: "mcg" instead of "ug"
2. **Missing denominator validation**: Not checking if denominator unit makes semantic sense
3. **Hardcoded unit mappings**: Should use CTS for dynamic unit resolution
4. **No validation logging**: Should log UCUM compliance issues for audit trails
5. **Template display inconsistency**: Ensure UI shows both value and unit properly

## 🔍 Validation Tools

### UCUM Code Validator
```python
def is_valid_ucum_code(unit_code):
    """Validate if a unit code is valid UCUM"""
    
    # Basic UCUM validation - in production, use proper UCUM library
    valid_ucum_codes = {
        'ug', 'mg', 'g', 'kg',  # Mass
        'mL', 'L', 'dL',        # Volume  
        '1',                     # Dimensionless
        'min', 'h', 'd',        # Time
        '%',                     # Percentage
        'U',                     # International Unit
    }
    
    return unit_code in valid_ucum_codes
```

## 📊 Quality Metrics

- **UCUM Compliance Rate**: % of pharmaceutical quantities using valid UCUM codes
- **Validation Coverage**: % of CDA documents with validated pharmaceutical quantities  
- **Error Detection**: Number of non-UCUM codes flagged and corrected
- **Template Consistency**: % of UI displays showing proper unit formatting

---

**Note**: This checklist should be referenced during all pharmaceutical quantity processing implementations to ensure European healthcare interoperability standards compliance.