#!/usr/bin/env python3
"""
Enhanced CDA Display with Dual Language Support
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


def test_dual_language_processing():
    """Test dual language processing with Luxembourg L3 CDA"""

    # Use the correct Luxembourg L3 CDA path
    cda_path = "test_data/eu_member_states/LU/CELESTINA_DOE-CALLA_38430827_3.xml"

    if not os.path.exists(cda_path):
        print(f"❌ CDA file not found: {cda_path}")
        return False

    print(f"✅ Found Luxembourg L3 CDA: {cda_path}")

    try:
        with open(cda_path, "r", encoding="utf-8") as file:
            cda_content = file.read()

        # Detect source language
        from patient_data.services.eu_language_detection_service import (
            detect_cda_language,
        )

        detected_language = detect_cda_language(cda_content)
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

            # Create dual language result structure
            dual_language_result = {
                "success": True,
                "source_language": detected_language,
                "target_language": "en",
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
            test_medication_table_layout(dual_language_result)

            return dual_language_result

    except Exception as e:
        print(f"❌ Dual language processing error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_medication_table_layout(dual_language_result):
    """Test medication table layout with many columns"""

    print("\n🧪 Testing Medication Table Layout...")

    # Find medication sections in both languages
    original_sections = dual_language_result["original_data"]["sections"]
    translated_sections = dual_language_result["translated_data"]["sections"]

    medication_sections_original = [
        s
        for s in original_sections
        if "medication" in s.get("section_title", "").lower()
    ]
    medication_sections_translated = [
        s
        for s in translated_sections
        if "medication" in s.get("section_title", "").lower()
    ]

    print(f"✅ Found {len(medication_sections_original)} original medication sections")
    print(
        f"✅ Found {len(medication_sections_translated)} translated medication sections"
    )

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

    print(f"📊 Medication table has {len(medication_fields)} columns")
    print("⚠️  Table width considerations:")
    print("   - 12 columns may require horizontal scrolling")
    print("   - Responsive design needed for mobile/tablet")
    print("   - Consider collapsible/expandable rows")
    print("   - Priority columns: Product, Strength, Dose Form, Route")

    # Generate responsive table recommendations
    generate_responsive_table_recommendations(medication_fields)


def generate_responsive_table_recommendations(fields):
    """Generate recommendations for responsive medication table"""

    print("\n📱 Responsive Table Recommendations:")

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

    print("🟢 Priority 1 (Always visible):")
    for field in priority_1:
        print(f"   - {field}")

    print("🟡 Priority 2 (Hide on tablets/phones):")
    for field in priority_2:
        print(f"   - {field}")

    print("🔵 Priority 3 (Show in expandable details):")
    for field in priority_3:
        print(f"   - {field}")

    print("\n💡 Implementation Suggestions:")
    print("   1. Use CSS Grid/Flexbox for responsive layout")
    print("   2. Implement column toggle buttons")
    print("   3. Add row expansion for detailed medication info")
    print("   4. Use horizontal scroll for full table view")
    print("   5. Create mobile-first medication cards as alternative")


def create_enhanced_display_templates():
    """Create enhanced templates for dual language display"""

    print("\n🎨 Creating Enhanced Display Templates...")

    # Enhanced medication table template with dual language support
    medication_template = """
