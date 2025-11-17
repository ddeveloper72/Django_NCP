# Quick Start Guide - Transaction Bundle Upload

## Problem
Healthcare Team shows "Practitioner (nnn)" instead of "António Pereira" because HAPI's document bundle upload doesn't resolve `urn:uuid:` references.

## Solution
Upload Diana's bundle as a **transaction bundle** so HAPI automatically resolves all references.

## Steps

### 1. Upload Transaction Bundle

**Windows (Easy)**:
```
Double-click: upload_diana.bat
```

**Or PowerShell**:
```powershell
.\.venv\Scripts\python.exe upload_diana_transaction.py
```

### 2. Verify Upload (Optional)

**Windows**:
```
Double-click: check_references.bat
```

**Or PowerShell**:
```powershell
.\.venv\Scripts\python.exe check_hapi_references.py
```

### 3. Clear Django Session

```powershell
.\.venv\Scripts\python.exe quick_clear.py
```

### 4. Test in Django

1. Go to http://127.0.0.1:8080/patients/
2. Search for Diana Ferreira:
   - Patient ID: `2-1234-W7`
   - Country: `PT`
3. Click **Healthcare Team & Contacts** tab
4. You should now see:
   - ✅ **António Pereira** (instead of "Practitioner (nnn)")
   - ✅ **Centro Hospitalar de Lisboa Central**

## What Changed

### Before (Document Bundle)
```json
{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [{
    "resource": {
      "resourceType": "Practitioner",
      "id": "nnn",
      "name": [{"family": "Pereira"}]
    }
  }]
}
```
❌ HAPI stores Practitioner with placeholder ID "nnn"
❌ Composition still references "Practitioner/nnn"
❌ Django can't fetch it because "nnn" isn't the real ID

### After (Transaction Bundle)
```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [{
    "fullUrl": "urn:uuid:03f5b6c0...",
    "resource": {
      "resourceType": "Practitioner",
      // No 'id' field
      "name": [{"family": "Pereira"}]
    },
    "request": {"method": "POST", "url": "Practitioner"}
  }]
}
```
✅ HAPI assigns real ID (e.g., "12345")
✅ HAPI updates Composition to reference "Practitioner/12345"
✅ Django enrichment fetches it successfully!

## Files Created

1. **`upload_diana_transaction.py`** - Main upload script
2. **`check_hapi_references.py`** - Verification script
3. **`upload_diana.bat`** - Windows shortcut for upload
4. **`check_references.bat`** - Windows shortcut for verification
5. **`quick_clear.py`** - Clear Django sessions
6. **`UPLOAD_INSTRUCTIONS.md`** - Detailed instructions
7. **`FHIR_ENRICHMENT_SUMMARY.md`** - Technical documentation

## Troubleshooting

### "Connection timeout" error
HAPI can be slow. Wait and try again.

### "Still shows Practitioner (nnn)"
1. Run `check_references.bat` to verify upload worked
2. Make sure you cleared Django session
3. Try restarting Django server

### "Module not found" error
Make sure you're in the project directory and using the venv:
```powershell
cd C:\Users\Duncan\VS_Code_Projects\django_ncp
.\.venv\Scripts\python.exe upload_diana_transaction.py
```

## Expected Results

**Console Output**:
```
📂 Loading bundle: test_data/eu_member_states/PT/Diana_Ferreira_bundle.json

📊 Bundle Contents:
  - AllergyIntolerance: 3
  - Composition: 1
  - Organization: 1
  - Patient: 1
  - Practitioner: 1
  ...

✅ SUCCESS! Status: 200

✅ Created Resources:
  - Composition: 1
      → Composition/12345
  - Organization: 1
      → Organization/67890
  - Practitioner: 1
      → Practitioner/98765

✅ Properly resolved!

🎉 Transaction bundle uploaded successfully!
```

**Django UI**:
- Healthcare Team tab shows proper names
- Custodian Organization details complete
- Contact information displays correctly

## For Production

When deploying to production:
1. Always use transaction bundles for uploads
2. Remove placeholder IDs from resources
3. Let FHIR server assign proper IDs
4. References will be automatically resolved

## Support

If you encounter issues:
1. Check `UPLOAD_INSTRUCTIONS.md` for detailed guidance
2. Review `FHIR_ENRICHMENT_SUMMARY.md` for technical details
3. Verify HAPI is accessible: https://hapi.fhir.org/baseR4/metadata
