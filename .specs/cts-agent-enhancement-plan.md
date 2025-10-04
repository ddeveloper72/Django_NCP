# CTS Agent Enhancement Plan - Dual-Key Implementation

## Current Status Analysis

### ✅ What's Working
- **CTS Infrastructure**: `_lookup_valueset_term` method functional
- **Allergies Integration**: Complete CTS lookup for reaction types, agents, and manifestations
- **Code Discovery**: System successfully identifies clinical codes across all sections
- **Fallback Logic**: Graceful degradation when codes lack displayName

### 🔧 What Needs Enhancement

#### Critical Finding: CTS Agent Already Discovering Codes!
The analysis shows our CTS agent is **already finding and resolving codes** across multiple sections:

```
✅ Problem Code: Type 2 diabetes mellitus; Without complications [SNOMED CT]
✅ Medication Code: 861007 [RxNorm] 
✅ Route Code: 26643006 [SNOMED CT]
✅ Procedure Code: Appendectomy [SNOMED CT]
```

**The key insight**: We have a **single-key system** that needs to become a **dual-key system**.

## Implementation Plan

### Phase 1: Enhance CTS Agent Core (Priority 1)

#### 1.1 Add Code System OID Support
```python
# Current: Single-key lookup
def _lookup_valueset_term(self, code: str, field_label: str) -> str

# Enhanced: Dual-key lookup  
def _lookup_valueset_term_enhanced(self, code: str, code_system: str, field_label: str) -> str
```

#### 1.2 Update ValueSetConcept Model
```python
# Add code_system field to existing model
class ValueSetConcept(models.Model):
    code = models.CharField(max_length=50)
    code_system = models.CharField(max_length=100)  # NEW: OID field
    display = models.TextField()
    status = models.CharField(max_length=20)
    
    class Meta:
        unique_together = ['code', 'code_system']  # Dual-key constraint
```

#### 1.3 Code System Registry
```python
# Enhanced CDA Processor
CODE_SYSTEMS = {
    "2.16.840.1.113883.6.96": "SNOMED CT",
    "2.16.840.1.113883.6.1": "LOINC", 
    "2.16.840.1.113883.6.3": "ICD-10",
    "2.16.840.1.113883.6.88": "RxNorm",
    "2.16.840.1.113883.6.8": "UCUM"
}
```

### Phase 2: Systematic CTS Integration (Priority 2)

#### 2.1 Medical Problems Enhancement
**Target**: ICD-10 and SNOMED CT condition codes
```python
# Enhanced condition extraction with dual-key CTS
def _extract_problem_condition(self, obs_elem, namespaces):
    value_elem = obs_elem.find("hl7:value", namespaces)
    if value_elem is not None:
        condition_code = value_elem.get("code", "")
        code_system = value_elem.get("codeSystem", "")
        display_name = value_elem.get("displayName", "")
        
        data["condition_code"] = condition_code
        data["condition_system"] = code_system
        
        # Dual-key CTS lookup
        if display_name and display_name.strip():
            data["condition_display"] = display_name
        elif condition_code and code_system:
            cts_condition = self._lookup_valueset_term_enhanced(
                condition_code, code_system, "condition"
            )
            data["condition_display"] = cts_condition or f"Condition: {condition_code}"
```

#### 2.2 Medications Enhancement  
**Target**: RxNorm drug codes, SNOMED CT route codes
```python
# Enhanced medication extraction with multi-system CTS
def _extract_medication_details(self, med_elem, namespaces):
    # Drug code (RxNorm)
    drug_code = med_elem.find(".//hl7:code", namespaces)
    if drug_code is not None:
        code = drug_code.get("code", "")
        code_system = drug_code.get("codeSystem", "")
        display_name = drug_code.get("displayName", "")
        
        if not display_name and code and code_system:
            cts_drug = self._lookup_valueset_term_enhanced(
                code, code_system, "medication"
            )
            data["medication_display"] = cts_drug
    
    # Route code (SNOMED CT)
    route_code = med_elem.find(".//hl7:routeCode", namespaces)
    if route_code is not None:
        code = route_code.get("code", "")
        code_system = route_code.get("codeSystem", "")
        display_name = route_code.get("displayName", "")
        
        if not display_name and code and code_system:
            cts_route = self._lookup_valueset_term_enhanced(
                code, code_system, "route"
            )
            data["route_display"] = cts_route
```

