# Azure FHIR Pregnancy Observations Analysis Summary

**Date**: November 17, 2025  
**Patient**: Diana Ferreira (2-1234-W7)  
**Source**: Azure FHIR API (healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com)

---

## Current Azure FHIR Structure

### Observations Found: 4 pregnancy-related observations

#### 1. Past Delivery (LOINC 93857-1 - NON-IPS)
```
ID: f4d3d8b6-5619-4afb-acd2-cd4c985a6f31
Code: LOINC 93857-1 "Date and time of obstetric delivery" ⚠️ NON-IPS
Value: valueCodeableConcept
  - SNOMED 281050002 "Livebirth"
effectiveDateTime: 2021-09-08
```

**Issue**: Uses non-IPS LOINC code 93857-1 with outcome in `valueCodeableConcept` instead of IPS pattern

#### 2. Current Pregnancy Status (LOINC 82810-3 - IPS✅)
```
ID: d52c7e2f-cf85-422b-8cfb-1d9d550fe64e
Code: LOINC 82810-3 "Pregnancy status" ✅ IPS
Value: valueCodeableConcept
  - SNOMED 77386006 "Pregnant"
effectiveDateTime: 2022-06-15
```

**Compliant**: Follows IPS Pregnancy Status profile correctly

#### 3. Termination Outcome (SNOMED 57797005)
```
ID: 2e66bd08-fe2d-40d8-8ca9-69eb737b6ab1
Code: SNOMED 57797005 "Termination of pregnancy"
Value: valueQuantity: 1.0
effectiveDateTime: 2022-06-08T10:49:00Z
```

**Issue**: Uses SNOMED as observation code instead of LOINC 11613-7 (Abortions.induced)

#### 4. Livebirth Outcome (SNOMED 281050002)
```
ID: 1b800d37-00d1-466d-8430-82456b7e749a
Code: SNOMED 281050002 "Livebirth"
Value: valueQuantity: 2.0
effectiveDateTime: 2022-06-08T10:49:00Z
```

