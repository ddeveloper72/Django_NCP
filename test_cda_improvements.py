#!/usr/bin/env python
"""
Test script for CDA improvements:
1. Clinical sections extraction for L3 CDA
2. ORCD PDF extraction for L1 CDA
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.cda_translation_manager import CDATranslationManager
from patient_data.services.clinical_pdf_service import ClinicalDocumentPDFService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_clinical_sections():
    """Test clinical sections extraction from L3 CDA"""
    print("\n=== Testing Clinical Sections Extraction ===")

    # Find an L3 CDA file
    test_data_path = "test_data/eu_member_states"
    l3_files = []

    for root, dirs, files in os.walk(test_data_path):
        for file in files:
            if (
                file.endswith(".xml") and "L3" not in file
            ):  # Most XML files are L3 format
                l3_files.append(os.path.join(root, file))
                if len(l3_files) >= 3:  # Test with a few files
                    break
        if len(l3_files) >= 3:
            break

    if not l3_files:
        print("No L3 CDA files found for testing")
        return

    translation_manager = CDATranslationManager(target_language="en")

    for file_path in l3_files[:2]:  # Test first 2 files
        print(f"\nTesting file: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cda_content = f.read()

            print(f"Content length: {len(cda_content)} characters")

            # Check if content looks like HTML (transformed) or XML (raw)
            is_html = (
                cda_content.strip().lower().startswith("<!doctype html")
                or "<html" in cda_content.lower()
            )
            print(f"Content type: {'HTML (transformed)' if is_html else 'XML (raw)'}")

            # Process for clinical sections
            result = translation_manager.process_cda_for_viewer(cda_content, "fr")

            if result.get("success"):
                sections = result.get("clinical_sections", [])
                print(f"✓ Found {len(sections)} clinical sections")

                for i, section in enumerate(sections[:3]):  # Show first 3 sections
                    title = section.get("title", "Unknown")
                    content_length = len(section.get("original_content", ""))
                    has_codes = section.get("has_coded_elements", False)
                    print(
                        f"  Section {i+1}: {title[:50]}... ({content_length} chars, coded: {has_codes})"
                    )
            else:
                print(f"✗ Processing failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")


def test_orcd_extraction():
    """Test ORCD PDF extraction from L1 CDA"""
    print("\n=== Testing ORCD PDF Extraction ===")

    # Look for L1 CDA files (typically contain embedded PDFs)
    test_data_path = "test_data/eu_member_states"
    l1_files = []

    for root, dirs, files in os.walk(test_data_path):
        for file in files:
            if file.endswith(".xml") and (
                "L1" in file or "ORCD" in file or "orcd" in file.lower()
            ):
                l1_files.append(os.path.join(root, file))
                if len(l1_files) >= 3:
                    break
        if len(l1_files) >= 3:
            break

    if not l1_files:
        print("No L1/ORCD CDA files found for testing")
        return

    pdf_service = ClinicalDocumentPDFService()

    for file_path in l1_files[:2]:  # Test first 2 files
        print(f"\nTesting file: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cda_content = f.read()

            print(f"Content length: {len(cda_content)} characters")

            # Extract PDFs
            pdf_attachments = pdf_service.extract_pdfs_from_xml(cda_content)

            if pdf_attachments:
                print(f"✓ Found {len(pdf_attachments)} PDF attachments")

                for i, pdf_info in enumerate(pdf_attachments):
                    size_kb = pdf_info["size"] / 1024
                    media_type = pdf_info.get("media_type", "unknown")
                    print(
                        f"  PDF {i+1}: {pdf_info['filename']} ({size_kb:.1f} KB, {media_type})"
                    )
            else:
                print("✗ No PDF attachments found")

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")


def test_both_systems():
    """Test both systems with sample data"""
    print("\n=== Testing Complete Workflow ===")

    # Create sample session data like what would be generated
    sample_match_data = {
        "file_path": "test_data/sample.xml",
        "country_code": "LU",
        "confidence_score": 0.95,
        "patient_data": {
            "given_name": "Mario",
            "family_name": "PINO",
            "birth_date": "1990-01-01",
            "gender": "M",
        },
        "cda_content": "<sample>content</sample>",
        "l3_cda_content": None,
        "l1_cda_content": None,
    }

    print("Sample match data structure:")
    for key, value in sample_match_data.items():
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}... ({len(value)} chars)")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    print("Testing CDA improvements...")
    test_clinical_sections()
    test_orcd_extraction()
    test_both_systems()
    print("\nTesting complete!")
