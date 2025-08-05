#!/usr/bin/env python3
"""
Quick EU CDA Structure Analysis
Simple analysis of CDA document structures across EU countries
"""

import os
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict


def quick_analysis():
    """Quick analysis of EU CDA documents"""

    test_data_path = Path("test_data/eu_member_states")

    print("🔍 QUICK EU CDA STRUCTURE ANALYSIS")
    print("=" * 60)

    # Find all XML files
    xml_files = list(test_data_path.glob("**/*.xml"))
    print(f"📄 Found {len(xml_files)} CDA files")

    # Group by country
    countries = defaultdict(list)
    for file_path in xml_files:
        country = file_path.parent.name
        countries[country].append(file_path)

    print(f"🌍 Countries: {sorted(countries.keys())}")
    print("-" * 60)

    # Analyze each country (sample)
    analysis_results = {}

    for country, files in sorted(countries.items()):
        print(f"\n🏳️  {country} ({len(files)} files)")

        if len(files) > 0:
            # Analyze first file
            sample_file = files[0]
            print(f"   📄 Sample: {sample_file.name}")

            try:
                tree = ET.parse(sample_file)
                root = tree.getroot()

                # Basic structure analysis
                structure = {
                    "root_tag": (
                        root.tag.split("}")[-1] if "}" in root.tag else root.tag
                    ),
                    "namespaces": (
                        len(dict(root.nsmap)) if hasattr(root, "nsmap") else 0
                    ),
                    "total_elements": len(list(root.iter())),
                    "has_structured_body": bool(
                        root.find(".//*[local-name()='structuredBody']") is not None
                    ),
                    "sections_count": len(root.findall(".//*[local-name()='section']")),
                    "entries_count": len(root.findall(".//*[local-name()='entry']")),
                    "coded_elements": len(root.findall(".//*[@code]")),
                    "code_systems": len(
                        set(
                            elem.get("codeSystem", "")
                            for elem in root.findall(".//*[@codeSystem]")
                            if elem.get("codeSystem")
                        )
                    ),
                }

                analysis_results[country] = structure

                print(f"      📊 Elements: {structure['total_elements']}")
                print(f"      📋 Sections: {structure['sections_count']}")
                print(f"      📝 Entries: {structure['entries_count']}")
                print(f"      🏷️  Coded elements: {structure['coded_elements']}")
                print(f"      🏷️  Code systems: {structure['code_systems']}")

                # Look for clinical codes sample
                coded_elements = root.findall(".//*[@code]")[:3]  # First 3
                if coded_elements:
                    print(f"      📋 Sample codes:")
                    for elem in coded_elements:
                        code = elem.get("code", "")
                        system = (
                            elem.get("codeSystem", "")[:30] + "..."
                            if len(elem.get("codeSystem", "")) > 30
                            else elem.get("codeSystem", "")
                        )
                        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                        print(f"         {tag}: {code} ({system})")

            except Exception as e:
                print(f"      ❌ Error: {e}")
                analysis_results[country] = {"error": str(e)}

    # Cross-country comparison
    print(f"\n📊 CROSS-COUNTRY COMPARISON")
    print("-" * 60)

    # Find patterns
    all_coded_counts = [
        data.get("coded_elements", 0)
        for data in analysis_results.values()
        if "error" not in data
    ]
    all_section_counts = [
        data.get("sections_count", 0)
        for data in analysis_results.values()
        if "error" not in data
    ]
    all_entry_counts = [
        data.get("entries_count", 0)
        for data in analysis_results.values()
        if "error" not in data
    ]

    if all_coded_counts:
        print(
            f"📋 Coded elements range: {min(all_coded_counts)} - {max(all_coded_counts)}"
        )
        print(
            f"📋 Sections range: {min(all_section_counts)} - {max(all_section_counts)}"
        )
        print(f"📋 Entries range: {min(all_entry_counts)} - {max(all_entry_counts)}")

    # Countries with most clinical codes
    coded_by_country = [
        (country, data.get("coded_elements", 0))
        for country, data in analysis_results.items()
        if "error" not in data
    ]
    coded_by_country.sort(key=lambda x: x[1], reverse=True)

    print(f"\n🏆 RICHEST CLINICAL CODING (by coded elements):")
    for country, count in coded_by_country[:5]:
        print(f"   {country}: {count} coded elements")

    # Recommendations
    print(f"\n💡 PARSER RECOMMENDATIONS")
    print("-" * 60)

    max_coded = max(all_coded_counts) if all_coded_counts else 0
    avg_coded = sum(all_coded_counts) / len(all_coded_counts) if all_coded_counts else 0

    print(
        f"📊 Clinical coding varies widely: {min(all_coded_counts) if all_coded_counts else 0} to {max_coded} coded elements"
    )
    print(f"📊 Average: {avg_coded:.1f} coded elements per document")

    if max_coded > avg_coded * 2:
        print(f"⚠️  High variation suggests need for flexible parsing approach")
        print(f"✅ JSON Bundle approach recommended for handling variations")
    else:
        print(f"✅ Consistent structure - current XML parser may work well")

    print(f"\n🚀 NEXT STEPS:")
    print(f"   1. Test current Enhanced XML Parser on all countries")
    print(f"   2. Identify which countries need special handling")
    print(f"   3. Implement JSON Bundle parser for complex cases")

    return analysis_results


if __name__ == "__main__":
    quick_analysis()
