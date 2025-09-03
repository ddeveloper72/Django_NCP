# Patient Directory - EU Member States CDA Test Data

## Overview

This directory contains all patients imported from the EU member states CDA test data located in `test_data/eu_member_states/`. Each patient record includes their raw CDA XML content and clinical data extracted using the Enhanced CDA XML Parser.

**Import Date**: August 7, 2025  
**Total Patients**: 15 unique patients (from 41 processed CDA documents)  
**Countries Represented**: 10 EU member states  

## Countries and Patients

### 🇧🇪 Belgium (BE) - 2 Patients

**1. Robert Schuman**

- **National ID**: `3-1234-W7`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**:
  - Diagnostic Imaging Report (18/06/2021)
  - Medical Images (19/01/2020)
- **Clinical Sections**: 0 coded sections
- **Source Files**: `3-1234-W7 (1).xml`, `3-1234-W7 (2).xml`

**2. Robert Schuman**

- **National ID**: `3-1234-W6`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Laboratory Report (18/09/2019)
- **Clinical Sections**: 0 coded sections
- **Source Files**: `3-1234-W7.xml`

---

### 🇪🇺 European Union (EU) - 1 Patient

**1. Mario Pino**

- **National ID**: `NCPNPH80A01H501K`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (28/07/2008)
- **Clinical Sections**: Up to 8 coded sections with 42 clinical codes
- **Source Files**: `Mario_Pino_NCPNPH80.xml`, `Mario_Pino_NCPNPH80_1.xml`, `Mario_Pino_NCPNPH80_2.xml`, `Mario_Pino_NCPNPH80_3.xml`
- **Notes**: L3 CDA documents contain structured clinical data

---

### 🇬🇷 Greece (GR) - 1 Patient

**1. ΜΑΡΙΑ ΔΗΜΟΥ (Maria Dimou)**

- **National ID**: `01017515303`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Laboratory Result H05AA02 539305450000074414 (24/10/2022)
- **Clinical Sections**: 0 coded sections
- **Source Files**: `ΜΑΡΙΑ_ΔΗΜΟΥ_01017515.xml`
- **Notes**: Greek patient with Unicode characters

---

### 🇮🇪 Ireland (IE) - 3 Patients

**1. Sean Murphy** *(Pre-existing)*

- **National ID**: `IE-12345678`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Notes**: Was in database before import

**2. Áine O'Brien** *(Pre-existing)*

- **National ID**: `IE-87654321`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Notes**: Was in database before import

**3. Patrick Murphy**

- **National ID**: `539305455995368085`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (25/01/2024 17:30)
- **Clinical Sections**: 5 coded sections with 33 clinical codes
- **Source Files**: `Patrick_Murphy_53930545.xml`
- **Notes**: L3 CDA with rich clinical data

---

### 🇮🇹 Italy (IT) - 1 Patient

**1. Mario Pino**

- **National ID**: `NCPNPH80A01H501K`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (28/07/2008)
- **Clinical Sections**: Up to 8 coded sections with 42 clinical codes
- **Source Files**: Multiple EHDSI validation files
- **Notes**: Same patient as EU entry, different country context

---

### 🇱🇺 Luxembourg (LU) - 2 Patients

**1. CELESTINA DOE-CALLA**

- **National ID**: `3843082788`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Résumé patient (03/06/2024 11:18)
- **Clinical Sections**: Up to 6 coded sections with 68 clinical codes
- **Source Files**: `CELESTINA_DOE-CALLA_38430827.xml` and variants
- **Notes**: Rich clinical data in L3 documents

**2. Norbert Claude Peters**

- **National ID**: `2544557646`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**:
  - Hospital discharge reports (01/11/2023)
  - MRI knee imaging (27/02/2024)
  - COVID-19 diagnosis (19/02/2024)
- **Clinical Sections**: 0 coded sections
- **Source Files**: `Norbert_Claude_Peters_25445576.xml` and variants
- **Notes**: Multiple document types available

---

### 🇱🇻 Latvia (LV) - 1 Patient

**1. JOLANTA EGLE**

