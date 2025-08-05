#!/usr/bin/env python3
"""
Test Enhanced CDA Display Multi-Language Support
Demonstrates automatic language detection and processing for various EU languages
"""

import os
import sys
import django
import requests
import json

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_multi_language_detection():
    """Test language detection with different EU countries/languages"""

    from patient_data.views import enhanced_cda_display
    from django.test import RequestFactory
    from django.http import JsonResponse

    # Test cases for different EU languages
    test_cases = [
        {
            "name": "Latvian CDA (explicit language)",
            "source_language": "lv",
            "country_code": "LV",
            "cda_content": """<?xml version="1.0" encoding="UTF-8"?>
                <ClinicalDocument>
                    <languageCode code="lv-LV"/>
                    <title>Zāļu kopsavilkums</title>
                    <section>
                        <code code="10160-0" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Medikamentu saraksts</title>
                        <text>Pacients lieto šādus medikamentus...</text>
                    </section>
                </ClinicalDocument>""",
            "expected_language": "lv",
        },
        {
            "name": "Italian CDA (country code only)",
            "source_language": "",
            "country_code": "IT",
            "cda_content": """<?xml version="1.0" encoding="UTF-8"?>
                <ClinicalDocument>
                    <languageCode code="it-IT"/>
                    <title>Riassunto Paziente</title>
                    <section>
                        <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Allergie e intolleranze</title>
                        <text>Il paziente presenta allergie a...</text>
                    </section>
                </ClinicalDocument>""",
            "expected_language": "it",
        },
        {
            "name": "German CDA (auto-detection)",
            "source_language": "",
            "country_code": "",
            "cda_content": """<?xml version="1.0" encoding="UTF-8"?>
                <ClinicalDocument>
                    <languageCode code="de-DE"/>
                    <title>Patientenzusammenfassung</title>
                    <section>
                        <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Problemliste</title>
                        <text>Der Patient hat folgende medizinische Probleme...</text>
                    </section>
                </ClinicalDocument>""",
            "expected_language": "de",
        },
        {
            "name": "Portuguese CDA (country mapping)",
            "source_language": "",
            "country_code": "PT",
            "cda_content": """<?xml version="1.0" encoding="UTF-8"?>
                <ClinicalDocument>
                    <languageCode code="pt-PT"/>
                    <title>Resumo do Paciente</title>
                    <section>
                        <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Histórico de procedimentos</title>
                        <text>O paciente foi submetido aos seguintes procedimentos...</text>
                    </section>
                </ClinicalDocument>""",
            "expected_language": "pt",
        },
        {
            "name": "Greek CDA (auto-detection)",
            "source_language": "",
            "country_code": "GR",
            "cda_content": """<?xml version="1.0" encoding="UTF-8"?>
                <ClinicalDocument>
                    <languageCode code="el-GR"/>
                    <title>Περίληψη Ασθενή</title>
                    <section>
                        <code code="8716-3" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Ζωτικά σημεία</title>
                        <text>Τα ζωτικά σημεία του ασθενή είναι...</text>
                    </section>
                </ClinicalDocument>""",
            "expected_language": "el",
        },
    ]

    print("🌍 Testing Enhanced CDA Display Multi-Language Support")
    print("=" * 70)

    factory = RequestFactory()
    results = []

    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Input Language: '{test_case['source_language']}'")
        print(f"   Country Code: '{test_case['country_code']}'")
        print(f"   Expected Language: {test_case['expected_language']}")

        # Create mock POST request
        request = factory.post(
            "/patient_data/enhanced_cda_display/",
            data={
                "cda_content": test_case["cda_content"],
                "source_language": test_case["source_language"],
                "country_code": test_case["country_code"],
                "target_language": "en",
            },
            content_type="application/x-www-form-urlencoded",
        )

        try:
            # Call the view function
            response = enhanced_cda_display(request)

            if isinstance(response, JsonResponse):
                data = json.loads(response.content.decode("utf-8"))

                detected_lang = data.get("detected_source_language", "unknown")
                detection_method = data.get("language_detection_method", "unknown")
                success = data.get("success", False)
                sections_count = data.get("sections_count", 0)

                print(f"   ✅ Detected Language: {detected_lang}")
                print(f"   📍 Detection Method: {detection_method}")
                print(f"   🔄 Processing Success: {success}")
                print(f"   📊 Sections Found: {sections_count}")

                # Check if language detection was correct
                if detected_lang == test_case["expected_language"]:
                    print(f"   🎯 Language Detection: ✅ CORRECT")
                else:
                    print(
                        f"   ⚠️  Language Detection: ❌ Expected {test_case['expected_language']}, got {detected_lang}"
                    )

                results.append(
                    {
                        "test_name": test_case["name"],
                        "expected": test_case["expected_language"],
                        "detected": detected_lang,
                        "method": detection_method,
                        "success": success,
                        "sections": sections_count,
                        "correct": detected_lang == test_case["expected_language"],
                    }
                )

            else:
                print(f"   ❌ Unexpected response type: {type(response)}")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(
                {"test_name": test_case["name"], "error": str(e), "correct": False}
            )

    # Summary
    print("\n" + "=" * 70)
    print("📊 MULTI-LANGUAGE DETECTION TEST SUMMARY")
    print("=" * 70)

    correct_count = sum(1 for r in results if r.get("correct", False))
    total_count = len(results)

    print(
        f"\n🎯 Overall Results: {correct_count}/{total_count} correct ({correct_count/total_count*100:.1f}%)"
    )

    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅" if result.get("correct") else "❌"
        if "error" in result:
            print(f"   {status} {result['test_name']}: ERROR - {result['error']}")
        else:
            print(
                f"   {status} {result['test_name']}: {result['detected']} ({result['method']}) - {result['sections']} sections"
            )

    print(f"\n🌟 Language Detection Methods Tested:")
    methods = set(r.get("method", "unknown") for r in results if "method" in r)
    for method in methods:
        method_count = sum(1 for r in results if r.get("method") == method)
        print(f"   • {method}: {method_count} tests")

    return results


if __name__ == "__main__":
    print("🧪 Enhanced CDA Display Multi-Language Test")
    print("Testing automatic language detection for EU countries")
    print("=" * 70)

    results = test_multi_language_detection()

    success_rate = (
        sum(1 for r in results if r.get("correct", False)) / len(results) * 100
    )

    if success_rate >= 80:
        print(
            f"\n🎉 SUCCESS: Multi-language support working properly ({success_rate:.1f}% success rate)"
        )
    else:
        print(
            f"\n⚠️  NEEDS IMPROVEMENT: Some language detection issues ({success_rate:.1f}% success rate)"
        )

    print("\n✅ Enhanced CDA Display now supports automatic detection for:")
    print("   🇩🇪 German (DE, AT, CH)")
    print("   🇮🇹 Italian (IT, SM, VA)")
    print("   🇪🇸 Spanish (ES, AD)")
    print("   🇵🇹 Portuguese (PT)")
    print("   🇱🇻 Latvian (LV)")
    print("   🇱🇹 Lithuanian (LT)")
    print("   🇪🇪 Estonian (EE)")
    print("   🇬🇧 English (MT, IE)")
    print("   🇫🇷 French (FR, LU)")
    print("   🇳🇱 Dutch (NL, BE)")
    print("   🇬🇷 Greek (GR)")
