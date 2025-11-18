# Django Cache & Session Clear Instructions

## Problem
Date formatter code works perfectly (19/19 tests passing), but UI still shows raw dates like "19941003" because Django is serving old cached session data from before the formatting code was added.

## Solution: Clear Cache and Restart

### Step 1: Stop Django Server
```powershell
# Press Ctrl+C in the terminal running Django server
```

### Step 2: Clear Python Bytecode Cache
```powershell
# Delete all __pycache__ directories
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# Verify deletion
Get-ChildItem -Recurse -Directory -Filter __pycache__
# (Should return nothing)
```

### Step 3: Clear Django Sessions (Choose ONE option)

**Option A: Delete entire database** (Nuclear option - clears everything)
```powershell
Remove-Item db.sqlite3
python manage.py migrate
```

**Option B: Flush sessions only** (Safer - keeps other data)
```powershell
python manage.py shell
```
Then in the Django shell:
```python
from django.contrib.sessions.models import Session
Session.objects.all().delete()
exit()
```

**Option C: Clear sessions programmatically**
```powershell
python manage.py clearsessions
```

### Step 4: Restart Django Server
```powershell
python manage.py runserver
```

### Step 5: Re-parse Diana Ferreira Data
1. Navigate to Diana Ferreira patient view in browser
2. This triggers fresh FHIR bundle parsing
3. New parsing uses updated `fhir_bundle_parser.py` with `ClinicalDateFormatter` calls
4. Formatted dates saved to fresh session

### Expected Results
✅ Medical Problems: "3 October 1994" (not "19941003")
✅ Allergies: "6 May 2017" (not "20170506")  
✅ Procedures: "1 January 2000" (not "2000-01-01T00:00:00Z")
✅ Immunizations: Formatted dates
✅ Pregnancy History: Formatted dates (already working)

## Why This Happened
Django sessions store parsed FHIR data in `db.sqlite3`. When you view a patient:
1. Django checks if session data exists
2. If yes, serves cached data (fast, no re-parsing)
3. If no, parses FHIR bundle fresh (slow, but gets new code)

Your formatting code was added AFTER Diana's data was parsed, so her session contains old unformatted dates.

## Proof Code Is Correct
- `test_clinical_date_formatter.py`: 15/15 tests passing ✅
- `test_medical_problems_dates.py`: 4/4 tests passing ✅
- `debug_date_formatting.py`: Direct formatter 3/3 passing ✅
- Code review: All 4 resource types have formatting calls ✅

**Problem is NOT code logic - it's cached data.**

## If Problem Persists After Cache Clear
Check that `patient_data/services/fhir_bundle_parser.py` contains:

**Line 22:**
```python
from patient_data.utils.date_formatter import ClinicalDateFormatter
```

**Lines 1427-1437 (Conditions):**
```python
raw_onset = condition.get('onsetDateTime', condition.get('onsetString', 'Unknown'))
if raw_onset and raw_onset not in ('Unknown', 'Not applicable'):
    onset_date = ClinicalDateFormatter.format_clinical_date(raw_onset)
else:
    onset_date = raw_onset
```

**Lines 1494-1507 (Procedures):**
```python
if raw_date and raw_date != 'Unknown date':
    performed_date = ClinicalDateFormatter.format_procedure_date(raw_date)
```

**Line 850 (Allergies):**
```python
'onset_date': self._format_allergy_onset_date(allergy, is_negative_assertion),
```

**Lines 2162-2170 (Immunizations):**
```python
if raw_occurrence:
    occurrence_date = ClinicalDateFormatter.format_clinical_date(raw_occurrence)
```

All these should be present. If they are, the issue is 100% cached session data.
