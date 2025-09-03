"""
Enhanced MVC Parser for EU Central Terminology Server Format
Handles the specific structure of MVC 9.0.0 Excel files
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple


class EUMVCParser:
    """Parser for EU Central Terminology Server MVC files"""

    def __init__(self):
        self.value_set_info = {}
        self.concepts = []

    def parse_mvc_sheet(self, file_path: str, sheet_name: str) -> Dict:
        """Parse a specific MVC sheet and extract value set information"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Extract value set metadata from header rows
            value_set_info = self._extract_value_set_info(df, sheet_name)

            # Extract concepts from data rows
            concepts = self._extract_concepts(df, value_set_info)

            return {
                "value_set_info": value_set_info,
                "concepts": concepts,
                "total_concepts": len(concepts),
                "sheet_name": sheet_name,
            }

        except Exception as e:
            return {"error": str(e), "sheet_name": sheet_name}

    def _extract_value_set_info(self, df: pd.DataFrame, sheet_name: str) -> Dict:
        """Extract value set metadata from the first few rows"""
        info = {
            "name": sheet_name,
            "oid": None,
            "canonical_url": None,
            "description": None,
            "version": "9.0.0",  # Default from MVC 9.0.0
        }

        # Look for OID in column headers (usually second column)
        if len(df.columns) > 1:
            potential_oid = df.columns[1]
            if self._is_oid(potential_oid):
                info["oid"] = potential_oid

        # Look for metadata in first few rows
        for idx in range(min(10, len(df))):
            row = df.iloc[idx]

            # Check for value set name
            if pd.notna(row.iloc[0]) and "Value Set Name" in str(row.iloc[0]):
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    info["name"] = str(row.iloc[1])

            # Check for canonical URL
            if pd.notna(row.iloc[0]) and "Canonical URL" in str(row.iloc[0]):
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    info["canonical_url"] = str(row.iloc[1])

        return info

    def _extract_concepts(self, df: pd.DataFrame, value_set_info: Dict) -> List[Dict]:
        """Extract concepts from the data portion of the sheet"""
        concepts = []

        # Find where the actual data starts (usually after metadata rows)
        data_start_row = self._find_data_start(df)

        if data_start_row is None:
            return concepts

        # Extract concepts from data rows
        for idx in range(data_start_row, len(df)):
            row = df.iloc[idx]
            concept = self._parse_concept_row(row, df.columns)

            if concept:
                concepts.append(concept)

        return concepts

    def _find_data_start(self, df: pd.DataFrame) -> Optional[int]:
        """Find the row where actual concept data starts"""
        # Based on the MVC structure, look for the column headers row
        # This is typically after the metadata section and an empty row

        for idx in range(len(df)):
            row = df.iloc[idx]

            # Look for a row that contains column headers like "Code System ID", "Concept Code", etc.
            if len(row) >= 3:  # Should have multiple columns
                row_str = " ".join(
                    [str(cell) for cell in row if pd.notna(cell)]
                ).lower()

                # Check for typical column headers in MVC files
                header_indicators = [
                    "code system",
                    "concept code",
                    "description",
                    "language code",
                    "system id",
                    "code",
                    "display",
                ]

                if any(indicator in row_str for indicator in header_indicators):
                    # This is the header row, data starts on the next row
                    return idx + 1

        # Fallback: if no clear header found, assume data starts after row 8 (common in MVC files)
        if len(df) > 8:
            return 8

        return None

    def _looks_like_concept_row(self, row: pd.Series) -> bool:
        """Check if a row looks like it contains concept data"""
        non_null_count = row.notna().sum()

        # Must have at least 2 non-null values
        if non_null_count < 2:
            return False

        # Check if first column looks like a code
        first_col = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""

        # Skip obvious header rows
        if any(
            header_word in first_col.lower()
            for header_word in [
                "value set",
                "canonical",
                "version",
                "description",
                "code system id",
                "concept code",
            ]
        ):
            return False

        return True

        # Look for patterns that suggest this is concept data
        # Codes are often alphanumeric, sometimes with dots or dashes
        if re.match(r"^[A-Za-z0-9][A-Za-z0-9\.\-_]*$", first_col.strip()):
            return True

        return False

    def _parse_concept_row(self, row: pd.Series, columns: List[str]) -> Optional[Dict]:
        """Parse a single concept row based on MVC structure"""
        if not self._looks_like_concept_row(row):
            return None

        concept = {
            "code_system_id": None,
            "code_system_version": None,
            "concept_code": None,
            "description": None,
            "language_code_1": None,
            "language_code_2": None,
        }

        # Based on the screenshot structure:
        # Column A: Code System ID
        # Column B: Code System Version
        # Column C: Concept Code
        # Column D: Description
        # Column E: <language code 1>
        # Column F: <language code 2>

        try:
            if len(row) >= 1 and pd.notna(row.iloc[0]):
                concept["code_system_id"] = str(row.iloc[0]).strip()

            if len(row) >= 2 and pd.notna(row.iloc[1]):
                concept["code_system_version"] = str(row.iloc[1]).strip()

            if len(row) >= 3 and pd.notna(row.iloc[2]):
                concept["concept_code"] = str(row.iloc[2]).strip()

            if len(row) >= 4 and pd.notna(row.iloc[3]):
                concept["description"] = str(row.iloc[3]).strip()

            if len(row) >= 5 and pd.notna(row.iloc[4]):
                concept["language_code_1"] = str(row.iloc[4]).strip()

            if len(row) >= 6 and pd.notna(row.iloc[5]):
                concept["language_code_2"] = str(row.iloc[5]).strip()

            # Only return if we have essential data
            if concept["concept_code"] and (
                concept["description"] or concept["language_code_1"]
            ):
                return concept

        except Exception as e:
            # If parsing fails, fall back to simple extraction
            pass

        return None

    def _is_oid(self, value: str) -> bool:
        """Check if a string looks like an OID"""
        if not isinstance(value, str):
            return False

        # OID pattern: digits separated by dots
        return bool(re.match(r"^\d+(\.\d+)+$", value.strip()))

    def _looks_like_system_uri(self, value: str) -> bool:
        """Check if a string looks like a code system URI"""
        if not isinstance(value, str):
            return False

        # Common patterns for code system URIs
        uri_patterns = [
            r"^https?://",
            r"^urn:",
            r".*snomed.*",
            r".*loinc.*",
            r".*hl7\.org.*",
        ]

        value_lower = value.lower()
        return any(re.search(pattern, value_lower) for pattern in uri_patterns)


