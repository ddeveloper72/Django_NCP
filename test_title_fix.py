#!/usr/bin/env python3
"""
Test script to verify the title handling fix in PSTableRenderer
"""

from patient_data.services.ps_table_renderer import PSTableRenderer

def test_title_handling():
    """Test that PSTableRenderer handles different title formats correctly"""
    renderer = PSTableRenderer()
    
    # Test cases with different title formats
    test_cases = [
        {
            "description": "String title",
            "section": {
                "title": "Medications", 
                "section_code": "",
                "content": {"original": "Test content"}
            }
        },
        {
            "description": "Dictionary title with original",
            "section": {
                "title": {"original": "Medications", "translated": "Médicaments"}, 
                "section_code": "",
                "content": {"original": "Test content"}
            }
        },
        {
            "description": "Dictionary title with only translated",
            "section": {
                "title": {"translated": "Médicaments"}, 
                "section_code": "",
                "content": {"original": "Test content"}
            }
        },
        {
            "description": "Empty title",
            "section": {
                "title": "", 
                "section_code": "",
                "content": {"original": "Test content"}
            }
        },
        {
            "description": "None title",
            "section": {
                "section_code": "",
                "content": {"original": "Test content"}
            }
        }
    ]
    
    print("🧪 Testing PSTableRenderer Title Handling Fix")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['description']}")
        try:
            # Test render_section
            result = renderer.render_section(test_case['section'])
            print(f"✅ render_section: Success - {result.get('section_type', 'unknown')}")
            
            # Test render_section_tables 
            result_tables = renderer.render_section_tables([test_case['section']])
            print(f"✅ render_section_tables: Success - {len(result_tables)} sections rendered")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 Title handling test completed!")

if __name__ == "__main__":
    test_title_handling()
