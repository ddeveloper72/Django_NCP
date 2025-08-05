#!/usr/bin/env python3
"""
Template Migration Helper for Date Formatting
Helps identify templates that need date formatting updates
"""

import os
import re
from pathlib import Path


def find_date_references_in_templates():
    """Find templates with raw date displays that could benefit from formatting"""

    template_dirs = [
        "templates",
        "patient_data/templates",
        "translation_services/templates",
        "ehealth_portal/templates",
        "translation_manager/templates",
    ]

    # Patterns that indicate raw date usage
    raw_date_patterns = [
        r"\{\{\s*\w*\.?\w*birth_date\s*\}\}",  # {{ birth_date }} or {{ patient.birth_date }}
        r"\{\{\s*\w*\.?\w*creation_date\s*\}\}",  # {{ creation_date }}
        r"\{\{\s*\w*\.?\w*document_date\s*\}\}",  # {{ document_date }}
        r"\{\{\s*\w*\.?\w*date\s*\}\}",  # Generic {{ date }}
        r'["\']date["\']:\s*["\']\d{8}["\']',  # "date": "20240101"
        r'birth_date.*=.*["\']?\d{8}["\']?',  # birth_date = "19700101"
    ]

    findings = []

    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith(".html"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            for pattern in raw_date_patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    findings.append(
                                        {
                                            "file": file_path,
                                            "pattern": pattern,
                                            "matches": matches,
                                            "content_preview": (
                                                content[:200] + "..."
                                                if len(content) > 200
                                                else content
                                            ),
                                        }
                                    )
                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

    return findings


def generate_migration_suggestions(findings):
    """Generate specific migration suggestions for each finding"""

    suggestions = []

    for finding in findings:
        file_path = finding["file"]
        matches = finding["matches"]

        for match in matches:
            if "birth_date" in match.lower():
                suggestion = {
                    "file": file_path,
                    "original": match,
                    "replacement": f"{{{{ {match.strip('{}').strip()}|patient_birth_date }}}}",
                    "filter_needed": "patient_birth_date",
                    "description": "Convert raw birth date to formatted display",
                }
            elif "creation_date" in match.lower() or "document_date" in match.lower():
                suggestion = {
                    "file": file_path,
                    "original": match,
                    "replacement": f"{{{{ {match.strip('{}').strip()}|document_date }}}}",
                    "filter_needed": "document_date",
                    "description": "Convert raw document date to formatted display",
                }
            else:
                suggestion = {
                    "file": file_path,
                    "original": match,
                    "replacement": f"{{{{ {match.strip('{}').strip()}|document_date }}}}",
                    "filter_needed": "document_date",
                    "description": "Convert generic date to formatted display",
                }

            suggestions.append(suggestion)

    return suggestions


def check_template_filter_loading():
    """Check if templates are properly loading the date filters"""

    template_dirs = [
        "templates",
        "patient_data/templates",
        "translation_services/templates",
    ]
    templates_needing_load = []

    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            for root, dirs, files in os.walk(template_dir):
                for file in files:
                    if file.endswith(".html"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                content = f.read()

                            # Check if template uses date filters but doesn't load them
                            has_date_filters = any(
                                filter_name in content
                                for filter_name in [
                                    "patient_birth_date",
                                    "document_date",
                                    "patient_age",
                                ]
                            )
                            has_load_statement = "load patient_date_filters" in content

                            if has_date_filters and not has_load_statement:
                                templates_needing_load.append(file_path)

                        except Exception as e:
                            print(f"Error reading {file_path}: {e}")

    return templates_needing_load


def main():
    print("🔍 Django NCP Date Formatting Migration Helper")
    print("=" * 50)

    # Find raw date references
    print("\n1. Scanning for raw date references...")
    findings = find_date_references_in_templates()

    if findings:
        print(f"Found {len(findings)} potential date formatting opportunities:")
        for finding in findings:
            print(f"  📄 {finding['file']}")
            for match in finding["matches"]:
                print(f"    → {match}")
    else:
        print("✅ No raw date references found in templates")

    # Generate migration suggestions
    if findings:
        print("\n2. Migration suggestions:")
        suggestions = generate_migration_suggestions(findings)

        for suggestion in suggestions:
            print(f"\n📝 {suggestion['file']}")
            print(f"   Original:    {suggestion['original']}")
            print(f"   Replace with: {suggestion['replacement']}")
            print(f"   Filter:      {suggestion['filter_needed']}")
            print(f"   Description: {suggestion['description']}")

    # Check template filter loading
    print("\n3. Checking template filter loading...")
    templates_needing_load = check_template_filter_loading()

    if templates_needing_load:
        print("⚠️  Templates using date filters but missing load statement:")
        for template in templates_needing_load:
            print(f"  📄 {template}")
        print("\n💡 Add this line at the top of each template:")
        print("   {% load patient_date_filters %}")
    else:
        print("✅ All templates correctly load date filters")

    # Summary
    print("\n" + "=" * 50)
    print("📋 MIGRATION SUMMARY")
    print("=" * 50)

    if findings:
        print(f"🔧 Templates to update: {len(set(f['file'] for f in findings))}")
        print(f"🎯 Date references found: {sum(len(f['matches']) for f in findings)}")
        print("\n📖 Next steps:")
        print(
            "1. Add '{% load patient_date_filters %}' to templates using date filters"
        )
        print("2. Replace raw date variables with formatted filters:")
        print("   - {{ birth_date }} → {{ birth_date|patient_birth_date }}")
        print("   - {{ creation_date }} → {{ creation_date|document_date }}")
        print("3. Test templates to ensure proper formatting")
        print("4. Consider adding age displays where relevant")
    else:
        print("✅ Your templates are already using formatted dates!")

    print(f"\n🎨 Template filters available:")
    print("   - patient_birth_date: Format birth dates (01/01/1970)")
    print("   - document_date: Format document dates with time")
    print("   - patient_age: Calculate and display age (54 years)")
    print("   - patient_birth_date_with_age: Birth date + age in one")


if __name__ == "__main__":
    main()