- **National ID**: `291003-21303`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: epSOS Patient Summary (01/04/2025)
- **Clinical Sections**: Up to 5 coded sections with 50 clinical codes
- **Source Files**: Multiple EHDSI validation files
- **Notes**: Recent L3 CDA with clinical codes

---

### 🇲🇹 Malta (MT) - 1 Patient

**1. Mario Borg** ⭐ **(Primary Test Patient)**

- **National ID**: `9999002M`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (17/03/2025 22:00)
- **Clinical Sections**: Up to 5 coded sections with 15 clinical codes
- **Source Files**: `Mario_Borg_9999002M.xml` and variants
- **Notes**: **This is the main test patient for Malta CDA processing**

---

### 🇵🇹 Portugal (PT) - 2 Patients

**1. Diana Ferreira**

- **National ID**: `2-1234-W7`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (08/06/2022 10:49)
- **Clinical Sections**: 13 sections, 12 coded with 162 clinical codes
- **Source Files**: `2-1234-W7.xml`
- **Notes**: **Richest clinical data set** with most coded sections

**2. Diana Ferreira**

- **National ID**: `2-5678-W7`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: Patient Summary (14/07/2023 19:45)
- **Clinical Sections**: 5 coded sections with 9 clinical codes
- **Source Files**: `2-5678-W7.xml`
- **Notes**: Same patient, different ID and clinical profile

---

### ❓ Unknown Country (UNKNOWN) - 1 Patient

**1. JOLANTA EGLE**

- **National ID**: `291003-21303`
- **Birth Date**: Not specified
- **Gender**: Unknown
- **Documents**: epSOS Patient Summary (01/04/2025)
- **Clinical Sections**: Up to 5 coded sections with 50 clinical codes
- **Source Files**: `JOLANTA_EGLE_291003-2.xml` and variants
- **Notes**: Duplicate of Latvia patient in unknown folder

---

## Clinical Data Summary

### Patients with Rich Clinical Data (L3 CDA)

1. **Diana Ferreira (PT - 2-1234-W7)**: 13 sections, 162 clinical codes ⭐ **Best for testing**
2. **CELESTINA DOE-CALLA (LU)**: 6 sections, 68 clinical codes
3. **JOLANTA EGLE (LV/UNKNOWN)**: 5 sections, 50 clinical codes
4. **Mario Pino (EU/IT)**: 8 sections, 42 clinical codes
5. **Patrick Murphy (IE)**: 5 sections, 33 clinical codes
6. **Mario Borg (MT)**: 5 sections, 15 clinical codes ⭐ **Malta test patient**

### Document Types Available

- **Patient Summary (PS)**: Most common document type
- **Laboratory Reports**: Available for several patients
- **Diagnostic Imaging**: MRI, X-ray reports
- **Hospital Discharge Reports**: Available for Luxembourg patients
- **COVID-19 Diagnostic Reports**: Recent pandemic-related documents

## Usage for Testing

### Recommended Test Patients

1. **Mario Borg (MT - 9999002M)**: Primary Malta test case
2. **Diana Ferreira (PT - 2-1234-W7)**: Richest clinical data for comprehensive testing
3. **Patrick Murphy (IE - 539305455995368085)**: Good L3 example with English context
4. **CELESTINA DOE-CALLA (LU - 3843082788)**: Multi-language testing (French)

### Search Parameters

To find patients in the web interface:

- Select country from dropdown
- Enter patient National ID
- System will load raw CDA content and process clinical sections

## Technical Notes

- All patients have raw CDA XML content stored in `raw_patient_summary` field
- Clinical sections are processed on-demand using Enhanced CDA XML Parser
- L1 CDA documents contain PDF attachments
- L3 CDA documents contain structured XML clinical data
- Some patients appear in multiple countries (cross-border scenarios)

## Files and Locations

- **Raw CDA Files**: `test_data/eu_member_states/{country}/`
- **Import Script**: `import_ncp_patients.py`
- **Database Models**: `ncp_gateway/models.py`
- **Parser**: `patient_data/services/enhanced_cda_xml_parser.py`
