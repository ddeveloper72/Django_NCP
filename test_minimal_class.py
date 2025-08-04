"""
Minimal test of PatientSearchResult class definition
"""

from typing import Dict
from dataclasses import dataclass


@dataclass
class PatientSearchResult:
    """Result of patient search"""

    file_path: str
    country_code: str
    confidence_score: float
    patient_data: Dict
    cda_content: str


# Test if the class works
print("Testing PatientSearchResult class...")
test_obj = PatientSearchResult(
    file_path="test",
    country_code="GB",
    confidence_score=0.9,
    patient_data={"test": "data"},
    cda_content="<test/>",
)
print(f"✓ Success: {test_obj.file_path}")
print(f"Class is available: {'PatientSearchResult' in dir()}")
