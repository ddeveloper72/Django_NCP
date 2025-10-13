# FHIR-CDA Architecture Separation Implementation Plan

## Overview
This branch implements a clean separation between FHIR and CDA processing paths to eliminate the hybrid processing issues that caused data loss and confusion in the patient view.

## Current Issues to Resolve
- ❌ **Multiple FHIR processors**: Competing FHIRAgentService vs FHIRBundleParser
- ❌ **Missing context data**: administrative_data not consistently passed to template
- ❌ **Confusing conditionals**: Multiple nested if statements in patient_cda_view
- ❌ **Data loss**: Context overwritten by competing processors
- ❌ **Hard debugging**: Unclear which processing path is taken

## Target Architecture

### 1. Router Function
```python
def patient_cda_view(request, session_id, cda_type=None):
    """
    Main entry point - routes to appropriate processor based on data source
    """
    match_data = get_session_match_data(session_id)
    data_source = match_data.get('data_source', 'CDA')
    
    if data_source == 'FHIR':
        return process_fhir_patient_view(request, session_id, match_data, cda_type)
    else:
        return process_cda_patient_view(request, session_id, match_data, cda_type)
```

### 2. Dedicated FHIR Processor
```python
def process_fhir_patient_view(request, session_id, match_data, cda_type):
    """
    DEDICATED FHIR PROCESSING PATH
    - Single consistent FHIR processor
    - FHIR-optimized context building
    - Guaranteed template data structure
    """
    # Implementation details in separate module
```

### 3. Dedicated CDA Processor  
```python
def process_cda_patient_view(request, session_id, match_data, cda_type):
    """
    DEDICATED CDA PROCESSING PATH
    - Single consistent CDA processor
    - CDA-optimized context building
    - Guaranteed template data structure
    """
    # Implementation details in separate module
```

## Implementation Phases

### Phase 1: Create Dedicated Processor Modules ✅ (This commit)
- Create `patient_data/view_processors/fhir_processor.py`
- Create `patient_data/view_processors/cda_processor.py`
- Create `patient_data/view_processors/context_builders.py`
- Create `patient_data/view_processors/__init__.py`

### Phase 2: Extract FHIR Processing Logic
- Move current FHIR processing from `patient_cda_view` to `fhir_processor.py`
- Implement unified FHIR context building
- Add comprehensive error handling
- Add debugging logs

### Phase 3: Extract CDA Processing Logic  
- Move current CDA processing from `patient_cda_view` to `cda_processor.py`
- Implement unified CDA context building
- Add comprehensive error handling
- Add debugging logs

### Phase 4: Implement Router Logic
- Replace current `patient_cda_view` with clean router function
- Add data source detection logic
- Add fallback handling

### Phase 5: Testing & Validation
- Test FHIR processing with Portuguese patient
- Test CDA processing with existing CDA documents
- Validate template compatibility
- Performance testing

### Phase 6: Cleanup & Documentation
- Remove old hybrid logic
- Update documentation
- Add architecture diagrams
- Code review and optimization

## Success Criteria

### ✅ Functional Requirements
- [ ] Portuguese FHIR patient displays correct organization data
- [ ] CDA patients continue to work as before
- [ ] No data loss in context passing
- [ ] Clear error messages for each path
- [ ] Consistent template data structure

### ✅ Technical Requirements
- [ ] Single responsibility for each processor
- [ ] No competing processors for same data type
- [ ] Clear execution path for debugging
- [ ] Maintainable code structure
- [ ] Future-proof for new features

### ✅ Quality Requirements
- [ ] Comprehensive test coverage
- [ ] Clear documentation
- [ ] Performance comparable to current implementation
- [ ] Backwards compatibility maintained

## Files to be Modified

### New Files (Phase 1)
- `patient_data/view_processors/__init__.py`
- `patient_data/view_processors/fhir_processor.py`
- `patient_data/view_processors/cda_processor.py`
- `patient_data/view_processors/context_builders.py`

### Modified Files (Later Phases)
- `patient_data/views.py` (router implementation)
- `patient_data/tests/` (test updates)
- Documentation files

## Benefits Expected

1. **🔍 Clear Debugging**: Know exactly which path is processing each request
2. **🛡️ Data Integrity**: Guaranteed context structure for templates
3. **⚡ Performance**: No competing processors or redundant operations
4. **🔧 Maintainability**: Easy to modify FHIR or CDA logic independently
5. **🚀 Future-Proof**: Easy to add new features to each path
6. **🧪 Testability**: Test each processor independently

## Risk Mitigation

- **Backwards Compatibility**: Keep existing function signatures during transition
- **Gradual Migration**: Implement router alongside existing logic initially
- **Comprehensive Testing**: Test all patient types before removing old logic
- **Rollback Plan**: Feature flag to switch between old and new architecture

---

**Branch**: `feature/fhir-cda-architecture-separation`
**Created**: October 13, 2025
**Target**: Clean separation of FHIR and CDA processing paths