#!/usr/bin/env python3
"""
Quick All-Countries CDA Test
Test a sample from each country to get quick overview
"""

import os
import sys
import django
from pathlib import Path
from collections import defaultdict

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


def quick_all_countries_test():
    """Quick test of Enhanced XML Parser on all countries"""

    print("🌍 QUICK ALL-COUNTRIES CDA TEST")
    print("=" * 60)

    # Find files by country
    test_data_path = Path("test_data/eu_member_states")

    if not test_data_path.exists():
        print(f"❌ Test data path not found: {test_data_path}")
        return

    countries = {}
    for country_dir in test_data_path.iterdir():
        if country_dir.is_dir():
            xml_files = list(country_dir.glob("**/*.xml"))
            if xml_files:
                countries[country_dir.name] = xml_files

    print(f"📊 Found {len(countries)} countries with XML files")
    print(f"Countries: {', '.join(sorted(countries.keys()))}")
    print("-" * 60)

    parser = EnhancedCDAXMLParser()
    results = {}

    # Test one file per country
    for country, files in sorted(countries.items()):
        print(f"\\n🏳️  Testing {country}")

        # Try to find a good test file (prefer L3 FRIENDLY, then L3 PIVOT, then any)
        test_file = None
        for file_path in files:
            if "FRIENDLY-CDA-(L3)" in file_path.name:
                test_file = file_path
                break

        if not test_file:
            for file_path in files:
                if "PIVOT-CDA-(L3)" in file_path.name:
                    test_file = file_path
                    break

        if not test_file:
            test_file = files[0]  # Use first available file

        print(f"   📄 File: {test_file.name}")

        try:
            # Read file content and parse
            with open(test_file, "r", encoding="utf-8") as f:
                xml_content = f.read()

            result = parser.parse_cda_content(xml_content)

            # Extract metrics
            sections = result.get("sections", [])
            total_codes = 0

            for section in sections:
                clinical_codes = section.get("clinical_codes")
                if clinical_codes:
                    if hasattr(clinical_codes, "codes"):
                        total_codes += len(clinical_codes.codes)
                    elif hasattr(clinical_codes, "all_codes"):
                        total_codes += len(clinical_codes.all_codes)

            patient = result.get("patient_identity", {})
            patient_name = f"{patient.get('given_name', '')} {patient.get('family_name', '')}".strip()

            results[country] = {
                "status": "SUCCESS",
                "sections": len(sections),
                "codes": total_codes,
                "patient": patient_name,
                "file_count": len(files),
            }

            print(f"   ✅ SUCCESS: {len(sections)} sections, {total_codes} codes")
            print(f"   👤 Patient: {patient_name}")
            print(f"   📁 Total files: {len(files)}")

        except Exception as e:
            results[country] = {
                "status": "ERROR",
                "error": str(e),
                "file_count": len(files),
            }
            print(f"   ❌ ERROR: {str(e)[:80]}...")

    # Summary
    print(f"\\n📊 SUMMARY")
    print("=" * 60)

    successful = [c for c, r in results.items() if r["status"] == "SUCCESS"]
    failed = [c for c, r in results.items() if r["status"] == "ERROR"]

    print(f"✅ Successful countries: {len(successful)}/{len(results)}")
    print(f"❌ Failed countries: {len(failed)}")

    if successful:
        print(f"\\n✅ WORKING COUNTRIES:")
        total_files = sum(results[c]["file_count"] for c in successful)
        total_sections = sum(results[c]["sections"] for c in successful)
        total_codes = sum(results[c]["codes"] for c in successful)

        for country in successful:
            data = results[country]
            print(
                f"   {country}: {data['file_count']} files, {data['sections']} sections, {data['codes']} codes"
            )

        print(f"\\n📊 Totals for working countries:")
        print(f"   📁 Files: {total_files}")
        print(f"   📋 Sections: {total_sections}")
        print(f"   🏷️  Codes: {total_codes}")

    if failed:
        print(f"\\n❌ PROBLEMATIC COUNTRIES:")
        for country in failed:
            data = results[country]
            print(f"   {country}: {data['error'][:60]}...")

    # Assessment
    success_rate = len(successful) / len(results) * 100

    print(f"\\n🎯 ASSESSMENT:")
    print("-" * 60)
    print(f"Success rate: {success_rate:.1f}%")

    if success_rate >= 90:
        verdict = "EXCELLENT - Enhanced XML Parser works across EU countries"
        recommendation = "✅ Ready for production deployment"
    elif success_rate >= 75:
        verdict = "GOOD - High compatibility with minor issues"
        recommendation = "✅ Production ready, address specific country issues"
    elif success_rate >= 50:
        verdict = "FAIR - Some compatibility problems"
        recommendation = "⚠️  Consider JSON Bundle approach for failed countries"
    else:
        verdict = "POOR - Major compatibility issues"
        recommendation = "❌ JSON Bundle parser needed"

    print(f"Verdict: {verdict}")
    print(f"Recommendation: {recommendation}")

    return results


if __name__ == "__main__":
    quick_all_countries_test()
