# FHIR Implementation Roadmap
**Django_NCP FHIR Clinical Sections Rendering Plan**

---

## 1. Architecture Assessment ✅

### Current State Analysis

**Excellent Foundation Already in Place:**

Your architecture is **well-positioned** for FHIR integration:

```
Current Architecture:
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                             │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │  CDA L1/L3   │                    │ FHIR Bundles │       │
│  │  (Malta, IT) │                    │ (IE, PT)     │       │
│  └──────┬───────┘                    └──────┬───────┘       │
│         │                                    │               │
│         ▼                                    ▼               │
│  ┌──────────────┐                    ┌──────────────┐       │
│  │CDAProcessor  │                    │FHIRProcessor │       │
│  │ (ACTIVE ✅)  │                    │ (PARTIAL ⚠️) │       │
│  └──────┬───────┘                    └──────┬───────┘       │
│         │                                    │               │
│         └─────────────┬──────────────────────┘               │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │ Unified Context │                            │
│              │    Builder      │                            │
│              └────────┬────────┘                            │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │  Terminology    │                            │
│              │    Service      │                            │
│              └────────┬────────┘                            │
│                       │                                      │
│                       ▼                                      │
│              ┌─────────────────┐                            │
│              │ Django Templates│                            │
│              │  (enhanced_     │                            │
│              │   patient_cda)  │                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

**What You Have:**
- ✅ **Modular Services**: CDA parsers, FHIR parsers already separated
- ✅ **Unified Context Builder**: `context_builders.py` handles both CDA/FHIR
- ✅ **Clinical Section Pipeline**: Specialized extractors in `clinical_sections/`
- ✅ **View Processors**: Dedicated `fhir_processor.py` and `cda_processor.py`
- ✅ **Template Architecture**: Reusable clinical section components
- ✅ **Terminology Integration**: CTS service ready for both sources

**What's Missing:**
- ⚠️ **FHIR Clinical Section Extractors**: Need FHIR-specific section services
- ⚠️ **FHIR → Common Format**: Normalize FHIR resources to shared schema
- ⚠️ **Template Integration**: Wire FHIR data into existing templates
- ⚠️ **Testing Pipeline**: Validate FHIR bundles before UI integration

---

## 2. Design Pattern: Unified Clinical Section Interface

### Proposed Architecture Pattern

**Key Insight**: Your CDA clinical sections already use a **common interface** that FHIR can adopt.

```python
# Common Clinical Section Interface (already implemented for CDA)
{
    "section_id": "allergies",           # Unified identifier
    "title": "Allergies",                # Display title
    "section_code": "48765-2",           # LOINC code
    "has_entries": True,                 # Has clinical data
    "clinical_table": {                  # Structured data
        "entries": [...],
        "columns": [...],
        "display_config": {...}
    },
    "original_text_html": "...",         # Narrative content
    "clinical_codes": [...],             # Coded concepts
    "is_coded_section": True,            # Has terminology codes
}
```

**Strategy**: Create **FHIR adapters** that transform FHIR resources into this common format.

```
FHIR Resources                 Common Format              Templates
┌──────────────┐              ┌──────────────┐         ┌──────────────┐
│AllergyInto-  │              │              │         │allergies_    │
│lerance       │──────────────▶│  Normalized  │────────▶│section.html  │
│              │ FHIR Adapter │  Section     │         │              │
└──────────────┘              │  Data        │         └──────────────┘
                              │              │
┌──────────────┐              │  - section_id│         ┌──────────────┐
│Medication    │──────────────▶│  - entries  │────────▶│medications_  │
│Statement     │ FHIR Adapter │  - codes    │         │section.html  │
└──────────────┘              │  - metadata │         └──────────────┘
                              └──────────────┘
