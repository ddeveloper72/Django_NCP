"""
Experimental CDA to FHIR conversion service using Greek xShare API

WARNING: This is experimental and may add synthetic data not present in the original CDA.
Use with caution and always compare with original CDA content.
"""

import requests
import logging
import json
import base64
from typing import Dict, Any, Optional, Tuple
from requests.auth import HTTPBasicAuth
from django.conf import settings

logger = logging.getLogger(__name__)


class CDAToFHIRService:
    """
    Experimental service to convert CDA documents to FHIR bundles using the Greek xShare API.

    ⚠️ WARNING: This service may add synthetic data not present in the original CDA
    to create proper FHIR resource relationships. Always validate against original CDA.
    """

    def __init__(self):
        self.api_url = "https://dev.ehealthpass.gr/xshare/cda2fhir/transform"
        self.username = "xshareuser"
        self.password = "sBXS3XnqGVhWyVGTWoNvX4W4C7JXia"
        self.timeout = 30  # seconds

    def convert_cda_to_fhir(self, cda_file_path: str) -> Dict[str, Any]:
        """
        Convert a CDA document to FHIR bundle using the xShare API.

        Args:
            cda_file_path: Path to the CDA XML file

        Returns:
            Dict containing:
            - success: bool
            - fhir_bundle: dict (FHIR Bundle JSON) if successful
            - error: str if failed
            - warnings: list of warnings about potential synthetic data
            - conversion_metadata: dict with conversion details
        """
        try:
            # Read CDA file
            with open(cda_file_path, "r", encoding="utf-8") as file:
                cda_content = file.read()

            logger.info(f"Converting CDA file to FHIR: {cda_file_path}")

            # Prepare request
            files = {"cda": ("document.xml", cda_content, "application/xml")}

            auth = HTTPBasicAuth(self.username, self.password)

            # Make API request
            response = requests.post(
                self.api_url, files=files, auth=auth, timeout=self.timeout
            )

            # Check response
            if response.status_code == 200:
                try:
                    fhir_bundle = response.json()

                    # Analyze the FHIR bundle for potential synthetic data
                    analysis_result = self._analyze_fhir_bundle(
                        fhir_bundle, cda_content
                    )

                    return {
                        "success": True,
                        "fhir_bundle": fhir_bundle,
                        "warnings": analysis_result["warnings"],
                        "conversion_metadata": analysis_result["metadata"],
                        "original_cda_size": len(cda_content),
                        "fhir_bundle_size": len(json.dumps(fhir_bundle)),
                    }

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse FHIR response as JSON: {e}")
                    return {
                        "success": False,
                        "error": f"Invalid JSON response from conversion service: {str(e)}",
                        "raw_response": response.text[
                            :1000
                        ],  # First 1000 chars for debugging
                    }

            else:
                logger.error(
                    f"CDA to FHIR conversion failed: {response.status_code} - {response.text}"
                )
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code} - {response.reason}",
                    "details": response.text[:500] if response.text else None,
                }

        except FileNotFoundError:
            error_msg = f"CDA file not found: {cda_file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during CDA to FHIR conversion: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error during CDA to FHIR conversion: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}

    def _analyze_fhir_bundle(
        self, fhir_bundle: Dict[str, Any], original_cda: str
    ) -> Dict[str, Any]:
        """
        Analyze the FHIR bundle to identify potential synthetic data additions.

        Args:
            fhir_bundle: The converted FHIR bundle
            original_cda: The original CDA content

        Returns:
            Dict with warnings and metadata about the conversion
        """
        warnings = []
        metadata = {
            "resource_count": 0,
            "resource_types": {},
            "has_references": False,
            "bundle_type": fhir_bundle.get("resourceType", "Unknown"),
        }

        try:
            # Count resources and types
            if "entry" in fhir_bundle:
                metadata["resource_count"] = len(fhir_bundle["entry"])

                for entry in fhir_bundle["entry"]:
                    if "resource" in entry:
                        resource_type = entry["resource"].get("resourceType", "Unknown")
                        metadata["resource_types"][resource_type] = (
                            metadata["resource_types"].get(resource_type, 0) + 1
                        )

                        # Check for references (potential synthetic relationships)
                        if self._has_references(entry["resource"]):
                            metadata["has_references"] = True

            # Generate warnings based on analysis
            if metadata["has_references"]:
                warnings.append(
                    "⚠️ FHIR bundle contains resource references that may be synthetic - "
                    "not all relationships may exist in the original CDA"
                )

            if metadata["resource_count"] > 10:
                warnings.append(
                    f"⚠️ Large number of FHIR resources ({metadata['resource_count']}) generated - "
                    "some may be synthetic to meet FHIR requirements"
                )

            # Check for specific synthetic indicators
            resource_types = list(metadata["resource_types"].keys())
            synthetic_indicators = ["Organization", "Practitioner", "Location"]
            found_indicators = [
                rt for rt in synthetic_indicators if rt in resource_types
            ]

            if found_indicators:
                warnings.append(
                    f"⚠️ Resources typically synthetic in CDA conversion found: {', '.join(found_indicators)} - "
                    "verify these exist in original CDA"
                )

            # General warning
            warnings.insert(
                0,
                "🔬 EXPERIMENTAL: This FHIR conversion may contain synthetic data not present in the original CDA. "
                "Always cross-reference with the original document.",
            )

        except Exception as e:
            logger.error(f"Error analyzing FHIR bundle: {e}")
            warnings.append(f"⚠️ Could not fully analyze FHIR bundle: {str(e)}")

        return {"warnings": warnings, "metadata": metadata}

    def _has_references(self, resource: Dict[str, Any]) -> bool:
        """Check if a FHIR resource contains references to other resources."""

        def check_for_references(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "reference" and isinstance(value, str):
                        return True
                    if isinstance(value, (dict, list)):
                        if check_for_references(value):
                            return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_for_references(item):
                        return True
            return False

        return check_for_references(resource)

    def extract_clinical_sections(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract clinical sections from the FHIR bundle for display.

        Args:
            fhir_bundle: The FHIR bundle

        Returns:
            Dict with organized clinical data sections
        """
        sections = {
            "patient": None,
            "allergies": [],
            "medications": [],
            "conditions": [],
            "procedures": [],
            "observations": [],
            "immunizations": [],
            "encounters": [],
            "organizations": [],
            "practitioners": [],
        }

        try:
            if "entry" not in fhir_bundle:
                return sections

            for entry in fhir_bundle["entry"]:
                if "resource" not in entry:
                    continue

                resource = entry["resource"]
                resource_type = resource.get("resourceType", "")

                if resource_type == "Patient":
                    sections["patient"] = resource
                elif resource_type == "AllergyIntolerance":
                    sections["allergies"].append(resource)
                elif resource_type in [
                    "Medication",
                    "MedicationStatement",
                    "MedicationRequest",
                ]:
                    sections["medications"].append(resource)
                elif resource_type == "Condition":
                    sections["conditions"].append(resource)
                elif resource_type == "Procedure":
                    sections["procedures"].append(resource)
                elif resource_type == "Observation":
                    sections["observations"].append(resource)
                elif resource_type == "Immunization":
                    sections["immunizations"].append(resource)
                elif resource_type == "Encounter":
                    sections["encounters"].append(resource)
                elif resource_type == "Organization":
                    sections["organizations"].append(resource)
                elif resource_type == "Practitioner":
                    sections["practitioners"].append(resource)

        except Exception as e:
            logger.error(f"Error extracting clinical sections from FHIR bundle: {e}")

        return sections
