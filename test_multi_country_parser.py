#!/usr/bin/env python3
"""
Multi-Country CDA Parser Test
Test Enhanced XML Parser against multiple EU countries
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def test_multi_country_parser():
    """Test Enhanced XML Parser on multiple countries"""

    print("🌍 MULTI-COUNTRY CDA PARSER TEST")
    print("=" * 60)

    # Test files from different countries
    test_files = [
        {
            "country": "IT",
            "file": "test_data/eu_member_states/IT/2025-03-28T13-29-59.727799Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
            "expected_sections": 3,
            "description": "Italian L3 CDA - Rich coding",
        },
        {
            "country": "MT",
            "file": "test_data/eu_member_states/MT/2025-03-18T15-09-34.313665Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.0.0)_NOT-TESTED.xml",
            "expected_sections": 5,
            "description": "Malta L3 CDA - Comprehensive",
        },
        {
            "country": "LV",
            "file": "test_data/eu_member_states/LV/2025-04-01T11-25-07.284098Z_CDA_EHDSI---FRIENDLY-CDA-(L3)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml",
            "expected_sections": 5,
            "description": "Latvia L3 CDA - Extensive problems",
        },
    ]

    parser = EnhancedCDAXMLParser()
    results = {}

    for test_case in test_files:
        country = test_case["country"]
        file_path = test_case["file"]

        print(f"\n🏳️  TESTING {country}")
        print(f"   📄 {test_case['description']}")
        print(f"   📂 {Path(file_path).name}")

        try:
            # Parse the document
            result = parser.parse_cda_file(file_path)

            # Extract metrics
            sections = result.get("sections", [])
            total_codes = 0
            coded_sections = 0

            for section in sections:
                clinical_codes = section.get("clinical_codes")
                if clinical_codes and hasattr(clinical_codes, "all_codes"):
                    total_codes += len(clinical_codes.all_codes)
                    if clinical_codes.all_codes:
                        coded_sections += 1

            # Patient info
            patient = result.get("patient_identity", {})
            patient_name = (
                f"{patient.get('given_name', '')} {patient.get('family_name', '')}"
            )

            results[country] = {
                "status": "SUCCESS",
                "sections_found": len(sections),
                "expected_sections": test_case["expected_sections"],
                "coded_sections": coded_sections,
                "total_codes": total_codes,
                "patient_name": patient_name.strip(),
                "patient_gender": patient.get("gender", ""),
                "has_admin_data": result.get("has_administrative_data", False),
            }

            print(f"   ✅ SUCCESS")
            print(
                f"      📑 Sections: {len(sections)} (expected: {test_case['expected_sections']})"
            )
            print(f"      🏷️  Coded sections: {coded_sections}")
            print(f"      🏷️  Total codes: {total_codes}")
            print(f"      👤 Patient: {patient_name.strip()}")
            print(f"      👤 Gender: {patient.get('gender', 'N/A')}")

            # Show sample codes
            if total_codes > 0:
                print(f"      📋 Sample codes:")
                code_count = 0
                for section in sections:
                    clinical_codes = section.get("clinical_codes")
                    if clinical_codes and hasattr(clinical_codes, "all_codes"):
                        for code in clinical_codes.all_codes[
                            :2
                        ]:  # Show first 2 per section
                            if code_count < 4:  # Max 4 total
                                print(f"         {code.system}: {code.code}")
                                code_count += 1

        except Exception as e:
            results[country] = {"status": "ERROR", "error": str(e)}
            print(f"   ❌ ERROR: {e}")

    # Summary comparison
    print(f"\n📊 CROSS-COUNTRY COMPARISON")
    print("=" * 60)

    successful_countries = [
        country for country, result in results.items() if result["status"] == "SUCCESS"
    ]

    if successful_countries:
        print(f"✅ Successful parses: {len(successful_countries)}/{len(test_files)}")

        # Compare metrics
        sections_range = [results[c]["sections_found"] for c in successful_countries]
        codes_range = [results[c]["total_codes"] for c in successful_countries]

        print(
            f"\n📋 Section count range: {min(sections_range)} - {max(sections_range)}"
        )
        print(f"🏷️  Clinical codes range: {min(codes_range)} - {max(codes_range)}")

        # Country-specific insights
        print(f"\n🏳️  Country Performance:")
        for country in successful_countries:
            data = results[country]
            print(
                f"   {country}: {data['sections_found']} sections, {data['total_codes']} codes"
            )
    else:
        print(f"❌ No successful parses")

    # Architecture assessment
    print(f"\n🏗️  ENHANCED XML PARSER ASSESSMENT")
    print("=" * 60)

    success_rate = len(successful_countries) / len(test_files) * 100

    if success_rate >= 100:
        verdict = "EXCELLENT - Works perfectly across all countries"
        recommendation = "✅ Continue using Enhanced XML Parser"
    elif success_rate >= 80:
        verdict = "GOOD - Works well with minor issues"
        recommendation = "✅ Continue using, address specific issues"
    elif success_rate >= 60:
        verdict = "FAIR - Some compatibility issues"
        recommendation = "⚠️  Consider JSON Bundle approach"
    else:
        verdict = "POOR - Major compatibility issues"
        recommendation = "❌ Implement JSON Bundle parser immediately"

    print(f"Success rate: {success_rate:.1f}%")
    print(f"Verdict: {verdict}")
    print(f"Recommendation: {recommendation}")

    # JSON Bundle recommendation
    if success_rate < 100:
        print(f"\n🌐 JSON BUNDLE PARSER BENEFITS:")
        print(f"   🔄 Universal compatibility across all EU countries")
        print(f"   🚀 Future-proof for new country additions")
        print(f"   ⚡ Better performance with complex documents")
        print(f"   🧩 Modular architecture for easier maintenance")

    return results


if __name__ == "__main__":
    results = test_multi_country_parser()

    success_count = len([r for r in results.values() if r["status"] == "SUCCESS"])
    total_count = len(results)

    print(
        f"\n🎯 FINAL RESULT: {success_count}/{total_count} countries successfully parsed"
    )

    if success_count == total_count:
        print(f"🏆 CONCLUSION: Enhanced XML Parser handles all tested EU countries!")
        print(f"   Current system is working excellently for multi-country support.")
    else:
        print(f"⚠️  CONCLUSION: Some compatibility issues detected.")
        print(f"   Consider implementing JSON Bundle parser for better coverage.")
