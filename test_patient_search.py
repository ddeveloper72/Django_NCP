"""
Test script to simulate patient search form submission
"""

import requests
from django.test import Client
from django.urls import reverse
import os
import sys
import django

# Setup Django environment
sys.path.append("C:/Users/Duncan/VS_Code_Projects/django_ncp")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from django.contrib.auth.models import User
from patient_data.models import MemberState


def test_patient_search():
    print("=== Testing Patient Search Form Submission ===")

    # Create a test client
    client = Client()

    # Login (assuming we have a user)
    try:
        user = User.objects.first()
        if user:
            client.force_login(user)
            print(f"Logged in as: {user.username}")
        else:
            print("No user found - creating test user")
            user = User.objects.create_user("testuser", "test@example.com", "testpass")
            client.force_login(user)
    except Exception as e:
        print(f"Error with user setup: {e}")
        return

    # Get member states
    ireland = MemberState.objects.filter(country_code="IE").first()
    portugal = MemberState.objects.filter(country_code="PT").first()

    print(f"Ireland member state: {ireland}")
    print(f"Portugal member state: {portugal}")

    # Test data
    test_cases = [
        {
            "member_state": ireland,
            "patient_id": "2-1234-W8",
            "birth_date": "1886/06/29",
        },
        {
            "member_state": portugal,
            "patient_id": "2-1234-W8",
            "birth_date": "1886/06/29",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        if not test_case["member_state"]:
            print(f"Test case {i}: Skipping - member state not found")
            continue

        print(f"\nTest case {i}: {test_case['member_state'].country_name}")

        # Prepare form data
        form_data = {
            "national_person_id": test_case["patient_id"],
            "birthdate": test_case["birth_date"],
            "member_state_id": test_case["member_state"].id,
        }

        print(f"Form data: {form_data}")

        # Submit form
        try:
            response = client.post(reverse("patient_data:patient_search"), form_data)
            print(f"Response status: {response.status_code}")

            if response.status_code == 302:
                print(f"Redirect to: {response.url}")
            elif response.status_code == 200:
                # Check if there are error messages in the context
                if hasattr(response, "context") and response.context:
                    messages = list(response.context.get("messages", []))
                    if messages:
                        print("Messages:")
                        for msg in messages:
                            print(f"  - {msg}")
                    else:
                        print("No messages in context")
                else:
                    print("No context available")

        except Exception as e:
            print(f"Error during form submission: {e}")


if __name__ == "__main__":
    test_patient_search()
