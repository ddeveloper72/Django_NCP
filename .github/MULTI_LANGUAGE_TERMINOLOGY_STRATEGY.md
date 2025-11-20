# Multi-Language Terminology Strategy

## European Cross-Border Healthcare Context

### The Challenge

In European cross-border healthcare, patient FHIR resources may contain clinical terminology in the **source country's language**, but healthcare professionals need to view data in their **own language**.

**Example Scenario:**
```
Patient: Diana Ferreira (Portugal)
Healthcare Professional: Dr. O'Brien (Ireland)
Required Language: English
```

### FHIR Resource Example

```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "72166-2",
      "display": "Tobacco use and exposure - extensive"
    }],
    "text": "Status de tabagismo"  // ❌ Portuguese - problematic!
  }
}
```

## Django NCP Solution

### Architecture: Universal Codes + MVC/CTS Translations

```
┌─────────────────────────────────────────────────────────────┐
│ 1. FHIR Resource (Source Country - Portugal)                │
│    - code: "72166-2"                                         │
│    - system: "http://loinc.org"                             │
│    - text: "Status de tabagismo" (Portuguese)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Django NCP (Ireland)                                      │
│    - Extract universal LOINC code: 72166-2                   │
│    - Query MVC/CTS for target language: 'en'                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Master Value Catalogue (MVC) / CTS                        │
│    Input:                                                    │
│      - code: "72166-2"                                       │
│      - code_system_oid: "2.16.840.1.113883.6.1" (LOINC)     │
│      - target_language: "en"                                 │
│    Output:                                                   │
│      - display_value: "Tobacco smoking status" (English) ✅  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. UI Display (Healthcare Professional View)                │
│    Social History:                                           │
│      • Tobacco smoking status: 0.5 (pack)/d                 │
│      • Alcoholic drinks per day: 2 drinks/d                 │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

**Location:** `patient_data/services/fhir_bundle_parser.py`

```python
def _transform_social_history_observations(self, observations):
    """
    Uses Enhanced CTS Service for language-independent LOINC lookups
    """
    enhanced_cts = EnhancedCTSService()
    LOINC_OID = "2.16.840.1.113883.6.1"
    
    for obs in observations:
        observation_code = obs.get('observation_code', '')
        
        if observation_code:
            # Query MVC for target language (English)
            mvc_data = enhanced_cts.get_comprehensive_code_data(
                code=observation_code,
                code_system_oid=LOINC_OID,
                target_language='en',  # Healthcare professional's language
                include_all_languages=True  # For future bilingual display
            )
            
            if mvc_data:
                observation_name = mvc_data['display_value']  # ✅ "Tobacco smoking status"
            else:
                # Fallback to FHIR code.text (may be Portuguese)
                observation_name = obs.get('observation_name')  # ⚠️ "Status de tabagismo"
```

## Advantages

### ✅ Language-Independent
- **LOINC codes** are universal across all EU member states
- No dependency on source country language

### ✅ Professional Medical Translations
- MVC/CTS provides **validated medical terminology**
- Not machine translation - clinically accurate

### ✅ Multi-Language Support
- `include_all_languages=True` retrieves all available translations
- **Future enhancement:** Display both source and target language

### ✅ European Interoperability Standards
- Aligns with **epSOS** (European Patient Summary) requirements
- Supports **FHIR R4** cross-border data exchange

### ✅ Fallback Strategy
```
Priority:
1. MVC/CTS lookup (preferred) → "Tobacco smoking status" (English)
2. FHIR code.text (fallback)  → "Status de tabagismo" (Portuguese)
3. Generic text (last resort) → "Social history observation"
```

## Future Enhancement: Bilingual Display

```python
mvc_data = enhanced_cts.get_comprehensive_code_data(
    code="72166-2",
    code_system_oid=LOINC_OID,
    target_language='en',
    include_all_languages=True
)

# Display both languages
if mvc_data:
    primary_display = mvc_data['display_value']  # "Tobacco smoking status" (English)
    source_language_display = mvc_data.get('translations', {}).get('pt')  # "Status de tabagismo" (Portuguese)
    
    # UI could show:
    # "Tobacco smoking status (Status de tabagismo)"
```

## MVC Data Population

### Via CTS Training Portal (When Access Granted)

```bash
python manage.py sync_cts --environment training --systems LOINC,SNOMED,ICD10,ATC
```

### Via Django Admin (Manual)

1. Navigate to: **Admin > Translation Services > Value Set Catalogues**
2. Select: **Import MVC Data**
3. Upload LOINC terminology dataset

## Related Documentation

- **CTS Configuration:** `translation_services/cts_config.py`
- **Enhanced CTS Service:** `translation_services/enhanced_cts_service.py`
- **MVC Models:** `translation_services/mvc_models.py`
- **FHIR Processing:** `eu_ncp_server/services/fhir_processing.py`

## Testing

**Test Script:** `test_mvc_loinc_integration.py`

```bash
python test_mvc_loinc_integration.py
```

Expected output:
- ✅ LOINC 72166-2 → "Tobacco smoking status" (English)
- ✅ LOINC 74013-4 → "Alcoholic drinks per day" (English)

## Healthcare Professional Language Preference

**Current:** Hardcoded to English (`target_language='en'`)

**Future Enhancement:**
- Store healthcare professional's language preference in user profile
- Dynamic language selection based on logged-in user
- Support all 24 official EU languages via MVC/CTS

```python
# Future implementation
target_language = request.user.profile.language_preference or 'en'

mvc_data = enhanced_cts.get_comprehensive_code_data(
    code=observation_code,
    code_system_oid=LOINC_OID,
    target_language=target_language,  # Dynamic based on user
    include_all_languages=True
)
```

## Summary

**Django NCP uses universal clinical codes (LOINC, SNOMED CT, ICD-10) with MVC/CTS translations to provide language-independent clinical terminology across EU member states, ensuring healthcare professionals can view patient data in their own language regardless of the source country.**

This approach aligns with European healthcare interoperability standards and provides a foundation for future bilingual display capabilities.
