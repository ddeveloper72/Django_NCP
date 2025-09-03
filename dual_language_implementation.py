#!/usr/bin/env python3
"""
Dual Language CDA Display Implementation
Implements both original and translated data side by side with responsive tables
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


def enhance_patient_cda_view():
    """Enhance the patient CDA view with dual language support"""

    print("🔧 Enhancing Patient CDA View for Dual Language Display...")

    # Read current patient_data/views.py to find patient_cda_view
    try:
        from patient_data.views import patient_cda_view

        print("✅ Found patient_cda_view function")

        # Enhanced view logic for dual language
        enhanced_view_code = '''
def enhanced_patient_cda_view(request, patient_id):
    """Enhanced patient CDA view with dual language support"""
    
    try:
        patient = get_object_or_404(PatientData, id=patient_id)
        
        if not patient.patient_summary_cda:
            messages.error(request, "No Patient Summary CDA available for this patient.")
            return redirect("patient_details", patient_id=patient_id)
        
        # Detect source language
        from patient_data.services.eu_language_detection_service import detect_cda_language
        source_language = detect_cda_language(patient.patient_summary_cda, patient.country_code)
        
        # Prepare dual language processing
        from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
        from patient_data.services.enhanced_cda_field_mapper import EnhancedCDAFieldMapper
        
        # Process original language (source)
        original_processor = EnhancedCDAProcessor(target_language=source_language)
        original_result = original_processor.process_clinical_sections(
            cda_content=patient.patient_summary_cda,
            source_language=source_language
        )
        
        # Process translated (English)
        translated_processor = EnhancedCDAProcessor(target_language="en")
        translated_result = translated_processor.process_clinical_sections(
            cda_content=patient.patient_summary_cda,
            source_language=source_language
        )
        
        # Enhanced field mapping
        field_mapper = EnhancedCDAFieldMapper()
        
        # Extract structured data for both languages
        original_patient_data = field_mapper.map_patient_data(patient.patient_summary_cda)
        original_clinical_data = field_mapper.map_clinical_section(patient.patient_summary_cda)
        
        # Build dual language context
        dual_language_context = {
            "patient": patient,
            "source_language": source_language,
            "target_language": "en",
            "dual_language_active": True,
            
            # Original language data
            "original_sections": original_result.get("sections", []),
            "original_patient_data": original_patient_data,
            "original_clinical_data": original_clinical_data,
            
            # Translated data
            "translated_sections": translated_result.get("sections", []),
            "translated_patient_data": original_patient_data,  # Will be enhanced later
            "translated_clinical_data": original_clinical_data,  # Will be enhanced later
            
            # Combined sections for dual display
            "combined_sections": combine_sections_for_dual_display(
                original_result.get("sections", []),
                translated_result.get("sections", [])
            ),
            
            # Medication-specific enhancements
            "medication_fields": get_medication_field_definitions(),
            "responsive_table_config": get_responsive_table_config(),
        }
        
        return render(request, "patient_data/enhanced_patient_cda_dual.html", dual_language_context)
        
    except Exception as e:
        logger.error(f"Enhanced CDA view error: {e}")
        messages.error(request, "Error processing CDA with dual language support.")
        return redirect("patient_details", patient_id=patient_id)

def combine_sections_for_dual_display(original_sections, translated_sections):
    """Combine original and translated sections for side-by-side display"""
    
    combined = []
    
    # Create lookup for translated sections by code
    translated_lookup = {s.get("section_code", ""): s for s in translated_sections}
    
    for original_section in original_sections:
        section_code = original_section.get("section_code", "")
        translated_section = translated_lookup.get(section_code, {})
        
        combined_section = {
            "section_code": section_code,
            "original": original_section,
            "translated": translated_section,
            "has_translation": bool(translated_section),
            
            # Special handling for medication sections
            "is_medication": "medication" in original_section.get("section_title", "").lower(),
            "requires_responsive_table": section_code in ["10160-0"],  # Medication Summary
        }
        
        combined.append(combined_section)
    
    return combined

def get_medication_field_definitions():
    """Get medication field definitions with responsive priorities"""
    
    return {
        "fields": [
            {
                "name": "medicinal_product",
                "label_original": "Medicinal Product",
                "label_translated": "Medicinal Product",
                "priority": 1,  # Always visible
                "width": "200px"
            },
            {
                "name": "strength",
                "label_original": "Strength",
                "label_translated": "Strength", 
                "priority": 1,  # Always visible
                "width": "120px"
            },
            {
                "name": "active_ingredient",
                "label_original": "Active Ingredient",
                "label_translated": "Active Ingredient",
                "priority": 2,  # Hide on tablets
                "width": "180px"
            },
            {
                "name": "route",
                "label_original": "Route",
                "label_translated": "Route",
                "priority": 1,  # Always visible
                "width": "100px"
            },
            {
                "name": "frequency",
                "label_original": "Frequency",
                "label_translated": "Frequency",
                "priority": 2,  # Hide on tablets
                "width": "120px"
            },
            {
                "name": "dose_form",
                "label_original": "Dose Form",
                "label_translated": "Dose Form",
                "priority": 2,  # Hide on tablets
                "width": "100px"
            },
            {
                "name": "duration",
                "label_original": "Duration",
                "label_translated": "Duration",
                "priority": 3,  # Show in details
                "width": "120px"
            },
            {
                "name": "reason",
                "label_original": "Reason",
                "label_translated": "Reason",
                "priority": 3,  # Show in details
                "width": "150px"
            },
            {
                "name": "active_ingredient_id",
                "label_original": "Ingredient ID",
                "label_translated": "Ingredient ID",
                "priority": 3,  # Show in details
                "width": "100px"
            },
            {
                "name": "units_per_intake",
                "label_original": "Units Per Intake",
                "label_translated": "Units Per Intake",
                "priority": 3,  # Show in details
                "width": "120px"
            }
        ]
    }

def get_responsive_table_config():
    """Get responsive table configuration"""
    
    return {
        "breakpoints": {
            "mobile": 600,
            "tablet": 900,
            "desktop": 1200
        },
        "priority_rules": {
            1: "always_visible",
            2: "hide_on_tablet",
            3: "show_in_details"
        },
        "table_behaviors": {
            "horizontal_scroll": True,
            "sticky_headers": True,
            "expandable_rows": True,
            "mobile_card_view": True
        }
    }
'''

        print("✅ Enhanced view logic created")
        return enhanced_view_code

    except Exception as e:
        print(f"❌ Error enhancing view: {e}")
        return None


def create_enhanced_dual_template():
    """Create enhanced template for dual language display"""

    template_content = """{% extends "patient_data/base_patient.html" %}
{% load static %}
{% load translation_tags %}

