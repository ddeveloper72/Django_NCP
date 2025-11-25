# FHIR Data Quality Issue - Patrick Murphy Medications

**Patient:** Patrick Murphy  
**Country:** Ireland (IE)  
**Azure Patient ID:** `9955eb80-a5f9-4c02-aa6c-d1853c76377c`  
**Date Analyzed:** 2025-11-25  
**Issue Severity:** HIGH - Missing critical medication data

---

## Executive Summary

Patrick Murphy's medication section displays "Unknown medication" because his MedicationStatement resource in Azure FHIR is **incomplete and has broken references**.

**Root Cause:** The MedicationStatement references a Medication resource that **does not exist** (HTTP 404), and contains **no alternative medication data** (no medicationCodeableConcept, no dosage).

---

## Issue Details

### MedicationStatement Resource

**Resource ID:** `cff54d48-b70a-4b50-9258-befaa472099a`  
**Version:** 2  
**Last Updated:** 2025-11-24T12:02:40.498+00:00  
**Status:** unknown

```json
{
  "resourceType": "MedicationStatement",
  "id": "cff54d48-b70a-4b50-9258-befaa472099a",
  "meta": {
    "versionId": "2",
    "lastUpdated": "2025-11-24T12:02:40.498+00:00"
  },
  "status": "unknown",
  "medicationReference": {
    "reference": "Medication/0d445f58-e41f-4c68-9851-1b0d3e1f642b"
  },
  "subject": {
    "reference": "Patient/9955eb80-a5f9-4c02-aa6c-d1853c76377c"
  },
  "informationSource": {
    "reference": "Practitioner/755944f9-064f-417c-975f-cf055c60b75a"
  }
}
```

### Problems Identified

| Field | Status | Issue |
|-------|--------|-------|
| **medicationCodeableConcept** | ❌ MISSING | No ATC code, no display name, no text |
| **medicationReference** | ⚠️ BROKEN | Points to `Medication/0d445f58-e41f-4c68-9851-1b0d3e1f642b` which **returns 404** |
| **dosage** | ❌ MISSING | No dosage instructions, no strength, no route |
| **status** | ⚠️ INVALID | Set to "unknown" instead of valid status |
| **effectivePeriod** | ❌ MISSING | No treatment dates |

---

## FHIR Specification Compliance

### MedicationStatement Requirements (FHIR R4)

**Required Elements:**
- ✅ `status` - Present but invalid value ("unknown" not in value set)
- ✅ `medicationCodeableConcept` OR `medicationReference` - Reference present but broken

**Recommended Elements:**
- ❌ `dosage` - MISSING
- ❌ `effectivePeriod` - MISSING
- ❌ Valid `status` value - Invalid

**Valid Status Values:**
- `active` - The medication is still being taken
- `completed` - The medication is no longer being taken
- `entered-in-error` - The statement was recorded incorrectly
- `intended` - The medication may be taken at some time in the future
- `stopped` - Actions implied by the statement have been permanently halted
- `on-hold` - Actions implied by the statement have been temporarily halted
- ❌ `unknown` - **NOT A VALID STATUS**

---

## Impact on Django NCP Display

### Current Display (Screenshot Evidence)

```
Medications: 1 items found

Unknown medication                                    [Unknown]

🔬 ACTIVE INGREDIENTS [STRENGTH]        💊 PHARMACEUTICAL FORM
Not specified                            Not specified

💪 STRENGTH                              💉 ROUTE OF ADMINISTRATION
Not specified                            Not available in source document

⏰ SCHEDULE                              🏥 MEDICAL INDICATION
Not available in source document         Not available in source document

📅 TREATMENT PERIOD                      💊 DOSE QUANTITY
Not available in source document         Not available in source document
```

### Why This Happens

**Parser Logic:** `fhir_bundle_parser.py` line 944-956

```python
# PRIORITY 1: Check for medicationReference
if medication.get('medicationReference', {}).get('reference'):
    med_ref = medication['medicationReference']['reference']
    med_id = med_ref.split('/')[-1]
    
    # Get referenced Medication resource from bundle
    if med_id in self.medication_resources:
        referenced_medication = self.medication_resources[med_id]
        # ❌ PROBLEM: med_id NOT in bundle because Medication resource doesn't exist!
```

**Fallback Chain:**
1. ❌ Try medicationReference → 404 error
2. ❌ Try medicationCodeableConcept → doesn't exist
3. ❌ Try medicationCodeableConcept.text → doesn't exist
4. ❌ Try medicationReference.display → doesn't exist
5. ✅ Use default: "Unknown medication"

---

## Required Fixes (For FHIR Team)

### Option 1: Add medicationCodeableConcept (RECOMMENDED)

Add medication data directly to MedicationStatement:

```json
{
  "resourceType": "MedicationStatement",
  "id": "cff54d48-b70a-4b50-9258-befaa472099a",
  "status": "active",
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.whocc.no/atc",
        "code": "C09AA02",
        "display": "Enalapril"
      }
    ],
    "text": "Enalapril 10 mg"
  },
  "subject": {
    "reference": "Patient/9955eb80-a5f9-4c02-aa6c-d1853c76377c"
  },
  "dosage": [
    {
      "text": "10 mg once daily",
      "route": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "26643006",
            "display": "Oral route"
          }
        ]
      },
      "doseAndRate": [
        {
          "doseQuantity": {
            "value": 10,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg"
          }
        }
      ]
    }
  ]
}
```

