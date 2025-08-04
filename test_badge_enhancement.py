#!/usr/bin/env python3
"""Test badge enhancement in PSTableRenderer"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eu_ncp_server.settings")
django.setup()

from patient_data.services.ps_table_renderer import PSTableRenderer


def test_badge_enhancement():
    """Test if badges are being added to original table cells"""
    print("=== TESTING BADGE ENHANCEMENT ===")

    renderer = PSTableRenderer()

    # Test cases
    test_cases = [
        "Metoprolol",
        "Allergie médicamenteuse",
        "ténofovir disoproxil fumarate",
        "Pénicilline",
        "Regular text without medical terms",
    ]

    for test_cell in test_cases:
        print(f"\nTesting: '{test_cell}'")
        enhanced = renderer._enhance_cell_with_badges(
            test_cell, "allergies", 1, ["Type", "Agent", "Reaction"]
        )
        print(f"Original: {test_cell}")
        print(f"Enhanced: {enhanced}")
        print(f"Has badge: {'code-system-badge' in enhanced}")
        print(f"Different: {enhanced != test_cell}")


if __name__ == "__main__":
    test_badge_enhancement()
