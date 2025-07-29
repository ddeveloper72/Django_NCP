"""
Simple MVC File Reader and Analyzer
Processes EU Central Terminology Server MVC Excel files
"""

import pandas as pd
import os
import sys
from datetime import datetime


def analyze_mvc_file(file_path):
    """Analyze MVC Excel file structure and content"""

    print(f"MVC File Analysis: {file_path}")
    print("=" * 60)

    if not os.path.exists(file_path):
        print(f"ERROR: File not found - {file_path}")
        print("\nPlease ensure the MVC_9.0.0.xlsx file is in the correct location.")
        return

    try:
        # Read Excel file
        xl_file = pd.ExcelFile(file_path)
        print(f"File successfully opened")
        print(f"Number of sheets: {len(xl_file.sheet_names)}")
        print(f"Sheet names: {xl_file.sheet_names}")
        print()

        # Analyze each sheet
        for sheet_name in xl_file.sheet_names:
            print(f"Sheet: {sheet_name}")
            print("-" * 30)

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"  Rows: {len(df)}")
                print(f"  Columns: {len(df.columns)}")
                print(f"  Column names: {list(df.columns)}")

                # Show first few rows
                if len(df) > 0:
                    print("  Sample data (first 2 rows):")
                    for i, (idx, row) in enumerate(df.head(2).iterrows()):
                        print(f"    Row {i+1}: {dict(row)}")

                # Look for terminology-related columns
                terminology_indicators = [
                    "oid",
                    "code",
                    "display",
                    "system",
                    "name",
                    "description",
                ]
                found_indicators = []

                for col in df.columns:
                    for indicator in terminology_indicators:
                        if indicator.lower() in col.lower():
                            found_indicators.append(col)
                            break

                if found_indicators:
                    print(f"  Terminology columns: {found_indicators}")

                print()

            except Exception as e:
                print(f"  Error reading sheet: {e}")
                print()

        # Summary
        print("Analysis Summary:")
        print("-" * 30)
        print("This appears to be a Master Value Set Catalogue (MVC) file containing:")
        print("- Value set definitions with OIDs")
        print("- Clinical terminology concepts")
        print("- Multi-language translations")
        print("- Concept mappings for cross-border healthcare")
        print()
        print("Next steps:")
        print(
            "1. Use Django management command: python manage.py import_mvc <file_path>"
        )
        print("2. Sync with CTS: python manage.py sync_cts --environment training")
        print("3. Integrate with clinical document translation")

    except Exception as e:
        print(f"ERROR: Failed to read file - {e}")
        print()
        print("Possible issues:")
        print("- File is corrupted or not a valid Excel file")
        print("- File is currently open in Excel")
        print("- Insufficient permissions to read the file")
        print("- Missing required Python packages (pandas, openpyxl)")


def main():
    """Main function to run MVC analysis"""

    # Default MVC file location - now in the project directory
    default_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "MVC_9.0.0.xlsx"
    )

    # Check if file path provided as argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path

    print("EU Central Terminology Server - MVC File Analyzer")
    print("=" * 60)
    print(f"Target file: {file_path}")
    print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    analyze_mvc_file(file_path)


if __name__ == "__main__":
    main()
