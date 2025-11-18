# FHIR IPS Pregnancy Observations Specification

**Version**: 1.0  
**Date**: November 17, 2025  
**Standard**: HL7 FHIR R4 International Patient Summary (IPS) v2.0.0  
**Purpose**: Define proper FHIR observation structure for pregnancy history in Django_NCP application

---

## Executive Summary

The HL7 FHIR IPS defines **THREE distinct observation profiles** for pregnancy data, each serving a specific purpose. Current implementation treats pregnancy as individual disconnected observations. This specification defines the proper structure using `hasMember` relationships to group related observations.

---

## 1. FHIR IPS Pregnancy Observation Profiles

### 1.1 Observation: Pregnancy Status (Current Pregnancy)

**Profile**: `http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-status-uv-ips`

**Purpose**: Represents **CURRENT** pregnancy status

**Structure**:
```json
{
  "resourceType": "Observation",
  "id": "pregnancy-status-current",
  "meta": {
    "profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-status-uv-ips"]
  },
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "82810-3",
      "display": "Pregnancy status"
    }]
  },
  "subject": {
    "reference": "Patient/2-1234-W7"
  },
  "effectiveDateTime": "2022-06-15",
  "valueCodeableConcept": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "77386006",
      "display": "Pregnant"
    }]
  },
  "hasMember": [
    {
      "reference": "Observation/pregnancy-edd-2023-02-14"
    }
  ]
}
```

**Key Elements**:
- **Code**: LOINC `82810-3` (Pregnancy status) - REQUIRED
- **Value**: SNOMED CT from pregnancy status ValueSet:
  - `77386006` - Pregnant
  - `60001007` - Not pregnant
  - `152231000119106` - Pregnancy not yet confirmed
  - `146799005` - Possible pregnancy
- **hasMember**: References Observation-pregnancy-edd (Expected Delivery Date)
- **effectiveDateTime**: Date of observation (when status determined)

---

### 1.2 Observation: Expected Delivery Date (EDD)

**Profile**: `http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-edd-uv-ips`

**Purpose**: Represents estimated delivery date for **CURRENT** pregnancy

**Structure**:
```json
{
  "resourceType": "Observation",
  "id": "pregnancy-edd-2023-02-14",
  "meta": {
    "profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-edd-uv-ips"]
  },
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11778-8",
      "display": "Delivery date Estimated"
    }]
  },
  "subject": {
    "reference": "Patient/2-1234-W7"
  },
  "effectiveDateTime": "2022-06-15",
  "valueDateTime": "2023-02-14"
}
```

**Key Elements**:
- **Code**: LOINC from EDD Method ValueSet (REQUIRED):
  - `11778-8` - Delivery date Estimated
  - `11779-6` - Delivery date Estimated from last menstrual period
  - `11780-4` - Delivery date Estimated from ovulation date
- **Value**: `valueDateTime` with estimated delivery date
- **effectiveDateTime**: Date when EDD was determined

**Relationship**: Referenced by Pregnancy Status via `hasMember`

---

### 1.3 Observation: Pregnancy Outcome (Past Pregnancies)

**Profile**: `http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-outcome-uv-ips`

**Purpose**: Represents **summarized history** of past pregnancy outcomes

**Structure**:
```json
{
  "resourceType": "Observation",
  "id": "pregnancy-outcome-livebirth-2021",
  "meta": {
    "profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Observation-pregnancy-outcome-uv-ips"]
  },
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11636-8",
      "display": "[#] Births.live"
    }]
  },
  "subject": {
    "reference": "Patient/2-1234-W7"
  },
  "effectiveDateTime": "2021-09-08",
  "valueQuantity": {
    "value": 1,
    "unit": "1",
    "system": "http://unitsofmeasure.org",
    "code": "1"
  }
}
```

