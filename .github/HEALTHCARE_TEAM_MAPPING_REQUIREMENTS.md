# Healthcare Team & Contacts Section - Mapping Requirements

**Date:** November 19, 2025  
**Purpose:** Define comprehensive mapping requirements for healthcare team and contact data from FHIR resources to Django NCP UI

## Current Implementation Analysis

### What We're Currently Mapping ✅

**From `FHIRBundleParser._extract_healthcare_data()`:**

1. **Practitioner Resources:**
   - `id`: Practitioner identifier
   - `name`: Full practitioner name (formatted from HumanName)
   - `family_name`: Family/surname
   - `given_names`: Array of given names
   - `qualification`: Practitioner qualifications array
   - `addresses`: Array of practitioner addresses
   - `telecoms`: Array of contact information (phone, email)
   - `identifiers`: Array of official identifiers
   - `gender`: Practitioner gender
   - `active`: Active status

2. **Organization Resources:**
   - `id`: Organization identifier
   - `name`: Organization name
   - `type`: Organization type codes
   - `addresses`: Array of organization addresses
   - `telecoms`: Array of organization contact information
   - `identifiers`: Array of official identifiers
   - `active`: Active status
   - `contact`: Organization contact persons

3. **Healthcare Team (from Composition):**
   - `reference`: Reference to practitioner/organization
   - `display_name`: Name of healthcare professional
   - `role`: Role type (Author, etc.)

### What's Missing ❌

Based on FHIR R4 specification and European healthcare standards, we're missing:

#### Practitioner Resource Fields

1. **Professional Identifiers:**
   - National practitioner IDs
   - Medical license numbers
   - Professional registration numbers
   - NPI (National Provider Identifier) equivalents for EU countries

2. **Specialty/Role Information:**
   - `practitionerRole`: Detailed role information (separate resource)
   - Primary specialty codes (SNOMED CT)
   - Additional specialties
   - Healthcare service types provided

3. **Professional Qualifications (Extended):**
   - Qualification identifier
   - Issuer organization
   - Period of validity
   - Qualification code (SNOMED CT, ISCO-08)

4. **Communication:**
   - Languages spoken (with proficiency level)
   - Preferred communication method

5. **Photo:**
   - Practitioner photo (base64 or URL)

6. **Active Period:**
   - Period during which practitioner is/was active

#### PractitionerRole Resource (Currently Not Mapped)

**Critical for European Healthcare:**

1. **Role Details:**
   - `code`: Role type codes (doctor, nurse, specialist, etc.)
   - `specialty`: Medical specialties (cardiology, surgery, etc.)
   - `practitioner`: Reference to Practitioner
   - `organization`: Reference to Organization
   - `location`: Where the practitioner practices
   - `healthcareService`: Services provided

2. **Availability:**
   - `availableTime`: Days/hours of availability
   - `notAvailable`: Periods of unavailability
   - `availabilityExceptions`: Holiday schedules, etc.

3. **Contact Information (Context-Specific):**
   - Role-specific phone numbers
   - Role-specific email addresses
   - Endpoint references (API, FHIR server URLs)

4. **Professional Period:**
   - Start date of role
   - End date (if applicable)

#### Organization Resource (Extended Fields)

1. **Organization Hierarchy:**
   - `partOf`: Parent organization reference
   - Department structure
   - Healthcare facility type

2. **Organization Contact (Extended):**
   - Contact purpose (administrative, billing, clinical)
   - Contact person name
   - Contact telecoms
   - Contact address

3. **Organization Services:**
   - Services provided
   - Opening hours
   - Emergency contact information

4. **Accreditation:**
   - Accreditation bodies
   - Certification dates
   - Quality ratings

#### RelatedPerson Resource (Currently Minimal Mapping)

1. **Patient Relationship:**
   - Relationship type (extensive SNOMED CT coding)
   - Relationship period
   - Active status

2. **Contact Preferences:**
   - Preferred contact method
   - Contact ranking/priority
   - Best time to contact

3. **Legal Authority:**
   - Guardian status
   - Power of attorney
   - Healthcare proxy

## Required Postman Endpoints for Development

### Recommended Test Data Endpoints

Please create the following Postman endpoints to test comprehensive mapping:

