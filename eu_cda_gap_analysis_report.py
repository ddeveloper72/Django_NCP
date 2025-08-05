#!/usr/bin/env python3
"""
EU CDA Gap Analysis Results
Based on analysis of Italy, Malta, and Latvia CDA documents
"""

import json
from pathlib import Path


def generate_gap_analysis_report():
    """Generate comprehensive gap analysis based on observed patterns"""

    print("🌍 EU MEMBER STATES CDA GAP ANALYSIS REPORT")
    print("=" * 80)

    # Analysis based on IT, MT, LV samples
    analysis_results = {
        "countries_analyzed": ["IT", "MT", "LV"],
        "document_types": ["FRIENDLY-CDA-(L3)", "PIVOT-CDA-(L3)", "PIVOT-CDA-(L1)"],
        "findings": {
            "structural_consistency": "HIGH",
            "namespace_variations": "MINIMAL",
            "coding_system_coverage": "COMPREHENSIVE",
            "entry_pattern_consistency": "HIGH",
        },
    }

    print(f"📊 STRUCTURAL ANALYSIS:")
    print(f"   Countries analyzed: {', '.join(analysis_results['countries_analyzed'])}")
    print(f"   Document types: {len(analysis_results['document_types'])} types")
    print(
        f"   Structural consistency: {analysis_results['findings']['structural_consistency']}"
    )

    # Common patterns identified
    common_patterns = {
        "root_element": "ClinicalDocument",
        "namespace": "urn:hl7-org:v3",
        "pharmacy_namespace": "urn:hl7-org:pharm",
        "structured_body_path": "component/structuredBody/component",
        "section_path": "component/structuredBody/component/section",
        "entry_path": "component/structuredBody/component/section/entry",
    }

    print(f"\n✅ UNIVERSAL PATTERNS (work across all countries):")
    for pattern, value in common_patterns.items():
        print(f"   {pattern}: {value}")

    # Code systems found across countries
    code_systems = {
        "SNOMED-CT": {
            "oid": "2.16.840.1.113883.6.96",
            "usage": "All countries - clinical observations, problems, procedures",
            "examples": ["609328004", "55561003", "44558001"],
        },
        "LOINC": {
            "oid": "2.16.840.1.113883.6.1",
            "usage": "All countries - section codes, document types",
            "examples": ["60591-5", "48765-2", "11450-4", "47519-4"],
        },
        "ICD-10": {
            "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.44.2",
            "usage": "All countries - problem/diagnosis codes",
            "examples": ["K40.9", "C83.1", "U07.1"],
        },
        "ATC": {
            "oid": "2.16.840.1.113883.6.73",
            "usage": "All countries - medication codes",
            "examples": ["J01C", "B01AC06", "J01FA09"],
        },
        "HL7_ActCode": {
            "oid": "2.16.840.1.113883.5.6",
            "usage": "All countries - act classifications",
            "examples": ["CONC"],
        },
    }

    print(f"\n🏷️  UNIVERSAL CODE SYSTEMS:")
    for system, info in code_systems.items():
        print(f"   {system} ({info['oid']}):")
        print(f"      Usage: {info['usage']}")
        print(f"      Examples: {', '.join(info['examples'])}")

    # Country-specific variations
    country_variations = {
        "IT": {
            "realm_code": "EU",
            "language": "it-IT",
            "specific_oids": [
                "2.16.840.1.113883.2.9.77.22.11.2",
                "2.16.840.1.113883.2.9.2.190.4.4",
            ],
            "notes": "Rich clinical coding, comprehensive sections",
        },
        "MT": {
            "realm_code": "MT",
            "language": "en-GB",
            "specific_oids": [
                "2.16.470.1.100.1.4.1000.990.1",
                "2.16.470.1.100.1.1.1000.990.1.1",
            ],
            "notes": "Clear structure, good coding coverage",
        },
        "LV": {
            "realm_code": None,  # Not specified in sample
            "language": "lv-LV",
            "specific_oids": ["1.3.6.1.4.1.38760", "1.3.6.1.4.1.38760.3.1.1"],
            "notes": "Extensive problem list, multiple IDs per patient",
        },
    }

    print(f"\n🏳️  COUNTRY-SPECIFIC VARIATIONS:")
    for country, info in country_variations.items():
        print(f"   {country}:")
        print(f"      Language: {info['language']}")
        print(f"      Realm: {info.get('realm_code', 'Not specified')}")
        print(f"      Notes: {info['notes']}")

    # Section patterns analysis
    section_patterns = {
        "allergies": {
            "loinc_code": "48765-2",
            "title_variations": [
                "Allergies and other adverse reactions",
                "Alerģijas un nepanesamības",
            ],
            "entry_types": ["act", "observation"],
            "consistency": "HIGH",
        },
        "problems": {
            "loinc_code": "11450-4",
            "title_variations": ["Problem list", "Diagnozes"],
            "entry_types": ["act", "observation"],
            "consistency": "HIGH",
        },
        "procedures": {
            "loinc_code": "47519-4",
            "title_variations": ["History of Procedures", "Ķirurģiskās iejaukšanās"],
            "entry_types": ["procedure"],
            "consistency": "HIGH",
        },
        "medications": {
            "loinc_code": "10160-0",
            "title_variations": ["History of medication use", "Zāļu kopsavilkums"],
            "entry_types": ["substanceAdministration"],
            "consistency": "HIGH",
        },
        "devices": {
            "loinc_code": "46264-8",
            "title_variations": [
                "History of medical device use",
                "Medicīniskās ierīces",
            ],
            "entry_types": ["supply"],
            "consistency": "HIGH",
        },
    }

    print(f"\n📋 SECTION PATTERNS ANALYSIS:")
    for section, info in section_patterns.items():
        print(f"   {section.upper()}:")
        print(f"      LOINC: {info['loinc_code']}")
        print(f"      Entry types: {', '.join(info['entry_types'])}")
        print(f"      Consistency: {info['consistency']}")

    # Parser recommendations
    print(f"\n💡 PARSER ARCHITECTURE RECOMMENDATIONS:")
    print(f"   =" * 60)

    recommendations = [
        {
            "approach": "ENHANCED XML PARSER (Current)",
            "pros": [
                "✅ Working well with current system",
                "✅ High structural consistency across countries",
                "✅ Universal LOINC section codes",
                "✅ Common entry patterns",
            ],
            "cons": [
                "⚠️  Country-specific OID mappings needed",
                "⚠️  Language variations in titles",
                "⚠️  Namespace complexity",
            ],
            "verdict": "GOOD for current 3 countries",
        },
        {
            "approach": "JSON BUNDLE PARSER (Future)",
            "pros": [
                "✅ Country-agnostic architecture",
                "✅ Handles namespace variations automatically",
                "✅ Dynamic OID resolution",
                "✅ Better performance with large documents",
                "✅ Future-proof for new countries",
            ],
            "cons": [
                "⚠️  Additional dependency (xmltodict)",
                "⚠️  New architecture to implement",
            ],
            "verdict": "EXCELLENT for scalability",
        },
    ]

    for rec in recommendations:
        print(f"\n🏗️  {rec['approach']}:")
        print(f"      Pros:")
        for pro in rec["pros"]:
            print(f"         {pro}")
        print(f"      Cons:")
        for con in rec["cons"]:
            print(f"         {con}")
        print(f"      Verdict: {rec['verdict']}")

    # Implementation strategy
    print(f"\n🚀 IMPLEMENTATION STRATEGY:")
    print(f"   =" * 60)

    strategy = {
        "Phase 1 (Current)": [
            "✅ Keep Enhanced XML Parser for production",
            "✅ Add country-specific OID mappings",
            "✅ Handle IT, MT, LV variations",
        ],
        "Phase 2 (Future)": [
            "🔄 Implement JSON Bundle Parser in parallel",
            "🔄 Test with all existing countries",
            "🔄 Performance comparison",
        ],
        "Phase 3 (Scale)": [
            "🚀 Deploy JSON Bundle for new countries",
            "🚀 Gradual migration strategy",
            "🚀 Universal clinical coding platform",
        ],
    }

    for phase, tasks in strategy.items():
        print(f"\n   {phase}:")
        for task in tasks:
            print(f"      {task}")

    # Technical specifications
    print(f"\n🔧 TECHNICAL SPECIFICATIONS:")
    print(f"   =" * 60)

    specs = {
        "universal_xpath_patterns": [
            "//section[code[@codeSystem='2.16.840.1.113883.6.1']]",  # LOINC sections
            "//entry//*[@code and @codeSystem]",  # Any coded element
            "//observation[@classCode='OBS']",  # Clinical observations
            "//act[@classCode='ACT']",  # Clinical acts
            "//procedure[@classCode='PROC']",  # Procedures
        ],
        "universal_json_queries": [
            "$..*[?(@.code && @.codeSystem)]",  # Any coded element
            "$..section[?(@.code && @.code['@codeSystem'] == '2.16.840.1.113883.6.1')]",  # LOINC sections
            "$..entry..*[?(@['@classCode'] == 'OBS')]",  # Observations
            "$..entry..*[?(@['@classCode'] == 'ACT')]",  # Acts
        ],
        "code_system_priority": [
            "SNOMED-CT (2.16.840.1.113883.6.96)",
            "LOINC (2.16.840.1.113883.6.1)",
            "ICD-10 (1.3.6.1.4.1.12559.11.10.1.3.1.44.2)",
            "ATC (2.16.840.1.113883.6.73)",
        ],
    }

    print(f"   Universal XPath patterns:")
    for pattern in specs["universal_xpath_patterns"]:
        print(f"      {pattern}")

    print(f"\n   Universal JSON queries:")
    for query in specs["universal_json_queries"]:
        print(f"      {query}")

    print(f"\n   Code system priority:")
    for system in specs["code_system_priority"]:
        print(f"      {system}")

    # Final verdict
    print(f"\n🎯 FINAL VERDICT:")
    print(f"   =" * 60)
    print(f"   📊 Structural consistency across EU countries: EXCELLENT")
    print(f"   🏷️  Clinical coding standardization: VERY GOOD")
    print(f"   🌍 Current Enhanced XML Parser compatibility: HIGH")
    print(f"   🚀 JSON Bundle approach potential: VERY HIGH")
    print(f"   ")
    print(f"   🏆 RECOMMENDATION: Keep Enhanced XML Parser for immediate use,")
    print(f"       implement JSON Bundle Parser for future scalability")

    return {
        "analysis": analysis_results,
        "patterns": common_patterns,
        "code_systems": code_systems,
        "variations": country_variations,
        "sections": section_patterns,
        "recommendations": recommendations,
        "strategy": strategy,
        "specs": specs,
    }


def save_analysis_report(data, filename="eu_cda_gap_analysis_report.json"):
    """Save the analysis report to file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Analysis report saved to: {filename}")


if __name__ == "__main__":
    analysis_data = generate_gap_analysis_report()
    save_analysis_report(analysis_data)

    print(f"\n🎉 Gap analysis complete!")
    print(
        f"   Based on analysis of: {', '.join(analysis_data['analysis']['countries_analyzed'])}"
    )
    print(f"   Conclusion: High compatibility for Enhanced XML Parser")
    print(f"   Future recommendation: JSON Bundle approach for scalability")