**Key Elements**:
- **Code**: LOINC from Pregnancy Outcome ValueSet (REQUIRED):
  - `11636-8` - [#] Births.live
  - `11637-6` - [#] Births.preterm
  - `11638-4` - [#] Births.still living
  - `11639-2` - [#] Births.term
  - `11640-0` - [#] Births total
  - `11612-9` - [#] Abortions
  - `11613-7` - [#] Abortions.induced
  - `11614-5` - [#] Abortions.spontaneous
  - `33065-4` - [#] Ectopic pregnancy
- **Value**: `valueQuantity` with count of outcomes
- **effectiveDateTime**: **Date of delivery/outcome event**

---

## 2. Proper Observation Grouping Strategy

### 2.1 Current Pregnancy Structure

```
Observation: Pregnancy Status (82810-3)
├── value: Pregnant (SNOMED 77386006)
├── effectiveDateTime: 2022-06-15
└── hasMember
    └── Observation: EDD (11778-8)
        ├── valueDateTime: 2023-02-14
        └── effectiveDateTime: 2022-06-15
```

### 2.2 Past Pregnancy Structure (Per Event)

**Option A: Single Observation Per Outcome**
```
Observation: Live Birth (11636-8)
├── valueQuantity: 1
└── effectiveDateTime: 2021-09-08 (DELIVERY DATE)
```

**Option B: Grouped Outcomes (Recommended for Multiple Births)**
```
Observation: Total Births (11640-0)
├── valueQuantity: 2
├── effectiveDateTime: 2021-09-08
└── component
    ├── Live Births (11636-8): 2
    ├── Term Births (11639-2): 2
    └── Preterm Births (11637-6): 0
```

---

## 3. Implementation Requirements for CDA-to-FHIR Converter

### 3.1 Current Pregnancy Conversion

**CDA Source**:
```xml
<observation classCode="OBS" moodCode="EVN">
  <code code="82810-3" codeSystem="2.16.840.1.113883.6.1" displayName="Pregnancy status"/>
  <value xsi:type="CD" code="77386006" codeSystem="2.16.840.1.113883.6.96" displayName="Pregnant"/>
  <effectiveTime value="20220615"/>
</observation>
```

**FHIR Target**:
1. Create **Observation-pregnancy-status** with:
   - `code.coding.code` = `82810-3`
   - `valueCodeableConcept.coding.code` = `77386006`
   - `effectiveDateTime` = `2022-06-15`

2. If EDD present in CDA, create **Observation-pregnancy-edd** with:
   - `code.coding.code` = `11778-8` or `11779-6` or `11780-4`
   - `valueDateTime` = estimated delivery date
   - Link via `hasMember` from pregnancy-status

### 3.2 Past Pregnancy Conversion

**CDA Source** (Per Delivery Event):
```xml
<organizer classCode="BATTERY" moodCode="EVN">
  <code code="PREG" displayName="Pregnancy"/>
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <code code="93857-1" codeSystem="2.16.840.1.113883.6.1" 
            displayName="Date and time of obstetric delivery"/>
      <effectiveTime value="20210908"/>
    </observation>
  </component>
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <code code="281050002" codeSystem="2.16.840.1.113883.6.96" 
            displayName="Livebirth"/>
      <value xsi:type="INT" value="1"/>
    </observation>
  </component>
</organizer>
```

**FHIR Target**:
Create **Observation-pregnancy-outcome** with:
- `code.coding.code` = `11636-8` ([#] Births.live)
- `valueQuantity.value` = `1`
- `effectiveDateTime` = `2021-09-08` (delivery date from CDA)

---

## 4. Additional Pregnancy Details (Optional Extensions)

### 4.1 Birth Weight (If Available)

```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8339-4",
      "display": "Birth weight"
    }]
  },
  "subject": {"reference": "Patient/newborn-id"},
  "focus": [{"reference": "Patient/2-1234-W7"}],
  "effectiveDateTime": "2021-09-08",
  "valueQuantity": {
    "value": 3200,
    "unit": "g",
    "system": "http://unitsofmeasure.org",
    "code": "g"
  }
}
```

**Key**: Use `focus` to reference mother, `subject` for newborn

### 4.2 Gestational Age (If Available)

```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11884-4",
      "display": "Gestational age at birth"
    }]
  },
  "subject": {"reference": "Patient/newborn-id"},
  "focus": [{"reference": "Patient/2-1234-W7"}],
  "effectiveDateTime": "2021-09-08",
  "valueQuantity": {
    "value": 39,
    "unit": "wk",
    "system": "http://unitsofmeasure.org",
    "code": "wk"
  }
}
```

---

## 5. Django Parser Updates Required

### 5.1 Pregnancy Status Filtering

```python
def _is_current_pregnancy(self, observation: Dict[str, Any]) -> bool:
    """Check if observation is current pregnancy status"""
    code_data = observation.get('code_data', observation.get('code', {}))
    
    # LOINC 82810-3 = Pregnancy status
    for coding in code_data.get('coding', []):
        if coding.get('system') == 'http://loinc.org' and coding.get('code') == '82810-3':
            return True
    
    return False

def _is_pregnancy_edd(self, observation: Dict[str, Any]) -> bool:
    """Check if observation is expected delivery date"""
    code_data = observation.get('code_data', observation.get('code', {}))
    
    # LOINC 11778-8, 11779-6, 11780-4 = EDD methods
    edd_codes = ['11778-8', '11779-6', '11780-4']
    for coding in code_data.get('coding', []):
        if coding.get('system') == 'http://loinc.org' and coding.get('code') in edd_codes:
            return True
    
    return False

def _is_pregnancy_outcome(self, observation: Dict[str, Any]) -> bool:
    """Check if observation is past pregnancy outcome"""
    code_data = observation.get('code_data', observation.get('code', {}))
    
    # LOINC pregnancy outcome codes
    outcome_codes = ['11636-8', '11637-6', '11638-4', '11639-2', '11640-0', 
                     '11612-9', '11613-7', '11614-5', '33065-4']
    for coding in code_data.get('coding', []):
        if coding.get('system') == 'http://loinc.org' and coding.get('code') in outcome_codes:
            return True
    
    return False
```

### 5.2 Pregnancy Grouping Logic

```python
def _group_pregnancy_observations(self, observations: List[Dict]) -> Dict:
    """Group pregnancy observations by type"""
    
    current_pregnancy = None
    edd_observation = None
    past_outcomes = []
    
    for obs in observations:
        if self._is_current_pregnancy(obs):
            current_pregnancy = obs
            
            # Check hasMember for EDD
            for member in obs.get('hasMember', []):
                edd_id = member.get('reference', '').split('/')[-1]
                edd_obs = next((o for o in observations if o.get('id') == edd_id), None)
                if edd_obs:
                    edd_observation = edd_obs
        
        elif self._is_pregnancy_outcome(obs):
            past_outcomes.append(obs)
    
    return {
        'current_pregnancy': {
            'status': current_pregnancy,
            'edd': edd_observation
        },
        'past_outcomes': past_outcomes
    }
```

---

## 6. Template Display Structure

### 6.1 Current Pregnancy Card

```html
<div class="pregnancy-card current">
    <h4><i class="fas fa-baby"></i> Current Pregnancy</h4>
    <div class="pregnancy-details">
        <div class="field">
            <label>Status:</label>
            <span>{{ current_pregnancy.status.value }}</span>
        </div>
        <div class="field">
            <label>Confirmed:</label>
            <span>{{ current_pregnancy.status.effectiveDateTime }}</span>
        </div>
        {% if current_pregnancy.edd %}
        <div class="field">
            <label>Expected Delivery:</label>
            <span>{{ current_pregnancy.edd.valueDateTime }}</span>
        </div>
        {% endif %}
    </div>
</div>
```

### 6.2 Past Pregnancy Timeline

```html
<div class="pregnancy-history">
    <h4><i class="fas fa-history"></i> Pregnancy History</h4>
    {% for outcome in past_outcomes %}
    <div class="pregnancy-event">
        <div class="event-date">
            <i class="fas fa-calendar"></i>
            {{ outcome.effectiveDateTime|date:"Y-m-d" }}
        </div>
        <div class="event-outcome">
            <span class="badge {{ outcome.code|outcome_badge }}">
                {{ outcome.code.display }}
            </span>
            <span class="count">{{ outcome.valueQuantity.value }}</span>
        </div>
    </div>
    {% endfor %}
</div>
```

---

## 7. Summary of Changes

### 7.1 CDA-to-FHIR Converter

**MUST**:
1. Map CDA pregnancy status to LOINC `82810-3` observation
2. Map CDA delivery dates to LOINC `11636-8`, `11637-6`, etc. observations
3. Use `effectiveDateTime` for delivery date (NOT observation date)
4. Create proper `hasMember` relationships for current pregnancy + EDD
5. Generate valid IPS profile references in `meta.profile`

**SHOULD**:
1. Map birth weight to LOINC `8339-4` with `focus` reference
2. Map gestational age to LOINC `11884-4` or `49051-6` with `focus` reference
3. Include delivery method if available in CDA narrative
4. Include complications if coded in CDA

### 7.2 Django Parser

**MUST**:
1. Filter observations by LOINC codes (not SNOMED codes)
2. Group current pregnancy (82810-3) separately from outcomes (11636-8, etc.)
3. Extract `effectiveDateTime` as delivery date for outcome observations
4. Follow `hasMember` references to link EDD to current pregnancy

**SHOULD**:
1. Display past outcomes in chronological order
2. Show outcome type (live birth, stillbirth, abortion) with appropriate badges
3. Handle missing data gracefully (no "Not specified" for non-existent fields)

---

## 8. Validation Checklist

### 8.1 FHIR Resource Validation

- [ ] All observations have valid `meta.profile` references
- [ ] Pregnancy status uses LOINC `82810-3` code
- [ ] Pregnancy status value uses SNOMED CT from pregnancy-status-uv-ips ValueSet
- [ ] EDD observations use LOINC codes from edd-method-uv-ips ValueSet
- [ ] Outcome observations use LOINC codes from pregnancies-summary-uv-ips ValueSet
- [ ] Current pregnancy has `hasMember` reference to EDD observation
- [ ] Outcome observations use delivery date in `effectiveDateTime`

### 8.2 Django UI Validation

- [ ] Current pregnancy displays separately from past outcomes
- [ ] Past outcomes sorted chronologically by delivery date
- [ ] Outcome types displayed with appropriate icons/badges
- [ ] Missing fields don't show "Not specified" placeholders
- [ ] EDD displays for current pregnancy if available

---

## 9. References

- **HL7 FHIR IPS Implementation Guide**: https://build.fhir.org/ig/HL7/fhir-ips/
- **Pregnancy Status Profile**: https://build.fhir.org/ig/HL7/fhir-ips/en/StructureDefinition-Observation-pregnancy-status-uv-ips.html
- **Pregnancy EDD Profile**: https://build.fhir.org/ig/HL7/fhir-ips/en/StructureDefinition-Observation-pregnancy-edd-uv-ips.html
- **Pregnancy Outcome Profile**: https://build.fhir.org/ig/HL7/fhir-ips/en/StructureDefinition-Observation-pregnancy-outcome-uv-ips.html

---

**Document Control**  
Created: November 17, 2025  
Status: Draft for CDA-to-FHIR Converter Implementation  
Next Review: After converter updates