#### 2.3 Procedures Enhancement
**Target**: SNOMED CT procedure codes
```python
# Enhanced procedure extraction with CTS
def _extract_procedure_details(self, proc_elem, namespaces):
    proc_code = proc_elem.find("hl7:code", namespaces)
    if proc_code is not None:
        code = proc_code.get("code", "")
        code_system = proc_code.get("codeSystem", "")
        display_name = proc_code.get("displayName", "")
        
        data["procedure_code"] = code
        data["procedure_system"] = code_system
        
        if display_name and display_name.strip():
            data["procedure_display"] = display_name
        elif code and code_system:
            cts_procedure = self._lookup_valueset_term_enhanced(
                code, code_system, "procedure"
            )
            data["procedure_display"] = cts_procedure or f"Procedure: {code}"
```

#### 2.4 Vital Signs Enhancement
**Target**: LOINC observation codes, UCUM unit codes
```python
# Enhanced vital signs extraction with LOINC CTS
def _extract_vital_sign_details(self, obs_elem, namespaces):
    # LOINC test code
    vital_code = obs_elem.find("hl7:code", namespaces)
    if vital_code is not None:
        code = vital_code.get("code", "")
        code_system = vital_code.get("codeSystem", "")
        display_name = vital_code.get("displayName", "")
        
        if not display_name and code and code_system:
            cts_vital = self._lookup_valueset_term_enhanced(
                code, code_system, "vital_sign"
            )
            data["vital_display"] = cts_vital
    
    # UCUM unit codes
    value_elem = obs_elem.find("hl7:value", namespaces)
    if value_elem is not None:
        unit = value_elem.get("unit", "")
        if unit:
            # UCUM units don't typically need CTS lookup but could be normalized
            data["unit_display"] = self._normalize_ucum_unit(unit)
```

### Phase 3: Template Integration (Priority 3)

#### 3.1 Update Clinical Templates
Each clinical section template needs to use the enhanced CTS-resolved display values:

```html
{# Medical Problems with CTS Integration #}
<td class="problem-name-cell">
    <strong class="text-dark">
        {% if problem.condition_display %}
            {{ problem.condition_display }}
        {% elif problem.condition_code %}
            Code: {{ problem.condition_code }}
        {% else %}
            Unknown Condition
        {% endif %}
    </strong>
    {% if problem.condition_code %}
        <br><small class="text-muted">
            Code: {{ problem.condition_code }}
            {% if problem.condition_system %}
                ({{ problem.condition_system|code_system_name }})
            {% endif %}
        </small>
    {% endif %}
</td>
```

#### 3.2 Template Filter for Code Systems
```python
# Template filter to display code system names
@register.filter
def code_system_name(oid):
    """Convert OID to readable code system name"""
    code_systems = {
        "2.16.840.1.113883.6.96": "SNOMED CT",
        "2.16.840.1.113883.6.1": "LOINC",
        "2.16.840.1.113883.6.3": "ICD-10",
        "2.16.840.1.113883.6.88": "RxNorm",
    }
    return code_systems.get(oid, oid)
```

## Implementation Timeline

### Week 1: CTS Agent Enhancement
- [ ] Enhance `_lookup_valueset_term` with dual-key support
- [ ] Add code system validation
- [ ] Update ValueSetConcept model migration
- [ ] Test dual-key lookup with existing allergies codes

### Week 2: Medical Problems Integration  
- [ ] Update problem extraction with CTS lookup
- [ ] Test with ICD-10 and SNOMED CT condition codes
- [ ] Update medical problems template
- [ ] Validate cross-patient compatibility

### Week 3: Medications Integration
- [ ] Update medication extraction with multi-system CTS
- [ ] Implement RxNorm drug code lookup
- [ ] Implement SNOMED CT route code lookup  
- [ ] Update medications template

### Week 4: Procedures & Vital Signs
- [ ] Update procedure extraction with SNOMED CT CTS
- [ ] Update vital signs extraction with LOINC CTS
- [ ] Update respective templates
- [ ] Comprehensive testing across all sections

### Week 5: Quality Assurance
- [ ] Cross-section CTS validation
- [ ] Performance optimization and caching
- [ ] Documentation updates
- [ ] European healthcare standards compliance testing

## Expected Outcomes

### For Healthcare Professionals
- **Consistent Terminology**: All clinical codes display proper medical terminology
- **Language Localization**: Terms appear in the healthcare professional's language
- **Professional Standards**: No more raw codes in clinical displays

### For System Performance
- **Cached Lookups**: Reduced database queries through intelligent caching
- **Fallback Reliability**: Graceful degradation maintains system stability
- **Scalable Architecture**: Easy addition of new code systems

### For Compliance
- **HL7 CDA Compliance**: Full adherence to international healthcare standards
- **EU Interoperability**: Seamless cross-border healthcare data exchange  
- **Quality Assurance**: Validated terminology prevents clinical misinterpretation

This comprehensive plan transforms our existing single-key CTS system into a robust dual-key international healthcare terminology service that meets European healthcare interoperability standards.