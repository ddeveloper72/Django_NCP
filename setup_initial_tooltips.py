"""
Initial Tooltip Data Setup
Creates initial tooltips for the healthcare interface
"""

import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.models import Tooltip


def create_initial_tooltips():
    """Create initial tooltips for the healthcare interface"""

    tooltips = [
        {
            "key": "source_country_flag",
            "title": "Source Country Indicator",
            "content": "Shows the country where this Clinical Document Architecture (CDA) was originally created. Detected automatically from document language code, custodian organization name, or patient address information.",
            "category": "indicators",
            "target_audience": "general",
            "placement": "bottom",
        },
        {
            "key": "translation_quality",
            "title": "Translation Quality Indicator",
            "content": 'Indicates the level of structured data extraction success. "High" means enhanced JSON field mapping is active and structured medical data was successfully extracted from the CDA document. "Basic" indicates standard text extraction only.',
            "category": "indicators",
            "target_audience": "general",
            "placement": "bottom",
        },
        {
            "key": "source_country_flag_technical",
            "title": "Source Country Detection (Technical)",
            "content": "Country code automatically detected via: 1) Language code mapping (e.g., en-IE → Ireland), 2) Custodian organization analysis (HSE → Ireland), 3) Patient address country field parsing. Used for optimizing country-specific CDA parsing strategies.",
            "category": "indicators",
            "target_audience": "technical",
            "placement": "bottom",
        },
        {
            "key": "translation_quality_technical",
            "title": "Translation Quality (Technical)",
            "content": "Indicates CDA processing pipeline success: Basic=Standard text extraction only, High=Enhanced JSON field mapping active (structured data successfully extracted via XPath), High (Structured)=L3 CDA with full field mapping. Determines availability of structured vs unstructured medical data.",
            "category": "indicators",
            "target_audience": "technical",
            "placement": "bottom",
        },
        {
            "key": "patient_name_header",
            "title": "Patient Identification",
            "content": "Primary patient identification extracted from the Clinical Document Architecture. May include given name, family name, and patient identifiers from the source healthcare system.",
            "category": "patient_header",
            "target_audience": "general",
            "placement": "bottom",
        },
        {
            "key": "clinical_section_accordion",
            "title": "Clinical Data Sections",
            "content": "Organized clinical information extracted from the patient's medical document. Each section contains specific types of medical data such as allergies, medications, procedures, or problems.",
            "category": "clinical_data",
            "target_audience": "medical",
            "placement": "top",
        },
        {
            "key": "extended_patient_tabs",
            "title": "Extended Patient Information",
            "content": "Comprehensive patient data organized into categories: Personal (contact information), Healthcare (providers and services), System (document metadata), and Clinical (medical conditions and treatments).",
            "category": "navigation",
            "target_audience": "general",
            "placement": "top",
        },
    ]

    created_count = 0
    updated_count = 0

    for tooltip_data in tooltips:
        tooltip, created = Tooltip.objects.get_or_create(
            key=tooltip_data["key"], defaults=tooltip_data
        )

        if created:
            created_count += 1
            print(f"✓ Created tooltip: {tooltip.key}")
        else:
            # Update existing tooltip with new data
            for field, value in tooltip_data.items():
                if field != "key":
                    setattr(tooltip, field, value)
            tooltip.save()
            updated_count += 1
            print(f"↻ Updated tooltip: {tooltip.key}")

    print(f"\n📋 Tooltip Setup Complete:")
    print(f"   • Created: {created_count} new tooltips")
    print(f"   • Updated: {updated_count} existing tooltips")
    print(f"   • Total: {Tooltip.objects.count()} tooltips in database")

    # Display categories
    categories = Tooltip.objects.values_list("category", flat=True).distinct()
    print(f"   • Categories: {', '.join(categories)}")


if __name__ == "__main__":
    create_initial_tooltips()
