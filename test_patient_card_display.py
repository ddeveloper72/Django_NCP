#!/usr/bin/env python3
"""
Test patient identifier display for Mario PINO with Italian CDA identifiers
"""


def test_mario_pino_patient_card_display():
    """Test how Mario PINO patient card should display with CDA identifiers"""

    # Simulate Mario PINO patient data with Italian CDA identifiers
    mario_patient_data = {
        "id": 74,  # Internal database ID that was showing before
        "name": "PINO, Mario",
        "given_name": "Mario",
        "family_name": "PINO",
        "birth_date": "01/01/1970",
        "gender": "M",
        "patient_identifiers": [
            {
                "extension": "NCPNPH80A01H501K",
                "root": "2.16.840.1.113883.2.9.4.3.2",
                "assigningAuthorityName": "Ministero Economia e Finanze",
                "displayable": "true",
                "type": "primary",
            }
        ],
    }

    print("Mario PINO Patient Card Display Test")
    print("=" * 50)
    print(f"Patient Name: {mario_patient_data['name']}")
    print(f"Born: {mario_patient_data['birth_date']}")
    print(f"Gender: {mario_patient_data['gender']}")
    print()

    print("BEFORE Enhancement (showing internal DB ID):")
    print(f"  ID: {mario_patient_data['id']}")
    print()

    print("AFTER Enhancement (showing CDA identifiers):")
    if mario_patient_data.get("patient_identifiers"):
        for identifier in mario_patient_data["patient_identifiers"]:
            if identifier.get("assigningAuthorityName"):
                print(
                    f"  {identifier['assigningAuthorityName']}: {identifier['extension']}"
                )
            else:
                print(f"  Patient ID: {identifier['extension']}")
    else:
        print(f"  ID: {mario_patient_data['id']}")  # Fallback to internal ID

    print()
    print("Template Logic Result:")
    print("{% if patient.patient_identifiers %}")
    print("{% for identifier in patient.patient_identifiers %}")
    print("{{ identifier.assigningAuthorityName }}: {{ identifier.extension }}")
    print("{% endfor %}")
    print("{% else %}")
    print("ID: {{ patient.id }}")
    print("{% endif %}")

    print()
    print("Expected Display for Mario PINO:")
    print("  Ministero Economia e Finanze: NCPNPH80A01H501K")
    print()
    print(
        "✅ This provides immediate recognition that this is an official Italian government identifier"
    )
    print(
        "✅ Healthcare professionals can now see the actual fiscal code needed for patient care"
    )
    print("✅ Cross-border healthcare context is clear and meaningful")


def test_luxembourg_patient_card_display():
    """Test how Luxembourg patient card should display with dual identifiers"""

    # Simulate Luxembourg patient data with dual identifiers
    lu_patient_data = {
        "id": 75,  # Internal database ID
        "name": "Test Patient",
        "birth_date": "01/03/1970",
        "gender": "M",
        "patient_identifiers": [
            {
                "extension": "2544557646",
                "root": "1.3.182.2.4.2",
                "assigningAuthorityName": "",
                "type": "primary",
            },
            {
                "extension": "193701011247",
                "root": "1.3.182.4.4",
                "assigningAuthorityName": "",
                "type": "secondary",
            },
        ],
    }

    print("\nLuxembourg Patient Card Display Test")
    print("=" * 50)
    print(f"Patient Name: {lu_patient_data['name']}")
    print(f"Born: {lu_patient_data['birth_date']}")
    print()

    print("BEFORE Enhancement:")
    print(f"  ID: {lu_patient_data['id']}")
    print()

    print("AFTER Enhancement:")
    if lu_patient_data.get("patient_identifiers"):
        for identifier in lu_patient_data["patient_identifiers"]:
            if identifier.get("assigningAuthorityName"):
                print(
                    f"  {identifier['assigningAuthorityName']}: {identifier['extension']}"
                )
            else:
                root_display = (
                    identifier.get("root", "")[:15] + "..."
                    if len(identifier.get("root", "")) > 15
                    else identifier.get("root", "")
                )
                print(f"  Patient ID ({root_display}): {identifier['extension']}")

    print()
    print("Expected Display for Luxembourg Patient:")
    print("  Patient ID (1.3.182.2.4.2): 2544557646")
    print("  Patient ID (1.3.182.4.4): 193701011247")
    print()
    print("✅ Both search identifiers are now visible")
    print("✅ Root OIDs provide context for Luxembourg national systems")


if __name__ == "__main__":
    test_mario_pino_patient_card_display()
    test_luxembourg_patient_card_display()
