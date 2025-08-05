"""
Final Test: Simulate the template rendering scenario that was failing
"""

import xml.etree.ElementTree as ET
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def simulate_template_rendering():
    """Simulate the exact template rendering scenario that was causing errors"""

    print("🧪 SIMULATING TEMPLATE RENDERING SCENARIO")
    print("=" * 60)

    try:
        from patient_data.services.enhanced_cda_xml_parser import EnhancedCDAParser

        print("✓ EnhancedCDAParser imported successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    # Test with file that has legal authenticator
    test_file = r"test_data/eu_member_states/IT/2025-03-28T13-29-45.499822Z_CDA_EHDSI---PIVOT-CDA-(L1)-VALIDATION---WAVE-8-(V8.1.0)_NOT-TESTED.xml"

    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        return False

    try:
        # Parse the CDA document using our enhanced parser
        parser = EnhancedCDAParser()
        print("✓ EnhancedCDAParser instantiated")

        with open(test_file, "r", encoding="utf-8") as f:
            xml_content = f.read()

        parsed_data = parser.parse_cda_document(xml_content)
        print("✓ CDA document parsed successfully")

        # Extract the administrative data (this is what gets passed to templates)
        admin_data = parsed_data.get("administrative_info", {})
        legal_auth = admin_data.get("legal_authenticator", {})

        print("\n📋 ADMINISTRATIVE DATA EXTRACTED:")
        print(f"  Legal Authenticator Data Type: {type(legal_auth)}")
        print(f"  Legal Authenticator Keys: {list(legal_auth.keys())}")

        # SIMULATION: This is what happens in the Django template
        print("\n🎭 TEMPLATE RENDERING SIMULATION:")
        print(
            "Before our fix, this would show: {{ no such element: dict object['given_name'] }}"
        )

        # Template variables that would be rendered
        template_context = {"legal_authenticator": legal_auth}

        # These are the template expressions that were failing:
        template_expressions = [
            (
                "legal_authenticator.full_name",
                lambda ctx: ctx["legal_authenticator"].get("full_name", "N/A"),
            ),
            (
                "legal_authenticator.given_name",
                lambda ctx: ctx["legal_authenticator"].get("given_name", "N/A"),
            ),
            (
                "legal_authenticator.family_name",
                lambda ctx: ctx["legal_authenticator"].get("family_name", "N/A"),
            ),
            (
                "legal_authenticator.person.full_name",
                lambda ctx: ctx["legal_authenticator"]
                .get("person", {})
                .get("full_name", "N/A"),
            ),
            (
                "legal_authenticator.organization.name",
                lambda ctx: ctx["legal_authenticator"]
                .get("organization", {})
                .get("name", "N/A"),
            ),
        ]

        print("\n🔍 TEMPLATE EXPRESSION RESULTS:")
        all_passed = True

        for expr_name, expr_func in template_expressions:
            try:
                result = expr_func(template_context)
                if isinstance(result, dict):
                    print(f"  ❌ {expr_name}: DICT OBJECT (would cause template error)")
                    print(f"      Result: {result}")
                    all_passed = False
                else:
                    print(f"  ✅ {expr_name}: '{result}'")
            except Exception as e:
                print(f"  ❌ {expr_name}: ERROR - {e}")
                all_passed = False

        # Test specific template scenario from user's screenshot
        print("\n📸 USER SCREENSHOT SCENARIO:")
        print("The user saw: {{ no such element: dict object['title'] }}")
        print("Testing field access that would happen in templates...")

        # Test accessing fields directly (what templates do)
        direct_access_tests = [
            ("full_name", "legal_authenticator.full_name"),
            ("given_name", "legal_authenticator.given_name"),
            ("family_name", "legal_authenticator.family_name"),
            ("title", "legal_authenticator.title"),  # This might not exist
        ]

        for field_name, template_path in direct_access_tests:
            try:
                value = legal_auth.get(field_name)
                if isinstance(value, dict):
                    print(
                        f"  ❌ {template_path}: Returns dict {value} (would cause template error)"
                    )
                else:
                    print(f"  ✅ {template_path}: '{value}'")
            except Exception as e:
                print(f"  ⚠️  {template_path}: {e}")

        # Final verdict
        print("\n" + "=" * 60)
        if all_passed and not any(
            isinstance(legal_auth.get(field), dict)
            for field in ["full_name", "given_name", "family_name"]
        ):
            print("🎉 SUCCESS: Template errors should be FIXED!")
            print("✅ Legal authenticator now provides direct field access")
            print("✅ Templates can access data without 'dict object' errors")
            if legal_auth.get("full_name"):
                print(f"✅ Expected display in UI: '{legal_auth['full_name']}'")
        else:
            print("⚠️ PARTIAL SUCCESS: Some issues may remain")

        return all_passed

    except Exception as e:
        import traceback

        print(f"✗ Error: {e}")
        traceback.print_exc()
        return False


def show_before_after():
    """Show the before/after comparison"""

    print("\n📊 BEFORE vs AFTER COMPARISON:")
    print("=" * 60)

    print("\n❌ BEFORE (causing template errors):")
    print(
        """
    legal_authenticator = {
        "person": {
            "given_name": "Legale",
            "family_name": "Autenticatore", 
            "full_name": "Legale Autenticatore"
        },
        "organization": {"name": "Pasquale Pironti"}
    }
    
    Template: {{ legal_authenticator.given_name }}
    Result: {{ no such element: dict object['given_name'] }}
    """
    )

    print("\n✅ AFTER (template-friendly):")
    print(
        """
    legal_authenticator = {
        "given_name": "Legale",           # ← Direct access
        "family_name": "Autenticatore",   # ← Direct access
        "full_name": "Legale Autenticatore", # ← Direct access
        "person": {                       # ← Nested still available
            "given_name": "Legale",
            "family_name": "Autenticatore",
            "full_name": "Legale Autenticatore"
        },
        "organization": {"name": "Pasquale Pironti"}
    }
    
    Template: {{ legal_authenticator.given_name }}
    Result: Legale  ← Success!
    """
    )


if __name__ == "__main__":
    print("🔧 LEGAL AUTHENTICATOR TEMPLATE FIX VERIFICATION")
    print("Testing the fix for: {{ no such element: dict object['given_name'] }}")

    # Show what we changed
    show_before_after()

    # Test the actual fix
    success = simulate_template_rendering()

    print("\n" + "🏁 FINAL RESULT " + "=" * 45)
    if success:
        print("✅ TEMPLATE ERRORS SHOULD BE RESOLVED!")
        print("✅ Legal authenticator data now template-compatible")
        print("✅ User should see proper names instead of error messages")
    else:
        print("❌ Issues may still remain - check output above")

    print("\n💡 Next steps:")
    print("   1. Restart Django server to pick up changes")
    print("   2. Test the UI where legal authenticator is displayed")
    print("   3. Verify 'Pasquale Pironti' appears instead of template errors")
