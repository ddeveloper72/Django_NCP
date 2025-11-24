# FHIR Condition Validation Requirements for CDA-to-FHIR Converter

## Issue Summary

The CDA-to-FHIR converter is creating **invalid Condition resources** that must be fixed at the source. The Django NCP application has implemented defensive filtering to handle these issues, but proper FHIR data should not require such filtering.

## Problem Conditions Identified

### 1. Metadata Codes Appearing as Clinical Conditions ❌
**Condition ID**: `39f63e41-9d46-47fc-ae1c-df3a627f02b7`

**Current Behavior**:
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
  },
  "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
  "subject": {"reference": "Patient/dbca9120-c667-41c1-82bc-7f06d3cc709d"}
}
```

**Problem**: Code `199` from system `urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5` is an **administrative assertion status code**, not a clinical diagnosis.

**Correct Behavior**:
- **DO NOT** create standalone Condition resources for metadata/workflow codes
- Metadata codes should be used in:
  - `Condition.category` (e.g., problem-list-item, encounter-diagnosis)
  - `Condition.verificationStatus` (confirmed, unconfirmed, refuted)
  - `Condition.clinicalStatus` (active, inactive, resolved)

**Code Systems to Exclude from Condition.code**:
```
urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5  # Diagnosis Assertion Status
http://terminology.hl7.org/CodeSystem/v3-ActCode  # HL7 Act codes
http://terminology.hl7.org/CodeSystem/condition-clinical  # Clinical status
http://terminology.hl7.org/CodeSystem/condition-ver-status  # Verification status
http://terminology.hl7.org/CodeSystem/condition-category  # Condition categories
```

---

### 2. Malformed Condition with Empty OID ❌
**Condition ID**: `f931f42b-5bd3-4945-91c7-606d29de639d`

**Current Behavior**:
```json
{
  "resourceType": "Condition",
  "id": "f931f42b-5bd3-4945-91c7-606d29de639d",
  "meta": {"versionId": "1", "lastUpdated": "2025-11-24T12:06:17.048+00:00"},
  "code": {
    "coding": [{
      "system": "urn:oid:"  // ❌ INVALID: Empty OID
      // ❌ MISSING: No code
      // ❌ MISSING: No display
    }]
  },
  "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
  "subject": {"reference": "Patient/dbca9120-c667-41c1-82bc-7f06d3cc709d"},
  "onsetDateTime": "2013-01-09"
}
```

**Problem**: The coding object contains invalid/incomplete data:
- `system`: `"urn:oid:"` (empty OID - must be `urn:oid:X.X.X.X`)
- `code`: Missing (required)
- `display`: Missing (recommended)

**Correct Behavior**:
- **Validate all Condition.code.coding elements before creating resources**:
  ```python
  # Required validation checks:
  1. system: Must be non-empty and valid (not "urn:oid:")
  2. code: Must be present and non-empty
  3. display: Should be present (warning if missing)
  ```
- **Skip invalid source CDA entries** rather than creating malformed FHIR resources
- **Log validation failures** for debugging:
  ```
  WARNING: Skipping invalid CDA diagnosis - empty code system (source line X)
  ```

---

### 3. Valid Clinical Conditions ✅
**These should continue to be created** (examples from Diana Ferreira's data):

```json
{
  "resourceType": "Condition",
  "code": {
    "coding": [{
      "system": "urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.2",  // Portuguese IPS ICD-10
      "code": "N10",
      "display": "Acute tubulo-interstitial nephritis"
    }]
  }
}

{
  "resourceType": "Condition",
  "code": {
    "coding": [{
      "system": "urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.2",
      "code": "O14",
      "display": "Pre-eclampsia"
    }]
  }
}

{
  "resourceType": "Condition",
  "code": {
    "coding": [{
      "system": "urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.2",
      "code": "I49",
      "display": "Other cardiac arrhythmias"
    }]
  }
}
```

---

## Validation Requirements for CDA-to-FHIR Converter

### Pre-Conversion Validation

```python
def validate_diagnosis_for_condition_resource(diagnosis_element):
    """
    Validate CDA diagnosis element before creating FHIR Condition resource
    
    Returns: (is_valid: bool, skip_reason: str)
    """
    code_system = extract_code_system(diagnosis_element)
    code = extract_code(diagnosis_element)
    display = extract_display_name(diagnosis_element)
    
    # 1. Check for metadata/administrative code systems
    METADATA_SYSTEMS = [
        'urn:oid:1.3.6.1.4.1.12559.11.10.1.3.1.44.5',  # Assertion status
        'http://terminology.hl7.org/CodeSystem/v3-ActCode',
        'http://terminology.hl7.org/CodeSystem/condition-clinical',
        'http://terminology.hl7.org/CodeSystem/condition-ver-status',
        'http://terminology.hl7.org/CodeSystem/condition-category'
    ]
    
    if code_system in METADATA_SYSTEMS:
        return False, f"Metadata code system {code_system} - use in Condition.category/status instead"
    
    # 2. Validate code system is valid OID or URL
    if not code_system or code_system == 'urn:oid:':
        return False, f"Invalid code system: '{code_system}'"
    
    # 3. Validate code is present
    if not code or code.strip() == '':
        return False, "Missing diagnosis code"
    
    # 4. Warn if display name missing (but don't skip)
    if not display:
        logger.warning(f"Diagnosis code {code} from {code_system} has no display name")
    
    return True, ""


