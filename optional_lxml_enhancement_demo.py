#!/usr/bin/env python3
"""
Optional LXML Enhancement Demonstration
Shows how we could optionally use lxml for advanced queries while keeping ElementTree as primary
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def demonstrate_optional_lxml_enhancement():
    """Demonstrate how lxml could enhance our parsing (if we chose to add it)"""

    print("🔍 OPTIONAL LXML ENHANCEMENT DEMONSTRATION")
    print("=" * 60)

    # Try to import lxml
    try:
        from lxml import etree as lxml_etree

        lxml_available = True
        print("✅ lxml is available for demonstration")
    except ImportError:
        lxml_available = False
        print("⚠️  lxml not installed - showing theoretical examples")

    # Find test file
    test_folders = [
        "test_data/eu_member_states/IT",
        "test_data/eu_member_states/FR",
        "test_data",
    ]

    test_file = None
    for folder in test_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            xml_files = list(folder_path.glob("*.xml"))
            if xml_files:
                test_file = xml_files[0]
                break

    if not test_file:
        print("❌ No test files found")
        return

    print(f"📁 Test file: {test_file}")

    # Load XML content
    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print("\n" + "=" * 60)
    print("COMPARISON: ElementTree vs LXML Syntax")
    print("=" * 60)

    # Parse with ElementTree (current approach)
    print("\n🔧 ELEMENTTREE (Current Approach):")
    et_root = ET.fromstring(xml_content)

    print("   # Finding patient role:")
    print(
        "   patient_role = root.find('.//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole')"
    )
    patient_role_et = et_root.find(
        ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
    )
    print(f"   Result: {patient_role_et is not None}")

    print("\n   # Finding all sections:")
    print("   sections = root.findall('.//{urn:hl7-org:v3}section')")
    sections_et = et_root.findall(".//{urn:hl7-org:v3}section")
    print(f"   Result: {len(sections_et)} sections found")

    print("\n   # Finding codes in entries:")
    print("   codes = []")
    print("   for entry in root.findall('.//{urn:hl7-org:v3}entry'):")
    print("       for elem in entry.iter():")
    print("           if elem.get('code'):")
    print("               codes.append(elem)")
    codes_et = []
    for entry in et_root.findall(".//{urn:hl7-org:v3}entry"):
        for elem in entry.iter():
            if elem.get("code"):
                codes_et.append(elem)
    print(f"   Result: {len(codes_et)} coded elements found")

    # Show lxml advantages
    if lxml_available:
        print("\n🚀 LXML (Enhanced Approach):")

        # Parse with lxml
        lxml_root = lxml_etree.fromstring(xml_content.encode("utf-8"))

        # Define namespaces once
        namespaces = {"cda": "urn:hl7-org:v3"}

        print("   # Define namespaces once:")
        print("   namespaces = {'cda': 'urn:hl7-org:v3'}")

        print("\n   # Finding patient role (cleaner syntax):")
        print(
            "   patient_role = root.xpath('//cda:recordTarget/cda:patientRole', namespaces=namespaces)"
        )
        patient_role_lxml = lxml_root.xpath(
            "//cda:recordTarget/cda:patientRole", namespaces=namespaces
        )
        print(f"   Result: {len(patient_role_lxml) > 0}")

        print("\n   # Finding all sections:")
        print("   sections = root.xpath('//cda:section', namespaces=namespaces)")
        sections_lxml = lxml_root.xpath("//cda:section", namespaces=namespaces)
        print(f"   Result: {len(sections_lxml)} sections found")

        print("\n   # Finding codes with advanced XPath:")
        print("   codes = root.xpath('//*[@code]', namespaces=namespaces)")
        codes_lxml = lxml_root.xpath("//*[@code]", namespaces=namespaces)
        print(f"   Result: {len(codes_lxml)} coded elements found")

        print("\n   # Advanced query - sections with specific codes:")
        print(
            "   ps_sections = root.xpath('//cda:section[cda:code[@code=\"11369-6\"]]', namespaces=namespaces)"
        )
        ps_sections = lxml_root.xpath(
            '//cda:section[cda:code[@code="11369-6"]]', namespaces=namespaces
        )
        print(f"   Result: {len(ps_sections)} Patient Summary sections")

        print("\n   # Find all medication entries:")
        print(
            "   medications = root.xpath('//cda:entry//cda:substanceAdministration', namespaces=namespaces)"
        )
        medications = lxml_root.xpath(
            "//cda:entry//cda:substanceAdministration", namespaces=namespaces
        )
        print(f"   Result: {len(medications)} medication entries")

    print("\n" + "=" * 60)
    print("BENEFITS ANALYSIS")
    print("=" * 60)

    print("\n✅ CURRENT ELEMENTTREE STRENGTHS:")
    print("   • Working well for our current needs")
    print("   • No external dependencies")
    print("   • Good performance")
    print("   • Team familiarity")
    print("   • Stable and reliable")

    if lxml_available:
        print("\n🚀 POTENTIAL LXML BENEFITS:")
        print("   • Cleaner namespace handling")
        print("   • Powerful XPath queries")
        print("   • Advanced element selection")
        print("   • Better for complex queries")
        print("   • Schema validation capabilities")

        print("\n📊 PRACTICAL IMPACT:")
        print(
            f"   • Both found patient role: ElementTree={patient_role_et is not None}, lxml={len(patient_role_lxml) > 0}"
        )
        print(
            f"   • Sections found: ElementTree={len(sections_et)}, lxml={len(sections_lxml)}"
        )
        print(
            f"   • Coded elements: ElementTree={len(codes_et)}, lxml={len(codes_lxml)}"
        )
        print("   • Syntax: lxml is cleaner for complex queries")

    print("\n🎯 RECOMMENDATION:")
    print("   ✅ STICK WITH ELEMENTTREE for now")
    print("   📋 REASONS:")
    print("      1. Current approach is working well")
    print("      2. Performance is adequate")
    print("      3. No critical missing features")
    print("      4. Deployment simplicity (no extra dependencies)")
    print("      5. Code is already optimized for ElementTree")

    print("\n🔮 FUTURE CONSIDERATIONS:")
    print("   • Add lxml as optional dependency if we need:")
    print("     - Schema validation for CDA compliance checking")
    print("     - Very complex XPath queries")
    print("     - Performance improvements for very large files")
    print("   • Use namespace helper utilities to improve current code")
    print("   • Consider hybrid approach: ElementTree + lxml for specific features")

    print("\n💡 IMMEDIATE IMPROVEMENTS (Without changing libraries):")
    print("   1. ✅ Use CDANamespaceHelper for cleaner syntax")
    print("   2. ✅ Create specialized helper functions for common patterns")
    print("   3. ✅ Add XML validation using ElementTree + schemas")
    print("   4. ✅ Optimize current extraction patterns")


def create_hybrid_approach_example():
    """Show how we could use both ElementTree and lxml in the same project"""

    print("\n" + "=" * 60)
    print("HYBRID APPROACH EXAMPLE")
    print("=" * 60)

    hybrid_code = '''
class EnhancedCDAXMLParser:
    """Parser that can use both ElementTree and lxml based on needs"""
    
    def __init__(self, prefer_lxml=False):
        self.prefer_lxml = prefer_lxml
        
        # Try to import lxml
        try:
            from lxml import etree as lxml_etree
            self.lxml_available = True
        except ImportError:
            self.lxml_available = False
            if prefer_lxml:
                logger.warning("lxml requested but not available, using ElementTree")
    
    def parse_cda_content(self, xml_content: str):
        """Parse using best available method"""
        if self.prefer_lxml and self.lxml_available:
            return self._parse_with_lxml(xml_content)
        else:
            return self._parse_with_elementtree(xml_content)
    
    def _parse_with_elementtree(self, xml_content: str):
        """Current ElementTree approach - stable and reliable"""
        root = ET.fromstring(xml_content)
        # ... existing logic
    
    def _parse_with_lxml(self, xml_content: str):
        """Enhanced lxml approach - for advanced features"""
        from lxml import etree
        root = etree.fromstring(xml_content.encode('utf-8'))
        namespaces = {'cda': 'urn:hl7-org:v3'}
        
        # Use XPath for complex queries
        sections = root.xpath('//cda:section', namespaces=namespaces)
        # ... enhanced logic with XPath
    
    def validate_cda_schema(self, xml_content: str):
        """Schema validation - requires lxml"""
        if not self.lxml_available:
            raise ImportError("Schema validation requires lxml")
        
        from lxml import etree
        # Validate against CDA schema
        # ... validation logic
'''

    print("📝 HYBRID APPROACH CODE EXAMPLE:")
    print(hybrid_code)

    print("\n🎯 BENEFITS OF HYBRID APPROACH:")
    print("   ✅ Best of both worlds")
    print("   ✅ Graceful fallback to ElementTree")
    print("   ✅ Optional advanced features with lxml")
    print("   ✅ No breaking changes to existing code")
    print("   ✅ Future-proof architecture")


if __name__ == "__main__":
    demonstrate_optional_lxml_enhancement()
    create_hybrid_approach_example()
