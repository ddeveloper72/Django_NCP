#!/usr/bin/env python
"""
Final verification test for removing database IDs from all patient displays
"""
import re


def test_template_database_id_removal():
    """Test that database IDs have been removed from all templates"""
    print("=== Database ID Removal Verification ===")
    print()

    templates_to_check = [
        "c:\\Users\\Duncan\\VS_Code_Projects\\django_ncp\\templates\\jinja2\\patient_data\\patient_cda.html",
        "c:\\Users\\Duncan\\VS_Code_Projects\\django_ncp\\templates\\jinja2\\ehealth_portal\\patient_search.html",
        "c:\\Users\\Duncan\\VS_Code_Projects\\django_ncp\\templates\\jinja2\\ehealth_portal\\patient_data.html",
        "c:\\Users\\Duncan\\VS_Code_Projects\\django_ncp\\templates\\jinja2\\patient_data\\patient_search_results.html",
    ]

    # Patterns that indicate database ID usage (these should NOT be found)
    bad_patterns = [
        r"ID:\s*{{\s*patient\.id\s*}}",
        r"ID:\s*{{\s*patient_identity\.patient_id\s*}}",
        r"ID:\s*{{\s*patient_identifier\.patient_id\s*}}",
        r">\s*{{\s*patient\.id\s*}}\s*<",
    ]

    # Patterns that indicate good CDA identifier usage (these SHOULD be found)
    good_patterns = [
        r"identifier\.extension",
        r"identifier\.assigningAuthorityName",
        r"identifier\.root",
        r"patient_identifiers",
        r"No CDA identifiers available",
    ]

    issues_found = []
    good_implementations = []

    for template_path in templates_to_check:
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            template_name = template_path.split("/")[-1]
            print(f"Checking {template_name}...")

            # Check for bad patterns (database IDs)
            for pattern in bad_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    issues_found.append(
                        f"❌ {template_name}: Found database ID pattern: {pattern}"
                    )
                    for match in matches:
                        issues_found.append(f"   Match: {match}")

            # Check for good patterns (CDA identifiers)
            found_good_patterns = []
            for pattern in good_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found_good_patterns.append(pattern)

            if found_good_patterns:
                good_implementations.append(
                    f"✅ {template_name}: Uses CDA patterns: {', '.join(found_good_patterns)}"
                )

        except FileNotFoundError:
            issues_found.append(f"❌ Template not found: {template_path}")
        except Exception as e:
            issues_found.append(f"❌ Error reading {template_path}: {e}")

    print("\n=== Results ===")

    if issues_found:
        print("⚠️  Issues Found:")
        for issue in issues_found:
            print(f"  {issue}")
    else:
        print("✅ No database ID patterns found in templates!")

    print("\n📋 Good Implementations:")
    for good in good_implementations:
        print(f"  {good}")

    print("\n=== Expected Display Examples ===")
    print("✅ Mario PINO should show: 'Ministero Economia e Finanze: NCPNPH80A01H501K'")
    print("✅ OR with OID: 'ID (2.16.840.1.113883.2.9.4.3.2): NCPNPH80A01H501K'")
    print("✅ Luxembourg should show: 'Patient ID (1.3.182.2.4.2): 2544557646'")
    print("✅ Fallback should show: 'No CDA identifiers available'")
    print("❌ Should NEVER show: 'ID: 74' or any database ID number")

    return len(issues_found) == 0


if __name__ == "__main__":
    success = test_template_database_id_removal()
    if success:
        print("\n🎉 SUCCESS: All templates properly use CDA identifiers!")
    else:
        print("\n⚠️  WARNING: Some templates still have database ID references")
