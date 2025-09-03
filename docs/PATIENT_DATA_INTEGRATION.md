# Patient Data System - Sample Data Integration

## Overview

This Django NCP system now integrates real sample patient data from the OpenNCP integration files. The system loads patient information from properties files organized by OID (Organization Identifier) and validates patient searches against this real data.

## Sample Data Structure

The sample patient data is organized as follows:

```
patient_data/sample_data/integration/
├── 1.3.6.1.4.1.48336/           # Portugal OID
│   ├── 1-1234-W8.properties
│   ├── 1-5678-W8.properties
│   ├── 2-1234-W8.properties
│   ├── 2-5678-W8.properties
│   └── 3-1234-W8.properties
├── 2.16.17.710.813.1000.990.1/  # Ireland OID
│   ├── 1-1234-W8.properties
│   ├── 1-5678-W8.properties
│   ├── 2-1234-W8.properties
│   ├── 2-5678-W8.properties
│   └── 3-1234-W8.properties
└── oid_mapping.json             # OID to country mapping
```

## Patient Properties File Format

Each patient file contains:

```properties
familyName=Schuman
givenName=Robert
administrativeGender=M
birthDate.year=1886
birthDate.month=06
birthDate.day=29
street=Breydelstraat, 4
city=Brussel
postalCode=1040
country=BE
telephone=00 800 67 89 10 11
email=robert.schuman@ec.europa.eu
```

## How to Test Patient Search

### Available Test Patients

All sample patients use the same personal information:

- **Name:** Robert Schuman
- **Birth Date:** 1886/06/29 (use format yyyy/MM/dd)
- **Gender:** Male
- **Address:** Breydelstraat, 4, Brussel, 1040, BE

**Available Patient IDs:**

- `1-1234-W8`
- `1-5678-W8`
- `2-1234-W8`
- `2-5678-W8`
- `3-1234-W8`

### Testing Steps

1. **Visit the Demo Page:** `/patient/demo/`
   - Shows all available sample patients
   - Displays patient information from the properties files
   - Provides "Search This Patient" buttons for quick testing

2. **Use Patient Search:** `/patient/search/`
   - Select Member State: Ireland or Portugal
   - Enter Patient ID: e.g., `2-1234-W8`
   - Enter Birth Date: `1886/06/29`
   - Submit the search

3. **View Results:**
   - System validates patient ID and birth date against sample data
   - If found, displays full patient information from properties file
   - Shows available services for the selected member state

### Validation Logic

The system performs the following validation:

1. **Patient Existence Check:** Looks for patient file `{patient_id}.properties` in the OID directory
2. **Birth Date Validation:** Compares provided birth date with the date from the properties file
3. **Data Loading:** If validation passes, loads and displays all patient information

### Error Scenarios

- **Patient Not Found:** "Patient {id} not found in {country}"
- **Birth Date Mismatch:** "Patient found but birth date does not match records"
- **Invalid Date Format:** "Birthdate must be in format yyyy/MM/dd"

## Member State Configuration

The system automatically configures member states with sample data OIDs:

- **Portugal (PT):** OID `1.3.6.1.4.1.48336`
- **Ireland (IE):** OID `2.16.17.710.813.1000.990.1`

## Integration with Translation Services

The patient search system integrates with the translation services:

1. Patient data is displayed in the original language from the properties files
2. Translation services can be used to translate medical terminologies
3. Service requests can be made for different document types (Patient Summary, ePrescription, Laboratory Reports)

## Management Commands

- **Populate Sample Data:** `python manage.py populate_sample_patients`
  - Copies sample data from OpenNCP integration folder
  - Creates/updates member states with sample data OIDs
  - Lists all available patients

## Architecture Components

### PatientDataLoader (`patient_data/patient_loader.py`)

- Loads and parses properties files
- Caches patient information for performance
- Provides search and validation methods

### Demo Views (`patient_data/demo_views.py`)

- Displays available sample patients
- Provides quick testing interface

### Updated Models

- `MemberState`: Added `sample_data_oid` field for linking to sample data
- Integration with existing patient identifier and data models

## Navigation

The system adds a "Patients" dropdown to the main navigation with:

- **Search Patient:** Main patient search interface
- **Sample Data Demo:** Shows available test patients

This provides a complete end-to-end testing environment using real OpenNCP sample data.
