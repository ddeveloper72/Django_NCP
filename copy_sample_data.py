"""
Script to copy sample patient data from OpenNCP integration folder
and create the necessary data structures for patient lookup
"""

import os
import shutil
import json
from pathlib import Path

# Paths
SOURCE_DIR = Path(
    "C:/Users/Duncan/VS_Code_Projects/ehealth-2/openncp-docker/openncp-configuration/integration"
)
TARGET_DIR = Path(
    "C:/Users/Duncan/VS_Code_Projects/django_ncp/patient_data/sample_data/integration"
)


def copy_sample_data():
    """Copy sample patient data files"""
    print("Copying sample patient data from OpenNCP integration folder...")

    if SOURCE_DIR.exists():
        # Ensure target directory exists
        TARGET_DIR.mkdir(parents=True, exist_ok=True)

        # Copy all contents
        for item in SOURCE_DIR.iterdir():
            if item.is_dir():
                target_path = TARGET_DIR / item.name
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(item, target_path)
                print(f"Copied OID directory: {item.name}")
            elif item.is_file():
                shutil.copy2(item, TARGET_DIR)
                print(f"Copied file: {item.name}")

        print("\nSample data copied successfully!")

        # List contents
        print("\nContents of integration folder:")
        for item in TARGET_DIR.iterdir():
            if item.is_dir():
                print(f"  📁 {item.name}/ (OID Directory)")
                # List patient files in this OID
                for patient_file in item.iterdir():
                    if patient_file.is_file():
                        print(f"    📄 {patient_file.name}")
            else:
                print(f"  📄 {item.name}")

        return True
    else:
        print(f"Source directory not found: {SOURCE_DIR}")
        print("Please check the path and try again.")
        return False


def create_oid_mapping():
    """Create OID to member state mapping based on discovered directories"""
    oid_mapping = {}

    if TARGET_DIR.exists():
        for oid_dir in TARGET_DIR.iterdir():
            if oid_dir.is_dir() and oid_dir.name.replace(".", "").isdigit():
                # This is an OID directory
                oid = oid_dir.name

                # Map common OIDs to countries (you can extend this)
                oid_to_country = {
                    "2.16.17.710.804.1000.990.1": "Portugal",
                    "2.16.17.710.804.1000.990.2": "Greece",
                    "1.2.276.0.76.3.1.315.3.2.1.1": "Germany",
                    "2.16.840.1.113883.2.16.1.8": "Croatia",
                    # Add more mappings as needed
                }

                country_name = oid_to_country.get(oid, f"Country_{oid}")

                # Count patient files
                patient_files = [f for f in oid_dir.iterdir() if f.is_file()]

                oid_mapping[oid] = {
                    "country_name": country_name,
                    "patient_count": len(patient_files),
                    "patient_files": [f.name for f in patient_files],
                }

                print(
                    f"Mapped OID {oid} to {country_name} with {len(patient_files)} patients"
                )

    # Save mapping to JSON file
    mapping_file = TARGET_DIR / "oid_mapping.json"
    with open(mapping_file, "w") as f:
        json.dump(oid_mapping, f, indent=2)

    print(f"\nOID mapping saved to: {mapping_file}")
    return oid_mapping


if __name__ == "__main__":
    success = copy_sample_data()
    if success:
        create_oid_mapping()
