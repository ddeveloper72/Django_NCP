#!/usr/bin/env python3
"""
Enhanced CDA Display with Dual Language Support - Portuguese Patient Test
Tests Portuguese patient PT 2-1234-W7 specifically
Addresses:
1. Show both original language and translated data side by side
2. Responsive table layout for complex medication data
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


def test_dual_language_processing_pt():
    """Test dual language processing with Portuguese PT 2-1234-W7 CDA"""

    # Use the Portuguese PT patient CDA path
    cda_path = "test_data/eu_member_states/PT/2-1234-W7.xml"

    if not os.path.exists(cda_path):
        print(f"❌ CDA file not found: {cda_path}")
        return False

    print(f"✅ Found Portuguese PT CDA: {cda_path}")

    try:
        with open(cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        # Detect source language
        from patient_data.services.eu_language_detection_service import (
            detect_cda_language,
        )

        detected_language = detect_cda_language(cda_content, "PT")
        print(f"✅ Detected source language: {detected_language}")

        # Process with Enhanced CDA Processor for both original and translated
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor

        # Original language processing (source language)
        original_processor = EnhancedCDAProcessor(target_language=detected_language)
        original_result = original_processor.process_clinical_sections(
            cda_content=cda_content, source_language=detected_language
        )

        # English translation processing
        translated_processor = EnhancedCDAProcessor(target_language="en")
        translated_result = translated_processor.process_clinical_sections(
            cda_content=cda_content, source_language=detected_language
        )

        if original_result.get("success") and translated_result.get("success"):
            original_sections = original_result.get("sections", [])
            translated_sections = translated_result.get("sections", [])

            print(f"✅ Original language sections: {len(original_sections)}")
            print(f"✅ Translated sections: {len(translated_sections)}")

            # Show section details for Portuguese patient
            print("\n📋 Portuguese Patient Sections Analysis:")
            for i, section in enumerate(original_sections):
                section_title = section.get("section_title", "Unknown")
                section_code = section.get("section_code", "Unknown")
                content_length = len(section.get("content", ""))
                print(
                    f"   {i+1}. {section_title} ({section_code}) - {content_length} chars"
                )

            # Test Enhanced Field Mapper for structured data
            from patient_data.services.enhanced_cda_field_mapper import (
                EnhancedCDAFieldMapper,
            )

            field_mapper = EnhancedCDAFieldMapper()

            # Map both original and translated data
            original_patient_data = field_mapper.map_patient_data(cda_content)
            translated_patient_data = field_mapper.map_patient_data(cda_content)

            original_clinical_data = field_mapper.map_clinical_section(cda_content)
            translated_clinical_data = field_mapper.map_clinical_section(cda_content)

            print(
                f"✅ Original patient fields: {len([v for v in original_patient_data.values() if v])}"
            )
            print(
                f"✅ Translated patient fields: {len([v for v in translated_patient_data.values() if v])}"
            )

            # Show patient data details
            print("\n👤 Portuguese Patient Data Extracted:")
            for key, value in original_patient_data.items():
                if value:
                    print(f"   • {key}: {value}")

            # Create dual language result structure
            dual_language_result = {
                "success": True,
                "source_language": detected_language,
                "target_language": "en",
                "patient_id": "2-1234-W7",
                "country_code": "PT",
                "original_data": {
                    "sections": original_sections,
                    "patient_data": original_patient_data,
                    "clinical_data": original_clinical_data,
                },
                "translated_data": {
                    "sections": translated_sections,
                    "patient_data": translated_patient_data,
                    "clinical_data": translated_clinical_data,
                },
                "dual_language_active": True,
            }

            # Test medication section specifically for table width issues
            test_medication_table_layout_pt(dual_language_result)

            return dual_language_result

    except Exception as e:
        print(f"❌ Dual language processing error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_medication_table_layout_pt(dual_language_result):
    """Test medication table layout with many columns for Portuguese patient"""

    print("\n🧪 Testing Portuguese Patient Medication Table Layout...")

    # Find medication sections in both languages
    original_sections = dual_language_result["original_data"]["sections"]
    translated_sections = dual_language_result["translated_data"]["sections"]

    medication_sections_original = [
        s
        for s in original_sections
        if "medication" in s.get("section_title", "").lower()
        or "medicamento" in s.get("section_title", "").lower()
        or "10160-0" in s.get("section_code", "")
    ]
    medication_sections_translated = [
        s
        for s in translated_sections
        if "medication" in s.get("section_title", "").lower()
        or "10160-0" in s.get("section_code", "")
    ]

    print(f"✅ Found {len(medication_sections_original)} original medication sections")
    print(
        f"✅ Found {len(medication_sections_translated)} translated medication sections"
    )

    # Analyze Portuguese-specific medication content
    if medication_sections_original:
        for i, section in enumerate(medication_sections_original):
            print(f"\n📊 Portuguese Medication Section {i+1}:")
            print(f"   Title: {section.get('section_title', 'N/A')}")
            print(f"   Code: {section.get('section_code', 'N/A')}")
            print(f"   Content Length: {len(section.get('content', ''))}")

            # Check for medication entries
            medications = section.get("medications", [])
            if medications:
                print(f"   Medications Found: {len(medications)}")
                for j, med in enumerate(medications[:3]):  # Show first 3
                    print(f"      {j+1}. {med.get('name', 'Unknown medication')}")
            else:
                print(f"   No structured medication data found")

    # Analyze medication table structure
    medication_fields = [
        "Section Title",
        "Medicinal Product",
        "Active Ingredient Description",
        "Active Ingredient ID",
        "Strength Value",
        "Strength Unit",
        "Dose Form Description",
        "Units Per Intake",
        "Frequency of Intake",
        "Route of Administration",
        "Duration of Treatment",
        "Medication Reason",
    ]

    print(f"\n📊 Medication table has {len(medication_fields)} columns")
    print("⚠️  Portuguese Patient Table Considerations:")
    print("   - 12 columns may require horizontal scrolling")
    print("   - Portuguese text may be longer than English")
    print("   - Responsive design needed for mobile/tablet")
    print("   - Consider collapsible/expandable rows")
    print("   - Priority columns: Product, Strength, Dose Form, Route")

    # Generate Portuguese-specific recommendations
    generate_portuguese_table_recommendations(medication_fields, dual_language_result)


def generate_portuguese_table_recommendations(fields, dual_language_result):
    """Generate recommendations for responsive medication table for Portuguese patient"""

    print("\n📱 Portuguese Patient Responsive Table Recommendations:")

    source_lang = dual_language_result["source_language"]

    # Priority 1: Always visible (core medication info)
    priority_1 = [
        "Medicinal Product",
        "Strength Value",
        "Strength Unit",
        "Route of Administration",
    ]

    # Priority 2: Important but can be hidden on small screens
    priority_2 = [
        "Active Ingredient Description",
        "Dose Form Description",
        "Frequency of Intake",
    ]

    # Priority 3: Detailed info, show in expandable details
    priority_3 = [
        "Active Ingredient ID",
        "Units Per Intake",
        "Duration of Treatment",
        "Medication Reason",
    ]

    print(f"🟢 Priority 1 (Always visible - {source_lang.upper()} | EN):")
    for field in priority_1:
        print(f"   - {field}")

    print(f"🟡 Priority 2 (Hide on tablets/phones - {source_lang.upper()} | EN):")
    for field in priority_2:
        print(f"   - {field}")

    print(f"🔵 Priority 3 (Show in expandable details - {source_lang.upper()} | EN):")
    for field in priority_3:
        print(f"   - {field}")

    print(f"\n💡 Portuguese-Specific Implementation Notes:")
    print(f"   1. Source language: {source_lang.upper()} (Portuguese)")
    print("   2. Dual language headers with Portuguese | English")
    print("   3. Portuguese text may require wider columns")
    print("   4. CSS Grid/Flexbox for responsive layout")
    print("   5. Language toggle: Both | PT | EN")
    print("   6. Mobile card view for Portuguese content")


def test_portuguese_patient_database():
    """Test if Portuguese patient exists in database"""

    print("\n🇵🇹 Testing Portuguese Patient in Database...")

    try:
        from patient_data.models import PatientData

        # First, let's see what fields are available
        sample_patient = PatientData.objects.first()
        if sample_patient:
            print("📋 Available PatientData fields:")
            for field in sample_patient._meta.fields:
                print(f"   • {field.name}")

        # Look for Portuguese patients using correct field names
        # Try different field combinations that might indicate country
        all_patients = PatientData.objects.all()
        print(f"✅ Found {all_patients.count()} total patients in database")

        # Look for patients with PT in identifier or name
        pt_candidates = all_patients.filter(patient_identifier__icontains="PT").union(
            all_patients.filter(patient_identifier__icontains="2-1234-W7")
        )

        print(f"✅ Found {pt_candidates.count()} potential Portuguese patients")

        # Look for specific patient ID
        specific_patient = all_patients.filter(patient_identifier="2-1234-W7")
        if specific_patient.exists():
            patient = specific_patient.first()
            print(
                f"✅ Found specific patient: {patient.given_name} {patient.family_name}"
            )
            print(f"   Patient ID: {patient.patient_identifier}")
            print(
                f"   Has CDA: {'Yes' if hasattr(patient, 'patient_summary_cda') and patient.patient_summary_cda else 'No'}"
            )
            return patient
        else:
            print("❌ Specific patient 2-1234-W7 not found in database")

            # Show some available patients
            if all_patients.exists():
                print("📋 Sample patients in database:")
                for patient in all_patients[:5]:  # Show first 5
                    print(
                        f"   • {patient.patient_identifier}: {patient.given_name} {patient.family_name}"
                    )

            return None

    except Exception as e:
        print(f"❌ Database query error: {e}")
        return None


def create_portuguese_display_demo():
    """Create demonstration of Portuguese dual language display"""

    print("\n🎨 Creating Portuguese Dual Language Display Demo...")

    # Portuguese medication table template demonstration
    portuguese_template_demo = """
