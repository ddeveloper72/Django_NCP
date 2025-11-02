"""
Django management command to test FHIR Procedures Extractor.

Usage:
    python manage.py test_fhir_procedures

Tests extraction of Procedure resources from Portuguese FHIR bundle.
"""

import json
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

from patient_data.services.clinical_sections.extractors.fhir_procedures_extractor import FHIRProceduresExtractor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test FHIR Procedures Extractor with Portuguese bundle'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('FHIR PROCEDURES EXTRACTOR TEST'))
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

        self.stdout.write(self.style.SUCCESS(f'Success: Bundle loaded successfully\n'))

        # Initialize extractor
        extractor = FHIRProceduresExtractor()
        
        # Extract procedures section
        self.stdout.write('Extracting procedures section...\n')
        section_data = extractor.extract_section(fhir_bundle)

        # Display results
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('EXTRACTION RESULTS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        self.stdout.write(f'Section ID: {section_data["section_id"]}')
        self.stdout.write(f'Section Title: {section_data["title"]}')
        self.stdout.write(f'Section Code: {section_data["section_code"]} ({section_data["section_system"]})')
        self.stdout.write(f'FHIR Resource Type: {section_data["fhir_resource_type"]}')
        self.stdout.write(f'Data Source: {section_data["data_source"]}\n')

        self.stdout.write(f'Has Entries: {section_data["has_entries"]}')
        self.stdout.write(f'Entry Count: {section_data["entry_count"]}')
        self.stdout.write(f'Is Coded Section: {section_data["is_coded_section"]}')
        self.stdout.write(f'Bundle Has Structured Codes: {section_data["bundle_has_structured_codes"]}')
        self.stdout.write(f'Display Text Only: {section_data["display_text_only"]}\n')

        # Display entries
        if section_data["has_entries"]:
            self.stdout.write(self.style.SUCCESS('='*80))
            self.stdout.write(self.style.SUCCESS('PROCEDURE ENTRIES'))
            self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

            entries = section_data["clinical_table"]["entries"]
            for i, entry in enumerate(entries, 1):
                self.stdout.write(f'\n{i}. {entry["display_text"]}')
                self.stdout.write(f'   ID: {entry["entry_id"]}')
                self.stdout.write(f'   Status: {entry["clinical_status"]}')
                
                if entry.get("table_data"):
                    td = entry["table_data"]
                    if td.get("procedure_date"):
                        self.stdout.write(f'   Date Performed: {td["procedure_date"]}')
                    if td.get("performer"):
                        self.stdout.write(f'   Performed By: {td["performer"]}')
                    if td.get("location"):
                        self.stdout.write(f'   Location: {td["location"]}')
                    if td.get("reason"):
                        self.stdout.write(f'   Indication: {td["reason"]}')
                    if td.get("body_site"):
                        self.stdout.write(f'   Body Site: {td["body_site"]}')
                    if td.get("outcome"):
                        self.stdout.write(f'   Outcome: {td["outcome"]}')
                    if td.get("notes"):
                        self.stdout.write(f'   Notes: {td["notes"]}')
                
                if entry.get("coded_concepts"):
                    self.stdout.write(f'   Coded Concepts: {len(entry["coded_concepts"])} found')
                    for concept in entry["coded_concepts"][:2]:  # Show first 2
                        code = concept.get("code", "N/A")
                        system = concept.get("system", "N/A")
                        display = concept.get("display", "N/A")
                        system_name = concept.get("system_name", "Unknown")
                        self.stdout.write(f'      - {display} ({system_name}: {code})')

        # Display clinical codes summary
        self.stdout.write(f'\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('CLINICAL CODES SUMMARY'))
        self.stdout.write('='*80 + '\n')
        
        clinical_codes = section_data["clinical_codes"]
        self.stdout.write(f'Total Clinical Codes: {len(clinical_codes)}')
        
        if clinical_codes:
            # Group by system
            by_system = {}
            for code in clinical_codes:
                system_name = code.get("system_name", "Unknown")
                by_system.setdefault(system_name, []).append(code)
            
            for system_name, codes in by_system.items():
                self.stdout.write(f'\n{system_name}: {len(codes)} codes')
                for code in codes[:3]:  # Show first 3 from each system
                    display = code.get("display", "N/A")
                    code_val = code.get("code", "N/A")
                    self.stdout.write(f'   - {display} ({code_val})')

        # Display table configuration
        self.stdout.write(f'\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('TABLE CONFIGURATION'))
        self.stdout.write('='*80 + '\n')
        
        columns = section_data["clinical_table"]["columns"]
        self.stdout.write(f'Columns: {len(columns)}')
        for col in columns:
            self.stdout.write(f'   - {col["label"]} (key: {col["key"]})')

        display_config = section_data["clinical_table"]["display_config"]
        self.stdout.write(f'\nDisplay Format: {display_config["display_format"]}')
        self.stdout.write(f'Show Timeline: {display_config["show_timeline"]}')
        self.stdout.write(f'Group By: {display_config["group_by"]}')
        self.stdout.write(f'Collapsible: {display_config["collapsible"]}')
        
        self.stdout.write(f'\nStatus Colors:')
        for status, color in display_config["status_colors"].items():
            self.stdout.write(f'   - {status}: {color}')

        # Run validation checks
        self.stdout.write(f'\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('VALIDATION CHECKS'))
        self.stdout.write('='*80 + '\n')

        checks_passed = 0
        total_checks = 0

        # Check 1: Section has correct ID
        total_checks += 1
        if section_data["section_id"] == "procedures":
            self.stdout.write(self.style.SUCCESS('Success: Section ID is correct'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR(f'Error: Section ID incorrect: {section_data["section_id"]}'))

        # Check 2: Expected number of entries (Portuguese bundle has 3 procedures)
        total_checks += 1
        expected_count = 3
        if section_data["entry_count"] == expected_count:
            self.stdout.write(self.style.SUCCESS(f'Success: Entry count matches expected ({expected_count})'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING(f'Warning: Entry count: {section_data["entry_count"]}, expected: {expected_count}'))

        # Check 3: All entries have display text
        total_checks += 1
        all_have_display = all(entry.get("display_text") for entry in section_data["clinical_table"]["entries"])
        if all_have_display:
            self.stdout.write(self.style.SUCCESS('Success: All entries have display text'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Some entries missing display text'))

        # Check 4: All entries have status
        total_checks += 1
        all_have_status = all(entry.get("clinical_status") for entry in section_data["clinical_table"]["entries"])
        if all_have_status:
            self.stdout.write(self.style.SUCCESS('Success: All entries have clinical status'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Some entries missing clinical status'))

        # Check 5: All entries have procedure dates
        total_checks += 1
        all_have_dates = all(
            entry.get("table_data", {}).get("procedure_date") 
            for entry in section_data["clinical_table"]["entries"]
        )
        if all_have_dates:
            self.stdout.write(self.style.SUCCESS('Success: All entries have procedure dates'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING('Warning: Some entries missing procedure dates'))

        # Check 6: Has clinical codes
        total_checks += 1
        if len(clinical_codes) > 0:
            self.stdout.write(self.style.SUCCESS(f'Success: Clinical codes extracted ({len(clinical_codes)} codes)'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.WARNING('Warning: No clinical codes extracted'))

        # Check 7: Table columns configured
        total_checks += 1
        if len(columns) >= 4:
            self.stdout.write(self.style.SUCCESS(f'Success: Table columns configured ({len(columns)} columns)'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR(f'Error: Insufficient table columns: {len(columns)}'))

        # Check 8: Data structure matches CDA format
        total_checks += 1
        required_keys = ["section_id", "title", "clinical_table", "clinical_codes", "is_coded_section"]
        has_all_keys = all(key in section_data for key in required_keys)
        if has_all_keys:
            self.stdout.write(self.style.SUCCESS('Success: Data structure matches CDA format'))
            checks_passed += 1
        else:
            self.stdout.write(self.style.ERROR('Error: Data structure incomplete'))

        # Summary
        self.stdout.write(f'\n' + '='*80)
        if checks_passed == total_checks:
            self.stdout.write(self.style.SUCCESS(f'SUCCESS: ALL VALIDATION CHECKS PASSED! ({checks_passed}/{total_checks})'))
        else:
            self.stdout.write(self.style.WARNING(f'WARNING: VALIDATION: {checks_passed}/{total_checks} checks passed'))
        self.stdout.write('='*80 + '\n')

        # Export to JSON for inspection
        output_file = Path(settings.BASE_DIR) / 'test_fhir_procedures_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f'Full results exported to: {output_file}\n')