#### 1. Complete Practitioner Resource
```
GET {{fhir_base_url}}/Practitioner/{{practitioner_id}}
```

**Should Include:**
- Full HumanName with prefix, suffix, period
- Multiple identifiers (national ID, license, NPI)
- Comprehensive qualification array with:
  - Qualification identifier
  - Issuer organization reference
  - Code with SNOMED CT
  - Period (start/end dates)
- Multiple addresses (work, home) with full FHIR R4 compliance
- Multiple telecoms (office phone, mobile, fax, email) with use/rank
- Communication array (languages + proficiency)
- Photo attachment (optional)
- Active period (start/end dates)
- Gender (male/female/other/unknown)
- Birth date (for age calculation)

**Example Structure:**
```json
{
  "resourceType": "Practitioner",
  "id": "practitioner-pereira-antonio",
  "identifier": [
    {
      "system": "https://rnpr.min-saude.pt",
      "value": "PT-RNPR-123456",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "MD",
          "display": "Medical License number"
        }]
      }
    },
    {
      "system": "https://niss.seg-social.pt",
      "value": "12345678901",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "NI",
          "display": "National unique individual identifier"
        }]
      }
    }
  ],
  "active": true,
  "name": [{
    "use": "official",
    "family": "Pereira",
    "given": ["António", "José"],
    "prefix": ["Dr."],
    "suffix": ["MD"]
  }],
  "telecom": [
    {
      "system": "phone",
      "value": "351211234568",
      "use": "work",
      "rank": 1
    },
    {
      "system": "email",
      "value": "medico@gmail.com",
      "use": "work"
    }
  ],
  "address": [{
    "use": "work",
    "type": "physical",
    "line": ["3, Alameda Santo António dos Capuchos"],
    "city": "Lisbon",
    "postalCode": "1169-050",
    "country": "PT"
  }],
  "gender": "male",
  "birthDate": "1975-03-15",
  "qualification": [
    {
      "identifier": [{
        "system": "https://ordem-medicos.pt",
        "value": "OM-45678"
      }],
      "code": {
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "309343006",
          "display": "Physician"
        }],
        "text": "Medical Doctor"
      },
      "period": {
        "start": "2000-06-15"
      },
      "issuer": {
        "reference": "Organization/ordem-medicos-pt",
        "display": "Ordem dos Médicos (Portuguese Medical Association)"
      }
    },
    {
      "code": {
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "394814009",
          "display": "General practice"
        }],
        "text": "General Practitioner"
      },
      "period": {
        "start": "2003-09-01"
      }
    }
  ],
  "communication": [
    {
      "coding": [{
        "system": "urn:ietf:bcp:47",
        "code": "pt",
        "display": "Portuguese"
      }],
      "text": "Portuguese (native)"
    },
    {
      "coding": [{
        "system": "urn:ietf:bcp:47",
        "code": "en",
        "display": "English"
      }],
      "text": "English (fluent)"
    }
  ]
}
```

#### 2. PractitionerRole Resource (Critical - Currently Not Mapped)
```
GET {{fhir_base_url}}/PractitionerRole?practitioner={{practitioner_id}}
```

**Should Include:**
- Active status
- Period (start/end dates)
- Practitioner reference
- Organization reference
- Code (role type: doctor, nurse, specialist)
- Specialty codes (SNOMED CT)
- Location references
- HealthcareService references
- Telecoms (role-specific contact info)
- AvailableTime (schedule)
- NotAvailable (exceptions)
- Endpoint references

