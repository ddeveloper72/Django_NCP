"""
Test FHIR Observations Extractor

Tests extraction of Observation resources from FHIR bundles.
Validates multi-component observations, interpretations, and reference ranges.

Usage:
    python manage.py test_fhir_observations
"""

import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone

from patient_data.services.clinical_sections.extractors.fhir_observations_extractor import FHIRObservationsExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test FHIR Observations extraction from sample bundle"

    def handle(self, *args, **options):
        """Execute observations extractor test."""
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("FHIR OBSERVATIONS EXTRACTOR TEST"))
        self.stdout.write("=" * 80 + "\n")
        
        # Load sample FHIR bundle with Observation resources
        bundle_path = Path("patient_data/test_data/sample_fhir_bundle.json")
        
        if not bundle_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ Bundle not found: {bundle_path}"))
            return
        
        self.stdout.write(f"📂 Loading bundle: {bundle_path}")
        
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                fhir_bundle = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load bundle: {e}"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✅ Bundle loaded successfully\n"))
        
        # Initialize extractor
        extractor = FHIRObservationsExtractor()
        
        self.stdout.write(f"🔧 Extractor Configuration:")
        self.stdout.write(f"   Section ID: {extractor.section_id}")
        self.stdout.write(f"   Section Title: {extractor.section_title}")
        self.stdout.write(f"   LOINC Code: {extractor.section_code}")
        self.stdout.write(f"   Resource Type: {extractor.fhir_resource_type}\n")
        
        # Extract observations
        self.stdout.write(f"🔍 Extracting observations from bundle...")
        
        try:
            result = extractor.extract_section(fhir_bundle)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Extraction failed: {e}"))
            import traceback
            traceback.print_exc()
            return
        
        # Display results (result is the section data dict directly)
        entries = result.get("clinical_table", {}).get("entries", [])
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Extracted {len(entries)} observations\n"))
        
        if not entries:
            self.stdout.write(self.style.WARNING("⚠️  No observations found in bundle"))
            return
        
        # Display each observation
        self.stdout.write("-" * 80)
        self.stdout.write("OBSERVATION DETAILS")
        self.stdout.write("-" * 80 + "\n")
        
        for idx, entry in enumerate(entries, 1):
            table_data = entry.get("table_data", {})
            
            self.stdout.write(self.style.WARNING(f"\n📊 OBSERVATION {idx}:"))
            self.stdout.write(f"   Observation: {table_data.get('observation_name', 'N/A')}")
            self.stdout.write(f"   Value: {table_data.get('value', 'N/A')}")
            
            # Display components if multi-component observation
            components = table_data.get("components", [])
            if components:
                self.stdout.write(f"   Components:")
                for comp in components:
                    self.stdout.write(f"      - {comp.get('display', 'N/A')}")
            
            interpretation = table_data.get("interpretation")
            if interpretation:
                self.stdout.write(f"   Interpretation: {interpretation}")
            
            ref_range = table_data.get("reference_range")
            if ref_range:
                self.stdout.write(f"   Reference Range: {ref_range}")
            
            self.stdout.write(f"   Date: {table_data.get('observation_date', 'N/A')}")
            self.stdout.write(f"   Status: {table_data.get('status', 'N/A')}")
            
            category = table_data.get("category")
            if category:
                self.stdout.write(f"   Category: {category}")
            
            notes = table_data.get("notes")
            if notes:
                self.stdout.write(f"   Notes: {notes}")
            
            # Display coded concepts
            coded_concepts = entry.get("coded_concepts", [])
            if coded_concepts:
                self.stdout.write(f"   Coded Concepts:")
                for concept in coded_concepts:
                    code = concept.get("code", "N/A")
                    system = concept.get("system", "N/A")
                    display = concept.get("display", "N/A")
                    self.stdout.write(f"      - {code} ({system}): {display}")
        
        # Summary statistics
        self.stdout.write("\n" + "-" * 80)
        self.stdout.write("SUMMARY STATISTICS")
        self.stdout.write("-" * 80 + "\n")
        
        # Count by category
        categories = {}
        for entry in entries:
            category = entry.get("table_data", {}).get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
        
        self.stdout.write("📊 Observations by Category:")
        for category, count in categories.items():
            self.stdout.write(f"   {category}: {count}")
        
        # Count by interpretation
        interpretations = {}
        for entry in entries:
            interp = entry.get("table_data", {}).get("interpretation")
            if interp:
                interpretations[interp] = interpretations.get(interp, 0) + 1
        
        if interpretations:
            self.stdout.write("\n🎯 Observations by Interpretation:")
            for interp, count in interpretations.items():
                self.stdout.write(f"   {interp}: {count}")
        
        # Count multi-component observations
        multi_component = sum(1 for e in entries if e.get("table_data", {}).get("components"))
        if multi_component:
            self.stdout.write(f"\n🔢 Multi-component observations: {multi_component}")
        
        # Clinical codes summary
        total_concepts = sum(len(e.get("coded_concepts", [])) for e in entries)
        self.stdout.write(f"\n💊 Total Clinical Codes: {total_concepts}")
        
        if total_concepts > 0:
            # Group by code system
            code_systems = {}
            for entry in entries:
                for concept in entry.get("coded_concepts", []):
                    system = concept.get("system", "Unknown")
                    code_systems[system] = code_systems.get(system, 0) + 1
            
            self.stdout.write("   Code Systems:")
            for system, count in code_systems.items():
                self.stdout.write(f"      {system}: {count}")
        
        # Validation checks
        self.stdout.write("\n" + "-" * 80)
        self.stdout.write("VALIDATION CHECKS")
        self.stdout.write("-" * 80 + "\n")
        
        checks_passed = 0
        total_checks = 8
        
        # Check 1: Observations extracted
        if len(entries) > 0:
            self.stdout.write(self.style.SUCCESS("✅ Check 1: Observations extracted"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 1: No observations extracted"))
        
        # Check 2: All observations have names
        all_have_names = all(e.get("table_data", {}).get("observation_name") for e in entries)
        if all_have_names:
            self.stdout.write(self.style.SUCCESS("✅ Check 2: All observations have names"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 2: Some observations missing names"))
        
        # Check 3: All observations have values or components
        all_have_values = all(
            e.get("table_data", {}).get("value") or e.get("table_data", {}).get("components")
            for e in entries
        )
        if all_have_values:
            self.stdout.write(self.style.SUCCESS("✅ Check 3: All observations have values or components"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 3: Some observations missing values and components"))
        
        # Check 4: All observations have dates
        all_have_dates = all(e.get("table_data", {}).get("observation_date") for e in entries)
        if all_have_dates:
            self.stdout.write(self.style.SUCCESS("✅ Check 4: All observations have dates"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 4: Some observations missing dates"))
        
        # Check 5: Multi-component observations handled
        has_multi_component = any(e.get("table_data", {}).get("components") for e in entries)
        if has_multi_component:
            self.stdout.write(self.style.SUCCESS("✅ Check 5: Multi-component observations handled"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING("⚠️  Check 5: No multi-component observations in bundle"))
        
        # Check 6: Section metadata present
        section_id = result.get("section_id")
        if section_id == "observations":
            self.stdout.write(self.style.SUCCESS("✅ Check 6: Section metadata present"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 6: Section metadata missing or invalid"))
        
        # Check 7: Display configuration present
        clinical_table = result.get("clinical_table", {})
        display_config = clinical_table.get("display_config", {})
        if display_config and display_config.get("display_format") == "table":
            self.stdout.write(self.style.SUCCESS("✅ Check 7: Display configuration present"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 7: Display configuration missing"))
        
        # Check 8: Table columns defined
        table_columns = clinical_table.get("columns", [])
        if table_columns and len(table_columns) > 0:
            self.stdout.write(self.style.SUCCESS("✅ Check 8: Table columns defined"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 8: Table columns missing"))
        
        # Final summary
        self.stdout.write("\n" + "=" * 80)
        if checks_passed == total_checks:
            self.stdout.write(self.style.SUCCESS(f"✅ ALL CHECKS PASSED ({checks_passed}/{total_checks})"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  CHECKS PASSED: {checks_passed}/{total_checks}"))
        self.stdout.write("=" * 80 + "\n")
        
        # Export to JSON for inspection
        output_file = "test_fhir_observations_output.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            self.stdout.write(f"📄 Detailed results exported to: {output_file}\n")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Could not export results: {e}\n"))
