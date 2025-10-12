#!/usr/bin/env python3
"""
Improved FHIR vs CDA View Processing Architecture

Suggests a cleaner separation between FHIR and CDA processing paths
to avoid the confusion and data loss issues we've been experiencing.
"""

def suggested_patient_view_architecture():
    """
    Suggested improved architecture for patient_cda_view that clearly separates
    FHIR and CDA processing paths to avoid data loss and confusion.
    """
    
    print("🏗️  SUGGESTED IMPROVED VIEW ARCHITECTURE")
    print("=" * 60)
    
    architecture_suggestion = """
# IMPROVED patient_cda_view ARCHITECTURE

def patient_cda_view(request, session_id, cda_type=None):
    '''
    CLEANER ARCHITECTURE: Separate FHIR and CDA processing paths
    '''
    
    # 1. DETERMINE DATA SOURCE TYPE
    match_data = get_session_match_data(session_id)
    data_source = match_data.get('data_source', 'CDA')
    
    # 2. ROUTE TO APPROPRIATE PROCESSOR
    if data_source == 'FHIR':
        return process_fhir_patient_view(request, session_id, match_data, cda_type)
    else:
        return process_cda_patient_view(request, session_id, match_data, cda_type)


def process_fhir_patient_view(request, session_id, match_data, cda_type):
    '''
    DEDICATED FHIR PROCESSING PATH
    - Uses FHIRBundleParser or FHIRAgentService consistently
    - Builds context specifically for FHIR data
    - Returns template with FHIR-optimized context
    '''
    
    try:
        # SINGLE FHIR PROCESSING PATH (no multiple competing paths)
        fhir_bundle = match_data.get('fhir_bundle')
        if not fhir_bundle:
            return handle_fhir_error(request, "No FHIR bundle found")
        
        # Use consistent FHIR processor
        fhir_processor = FHIRBundleParser()  # OR FHIRAgentService() - pick ONE
        parsed_data = fhir_processor.parse_patient_summary_bundle(fhir_bundle)
        
        if not parsed_data or not parsed_data.get('success'):
            return handle_fhir_error(request, "FHIR bundle parsing failed")
        
        # BUILD FHIR-SPECIFIC CONTEXT
        context = build_fhir_context(parsed_data, session_id, match_data)
        
        # CRITICAL: Ensure all required template data is included
        context.update({
            'data_source': 'FHIR',
            'patient_data': parsed_data.get('patient_identity', {}),
            'administrative_data': parsed_data.get('administrative_data', {}),  # CRITICAL FOR ORGANIZATION DATA
            'healthcare_data': parsed_data.get('healthcare_data', {}),
            'contact_data': parsed_data.get('contact_data', {}),
            'clinical_arrays': parsed_data.get('clinical_arrays', {}),
            'sections': parsed_data.get('sections', []),
            # ... other FHIR-specific context
        })
        
        return render(request, 'patient_data/enhanced_patient_cda.html', context)
        
    except Exception as e:
        logger.error(f"FHIR processing error: {e}")
        return handle_fhir_error(request, str(e))


def process_cda_patient_view(request, session_id, match_data, cda_type):
    '''
    DEDICATED CDA PROCESSING PATH  
    - Uses CDADisplayService consistently
    - Builds context specifically for CDA data
    - Returns template with CDA-optimized context
    '''
    
    try:
        # SINGLE CDA PROCESSING PATH
        cda_content = get_cda_content(match_data, cda_type)
        if not cda_content:
            return handle_cda_error(request, "No CDA content found")
        
        # Use consistent CDA processor
        cda_processor = CDADisplayService()
        parsed_data = cda_processor.extract_patient_clinical_data(session_id)
        
        # BUILD CDA-SPECIFIC CONTEXT
        context = build_cda_context(parsed_data, session_id, match_data, cda_content)
        
        context.update({
            'data_source': 'CDA',
            'cda_content': cda_content,
            'cda_type': cda_type,
            # ... other CDA-specific context
        })
        
        return render(request, 'patient_data/enhanced_patient_cda.html', context)
        
    except Exception as e:
        logger.error(f"CDA processing error: {e}")
        return handle_cda_error(request, str(e))


# BENEFITS OF THIS ARCHITECTURE:
# 1. CLEAR SEPARATION: No confusion between FHIR and CDA processing
# 2. SINGLE RESPONSIBILITY: Each function handles one data type
# 3. CONSISTENT PROCESSING: No competing/conflicting processors
# 4. EASIER DEBUGGING: Clear path for each data source
# 5. TEMPLATE COMPATIBILITY: Guaranteed context structure
# 6. ERROR HANDLING: Specific error handling for each path
# 7. MAINTAINABILITY: Easy to modify FHIR or CDA logic independently

"""
    
    print(architecture_suggestion)
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("1. ✅ **Single responsibility**: Each function handles one data type")
    print("2. ✅ **No competing processors**: One FHIR path, one CDA path")  
    print("3. ✅ **Guaranteed context**: Template always gets required data")
    print("4. ✅ **Clear error handling**: Specific errors for each path")
    print("5. ✅ **Easy debugging**: Clear execution path")
    print("6. ✅ **Future-proof**: Easy to add new features to each path")
    
    print("\n🔧 CURRENT ISSUES RESOLVED:")
    print("❌ **Multiple FHIR processors**: Competing FHIRAgentService vs FHIRBundleParser")
    print("❌ **Missing context data**: administrative_data not passed to template")
    print("❌ **Confusing conditionals**: Multiple nested if statements") 
    print("❌ **Data loss**: Context overwritten by competing processors")
    print("❌ **Hard debugging**: Unclear which path is taken")
    
    print("\n💡 IMPLEMENTATION STRATEGY:")
    print("1. **Phase 1**: Extract current FHIR processing into dedicated function")
    print("2. **Phase 2**: Extract current CDA processing into dedicated function") 
    print("3. **Phase 3**: Create router function that chooses the right processor")
    print("4. **Phase 4**: Test both paths independently")
    print("5. **Phase 5**: Remove old hybrid logic")

if __name__ == "__main__":
    suggested_patient_view_architecture()