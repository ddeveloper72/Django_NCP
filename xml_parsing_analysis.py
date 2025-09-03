#!/usr/bin/env python3
"""
XML Parsing Tools Analysis for Django NCP CDA Processing
Analysis of current ElementTree vs alternative XML parsing libraries
"""

import os
import sys
import django
from pathlib import Path
import time
import xml.etree.ElementTree as ET

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def analyze_current_parsing_approach():
    """Analyze our current XML parsing approach and identify potential improvements"""

    print("🔍 XML PARSING TOOLS ANALYSIS FOR CDA PROCESSING")
    print("=" * 60)

    # Find a test file to analyze
    test_folders = [
        "test_data/eu_member_states/IT",
        "test_data/eu_member_states/FR",
        "test_data/eu_member_states/DE",
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
        print("❌ No test files found for analysis")
        return

    print(f"📁 Analyzing: {test_file}")

    # Load the XML content
    with open(test_file, "r", encoding="utf-8") as f:
        xml_content = f.read()

    print(f"📏 File size: {len(xml_content):,} characters")

    print("\n" + "=" * 60)
    print("CURRENT APPROACH: xml.etree.ElementTree (Standard Library)")
    print("=" * 60)

    # Test current ElementTree approach
    start_time = time.time()
    try:
        root = ET.fromstring(xml_content)
        et_parse_time = time.time() - start_time

        print(f"✅ Parse time: {et_parse_time:.4f} seconds")
        print(f"📊 Root tag: {root.tag}")
        print(f"📊 Root attributes: {len(root.attrib)}")

        # Test namespace handling
        print("\n🔍 NAMESPACE HANDLING:")
        namespaced_elements = root.findall(".//{urn:hl7-org:v3}section")
        print(f"   Found {len(namespaced_elements)} sections using namespace")

        # Test complex queries
        print("\n🔍 COMPLEX QUERIES:")
        start_time = time.time()
        patient_role = root.find(
            ".//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole"
        )
        query_time = time.time() - start_time
        print(f"   Patient role query time: {query_time:.6f} seconds")
        print(f"   Patient role found: {patient_role is not None}")

        # Test our enhanced parser
        print("\n🔧 ENHANCED PARSER PERFORMANCE:")
        parser = EnhancedCDAXMLParser()
        start_time = time.time()
        result = parser.parse_cda_content(xml_content)
        enhanced_parse_time = time.time() - start_time

        print(f"   Enhanced parse time: {enhanced_parse_time:.4f} seconds")
        print(f"   Sections extracted: {len(result.get('sections', []))}")
        print(f"   Clinical codes found: {result.get('medical_terms_count', 0)}")

    except Exception as e:
        print(f"❌ ElementTree error: {str(e)}")
        et_parse_time = None
        enhanced_parse_time = None

    print("\n" + "=" * 60)
    print("ANALYSIS: STRENGTHS & WEAKNESSES OF CURRENT APPROACH")
    print("=" * 60)

    print("\n✅ STRENGTHS OF CURRENT ElementTree APPROACH:")
    print("   • Standard library - no external dependencies")
    print("   • Lightweight and memory efficient")
    print("   • Good performance for our current use cases")
    print("   • Well-tested and stable")
    print("   • Handles CDA namespace requirements adequately")
    print("   • Works well with our current extraction patterns")

    print("\n⚠️  CURRENT CHALLENGES:")
    print("   • Verbose namespace syntax: {urn:hl7-org:v3}element")
    print("   • Limited XPath support (no advanced XPath queries)")
    print("   • Manual namespace handling required")
    print("   • Complex queries can be cumbersome")

    print("\n" + "=" * 60)
    print("ALTERNATIVE TOOLS EVALUATION")
    print("=" * 60)

    print("\n🔧 1. LXML (Recommended for Enhanced Features)")
    print("   Pros:")
    print("   ✅ Full XPath 1.0 support - could simplify complex queries")
    print("   ✅ Better namespace handling with xpath()")
    print("   ✅ Higher performance for large files")
    print("   ✅ More powerful element selection")
    print("   ✅ Validation support (XML Schema, RelaxNG)")
    print("   ")
    print("   Cons:")
    print("   ❌ External dependency (requires installation)")
    print("   ❌ Slightly more complex for simple use cases")
    print("   ❌ Larger memory footprint")
    print("   ")
    print("   Example improvement:")
    print("   # Current ElementTree:")
    print(
        "   # root.find('.//{urn:hl7-org:v3}recordTarget/{urn:hl7-org:v3}patientRole')"
    )
    print("   # With lxml XPath:")
    print(
        "   # root.xpath('//cda:recordTarget/cda:patientRole', namespaces={'cda': 'urn:hl7-org:v3'})"
    )

    print("\n🔧 2. BeautifulSoup (Not Recommended for CDA)")
    print("   Pros:")
    print("   ✅ Very user-friendly syntax")
    print("   ✅ Handles malformed XML gracefully")
    print("   ✅ Good for HTML-like content")
    print("   ")
    print("   Cons:")
    print("   ❌ Slower than ElementTree/lxml")
    print("   ❌ Less efficient for structured XML like CDA")
    print("   ❌ Overkill for our well-formed CDA documents")

    print("\n🔧 3. xmltodict (Not Recommended for CDA)")
    print("   Pros:")
    print("   ✅ Very simple dictionary-based access")
    print("   ✅ Easy to understand structure")
    print("   ")
    print("   Cons:")
    print("   ❌ Loses XML structure information")
    print("   ❌ Poor namespace handling")
    print("   ❌ High memory usage for large files")
    print("   ❌ Doesn't preserve element order")
    print("   ❌ Would require major refactoring")

    print("\n🔧 4. minidom (Not Recommended)")
    print("   Pros:")
    print("   ✅ Standard library")
    print("   ✅ DOM-style access")
    print("   ")
    print("   Cons:")
    print("   ❌ Very memory intensive")
    print("   ❌ Slower than ElementTree")
    print("   ❌ More complex API")
    print("   ❌ No advantages over ElementTree for our use case")

    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)

    print("\n🎯 RECOMMENDATION: STICK WITH ElementTree + SELECTIVE LXML ENHANCEMENT")
    print("\n📊 Current Performance Assessment:")
    if et_parse_time:
        print(f"   • Parse time: {et_parse_time:.4f}s (acceptable for CDA files)")
    if enhanced_parse_time:
        print(
            f"   • Enhanced extraction: {enhanced_parse_time:.4f}s (good performance)"
        )
    print("   • Memory usage: Low")
    print("   • Reliability: High")
    print("   • Maintenance: Easy")

    print("\n✅ WHY ELEMENTTREE IS WORKING WELL:")
    print("   1. CDA files are well-formed XML (ElementTree handles perfectly)")
    print("   2. Our extraction patterns are working effectively")
    print("   3. Performance is adequate for healthcare document sizes")
    print("   4. No external dependencies - better for deployment")
    print("   5. Team familiarity and existing codebase")

    print("\n🚀 POTENTIAL FUTURE ENHANCEMENTS (Optional):")
    print("   1. Add lxml as optional dependency for advanced XPath queries")
    print("   2. Create XPath-based helper methods for complex extractions")
    print("   3. Use lxml for XML validation (schema checking)")
    print("   4. Implement hybrid approach: ElementTree + lxml for specific cases")

    print("\n📋 SPECIFIC IMPROVEMENTS WE COULD MAKE:")
    print("   1. Create namespace utility methods to reduce verbosity")
    print("   2. Add XPath helpers for complex queries (using lxml optionally)")
    print("   3. Implement XML validation for CDA compliance")
    print("   4. Add performance monitoring for large file processing")

    return {
        "recommendation": "Keep ElementTree as primary, consider lxml for advanced features",
        "current_performance": {
            "parse_time": et_parse_time,
            "enhanced_parse_time": enhanced_parse_time,
        },
        "benefits_of_change": "Limited - current approach is working well",
        "risks_of_change": "High - would require significant refactoring",
    }


if __name__ == "__main__":
    analyze_current_parsing_approach()
