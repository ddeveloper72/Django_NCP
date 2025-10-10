#!/usr/bin/env python
"""
HAPI FHIR Connectivity Test Script
Test the new HAPI FHIR integration service for Django NCP

This script tests:
1. HAPI FHIR server connectivity
2. Patient Summary retrieval
3. Patient search functionality
4. FHIR Bundle processing
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

from eu_ncp_server.services.fhir_integration import hapi_fhir_service, HAPIFHIRIntegrationError
from eu_ncp_server.services.fhir_processing import fhir_processor, FHIRProcessingError


def test_hapi_fhir_connectivity():
    """Test basic connectivity to HAPI FHIR server"""
    print("=" * 60)
    print("TESTING HAPI FHIR SERVER CONNECTIVITY")
    print("=" * 60)
    
    try:
        connectivity_result = hapi_fhir_service.test_connectivity()
        
        print(f"Connection Status: {connectivity_result.get('status')}")
        print(f"Server Software: {connectivity_result.get('software_name')} {connectivity_result.get('software_version')}")
        print(f"FHIR Version: {connectivity_result.get('server_version')}")
        print(f"Base URL: {connectivity_result.get('base_url')}")
        print(f"Response Time: {connectivity_result.get('response_time_ms')}ms")
        print(f"Supported Resources: {len(connectivity_result.get('supported_resources', []))}")
        
        if connectivity_result.get('supported_resources'):
            print("\nAvailable Resource Types:")
            for resource_type in sorted(connectivity_result.get('supported_resources', [])[:10]):  # Show first 10
                print(f"  - {resource_type}")
            if len(connectivity_result.get('supported_resources', [])) > 10:
                print(f"  ... and {len(connectivity_result.get('supported_resources', [])) - 10} more")
        
        return connectivity_result.get('status') == 'connected'
        
    except Exception as e:
        print(f"❌ CONNECTIVITY TEST FAILED: {str(e)}")
        return False


def test_patient_search():
    """Test patient search functionality"""
    print("\n" + "=" * 60)
    print("TESTING PATIENT SEARCH")
    print("=" * 60)
    
    try:
        # Test basic patient search with common parameters
        search_params = {
            'name': 'test',
            'limit': '5'
        }
        
        print(f"Searching for patients with name containing 'test'...")
        search_results = hapi_fhir_service.search_patients(search_params)
        
        print(f"Total Results: {search_results.get('total', 0)}")
        print(f"Returned Patients: {len(search_results.get('patients', []))}")
        
        for i, patient in enumerate(search_results.get('patients', [])[:3]):  # Show first 3
            print(f"\nPatient {i+1}:")
            print(f"  ID: {patient.get('id')}")
            print(f"  Name: {patient.get('name')}")
            print(f"  Birth Date: {patient.get('birth_date', 'Unknown')}")
            print(f"  Gender: {patient.get('gender', 'Unknown')}")
        
        return True
        
    except HAPIFHIRIntegrationError as e:
        print(f"❌ PATIENT SEARCH FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR IN PATIENT SEARCH: {str(e)}")
        return False


def test_patient_summary_retrieval():
    """Test Patient Summary retrieval with a known patient ID"""
    print("\n" + "=" * 60)
    print("TESTING PATIENT SUMMARY RETRIEVAL")
    print("=" * 60)
    
    # Use patient ID from HAPI FHIR documentation
    test_patient_id = "4084299"  # Known patient ID from HAPI FHIR
    
    try:
        print(f"Retrieving Patient Summary for patient ID: {test_patient_id}")
        
        patient_summary = hapi_fhir_service.get_patient_summary(
            patient_id=test_patient_id,
            requesting_user="test_user"
        )
        
        print(f"Bundle Type: {patient_summary.get('resourceType')}")
        print(f"Bundle ID: {patient_summary.get('id')}")
        print(f"Total Resources: {patient_summary.get('total', len(patient_summary.get('entry', [])))}")
        print(f"Bundle Timestamp: {patient_summary.get('timestamp')}")
        
        # Show resource types in the bundle
        if patient_summary.get('entry'):
            resource_types = {}
            for entry in patient_summary.get('entry', []):
                resource_type = entry.get('resource', {}).get('resourceType')
                if resource_type:
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            
            print("\nResources in Patient Summary:")
            for resource_type, count in sorted(resource_types.items()):
                print(f"  - {resource_type}: {count}")
        
        return True
        
    except HAPIFHIRIntegrationError as e:
        print(f"❌ PATIENT SUMMARY RETRIEVAL FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR IN PATIENT SUMMARY: {str(e)}")
        return False


def test_fhir_processing():
    """Test FHIR resource processing capabilities"""
    print("\n" + "=" * 60)
    print("TESTING FHIR RESOURCE PROCESSING")
    print("=" * 60)
    
    try:
        # Create a simple test FHIR Bundle
        test_bundle = {
            'resourceType': 'Bundle',
            'id': 'test-bundle',
            'type': 'document',
            'timestamp': datetime.now().isoformat(),
            'total': 1,
            'entry': [
                {
                    'resource': {
                        'resourceType': 'Patient',
                        'id': 'test-patient',
                        'name': [{'family': 'Test', 'given': ['Patient']}],
                        'birthDate': '1980-01-01',
                        'gender': 'unknown'
                    }
                }
            ]
        }
        
        print("Processing test FHIR Bundle...")
        
        # Validate the bundle
        validation_result = fhir_processor.validate_fhir_bundle(test_bundle)
        print(f"Bundle Valid: {validation_result.get('valid', False)}")
        
        if validation_result.get('errors'):
            print("Validation Errors:")
            for error in validation_result.get('errors', []):
                print(f"  - {error}")
        
        # Process the bundle
        processed_summary = fhir_processor.parse_patient_summary_bundle(test_bundle)
        
        print(f"Processing Status: {processed_summary.get('status', 'unknown')}")
        print(f"Patient Name: {processed_summary.get('patient_info', {}).get('name', 'Unknown')}")
        
        return True
        
    except FHIRProcessingError as e:
        print(f"❌ FHIR PROCESSING FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR IN FHIR PROCESSING: {str(e)}")
        return False


def main():
    """Run all HAPI FHIR connectivity tests"""
    print("🔥 DJANGO NCP - HAPI FHIR INTEGRATION TEST SUITE")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Connectivity Test", test_hapi_fhir_connectivity),
        ("Patient Search Test", test_patient_search),
        ("Patient Summary Test", test_patient_summary_retrieval),
        ("FHIR Processing Test", test_fhir_processing)
    ]
    
    results = {}
    
    for test_name, test_function in tests:
        try:
            results[test_name] = test_function()
        except Exception as e:
            print(f"❌ {test_name.upper()} CRASHED: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! HAPI FHIR integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()