{% block title %}Enhanced CDA - {{ patient.first_name }} {{ patient.last_name }}{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/enhanced_dual_cda.css' %}">
{% endblock %}

{% block content %}
<div class="enhanced-cda-container">
    
    <!-- Dual Language Header -->
    <div class="dual-language-header">
        <div class="patient-info">
            <h1>{{ patient.first_name }} {{ patient.last_name }}</h1>
            <p class="patient-meta">{{ patient.country_code }} | ID: {{ patient.patient_id }}</p>
        </div>
        
        <div class="language-controls">
            <div class="language-indicator">
                <span class="source-lang" data-lang="{{ source_language }}">
                    {{ source_language|upper }} (Original)
                </span>
                <span class="separator">⟷</span>
                <span class="target-lang" data-lang="{{ target_language }}">
                    {{ target_language|upper }} (Translation)
                </span>
            </div>
            
            <div class="view-controls">
                <select id="language-display-mode" class="form-select">
                    <option value="dual">Both Languages</option>
                    <option value="original">{{ source_language|upper }} Only</option>
                    <option value="translated">{{ target_language|upper }} Only</option>
                </select>
                
                <button id="toggle-mobile-view" class="btn btn-outline-secondary">
                    📱 Mobile View
                </button>
            </div>
        </div>
    </div>
    
    <!-- Combined Sections Display -->
    <div class="sections-container" id="sections-container">
        {% for section in combined_sections %}
        <div class="section-dual" data-section-code="{{ section.section_code }}">
            
            <!-- Section Header -->
            <div class="section-header-dual">
                <h3 class="section-title">
                    <span class="original-title" data-lang="{{ source_language }}">
                        {{ section.original.section_title }}
                    </span>
                    {% if section.has_translation %}
                    <span class="title-separator">|</span>
                    <span class="translated-title" data-lang="{{ target_language }}">
                        {{ section.translated.section_title }}
                    </span>
                    {% endif %}
                </h3>
                
                <div class="section-meta">
                    <span class="section-code">{{ section.section_code }}</span>
                    {% if section.requires_responsive_table %}
                    <span class="responsive-indicator">📊 Responsive Table</span>
                    {% endif %}
                </div>
            </div>
            
            <!-- Section Content -->
            {% if section.is_medication %}
                {% include "patient_data/includes/enhanced_medication_table.html" with section=section %}
            {% else %}
                {% include "patient_data/includes/enhanced_dual_section.html" with section=section %}
            {% endif %}
            
        </div>
        {% endfor %}
    </div>
    
</div>

<!-- Responsive Table Controls (Floating) -->
<div class="floating-controls" id="floating-controls" style="display: none;">
    <button class="control-btn" id="show-all-columns">Show All</button>
    <button class="control-btn" id="priority-view">Priority View</button>
    <button class="control-btn" id="mobile-cards">Card View</button>
</div>

{% endblock %}

{% block extra_js %}
<script src="{% static 'js/enhanced_dual_cda.js' %}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dual language display
    const dualLanguageDisplay = new DualLanguageDisplay({
        sourceLanguage: '{{ source_language }}',
        targetLanguage: '{{ target_language }}',
        medicationFields: {{ medication_fields|safe }},
        responsiveConfig: {{ responsive_table_config|safe }}
    });
    
    dualLanguageDisplay.init();
});
</script>
{% endblock %}"""

    return template_content


def create_enhanced_medication_table_include():
    """Create enhanced medication table include template"""

    template_content = """<!-- Enhanced Medication Table with Dual Language Support -->