```

---

## 3. Implementation Plan

### Phase 1: FHIR Section Extractors (Week 1-2)

**Goal**: Create FHIR-specific clinical section services that mirror CDA extractors.

#### Step 1.1: Create FHIR Section Base Class

**File**: `patient_data/services/clinical_sections/base/fhir_section_base.py`

```python
"""
FHIR Section Base Service
Base class for FHIR R4 resource extraction following Django_NCP patterns
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FHIRSectionEntry:
    """Common FHIR section entry format (matches CDA pattern)"""
    entry_id: str
    display_text: str
    coded_concepts: List[Dict[str, Any]]
    clinical_status: Optional[str] = None
    onset_date: Optional[str] = None
    recorded_date: Optional[str] = None
    recorder: Optional[str] = None
    notes: Optional[List[str]] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    fhir_resource_reference: Optional[str] = None


class FHIRSectionServiceBase:
    """
    Base service for extracting clinical sections from FHIR resources
    Follows Django_NCP service layer pattern
    """
    
    def __init__(self):
        self.section_id: str = "unknown"
        self.section_title: str = "Unknown Section"
        self.section_code: str = None
        self.fhir_resource_type: str = None
    
    def extract_section(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract clinical section from FHIR bundle
        Returns normalized section data matching CDA format
        """
        # Find relevant resources in bundle
        resources = self._find_resources_in_bundle(fhir_bundle)
        
        if not resources:
            return self._create_empty_section()
        
        # Extract entries from resources
        entries = []
        for resource in resources:
            entry = self._extract_entry_from_resource(resource)
            if entry:
                entries.append(asdict(entry))
        
        # Build section data structure
        return {
            "section_id": self.section_id,
            "title": self.section_title,
            "section_code": self.section_code,
            "has_entries": len(entries) > 0,
            "entry_count": len(entries),
            "clinical_table": {
                "entries": entries,
                "columns": self._get_table_columns(),
                "display_config": self._get_display_config()
            },
            "clinical_codes": self._extract_all_codes(entries),
            "is_coded_section": self._has_coded_data(entries),
            "fhir_resource_type": self.fhir_resource_type,
            "data_source": "FHIR",
        }
    
    def _find_resources_in_bundle(self, fhir_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find resources of specific type in FHIR bundle"""
        resources = []
        entries = fhir_bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            if resource.get("resourceType") == self.fhir_resource_type:
                resources.append(resource)
        
        return resources
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """
        Extract entry from FHIR resource (to be implemented by subclasses)
        Subclasses MUST override this method
        """
        raise NotImplementedError("Subclasses must implement _extract_entry_from_resource")
    
    def _get_table_columns(self) -> List[str]:
        """Get table column configuration for this section"""
        return ["display_text", "onset_date", "clinical_status"]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """Get display configuration for this section"""
        return {
            "show_timeline": False,
            "show_severity": False,
            "show_status": True,
            "enable_filtering": True,
        }
    
    def _extract_all_codes(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all coded concepts from entries"""
        codes = []
        for entry in entries:
            codes.extend(entry.get("coded_concepts", []))
        return codes
    
    def _has_coded_data(self, entries: List[Dict[str, Any]]) -> bool:
        """Check if entries contain coded data"""
        return any(entry.get("coded_concepts") for entry in entries)
    
    def _create_empty_section(self) -> Dict[str, Any]:
        """Create empty section structure"""
        return {
            "section_id": self.section_id,
            "title": self.section_title,
            "has_entries": False,
            "entry_count": 0,
            "clinical_table": {"entries": [], "columns": [], "display_config": {}},
            "clinical_codes": [],
            "is_coded_section": False,
            "fhir_resource_type": self.fhir_resource_type,
        }
```

#### Step 1.2: Implement Specialized FHIR Extractors

**File Structure**:
```
patient_data/services/clinical_sections/extractors/
├── fhir_allergies_extractor.py
├── fhir_medications_extractor.py
├── fhir_conditions_extractor.py
├── fhir_procedures_extractor.py
├── fhir_observations_extractor.py
└── fhir_immunizations_extractor.py
```

**Example**: `fhir_allergies_extractor.py`

```python
"""
FHIR Allergies Section Extractor
Extracts AllergyIntolerance resources from FHIR bundles
"""

from typing import Dict, Any, List, Optional
from .base.fhir_section_base import FHIRSectionServiceBase, FHIRSectionEntry
import logging

logger = logging.getLogger(__name__)


class FHIRAllergiesExtractor(FHIRSectionServiceBase):
    """Extract allergies from FHIR R4 AllergyIntolerance resources"""
    
    def __init__(self):
        super().__init__()
        self.section_id = "allergies"
        self.section_title = "Allergies and Intolerances"
        self.section_code = "48765-2"  # LOINC: Allergies
        self.fhir_resource_type = "AllergyIntolerance"
    
    def _extract_entry_from_resource(self, resource: Dict[str, Any]) -> Optional[FHIRSectionEntry]:
        """Extract allergy entry from AllergyIntolerance resource"""
        try:
            # Extract basic info
            allergy_id = resource.get("id", "unknown")
            
            # Get allergen code and display text
            code_data = resource.get("code", {})
            coding = code_data.get("coding", [{}])[0]
            allergen_display = coding.get("display") or code_data.get("text", "Unknown allergen")
            
            # Extract coded concepts
            coded_concepts = self._extract_coded_concepts(resource)
            
            # Get clinical status
            clinical_status = resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code")
            
            # Get verification status
            verification_status = resource.get("verificationStatus", {}).get("coding", [{}])[0].get("code")
            
            # Get onset date
            onset_date = resource.get("onsetDateTime") or resource.get("onsetString")
            
            # Get recorded date
            recorded_date = resource.get("recordedDate")
            
            # Get severity
            criticality = resource.get("criticality")  # low, high, unable-to-assess
            
            # Get reaction details
            reactions = self._extract_reactions(resource)
            
            # Build display text
            display_text = f"{allergen_display}"
            if criticality:
                display_text += f" ({criticality})"
            
            # Get notes
            notes = []
            for note in resource.get("note", []):
                notes.append(note.get("text", ""))
            
            return FHIRSectionEntry(
                entry_id=allergy_id,
                display_text=display_text,
                coded_concepts=coded_concepts,
                clinical_status=f"{clinical_status}/{verification_status}",
                onset_date=onset_date,
                recorded_date=recorded_date,
                notes=notes,
                severity=criticality,
                category=resource.get("category", [None])[0],
                fhir_resource_reference=f"AllergyIntolerance/{allergy_id}"
            )
            
        except Exception as e:
            logger.error(f"Error extracting allergy entry: {e}")
            return None
    
    def _extract_coded_concepts(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all coded concepts from AllergyIntolerance resource"""
        codes = []
        
        # Main allergen code
        code_data = resource.get("code", {})
        for coding in code_data.get("coding", []):
            codes.append({
                "code": coding.get("code"),
                "system": coding.get("system"),
                "display": coding.get("display"),
                "system_name": self._get_system_name(coding.get("system")),
            })
        
        # Reaction manifestation codes
        for reaction in resource.get("reaction", []):
            manifestation = reaction.get("manifestation", [])
            for manifest in manifestation:
                for coding in manifest.get("coding", []):
                    codes.append({
                        "code": coding.get("code"),
                        "system": coding.get("system"),
                        "display": coding.get("display"),
                        "system_name": self._get_system_name(coding.get("system")),
                        "type": "reaction"
                    })
        
        return codes
    
    def _extract_reactions(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract reaction details"""
        reactions = []
        for reaction in resource.get("reaction", []):
            reactions.append({
                "manifestation": [m.get("text") for m in reaction.get("manifestation", [])],
                "severity": reaction.get("severity"),
                "onset": reaction.get("onset")
            })
        return reactions
    
    def _get_system_name(self, system: str) -> str:
        """Get human-readable system name"""
        system_map = {
            "http://snomed.info/sct": "SNOMED CT",
            "http://www.whocc.no/atc": "ATC",
            "http://loinc.org": "LOINC",
            "http://hl7.org/fhir/sid/icd-10": "ICD-10",
        }
        return system_map.get(system, system)
    
    def _get_table_columns(self) -> List[str]:
        """Columns for allergy table display"""
        return ["display_text", "onset_date", "clinical_status", "severity"]
    
    def _get_display_config(self) -> Dict[str, Any]:
        """Display configuration for allergies section"""
        return {
            "show_timeline": True,
            "show_severity": True,
            "show_status": True,
            "enable_filtering": True,
            "severity_colors": {
                "high": "danger",
                "low": "warning",
                "unable-to-assess": "secondary"
            }
        }
```

#### Step 1.3: Create FHIR Pipeline Manager

**File**: `patient_data/services/clinical_sections/pipeline/fhir_pipeline_manager.py`

```python
"""
FHIR Clinical Section Pipeline Manager
Coordinates extraction of all clinical sections from FHIR bundles
"""

from typing import Dict, Any, List
import logging

from ..extractors.fhir_allergies_extractor import FHIRAllergiesExtractor
from ..extractors.fhir_medications_extractor import FHIRMedicationsExtractor
from ..extractors.fhir_conditions_extractor import FHIRConditionsExtractor
from ..extractors.fhir_procedures_extractor import FHIRProceduresExtractor
from ..extractors.fhir_observations_extractor import FHIRObservationsExtractor
from ..extractors.fhir_immunizations_extractor import FHIRImmunizationsExtractor

logger = logging.getLogger(__name__)


class FHIRPipelineManager:
    """
    Manages extraction of clinical sections from FHIR bundles
    Mirrors CDA pipeline manager pattern
    """
    
    def __init__(self):
        """Initialize FHIR extractors"""
        self.extractors = {
            "allergies": FHIRAllergiesExtractor(),
            "medications": FHIRMedicationsExtractor(),
            "conditions": FHIRConditionsExtractor(),
            "procedures": FHIRProceduresExtractor(),
            "observations": FHIRObservationsExtractor(),
            "immunizations": FHIRImmunizationsExtractor(),
        }
        
        logger.info(f"[FHIR PIPELINE] Initialized with {len(self.extractors)} extractors")
    
    def process_fhir_bundle(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process FHIR bundle and extract all clinical sections
        
        Args:
            fhir_bundle: FHIR R4 Bundle resource
            
        Returns:
            Dictionary with clinical sections and metadata
        """
        logger.info("[FHIR PIPELINE] Processing FHIR bundle")
        
        sections = []
        clinical_arrays = {}
        
        for section_id, extractor in self.extractors.items():
            try:
                logger.info(f"[FHIR PIPELINE] Processing section: {section_id}")
                
                # Extract section
                section_data = extractor.extract_section(fhir_bundle)
                
                if section_data.get("has_entries"):
                    sections.append(section_data)
                    clinical_arrays[section_id] = section_data["clinical_table"]["entries"]
                    
                    logger.info(f"[FHIR PIPELINE] Section {section_id}: {section_data['entry_count']} entries")
                else:
                    logger.info(f"[FHIR PIPELINE] Section {section_id}: No entries")
                    
            except Exception as e:
                logger.error(f"[FHIR PIPELINE] Error processing section {section_id}: {e}")
        
        return {
            "sections": sections,
            "clinical_arrays": clinical_arrays,
            "sections_count": len(sections),
            "total_entries": sum(s.get("entry_count", 0) for s in sections),
        }
    
    def get_available_sections(self) -> List[str]:
        """Get list of available section extractors"""
        return list(self.extractors.keys())
```

---

### Phase 2: Integration with View Processor (Week 2)

#### Step 2.1: Update FHIR View Processor

**File**: `patient_data/view_processors/fhir_processor.py` (UPDATE)

```python
# Add FHIR pipeline import
from ..services.clinical_sections.pipeline.fhir_pipeline_manager import FHIRPipelineManager

class FHIRViewProcessor:
    """Dedicated FHIR bundle processor for patient view rendering"""
    
    def __init__(self):
        """Initialize FHIR processor with required services"""
        self.fhir_parser = FHIRBundleParser()
        self.fhir_agent = FHIRAgentService()
        self.context_builder = ContextBuilder()
        self.fhir_pipeline = FHIRPipelineManager()  # ✅ NEW
    
    def _build_fhir_context(
        self, 
        context: Dict[str, Any], 
        parsed_data: Dict[str, Any], 
        match_data: Dict[str, Any]
    ) -> None:
        """Build template context from parsed FHIR data"""
        
        # Get raw FHIR bundle for pipeline processing
        fhir_bundle = match_data.get('fhir_bundle')
        
        # Process clinical sections through FHIR pipeline
        pipeline_result = self.fhir_pipeline.process_fhir_bundle(fhir_bundle)
        
        # Merge pipeline results into context
        context['sections'] = pipeline_result['sections']
        context['clinical_arrays'] = pipeline_result['clinical_arrays']
        context['sections_count'] = pipeline_result['sections_count']
        
        # Add patient demographic data
        patient_identity = parsed_data.get('patient_identity', {})
        if patient_identity:
            self.context_builder.add_patient_data(context, patient_identity)
        
        # ... rest of existing code
```

---

### Phase 3: Template Integration (Week 3)

#### Step 3.1: Verify Template Compatibility

**The good news**: Your existing templates already support the data format!

**File**: `templates/patient_data/sections/clinical_section_router.html`

This template routes based on `section_id` and expects:
- `section.title`
- `section.has_entries`
- `section.clinical_table.entries`
- `section.clinical_codes`

✅ **Your FHIR extractors provide exactly this format!**

#### Step 3.2: Add FHIR-Specific Template Enhancements (Optional)

**File**: `templates/patient_data/components/fhir_resource_badge.html`

```django
{# FHIR Resource Type Badge Component #}
{% if fhir_resource_type %}
<span class="badge bg-info ms-2" title="FHIR Resource Type">
    <i class="fa-solid fa-code me-1"></i>
    {{ fhir_resource_type }}
</span>
{% endif %}
```

**Update**: `templates/patient_data/sections/enhanced_clinical_section_optimized.html`

```django
{# Add FHIR badge if data source is FHIR #}
{% if section.data_source == 'FHIR' %}
    {% include 'patient_data/components/fhir_resource_badge.html' with fhir_resource_type=section.fhir_resource_type %}
{% endif %}
```

---

### Phase 4: Terminology Integration (Week 3-4)

#### Step 4.1: Update CTS Integration Service

**File**: `patient_data/services/clinical_sections/cts_integration.py` (UPDATE)

```python
class CTSIntegrationService:
    """Integrate CTS terminology lookups for both CDA and FHIR"""
    
    def enrich_clinical_section(self, section: Dict[str, Any], data_source: str = "CDA") -> Dict[str, Any]:
        """
        Enrich clinical section with terminology lookups
        
        Args:
            section: Clinical section data (CDA or FHIR format)
            data_source: "CDA" or "FHIR"
        
        Returns:
            Enriched section with terminology translations
        """
        # Extract coded concepts
        codes = section.get("clinical_codes", [])
        
        if not codes:
            logger.debug(f"[CTS] No codes to enrich in section {section.get('section_id')}")
            return section
        
        # Lookup codes via CTS
        enriched_codes = []
        for code_data in codes:
            # CTS lookup (same for both CDA and FHIR!)
            translation = self.cts_client.lookup_code(
                code=code_data.get("code"),
                code_system=code_data.get("system")
            )
            
            if translation:
                code_data["translated_display"] = translation.get("display_name")
                code_data["preferred_term"] = translation.get("preferred_term")
            
            enriched_codes.append(code_data)
        
        section["clinical_codes"] = enriched_codes
        section["cts_enriched"] = True
        
        return section
```

---

## 4. Testing Strategy

### Phase 5: Testing & Validation (Week 4)

#### Test 1: FHIR Bundle Validation

**File**: `tests/test_fhir_extractors.py`

```python
"""Test FHIR clinical section extractors"""

import pytest
import json
from patient_data.services.clinical_sections.extractors.fhir_allergies_extractor import FHIRAllergiesExtractor
from patient_data.services.clinical_sections.pipeline.fhir_pipeline_manager import FHIRPipelineManager


def load_test_bundle(country: str) -> dict:
    """Load test FHIR bundle"""
    with open(f"test_data/fhir_bundles/{country}_patient_summary.json") as f:
        return json.load(f)


def test_allergies_extractor_irish_bundle():
    """Test allergies extraction from Irish FHIR bundle"""
    # Load Irish bundle
    bundle = load_test_bundle("IE")
    
    # Extract allergies
    extractor = FHIRAllergiesExtractor()
    section = extractor.extract_section(bundle)
    
    # Assertions
    assert section["section_id"] == "allergies"
    assert section["has_entries"] is True
    assert section["entry_count"] > 0
    assert "clinical_table" in section
    assert len(section["clinical_codes"]) > 0


def test_pipeline_manager_portuguese_bundle():
    """Test full pipeline on Portuguese FHIR bundle"""
    # Load Portuguese bundle
    bundle = load_test_bundle("PT")
    
    # Process through pipeline
    pipeline = FHIRPipelineManager()
    result = pipeline.process_fhir_bundle(bundle)
    
    # Assertions
    assert result["sections_count"] > 0
    assert "allergies" in result["clinical_arrays"]
    assert "medications" in result["clinical_arrays"]


def test_section_format_compatibility():
    """Test that FHIR sections match CDA format"""
    bundle = load_test_bundle("IE")
    
    extractor = FHIRAllergiesExtractor()
    section = extractor.extract_section(bundle)
    
    # Required keys for template compatibility
    required_keys = [
        "section_id", "title", "has_entries", "clinical_table",
        "clinical_codes", "is_coded_section"
    ]
    
    for key in required_keys:
        assert key in section, f"Missing required key: {key}"
```

#### Test 2: View Integration Test

**File**: `tests/test_fhir_view_integration.py`

```python
"""Test FHIR view processor integration"""

import pytest
from django.test import RequestFactory
from patient_data.view_processors.fhir_processor import FHIRViewProcessor


@pytest.mark.django_db
def test_fhir_view_processor(client, irish_fhir_session):
    """Test FHIR view processor with Irish bundle"""
    processor = FHIRViewProcessor()
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get(f'/patients/fhir/{irish_fhir_session}/')
    request.session = {
        f'patient_match_{irish_fhir_session}': {
            'fhir_bundle': load_test_bundle("IE")
        }
    }
    
    # Process view
    response = processor.process_fhir_document(request, irish_fhir_session)
    
    # Assertions
    assert response.status_code == 200
    assert 'sections' in response.context_data
    assert 'clinical_arrays' in response.context_data
```

---

## 5. Implementation Roadmap

### Week 1: Foundation
- [ ] Create `FHIRSectionServiceBase` class
- [ ] Implement `FHIRAllergiesExtractor`
- [ ] Implement `FHIRMedicationsExtractor`
- [ ] Write unit tests for extractors

### Week 2: Core Extractors
- [ ] Implement remaining extractors (Conditions, Procedures, Observations, Immunizations)
- [ ] Create `FHIRPipelineManager`
- [ ] Integrate pipeline with `FHIRViewProcessor`
- [ ] Test with Irish FHIR bundle

### Week 3: Template Integration
- [ ] Verify template compatibility
- [ ] Add FHIR-specific badges/indicators
- [ ] Test rendering with Portuguese FHIR bundle
- [ ] Fix any template formatting issues

### Week 4: Terminology & Polish
- [ ] Integrate CTS for FHIR codes
- [ ] Add comprehensive logging
- [ ] Write integration tests
- [ ] Documentation updates

---

## 6. Key Design Decisions

### Decision 1: Reuse Templates vs. Create New Ones

**✅ RECOMMENDATION: Reuse Existing Templates**

**Rationale**:
- Your CDA templates already support the data structure
- Clinical sections are **domain-agnostic** (allergies are allergies, whether from CDA or FHIR)
- Reduces maintenance burden
- **Add FHIR badges for visual distinction**, not separate templates

### Decision 2: Normalization Strategy

**✅ RECOMMENDATION: Normalize at Service Layer**

**Pattern**:
```
FHIR Resources → FHIR Extractors → Common Section Format → Templates
CDA Documents  → CDA Extractors  → Common Section Format → Templates
```

**NOT**:
```
FHIR Resources → Templates (duplicates CDA logic)
```

### Decision 3: Terminology Service

**✅ RECOMMENDATION: Single CTS Integration Point**

Your CTS service should be **data-source agnostic**:
```python
def lookup_code(code: str, system: str) -> Dict:
    """Works for both CDA and FHIR codes"""
    # SNOMED, LOINC, ATC codes are the same regardless of source!
```

---

## 7. Success Criteria

**FHIR implementation is successful when:**

✅ Irish FHIR bundle displays clinical sections in UI
✅ Portuguese FHIR bundle displays clinical sections in UI
✅ Clinical section format matches CDA sections (seamless user experience)
✅ Terminology lookups work for FHIR codes
✅ Tests pass for all extractors and view integration
✅ No code duplication between CDA and FHIR pipelines
✅ Logging provides clear FHIR processing visibility

---

## 8. Next Steps

### Immediate Action (Today):

1. **Review this roadmap** - Confirm architecture aligns with your vision
2. **Prioritize extractors** - Which clinical sections are most important?
3. **Choose test bundle** - Irish or Portuguese for first implementation?

### This Week:

1. **Create base classes** - `FHIRSectionServiceBase` foundation
2. **Implement 1-2 extractors** - Start with Allergies + Medications
3. **Test with real bundle** - Validate against Irish/Portuguese data

### Ready to Start?

**Would you like me to:**
- 🔨 Start implementing the base classes and first extractor?
- 📊 Analyze your Irish/Portuguese FHIR bundles to validate the design?
- 🧪 Create test scripts to validate your existing FHIR data?
- 📝 Generate more detailed specifications for specific extractors?

**Let's get the FHIR pipeline operational!** 🚀