**Issue**: Uses SNOMED as observation code instead of LOINC 11636-8 ([#] Births.live)

---

## Parser Test Results

### Current Parser Output
```
Total Pregnancy Records: 3

1. PAST PREGNANCY
   Delivery Date: 2022-06-08
   Outcome: Livebirth
   Observation Date: 2022-06-08

2. PAST PREGNANCY
   Delivery Date: 2021-09-08 00:00
   Outcome: Livebirth
   Observation Date: 2021-09-08

3. CURRENT PREGNANCY
   Status: Pregnant
   Observation Date: 2022-06-15 00:00
```

### Parser Behavior Analysis

✅ **Working Correctly:**
- Detects LOINC 82810-3 (Pregnancy Status) as current pregnancy
- Extracts "Pregnant" status from valueCodeableConcept
- Groups observations by delivery date
- Separates current vs past pregnancies

⚠️ **Inconsistencies:**
- Observation #3 (Termination, 2022-06-08) grouped with #4 (Livebirth, 2022-06-08) - same effectiveDateTime
- This creates ambiguous pregnancy record: both show "Livebirth" outcome
- SNOMED code observations (#3, #4) processed separately from LOINC 93857-1 (#1)

---

## IPS Compliance Gap Analysis

### Current vs IPS Standard

| Current Azure | IPS Requirement | Compliance |
|--------------|----------------|------------|
| LOINC 93857-1 with valueCodeableConcept | LOINC 11636-8 with valueQuantity | ❌ Non-compliant |
| SNOMED 281050002 as code | LOINC 11636-8 as code, count in valueQuantity | ❌ Non-compliant |
| SNOMED 57797005 as code | LOINC 11613-7 as code, count in valueQuantity | ❌ Non-compliant |
| LOINC 82810-3 with valueCodeableConcept | ✅ Correct | ✅ Compliant |
| effectiveDateTime for dates | effectiveDateTime for dates | ✅ Compliant |

### Missing IPS Elements

1. **No hasMember relationships**: Current pregnancy (82810-3) should link to EDD observation via hasMember
2. **No EDD observation**: Expected LOINC 11778-8 observation with valueDateTime
3. **Individual delivery dates**: IPS expects summary counts, not individual dates for past pregnancies
4. **Wrong code systems**: Using SNOMED as observation codes instead of LOINC

---

## Recommendations for CDA-to-FHIR Converter

### Priority 1: Fix Observation Codes

**Current:**
```json
{
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "93857-1",
      "display": "Date and time of obstetric delivery"
    }]
  },
  "valueCodeableConcept": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "281050002",
      "display": "Livebirth"
    }]
  },
  "effectiveDateTime": "2021-09-08"
}
```

**IPS Standard:**
```json
{
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11636-8",
      "display": "[#] Births.live"
    }]
  },
  "valueQuantity": {
    "value": 1,
    "unit": "1",
    "system": "http://unitsofmeasure.org",
    "code": "1"
  },
  "effectiveDateTime": "2021-09-08"
}
```

### Priority 2: Add EDD Observation

**Create for current pregnancy:**
```json
{
  "resourceType": "Observation",
  "id": "pregnancy-edd-2023-02-14",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11778-8",
      "display": "Delivery date Estimated"
    }]
  },
  "valueDateTime": "2023-02-14",
  "effectiveDateTime": "2022-06-15"
}
```

**Link from pregnancy status:**
```json
{
  "resourceType": "Observation",
  "id": "d52c7e2f-cf85-422b-8cfb-1d9d550fe64e",
  "code": {"coding": [{"code": "82810-3"}]},
  "hasMember": [
    {"reference": "Observation/pregnancy-edd-2023-02-14"}
  ]
}
```

### Priority 3: Map CDA Pregnancy Section Correctly

**CDA Pregnancy Outcome Codes → IPS LOINC Codes:**
```
SNOMED 281050002 (Livebirth) → LOINC 11636-8 ([#] Births.live)
SNOMED 57797005 (Termination) → LOINC 11613-7 ([#] Abortions.induced)
SNOMED 237364002 (Stillbirth) → LOINC 11638-4 ([#] Births.still living)
SNOMED 17369002 (Miscarriage) → LOINC 11614-5 ([#] Abortions.spontaneous)
```

**Use effectiveDateTime for delivery dates, valueQuantity for counts**

---

## Django Parser Updates Required

### 1. Update Pregnancy Detection

**Current:**
```python
def _is_pregnancy_related(self, observation: Dict[str, Any]) -> bool:
    # Checks observation name keywords
    pregnancy_keywords = ['pregnancy', 'gravida', 'para', 'pregnant', ...]
```

**Add IPS LOINC codes:**
```python
def _is_pregnancy_related(self, observation: Dict[str, Any]) -> bool:
    # Check LOINC codes first
    code_data = observation.get('code_data', {})
    for coding in code_data.get('coding', []):
        if coding.get('system') == 'http://loinc.org':
            loinc_code = coding.get('code', '')
            if loinc_code in ['82810-3', '11778-8', '11779-6', '11780-4',
                             '11636-8', '11637-6', '11638-4', '11639-2', '11640-0',
                             '11612-9', '11613-7', '11614-5', '33065-4']:
                return True
    
    # Fallback to keyword matching
    # ...
```

### 2. Handle hasMember Relationships

```python
def _extract_current_pregnancy_with_edd(self, observations: List[Dict]) -> Dict:
    """Extract current pregnancy with linked EDD observation"""
    
    # Find pregnancy status observation (82810-3)
    pregnancy_status = next((obs for obs in observations 
                            if self._is_pregnancy_status(obs)), None)
    
    if not pregnancy_status:
        return {}
    
    # Extract linked EDD observation via hasMember
    edd_obs = None
    for member_ref in pregnancy_status.get('hasMember', []):
        ref_id = member_ref.get('reference', '').split('/')[-1]
        edd_obs = next((obs for obs in observations if obs.get('id') == ref_id), None)
        if edd_obs:
            break
    
    return {
        'status': pregnancy_status,
        'edd': edd_obs
    }
```

### 3. Parse valueQuantity for Outcome Counts

```python
def _extract_outcome_count(self, observation: Dict[str, Any]) -> int:
    """Extract count from valueQuantity"""
    value_data = observation.get('value_data', {})
    
    if isinstance(value_data, dict) and 'value' in value_data:
        try:
            return int(value_data['value'])
        except (ValueError, TypeError):
            return 1  # Default to 1 if can't parse
    
    return 1
```

---

## Testing Recommendations

### 1. Unit Tests for IPS Code Detection
```python
def test_ips_pregnancy_status_detection():
    obs = {
        'code_data': {
            'coding': [{
                'system': 'http://loinc.org',
                'code': '82810-3'
            }]
        }
    }
    assert parser._is_pregnancy_related(obs) == True

def test_ips_birth_outcome_detection():
    obs = {
        'code_data': {
            'coding': [{
                'system': 'http://loinc.org',
                'code': '11636-8'
            }]
        }
    }
    assert parser._is_pregnancy_related(obs) == True
```

### 2. Integration Tests with Azure FHIR
```python
def test_azure_pregnancy_pipeline():
    """Test complete pipeline from Azure to UI"""
    # 1. Fetch from Azure
    bundle = fhir_service.get_patient_summary('2-1234-W7', 'test')
    
    # 2. Parse with parser
    sections = parser.parse_patient_summary_bundle(bundle)
    
    # 3. Verify pregnancy records
    pregnancy_history = sections['clinical_arrays']['pregnancy_history']
    assert len(pregnancy_history) >= 3
    
    # 4. Verify current pregnancy has EDD if available
    current = [p for p in pregnancy_history if p.get('pregnancy_type') == 'current']
    if current:
        assert current[0].get('data', {}).get('delivery_date_estimated')
```

---

## Next Steps

1. ✅ **Analysis Complete**: Azure FHIR structure documented
2. ✅ **Parser Testing**: Verified current parser behavior
3. ✅ **IPS Specification**: Created comprehensive spec document
4. 🔄 **CDA Converter Update**: Update to generate IPS-compliant observations
5. 🔄 **Parser Enhancement**: Add IPS code detection and hasMember handling
6. 🔄 **UI Verification**: Test rendering with new structure
7. 🔄 **Azure Upload**: Upload new IPS-compliant observations

**Reference Documents:**
- `.specs/fhir-ips-pregnancy-observations-specification.md` - Full IPS implementation guide
- This document - Current state analysis and recommendations