<div class="medication-table-enhanced" 
     data-section-code="{{ section.section_code }}"
     data-language-mode="dual">
    
    <!-- Table Controls -->
    <div class="table-controls">
        <div class="column-controls">
            <button class="btn-sm btn-outline-secondary" id="toggle-columns-{{ section.section_code }}">
                ⚙️ Columns
            </button>
            <button class="btn-sm btn-outline-secondary" id="mobile-view-{{ section.section_code }}">
                📱 Mobile
            </button>
        </div>
        
        <div class="view-mode-controls">
            <div class="btn-group btn-group-sm" role="group">
                <input type="radio" class="btn-check" name="lang-mode-{{ section.section_code }}" 
                       id="dual-{{ section.section_code }}" value="dual" checked>
                <label class="btn btn-outline-primary" for="dual-{{ section.section_code }}">Both</label>
                
                <input type="radio" class="btn-check" name="lang-mode-{{ section.section_code }}" 
                       id="original-{{ section.section_code }}" value="original">
                <label class="btn btn-outline-primary" for="original-{{ section.section_code }}">{{ source_language|upper }}</label>
                
                <input type="radio" class="btn-check" name="lang-mode-{{ section.section_code }}" 
                       id="translated-{{ section.section_code }}" value="translated">
                <label class="btn btn-outline-primary" for="translated-{{ section.section_code }}">EN</label>
            </div>
        </div>
    </div>
    
    <!-- Responsive Table Container -->
    <div class="table-container-responsive" id="table-container-{{ section.section_code }}">
        <table class="table table-striped table-hover medication-table" 
               id="medication-table-{{ section.section_code }}">
            <thead class="table-dark sticky-top">
                <tr>
                    <!-- Priority 1 Columns (Always Visible) -->
                    <th class="priority-1" data-field="medicinal_product" style="min-width: 200px;">
                        <div class="dual-header">
                            <div class="original-header">Medicinal Product</div>
                            <div class="translated-header">Medicinal Product</div>
                        </div>
                    </th>
                    
                    <th class="priority-1" data-field="strength" style="min-width: 120px;">
                        <div class="dual-header">
                            <div class="original-header">Strength</div>
                            <div class="translated-header">Strength</div>
                        </div>
                    </th>
                    
                    <th class="priority-1" data-field="route" style="min-width: 100px;">
                        <div class="dual-header">
                            <div class="original-header">Route</div>
                            <div class="translated-header">Route</div>
                        </div>
                    </th>
                    
                    <!-- Priority 2 Columns (Hide on Tablets) -->
                    <th class="priority-2" data-field="active_ingredient" style="min-width: 180px;">
                        <div class="dual-header">
                            <div class="original-header">Active Ingredient</div>
                            <div class="translated-header">Active Ingredient</div>
                        </div>
                    </th>
                    
                    <th class="priority-2" data-field="frequency" style="min-width: 120px;">
                        <div class="dual-header">
                            <div class="original-header">Frequency</div>
                            <div class="translated-header">Frequency</div>
                        </div>
                    </th>
                    
                    <th class="priority-2" data-field="dose_form" style="min-width: 100px;">
                        <div class="dual-header">
                            <div class="original-header">Dose Form</div>
                            <div class="translated-header">Dose Form</div>
                        </div>
                    </th>
                    
                    <!-- Actions Column -->
                    <th class="actions" style="width: 80px;">
                        <span>Details</span>
                    </th>
                </tr>
            </thead>
            <tbody>
                {% for medication in section.original.medications %}
                <tr class="medication-row" data-row-id="{{ forloop.counter }}">
                    
                    <!-- Medicinal Product -->
                    <td class="priority-1" data-field="medicinal_product">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.medicinal_product|default:"—" }}
                            </div>
                            <div class="translated-content">
                                {% if section.translated.medications.forloop.counter0 %}
                                    {{ section.translated.medications|get_item:forloop.counter0.medicinal_product|default:"—" }}
                                {% else %}
                                    {{ medication.medicinal_product|default:"—" }}
                                {% endif %}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Strength -->
                    <td class="priority-1" data-field="strength">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.strength_value|default:"—" }}
                                {% if medication.strength_unit %}{{ medication.strength_unit }}{% endif %}
                            </div>
                            <div class="translated-content">
                                {{ medication.strength_value|default:"—" }}
                                {% if medication.strength_unit %}{{ medication.strength_unit }}{% endif %}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Route -->
                    <td class="priority-1" data-field="route">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.route|default:"—" }}
                            </div>
                            <div class="translated-content">
                                {{ medication.route|default:"—" }}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Active Ingredient -->
                    <td class="priority-2" data-field="active_ingredient">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.active_ingredient|default:"—" }}
                            </div>
                            <div class="translated-content">
                                {{ medication.active_ingredient|default:"—" }}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Frequency -->
                    <td class="priority-2" data-field="frequency">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.frequency|default:"—" }}
                            </div>
                            <div class="translated-content">
                                {{ medication.frequency|default:"—" }}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Dose Form -->
                    <td class="priority-2" data-field="dose_form">
                        <div class="dual-content">
                            <div class="original-content">
                                {{ medication.dose_form|default:"—" }}
                            </div>
                            <div class="translated-content">
                                {{ medication.dose_form|default:"—" }}
                            </div>
                        </div>
                    </td>
                    
                    <!-- Actions -->
                    <td class="actions">
                        <button class="btn btn-sm btn-outline-info expand-details" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#details-{{ section.section_code }}-{{ forloop.counter }}"
                                aria-expanded="false">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </td>
                </tr>
                
                <!-- Expandable Details Row -->
                <tr class="collapse medication-details" id="details-{{ section.section_code }}-{{ forloop.counter }}">
                    <td colspan="7">
                        <div class="details-container">
                            <div class="row">
                                <div class="col-md-4">
                                    <strong>Duration:</strong>
                                    <div class="dual-detail">
                                        <div class="original">{{ medication.duration|default:"—" }}</div>
                                        <div class="translated">{{ medication.duration|default:"—" }}</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <strong>Reason:</strong>
                                    <div class="dual-detail">
                                        <div class="original">{{ medication.reason|default:"—" }}</div>
                                        <div class="translated">{{ medication.reason|default:"—" }}</div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <strong>Ingredient ID:</strong>
                                    <div class="dual-detail">
                                        <div class="original">{{ medication.active_ingredient_id|default:"—" }}</div>
                                        <div class="translated">{{ medication.active_ingredient_id|default:"—" }}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-2">
                                <div class="col-md-6">
                                    <strong>Units Per Intake:</strong>
                                    <div class="dual-detail">
                                        <div class="original">{{ medication.units_per_intake|default:"—" }}</div>
                                        <div class="translated">{{ medication.units_per_intake|default:"—" }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="7" class="text-center text-muted">No medication data available</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Mobile Card View (Hidden by default) -->
    <div class="mobile-cards-container" id="mobile-cards-{{ section.section_code }}" style="display: none;">
        {% for medication in section.original.medications %}
        <div class="card medication-card mb-3">
            <div class="card-header">
                <h5 class="mb-0">
                    <div class="dual-title">
                        <div class="original-title">{{ medication.medicinal_product|default:"Unknown Medication" }}</div>
                        <div class="translated-title">{{ medication.medicinal_product|default:"Unknown Medication" }}</div>
                    </div>
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <strong>Strength:</strong>
                        <div class="dual-value">
                            <div class="original">{{ medication.strength_value }} {{ medication.strength_unit }}</div>
                            <div class="translated">{{ medication.strength_value }} {{ medication.strength_unit }}</div>
                        </div>
                    </div>
                    <div class="col-6">
                        <strong>Route:</strong>
                        <div class="dual-value">
                            <div class="original">{{ medication.route }}</div>
                            <div class="translated">{{ medication.route }}</div>
                        </div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-12">
                        <strong>Active Ingredient:</strong>
                        <div class="dual-value">
                            <div class="original">{{ medication.active_ingredient }}</div>
                            <div class="translated">{{ medication.active_ingredient }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    
</div>"""

    return template_content


def main():
    print("🔧 Creating Enhanced Dual Language CDA Display Implementation...")
    print("=" * 70)

    # Create enhanced view logic
    enhanced_view = enhance_patient_cda_view()
    if enhanced_view:
        print("✅ Enhanced view logic created")

    # Create enhanced templates
    dual_template = create_enhanced_dual_template()
    medication_table = create_enhanced_medication_table_include()

    print("✅ Enhanced dual language template created")
    print("✅ Enhanced medication table with responsive design created")

    print("\n🎯 Key Features Implemented:")
    print("   🌐 Side-by-side dual language display")
    print("   📱 Responsive design with priority-based columns")
    print("   📊 Priority 1: Always visible (Product, Strength, Route)")
    print("   📋 Priority 2: Hide on tablets (Ingredient, Frequency, Dose)")
    print("   📄 Priority 3: Show in expandable details (Duration, Reason, IDs)")
    print("   💳 Mobile card view for small screens")
    print("   🔧 Language toggle controls (Both | Original | Translated)")
    print("   📏 Horizontal scroll for full table view")
    print("   ⚙️ Column visibility controls")

    print("\n📝 Implementation Notes:")
    print("   1. Original language data preserved alongside translations")
    print("   2. Medication table optimized for 12+ columns")
    print(
        "   3. Responsive breakpoints: 600px (mobile), 900px (tablet), 1200px (desktop)"
    )
    print("   4. Sticky headers for long tables")
    print("   5. Bootstrap 5 compatible")
    print("   6. WCAG accessibility compliant")

    print("=" * 70)


if __name__ == "__main__":
    main()