**Example Structure:**
```json
{
  "resourceType": "PractitionerRole",
  "id": "role-pereira-general-practice",
  "active": true,
  "period": {
    "start": "2010-01-01"
  },
  "practitioner": {
    "reference": "Practitioner/practitioner-pereira-antonio",
    "display": "Dr. António Pereira"
  },
  "organization": {
    "reference": "Organization/centro-hospitalar-lisboa-central",
    "display": "Centro Hospitalar de Lisboa Central"
  },
  "code": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "158965000",
      "display": "Medical practitioner"
    }],
    "text": "General Practitioner"
  }],
  "specialty": [
    {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "394814009",
        "display": "General practice"
      }],
      "text": "General Medicine"
    },
    {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "408443003",
        "display": "General medical practice"
      }]
    }
  ],
  "location": [{
    "reference": "Location/hospital-main-building",
    "display": "Main Hospital Building"
  }],
  "healthcareService": [{
    "reference": "HealthcareService/general-medicine",
    "display": "General Medicine Department"
  }],
  "telecom": [
    {
      "system": "phone",
      "value": "351211234568",
      "use": "work"
    },
    {
      "system": "email",
      "value": "antonio.pereira@chlc.min-saude.pt",
      "use": "work"
    }
  ],
  "availableTime": [
    {
      "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
      "availableStartTime": "08:00:00",
      "availableEndTime": "17:00:00"
    }
  ],
  "notAvailable": [{
    "description": "Annual Leave",
    "during": {
      "start": "2025-08-01",
      "end": "2025-08-15"
    }
  }],
  "endpoint": [{
    "reference": "Endpoint/practitioner-fhir-endpoint",
    "display": "Practitioner FHIR API Endpoint"
  }]
}
```

#### 3. Organization Resource (Extended)
```
GET {{fhir_base_url}}/Organization/{{organization_id}}
```

**Should Include:**
- Full identifier array (national health system ID, tax ID, facility ID)
- Organization type codes
- Name (official + aliases)
- Telecom array (phone, fax, email, url)
- Address array (with use: work/billing/physical)
- PartOf (parent organization)
- Contact array (administrative, billing, HR contacts)
- Endpoint references
- Active period

**Example Structure:**
```json
{
  "resourceType": "Organization",
  "id": "centro-hospitalar-lisboa-central",
  "identifier": [
    {
      "system": "https://spms.min-saude.pt/institutions",
      "value": "PT-HOSP-106001",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "XX",
          "display": "Organization identifier"
        }]
      }
    },
    {
      "system": "https://finan.gov.pt/tax-id",
      "value": "500066471",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "TAX",
          "display": "Tax ID number"
        }],
        "text": "NIPC (Tax Identification Number)"
      }
    }
  ],
  "active": true,
  "type": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/organization-type",
      "code": "prov",
      "display": "Healthcare Provider"
    }]
  }, {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "22232009",
      "display": "Hospital"
    }]
  }],
  "name": "Centro Hospitalar de Lisboa Central",
  "alias": ["CHLC", "Hospital de São José"],
  "telecom": [
    {
      "system": "phone",
      "value": "351217805000",
      "use": "work"
    },
    {
      "system": "email",
      "value": "hospital@gmail.com",
      "use": "work"
    },
    {
      "system": "url",
      "value": "http://www.chlc.min-saude.pt",
      "use": "work"
    }
  ],
  "address": [{
    "use": "work",
    "type": "physical",
    "line": ["3, Alameda Santo António dos Capuchos"],
    "city": "Lisbon",
    "state": "Lisboa",
    "postalCode": "1169-050",
    "country": "PT"
  }, {
    "use": "billing",
    "type": "postal",
    "line": ["P.O. Box 1234"],
    "city": "Lisbon",
    "postalCode": "1100-000",
    "country": "PT"
  }],
  "partOf": {
    "reference": "Organization/servico-nacional-saude",
    "display": "Serviço Nacional de Saúde (SNS)"
  },
  "contact": [
    {
      "purpose": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
          "code": "ADMIN",
          "display": "Administrative"
        }]
      },
      "name": {
        "use": "official",
        "family": "Silva",
        "given": ["Maria"]
      },
      "telecom": [
        {
          "system": "phone",
          "value": "351217805100",
          "use": "work"
        },
        {
          "system": "email",
          "value": "maria.silva@chlc.min-saude.pt",
          "use": "work"
        }
      ]
    },
    {
      "purpose": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
          "code": "BILL",
          "display": "Billing"
        }]
      },
      "name": {
        "use": "official",
        "family": "Santos",
        "given": ["João"]
      },
      "telecom": [
        {
          "system": "phone",
          "value": "351217805200",
          "use": "work"
        },
        {
          "system": "email",
          "value": "billing@chlc.min-saude.pt",
          "use": "work"
        }
      ]
    }
  ],
  "endpoint": [{
    "reference": "Endpoint/chlc-fhir-endpoint",
    "display": "CHLC FHIR Server"
  }]
}
```

