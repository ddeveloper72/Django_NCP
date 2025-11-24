# CDA-to-FHIR Converter Requirements - Condition Resource Validation

## Overview
The CDA-to-FHIR converter is creating invalid Condition resources that need validation before conversion.

---

## Problem 1: Metadata Codes as Clinical Conditions ❌

### Current Behavior
```json
{
  "resourceType": "Condition",
  "id": "39f63e41-9d46-47fc-ae1c-df3a627f02b7",
  "code": {
    "coding": [{
      "system": "urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5",
      "code": "199",
      "display": "Diagnosis Assertion Status"
    }]
  }
}
```

### Issue
Code `199` is an **administrative/workflow code**, not a clinical diagnosis.

### Required Fix
**DO NOT create Condition resources for these code systems:**
```
urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5
http://terminology.hl7.org/CodeSystem/v3-ActCode
http://terminology.hl7.org/CodeSystem/condition-clinical
http://terminology.hl7.org/CodeSystem/condition-ver-status
http://terminology.hl7.org/CodeSystem/condition-category
```

**Instead**, use metadata codes in:
- `Condition.category` (e.g., problem-list-item, encounter-diagnosis)
- `Condition.verificationStatus` (confirmed, unconfirmed, refuted)
- `Condition.clinicalStatus` (active, inactive, resolved)

---

## Problem 2: Malformed Condition with Empty OID ❌

### Current Behavior
```json
{
  "resourceType": "Condition",
  "id": "f931f42b-5bd3-4945-91c7-606d29de639d",
  "code": {
    "coding": [{
      "system": "urn:oid:"  // ❌ INVALID: Empty OID
      // ❌ MISSING: No code
      // ❌ MISSING: No display
    }]
  }
}
```

### Issue
The coding object has:
- Empty/invalid code system: `"urn:oid:"` (must be `urn:oid:X.X.X.X`)
- Missing code (required)
- Missing display (recommended)

### Required Fix
**Validate ALL Condition.code.coding elements:**
1. ✅ `system`: Must be non-empty and valid (not `"urn:oid:"`)
2. ✅ `code`: Must be present and non-empty
3. ⚠️ `display`: Should be present (log warning if missing)

**Skip invalid source CDA entries** rather than creating malformed FHIR resources.

---

## Implementation Pseudocode

```python
def should_create_condition_resource(diagnosis_element):
    """Validate before creating FHIR Condition resource"""
    
    code_system = extract_code_system(diagnosis_element)
    code = extract_code(diagnosis_element)
    display = extract_display_name(diagnosis_element)
    
    # 1. Check for metadata/administrative code systems
    METADATA_SYSTEMS = [
        'urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5',
        'http://terminology.hl7.org/CodeSystem/v3-ActCode',
        'http://terminology.hl7.org/CodeSystem/condition-clinical',
        'http://terminology.hl7.org/CodeSystem/condition-ver-status',
        'http://terminology.hl7.org/CodeSystem/condition-category'
    ]
    
    if code_system in METADATA_SYSTEMS:
        log.info(f"Skipping metadata code {code} - use in Condition.category/status")
        return False
    
    # 2. Validate code system is valid
    if not code_system or code_system == 'urn:oid:':
        log.warning(f"Skipping invalid code system: '{code_system}'")
        return False
    
    # 3. Validate code is present
    if not code or code.strip() == '':
        log.warning(f"Skipping diagnosis with missing code")
        return False
    
    # 4. Warn if display name missing (but continue)
    if not display:
        log.warning(f"Code {code} has no display name")
    
    return True
```

---

## Test Case: Patient Diana Ferreira (ID: 2-1234-W7)

### Current State
7 Condition resources in Azure FHIR

### Expected State After Fix
5 Condition resources

### Conditions to REMOVE (invalid):
1. ❌ `39f63e41-9d46-47fc-ae1c-df3a627f02b7` - "Diagnosis Assertion Status" (metadata)
2. ❌ `f931f42b-5bd3-4945-91c7-606d29de639d` - "Unknown code" (malformed)

### Conditions to KEEP (valid):
1. ✅ N10: Acute tubulo-interstitial nephritis
2. ✅ O14: Pre-eclampsia
3. ✅ I49: Other cardiac arrhythmias
4. ✅ E89: Postprocedural endocrine disorders
5. ✅ J45: Asthma

---

## Validation Checklist

After implementing fixes:

- [ ] Delete existing invalid Condition resources from Azure FHIR
- [ ] Re-run CDA-to-FHIR conversion for patient 2-1234-W7
- [ ] Verify only 5 Condition resources created (down from 7)
- [ ] Verify no metadata code systems in Condition.code
- [ ] Verify all Condition resources have valid code systems (not `"urn:oid:"`)
- [ ] Verify all Condition resources have non-empty codes

---

## Expected Logs

```
INFO: Skipping metadata code 199 - use in Condition.category/status
WARNING: Skipping invalid code system: 'urn:oid:'
```

---

**References**
- FHIR R4 Condition: https://hl7.org/fhir/R4/condition.html
- FHIR Coding: https://hl7.org/fhir/R4/datatypes.html#Coding
