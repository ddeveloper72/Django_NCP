# Dual-View Clinical Data Architecture Plan

**Date**: October 30, 2025  
**Purpose**: Design architecture for displaying both CTS-translated data AND original narrative text  
**Goal**: Enable clinicians to toggle between universal clinical language and country-of-origin narrative

---

## 🎯 User Requirements

### Primary View (Default)
- **Display**: CTS-translated SNOMED code descriptions
- **Language**: Clinician's preferred language (e.g., English)
- **Source**: CTS (Concept Translation Service)
- **Example**: "Implantation of heart assist system"

### Secondary View (Toggle)
- **Display**: Original narrative text from CDA document
- **Language**: Country of origin language (e.g., Portuguese)
- **Source**: CDA `<text>` narrative section
- **Example**: "Implantação de sistema de assistência cardíaca"

### UI Interaction
```html
<!-- Default view -->
<div class="procedure-name">Implantation of heart assist system</div>
<span class="translation-badge">Translated via CTS</span>

<!-- Toggle button -->
<button class="btn-toggle-original">View Original Text</button>

<!-- After toggle -->
<div class="procedure-name original-language">Implantação de sistema de assistência cardíaca</div>
<span class="language-badge">Portuguese (PT)</span>
```

---

## ❌ Why Original Fix Won't Work

### My Proposed Fix (WRONG)
```python
# Filter out procedures without names
good_procedures = [p for p in clinical_arrays['procedures'] 
                  if p.get('name') or p.get('display_name')]
```

**Problem**: This discards procedures from EnhancedCDAXMLParser which have SNOMED codes but no names

**Result**: We lose the codes needed for CTS translation! ❌

---

## ✅ Correct Architecture: Data Merging Strategy

### Step 1: Identify Dual Sources

**Source 1: ProceduresSectionService** (Specialized)
- **Extracts**: Narrative text from `<text><reference value="#pro-1"/></text>`
- **Has**: Procedure names ✅
- **Missing**: SNOMED codes (partially - needs enhancement)

**Source 2: EnhancedCDAXMLParser** (Generic)
- **Extracts**: Structured code from `<code codeSystem="..." code="64253000">`
- **Has**: SNOMED codes ✅
- **Missing**: Display names (by design - should come from CTS)

### Step 2: Match and Merge

**Matching Strategy**: Use procedure date + position in document

```python
def merge_procedure_sources(narrative_procs, coded_procs):
    """Merge narrative and coded procedures into unified structure"""
    merged = []
    
    # Match procedures by date and document order
    for i, narrative_proc in enumerate(narrative_procs):
        matched_code_proc = None
        
        # Try to find corresponding coded procedure
        if i < len(coded_procs):
            coded_proc = coded_procs[i]
            # Verify dates match (if available)
            if narrative_proc.get('date') == coded_proc.get('date'):
                matched_code_proc = coded_proc
        
        # Create unified procedure entry
        merged_proc = {
            # SNOMED Code (for CTS)
            'procedure_code': matched_code_proc.get('code') if matched_code_proc else None,
            'code_system': matched_code_proc.get('codeSystem') if matched_code_proc else None,
            
            # Original Narrative (country language)
            'narrative_text': narrative_proc.get('name'),
            'narrative_language': 'pt-PT',  # Extract from CDA language attribute
            'narrative_reference': narrative_proc.get('text_reference'),
            
            # CTS Translation (will be populated)
            'cts_display_name': None,  # Populated by CTS service
            'cts_language': 'en-US',   # Clinician's language
            
            # Clinical Data
            'procedure_date': narrative_proc.get('date'),
            'status': narrative_proc.get('status'),
            'target_site': narrative_proc.get('target_site'),
            'laterality': narrative_proc.get('laterality'),
            
            # Metadata
            'has_code': matched_code_proc is not None,
            'has_narrative': True,
            'source': 'merged'
        }
        
        merged.append(merged_proc)
    
    return merged
```

---

## 🏗️ Implementation Plan

### Phase 1: Enhance ProceduresSectionService (CRITICAL)

**File**: `patient_data/services/clinical_sections/specialized/procedures_service.py`

**Current State** (Line 272):
```python
procedure_code = code_elem.get('code')
code_system = code_elem.get('codeSystem')
```

**✅ Good**: Already extracts codes from structured `<code>` element

**Issue**: Not clear if these are being preserved through the data flow