#### 4. RelatedPerson Resource (Enhanced)
```
GET {{fhir_base_url}}/RelatedPerson?patient={{patient_id}}
```

**Should Include:**
- Patient reference
- Relationship coding (comprehensive SNOMED CT)
- Active status
- Period
- Name (full HumanName structure)
- Telecom (with preferred contact method)
- Address
- Gender
- Birth date
- Photo (optional)
- Communication (languages)

**Example Structure:**
```json
{
  "resourceType": "RelatedPerson",
  "id": "joaquim-baptista-guardian",
  "active": true,
  "patient": {
    "reference": "Patient/diana-ferreira",
    "display": "Diana Ferreira"
  },
  "relationship": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "GUARD",
      "display": "Guardian"
    }, {
      "system": "http://snomed.info/sct",
      "code": "394863008",
      "display": "Guardian"
    }],
    "text": "Legal Guardian"
  }],
  "name": [{
    "use": "official",
    "family": "Baptista",
    "given": ["Joaquim"]
  }],
  "telecom": [
    {
      "system": "phone",
      "value": "351211234569",
      "use": "mobile",
      "rank": 1
    },
    {
      "system": "email",
      "value": "guardian@gmail.com",
      "use": "home"
    }
  ],
  "address": [{
    "use": "home",
    "type": "physical",
    "line": ["155, Avenida da Liberdade"],
    "city": "Lisbon",
    "postalCode": "1250-141",
    "country": "PT"
  }],
  "gender": "male",
  "birthDate": "1955-12-10",
  "communication": [{
    "language": {
      "coding": [{
        "system": "urn:ietf:bcp:47",
        "code": "pt",
        "display": "Portuguese"
      }]
    },
    "preferred": true
  }],
  "period": {
    "start": "2015-01-01"
  }
}
```

#### 5. Composition Resource (Healthcare Team Authors)
```
GET {{fhir_base_url}}/Composition?patient={{patient_id}}&type=60591-5
```

**Should Include:**
- Multiple authors (can be Practitioner, PractitionerRole, Organization, Device)
- Attester information (legal authenticator, professional authenticator)
- Custodian reference
- Encounter context
- Event references

**Example Structure:**
```json
{
  "resourceType": "Composition",
  "id": "patient-summary-diana-ferreira",
  "status": "final",
  "type": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "60591-5",
      "display": "Patient summary Document"
    }]
  },
  "subject": {
    "reference": "Patient/diana-ferreira",
    "display": "Diana Ferreira"
  },
  "date": "2022-06-08T10:49:00+02:00",
  "author": [
    {
      "reference": "Practitioner/practitioner-pereira-antonio",
      "display": "Dr. António Pereira"
    },
    {
      "reference": "PractitionerRole/role-pereira-general-practice",
      "display": "General Practitioner Role"
    }
  ],
  "title": "Patient Summary for Diana Ferreira",
  "custodian": {
    "reference": "Organization/centro-hospitalar-lisboa-central",
    "display": "Centro Hospitalar de Lisboa Central"
  },
  "attester": [
    {
      "mode": "legal",
      "time": "2022-06-08T10:49:00+02:00",
      "party": {
        "reference": "Practitioner/practitioner-pereira-antonio",
        "display": "Dr. António Pereira"
      }
    },
    {
      "mode": "professional",
      "time": "2022-06-08T10:49:00+02:00",
      "party": {
        "reference": "PractitionerRole/role-pereira-general-practice"
      }
    }
  ],
  "event": [{
    "code": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
        "code": "PCPR",
        "display": "care provision"
      }]
    }],
    "period": {
      "end": "2010-10-01"
    }
  }]
}
```

## UI Display Requirements

### Healthcare Team Section

The UI should display:

1. **Healthcare Professional Card (for each practitioner):**
   - Full name with prefix/suffix
   - Primary specialty
   - Medical license/registration number
   - Organization affiliation
   - Role-specific contact information
   - Languages spoken
   - Working hours/availability

2. **Organization Card (custodian):**
   - Organization name with logo (if available)
   - Organization type (hospital, clinic, etc.)
   - Full address with map link
   - Multiple contact methods (phone, fax, email, website)
   - Department/service information
   - Administrative contact person

