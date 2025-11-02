"""
Django management command to test FHIR Pipeline Manager.

Usage:
    python manage.py test_fhir_pipeline

Tests orchestration of all FHIR extractors through the pipeline manager.
"""

import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from patient_data.services.clinical_sections.pipeline.fhir_pipeline_manager import fhir_pipeline_manager
from patient_data.services.clinical_sections.extractors.fhir_allergies_extractor import FHIRAllergiesExtractor
from patient_data.services.clinical_sections.extractors.fhir_medications_extractor import FHIRMedicationsExtractor
from patient_data.services.clinical_sections.extractors.fhir_conditions_extractor import FHIRConditionsExtractor
from patient_data.services.clinical_sections.extractors.fhir_procedures_extractor import FHIRProceduresExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test FHIR Pipeline Manager with Portuguese bundle'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('FHIR PIPELINE MANAGER TEST'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Load Portuguese FHIR bundle
        bundle_path = Path(settings.BASE_DIR) / 'test_data' / 'eu_member_states' / 'PT' / '2-1234-W7_enhanced_fhir_bundle_pre_gazelle_fix_backup.json'
        
        self.stdout.write(f'Loading bundle: {bundle_path}')
        
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                fhir_bundle = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Error: Bundle not found: {bundle_path}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Error: Invalid JSON: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Success: Bundle loaded successfully'))
        self.stdout.write(f'Bundle Type: {fhir_bundle.get("type")}')
        self.stdout.write(f'Bundle ID: {fhir_bundle.get("id")}\n')

        # Register all extractors with the pipeline manager
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('REGISTERING EXTRACTORS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        extractors = [
            FHIRAllergiesExtractor(),
            FHIRMedicationsExtractor(),
            FHIRConditionsExtractor(),
            FHIRProceduresExtractor(),
        ]

        for extractor in extractors:
            fhir_pipeline_manager.register_extractor(extractor)
            self.stdout.write(f'Registered: {extractor.section_title} (ID: {extractor.section_id})')

        registered = fhir_pipeline_manager.get_all_extractors()
        self.stdout.write(f'\nTotal Registered Extractors: {len(registered)}\n')

        # Process FHIR bundle through pipeline
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('PROCESSING FHIR BUNDLE'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        session_id = "test_pipeline_session"
        results = fhir_pipeline_manager.process_fhir_bundle(
            fhir_bundle=fhir_bundle,
            session_id=session_id
        )

        # Display summary
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('PIPELINE RESULTS SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        summary = results.get('summary', {})
        self.stdout.write(f'Total Sections Processed: {summary.get("total_sections")}')
        self.stdout.write(f'Sections With Data: {summary.get("sections_with_data")}')
        self.stdout.write(f'Total Entries Extracted: {summary.get("total_entries")}')
        self.stdout.write(f'Bundle Type: {summary.get("bundle_type")}')
        self.stdout.write(f'Bundle ID: {summary.get("bundle_id")}\n')

        # Display section-by-section results
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('SECTION EXTRACTION DETAILS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        sections = results.get('sections', {})
        for section_id, section_data in sections.items():
            self.stdout.write(f'\n{section_data.get("title")} (ID: {section_id})')
            self.stdout.write(f'  Entries: {section_data.get("entry_count")}')
            self.stdout.write(f'  Has Data: {section_data.get("has_entries")}')
            self.stdout.write(f'  Is Coded: {section_data.get("is_coded_section")}')
            self.stdout.write(f'  Clinical Codes: {len(section_data.get("clinical_codes", []))}')
            
            if section_data.get("has_entries"):
                entries = section_data.get("clinical_table", {}).get("entries", [])
                self.stdout.write(f'  Sample Entries:')
                for i, entry in enumerate(entries[:3], 1):
                    self.stdout.write(f'    {i}. {entry.get("display_text")}')

        # Test template context generation
        self.stdout.write(f'\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('TEMPLATE CONTEXT GENERATION'))
        self.stdout.write('='*80 + '\n')

        context = fhir_pipeline_manager.get_template_context(session_id=session_id)

        self.stdout.write(f'Context Keys: {list(context.keys())}\n')
        
        # Display clinical data counts
        clinical_sections = ['allergies', 'medications', 'problems', 'procedures']
        for section in clinical_sections:
            entries = context.get(section, [])
            self.stdout.write(f'{section.capitalize()}: {len(entries)} entries')

        # Display metadata
        metadata = context.get('sections_metadata', {})
        self.stdout.write(f'\nSections Metadata: {len(metadata)} sections')
        
        self.stdout.write(f'\nData Source: {context.get("data_source")}')
        self.stdout.write(f'Bundle Processed: {context.get("bundle_processed")}')
        self.stdout.write(f'Total Entries: {context.get("total_entries")}')

        # Run validation checks
        self.stdout.write(f'\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('VALIDATION CHECKS'))
        self.stdout.write('='*80 + '\n')

        checks_passed = 0
        total_checks = 0

        # Check 1: All extractors registered
        total_checks += 1
        if len(registered) == 4:
            self.stdout.write(self.style.SUCCESS('Success: All 4 extractors registered'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR(f'Error: Expected 4 extractors, got {len(registered)}'))

        # Check 2: All sections processed
        total_checks += 1
        if summary.get('total_sections') == 4:
            self.stdout.write(self.style.SUCCESS('Success: All 4 sections processed'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR(f'Error: Expected 4 sections, got {summary.get("total_sections")}'))

        # Check 3: Expected total entries (4 allergies + 5 medications + 7 conditions + 3 procedures = 19)
        total_checks += 1
        expected_entries = 19
        if summary.get('total_entries') == expected_entries:
            self.stdout.write(self.style.SUCCESS(f'Success: Extracted expected {expected_entries} total entries'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING(f'Warning: Expected {expected_entries} entries, got {summary.get("total_entries")}'))

        # Check 4: All sections have data
        total_checks += 1
        if summary.get('sections_with_data') == 4:
            self.stdout.write(self.style.SUCCESS('Success: All 4 sections have data'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR(f'Error: Expected 4 sections with data, got {summary.get("sections_with_data")}'))

        # Check 5: Template context has clinical sections
        total_checks += 1
        clinical_data_present = all(section in context for section in clinical_sections)
        if clinical_data_present:
            self.stdout.write(self.style.SUCCESS('Success: Template context has all clinical sections'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Template context missing clinical sections'))

        # Check 6: Template context has metadata
        total_checks += 1
        if 'sections_metadata' in context and len(metadata) == 4:
            self.stdout.write(self.style.SUCCESS('Success: Template context has complete metadata'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Template context missing or incomplete metadata'))

        # Check 7: Cached results retrievable
        total_checks += 1
        cached_summary = fhir_pipeline_manager.get_section_summary(session_id)
        if cached_summary and not cached_summary.get('error'):
            self.stdout.write(self.style.SUCCESS('Success: Cached results retrievable'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Failed to retrieve cached results'))

        # Check 8: Individual extractor retrieval works
        total_checks += 1
        allergies_ext = fhir_pipeline_manager.get_extractor('allergies')
        if allergies_ext and allergies_ext.section_id == 'allergies':
            self.stdout.write(self.style.SUCCESS('Success: Individual extractor retrieval works'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Failed to retrieve individual extractor'))

        # Summary
        self.stdout.write(f'\n' + '='*80)
        if checks_passed == total_checks:
            self.stdout.write(self.style.SUCCESS(f'SUCCESS: ALL VALIDATION CHECKS PASSED! ({checks_passed}/{total_checks})'))
        else:
            self.stdout.write(self.style.WARNING(f'WARNING: VALIDATION: {checks_passed}/{total_checks} checks passed'))
        self.stdout.write('='*80 + '\n')

        # Export results to JSON for inspection
        output_file = Path(settings.BASE_DIR) / 'test_fhir_pipeline_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'results': results,
                'context': context
            }, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'Full results exported to: {output_file}\n')

        # Test cache clearing
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('CACHE MANAGEMENT TEST'))
        self.stdout.write('='*80 + '\n')

        self.stdout.write('Testing cache clear...')
        fhir_pipeline_manager.clear_cache(session_id)
        cleared_summary = fhir_pipeline_manager.get_section_summary(session_id)
        
        if cleared_summary.get('error'):
            self.stdout.write(self.style.SUCCESS('Success: Cache cleared successfully'))
        else:
            self.stdout.write(self.style.ERROR('Error: Cache not properly cleared'))

        self.stdout.write('\n')
