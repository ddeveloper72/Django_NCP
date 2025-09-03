#!/usr/bin/env python3
"""
EU Member States CDA Gap Analysis
Analyze CDA documents from all EU countries to understand structural variations
"""

import os
import sys
import django
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import json

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


class EUCDAGapAnalysis:
    """Analyze CDA documents from all EU member states"""

    def __init__(self):
        self.test_data_path = Path("test_data/eu_member_states")
        self.analysis_results = {
            "countries": {},
            "namespace_patterns": Counter(),
            "section_code_patterns": Counter(),
            "clinical_code_systems": Counter(),
            "entry_structures": Counter(),
            "coding_patterns": Counter(),
            "common_elements": set(),
            "country_variations": defaultdict(list),
        }

    def run_analysis(self):
        """Run comprehensive gap analysis"""
        print("🌍 EU MEMBER STATES CDA GAP ANALYSIS")
        print("=" * 80)

        # Find all CDA files
        cda_files = list(self.test_data_path.glob("**/*.xml"))
        print(f"📄 Found {len(cda_files)} CDA files")

        # Group by country
        countries = defaultdict(list)
        for file_path in cda_files:
            country = file_path.parent.name
            countries[country].append(file_path)

        print(f"🌍 Countries found: {list(countries.keys())}")
        print("-" * 80)

        # Analyze each country
        for country, files in countries.items():
            print(f"\n🏳️  ANALYZING {country} ({len(files)} files)")
            self.analyze_country(country, files)

        # Generate comparison report
        self.generate_comparison_report()

        # Generate recommendations
        self.generate_recommendations()

        return self.analysis_results

    def analyze_country(self, country: str, files: list):
        """Analyze CDA files for a specific country"""
        country_data = {
            "file_count": len(files),
            "namespaces": Counter(),
            "section_codes": Counter(),
            "code_systems": Counter(),
            "entry_types": Counter(),
            "coding_elements": Counter(),
            "sample_structures": [],
            "errors": [],
        }

        for file_path in files[:3]:  # Analyze first 3 files per country
            try:
                print(f"   📄 {file_path.name}")
                file_analysis = self.analyze_file(file_path)

                # Aggregate data
                country_data["namespaces"].update(file_analysis["namespaces"])
                country_data["section_codes"].update(file_analysis["section_codes"])
                country_data["code_systems"].update(file_analysis["code_systems"])
                country_data["entry_types"].update(file_analysis["entry_types"])
                country_data["coding_elements"].update(file_analysis["coding_elements"])

                if len(country_data["sample_structures"]) < 2:
                    country_data["sample_structures"].append(
                        {
                            "file": file_path.name,
                            "structure": file_analysis["structure_sample"],
                        }
                    )

            except Exception as e:
                country_data["errors"].append(f"{file_path.name}: {str(e)}")
                print(f"      ❌ Error: {e}")

        # Store country analysis
        self.analysis_results["countries"][country] = country_data

        # Update global counters
        self.analysis_results["namespace_patterns"].update(country_data["namespaces"])
        self.analysis_results["section_code_patterns"].update(
            country_data["section_codes"]
        )
        self.analysis_results["clinical_code_systems"].update(
            country_data["code_systems"]
        )
        self.analysis_results["entry_structures"].update(country_data["entry_types"])
        self.analysis_results["coding_patterns"].update(country_data["coding_elements"])

        # Show summary
        print(f"      📊 Namespaces: {len(country_data['namespaces'])}")
        print(f"      📋 Section codes: {len(country_data['section_codes'])}")
        print(f"      🏷️  Code systems: {len(country_data['code_systems'])}")
        print(f"      📝 Entry types: {len(country_data['entry_types'])}")

        # Show top patterns
        if country_data["code_systems"]:
            top_systems = country_data["code_systems"].most_common(3)
            print(f"      🔝 Top code systems: {[f'{s}({c})' for s, c in top_systems]}")

    def analyze_file(self, file_path: Path) -> dict:
        """Analyze a single CDA file"""
        file_analysis = {
            "namespaces": Counter(),
            "section_codes": Counter(),
            "code_systems": Counter(),
            "entry_types": Counter(),
            "coding_elements": Counter(),
            "structure_sample": {},
        }

        try:
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Extract namespaces
            namespaces = {}
            for prefix, uri in root.nsmap.items() if hasattr(root, "nsmap") else {}:
                if prefix:
                    namespaces[prefix] = uri
                    file_analysis["namespaces"][f"{prefix}:{uri[:50]}..."] += 1

            # Find all elements with codes
            coded_elements = root.xpath(".//*[@code or @codeSystem or @value]")

            # Analyze coded elements
            for element in coded_elements:
                tag_name = (
                    element.tag.split("}")[-1] if "}" in element.tag else element.tag
                )
                file_analysis["entry_types"][tag_name] += 1

                # Check for code attributes
                if element.get("code"):
                    file_analysis["coding_elements"][f"@code:{tag_name}"] += 1
                if element.get("codeSystem"):
                    system = element.get("codeSystem")
                    file_analysis["code_systems"][system] += 1
                    file_analysis["coding_elements"][f"@codeSystem:{tag_name}"] += 1
                if element.get("value"):
                    file_analysis["coding_elements"][f"@value:{tag_name}"] += 1

            # Find section codes specifically
            sections = root.xpath(".//section/code[@code]")
            for section_code in sections:
                code = section_code.get("code")
                system = section_code.get("codeSystem", "unknown")
                file_analysis["section_codes"][f"{code}({system[:30]}...)"] += 1

            # Sample structure
            file_analysis["structure_sample"] = {
                "root_tag": root.tag.split("}")[-1] if "}" in root.tag else root.tag,
                "total_elements": len(list(root.iter())),
                "coded_elements": len(coded_elements),
                "sections_found": len(sections),
                "has_structured_body": bool(root.xpath(".//structuredBody")),
                "has_entries": bool(root.xpath(".//entry")),
            }

        except Exception as e:
            raise Exception(f"Error parsing {file_path}: {e}")

        return file_analysis

    def generate_comparison_report(self):
        """Generate comparison report between countries"""
        print(f"\n📊 CROSS-COUNTRY COMPARISON REPORT")
        print("=" * 80)

        countries = self.analysis_results["countries"]

        # Compare namespace usage
        print(f"\n🌐 NAMESPACE VARIATIONS:")
        all_namespaces = set()
        for country, data in countries.items():
            all_namespaces.update(data["namespaces"].keys())

        for ns in sorted(all_namespaces):
            usage = []
            for country, data in countries.items():
                count = data["namespaces"].get(ns, 0)
                if count > 0:
                    usage.append(f"{country}({count})")
            print(f"   {ns[:60]}... → {', '.join(usage)}")

        # Compare code systems
        print(f"\n🏷️  CODE SYSTEM VARIATIONS:")
        all_systems = set()
        for country, data in countries.items():
            all_systems.update(data["code_systems"].keys())

        for system in sorted(all_systems):
            usage = []
            for country, data in countries.items():
                count = data["code_systems"].get(system, 0)
                if count > 0:
                    usage.append(f"{country}({count})")
            print(f"   {system} → {', '.join(usage)}")

        # Compare entry patterns
        print(f"\n📝 ENTRY PATTERN VARIATIONS:")
        all_patterns = set()
        for country, data in countries.items():
            all_patterns.update(data["coding_elements"].keys())

        for pattern in sorted(all_patterns):
            usage = []
            for country, data in countries.items():
                count = data["coding_elements"].get(pattern, 0)
                if count > 0:
                    usage.append(f"{country}({count})")
            if len(usage) > 1:  # Only show patterns used by multiple countries
                print(f"   {pattern} → {', '.join(usage)}")

    def generate_recommendations(self):
        """Generate recommendations for universal parser"""
        print(f"\n💡 PARSER RECOMMENDATIONS")
        print("=" * 80)

        # Identify common patterns
        common_systems = [
            system
            for system, count in self.analysis_results[
                "clinical_code_systems"
            ].most_common(10)
        ]
        common_patterns = [
            pattern
            for pattern, count in self.analysis_results["coding_patterns"].most_common(
                10
            )
        ]

        print(f"\n✅ UNIVERSAL PATTERNS (work across countries):")
        print(f"   🏷️  Code Systems: {common_systems[:5]}")
        print(f"   📝 Coding Patterns: {common_patterns[:5]}")

        # Identify country-specific patterns
        print(f"\n⚠️  COUNTRY-SPECIFIC VARIATIONS:")
        for country, data in self.analysis_results["countries"].items():
            unique_systems = []
            for system, count in data["code_systems"].most_common(3):
                if system not in common_systems:
                    unique_systems.append(system)

            if unique_systems:
                print(f"   🏳️  {country}: {unique_systems}")

        # Architecture recommendations
        print(f"\n🏗️  ARCHITECTURE RECOMMENDATIONS:")

        total_countries = len(self.analysis_results["countries"])
        common_threshold = total_countries * 0.7  # 70% of countries

        universal_patterns = []
        for pattern, count in self.analysis_results["coding_patterns"].most_common():
            if count >= common_threshold:
                universal_patterns.append(pattern)

        print(
            f"   1. 🌍 UNIVERSAL APPROACH: Use patterns that work for {int(common_threshold)}+ countries"
        )
        print(f"      Recommended patterns: {universal_patterns[:3]}")

        print(f"   2. 🔀 FALLBACK STRATEGY: Country-specific patterns for unique cases")

        print(f"   3. 🚀 JSON BUNDLE APPROACH: Convert all CDA → JSON, then use:")
        print(f"      - Universal JSONPath queries for common patterns")
        print(f"      - Country-specific queries for variations")
        print(f"      - Dynamic pattern detection")

        return {
            "universal_patterns": universal_patterns,
            "common_systems": common_systems,
            "recommendation": "JSON_Bundle_with_fallbacks",
        }

    def save_analysis(self, output_file: str = "eu_cda_gap_analysis.json"):
        """Save analysis results to JSON file"""
        # Convert Counter objects to regular dicts for JSON serialization
        serializable_results = {}
        for key, value in self.analysis_results.items():
            if isinstance(value, Counter):
                serializable_results[key] = dict(value)
            elif isinstance(value, defaultdict):
                serializable_results[key] = dict(value)
            elif isinstance(value, set):
                serializable_results[key] = list(value)
            else:
                serializable_results[key] = value

        # Convert nested Counter objects
        for country, data in serializable_results.get("countries", {}).items():
            for field, counter in data.items():
                if isinstance(counter, Counter):
                    data[field] = dict(counter)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Analysis saved to: {output_file}")


def main():
    """Run the gap analysis"""
    analyzer = EUCDAGapAnalysis()
    results = analyzer.run_analysis()
    analyzer.save_analysis()

    print(f"\n🎯 ANALYSIS COMPLETE!")
    print(f"Countries analyzed: {len(results['countries'])}")
    print(f"Total namespace patterns: {len(results['namespace_patterns'])}")
    print(f"Total code systems found: {len(results['clinical_code_systems'])}")
    print(f"Total coding patterns: {len(results['coding_patterns'])}")


if __name__ == "__main__":
    main()
