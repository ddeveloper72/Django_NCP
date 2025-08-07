#!/usr/bin/env python3
"""
Portuguese Patient Index Test
Check if Portuguese patient PT 2-1234-W7 is properly indexed for directory search
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()


def test_portuguese_patient_indexing():
    """Test if Portuguese patient is properly indexed in the CDA document system"""

    print("🔍 Testing Portuguese Patient Indexing System")
    print("=" * 60)

    # Check if Portuguese files exist
    pt_file_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    if not os.path.exists(pt_file_path):
        print(f"❌ Portuguese patient file not found: {pt_file_path}")
        return False

    print(f"✅ Portuguese patient file exists: {pt_file_path}")

    # Test the CDA document indexer
    try:
        from patient_data.services.cda_document_index import get_cda_indexer

        indexer = get_cda_indexer()

        # Force refresh the index to make sure it's up to date
        print("🔄 Refreshing CDA document index...")
        indexer.refresh_index()

        # Get all patients in index
        all_patients = indexer.get_all_patients()
        print(f"✅ Found {len(all_patients)} total patients in index")

        # Look for Portuguese patients
        pt_patients = [p for p in all_patients if p["country_code"].upper() == "PT"]
        print(f"✅ Found {len(pt_patients)} Portuguese patients in index")

        # Look for specific patient
        target_patient = None
        for patient in pt_patients:
            if patient["patient_id"] == "2-1234-W7":
                target_patient = patient
                break

        if target_patient:
            print(f"✅ Found target Portuguese patient in index:")
            print(f"   Patient ID: {target_patient['patient_id']}")
            print(
                f"   Name: {target_patient['given_name']} {target_patient['family_name']}"
            )
            print(f"   Country: {target_patient['country_code']}")
            print(f"   Documents: {target_patient['document_count']}")
            print(f"   CDA Types: {target_patient['cda_types']}")

            # Test document retrieval
            documents = indexer.find_patient_documents("2-1234-W7", "PT")
            print(f"✅ Document retrieval test: {len(documents)} documents found")

            for doc in documents:
                print(f"   📄 {doc.cda_type} CDA: {doc.file_path}")

            return True
        else:
            print("❌ Target patient 2-1234-W7 NOT found in index")
            print("\n📋 Available Portuguese patients:")
            for patient in pt_patients:
                print(
                    f"   • {patient['patient_id']}: {patient['given_name']} {patient['family_name']}"
                )

            # Try to manually trigger indexing of the PT directory
            print("\n🔧 Attempting manual indexing of PT directory...")
            return attempt_manual_indexing()

    except Exception as e:
        print(f"❌ Error testing CDA indexer: {e}")
        import traceback

        traceback.print_exc()
        return False


def attempt_manual_indexing():
    """Manually trigger indexing of Portuguese patient files"""

    print("🔧 Manual Portuguese Patient Indexing")
    print("-" * 40)

    try:
        from patient_data.services.cda_document_index import CDADocumentIndexer

        indexer = CDADocumentIndexer()

        # Check the base directories being scanned
        from django.conf import settings

        base_dir = getattr(settings, "BASE_DIR", ".")
        test_data_dir = os.path.join(base_dir, "test_data", "eu_member_states")

        print(f"✅ Base directory: {base_dir}")
        print(f"✅ Test data directory: {test_data_dir}")

        # Check if PT directory exists
        pt_dir = os.path.join(test_data_dir, "PT")
        if os.path.exists(pt_dir):
            print(f"✅ PT directory found: {pt_dir}")

            # List files in PT directory
            pt_files = os.listdir(pt_dir)
            xml_files = [f for f in pt_files if f.endswith(".xml")]
            print(f"✅ Found {len(xml_files)} XML files in PT directory:")
            for xml_file in xml_files:
                full_path = os.path.join(pt_dir, xml_file)
                file_size = os.path.getsize(full_path)
                print(f"   📄 {xml_file} ({file_size:,} bytes)")
        else:
            print(f"❌ PT directory not found: {pt_dir}")
            return False

        # Force rebuild index
        print("\n🔄 Force rebuilding CDA index...")
        indexer.index_cache = None  # Clear cache
        index = indexer.get_index()  # This will rebuild

        # Check again for Portuguese patients
        pt_patients = []
        for patient_id, documents in index.items():
            if documents and documents[0].country_code.upper() == "PT":
                pt_patients.append(
                    {
                        "patient_id": patient_id,
                        "given_name": documents[0].given_name,
                        "family_name": documents[0].family_name,
                        "country_code": documents[0].country_code,
                    }
                )

        print(f"✅ After rebuild: {len(pt_patients)} Portuguese patients found")

        # Look for our target patient again
        target_found = any(p["patient_id"] == "2-1234-W7" for p in pt_patients)

        if target_found:
            print("✅ Target patient 2-1234-W7 now found after rebuild!")
            return True
        else:
            print("❌ Target patient still not found after rebuild")

            # Show what was actually indexed
            print("\n📋 All indexed patients:")
            for patient_id, documents in index.items():
                if documents:
                    doc = documents[0]
                    print(
                        f"   • {patient_id} ({doc.country_code}): {doc.given_name} {doc.family_name}"
                    )

            return False

    except Exception as e:
        print(f"❌ Manual indexing error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_patient_search_service():
    """Test the actual patient search service that the UI uses"""

    print("\n🔍 Testing Patient Search Service (UI Integration)")
    print("=" * 60)

    try:
        from patient_data.services.patient_search_service import (
            EUPatientSearchService,
            PatientCredentials,
        )

        search_service = EUPatientSearchService()

        # Create credentials for Portuguese patient
        credentials = PatientCredentials(country_code="PT", patient_id="2-1234-W7")

        print(
            f"🔍 Searching for patient: {credentials.patient_id} in {credentials.country_code}"
        )

        # Perform search
        matches = search_service.search_patient(credentials)

        if matches:
            print(f"✅ Search successful! Found {len(matches)} matches")

            for i, match in enumerate(matches):
                print(f"\n📋 Match {i+1}:")
                print(f"   Patient ID: {match.patient_id}")
                print(f"   Name: {match.given_name} {match.family_name}")
                print(f"   Country: {match.country_code}")
                print(f"   Birth Date: {match.birth_date}")
                print(f"   Gender: {match.gender}")
                print(f"   Confidence: {match.confidence_score}")
                print(f"   L1 CDA: {'Yes' if match.l1_cda_content else 'No'}")
                print(f"   L3 CDA: {'Yes' if match.l3_cda_content else 'No'}")

                # Test if we can load the CDA content
                if match.l3_cda_content:
                    content_length = len(match.l3_cda_content)
                    print(f"   L3 Content Length: {content_length:,} characters")

                    # Check for Portuguese language content
                    if (
                        "pt" in match.l3_cda_content.lower()
                        or "português" in match.l3_cda_content.lower()
                    ):
                        print(f"   ✅ Portuguese language content detected")

            return True
        else:
            print("❌ No matches found for Portuguese patient")
            return False

    except Exception as e:
        print(f"❌ Patient search service error: {e}")
        import traceback

        traceback.print_exc()
        return False


def show_indexing_recommendations():
    """Show recommendations for fixing the indexing issue"""

    print("\n💡 Indexing Troubleshooting Recommendations")
    print("=" * 60)

    print("1. 🔧 Check file permissions:")
    print("   - Ensure test_data/eu_member_states/PT/ is readable")
    print("   - Verify XML files are not corrupted")

    print("\n2. 🔄 Force index rebuild:")
    print("   - The indexer may need to be manually refreshed")
    print("   - Consider clearing any cached index files")

    print("\n3. 📂 Verify directory structure:")
    print("   Expected: test_data/eu_member_states/PT/2-1234-W7.xml")
    print("   - Check country code case (PT vs pt)")
    print("   - Verify patient ID format matches file name")

    print("\n4. 🏥 XML content validation:")
    print("   - Ensure CDA has proper patient ID elements")
    print("   - Check for correct HL7 namespaces")
    print("   - Verify patient demographic information")

    print("\n5. 🎯 Next steps:")
    print("   - Run this test again after making changes")
    print("   - Check Django server logs for indexing errors")
    print("   - Test search functionality in the web UI")


def main():
    print("🇵🇹 Portuguese Patient Index Diagnostic Test")
    print("=" * 80)

    # Test 1: Check indexing
    indexing_success = test_portuguese_patient_indexing()

    # Test 2: Check search service
    search_success = test_patient_search_service()

    # Show results
    print("\n📊 DIAGNOSTIC RESULTS")
    print("=" * 40)
    print(f"Indexing System: {'✅ PASS' if indexing_success else '❌ FAIL'}")
    print(f"Search Service: {'✅ PASS' if search_success else '❌ FAIL'}")

    if indexing_success and search_success:
        print("\n🎉 Portuguese patient is properly indexed and searchable!")
        print("   You should now be able to find patient 2-1234-W7 in the UI")
    else:
        print("\n⚠️  Portuguese patient indexing needs attention")
        show_indexing_recommendations()

    print("=" * 80)


if __name__ == "__main__":
    main()
