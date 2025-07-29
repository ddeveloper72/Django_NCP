#!/usr/bin/env python3
"""
MVC (Master Value Set Catalogue) Analysis Script
Analyzes the EU Central Terminology Server MVC Excel file
"""

import pandas as pd
import sys
import os
from pathlib import Path


def analyze_mvc_file(file_path):
    """Analyze the MVC Excel file structure and content"""
    try:
        print(f"Analyzing MVC file: {file_path}")
        print("=" * 60)

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"ERROR: File not found: {file_path}")
            return

        # Read Excel file
        xl_file = pd.ExcelFile(file_path)
        print(f"Total sheets: {len(xl_file.sheet_names)}")
        print(f"Sheet names: {xl_file.sheet_names}")
        print()

        # Analyze each sheet
        for i, sheet_name in enumerate(xl_file.sheet_names):
            print(f"Sheet {i+1}: {sheet_name}")
            print("-" * 40)

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"Shape: {df.shape} (rows x columns)")
                print(f"Columns: {list(df.columns)}")

                # Show sample data
                if len(df) > 0:
                    print("\nSample data (first 2 rows):")
                    for idx, row in df.head(2).iterrows():
                        print(f"  Row {idx}: {dict(row)}")

                # Look for key columns that indicate value sets
                key_columns = [
                    "oid",
                    "name",
                    "description",
                    "code",
                    "display",
                    "system",
                ]
                found_keys = [
                    col
                    for col in key_columns
                    if col.lower() in [c.lower() for c in df.columns]
                ]
                if found_keys:
                    print(f"\nKey terminology columns found: {found_keys}")

                print()

            except Exception as e:
                print(f"Error reading sheet '{sheet_name}': {e}")
                print()

        # Try to identify the main value sets sheet
        print("Identifying main value sets...")
        print("-" * 40)

        for sheet_name in xl_file.sheet_names:
            if any(
                keyword in sheet_name.lower()
                for keyword in ["value", "set", "mvc", "catalogue"]
            ):
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    print(f"Potential main sheet: {sheet_name}")
                    print(f"  Contains {len(df)} entries")

                    # Look for OID patterns
                    for col in df.columns:
                        if "oid" in col.lower():
                            sample_oids = df[col].dropna().head(3).tolist()
                            print(f"  OID column '{col}' samples: {sample_oids}")

                    # Look for name/title patterns
                    for col in df.columns:
                        if any(
                            word in col.lower()
                            for word in ["name", "title", "description"]
                        ):
                            sample_names = df[col].dropna().head(3).tolist()
                            print(f"  Name column '{col}' samples: {sample_names}")

                    print()
                except Exception as e:
                    print(f"Error analyzing sheet '{sheet_name}': {e}")

    except Exception as e:
        print(f"ERROR analyzing file: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Update this path to point to your MVC file
    mvc_file = r"path/to/your/MVC_9.0.0.xlsx"
    analyze_mvc_file(mvc_file)
