#!/usr/bin/env python3
"""
Comprehensive EU CDA Gap Analysis
Test every CDA file in all folders and subfolders
"""

import os
import sys
import django
from pathlib import Path
from collections import defaultdict, Counter
import json
import time

# Add the Django project path
project_path = Path(__file__).parent
sys.path.insert(0, str(project_path))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAXMLParser


class ComprehensiveCDAGapAnalysis:
    """Comprehensive gap analysis of all CDA files"""

    def __init__(self):
        self.parser = EnhancedCDAXMLParser()
        self.results = {
            "summary": {
                "total_files": 0,
                "successful_parses": 0,
                "failed_parses": 0,
                "countries": set(),
                "document_types": Counter(),
                "total_sections": 0,
                "total_clinical_codes": 0,
            },
            "by_country": defaultdict(
                lambda: {
                    "files": [],
                    "successful": 0,
                    "failed": 0,
                    "total_sections": 0,
                    "total_codes": 0,
                    "errors": [],
                    "sample_patients": [],
                }
            ),
            "document_analysis": {
                "ehdsi_friendly_l3": [],
                "ehdsi_pivot_l3": [],
                "ehdsi_pivot_l1": [],
                "patient_samples": [],
                "other_formats": [],
            },
            "code_systems": Counter(),
            "section_patterns": Counter(),
            "parsing_errors": [],
        }

    def find_all_cda_files(self):
        """Find all CDA XML files in test directories"""
        test_paths = [Path("test_data"), Path("patient_data/test_data")]

        xml_files = []
        for test_path in test_paths:
            if test_path.exists():
                xml_files.extend(list(test_path.glob("**/*.xml")))

        print(f"🔍 Found {len(xml_files)} XML files across all directories")
        return xml_files

    def categorize_file(self, file_path: Path):
        """Categorize CDA file by type and country"""
        file_name = file_path.name
        file_str = str(file_path)

        # Extract country from path
        country = "UNKNOWN"
        path_parts = file_path.parts
        for i, part in enumerate(path_parts):
            if part == "eu_member_states" and i + 1 < len(path_parts):
                country = path_parts[i + 1]
                break

        # Categorize document type
        doc_type = "other"
        if "FRIENDLY-CDA-(L3)" in file_name:
            doc_type = "ehdsi_friendly_l3"
        elif "PIVOT-CDA-(L3)" in file_name:
            doc_type = "ehdsi_pivot_l3"
        elif "PIVOT-CDA-(L1)" in file_name:
            doc_type = "ehdsi_pivot_l1"
        elif any(
            name in file_name for name in ["Patient", "patient", "CDA", "clinical"]
        ):
            doc_type = "patient_sample"

        return country, doc_type

    def analyze_single_file(self, file_path: Path):
        """Analyze a single CDA file"""
        country, doc_type = self.categorize_file(file_path)

        file_analysis = {
            "file_path": str(file_path),
            "country": country,
            "doc_type": doc_type,
            "file_name": file_path.name,
            "status": "unknown",
            "sections": 0,
            "clinical_codes": 0,
            "patient_name": "",
            "error": None,
            "parsing_time": 0,
        }

        try:
            start_time = time.time()

            # Parse with Enhanced XML Parser
            result = self.parser.parse_cda_file(str(file_path))

            parsing_time = time.time() - start_time
            file_analysis["parsing_time"] = round(parsing_time, 3)

            # Extract metrics
            sections = result.get("sections", [])
            total_codes = 0

            for section in sections:
                clinical_codes = section.get("clinical_codes")
                if clinical_codes and hasattr(clinical_codes, "all_codes"):
                    total_codes += len(clinical_codes.all_codes)

                    # Collect code systems
                    for code in clinical_codes.all_codes:
                        self.results["code_systems"][code.system] += 1

                # Collect section patterns
                section_code = section.get("section_code", "")
                if section_code:
                    self.results["section_patterns"][section_code] += 1

            # Patient info
            patient = result.get("patient_identity", {})
            patient_name = f"{patient.get('given_name', '')} {patient.get('family_name', '')}".strip()

            file_analysis.update(
                {
                    "status": "success",
                    "sections": len(sections),
                    "clinical_codes": total_codes,
                    "patient_name": patient_name,
                    "patient_gender": patient.get("gender", ""),
                    "has_admin_data": result.get("has_administrative_data", False),
                }
            )

            return file_analysis

        except Exception as e:
            file_analysis.update({"status": "error", "error": str(e)})
            return file_analysis

    def run_comprehensive_analysis(self):
        """Run analysis on all CDA files"""
        print("🌍 COMPREHENSIVE EU CDA GAP ANALYSIS")
        print("=" * 80)

        # Find all files
        xml_files = self.find_all_cda_files()
        self.results["summary"]["total_files"] = len(xml_files)

        print(f"📊 Processing {len(xml_files)} files...")
        print("-" * 80)

        # Process each file
        for i, file_path in enumerate(xml_files, 1):
            print(f"📄 [{i:3d}/{len(xml_files)}] {file_path.name}")

            file_analysis = self.analyze_single_file(file_path)

            country = file_analysis["country"]
            status = file_analysis["status"]

            # Update country statistics
            self.results["by_country"][country]["files"].append(file_analysis)

            if status == "success":
                self.results["summary"]["successful_parses"] += 1
                self.results["by_country"][country]["successful"] += 1
                self.results["by_country"][country]["total_sections"] += file_analysis[
                    "sections"
                ]
                self.results["by_country"][country]["total_codes"] += file_analysis[
                    "clinical_codes"
                ]
                self.results["summary"]["total_sections"] += file_analysis["sections"]
                self.results["summary"]["total_clinical_codes"] += file_analysis[
                    "clinical_codes"
                ]

                # Add to document type analysis
                doc_type = file_analysis["doc_type"]
                self.results["document_analysis"][doc_type].append(file_analysis)

                # Sample patients
                if file_analysis["patient_name"]:
                    self.results["by_country"][country]["sample_patients"].append(
                        {
                            "name": file_analysis["patient_name"],
                            "gender": file_analysis["patient_gender"],
                            "file": file_path.name,
                        }
                    )

                print(
                    f"   ✅ {file_analysis['sections']} sections, {file_analysis['clinical_codes']} codes"
                )

            else:
                self.results["summary"]["failed_parses"] += 1
                self.results["by_country"][country]["failed"] += 1
                self.results["by_country"][country]["errors"].append(
                    {"file": file_path.name, "error": file_analysis["error"]}
                )
                self.results["parsing_errors"].append(file_analysis)
                print(f"   ❌ ERROR: {file_analysis['error']}")

            # Update document types
            self.results["summary"]["document_types"][file_analysis["doc_type"]] += 1
            self.results["summary"]["countries"].add(country)

        return self.results

    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        print(f"\n📊 COMPREHENSIVE ANALYSIS REPORT")
        print("=" * 80)

        summary = self.results["summary"]
        success_rate = (summary["successful_parses"] / summary["total_files"]) * 100

        # Overall summary
        print(f"📄 Total files analyzed: {summary['total_files']}")
        print(f"✅ Successful parses: {summary['successful_parses']}")
        print(f"❌ Failed parses: {summary['failed_parses']}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        print(f"🌍 Countries found: {len(summary['countries'])}")
        print(f"📋 Total sections extracted: {summary['total_sections']}")
        print(f"🏷️  Total clinical codes: {summary['total_clinical_codes']}")

        # Countries breakdown
        print(f"\n🏳️  COUNTRY-BY-COUNTRY ANALYSIS:")
        print("-" * 60)

        countries = sorted(self.results["by_country"].keys())
        for country in countries:
            data = self.results["by_country"][country]
            total_files = len(data["files"])
            success_rate_country = (
                (data["successful"] / total_files * 100) if total_files > 0 else 0
            )

            print(f"\n{country}:")
            print(f"   📄 Files: {total_files}")
            print(f"   ✅ Success: {data['successful']} ({success_rate_country:.1f}%)")
            print(f"   ❌ Failed: {data['failed']}")
            print(f"   📋 Sections: {data['total_sections']}")
            print(f"   🏷️  Codes: {data['total_codes']}")

            # Sample patients
            if data["sample_patients"]:
                print(
                    f"   👤 Sample patients: {', '.join([p['name'] for p in data['sample_patients'][:3]])}"
                )

            # Errors
            if data["errors"]:
                print(f"   ⚠️  Errors: {len(data['errors'])} files failed")
                for error in data["errors"][:2]:  # Show first 2 errors
                    print(f"      • {error['file']}: {error['error'][:50]}...")

        # Document types analysis
        print(f"\n📋 DOCUMENT TYPES ANALYSIS:")
        print("-" * 60)

        for doc_type, count in summary["document_types"].most_common():
            print(f"{doc_type}: {count} files")

            # Success rate by document type
            successful_docs = len(self.results["document_analysis"][doc_type])
            success_rate_doc = (successful_docs / count * 100) if count > 0 else 0
            print(f"   Success rate: {success_rate_doc:.1f}%")

        # Code systems analysis
        print(f"\n🏷️  CODE SYSTEMS FOUND:")
        print("-" * 60)

        for system, count in self.results["code_systems"].most_common(10):
            print(f"{system}: {count} codes")

        # Section patterns
        print(f"\n📋 SECTION PATTERNS:")
        print("-" * 60)

        for pattern, count in self.results["section_patterns"].most_common(10):
            print(f"{pattern}: {count} occurrences")

        # Parser assessment
        print(f"\n🏗️  ENHANCED XML PARSER ASSESSMENT:")
        print("=" * 80)

        if success_rate >= 95:
            verdict = "EXCELLENT - Works across virtually all documents"
            recommendation = (
                "✅ Enhanced XML Parser is production-ready for all EU countries"
            )
        elif success_rate >= 85:
            verdict = "VERY GOOD - High compatibility with minor issues"
            recommendation = (
                "✅ Continue with Enhanced XML Parser, address specific edge cases"
            )
        elif success_rate >= 70:
            verdict = "GOOD - Solid performance with some compatibility gaps"
            recommendation = "⚠️  Enhanced XML Parser good for most cases, consider JSON Bundle for problematic formats"
        elif success_rate >= 50:
            verdict = "FAIR - Significant compatibility issues"
            recommendation = "❗ Implement JSON Bundle parser for better coverage"
        else:
            verdict = "POOR - Major compatibility problems"
            recommendation = "❌ JSON Bundle parser essential for production use"

        print(f"Overall success rate: {success_rate:.1f}%")
        print(f"Verdict: {verdict}")
        print(f"Recommendation: {recommendation}")

        # JSON Bundle benefits analysis
        if success_rate < 95:
            print(f"\n🌐 JSON BUNDLE PARSER BENEFITS:")
            print("-" * 60)
            failed_by_country = {
                country: data["failed"]
                for country, data in self.results["by_country"].items()
                if data["failed"] > 0
            }

            if failed_by_country:
                print(f"   🔧 Would help with: {', '.join(failed_by_country.keys())}")
                print(
                    f"   📈 Potential improvement: {len(self.results['parsing_errors'])} additional successful parses"
                )
                print(f"   🎯 Target success rate: 99%+")

        # Specific recommendations
        print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
        print("=" * 80)

        if success_rate >= 95:
            print(f"1. ✅ Enhanced XML Parser is excellent for all tested countries")
            print(
                f"2. 🔧 Minor tweaks may resolve remaining {summary['failed_parses']} failures"
            )
            print(f"3. 📊 Strong foundation for production deployment")
        else:
            print(f"1. 🔧 Enhance XML parser for specific failure patterns")
            print(f"2. 🌐 Consider JSON Bundle approach for edge cases")
            print(f"3. 🎯 Target 95%+ success rate for production")

        return {
            "success_rate": success_rate,
            "verdict": verdict,
            "recommendation": recommendation,
        }

    def save_detailed_report(self, filename="comprehensive_cda_gap_analysis.json"):
        """Save detailed analysis to JSON file"""
        # Convert sets to lists for JSON serialization
        report_data = dict(self.results)
        report_data["summary"]["countries"] = list(report_data["summary"]["countries"])

        # Convert Counters to dicts
        report_data["summary"]["document_types"] = dict(
            report_data["summary"]["document_types"]
        )
        report_data["code_systems"] = dict(report_data["code_systems"])
        report_data["section_patterns"] = dict(report_data["section_patterns"])

        # Convert defaultdict to regular dict
        report_data["by_country"] = dict(report_data["by_country"])

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed analysis saved to: {filename}")


def main():
    """Run comprehensive gap analysis"""
    analyzer = ComprehensiveCDAGapAnalysis()

    start_time = time.time()
    results = analyzer.run_comprehensive_analysis()
    analysis_time = time.time() - start_time

    assessment = analyzer.generate_comprehensive_report()
    analyzer.save_detailed_report()

    print(f"\n🎯 FINAL ASSESSMENT:")
    print("=" * 80)
    print(f"Analysis completed in {analysis_time:.1f} seconds")
    print(f"Files processed: {results['summary']['total_files']}")
    print(f"Success rate: {assessment['success_rate']:.1f}%")
    print(f"Verdict: {assessment['verdict']}")
    print(f"Recommendation: {assessment['recommendation']}")

    if assessment["success_rate"] >= 90:
        print(
            f"\n🏆 CONCLUSION: Enhanced XML Parser performs excellently across EU CDA documents!"
        )
        print(f"   Your current parsing system is ready for multi-country deployment.")
    else:
        print(f"\n🔧 CONCLUSION: Enhanced XML Parser shows good compatibility.")
        print(f"   Consider JSON Bundle approach for universal coverage.")


if __name__ == "__main__":
    main()
