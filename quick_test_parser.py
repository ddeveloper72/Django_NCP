#!/usr/bin/env python
"""
Simple test to validate the enhanced CDA parser works
"""

import os
import sys
import django

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def quick_test():
    """Quick test of enhanced parser"""

    # Simple XML CDA content for testing
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <component>
            <structuredBody>
                <component>
                    <section>
                        <templateId root="1.3.6.1.4.1.12559.11.10.1.3.1.2.2"/>
                        <code code="48765-2" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC" displayName="Allergies"/>
                        <title>Allergies and Intolerances</title>
                        <text>
                            <table>
                                <thead>
                                    <tr><th>Type</th><th>Agent</th><th>Reaction</th></tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><content ID="TYPE_A0">Food Allergy</content></td>
                                        <td><content ID="AGENT_A0">Peanuts</content></td>
                                        <td><content ID="REACTION_A0">Anaphylaxis</content></td>
                                    </tr>
                                </tbody>
                            </table>
                        </text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <code code="609328004" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED CT" displayName="Allergic disposition"/>
                                <text><reference value="#TYPE_A0"/></text>
                                <participant typeCode="CSM">
                                    <participantRole classCode="MANU">
                                        <playingEntity classCode="MMAT">
                                            <code code="256349002" codeSystem="2.16.840.1.113883.6.96" codeSystemName="SNOMED CT" displayName="Peanut">
                                                <originalText><reference value="#AGENT_A0"/></originalText>
                                            </code>
                                        </playingEntity>
                                    </participantRole>
                                </participant>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    try:
        from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser

        parser = EnhancedCDAXMLParser()
        result = parser.parse_cda_content(test_xml)

        print("✅ Enhanced CDA Parser Test Results:")
        print(f"   - Sections: {result['sections_count']}")
        print(f"   - Coded sections: {result['coded_sections_count']}")
        print(f"   - Clinical codes: {result['medical_terms_count']}")
        print(f"   - Quality: {result['translation_quality']}")

        if result["sections"]:
            section = result["sections"][0]
            print(f"   - First section: {section['title']['coded']}")
            print(f"   - Has codes: {section['is_coded_section']}")

            if section.get("clinical_codes") and hasattr(
                section["clinical_codes"], "codes"
            ):
                codes = section["clinical_codes"].codes
                print(f"   - Clinical codes found: {len(codes)}")
                for code in codes[:2]:
                    print(
                        f"     * {code.system_name}: {code.code} - {code.display_name}"
                    )

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running quick enhanced CDA parser test...")
    success = quick_test()
    if success:
        print("\n🎉 Parser is working! Now test in browser by navigating:")
        print("   1. View Test Patients")
        print("   2. Test NCP Query")
        print("   3. View CDA Document")
        print("   4. Check for clinical sections with coded data")
    else:
        print("\n🔧 Parser needs debugging")
