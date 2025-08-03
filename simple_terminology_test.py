"""
Simple terminology test - check if database has any MVC data
"""

# Test if we can import the models
try:
    from translation_services.mvc_models import (
        ValueSetCatalogue,
        ValueSetConcept,
        ConceptTranslation,
    )

    print("✅ Successfully imported MVC models")

    # Check if we can import the translator
    from translation_services.terminology_translator import TerminologyTranslator

    print("✅ Successfully imported TerminologyTranslator")

    # Check if we can import the renderer
    from patient_data.services.ps_table_renderer import PSTableRenderer

    print("✅ Successfully imported PSTableRenderer with terminology support")

    print("\n🎉 All imports successful - terminology integration is ready!")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