3. **Healthcare Team Members:**
   - List of all document authors
   - Their roles in document creation
   - Timestamps of involvement
   - Legal authenticator designation

### Contact Person Section

1. **Emergency Contacts/Next of Kin:**
   - Relationship type (with proper SNOMED CT display)
   - Full contact information
   - Preferred contact method
   - Contact ranking/priority
   - Legal authority status (guardian, power of attorney)

2. **General Practitioner:**
   - GP name and specialty
   - Practice location
   - Contact information
   - Referral relationships

## Parser Enhancement Requirements

### Immediate Actions Needed

1. **Add PractitionerRole Resource Mapping:**
   ```python
   def _extract_practitioner_roles(self, practitioner_role_resources: List[Dict]) -> List[Dict[str, Any]]:
       """Extract PractitionerRole resources with specialty, organization, and availability"""
       # Map PractitionerRole.code, specialty, organization, location, telecom, availableTime
   ```

2. **Enhance Practitioner Mapping:**
   ```python
   # Add to _extract_healthcare_data():
   - qualification.issuer (organization reference)
   - qualification.period (validity dates)
   - communication (languages + proficiency)
   - photo (if available)
   ```

3. **Enhance Organization Mapping:**
   ```python
   # Add to _extract_healthcare_data():
   - partOf (parent organization)
   - contact array (administrative, billing contacts)
   - endpoint references
   - alias (organization aliases)
   ```

4. **Enhance RelatedPerson Mapping:**
   ```python
   # Add to _extract_emergency_contacts():
   - period (relationship period)
   - communication (languages)
   - birthDate
   - preferredContactMethod (derived from telecom.rank)
   ```

5. **Add Composition Attester Mapping:**
   ```python
   def _extract_document_attesters(self, composition: Dict) -> List[Dict[str, Any]]:
       """Extract legal and professional authenticators from Composition.attester"""
       # Map attester.mode, attester.time, attester.party
   ```

## Testing Checklist

### For Each Postman Endpoint:

- [ ] Resource validates against FHIR R4 specification
- [ ] All mandatory fields present
- [ ] Portuguese/European healthcare context preserved
- [ ] SNOMED CT codes use correct European edition
- [ ] Date formats follow ISO 8601
- [ ] Identifiers use correct Portuguese national systems
- [ ] Telecoms follow Portuguese format (+351...)
- [ ] Addresses use Portuguese postal code format
- [ ] Language codes use BCP 47 standard (pt, pt-PT, en)

### For Parser Implementation:

- [ ] All FHIR R4 fields mapped to Django models
- [ ] Template receives comprehensive data structure
- [ ] CDA compatibility preserved (backwards compatible)
- [ ] GDPR-compliant data handling (no Cyprus contamination)
- [ ] Logging captures all mapping failures
- [ ] Fallback mechanisms for missing data
- [ ] Type safety (DotDict conversions)

## Expected Benefits

After implementing complete mapping:

1. **Enhanced Clinical Context:**
   - Clear practitioner specialties visible in UI
   - Organization hierarchy displayed
   - Multiple contact methods available

2. **Improved User Experience:**
   - Professional-looking healthcare team cards
   - One-click contact options (call, email)
   - Map integration for addresses

3. **Regulatory Compliance:**
   - Complete audit trail (document authors, attesters)
   - Legal authenticator identification
   - Custodian organization clearly identified

4. **European Healthcare Standards:**
   - SNOMED CT specialty codes
   - National practitioner identifiers
   - Cross-border contact information

## Next Steps

1. **CDA to FHIR Converter AI Agent:**
   - Create Postman collection with all 5 endpoint examples
   - Validate against Diana Ferreira patient data
   - Ensure Portuguese healthcare context preserved

2. **Django NCP Development:**
   - Implement parser enhancements for PractitionerRole
   - Update template to display comprehensive data
   - Add collapsible sections for long lists

3. **Testing:**
   - Validate with multiple Portuguese hospital systems
   - Test cross-border scenarios (EU member states)
   - Verify GDPR compliance

---

**Status:** Requirements Defined ✅  
**Next:** Awaiting Postman endpoint creation from CDA to FHIR converter AI agent
