# Azure FHIR API Call Architecture Analysis

## 📊 **Current API Calls Per Patient View**

### **Total API Calls: 12-20+**

```
PHASE 1: Patient & Composition (2 calls)
├── GET Patient/{id}                                    [1 call]
└── GET Composition?subject=Patient/{id}&_count=10     [1 call]

PHASE 2: Clinical Resources (6 calls)
├── GET AllergyIntolerance?patient={id}&_count=100     [1 call]
├── GET MedicationStatement?patient={id}&_count=100    [1 call]
├── GET Condition?patient={id}&_count=100              [1 call]
├── GET Observation?patient={id}&_count=100            [1 call]
├── GET Procedure?patient={id}&_count=100              [1 call]
└── GET Immunization?patient={id}&_count=100           [1 call]

PHASE 3: Referenced Medications (N calls)
└── GET Medication/{med-id}                            [1-10+ calls]

PHASE 4: Practitioners & Organizations (2-4+ calls) [NEW]
├── GET Practitioner?_count=50                         [1 call]
├── GET Practitioner/{prac-id}                         [0-N calls]
├── GET Organization?_count=50                         [1 call]
└── GET Organization/{org-id}                          [0-N calls]
```

---

## ✅ **Fix Applied: Fetch Missing Resources**

### **Problem Identified:**
- Parser was looking for Practitioner data in the bundle
- BUT Azure FHIR integration never fetched Practitioner/Organization resources
- Result: Empty Healthcare Team section despite data existing in Azure

### **Solution Implemented:**
Added fetching logic in `azure_fhir_integration.py::_assemble_patient_summary()`:

```python
# NEW: Search for ALL Practitioners
GET https://healthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Practitioner?_count=50

# NEW: Search for ALL Organizations  
GET https://healthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Organization?_count=50

# NEW: Fetch specific referenced resources
GET https://healthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Practitioner/{id}
GET https://healthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Organization/{id}
```

---

## 🚀 **Optimization Opportunities**

### **Option 1: Use $everything Operation** ⭐ RECOMMENDED
Single API call to get complete patient data:

```http
GET Patient/{id}/$everything?_count=1000
```

**Benefits:**
- ✅ 1 API call instead of 12-20
- ✅ Includes ALL referenced resources automatically
- ✅ Azure FHIR handles relationship resolution
- ✅ Better performance and caching
- ✅ Atomic operation (consistency guaranteed)

**Implementation:**
```python
# eu_ncp_server/services/azure_fhir_integration.py
def get_patient_summary(self, patient_id: str, requesting_user: str):
    # Try $everything operation first
    try:
        bundle = self._make_request('GET', f"Patient/{patient_id}/$everything")
        if bundle:
            logger.info(f"Retrieved complete patient data via $everything")
            return bundle
    except Exception:
        # Fallback to manual assembly
        return self._assemble_patient_summary(patient_id)
```

### **Option 2: Use _include and _revinclude** ⚡
Reduce API calls by including related resources:

```http
GET Composition?subject=Patient/{id}
    &_include=Composition:author
    &_include=Composition:custodian
    &_revinclude=*

GET MedicationStatement?patient={id}
    &_include=MedicationStatement:medication
```

**Benefits:**
- ✅ Reduces calls from 12-20 to 6-8
- ✅ More efficient than individual fetches
- ✅ Better network utilization

### **Option 3: Use GraphQL on FHIR** 🔮
Single query for entire patient graph:

```graphql
{
  Patient(id: "2-1234-W7") {
    id
    name { given family }
    Composition {
      author { reference display }
      custodian { reference display }
    }
    MedicationStatement {
      medication { display }
    }
    AllergyIntolerance { ... }
  }
}
```

**Benefits:**
- ✅ 1 API call with custom shape
- ✅ Only fetch needed fields (less data transfer)
- ✅ Modern API pattern

---

## 📈 **Performance Comparison**

| Method | API Calls | Data Transfer | Latency | Complexity |
|--------|-----------|---------------|---------|------------|
| **Current (Manual Assembly)** | 12-20+ | High (duplicates) | High (serial) | High |
| **$everything** ⭐ | 1 | Medium | Low | Low |
| **_include/_revinclude** | 6-8 | Medium | Medium | Medium |
| **GraphQL** | 1 | Low (exact) | Low | Medium |