### Option 2: Create Valid Medication Resource

Create the missing `Medication/0d445f58-e41f-4c68-9851-1b0d3e1f642b` resource:

```json
{
  "resourceType": "Medication",
  "id": "0d445f58-e41f-4c68-9851-1b0d3e1f642b",
  "code": {
    "coding": [
      {
        "system": "http://www.whocc.no/atc",
        "code": "C09AA02",
        "display": "Enalapril"
      }
    ],
    "text": "Enalapril 10 mg"
  },
  "form": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "385055001",
        "display": "Tablet"
      }
    ]
  },
  "ingredient": [
    {
      "itemCodeableConcept": {
        "coding": [
          {
            "system": "http://www.whocc.no/atc",
            "code": "C09AA02",
            "display": "Enalapril"
          }
        ]
      },
      "strength": {
        "numerator": {
          "value": 10,
          "unit": "mg",
          "system": "http://unitsofmeasure.org",
          "code": "mg"
        },
        "denominator": {
          "value": 1,
          "unit": "tablet",
          "system": "http://unitsofmeasure.org",
          "code": "1"
        }
      }
    }
  ]
}
```

### Option 3: Fix Status Value

At minimum, fix the invalid status:

```json
{
  "status": "active"  // Change from "unknown" to valid value
}
```

---

## Validation Checklist

### Minimum Requirements for Valid MedicationStatement

- [ ] **status** - Must be one of: active, completed, entered-in-error, intended, stopped, on-hold
- [ ] **medication** - EITHER:
  - [ ] `medicationCodeableConcept` with valid coding (ATC code preferred)
  - [ ] `medicationReference` that points to existing Medication resource
- [ ] **dosage** - At least one dosage with:
  - [ ] `text` (human-readable dosage instruction)
  - [ ] OR `doseAndRate` with structured dose

### Recommended Elements

- [ ] `effectivePeriod` or `effectiveDateTime` - When medication was/is taken
- [ ] `dosage.route` - Route of administration
- [ ] `dosage.timing` - Frequency and timing
- [ ] `reasonCode` or `reasonReference` - Medical indication

---

## Testing After Fix

### Expected Result in Django NCP

After fixing the MedicationStatement, the UI should display:

```
Medications: 1 items found

Enalapril                                             [Active]

🔬 ACTIVE INGREDIENTS [STRENGTH]        💊 PHARMACEUTICAL FORM
Enalapril 10 mg                          Tablet

💪 STRENGTH                              💉 ROUTE OF ADMINISTRATION
10 mg                                    Oral

⏰ SCHEDULE                              🏥 MEDICAL INDICATION
Once daily                               [Condition if specified]

📅 TREATMENT PERIOD                      💊 DOSE QUANTITY
[Start date] - [End date]                10 mg
```

### Verification Steps

1. Update MedicationStatement in Azure FHIR (use Option 1 or 2)
2. Clear Django cache: `python clear_diana_fhir_cache.py` (modify for Patrick)
3. Navigate to Patrick Murphy's patient page
4. Verify medication displays with proper name and details
5. Check all medication fields populate correctly

---

## Related Patients

### Diana Ferreira (Portugal)

**Status:** ✅ WORKING CORRECTLY

Diana's medications display properly because her MedicationStatement resources have:
- ✅ Valid `medicationCodeableConcept` with ATC codes
- ✅ Complete `dosage` information
- ✅ Valid `status` values

**Example:** Diana's medication shows proper ATC codes, CTS-resolved names, and complete dosage details.

---

## Technical Notes

### Azure FHIR Resource Existence Check

Query to verify Medication resource exists:

```http
GET https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Medication/0d445f58-e41f-4c68-9851-1b0d3e1f642b
Authorization: Bearer {token}
```

**Current Response:** HTTP 404 Not Found

### Django Parser Behavior

The parser attempts to gracefully handle missing data by:
1. Checking multiple fallback fields (reference → codeable → text)
2. Using "Unknown medication" when all lookups fail
3. Setting all optional fields to "Not specified" or "Not available"
4. Still displaying the medication section (count: 1 item found)

This prevents errors but results in non-informative UI.

---

## Recommendations

### Priority 1: Fix Patrick Murphy's Data

Use **Option 1** (add medicationCodeableConcept) because:
- ✅ Self-contained (no dependent resources)
- ✅ Simpler to implement
- ✅ Consistent with Diana Ferreira's working medications
- ✅ Supports CTS agent lookup via ATC codes

### Priority 2: Add Validation

Implement FHIR validation to catch issues before upload:
- Validate MedicationStatement.status against value set
- Verify referenced Medication resources exist before creating references
- Require either medicationCodeableConcept OR valid medicationReference
- Recommend including dosage information

### Priority 3: Audit Other Patients

Check if other patients have similar issues:
- Search for MedicationStatements with status="unknown"
- Validate all medicationReference references resolve (no 404s)
- Check for empty MedicationStatements (no dosage, no medication data)

---

## Contact Information

**For FHIR data fixes:**
- Django_NCP Repository: https://github.com/ddeveloper72/Django_NCP
- FHIR Parser: `patient_data/services/fhir_bundle_parser.py`
- Azure FHIR Service: `healtthdata-dev-fhir-service`

**Debug Scripts:**
- `debug_patrick_medications.py` - Analyze Patrick's medications
- `list_azure_patients.py` - List all patients in Azure FHIR

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-25  
**Status:** FHIR Team Action Required
