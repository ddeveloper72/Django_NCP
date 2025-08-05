#!/usr/bin/env python3
"""
Comprehensive European CDA Document Analysis
Analyzes all European CDA documents to determine structure type and clinical sections support
"""

import os
import sys
import django
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import Dict, List, Any, Optional

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for mass analysis
    format="%(levelname)s %(message)s",
    stream=sys.stdout,
)

# Add project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor


class CDADocumentAnalyzer:
    """Analyzes CDA documents to determine structure and compatibility"""

    def __init__(self):
        self.processor = EnhancedCDAProcessor(target_language="en")

    def analyze_cda_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze CDA document structure without full processing

        Returns:
            Dictionary with analysis results including:
            - document_type: L1, L2, L3, or UNKNOWN
            - has_clinical_sections: boolean
            - has_base64_content: boolean
            - language: detected language
            - sections_count: estimated number of sections
            - is_processable: whether our processor can handle it
        """

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": len(content),
                "is_xml": False,
                "document_type": "UNKNOWN",
                "has_clinical_sections": False,
                "has_base64_content": False,
                "language": "UNKNOWN",
                "sections_count": 0,
                "section_codes": [],
                "is_processable": False,
                "structure_indicators": [],
                "error": None,
            }

            # Basic XML validation
            try:
                root = ET.fromstring(content)
                analysis["is_xml"] = True

                # Extract language
                language_elem = root.find(".//{urn:hl7-org:v3}languageCode")
                if language_elem is not None:
                    lang_code = language_elem.get("code", "")
                    analysis["language"] = lang_code

                # Analyze document structure
                analysis.update(self._analyze_xml_structure(root, content))

            except ET.ParseError as e:
                analysis["error"] = f"XML Parse Error: {e}"
                analysis["is_xml"] = False
                # Try HTML analysis as fallback
                analysis.update(self._analyze_html_structure(content))

            return analysis

        except Exception as e:
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "error": f"File reading error: {e}",
                "is_processable": False,
            }

    def _analyze_xml_structure(self, root, content: str) -> Dict[str, Any]:
        """Analyze XML CDA structure"""

        namespaces = {
            "hl7": "urn:hl7-org:v3",
            "ext": "urn:hl7-EE-DL-Ext:v1",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

        analysis = {
            "structure_indicators": [],
            "sections_count": 0,
            "section_codes": [],
            "has_clinical_sections": False,
            "has_base64_content": False,
            "document_type": "UNKNOWN",
            "is_processable": False,
        }

        # Check for different CDA levels

        # L1: Non-XML body (PDF content)
        non_xml_body = root.find(".//hl7:nonXMLBody", namespaces)
        if non_xml_body is not None:
            analysis["structure_indicators"].append("nonXMLBody (L1/L2)")
            analysis["has_base64_content"] = True

            # Check if there are also structured sections (mixed L2/L3)
            sections = root.findall(".//hl7:section", namespaces)
            if sections:
                analysis["document_type"] = "L2_MIXED"
                analysis["structure_indicators"].append("Mixed: PDF + Sections")
            else:
                analysis["document_type"] = "L1"
                analysis["structure_indicators"].append("Pure PDF content")

        # L3: Structured sections
        sections = root.findall(".//hl7:section", namespaces)
        if sections:
            analysis["has_clinical_sections"] = True
            analysis["sections_count"] = len(sections)
            analysis["structure_indicators"].append(
                f"{len(sections)} structured sections"
            )

            # Extract section codes
            for section in sections:
                code_elem = section.find("hl7:code", namespaces)
                if code_elem is not None:
                    code = code_elem.get("code", "")
                    if code:
                        analysis["section_codes"].append(code)

            # Determine if it's L3 or mixed
            if analysis["document_type"] == "UNKNOWN":
                analysis["document_type"] = "L3"
                analysis["structure_indicators"].append("Pure structured XML")

        # Check for structured entries (high-level L3)
        entries = root.findall(".//hl7:entry", namespaces)
        if entries:
            analysis["structure_indicators"].append(
                f"{len(entries)} structured entries"
            )

        # Check for tables
        tables = root.findall(".//hl7:table", namespaces)
        if tables:
            analysis["structure_indicators"].append(f"{len(tables)} XML tables")

        # Determine processability
        analysis["is_processable"] = analysis["has_clinical_sections"] or analysis[
            "document_type"
        ] in ["L3", "L2_MIXED"]

        return analysis

    def _analyze_html_structure(self, content: str) -> Dict[str, Any]:
        """Analyze HTML CDA structure as fallback"""

        analysis = {
            "structure_indicators": ["HTML content"],
            "sections_count": 0,
            "section_codes": [],
            "has_clinical_sections": False,
            "has_base64_content": False,
            "document_type": "HTML",
            "is_processable": False,
        }

        # Check for sections in HTML
        section_patterns = [
            r'<div[^>]*class="[^"]*section[^"]*"',
            r"<section",
            r"<h[1-6][^>]*>",
        ]

        section_count = 0
        for pattern in section_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            section_count += len(matches)

        if section_count > 0:
            analysis["has_clinical_sections"] = True
            analysis["sections_count"] = section_count
            analysis["structure_indicators"].append(f"{section_count} HTML sections")
            analysis["is_processable"] = True

        # Check for base64 content
        if "base64" in content.lower():
            analysis["has_base64_content"] = True
            analysis["structure_indicators"].append("Contains base64 content")

        return analysis

    def test_processing_capability(self, file_path: str) -> Dict[str, Any]:
        """Test if our Enhanced CDA Processor can handle the document"""

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract language for testing
            language_match = re.search(r'languageCode code="([^"]+)"', content)
            source_language = (
                language_match.group(1).split("-")[0] if language_match else "en"
            )

            # Quick test processing
            result = self.processor.process_clinical_sections(
                cda_content=content, source_language=source_language
            )

            return {
                "processing_success": result.get("success", False),
                "sections_found": result.get("sections_count", 0),
                "medical_terms": result.get("medical_terms_count", 0),
                "coded_sections": result.get("coded_sections_count", 0),
                "content_type": result.get("content_type", "unknown"),
                "error": result.get("error", None),
            }

        except Exception as e:
            return {
                "processing_success": False,
                "error": f"Processing test failed: {e}",
                "sections_found": 0,
            }


def analyze_all_european_cdas():
    """Analyze all European CDA documents in the test data directory"""

    analyzer = CDADocumentAnalyzer()

    # Find all CDA XML files
    test_data_dir = Path("test_data/eu_member_states")
    if not test_data_dir.exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        return

    cda_files = list(test_data_dir.rglob("*.xml"))

    print(f"🔍 Found {len(cda_files)} CDA documents to analyze")
    print("=" * 80)

    results = {
        "total_files": len(cda_files),
        "by_country": {},
        "by_document_type": {},
        "processable_count": 0,
        "structured_count": 0,
        "analysis_details": [],
    }

    for file_path in cda_files:
        # Extract country code from path
        country_code = None
        path_parts = file_path.parts
        for part in path_parts:
            if len(part) == 2 and part.isupper():
                country_code = part
                break

        if not country_code:
            country_code = "UNKNOWN"

        # Perform analysis
        print(f"\n📄 Analyzing: {file_path.name}")
        print(f"   Country: {country_code}")

        analysis = analyzer.analyze_cda_structure(str(file_path))

        # Test processing if document looks processable
        if analysis.get("is_processable", False):
            processing_test = analyzer.test_processing_capability(str(file_path))
            analysis["processing_test"] = processing_test

        # Display results
        print(f"   Language: {analysis.get('language', 'UNKNOWN')}")
        print(f"   Type: {analysis.get('document_type', 'UNKNOWN')}")
        print(f"   Sections: {analysis.get('sections_count', 0)}")
        print(f"   Processable: {'✅' if analysis.get('is_processable') else '❌'}")

        if analysis.get("processing_test"):
            test = analysis["processing_test"]
            print(f"   Processing Test: {'✅' if test['processing_success'] else '❌'}")
            if test["processing_success"]:
                print(f"   Found Clinical Sections: {test['sections_found']}")

        if analysis.get("structure_indicators"):
            print(f"   Structure: {', '.join(analysis['structure_indicators'])}")

        if analysis.get("error"):
            print(f"   ❌ Error: {analysis['error']}")

        # Update statistics
        if country_code not in results["by_country"]:
            results["by_country"][country_code] = []
        results["by_country"][country_code].append(analysis)

        doc_type = analysis.get("document_type", "UNKNOWN")
        if doc_type not in results["by_document_type"]:
            results["by_document_type"][doc_type] = 0
        results["by_document_type"][doc_type] += 1

        if analysis.get("is_processable"):
            results["processable_count"] += 1

        if analysis.get("has_clinical_sections"):
            results["structured_count"] += 1

        results["analysis_details"].append(analysis)

    # Print summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 80)

    print(f"\n📈 Overall Statistics:")
    print(f"   Total Documents: {results['total_files']}")
    print(
        f"   Processable Documents: {results['processable_count']} ({results['processable_count']/results['total_files']*100:.1f}%)"
    )
    print(
        f"   With Clinical Sections: {results['structured_count']} ({results['structured_count']/results['total_files']*100:.1f}%)"
    )

    print(f"\n🌍 By Country:")
    for country, documents in results["by_country"].items():
        processable = sum(1 for doc in documents if doc.get("is_processable"))
        print(f"   {country}: {len(documents)} documents, {processable} processable")

    print(f"\n📋 By Document Type:")
    for doc_type, count in results["by_document_type"].items():
        print(f"   {doc_type}: {count} documents")

    # Identify best candidates for testing
    print(f"\n🎯 Best Candidates for Enhanced CDA Processor:")
    best_candidates = [
        doc
        for doc in results["analysis_details"]
        if doc.get("is_processable") and doc.get("sections_count", 0) > 0
    ]

    for doc in best_candidates[:10]:  # Show top 10
        print(f"   ✅ {doc['file_name']}")
        print(f"      Country: {doc.get('language', 'Unknown')}")
        print(f"      Sections: {doc.get('sections_count', 0)}")
        print(f"      Codes: {', '.join(doc.get('section_codes', [])[:3])}...")

    return results


if __name__ == "__main__":
    print("🔬 Comprehensive European CDA Document Analysis")
    print("=" * 80)

    results = analyze_all_european_cdas()

    print(f"\n✅ Analysis completed!")
    print(
        f"Found {results['processable_count']} processable documents out of {results['total_files']} total."
    )