**Action Required**:
1. ✅ Verify code extraction (already working)
2. ✅ Verify narrative extraction (already working)
3. ❌ Add language detection from CDA document
4. ❌ Preserve both in unified structure

**Enhanced Method**:
```python
def _parse_procedure_element(self, procedure_elem, document_language='en-US') -> Dict[str, Any]:
    """Parse procedure with both code and narrative preservation"""
    
    # Extract SNOMED code (already working)
    code_elem = procedure_elem.find('hl7:code', self.namespaces)
    procedure_code = code_elem.get('code') if code_elem is not None else None
    code_system = code_elem.get('codeSystem') if code_elem is not None else None
    
    # Extract narrative reference (already working)
    text_elem = procedure_elem.find('hl7:text', self.namespaces)
    narrative_ref = None
    if text_elem is not None:
        ref_elem = text_elem.find('hl7:reference', self.namespaces)
        if ref_elem is not None:
            narrative_ref = ref_elem.get('value', '').replace('#', '')
    
    # NEW: Extract originalText reference for narrative
    original_text_ref = None
    if code_elem is not None:
        original_text = code_elem.find('hl7:originalText', self.namespaces)
        if original_text is not None:
            ref_elem = original_text.find('hl7:reference', self.namespaces)
            if ref_elem is not None:
                original_text_ref = ref_elem.get('value', '').replace('#', '')
    
    return {
        # Structured code data (for CTS)
        'procedure_code': procedure_code,
        'code_system': code_system,
        'code_system_name': 'SNOMED CT' if code_system == '2.16.840.1.113883.6.96' else None,
        
        # Narrative data (original language)
        'narrative_reference': narrative_ref or original_text_ref,
        'narrative_text': None,  # Will be resolved from narrative_mapping
        'narrative_language': document_language,
        
        # Other clinical data...
        'date': ...
        'status': ...
        'target_site': ...
    }
```

### Phase 2: Add Document Language Detection

**File**: `patient_data/services/clinical_sections/specialized/procedures_service.py`

**Method**: Extract from CDA header

```python
def _extract_document_language(self, root) -> str:
    """Extract language code from CDA document header"""
    try:
        # CDA language is in <ClinicalDocument> element
        lang_code = root.get('lang', 'en-US')  # Default to English
        
        # Or check <languageCode> element
        lang_elem = root.find('hl7:languageCode', self.namespaces)
        if lang_elem is not None:
            lang_code = lang_elem.get('code', 'en-US')
        
        return lang_code
    except:
        return 'en-US'  # Safe default
```

**Integration**:
```python
def extract_from_cda(self, cda_content: str) -> List[Dict[str, Any]]:
    """Extract procedures with language detection"""
    root = etree.fromstring(cda_content.encode('utf-8'))
    
    # Extract document language ONCE
    document_language = self._extract_document_language(root)
    
    # Find procedures section
    section = self._find_section_by_code(root, ['47519-4'])
    
    if section is not None:
        # Pass language to parser
        procedures = self._parse_procedures_xml(section, document_language)
        return procedures
```

### Phase 3: Remove Deduplication Filter from Comprehensive Service

**File**: `patient_data/services/comprehensive_clinical_data_service.py`

**Current Issue** (from restore point): Line 629 needs fix

**WRONG Approach**:
```python
# DON'T DO THIS - loses codes!
good_procedures = [p for p in clinical_arrays['procedures'] 
                  if p.get('name') or p.get('display_name')]
```

**CORRECT Approach**:
```python
# NO FILTER NEEDED if ProceduresSectionService extracts both codes and narratives
# Just use the procedures from specialized service
clinical_arrays['procedures'] = specialized_procedures
```

**Action**: 
- ❌ Do NOT add filter at line 629
- ✅ Verify ProceduresSectionService is canonical source
- ✅ Disable EnhancedCDAXMLParser procedure extraction (or use as fallback only)

### Phase 4: Add CTS Translation Service

**New File**: `patient_data/services/cts_translation_service.py`

