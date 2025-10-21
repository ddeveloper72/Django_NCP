"""
Enhanced FHIR Integration Example

Shows how to integrate the ChatGPT-recommended FHIR enhancements into our
existing Django views and services. This example demonstrates the recommended
workflow:

1. fhir.resources → strict validation and Python object models
2. fhir-kindling → bundle traversal + CRUD convenience  
3. FHIRPath-py → rich querying for UI rendering
4. Terminology service integration → semantic rigor

Usage:
    from patient_data.services.enhanced_fhir_integration import EnhancedFHIRIntegration
    
    # In your view
    integrator = EnhancedFHIRIntegration()
    result = integrator.process_fhir_for_ui(fhir_bundle_data)
"""

import logging
from typing import Dict, List, Optional, Any, Union

from .enhanced_fhir_service import EnhancedFHIRService, FHIRPathQueryService
from .fhir_bundle_service import FHIRBundleService

logger = logging.getLogger(__name__)


class EnhancedFHIRIntegration:
    """
    Integration service combining ChatGPT recommendations with existing infrastructure.
    
    This service demonstrates how to layer the enhanced capabilities onto our
    existing FHIR processing while maintaining backward compatibility.
    """
    
    def __init__(self):
        self.enhanced_service = EnhancedFHIRService()
        self.fhirpath_service = FHIRPathQueryService()
        self.legacy_service = FHIRBundleService()
        
    def process_fhir_for_ui(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """
        Process FHIR bundle for UI display using enhanced capabilities.
        
        This method demonstrates the ChatGPT-recommended workflow:
        1. Strict validation with fhir.resources
        2. Rich data extraction
        3. FHIRPath queries for UI components
        4. Fallback to legacy processing if needed
        """
        try:
            # Step 1: Enhanced processing with validation
            enhanced_result = self.enhanced_service.parse_fhir_bundle_enhanced(bundle_data)
            
            if not enhanced_result.get('success'):
                logger.warning("[ENHANCED FHIR INTEGRATION] Enhanced processing failed, using fallback")
                return self._fallback_processing(bundle_data)
            
            # Step 2: Generate UI component data using FHIRPath
            ui_components = self._generate_ui_components(bundle_data)
            
            # Step 3: Merge enhanced data with UI components
            integrated_result = {
                'patient_summary': enhanced_result['enhanced_data'],
                'ui_components': ui_components,
                'validation_results': enhanced_result.get('validation_results', {}),
                'processing_metadata': enhanced_result.get('processing_metadata', {}),
                'integration_type': 'enhanced',
                'success': True
            }
            
            logger.info("[ENHANCED FHIR INTEGRATION] Successfully processed with enhanced capabilities")
            return integrated_result
            
        except Exception as e:
            logger.error(f"[ENHANCED FHIR INTEGRATION] Error in enhanced processing: {str(e)}")
            return self._fallback_processing(bundle_data)
    
    def _generate_ui_components(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """Generate UI component data using FHIRPath queries."""
        if isinstance(bundle_data, str):
            import json
            bundle_dict = json.loads(bundle_data)
        else:
            bundle_dict = bundle_data
        
        ui_components = {}
        
        # UI components from ChatGPT example
        component_types = [
            'patient_name',
            'patient_family', 
            'patient_id',
            'medication_names',
            'condition_names',
            'allergy_substances',
            'vital_signs'
        ]
        
        for component_type in component_types:
            result = self.fhirpath_service.query_for_ui_component(bundle_dict, component_type)
            ui_components[component_type] = result
        
        return ui_components
    
    def _fallback_processing(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """Fallback to legacy FHIR processing."""
        try:
            legacy_result = self.legacy_service.parse_fhir_bundle(bundle_data)
            return {
                'patient_summary': legacy_result.get('patient_summary', {}),
                'ui_components': {},
                'validation_results': {'fallback': True},
                'processing_metadata': {'fallback_used': True},
                'integration_type': 'legacy',
                'success': legacy_result.get('success', False)
            }
        except Exception as e:
            logger.error(f"[ENHANCED FHIR INTEGRATION] Fallback processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'integration_type': 'failed'
            }
    
    def validate_fhir_compliance(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """
        Perform comprehensive FHIR compliance validation.
        
        Implements ChatGPT recommendation for structural + semantic validation.
        """
        try:
            # Enhanced validation using the new service
            enhanced_result = self.enhanced_service.parse_fhir_bundle_enhanced(bundle_data)
            
            if enhanced_result.get('success'):
                validation_results = enhanced_result.get('validation_results', {})
                return {
                    'structural_validation': validation_results.get('structural_validation', 'UNKNOWN'),
                    'semantic_validation': validation_results.get('semantic_validation', {}),
                    'compliance_checks': validation_results.get('compliance_checks', []),
                    'warnings': validation_results.get('warnings', []),
                    'validation_type': 'enhanced',
                    'success': True
                }
            else:
                return {
                    'structural_validation': 'FAILED',
                    'error': 'Enhanced validation failed',
                    'validation_type': 'enhanced',
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"[ENHANCED FHIR INTEGRATION] Validation error: {str(e)}")
            return {
                'structural_validation': 'ERROR',
                'error': str(e),
                'validation_type': 'enhanced',
                'success': False
            }
    
    def extract_for_clinical_display(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """
        Extract FHIR data specifically formatted for clinical display.
        
        This method shows how to use FHIRPath for clinical workflow optimization.
        """
        if isinstance(bundle_data, str):
            import json
            bundle_dict = json.loads(bundle_data)
        else:
            bundle_dict = bundle_data
        
        clinical_display = {
            'patient_header': {},
            'clinical_summary': {},
            'medication_summary': {},
            'alert_conditions': {}
        }
        
        # Patient header for clinical view
        patient_name = self.fhirpath_service.query_for_ui_component(bundle_dict, 'patient_name')
        patient_family = self.fhirpath_service.query_for_ui_component(bundle_dict, 'patient_family')
        patient_id = self.fhirpath_service.query_for_ui_component(bundle_dict, 'patient_id')
        
        clinical_display['patient_header'] = {
            'name': patient_name.get('result', []),
            'family': patient_family.get('result', []),
            'id': patient_id.get('result', [])
        }
        
        # Medication summary for quick reference
        medications = self.fhirpath_service.query_for_ui_component(bundle_dict, 'medication_names')
        clinical_display['medication_summary'] = {
            'count': len(medications.get('result', [])),
            'names': medications.get('result', [])
        }
        
        # Key conditions for clinical attention
        conditions = self.fhirpath_service.query_for_ui_component(bundle_dict, 'condition_names')
        clinical_display['clinical_summary'] = {
            'condition_count': len(conditions.get('result', [])),
            'conditions': conditions.get('result', [])
        }
        
        # Allergies for safety alerts
        allergies = self.fhirpath_service.query_for_ui_component(bundle_dict, 'allergy_substances')
        clinical_display['alert_conditions'] = {
            'allergy_count': len(allergies.get('result', [])),
            'substances': allergies.get('result', [])
        }
        
        return clinical_display


def integrate_enhanced_fhir_in_view(bundle_data: Union[str, dict]) -> Dict[str, Any]:
    """
    Example function showing how to integrate enhanced FHIR processing in Django views.
    
    This demonstrates the ChatGPT-recommended workflow in a Django context.
    """
    integrator = EnhancedFHIRIntegration()
    
    # Process bundle with enhanced capabilities
    result = integrator.process_fhir_for_ui(bundle_data)
    
    if result.get('success'):
        # Enhanced processing succeeded
        context_data = {
            'patient_data': result['patient_summary'],
            'ui_components': result['ui_components'],
            'validation_status': result['validation_results'],
            'processing_type': 'enhanced_fhir',
            'fhir_compliance': 'validated'
        }
        
        # Add clinical display data
        clinical_display = integrator.extract_for_clinical_display(bundle_data)
        context_data['clinical_display'] = clinical_display
        
        return context_data
    else:
        # Fallback or error occurred
        return {
            'patient_data': result.get('patient_summary', {}),
            'processing_type': result.get('integration_type', 'unknown'),
            'error': result.get('error'),
            'fhir_compliance': 'not_validated'
        }


# Example usage patterns for different scenarios

def example_medication_focus_view(bundle_data: Union[str, dict]) -> Dict[str, Any]:
    """Example: Focus on medication data extraction using FHIRPath."""
    integrator = EnhancedFHIRIntegration()
    
    # Use FHIRPath for targeted medication queries
    if isinstance(bundle_data, str):
        import json
        bundle_dict = json.loads(bundle_data)
    else:
        bundle_dict = bundle_data
    
    medication_data = integrator.fhirpath_service.query_for_ui_component(bundle_dict, 'medication_names')
    
    return {
        'medication_focus': True,
        'medications': medication_data.get('result', []),
        'query_used': medication_data.get('query'),
        'success': medication_data.get('success', False)
    }


def example_validation_focus_view(bundle_data: Union[str, dict]) -> Dict[str, Any]:
    """Example: Focus on FHIR validation and compliance."""
    integrator = EnhancedFHIRIntegration()
    
    validation_result = integrator.validate_fhir_compliance(bundle_data)
    
    return {
        'validation_focus': True,
        'compliance_status': validation_result.get('structural_validation'),
        'warnings': validation_result.get('warnings', []),
        'checks_passed': validation_result.get('compliance_checks', []),
        'validation_success': validation_result.get('success', False)
    }