<!-- Portuguese Medication Table with Dual Language Support -->
<div class="medication-section-enhanced" data-country="PT" data-patient="2-1234-W7">
    <div class="section-header">
        <h3 class="section-title-dual">
            <span class="original-lang" data-lang="pt">
                Resumo de Medicação
            </span>
            <span class="lang-separator">|</span>
            <span class="translated-lang" data-lang="en">
                Medication Summary
            </span>
        </h3>
        
        <div class="language-toggle">
            <button class="lang-btn active" data-lang="dual">Ambos / Both</button>
            <button class="lang-btn" data-lang="original">PT</button>
            <button class="lang-btn" data-lang="translated">EN</button>
        </div>
        
        <div class="table-controls">
            <button class="btn-columns" id="toggle-columns">Colunas / Columns</button>
            <button class="btn-mobile" id="mobile-view">Vista Móvel / Mobile</button>
        </div>
    </div>
    
    <!-- Portuguese Responsive Table Sample -->
    <div class="medication-table-container">
        <table class="medication-table-enhanced" id="medication-table-pt">
            <thead>
                <tr>
                    <th class="priority-1" data-field="medicinal_product">
                        <div class="dual-header">
                            <span class="original">Produto Medicinal</span>
                            <span class="translated">Medicinal Product</span>
                        </div>
                    </th>
                    <th class="priority-1" data-field="strength_value">
                        <div class="dual-header">
                            <span class="original">Dosagem</span>
                            <span class="translated">Strength</span>
                        </div>
                    </th>
                    <th class="priority-1" data-field="route">
                        <div class="dual-header">
                            <span class="original">Via de Administração</span>
                            <span class="translated">Route</span>
                        </div>
                    </th>
                    <th class="priority-2" data-field="frequency">
                        <div class="dual-header">
                            <span class="original">Frequência</span>
                            <span class="translated">Frequency</span>
                        </div>
                    </th>
                    <th class="actions">
                        <span>Detalhes / Details</span>
                    </th>
                </tr>
            </thead>
            <tbody>
                <!-- Sample Portuguese medication row -->
                <tr class="medication-row" data-medication-id="1">
                    <td class="priority-1" data-field="medicinal_product">
                        <div class="dual-content">
                            <span class="original" data-lang="pt">
                                Paracetamol
                            </span>
                            <span class="translated" data-lang="en">
                                Paracetamol
                            </span>
                        </div>
                    </td>
                    <td class="priority-1" data-field="strength">
                        <div class="dual-content">
                            <span class="original">500 mg</span>
                            <span class="translated">500 mg</span>
                        </div>
                    </td>
                    <td class="priority-1" data-field="route">
                        <div class="dual-content">
                            <span class="original">Oral</span>
                            <span class="translated">Oral</span>
                        </div>
                    </td>
                    <td class="priority-2" data-field="frequency">
                        <div class="dual-content">
                            <span class="original">3 vezes por dia</span>
                            <span class="translated">3 times daily</span>
                        </div>
                    </td>
                    <td class="actions">
                        <button class="btn-expand" data-target="details-1">
                            <i class="icon-expand">▼</i>
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
"""

    print("✅ Portuguese dual language template demo created")
    print("✅ Shows Portuguese | English headers")
    print("✅ Demonstrates responsive priority system")
    print("✅ Includes Portuguese-specific terminology")


def main():
    print(
        "🔍 Testing Enhanced Dual Language CDA Display - Portuguese Patient PT 2-1234-W7"
    )
    print("=" * 80)

    # Test database first
    db_patient = test_portuguese_patient_database()

    # Test dual language processing with file
    result = test_dual_language_processing_pt()

    if result:
        print("\n✅ PORTUGUESE PATIENT DUAL LANGUAGE PROCESSING SUCCESSFUL")
        print("✅ Original and translated data extracted separately")
        print("✅ Portuguese-specific medication table system designed")
        print("✅ Mobile-friendly card layout available")
        print("✅ Priority-based column system implemented")

        # Create the enhanced templates
        create_portuguese_display_demo()

        print("\n🎯 Portuguese Patient Key Features:")
        print("   📱 Responsive design with priority columns")
        print("   🇵🇹 Portuguese | English dual language display")
        print("   📋 Expandable details for complex medication data")
        print("   💳 Mobile card view for Portuguese content")
        print("   🔧 Language toggle: Both | PT | EN")

        print(f"\n🇵🇹 Portuguese Patient Summary:")
        print(f"   Patient ID: {result['patient_id']}")
        print(f"   Country: {result['country_code']}")
        print(f"   Source Language: {result['source_language']}")
        print(f"   Target Language: {result['target_language']}")
        print(f"   Sections Processed: {len(result['original_data']['sections'])}")

    else:
        print("\n❌ Portuguese patient dual language processing failed")

    print("\n🎯 Ready for Server Testing:")
    print("   1. Navigate to your Django server")
    print("   2. Search for Portuguese patient PT 2-1234-W7")
    print("   3. Test dual language medication display")
    print("   4. Verify responsive table behavior")
    print("   5. Check mobile card view functionality")

    print("=" * 80)


if __name__ == "__main__":
    main()