```python
class CTSTranslationService:
    """Service for translating SNOMED CT codes via CTS"""
    
    def __init__(self):
        self.cache = {}  # In-memory cache
        # Later: Use Django cache or database
    
    def translate_procedure_code(self, snomed_code: str, target_language: str) -> Dict[str, Any]:
        """
        Translate SNOMED CT code to display name
        
        Args:
            snomed_code: SNOMED CT code (e.g., "64253000")
            target_language: Target language code (e.g., "en-US")
        
        Returns:
            Dict with translation details
        """
        cache_key = f"{snomed_code}:{target_language}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # TODO: Call actual CTS API
            # For now, return placeholder
            translation = {
                'code': snomed_code,
                'display_name': f"CTS Translation for {snomed_code}",
                'language': target_language,
                'translation_date': timezone.now().isoformat(),
                'source': 'CTS',
                'success': True
            }
            
            # Cache result
            self.cache[cache_key] = translation
            return translation
            
        except Exception as e:
            logger.error(f"CTS translation failed for {snomed_code}: {e}")
            return {
                'code': snomed_code,
                'display_name': None,
                'language': target_language,
                'source': 'CTS',
                'success': False,
                'error': str(e)
            }
    
    def translate_procedures_batch(self, procedures: List[Dict], target_language: str) -> List[Dict]:
        """Translate multiple procedures"""
        for procedure in procedures:
            code = procedure.get('procedure_code')
            if code:
                translation = self.translate_procedure_code(code, target_language)
                procedure['cts_display_name'] = translation.get('display_name')
                procedure['cts_translation_date'] = translation.get('translation_date')
                procedure['cts_success'] = translation.get('success')
        
        return procedures
```

### Phase 5: Update Template for Dual View

**File**: `templates/patient_data/clinical_sections/procedures_section_new.html`

```django
{% for procedure in procedures.items %}
<div class="procedure-card" data-procedure-id="{{ forloop.counter }}">
    <div class="procedure-header">
        <!-- Primary Display: CTS Translation -->
        <h5 class="procedure-name cts-view" data-view="cts">
            {% if procedure.cts_display_name %}
                {{ procedure.cts_display_name }}
                <span class="badge badge-info">
                    <i class="fa-solid fa-language"></i> Translated
                </span>
            {% elif procedure.narrative_text %}
                {{ procedure.narrative_text }}
                <span class="badge badge-warning">
                    <i class="fa-solid fa-exclamation-triangle"></i> CTS Unavailable
                </span>
            {% else %}
                Unknown Procedure
            {% endif %}
        </h5>
        
        <!-- Secondary Display: Original Narrative (hidden by default) -->
        <h5 class="procedure-name narrative-view d-none" data-view="narrative">
            {% if procedure.narrative_text %}
                {{ procedure.narrative_text }}
                <span class="badge badge-secondary">
                    <i class="fa-solid fa-flag"></i> {{ procedure.narrative_language|upper }}
                </span>
            {% else %}
                No original text available
            {% endif %}
        </h5>
        
        <!-- Toggle Button -->
        <button class="btn btn-sm btn-outline-primary toggle-view-btn" 
                data-procedure-id="{{ forloop.counter }}">
            <i class="fa-solid fa-language"></i> 
            <span class="toggle-text">View Original</span>
        </button>
    </div>
    
    <div class="procedure-details">
        <!-- SNOMED Code (always visible for clinical staff) -->
        {% if procedure.procedure_code %}
        <div class="clinical-code">
            <strong>SNOMED CT:</strong> {{ procedure.procedure_code }}
            <span class="text-muted">({{ procedure.code_system_name }})</span>
        </div>
        {% endif %}
        
        <!-- Procedure Date -->
        <div class="procedure-date">
            <strong>Date:</strong> {{ procedure.procedure_date }}
        </div>
        
        <!-- Other fields... -->
    </div>
</div>
{% endfor %}

<script>
// Toggle between CTS and narrative view
document.querySelectorAll('.toggle-view-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const procedureId = this.dataset.procedureId;
        const card = this.closest('.procedure-card');
        const ctsView = card.querySelector('.cts-view');
        const narrativeView = card.querySelector('.narrative-view');
        const toggleText = this.querySelector('.toggle-text');
        
        if (ctsView.classList.contains('d-none')) {
            // Show CTS view
            ctsView.classList.remove('d-none');
            narrativeView.classList.add('d-none');
            toggleText.textContent = 'View Original';
        } else {
            // Show narrative view
            ctsView.classList.add('d-none');
            narrativeView.classList.remove('d-none');
            toggleText.textContent = 'View Translation';
        }
    });
});
</script>
```

---

## 📊 Data Structure Evolution

