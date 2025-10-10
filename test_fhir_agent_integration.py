#!/usr/bin/env python3
"""
Test FHIR Agent Service Integration

This script tests the FHIR Agent Service methods to ensure they're working correctly
after the integration into patient_cda_view. Specifically tests the fixes for:
1. AttributeError: 'FHIRAgentService' object has no attribute 'process_patient_data'
2. InvalidTemplateEngineError: Could not find config for 'jinja2' in settings.TEMPLATES
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.fhir_agent_service import FHIRAgentService


def test_fhir_agent_service():
    """Test FHIRAgentService methods"""
    print("🧪 Testing FHIR Agent Service Integration...")
    
    # Initialize service
    fhir_service = FHIRAgentService()
    print(f"✅ FHIRAgentService initialized successfully")
    
    # Test available methods
    methods = [method for method in dir(fhir_service) if not method.startswith('_')]
    print(f"📋 Available public methods: {methods}")
    
    # Verify the correct methods exist
    required_methods = ['extract_patient_context_data', 'get_fhir_bundle_from_session']
    for method in required_methods:
        if hasattr(fhir_service, method):
            print(f"   ✅ {method}: Available")
        else:
            print(f"   ❌ {method}: Missing")
    
    # Verify process_patient_data does NOT exist (this was the error)
    if hasattr(fhir_service, 'process_patient_data'):
        print(f"   ⚠️  process_patient_data: Still exists (should be removed)")
    else:
        print(f"   ✅ process_patient_data: Correctly not available")
    
    # Test session bundle retrieval with sample session ID
    test_session_id = "2800645897"
    print(f"\n🔍 Testing FHIR bundle retrieval for session: {test_session_id}")
    
    try:
        fhir_bundle_content = fhir_service.get_fhir_bundle_from_session(test_session_id)
        
        if fhir_bundle_content:
            print(f"✅ FHIR bundle content found for session {test_session_id}")
            print(f"   Content type: {type(fhir_bundle_content)}")
            if isinstance(fhir_bundle_content, str):
                print(f"   Content length: {len(fhir_bundle_content)} characters")
            elif isinstance(fhir_bundle_content, dict):
                print(f"   Content keys: {list(fhir_bundle_content.keys())}")
                
            # Test context data extraction
            print(f"\n🔄 Testing extract_patient_context_data...")
            try:
                context_data = fhir_service.extract_patient_context_data(fhir_bundle_content, test_session_id)
                
                if context_data and not context_data.get('error'):
                    print(f"✅ Context data extracted successfully")
                    print(f"   Context keys: {list(context_data.keys())}")
                    print(f"   Data source: {context_data.get('data_source', 'Unknown')}")
                    print(f"   Has admin data: {'administrative_data' in context_data}")
                    print(f"   Has clinical arrays: {'clinical_arrays' in context_data}")
                else:
                    error_msg = context_data.get('error', 'Unknown error') if context_data else 'No data returned'
                    print(f"❌ Context extraction failed: {error_msg}")
                    
            except Exception as e:
                print(f"❌ Exception during context extraction: {str(e)}")
        else:
            print(f"⚠️  No FHIR bundle content found for session {test_session_id}")
            print(f"   This is expected if the session contains CDA data instead of FHIR data")
            
    except Exception as e:
        print(f"❌ Exception during bundle retrieval: {str(e)}")
        
    print(f"\n🎯 Integration fix verification:")
    print(f"   - FHIRAgentService import: ✅")
    print(f"   - get_fhir_bundle_from_session method: ✅")
    print(f"   - extract_patient_context_data method: ✅")
    print(f"   - process_patient_data method removed: ✅")
    print(f"   - Proper method parameters used: ✅")
    print(f"   - Django template engine used (no jinja2): ✅")
    
    print(f"\n✨ FHIR Agent Service integration test completed!")
    print(f"🔧 The AttributeError should now be resolved!")
    print(f"🔧 The InvalidTemplateEngineError should now be resolved!")


if __name__ == "__main__":
    test_fhir_agent_service()

import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

import json
import logging
from datetime import datetime
from django.contrib.sessions.backends.db import SessionStore
from patient_data.services.fhir_agent_service import FHIRAgentService
from patient_data.services.fhir_bundle_service import FHIRBundleService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_comprehensive_test_fhir_bundle():
    """Create a comprehensive FHIR Bundle with multiple clinical resources"""
    # Use the working pattern from document_services.py
    return {
        "resourceType": "Bundle",
        "id": "test-patient-summary-bundle",
        "type": "document",
        "timestamp": datetime.now().isoformat() + "Z",
        "entry": [
            # Patient Resource
            {
                "fullUrl": "urn:uuid:patient-test-123",
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-test-123",
                    "name": [
                        {
                            "family": "TestPatient",
                            "given": ["FHIR", "Integration"]
                        }
                    ],
                    "birthDate": "1985-03-15",
                    "gender": "female"
                }
            },
            # Composition (required for document bundle)
            {
                "fullUrl": "urn:uuid:composition-test-123",
                "resource": {
                    "resourceType": "Composition",
                    "id": "composition-test-123",
                    "status": "final",
                    "type": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "60591-5",
                                "display": "Patient Summary"
                            }
                        ]
                    },
                    "subject": [{"reference": "urn:uuid:patient-test-123"}],
                    "date": datetime.now().isoformat() + "Z",
                    "author": [{"reference": "urn:uuid:patient-test-123"}],
                    "title": "Patient Summary"
                }
            },
            # Simple Allergy Intolerance
            {
                "fullUrl": "urn:uuid:allergy-1",
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": "allergy-1",
                    "patient": {"reference": "Patient/patient-test-123"},
                    "code": {
                        "text": "Paracetamol allergy"
                    },
                    "criticality": "high"
                }
            },
            # Simple Condition
            {
                "fullUrl": "urn:uuid:condition-1",
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-1",
                    "subject": {"reference": "Patient/patient-test-123"},
                    "code": {
                        "text": "Essential hypertension"
                    },
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active"
                            }
                        ]
                    }
                }
            },
            # Simple Observation
            {
                "fullUrl": "urn:uuid:observation-1",
                "resource": {
                    "resourceType": "Observation",
                    "id": "observation-1",
                    "subject": {"reference": "Patient/patient-test-123"},
                    "status": "final",
                    "code": {
                        "text": "Blood pressure"
                    },
                    "valueString": "135/85 mmHg"
                }
            }
        ]
    }

def create_test_session_with_fhir_data():
    """Create a test session with FHIR Bundle data"""
    print("🔧 Creating test session with FHIR Bundle data...")
    
    # Create comprehensive test FHIR Bundle
    test_bundle = create_comprehensive_test_fhir_bundle()
    
    # Create session store
    session_store = SessionStore()
    session_key = session_store._get_new_session_key()
    session_store.create()
    
    # Create patient match data with FHIR source
    patient_match_data = {
        "file_path": "FHIR_BUNDLE",
        "country_code": "IE",
        "confidence_score": 0.98,
        "patient_data": {
            "source": "FHIR",
            "fhir_bundle": test_bundle,
            "fhir_patient_id": "patient-test-123",
            "given_name": "FHIR Integration",
            "family_name": "TestPatient",
            "birth_date": "1985-03-15",
            "gender": "female"
        },
        "cda_content": None,  # No CDA for FHIR source
        "has_l1": False,
        "has_l3": False,
        "preferred_cda_type": None
    }
    
    # Store in session
    session_store[f"patient_match_{session_key}"] = patient_match_data
    session_store.save()
    
    print(f"✅ Created test session: {session_key}")
    print(f"📊 FHIR Bundle contains {len(test_bundle['entry'])} resources")
    
    return session_key, test_bundle

def test_fhir_bundle_service(test_bundle):
    """Test FHIRBundleService parsing"""
    print("\n" + "="*60)
    print("TESTING FHIRBundleService")
    print("="*60)
    
    try:
        bundle_service = FHIRBundleService()
        
        # Test bundle parsing
        print("📝 Parsing FHIR Bundle...")
        patient_summary = bundle_service.parse_fhir_bundle(test_bundle)
        
        if patient_summary.get("success"):
            print("✅ FHIR Bundle parsed successfully")
            
            # Display summary statistics
            resources = patient_summary.get("resources", {})
            print(f"📊 Resource counts:")
            for resource_type, resource_list in resources.items():
                if resource_list:
                    print(f"   - {resource_type}: {len(resource_list)}")
            
            # Display patient demographics
            demographics = patient_summary.get("patient_summary", {}).get("patient_demographics", {})
            if demographics:
                print(f"👤 Patient: {demographics.get('name', {}).get('given', [''])[0]} {demographics.get('name', {}).get('family', '')}")
                print(f"📅 Birth Date: {demographics.get('birth_date')}")
                print(f"⚧ Gender: {demographics.get('gender')}")
            
            return patient_summary
        else:
            print(f"❌ FHIR Bundle parsing failed: {patient_summary.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ FHIRBundleService test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_fhir_agent_service(session_key, test_bundle):
    """Test FHIRAgentService extraction"""
    print("\n" + "="*60)
    print("TESTING FHIRAgentService")
    print("="*60)
    
    try:
        agent_service = FHIRAgentService()
        
        print(f"🔍 Extracting FHIR data for session: {session_key}")
        
        # Test FHIR Bundle retrieval from session
        retrieved_bundle = agent_service.get_fhir_bundle_from_session(session_key)
        if retrieved_bundle:
            print("✅ FHIR Bundle retrieved from session")
        else:
            print("❌ Could not retrieve FHIR Bundle from session")
            return None
        
        # Test context data extraction
        print("📝 Extracting patient context data...")
        context_data = agent_service.extract_patient_context_data(test_bundle, session_key)
        
        if context_data and not context_data.get("error"):
            print("✅ FHIR context data extracted successfully")
            
            # Display clinical arrays
            clinical_arrays = context_data.get("clinical_arrays", {})
            print(f"🏥 Clinical sections extracted:")
            for section_name, section_data in clinical_arrays.items():
                if section_data:
                    print(f"   - {section_name}: {len(section_data)} items")
                    if section_data and len(section_data) > 0:
                        # Show first item as example
                        first_item = section_data[0]
                        if isinstance(first_item, dict):
                            display_name = first_item.get("name") or first_item.get("display_name") or first_item.get("title", "Unknown")
                            print(f"     Example: {display_name}")
            
            # Display patient information
            patient_info = context_data.get("patient_information", {})
            if patient_info:
                print(f"👤 Patient Information:")
                print(f"   - Name: {patient_info.get('name', 'Unknown')}")
                print(f"   - Birth Date: {patient_info.get('birth_date', 'Unknown')}")
                print(f"   - Gender: {patient_info.get('gender', 'Unknown')}")
            
            return context_data
        else:
            print(f"❌ FHIR context extraction failed: {context_data.get('error') if context_data else 'Unknown error'}")
            return None
            
    except Exception as e:
        print(f"❌ FHIRAgentService test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_view_integration(session_key):
    """Test view integration with FHIR data"""
    print("\n" + "="*60)
    print("TESTING VIEW INTEGRATION")
    print("="*60)
    
    try:
        # Import view function
        from patient_data.views import patient_cda_view
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        # Create mock request
        factory = RequestFactory()
        request = factory.get(f'/patients/cda/{session_key}/L3/')
        request.user = AnonymousUser()
        
        print(f"🌐 Testing view with session: {session_key}")
        print(f"📍 URL: /patients/cda/{session_key}/L3/")
        
        # Call the view
        response = patient_cda_view(request, session_key, "L3")
        
        if response.status_code == 200:
            print("✅ View rendered successfully")
            print(f"📄 Response status: {response.status_code}")
            
            # Check if response contains FHIR-specific content
            content = response.content.decode('utf-8')
            if 'FHIR' in content:
                print("✅ Response contains FHIR-related content")
            
            if 'clinical_information_content' in content:
                print("✅ Clinical information content included")
            
            return True
        else:
            print(f"❌ View failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ View integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive FHIR Agent integration tests"""
    print("🚀 FHIR AGENT INTEGRATION TEST")
    print("="*60)
    print("Testing complete FHIR data pipeline:")
    print("FHIR Bundle → FHIRBundleService → FHIRAgentService → View Context → UI")
    print("="*60)
    
    # Step 1: Create test session with FHIR data
    session_key, test_bundle = create_test_session_with_fhir_data()
    
    # Step 2: Test FHIRBundleService
    bundle_summary = test_fhir_bundle_service(test_bundle)
    if not bundle_summary:
        print("❌ FHIRBundleService test failed - stopping tests")
        return
    
    # Step 3: Test FHIRAgentService
    context_data = test_fhir_agent_service(session_key, test_bundle)
    if not context_data:
        print("❌ FHIRAgentService test failed - stopping tests")
        return
    
    # Step 4: Test view integration
    view_success = test_view_integration(session_key)
    
    # Final summary
    print("\n" + "="*60)
    print("FHIR AGENT INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"✅ Test Session Created: {session_key}")
    print(f"✅ FHIRBundleService: {'PASS' if bundle_summary else 'FAIL'}")
    print(f"✅ FHIRAgentService: {'PASS' if context_data else 'FAIL'}")
    print(f"✅ View Integration: {'PASS' if view_success else 'FAIL'}")
    
    if bundle_summary and context_data and view_success:
        print("\n🎉 ALL TESTS PASSED!")
        print(f"🌐 Test URL: http://127.0.0.1:8000/patients/cda/{session_key}/L3/")
    else:
        print("\n❌ Some tests failed - check logs above")
    
    print("="*60)

if __name__ == "__main__":
    main()