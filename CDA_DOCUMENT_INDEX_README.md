# CDA Document Index Management System

## Overview

This system provides automated indexing and discovery of test CDA documents for the Django NCP demonstration platform. It maintains the realistic NCP workflow principle of not storing patient data persistently while providing efficient access to test documents.

## Features

- **Automatic Discovery**: Scans `test_data/eu_member_states/` directories for CDA XML files
- **Patient Information Extraction**: Extracts patient identifiers, names, demographics from HL7 CDA content
- **L1/L3 CDA Support**: Distinguishes between L1 (PDF-based) and L3 (structured XML) CDA documents
- **No Persistent Storage**: Patient data is extracted on-demand, maintaining realistic NCP workflow
- **Fast Lookups**: JSON-based index file for quick patient discovery

## Architecture

### Components

1. **CDADocumentIndexer** (`patient_data/services/cda_document_index.py`)
   - Scans directories for CDA files
   - Extracts patient information from XML
   - Builds and maintains index file

2. **Enhanced Patient Search Service** (`patient_data/services/patient_search_service.py`)
   - Uses index for patient lookups
   - Loads CDA content on-demand
   - Supports both indexed and fallback patients

3. **Management Command** (`patient_data/management/commands/build_cda_index.py`)
   - Django command to build/refresh index
   - Usage: `python manage.py build_cda_index [--force] [--list-patients]`

4. **Test Patient Views** (`patient_data/cda_test_views.py`)
   - Web interface to view available test patients
   - AJAX index refresh functionality

## Directory Structure

```
test_data/
└── eu_member_states/
    ├── IT/                           # Italy
    │   ├── mario_pino_l1.xml        # L1 CDA (PDF-based)
    │   └── mario_pino_l3.xml        # L3 CDA (structured)
    ├── IE/                           # Ireland
    ├── GR/                           # Greece
    └── [other EU countries]/
```

## Usage

### Building the Index

```bash
# Build/update the index
python manage.py build_cda_index

# Force rebuild even if index exists
python manage.py build_cda_index --force

# Build and list all found patients
python manage.py build_cda_index --list-patients
```

### Accessing Test Patients

1. **Web Interface**: Visit `/patients/test-patients/` to see all available test patients
2. **Direct Query**: Use the patient search form with pre-populated links from the test patient page
3. **API Access**: The indexer can be used programmatically in views and services

### Adding New Test Patients

1. Place CDA XML files in the appropriate country directory under `test_data/eu_member_states/[COUNTRY]/`
2. Ensure files contain valid HL7 CDA patient information with:
   - Patient ID in `<id extension="..." assigningAuthorityName="..."/>`
   - Patient name in `<name><given>...</given><family>...</family></name>`
   - Optional birth date, gender, etc.
3. Run `python manage.py build_cda_index --force` to refresh the index
4. New patients will appear in the test patient interface

## Patient Identifier Extraction

The system extracts patient identifiers from CDA documents:

```xml
<patientRole>
    <id assigningAuthorityName="Ministero Economia e Finanze" 
        extension="NCPNPH80A01H501K" 
        root="2.16.840.1.113883.2.9.4.3.2"/>
    <patient>
        <name>
            <family>Pino</family>
            <given>Mario</given>
        </name>
        <administrativeGenderCode code="M"/>
        <birthTime value="19700101"/>
    </patient>
</patientRole>
```

## Index File Format

The index is stored as JSON in `cda_document_index.json`:

```json
{
  "NCPNPH80A01H501K": [
    {
      "file_path": "/path/to/mario_l1.xml",
      "patient_id": "NCPNPH80A01H501K",
      "given_name": "Mario",
      "family_name": "Pino",
      "birth_date": "1970-01-01",
      "gender": "Male",
      "country_code": "IT",
      "cda_type": "L1",
      "assigning_authority": "Ministero Economia e Finanze",
      "last_modified": 1691234567.89,
      "file_size": 12345
    }
  ]
}
```

## Realistic NCP Workflow

This system maintains the authentic NCP workflow:

1. **No Patient Storage**: Patient data is never saved to the database
2. **Session-Based**: Patient information is stored in Django sessions during queries
3. **On-Demand Loading**: CDA content is loaded only when needed
4. **Audit Trail**: Patient queries are logged but data is not persisted
5. **Cross-Border Simulation**: Mimics real NCP-to-NCP document exchange

## Current Test Patients

Based on the Italian CDA files, the following test patients are available:

- **Mario PINO** (IT)
  - Patient ID: `NCPNPH80A01H501K`
  - Authority: Ministero Economia e Finanze
  - Both L1 and L3 CDA documents available
  - Birth: 1970-01-01, Gender: Male

Additional patients can be discovered by running the index command.

## Integration with Existing System

The indexing system integrates seamlessly with the existing NCP platform:

- **Patient Search Form**: Enhanced with "View Test Patients" button
- **URL Pre-population**: Test patient page links auto-fill the search form
- **Session Compatibility**: Works with existing session-based patient handling
- **Template System**: Uses existing Jinja2 templates and styling

## Security Considerations

- Index file contains only minimal patient demographics
- Full CDA content is loaded on-demand, not cached
- Patient identifiers are handled according to GDPR requirements
- Audit logging maintains compliance with healthcare regulations