def demo_mvc_parsing():
    """Demonstrate MVC parsing with the actual file"""
    parser = EUMVCParser()

    print("EU MVC Parser Demonstration")
    print("=" * 50)

    # Test with a few different value set sheets
    test_sheets = [
        "eHDSICountry",
        "eHDSILanguage",
        "eHDSIAdministrativeGender",
        "eHDSIBloodGroup",
    ]

    for sheet_name in test_sheets:
        print(f"\nParsing sheet: {sheet_name}")
        print("-" * 30)

        try:
            result = parser.parse_mvc_sheet("MVC_9.0.0.xlsx", sheet_name)

            if "error" in result:
                print(f"Error: {result['error']}")
                continue

            vs_info = result["value_set_info"]
            concepts = result["concepts"]

            print(f"Value Set Name: {vs_info['name']}")
            print(f"OID: {vs_info['oid']}")
            print(f"Canonical URL: {vs_info['canonical_url']}")
            print(f"Total Concepts: {len(concepts)}")

            if concepts:
                print("\nSample concepts:")
                for i, concept in enumerate(concepts[:3]):
                    print(f"  {i+1}. Concept Code: {concept['concept_code']}")
                    print(f"     Description: {concept['description']}")
                    if concept["code_system_id"]:
                        print(f"     Code System: {concept['code_system_id']}")
                    if concept["language_code_1"]:
                        print(f"     Language 1: {concept['language_code_1']}")
                    print()

        except Exception as e:
            print(f"Error parsing {sheet_name}: {e}")


if __name__ == "__main__":
    demo_mvc_parsing()
