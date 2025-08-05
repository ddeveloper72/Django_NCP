#!/usr/bin/env python3
"""
Comprehensive test of data extraction across all EU member state CDA documents.
Tests the fixed extractors against the complete dataset.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from patient_data.utils.administrative_extractor import EnhancedAdministrativeExtractor


# Simple parser for contact card compatibility (inline for testing)
class SimpleContactCardParser:
    def parse_administrative_data(self, administrative_data):
        """Simple parser to transform administrative_data to contact card format"""
        contact_entities = []

        # Add authors as contact entities
        for author in administrative_data.get("authors", []):
            contact_entities.append(
                {
                    "name": author.get("name", "Unknown Author"),
                    "title": "Author",
                    "organization": author.get("organization", ""),
                    "contact_info": author.get("contact_info", []),
                }
            )

        # Add legal authenticators
        for auth in administrative_data.get("legal_authenticators", []):
            contact_entities.append(
                {
                    "name": auth.get("name", "Unknown Legal Authenticator"),
                    "title": "Legal Authenticator",
                    "organization": auth.get("organization", ""),
                    "contact_info": auth.get("contact_info", []),
                }
            )

        # Add custodians
        for custodian in administrative_data.get("custodians", []):
            contact_entities.append(
                {
                    "name": custodian.get("organization", "Unknown Custodian"),
                    "title": "Custodian",
                    "organization": custodian.get("organization", ""),
                    "contact_info": custodian.get("contact_info", []),
                }
            )

        return {
            "contact_entities": contact_entities,
            "patient_info": administrative_data.get("patient", {}),
        }


def test_all_eu_member_states():
    """Test extraction across all EU member state CDA documents."""

    base_path = "test_data/eu_member_states"

    if not os.path.exists(base_path):
        print(f"❌ Base path not found: {base_path}")
        return

    print("🌍 COMPREHENSIVE EU MEMBER STATE EXTRACTION TEST")
    print("=" * 60)
    print(f"Testing extraction fixes across all EU member state documents")
    print(f"Base path: {base_path}")
    print()

    # Results tracking
    results = {
        "test_date": datetime.now().isoformat(),
        "countries": {},
        "summary": {
            "total_countries": 0,
            "total_files": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "files_with_authors": 0,
            "files_with_patient_names": 0,
            "files_with_custodians": 0,
            "files_with_legal_auth": 0,
        },
    }

    admin_extractor = EnhancedAdministrativeExtractor()
    parser = SimpleContactCardParser()

    # Scan all country directories
    country_dirs = [
        d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))
    ]
    country_dirs.sort()

    results["summary"]["total_countries"] = len(country_dirs)

    for country in country_dirs:
        country_path = os.path.join(base_path, country)
        print(f"🇪🇺 Testing {country}...")

        country_results = {
            "files": [],
            "total_files": 0,
            "successful_extractions": 0,
            "files_with_authors": 0,
            "files_with_patient_names": 0,
            "files_with_custodians": 0,
            "files_with_legal_auth": 0,
        }

        # Find all XML files in country directory
        xml_files = [f for f in os.listdir(country_path) if f.endswith(".xml")]
        country_results["total_files"] = len(xml_files)
        results["summary"]["total_files"] += len(xml_files)

        for xml_file in xml_files:
            file_path = os.path.join(country_path, xml_file)

            file_result = {
                "filename": xml_file,
                "parse_success": False,
                "patient_name": None,
                "patient_id": None,
                "authors_count": 0,
                "custodians_count": 0,
                "legal_auth_count": 0,
                "contact_entities_count": 0,
                "extraction_error": None,
            }

            try:
                # Parse XML
                tree = ET.parse(file_path)
                root = tree.getroot()
                file_result["parse_success"] = True
                results["summary"]["successful_parses"] += 1

                # Extract administrative data
                administrative_data = admin_extractor.extract_administrative_section(
                    root
                )

                # Check patient info
                patient_info = administrative_data.get("patient", {})
                if patient_info.get("name"):
                    file_result["patient_name"] = patient_info["name"]
                    country_results["files_with_patient_names"] += 1
                    results["summary"]["files_with_patient_names"] += 1

                if patient_info.get("patient_id"):
                    file_result["patient_id"] = patient_info["patient_id"]

                # Check authors
                authors = administrative_data.get("authors", [])
                file_result["authors_count"] = len(authors)
                if len(authors) > 0:
                    country_results["files_with_authors"] += 1
                    results["summary"]["files_with_authors"] += 1

                # Check custodians
                custodians = administrative_data.get("custodians", [])
                file_result["custodians_count"] = len(custodians)
                if len(custodians) > 0:
                    country_results["files_with_custodians"] += 1
                    results["summary"]["files_with_custodians"] += 1

                # Check legal authenticators
                legal_auth = administrative_data.get("legal_authenticators", [])
                file_result["legal_auth_count"] = len(legal_auth)
                if len(legal_auth) > 0:
                    country_results["files_with_legal_auth"] += 1
                    results["summary"]["files_with_legal_auth"] += 1

                # Test contact card transformation
                administrative_info = parser.parse_administrative_data(
                    administrative_data
                )
                contact_entities = administrative_info.get("contact_entities", [])
                file_result["contact_entities_count"] = len(contact_entities)

                country_results["successful_extractions"] += 1

            except Exception as e:
                file_result["extraction_error"] = str(e)
                results["summary"]["failed_parses"] += 1
                print(f"    ❌ Error processing {xml_file}: {str(e)}")

            country_results["files"].append(file_result)

        # Print country summary
        print(f"    Files: {country_results['total_files']}")
        print(
            f"    ✅ Successful extractions: {country_results['successful_extractions']}"
        )
        print(
            f"    👤 Files with patient names: {country_results['files_with_patient_names']}"
        )
        print(f"    ✍️ Files with authors: {country_results['files_with_authors']}")
        print(
            f"    🏥 Files with custodians: {country_results['files_with_custodians']}"
        )
        print(
            f"    📋 Files with legal auth: {country_results['files_with_legal_auth']}"
        )
        print()

        results["countries"][country] = country_results

    # Print overall summary
    print("📊 OVERALL TEST RESULTS")
    print("=" * 40)
    print(f"Countries tested: {results['summary']['total_countries']}")
    print(f"Total files: {results['summary']['total_files']}")
    print(f"✅ Successful parses: {results['summary']['successful_parses']}")
    print(f"❌ Failed parses: {results['summary']['failed_parses']}")
    print()
    print("EXTRACTION SUCCESS RATES:")
    total_files = results["summary"]["total_files"]
    if total_files > 0:
        print(
            f"👤 Patient names: {results['summary']['files_with_patient_names']}/{total_files} ({results['summary']['files_with_patient_names']/total_files*100:.1f}%)"
        )
        print(
            f"✍️ Authors: {results['summary']['files_with_authors']}/{total_files} ({results['summary']['files_with_authors']/total_files*100:.1f}%)"
        )
        print(
            f"🏥 Custodians: {results['summary']['files_with_custodians']}/{total_files} ({results['summary']['files_with_custodians']/total_files*100:.1f}%)"
        )
        print(
            f"📋 Legal authenticators: {results['summary']['files_with_legal_auth']}/{total_files} ({results['summary']['files_with_legal_auth']/total_files*100:.1f}%)"
        )

    # Save detailed results
    with open("eu_extraction_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to: eu_extraction_test_results.json")

    # Show top performers
    print("\n🏆 TOP PERFORMING COUNTRIES:")
    country_scores = []
    for country, data in results["countries"].items():
        if data["total_files"] > 0:
            score = (
                (
                    data["files_with_patient_names"]
                    + data["files_with_authors"]
                    + data["files_with_custodians"]
                    + data["files_with_legal_auth"]
                )
                / (data["total_files"] * 4)
                * 100
            )
            country_scores.append((country, score, data["total_files"]))

    country_scores.sort(key=lambda x: x[1], reverse=True)
    for i, (country, score, files) in enumerate(country_scores[:5], 1):
        print(f"  {i}. {country}: {score:.1f}% extraction success ({files} files)")

    # Identify problem areas
    print("\n⚠️ AREAS NEEDING ATTENTION:")
    if results["summary"]["files_with_patient_names"] < total_files * 0.5:
        print("  • Patient name extraction needs improvement")
    if results["summary"]["files_with_authors"] < total_files * 0.5:
        print("  • Author extraction needs improvement")
    if results["summary"]["failed_parses"] > 0:
        print(f"  • {results['summary']['failed_parses']} files failed to parse")

    print("\n✅ Comprehensive extraction test completed!")


if __name__ == "__main__":
    test_all_eu_member_states()
