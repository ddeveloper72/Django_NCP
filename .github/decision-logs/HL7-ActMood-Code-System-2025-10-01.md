# 📑 Decision Log Entry: HL7 ActMood Code System

**Decision ID:** HL7-CS-ActMood-2025-10-01  
**Date:** 2025-10-01  
**Owner:** Architecture & Compliance  

## 🔹 Context

While aligning CDA payloads with HL7 vocabularies, we encountered OID `2.16.840.1.113883.5.139`.

This OID corresponds to the HL7 ActMood code system, which defines the mood (intent, state, or temporal context) of an Act.

CDA documents frequently reference this to distinguish between events, requests, promises, and intentions.

## 🔹 Decision

**Adopt HL7 ActMood (OID: `2.16.840.1.113883.5.139`) as a required vocabulary for all CDA-compliant payloads in Django_NCP.**

- Store this OID in the central code system registry for validation and enforcement.
- Implement validation rules to ensure that any `moodCode` attribute in CDA documents maps to a valid ActMood code.

## 🔹 Examples of Valid Codes

| Code | Description |
|------|-------------|
| `EVN` | Event (actual occurrence) |
| `INT` | Intent |
| `RQO` | Request/Order |
| `PRMS` | Promise |
| `APT` | Appointment |

## 🔹 Enforcement Strategy

### Validation Layer
Extend CDA parser to check `moodCode` values against the ActMood code system.

### Spec Checklist
Add an item under "CDA Vocabulary Compliance" → Verify all `moodCode` attributes resolve to HL7 ActMood codes.

### Documentation
Update retro-spec with a reference to this OID and its purpose.

### Testing
Add unit tests with sample CDA fragments containing each of the common ActMood codes.

## 🔹 Rationale

- **Semantic Consistency:** Ensures semantic consistency across CDA payloads.
- **Data Quality:** Prevents invalid or non-standard `moodCode` values from entering the system.
- **Standards Compliance:** Aligns Django_NCP with HL7 v3 structural vocabulary requirements.

## 🔹 Implementation Details

### Code System Registry Entry
```json
{
  "oid": "2.16.840.1.113883.5.139",
  "name": "HL7 ActMood",
  "description": "Codes for the mood (intent, state, or temporal context) of an Act",
  "status": "active",
  "validation_required": true
}
```

### CDA Parser Enhancement
```python
def validate_mood_code(self, mood_code):
    """Validate moodCode against HL7 ActMood vocabulary"""
    valid_codes = ['EVN', 'INT', 'RQO', 'PRMS', 'APT', 'DEF', 'SLOT']
    if mood_code not in valid_codes:
        raise ValidationError(f"Invalid moodCode: {mood_code}")
```

### Unit Test Example
```python
def test_valid_mood_codes(self):
    """Test that common ActMood codes are properly validated"""
    test_codes = ['EVN', 'INT', 'RQO', 'PRMS', 'APT']
    for code in test_codes:
        self.assertTrue(self.parser.validate_mood_code(code))
```

## 🔹 Related Standards

- **HL7 v3 Data Types:** ActMood is part of the HL7 v3 structural vocabulary
- **CDA R2:** Clinical Document Architecture Release 2 specification
- **IHE Profiles:** International patient care coordination profiles

## 🔹 Status

✅ **Approved and added to compliance framework.**

---

*This decision log entry supports Django_NCP's commitment to healthcare interoperability standards and semantic consistency across European healthcare data exchange.*