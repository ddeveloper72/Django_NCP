"""
Test FHIR Immunizations Extractor

Tests extraction of Immunization resources from FHIR bundles.
Validates vaccination records, dose information, and clinical metadata.

Usage:
    python manage.py test_fhir_immunizations
"""

import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.utils import timezone

from patient_data.services.clinical_sections.extractors.fhir_immunizations_extractor import FHIRImmunizationsExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test FHIR Immunizations extraction from sample bundle"

    def handle(self, *args, **options):
        """Execute immunizations extractor test."""
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("FHIR IMMUNIZATIONS EXTRACTOR TEST"))
        self.stdout.write("=" * 80 + "\n")
        
        # Check for Portuguese bundle first (may have immunizations)
        pt_bundle_path = Path("test_data/eu_member_states/PT/2-1234-W7_enhanced_fhir_bundle_pre_gazelle_fix_backup.json")
        sample_bundle_path = Path("patient_data/test_data/sample_fhir_bundle.json")
        
        # Try Portuguese bundle first, fall back to sample
        bundle_path = pt_bundle_path if pt_bundle_path.exists() else sample_bundle_path
        
        if not bundle_path.exists():
            self.stdout.write(self.style.ERROR(f"❌ No bundle found. Tried:"))
            self.stdout.write(f"   - {pt_bundle_path}")
            self.stdout.write(f"   - {sample_bundle_path}")
            self.stdout.write("\nℹ️  To test with actual data, ensure a bundle with Immunization resources exists.")
            return
        
        self.stdout.write(f"📂 Loading bundle: {bundle_path}")
        
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                fhir_bundle = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to load bundle: {e}"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✅ Bundle loaded successfully\n"))
        
        # Check if bundle has any Immunization resources
        entries = fhir_bundle.get("entry", [])
        immunization_count = sum(1 for e in entries if e.get("resource", {}).get("resourceType") == "Immunization")
        
        if immunization_count == 0:
            self.stdout.write(self.style.WARNING("⚠️  No Immunization resources found in bundle"))
            self.stdout.write("\nℹ️  This is expected - the Portuguese test bundle may not include immunizations.")
            self.stdout.write("   The extractor is ready to process Immunization resources when available.\n")
            
            # Still demonstrate the extractor configuration
            extractor = FHIRImmunizationsExtractor()
            
            self.stdout.write(f"🔧 Extractor Configuration:")
            self.stdout.write(f"   Section ID: {extractor.section_id}")
            self.stdout.write(f"   Section Title: {extractor.section_title}")
            self.stdout.write(f"   LOINC Code: {extractor.section_code}")
            self.stdout.write(f"   Resource Type: {extractor.fhir_resource_type}")
            self.stdout.write(f"   Icon: {extractor.icon_class}\n")
            
            self.stdout.write(self.style.SUCCESS("✅ Extractor initialized successfully"))
            self.stdout.write(f"   Ready to process Immunization resources\n")
            
            # Show expected FHIR R4 Immunization structure
            self.stdout.write("-" * 80)
            self.stdout.write("EXPECTED FHIR R4 IMMUNIZATION STRUCTURE")
            self.stdout.write("-" * 80 + "\n")
            
            example_immunization = {
                "resourceType": "Immunization",
                "id": "example",
                "status": "completed",
                "vaccineCode": {
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/cvx",
                        "code": "207",
                        "display": "COVID-19, mRNA, LNP-S, PF"
                    }],
                    "text": "COVID-19 Vaccine"
                },
                "occurrenceDateTime": "2024-01-15",
                "lotNumber": "ABC123",
                "protocolApplied": [{
                    "doseNumberPositiveInt": 1,
                    "targetDisease": [{
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "840539006",
                            "display": "COVID-19"
                        }]
                    }]
                }]
            }
            
            self.stdout.write(json.dumps(example_immunization, indent=2))
            self.stdout.write("\n")
            
            return
        
        # Initialize extractor
        extractor = FHIRImmunizationsExtractor()
        
        self.stdout.write(f"🔧 Extractor Configuration:")
        self.stdout.write(f"   Section ID: {extractor.section_id}")
        self.stdout.write(f"   Section Title: {extractor.section_title}")
        self.stdout.write(f"   LOINC Code: {extractor.section_code}")
        self.stdout.write(f"   Resource Type: {extractor.fhir_resource_type}\n")
        
        # Extract immunizations
        self.stdout.write(f"🔍 Extracting {immunization_count} immunizations from bundle...")
        
        try:
            result = extractor.extract_section(fhir_bundle)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Extraction failed: {e}"))
            import traceback
            traceback.print_exc()
            return
        
        # Display results (result is the section data dict directly)
        entries = result.get("clinical_table", {}).get("entries", [])
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Extracted {len(entries)} immunizations\n"))
        
        # Display each immunization
        self.stdout.write("-" * 80)
        self.stdout.write("IMMUNIZATION DETAILS")
        self.stdout.write("-" * 80 + "\n")
        
        for idx, entry in enumerate(entries, 1):
            table_data = entry.get("table_data", {})
            
            self.stdout.write(self.style.WARNING(f"\n💉 IMMUNIZATION {idx}:"))
            self.stdout.write(f"   Vaccine: {table_data.get('vaccine_name', 'N/A')}")
            self.stdout.write(f"   Date: {table_data.get('immunization_date', 'N/A')}")
            self.stdout.write(f"   Status: {table_data.get('status', 'N/A')}")
            
            dose_number = table_data.get("dose_number")
            if dose_number:
                self.stdout.write(f"   Dose Number: {dose_number}")
            
            series = table_data.get("series")
            if series:
                self.stdout.write(f"   Series: {series}")
            
            target_disease = table_data.get("target_disease")
            if target_disease:
                self.stdout.write(f"   Protects Against: {target_disease}")
            
            lot_number = table_data.get("lot_number")
            if lot_number:
                self.stdout.write(f"   Lot Number: {lot_number}")
            
            manufacturer = table_data.get("manufacturer")
            if manufacturer:
                self.stdout.write(f"   Manufacturer: {manufacturer}")
            
            site = table_data.get("site")
            if site:
                self.stdout.write(f"   Site: {site}")
            
            route = table_data.get("route")
            if route:
                self.stdout.write(f"   Route: {route}")
            
            dose = table_data.get("dose")
            if dose:
                self.stdout.write(f"   Dose: {dose}")
            
            performer = table_data.get("performer")
            if performer:
                self.stdout.write(f"   Administered By: {performer}")
            
            reaction = table_data.get("reaction")
            if reaction:
                self.stdout.write(f"   Reaction: {reaction}")
            
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
        
        # Count by status
        statuses = {}
        for entry in entries:
            status = entry.get("table_data", {}).get("status", "Unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        self.stdout.write("💉 Immunizations by Status:")
        for status, count in statuses.items():
            self.stdout.write(f"   {status}: {count}")
        
        # Count by target disease
        diseases = {}
        for entry in entries:
            disease = entry.get("table_data", {}).get("target_disease")
            if disease:
                diseases[disease] = diseases.get(disease, 0) + 1
        
        if diseases:
            self.stdout.write("\n🦠 Immunizations by Target Disease:")
            for disease, count in diseases.items():
                self.stdout.write(f"   {disease}: {count}")
        
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
        
        # Check 1: Immunizations extracted
        if len(entries) > 0:
            self.stdout.write(self.style.SUCCESS("✅ Check 1: Immunizations extracted"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 1: No immunizations extracted"))
        
        # Check 2: All immunizations have vaccine names
        all_have_names = all(e.get("table_data", {}).get("vaccine_name") for e in entries)
        if all_have_names:
            self.stdout.write(self.style.SUCCESS("✅ Check 2: All immunizations have vaccine names"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 2: Some immunizations missing vaccine names"))
        
        # Check 3: All immunizations have dates
        all_have_dates = all(e.get("table_data", {}).get("immunization_date") for e in entries)
        if all_have_dates:
            self.stdout.write(self.style.SUCCESS("✅ Check 3: All immunizations have dates"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 3: Some immunizations missing dates"))
        
        # Check 4: All immunizations have status
        all_have_status = all(e.get("table_data", {}).get("status") for e in entries)
        if all_have_status:
            self.stdout.write(self.style.SUCCESS("✅ Check 4: All immunizations have status"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 4: Some immunizations missing status"))
        
        # Check 5: CDA field aliases present
        has_aliases = all(
            e.get("table_data", {}).get("vaccination_name") and
            e.get("table_data", {}).get("vaccination_date")
            for e in entries
        )
        if has_aliases:
            self.stdout.write(self.style.SUCCESS("✅ Check 5: CDA field aliases present"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 5: CDA field aliases missing"))
        
        # Check 6: Section metadata present
        section_id = result.get("section_id")
        if section_id == "immunizations":
            self.stdout.write(self.style.SUCCESS("✅ Check 6: Section metadata present"))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR("❌ Check 6: Section metadata missing or invalid"))
        
        # Check 7: Display configuration present
        clinical_table = result.get("clinical_table", {})
        display_config = clinical_table.get("display_config", {})
        if display_config and display_config.get("display_format") == "card":
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
        output_file = "test_fhir_immunizations_output.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            self.stdout.write(f"📄 Detailed results exported to: {output_file}\n")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Could not export results: {e}\n"))
