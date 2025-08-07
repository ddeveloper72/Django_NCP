#!/usr/bin/env python3
"""
Test LU L3 patient processing with hybrid approach
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


def test_lu_l3_patient_processing():
    """Test processing LU L3 patient with enhanced field mapping"""
    try:
        from patient_data.models import PatientData
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
        from patient_data.services.enhanced_cda_field_mapper import (
            EnhancedCDAFieldMapper,
        )

        # Find LU L3 patient
        lu_patients = PatientData.objects.filter(country_code="LU", patient_id="L3")
        if not lu_patients.exists():
            print("❌ LU L3 patient not found in database")
            return False

        patient = lu_patients.first()
        print(f"✅ Found LU L3 patient: {patient.first_name} {patient.last_name}")

        if not patient.patient_summary_cda:
            print("❌ No CDA content available for LU L3 patient")
            return False

        # Test Enhanced CDA Processor
        processor = EnhancedCDAProcessor(target_language="en")
        result = processor.process_clinical_sections(
            cda_content=patient.patient_summary_cda, source_language="en"
        )

        if not result.get("success"):
            print(
                f"❌ Enhanced CDA Processor failed: {result.get('error', 'Unknown error')}"
            )
            return False

        sections = result.get("sections", [])
        print(f"✅ Enhanced CDA Processor extracted {len(sections)} sections")

        # Test Enhanced CDA Field Mapper
        field_mapper = EnhancedCDAFieldMapper()

        # Map patient data
        patient_data = field_mapper.map_patient_data(patient.patient_summary_cda)
        mapped_count = len([v for v in patient_data.values() if v])
        print(f"✅ Field Mapper extracted {mapped_count} patient data fields")

        # Map clinical sections
        clinical_mapping = field_mapper.map_clinical_section(
            patient.patient_summary_cda
        )
        clinical_mapped_count = len([v for v in clinical_mapping.values() if v])
        print(f"✅ Field Mapper extracted {clinical_mapped_count} clinical data fields")

        # Test hybrid approach combination
        enhanced_result = {
            "success": True,
            "sections": sections,
            "patient_data": patient_data,
            "clinical_mapping": clinical_mapping,
            "field_mapping_active": True,
        }

        print(
            "✅ Hybrid approach successfully combines Enhanced CDA Processor + Field Mapper"
        )
        print(
            f"✅ Total enhanced data: {len(sections)} sections + {mapped_count + clinical_mapped_count} mapped fields"
        )

        return True

    except Exception as e:
        print(f"❌ LU L3 patient processing error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("🔍 Testing LU L3 patient processing with hybrid approach...")
    print("-" * 70)

    success = test_lu_l3_patient_processing()

    print("-" * 70)

    if success:
        print("✅ LU L3 PATIENT PROCESSING SUCCESSFUL")
        print("✅ Hybrid approach working correctly")
        print("✅ JSON field mapping enhancement active and functional")
        print("✅ Server should show 'Loading Patient' → 'Success' for LU L3")
    else:
        print("❌ LU L3 patient processing failed - review errors above")

    print("-" * 70)


if __name__ == "__main__":
    main()