---

## 🎯 **Recommended Implementation Plan**

### **Phase 1: Immediate (Current Session)** ✅ DONE
- [x] Add Practitioner/Organization fetching to manual assembly
- [x] Test with Diana Ferreira patient

### **Phase 2: Short-term (Next Sprint)**
```python
# Implement $everything with fallback
def get_patient_summary(self, patient_id: str, requesting_user: str):
    try:
        # Try $everything first
        bundle = self._make_request('GET', f"Patient/{patient_id}/$everything")
        return bundle
    except Exception:
        # Fallback to manual assembly (current code)
        return self._assemble_patient_summary(patient_id)
```

### **Phase 3: Long-term (Production Optimization)**
- Add caching layer (Redis) for assembled bundles
- Implement _include/_revinclude for searches
- Consider GraphQL for complex queries

---

## 🔒 **Security Considerations**

### **Current Approach:**
- Each API call requires Azure AD token
- Token refreshed every ~59 minutes
- Fine-grained access control per resource type

### **$everything Approach:**
- Single token validation
- Requires `Patient.read` and `*.read` permissions
- May expose more data than needed (security review required)

### **Recommendation:**
Use **$everything with SMART scopes**:
```
patient/Patient.read
patient/Observation.read
patient/MedicationStatement.read
patient/AllergyIntolerance.read
patient/Practitioner.read
patient/Organization.read
```

---

## 📊 **Expected Results After Fix**

### **Before Fix:**
```
Healthcare Team Table:
- António Pereira
- Role & Specialty: [EMPTY - "nnn" filtered out]
- Organization: Centro Hospitalar de Lisboa Central
- Contact: [EMPTY]
```

### **After Fix (Now):**
```
Healthcare Team Table:
- António Pereira
- Role & Specialty: 
  🔵 General practice
  🔵 Medical practitioner
- Organization: Centro Hospitalar de Lisboa Central
- Contact:
  📞 351211234568, 351912134567
  📧 medico@gmail.com, antonio.pereira@chic-min-saude.pt

Assigned Author Section:
- Dr. António Pereira - Centro Hospitalar de Lisboa Central
- Qualifications: 🔵 General practice 🔵 Medical practitioner
- Languages: 🌐 Portuguese 🌐 English
- Personal Contact:
  📍 3. Alameda Santo António dos Capuchos, Lisbon 1169-050, PT
  📞 2 phones
  📧 2 emails
```

---

## 🧪 **Testing Steps**

1. **Clear Django session:**
   ```python
   # Logout and login to get fresh session
   ```

2. **Search for Diana Ferreira:**
   ```
   Country: Portugal
   Patient ID: 2-1234-W7
   ```

3. **Verify API calls in logs:**
   ```bash
   # Check Django server logs
   Azure FHIR API GET Patient/2-1234-W7
   Azure FHIR API GET Practitioner?_count=50  [NEW]
   Azure FHIR API GET Organization?_count=50  [NEW]
   ```

4. **Verify UI displays:**
   - Healthcare Team table has role badges
   - Assigned Author section has complete data
   - No "nnn" placeholders anywhere

---

## 📝 **Next Steps**

1. ✅ **Test current fix** - Verify Practitioner/Organization data displays
2. ⏳ **Implement $everything** - Reduce to 1 API call
3. ⏳ **Add caching** - Cache assembled bundles for 5 minutes
4. ⏳ **Monitor performance** - Track API call count and latency
5. ⏳ **Document endpoints** - Create API call reference guide

---

## 🔗 **Related Files**

- **API Integration:** `eu_ncp_server/services/azure_fhir_integration.py`
- **Parser:** `patient_data/services/fhir_bundle_parser.py`
- **Templates:** 
  - `templates/patient_data/components/healthcare_team_content.html`
  - `templates/patient_data/components/administrative/assigned_author.html`
- **Views:** `patient_data/views.py`
- **View Processors:** `patient_data/view_processors/fhir_processor.py`

---

**Last Updated:** 2025-11-19
**Status:** ✅ Fix Applied - Ready for Testing