### Current State (Broken)
```python
clinical_arrays['procedures'] = [
    # From ProceduresSectionService (3 procedures with names, no codes)
    {'name': 'Implantation of heart assist system', 'date': '2014-10-20'},
    {'name': 'Cesarean section', 'date': '2012-04-14'},
    {'name': 'Thyroidectomy', 'date': '1997-06-05'},
    
    # From EnhancedCDAXMLParser (3 procedures with codes, no names)
    {'code': '64253000', 'codeSystem': '2.16.840.1.113883.6.96'},
    {'code': '11466000', 'codeSystem': '2.16.840.1.113883.6.96'},
    {'code': '13619001', 'codeSystem': '2.16.840.1.113883.6.96'},
]
# Result: 6 procedures instead of 3
```

### Target State (Fixed)
```python
clinical_arrays['procedures'] = [
    {
        # SNOMED Code (for CTS)
        'procedure_code': '64253000',
        'code_system': '2.16.840.1.113883.6.96',
        'code_system_name': 'SNOMED CT',
        
        # Original Narrative (Portuguese)
        'narrative_text': 'Implantação de sistema de assistência cardíaca',
        'narrative_language': 'pt-PT',
        'narrative_reference': '#pro-1',
        
        # CTS Translation (English)
        'cts_display_name': 'Implantation of heart assist system',
        'cts_language': 'en-US',
        'cts_translation_date': '2025-10-30T09:00:00Z',
        'cts_success': True,
        
        # Clinical Data
        'procedure_date': '2014-10-20',
        'status': 'completed',
        'target_site': {
            'code': '76552005',
            'display_name': 'skin structure of shoulder',
            'laterality': 'Left'
        },
        
        # Metadata
        'has_code': True,
        'has_narrative': True,
        'source': 'procedures_service',
        'data': {...}  # Original raw data for debugging
    },
    # ... 2 more procedures
]
# Result: 3 procedures with complete dual-view data
```

---

## 🔍 Investigation Required

### Question 1: Is ProceduresService Already Extracting Codes?

**File**: `procedures_service.py` line 272
```python
procedure_code = code_elem.get('code')
```

**Status**: ✅ YES, it extracts codes

**Question**: Are they being preserved in `enhance_and_store()`?

**Check**: Line 123
```python
'procedure_code': get_value(procedure_data, 'procedure_code'),
```

**Status**: ✅ YES, they're preserved

**Conclusion**: ProceduresSectionService already has the codes! We just need to verify they're not being lost downstream.

### Question 2: Why Are We Getting "Not specified" for Codes?

From restore point:
> Good procedures show "Not specified" for procedure_code

**Hypothesis**: Field mapper is wrapping codes in display_value structure
```python
"procedure_code": {"display_value": "Not specified", "value": ""}
```

**Investigation Needed**: Check `clinical_field_mapper.py` line 220-240 (already has dict handling fix)

---

## ✅ Summary: What NOT to Do

1. ❌ **Don't filter out procedures without names** - loses codes
2. ❌ **Don't discard EnhancedCDAXMLParser output** - may need as fallback
3. ❌ **Don't use narrative text as sole source** - lacks SNOMED codes for CTS

## ✅ Summary: What TO Do

1. ✅ **Verify ProceduresSectionService extracts BOTH codes and narratives**
2. ✅ **Add document language detection** from CDA header
3. ✅ **Preserve original narrative text** with language tag
4. ✅ **Implement CTS translation service** for code-to-name conversion
5. ✅ **Update template** with dual-view toggle
6. ✅ **Test with multiple EU member states** (PT, MT, GR, etc.)

---

## 🎯 Next Actions (Priority Order)

1. **Investigate Current State** (30 minutes)
   - Check if ProceduresSectionService codes are reaching the template
   - Add debug logging to trace data flow
   - Verify field mapper isn't corrupting codes

2. **Add Document Language Detection** (1 hour)
   - Implement `_extract_document_language()` method
   - Pass language through to `_parse_procedure_element()`
   - Store language in procedure data structure

3. **Design CTS Integration** (2 hours)
   - Create `CTSTranslationService` class
   - Implement caching strategy
   - Add fallback for CTS failures

4. **Update Template** (2 hours)
   - Add dual-view UI components
   - Implement toggle JavaScript
   - Style with SCSS standards

5. **Testing** (2 hours)
   - Test with Portuguese patient (Diana Ross)
   - Test with Maltese patient (Mario Borg)
   - Verify language detection works

---

**Total Estimated Time**: 7.5 hours

**Ready to Start**: After verifying current code extraction status
