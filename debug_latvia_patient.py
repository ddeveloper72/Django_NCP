#!/usr/bin/env python3
"""
Debug script to check Latvia patient 241070-77726 in CDA index
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from patient_data.services.cda_document_index import get_cda_indexer
import json


def debug_latvia_patient():
    """Debug the Latvia patient search issue"""
    print("=== Latvia Patient Debug ===")

    # Get the indexer
    indexer = get_cda_indexer()
    print(f"Index file: {indexer.index_file}")
    print(f"Index exists: {os.path.exists(indexer.index_file)}")

    if not os.path.exists(indexer.index_file):
        print("No index file found - rebuilding...")
        indexer.rebuild_index()

    if os.path.exists(indexer.index_file):
        with open(indexer.index_file, "r") as f:
            index_data = json.load(f)
            print(f"Index contains {len(index_data)} documents")

            # Look for Latvia documents
            lv_docs = [doc for doc in index_data if doc.get("country_code") == "LV"]
            print(f"Latvia documents: {len(lv_docs)}")

            if lv_docs:
                print("Latvia documents found:")
                for doc in lv_docs:
                    print(f"  Patient ID: {doc.get('patient_id')}")
                    print(f"  Name: {doc.get('given_name')} {doc.get('family_name')}")
                    print(f"  File: {doc.get('file_path')}")
                    print(f"  Type: {doc.get('cda_type')}")
                    print()

            # Look for patient ID 241070-77726
            target_docs = [
                doc for doc in index_data if "241070-77726" in doc.get("patient_id", "")
            ]
            print(f"Documents with patient ID 241070-77726: {len(target_docs)}")

            if target_docs:
                for doc in target_docs:
                    print(f"  File: {doc.get('file_path')}")
                    print(f"  Type: {doc.get('cda_type')}")
                    print(f"  Country: {doc.get('country_code')}")
                    print(f"  Name: {doc.get('given_name')} {doc.get('family_name')}")
            else:
                print("❌ No documents found for patient ID 241070-77726")

            # Check if the expected files exist in the file system
            test_data_path = os.path.join(
                os.path.dirname(__file__), "test_data", "eu_member_states"
            )
            print(f"\nChecking test data directory: {test_data_path}")

            if os.path.exists(test_data_path):
                # Look for Latvia folder
                lv_path = os.path.join(test_data_path, "LV")
                if os.path.exists(lv_path):
                    print(f"Latvia folder exists: {lv_path}")
                    files = os.listdir(lv_path)
                    xml_files = [f for f in files if f.endswith(".xml")]
                    print(f"XML files in LV folder: {len(xml_files)}")

                    # Look for files containing our patient ID
                    matching_files = [f for f in xml_files if "241070-77726" in f]
                    print(f"Files with patient ID 241070-77726: {matching_files}")

                    if matching_files:
                        for file in matching_files:
                            file_path = os.path.join(lv_path, file)
                            print(f"Found file: {file_path}")

                            # Try to extract patient info from this file
                            try:
                                patient_info = indexer.extract_patient_info_from_cda(
                                    file_path
                                )
                                if patient_info:
                                    print(f"  Patient info: {patient_info}")
                                else:
                                    print("  ❌ Could not extract patient info")
                            except Exception as e:
                                print(f"  ❌ Error extracting patient info: {e}")
                else:
                    print("❌ Latvia folder not found")

                # List all country folders
                country_folders = [
                    d
                    for d in os.listdir(test_data_path)
                    if os.path.isdir(os.path.join(test_data_path, d))
                ]
                print(f"\nAvailable country folders: {country_folders}")
            else:
                print("❌ Test data directory not found")
    else:
        print("❌ Could not create or access index file")


if __name__ == "__main__":
    debug_latvia_patient()
