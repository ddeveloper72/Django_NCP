# 🗓️ eHDSI Date Formatting Standards - Research Document

**Created:** August 8, 2025  
**Purpose:** Research and implement compliant date formatting for clinical data display  
**Priority:** HIGH - Clinical compliance requirement

---

## 📚 **RESEARCH SOURCES NEEDED**

### Primary Sources

- [ ] **eHDSI Implementation Guide** - Date/Time formatting specifications
- [ ] **European Patient Summary (EPS) Guidelines** - Clinical date display standards
- [ ] **CDA R2 Implementation Guide** - HL7 date formatting requirements
- [ ] **ISO 8601** - International date standard (baseline)

### Secondary Sources  

- [ ] **EU Cross-Border Healthcare Directive** - Date formatting in healthcare
- [ ] **Country-Specific Guidelines** (FR, DE, IT, ES, etc.)
- [ ] **Medical Terminology Standards** (SNOMED CT date contexts)

---

## 🔍 **CURRENT STATE ANALYSIS**

### Current Implementation (`format_clinical_date()`)

```python
# Current formats supported:
- "%Y-%m-%d"           # 2024-01-15
- "%d/%m/%Y"           # 15/01/2024  
- "%m/%d/%Y"           # 01/15/2024
- "%Y-%m-%d %H:%M:%S"  # 2024-01-15 10:30:00

# Current output format:
- "%B %d, %Y"          # January 15, 2024 (English only)
```

### Issues Identified

1. **English-only output** - Not multilingual
2. **Limited input formats** - Missing HL7 CDA formats
3. **No timezone handling** - May be required for clinical accuracy
4. **No context awareness** - Start vs end vs effective dates
5. **No precision handling** - Day vs datetime precision

---

## 📋 **REQUIREMENTS GATHERING**

### Expected eHDSI Date Formats (Research Needed)

#### Input Formats (from CDA documents)

- [ ] **HL7 CDA Format:** `YYYYMMDD` or `YYYYMMDDHHMMSS`
- [ ] **ISO 8601:** `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
- [ ] **Partial Dates:** `YYYY-MM` or `YYYY` (year/month precision)
- [ ] **Time Zones:** UTC offsets or local time handling

#### Output Formats (for UI display)

- [ ] **Patient-facing:** Localized, readable format
- [ ] **Clinical:** Precise, unambiguous format  
- [ ] **Professional:** Medical standard format
- [ ] **Multilingual:** Language-specific formatting

### Context-Specific Requirements

- [ ] **Medication dates:** Start, end, effective times
- [ ] **Procedure dates:** Performed, scheduled dates
- [ ] **Allergy dates:** Onset, first noted dates
- [ ] **Document dates:** Creation, validation dates

---

## 🎯 **IMPLEMENTATION PLAN**

### Phase 1: Research & Standards

1. **Locate eHDSI Implementation Guide**
   - Official EU eHealth documentation
   - Date formatting specifications
   - Clinical display requirements

2. **Analyze Sample CDAs**
   - Review existing eHDSI validation files in project
   - Document actual date formats used
   - Identify patterns and variations

### Phase 2: Enhanced Date Parser

1. **Expand input format support**
   - HL7 CDA date formats (`YYYYMMDD`, etc.)
   - Partial date handling
   - Timezone awareness

2. **Create context-aware formatting**
   - Different formats for different clinical contexts
   - Precision-appropriate display
   - Multilingual output support

### Phase 3: eHDSI Compliance

1. **Implement standard-compliant formatting**
   - Official eHDSI format requirements
   - Country-specific variations if needed
   - Clinical safety considerations

---

## 🧪 **TEST CASES NEEDED**

### Input Date Formats

```python
test_dates = [
    # HL7 CDA formats
    "20240115",           # YYYYMMDD
    "202401151030",       # YYYYMMDDHHMM  
    "20240115103045",     # YYYYMMDDHHMMSS
    
    # ISO formats
    "2024-01-15",         # YYYY-MM-DD
    "2024-01-15T10:30:45", # ISO datetime
    
    # Partial dates
    "2024-01",            # Year-month
    "2024",               # Year only
    
    # European formats
    "15/01/2024",         # DD/MM/YYYY
    "15.01.2024",         # DD.MM.YYYY (German)
    "15-01-2024",         # DD-MM-YYYY
]
```

### Expected Outputs (Research Required)

- [ ] Document expected eHDSI-compliant outputs for each input
- [ ] Define language-specific formatting rules
- [ ] Specify clinical context formatting

---

## 🚀 **IMMEDIATE ACTIONS**

### 1. Research eHDSI Documentation

- [ ] Search for official eHDSI Implementation Guide
- [ ] Contact EU eHealth authorities if needed
- [ ] Review existing project CDA samples for date formats

### 2. Analyze Current Data

```bash
# Search for date patterns in existing CDAs
grep -r "effectiveTime\|observationDateTime\|time" test_data/
```

### 3. Create Enhanced Date Formatter

```python
# Proposed function signature
def format_clinical_date_ehdsi(
    date_string: str,
    context: str = "general",        # medication, procedure, allergy
    language: str = "en",            # en, fr, de, it, es
    precision: str = "auto",         # day, datetime, year, month
    clinical_standard: str = "ehdsi" # ehdsi, iso, local
) -> str:
    """eHDSI-compliant clinical date formatting"""
    pass
```

---

## 📝 **RESEARCH NOTES**

### Date Format Discoveries

*(To be filled as research progresses)*

### eHDSI Specifications

*(To be documented from official sources)*

### Country-Specific Requirements  

*(To be added based on research)*

---

## ✅ **COMPLETION CHECKLIST**

- [ ] Research completed - eHDSI standards documented
- [ ] Enhanced date parser implemented
- [ ] Test cases created and passing
- [ ] Multilingual support added
- [ ] Clinical context awareness implemented
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Production deployment tested

---

*This document will be updated as research progresses and implementation advances.*
