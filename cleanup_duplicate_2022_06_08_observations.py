"""
Script to delete duplicate/incorrect observations for 2022-06-08
IMPORTANT: Review carefully before running!
"""

# Observations to delete (v1 duplicates with conflicting outcomes on same date)
observations_to_delete = [
    {
        'id': 'e2fb0492-a18d-4616-a9a1-1d9d5ea1fedd',
        'version': 1,
        'date': '2022-06-08T10:49:00Z',
        'outcome': 'Termination of pregnancy',
        'code': '57797005',
        'reason': 'Duplicate v1 - conflicts with Livebirth on same date'
    },
    {
        'id': '77498f9b-41a4-4b12-b060-14874bf8261a',
        'version': 1,
        'date': '2022-06-08T10:49:00Z',
        'outcome': 'Livebirth',
        'code': '281050002',
        'reason': 'Duplicate v1 - conflicts with Termination on same date'
    }
]

# Observations to KEEP (v2 corrected versions)
observations_to_keep = [
    {
        'id': '2e66bd08-fe2d-40d8-8ca9-69eb737b6ab1',
        'version': 2,
        'date': '2022-06-08T10:49:00Z',
        'outcome': 'Termination of pregnancy',
        'code': '57797005',
        'reason': 'Corrected v2 version'
    },
    {
        'id': '1b800d37-00d1-466d-8430-82456b7e749a',
        'version': 2,
        'date': '2022-06-08T10:49:00Z',
        'outcome': 'Livebirth',
        'code': '281050002',
        'reason': 'Corrected v2 version'
    }
]

print("=" * 80)
print("AZURE FHIR DATA CLEANUP PLAN - 2022-06-08 Duplicate Observations")
print("=" * 80)

print("\n[PROBLEM]")
print("Date 2022-06-08 has BOTH Livebirth AND Termination observations.")
print("This is medically impossible and indicates duplicate/incorrect data.")

print("\n[OBSERVATIONS TO DELETE]")
for obs in observations_to_delete:
    print(f"\n  ID: {obs['id']}")
    print(f"  Version: {obs['version']}")
    print(f"  Date: {obs['date']}")
    print(f"  Outcome: {obs['outcome']} (code: {obs['code']})")
    print(f"  Reason: {obs['reason']}")

print("\n[OBSERVATIONS TO KEEP]")
for obs in observations_to_keep:
    print(f"\n  ID: {obs['id']}")
    print(f"  Version: {obs['version']}")
    print(f"  Date: {obs['date']}")
    print(f"  Outcome: {obs['outcome']} (code: {obs['code']})")
    print(f"  Reason: {obs['reason']}")

print("\n" + "=" * 80)
print("DECISION REQUIRED")
print("=" * 80)

print("\nYou need to decide which observation is CORRECT for 2022-06-08:")
print("\nOption A: Keep ONLY Termination (delete Livebirth observations)")
print("  - Delete: e2fb0492, 77498f9b, 1b800d37")
print("  - Keep: 2e66bd08 (Termination v2)")

print("\nOption B: Keep ONLY Livebirth (delete Termination observations)")
print("  - Delete: e2fb0492, 77498f9b, 2e66bd08")
print("  - Keep: 1b800d37 (Livebirth v2)")

print("\n⚠️  WARNING: You CANNOT have both outcomes on the same date!")
print("           This creates ambiguous/incorrect medical records.")

print("\n[RECOMMENDED NEXT STEPS]")
print("1. Consult the CDA source document to determine correct outcome for 2022-06-08")
print("2. Delete the incorrect observations via Azure Portal or API")
print("3. Clear Django cache and sessions")
print("4. Restart Django server")
print("5. Re-test patient lookup")

# To actually delete observations, use Azure FHIR API:
print("\n[AZURE FHIR DELETE COMMANDS]")
print("\nTo delete observations via curl (replace with your access token):")
for obs in observations_to_delete:
    print(f"\ncurl -X DELETE \\")
    print(f"  'https://healtthdata-dev-fhir-service.fhir.azurehealthcareapis.com/Observation/{obs['id']}' \\")
    print(f"  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'")
