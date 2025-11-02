"""
Django management command to test FHIR allergies extractor
Usage: python manage.py test_fhir_allergies
"""

import json
from django.core.management.base import BaseCommand
from pathlib import Path
from patient_data.services.clinical_sections.extractors.fhir_allergies_extractor import FHIRAllergiesExtractor


class Command(BaseCommand):
    help = 'Test FHIR Allergies Extractor with Portuguese Bundle'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS(
            "FHIR ALLERGIES EXTRACTOR TEST - Portuguese Bundle (Diana Ferreira)"
        ))
        self.stdout.write("=" * 80)
        
        # Load Portuguese bundle
        # Get Django project root
        import django
        from django.conf import settings
        project_root = Path(settings.BASE_DIR)
        bundle_path = project_root / "test_data" / "eu_member_states" / "PT" / "2-1234-W7_enhanced_fhir_bundle_pre_gazelle_fix_backup.json"
        
        self.stdout.write(f"\n📂 Loading bundle from: {bundle_path}")
        
        with open(bundle_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Bundle loaded: {bundle.get('id')}"))
        self.stdout.write(f"   Bundle type: {bundle.get('type')}")
        self.stdout.write(f"   Total entries: {len(bundle.get('entry', []))}")
        
        # Initialize extractor
        extractor = FHIRAllergiesExtractor()
        self.stdout.write(self.style.SUCCESS(f"\n✅ Extractor initialized:"))
        self.stdout.write(f"   Section ID: {extractor.section_id}")
        self.stdout.write(f"   Section Title: {extractor.section_title}")
        self.stdout.write(f"   FHIR Resource Type: {extractor.fhir_resource_type}")
        
        # Extract allergies section
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.WARNING("EXTRACTING ALLERGIES SECTION"))
        self.stdout.write("=" * 80)
        
        section = extractor.extract_section(bundle)
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n📊 EXTRACTION RESULTS:"))
        self.stdout.write(f"   Section ID: {section['section_id']}")
        self.stdout.write(f"   Title: {section['title']}")
        self.stdout.write(f"   Has Entries: {section['has_entries']}")
        self.stdout.write(f"   Entry Count: {section['entry_count']}")
        self.stdout.write(f"   Is Coded Section: {section['is_coded_section']}")
        self.stdout.write(f"   Total Codes: {len(section['clinical_codes'])}")
        
        # Display individual entries
        if section['has_entries']:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.WARNING("EXTRACTED ALLERGY ENTRIES"))
            self.stdout.write("=" * 80)
            
            entries = section['clinical_table']['entries']
            for idx, entry in enumerate(entries, 1):
                self.stdout.write(self.style.SUCCESS(f"\n🔹 Entry {idx}/{len(entries)}"))
                self.stdout.write(f"   Display Text: {entry['display_text']}")
                self.stdout.write(f"   Category: {entry.get('category', 'N/A')}")
                self.stdout.write(f"   Severity: {entry.get('severity', 'N/A')}")
                self.stdout.write(f"   Status: {entry.get('clinical_status', 'N/A')}")
                self.stdout.write(f"   Verification: {entry.get('verification_status', 'N/A')}")
                self.stdout.write(f"   Onset Date: {entry.get('onset_date', 'N/A')}")
                
                if entry.get('notes'):
                    self.stdout.write("   Notes:")
                    for note in entry['notes']:
                        self.stdout.write(f"      - {note}")
                
                if entry.get('coded_concepts'):
                    self.stdout.write(f"   Coded Concepts: {len(entry['coded_concepts'])}")
                    for concept in entry['coded_concepts']:
                        self.stdout.write(f"      - {concept.get('display', 'No display')} [{concept.get('system_name', 'No system')}]")
        
        # Display clinical codes summary
        if section['clinical_codes']:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.WARNING("CLINICAL CODES FOR CTS INTEGRATION"))
            self.stdout.write("=" * 80)
            
            for idx, code in enumerate(section['clinical_codes'], 1):
                self.stdout.write(f"\n   Code {idx}:")
                self.stdout.write(f"      Display: {code.get('display', 'N/A')}")
                self.stdout.write(f"      Code: {code.get('code', 'N/A')}")
                self.stdout.write(f"      System: {code.get('system_name', 'N/A')}")
                self.stdout.write(f"      Type: {code.get('type', 'N/A')}")
        
        # Validation
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.WARNING("VALIDATION CHECKS"))
        self.stdout.write("=" * 80)
        
        checks = {
            "Has section_id": 'section_id' in section,
            "Has title": 'title' in section,
            "Has entries": section['has_entries'],
            "Entry count matches": section['entry_count'] == 4,  # Portuguese bundle has 4 allergies
            "Has clinical codes": len(section['clinical_codes']) > 0,
            "Has table config": 'clinical_table' in section,
            "Data source is FHIR": section.get('data_source') == 'FHIR',
        }
        
        self.stdout.write("")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            style = self.style.SUCCESS if result else self.style.ERROR
            self.stdout.write(style(f"   {status} {check_name}: {result}"))
        
        all_passed = all(checks.values())
        
        self.stdout.write("\n" + "=" * 80)
        if all_passed:
            self.stdout.write(self.style.SUCCESS("🎉 ALL VALIDATION CHECKS PASSED!"))
        else:
            self.stdout.write(self.style.ERROR("⚠️  SOME VALIDATION CHECKS FAILED"))
        self.stdout.write("=" * 80)
        
        # Export to JSON
        output_path = project_root / "test_fhir_allergies_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(section, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f"\n📄 Full section data exported to: {output_path}"))