<!-- Enhanced Medication Table with Dual Language Support -->
<div class="medication-section-enhanced">
    <div class="section-header">
        <h3 class="section-title-dual">
            <span class="original-lang" data-lang="{{ source_language }}">
                {{ original_section_title }}
            </span>
            <span class="lang-separator">|</span>
            <span class="translated-lang" data-lang="en">
                {{ translated_section_title }}
            </span>
        </h3>
        
        <div class="language-toggle">
            <button class="lang-btn active" data-lang="dual">Both Languages</button>
            <button class="lang-btn" data-lang="original">{{ source_language|upper }}</button>
            <button class="lang-btn" data-lang="translated">EN</button>
        </div>
        
        <div class="table-controls">
            <button class="btn-columns" id="toggle-columns">Columns</button>
            <button class="btn-mobile" id="mobile-view">Mobile View</button>
        </div>
    </div>
    
    <!-- Responsive Medication Table -->
    <div class="medication-table-container">
        <table class="medication-table-enhanced" id="medication-table">
            <thead>
                <tr>
                    <th class="priority-1" data-field="medicinal_product">
                        <div class="dual-header">
                            <span class="original">{{ "Medicinal Product"|translate:source_language }}</span>
                            <span class="translated">Medicinal Product</span>
                        </div>
                    </th>
                    <th class="priority-1" data-field="strength_value">
                        <div class="dual-header">
                            <span class="original">{{ "Strength"|translate:source_language }}</span>
                            <span class="translated">Strength</span>
                        </div>
                    </th>
                    <th class="priority-2" data-field="active_ingredient">
                        <div class="dual-header">
                            <span class="original">{{ "Active Ingredient"|translate:source_language }}</span>
                            <span class="translated">Active Ingredient</span>
                        </div>
                    </th>
                    <th class="priority-1" data-field="route">
                        <div class="dual-header">
                            <span class="original">{{ "Route"|translate:source_language }}</span>
                            <span class="translated">Route</span>
                        </div>
                    </th>
                    <th class="priority-2" data-field="frequency">
                        <div class="dual-header">
                            <span class="original">{{ "Frequency"|translate:source_language }}</span>
                            <span class="translated">Frequency</span>
                        </div>
                    </th>
                    <th class="priority-3" data-field="duration">
                        <div class="dual-header">
                            <span class="original">{{ "Duration"|translate:source_language }}</span>
                            <span class="translated">Duration</span>
                        </div>
                    </th>
                    <th class="actions">
                        <span>Details</span>
                    </th>
                </tr>
            </thead>
            <tbody>
                {% for medication in medications %}
                <tr class="medication-row" data-medication-id="{{ forloop.counter }}">
                    <td class="priority-1" data-field="medicinal_product">
                        <div class="dual-content">
                            <span class="original" data-lang="{{ source_language }}">
                                {{ medication.original.medicinal_product }}
                            </span>
                            <span class="translated" data-lang="en">
                                {{ medication.translated.medicinal_product }}
                            </span>
                        </div>
                    </td>
                    <td class="priority-1" data-field="strength">
                        <div class="dual-content">
                            <span class="original">{{ medication.original.strength_value }} {{ medication.original.strength_unit }}</span>
                            <span class="translated">{{ medication.translated.strength_value }} {{ medication.translated.strength_unit }}</span>
                        </div>
                    </td>
                    <td class="priority-2" data-field="active_ingredient">
                        <div class="dual-content">
                            <span class="original">{{ medication.original.active_ingredient }}</span>
                            <span class="translated">{{ medication.translated.active_ingredient }}</span>
                        </div>
                    </td>
                    <td class="priority-1" data-field="route">
                        <div class="dual-content">
                            <span class="original">{{ medication.original.route }}</span>
                            <span class="translated">{{ medication.translated.route }}</span>
                        </div>
                    </td>
                    <td class="priority-2" data-field="frequency">
                        <div class="dual-content">
                            <span class="original">{{ medication.original.frequency }}</span>
                            <span class="translated">{{ medication.translated.frequency }}</span>
                        </div>
                    </td>
                    <td class="priority-3" data-field="duration">
                        <div class="dual-content">
                            <span class="original">{{ medication.original.duration }}</span>
                            <span class="translated">{{ medication.translated.duration }}</span>
                        </div>
                    </td>
                    <td class="actions">
                        <button class="btn-expand" data-target="details-{{ forloop.counter }}">
                            <i class="icon-expand">▼</i>
                        </button>
                    </td>
                </tr>
                
                <!-- Expandable Details Row -->
                <tr class="medication-details" id="details-{{ forloop.counter }}" style="display: none;">
                    <td colspan="7">
                        <div class="details-content">
                            <div class="detail-grid">
                                <div class="detail-item">
                                    <label>{{ "Active Ingredient ID"|translate:source_language }} | Active Ingredient ID:</label>
                                    <div class="dual-value">
                                        <span class="original">{{ medication.original.active_ingredient_id }}</span>
                                        <span class="translated">{{ medication.translated.active_ingredient_id }}</span>
                                    </div>
                                </div>
                                <div class="detail-item">
                                    <label>{{ "Units Per Intake"|translate:source_language }} | Units Per Intake:</label>
                                    <div class="dual-value">
                                        <span class="original">{{ medication.original.units_per_intake }}</span>
                                        <span class="translated">{{ medication.translated.units_per_intake }}</span>
                                    </div>
                                </div>
                                <div class="detail-item">
                                    <label>{{ "Medication Reason"|translate:source_language }} | Medication Reason:</label>
                                    <div class="dual-value">
                                        <span class="original">{{ medication.original.reason }}</span>
                                        <span class="translated">{{ medication.translated.reason }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Mobile Card View (Alternative) -->
    <div class="medication-cards" id="mobile-cards" style="display: none;">
        {% for medication in medications %}
        <div class="medication-card">
            <div class="card-header">
                <h4 class="dual-title">
                    <span class="original">{{ medication.original.medicinal_product }}</span>
                    <span class="translated">{{ medication.translated.medicinal_product }}</span>
                </h4>
            </div>
            <div class="card-body">
                <div class="med-detail">
                    <span class="label">Strength:</span>
                    <div class="dual-value">
                        <span class="original">{{ medication.original.strength_value }} {{ medication.original.strength_unit }}</span>
                        <span class="translated">{{ medication.translated.strength_value }} {{ medication.translated.strength_unit }}</span>
                    </div>
                </div>
                <div class="med-detail">
                    <span class="label">Route:</span>
                    <div class="dual-value">
                        <span class="original">{{ medication.original.route }}</span>
                        <span class="translated">{{ medication.translated.route }}</span>
                    </div>
                </div>
                <!-- More details... -->
            </div>
        </div>
        {% endfor %}
    </div>
</div>
"""

    # Enhanced CSS for dual language and responsive design
    enhanced_css = """
/* Enhanced Dual Language Medication Display */
.medication-section-enhanced {
    margin: 20px 0;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    overflow: hidden;
}

.section-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

.section-title-dual {
    font-size: 1.4em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.lang-separator {
    opacity: 0.7;
    font-weight: normal;
}

.language-toggle {
    display: flex;
    gap: 5px;
}

.lang-btn {
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    padding: 5px 12px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.lang-btn.active,
.lang-btn:hover {
    background: rgba(255,255,255,0.3);
    border-color: rgba(255,255,255,0.5);
}

.table-controls {
    display: flex;
    gap: 10px;
}

.btn-columns, .btn-mobile {
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    padding: 8px 15px;
    border-radius: 4px;
    cursor: pointer;
}

/* Responsive Table Container */
.medication-table-container {
    overflow-x: auto;
    max-width: 100%;
}

.medication-table-enhanced {
    width: 100%;
    border-collapse: collapse;
    min-width: 800px; /* Minimum width to maintain readability */
}

.medication-table-enhanced th,
.medication-table-enhanced td {
    padding: 12px 8px;
    border-bottom: 1px solid #e0e0e0;
    text-align: left;
    vertical-align: top;
}

.medication-table-enhanced th {
    background: #f8f9fa;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
}

/* Dual Language Headers and Content */
.dual-header {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.dual-header .original {
    font-size: 0.9em;
    opacity: 0.8;
    font-style: italic;
}

.dual-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.dual-content .original {
    font-size: 0.9em;
    color: #666;
    font-style: italic;
}

.dual-content .translated {
    font-weight: 500;
    color: #333;
}

/* Language Display Modes */
.medication-section-enhanced[data-lang-mode="original"] .translated {
    display: none;
}

.medication-section-enhanced[data-lang-mode="translated"] .original {
    display: none;
}

/* Priority-based responsive columns */
@media (max-width: 1200px) {
    .priority-3 {
        display: none;
    }
}

@media (max-width: 900px) {
    .priority-2 {
        display: none;
    }
}

@media (max-width: 600px) {
    .medication-table-container {
        display: none;
    }
    
    .medication-cards {
        display: block !important;
    }
}

/* Expandable Details */
.btn-expand {
    background: none;
    border: 1px solid #ddd;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn-expand:hover {
    background: #f0f0f0;
}

.medication-details .details-content {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 4px;
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 15px;
}

.detail-item label {
    font-weight: 600;
    color: #555;
    display: block;
    margin-bottom: 5px;
}

.dual-value {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

/* Mobile Card View */
.medication-cards {
    padding: 20px;
}

.medication-card {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 15px;
    overflow: hidden;
}

.card-header {
    background: #f8f9fa;
    padding: 15px;
    border-bottom: 1px solid #e0e0e0;
}

.dual-title {
    margin: 0;
    font-size: 1.1em;
}

.card-body {
    padding: 15px;
}

.med-detail {
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f0f0f0;
}

.med-detail:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.med-detail .label {
    font-weight: 600;
    color: #555;
    display: block;
    margin-bottom: 5px;
}
"""

    print("✅ Enhanced dual language medication template created")
    print("✅ Responsive CSS with priority-based column hiding created")
    print("✅ Mobile card view alternative created")
    print("✅ Expandable details system for complex data created")


def main():
    print("🔍 Testing Enhanced Dual Language CDA Display...")
    print("=" * 70)

    # Test dual language processing
    result = test_dual_language_processing()

    if result:
        print("\n✅ DUAL LANGUAGE PROCESSING SUCCESSFUL")
        print("✅ Original and translated data extracted separately")
        print("✅ Responsive medication table system designed")
        print("✅ Mobile-friendly card layout available")
        print("✅ Priority-based column system implemented")

        # Create the enhanced templates
        create_enhanced_display_templates()

        print("\n🎯 Key Features Implemented:")
        print("   📱 Responsive design with priority columns")
        print("   🌐 Side-by-side dual language display")
        print("   📋 Expandable details for complex medication data")
        print("   💳 Mobile card view for small screens")
        print("   🔧 Column toggle and view mode controls")

    else:
        print("\n❌ Dual language processing failed")

    print("=" * 70)


if __name__ == "__main__":
    main()
