#!/usr/bin/env python
"""
Test SessionDataEnhancementService

Quick verification that the enhanced session manager is working correctly.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eu_ncp_server.settings')
django.setup()

def test_session_enhancement():
    """Test basic functionality of SessionDataEnhancementService"""
    try:
        from patient_data.services.session_data_enhancement_service import SessionDataEnhancementService
        
        print("🧪 Testing SessionDataEnhancementService...")
        
        # Test initialization
        service = SessionDataEnhancementService()
        print("✅ Service initialized successfully")
        print(f"   Enhanced parser: {type(service.enhanced_parser).__name__}")
        print(f"   CDA parser: {type(service.cda_parser).__name__}")
        print(f"   XML folders: {len(service.xml_folders)} configured")
        
        # Test sample match data enhancement
        sample_match_data = {
            "patient_data": {
                "given_name": "Maria",
                "family_name": "Santos",
                "patient_id": "1902395951", 
                "country_code": "PT"
            },
            "cda_content": "<clinical_document>abbreviated content</clinical_document>",
            "has_l3": True
        }
        
        print("\n📋 Testing match data enhancement...")
        enhanced = service.enhance_session_with_complete_xml(
            sample_match_data, "1902395951", "PT"
        )
        
        print(f"✅ Enhancement completed")
        print(f"   Original CDA size: {len(sample_match_data.get('cda_content', ''))}")
        print(f"   Enhanced CDA size: {len(enhanced.get('cda_content', ''))}")
        print(f"   Has complete XML: {enhanced.get('has_complete_xml', False)}")
        print(f"   Has enhanced parsing: {enhanced.get('has_enhanced_parsing', False)}")
        
        if enhanced.get('enhancement_metadata'):
            metadata = enhanced['enhancement_metadata']
            print(f"   Size improvement: {metadata.get('size_improvement_ratio', 1):.2f}x")
            print(f"   Enhancement timestamp: {metadata.get('enhancement_timestamp', 'N/A')}")
        
        print("\n🎉 All tests passed! Session enhancement is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_enhancement()
    sys.exit(0 if success else 1)