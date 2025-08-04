import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")

import django

django.setup()

# Test importing the view function
try:
    from patient_data.views import patient_details_view

    print("SUCCESS: patient_details_view imported without errors")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