def convert_cda_diagnosis_to_fhir_condition(diagnosis_element):
    """Convert CDA diagnosis to FHIR Condition resource with validation"""
    
    # Validate before conversion
    is_valid, skip_reason = validate_diagnosis_for_condition_resource(diagnosis_element)
    
    if not is_valid:
        logger.info(f"Skipping diagnosis: {skip_reason}")
        return None  # Don't create Condition resource
    
    # Proceed with normal conversion...
    condition = create_fhir_condition(diagnosis_element)
    return condition
```

---

## Impact Assessment

### Patient: Diana Ferreira (ID: 2-1234-W7)
**Current State**: 7 Condition resources in Azure FHIR
**Expected State**: 5 Condition resources (after fixing at source)

**Conditions to Remove**:
1. `39f63e41-9d46-47fc-ae1c-df3a627f02b7` - "Diagnosis Assertion Status" (metadata)
2. `f931f42b-5bd3-4945-91c7-606d29de639d` - "Unknown code" (malformed)

**Conditions to Keep**:
1. `4abb6023-7737-4921-b3de-2772b59dfba6` - N10: Acute tubulo-interstitial nephritis ✅
2. `69c9ba0d-d6f4-449d-8455-ec7e5e260425` - O14: Pre-eclampsia ✅
3. `06024ade-c27a-45ce-89d5-189f32635507` - I49: Other cardiac arrhythmias ✅
4. `fe4dc709-68e1-42b8-9adb-8fed31414f6a` - E89: Postprocedural endocrine disorders ✅
5. `95c622ef-3d54-40ca-a1e8-7db10da470cc` - J45: Asthma ✅

---

## Testing Checklist

After implementing validation in the CDA-to-FHIR converter:

- [ ] Delete existing malformed Condition resources from Azure FHIR:
  ```
  DELETE /Condition/39f63e41-9d46-47fc-ae1c-df3a627f02b7
  DELETE /Condition/f931f42b-5bd3-4945-91c7-606d29de639d
  ```

- [ ] Re-run CDA-to-FHIR conversion for patient 2-1234-W7

- [ ] Verify only 5 Condition resources created:
  ```
  GET /Condition?patient=dbca9120-c667-41c1-82bc-7f06d3cc709d
  ```
  Expected count: 5 (down from 7)

- [ ] Verify no metadata codes appear in Condition.code:
  ```python
  for condition in conditions:
      assert condition['code']['coding'][0]['system'] not in METADATA_SYSTEMS
  ```

- [ ] Verify all Condition resources have valid code systems:
  ```python
  for condition in conditions:
      system = condition['code']['coding'][0]['system']
      assert system and system != 'urn:oid:'
      code = condition['code']['coding'][0]['code']
      assert code and code.strip() != ''
  ```

- [ ] Django NCP filter logs should show NO filtering:
  ```
  # Should NOT appear in logs:
  [CONDITION FILTER] Skipping malformed condition: ...
  ```

- [ ] Django NCP UI should display 5 conditions for Diana Ferreira

---

## Django NCP Defensive Implementation

**Status**: ✅ Implemented as defense-in-depth

The Django NCP application has implemented filtering in `patient_data/services/fhir_bundle_parser.py` (lines 1393-1407) to handle these issues defensively. However, this is a **safety net** - proper FHIR data should not trigger these filters.

**Monitoring**: Filter logs indicate data quality issues that should be resolved at the source:
```
INFO [CONDITION FILTER] Skipping malformed condition: ID=..., code='...', system='...', name='...'
```

If these logs appear, it indicates the CDA-to-FHIR converter needs fixes as documented above.

---

## References

- **FHIR R4 Condition Resource**: https://hl7.org/fhir/R4/condition.html
- **FHIR Coding Data Type**: https://hl7.org/fhir/R4/datatypes.html#Coding
- **OID Registry**: http://oid-info.com/
- **HL7 Terminology**: http://terminology.hl7.org/

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-24  
**Author**: Django NCP Development Team  
**Target**: CDA-to-FHIR Converter Development Team
