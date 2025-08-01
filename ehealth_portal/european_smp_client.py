"""
European SMP/SML Client Service
Integrates with European Commission's SMP/SML infrastructure for eHealth services
Based on OpenNCP configuration from ehealth-2 project
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EuropeanSMPClient:
    """Client for European Commission SMP/SML services"""

    # Configuration from OpenNCP ehealth-2 project
    SML_DOMAIN = "ehealth-trn.acc.edelivery.tech.ec.europa.eu"
    SMP_ADMIN_URL = "https://smp-ehealth-trn-cert-auth.acc.edelivery.tech.ec.europa.eu"

    # European countries supported
    EU_COUNTRIES = [
        "be",
        "bg",
        "cz",
        "dk",
        "de",
        "ee",
        "ie",
        "gr",
        "es",
        "fr",
        "hr",
        "it",
        "cy",
        "lv",
        "lt",
        "lu",
        "hu",
        "mt",
        "nl",
        "at",
        "pl",
        "pt",
        "ro",
        "si",
        "sk",
        "fi",
        "se",
        "eu",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = True  # Enable SSL verification
        self.session.timeout = 30

    def get_country_smp_url(self, country_code):
        """
        Get SMP URL for a specific country from SML
        """
        try:
            country_code = country_code.lower()
            if country_code not in self.EU_COUNTRIES:
                logger.warning(f"Country {country_code} not in supported EU countries")
                return None

            # Construct SMP URL based on SML domain pattern
            smp_url = f"https://smp-{country_code}.{self.SML_DOMAIN}"

            # Verify the SMP endpoint is accessible
            response = self.session.head(smp_url, timeout=10)
            if response.status_code == 200:
                return smp_url
            else:
                # Fallback to training environment pattern
                fallback_url = f"https://smp-ehealth-trn-{country_code}.acc.edelivery.tech.ec.europa.eu"
                return fallback_url

        except Exception as e:
            logger.error(f"Error getting SMP URL for {country_code}: {e}")
            return None

    def fetch_participant_list(self, country_code):
        """
        Fetch list of participants from country's SMP
        """
        try:
            smp_url = self.get_country_smp_url(country_code)
            if not smp_url:
                return []

            # SMP API endpoint for participant list
            participants_url = urljoin(smp_url, "/participants")

            response = self.session.get(participants_url)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            participants = []

            # Extract participant identifiers
            for participant in root.findall(".//participant"):
                participant_id = participant.get("id")
                if participant_id:
                    participants.append(participant_id)

            return participants

        except Exception as e:
            logger.error(f"Error fetching participants from {country_code}: {e}")
            return []

    def fetch_service_metadata(self, country_code, participant_id):
        """
        Fetch service metadata for a specific participant
        """
        try:
            smp_url = self.get_country_smp_url(country_code)
            if not smp_url:
                return None

            # SMP API endpoint for service metadata
            metadata_url = urljoin(smp_url, f"/participants/{participant_id}/services")

            response = self.session.get(metadata_url)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            services = []

            # Extract service information
            for service in root.findall(".//service"):
                service_info = {"service_id": service.get("id"), "endpoints": []}

                # Extract endpoints
                for endpoint in service.findall(".//endpoint"):
                    endpoint_info = {
                        "transport_profile": endpoint.get("transportProfile"),
                        "endpoint_url": endpoint.text,
                        "certificate": endpoint.get("certificate"),
                    }
                    service_info["endpoints"].append(endpoint_info)

                services.append(service_info)

            return services

        except Exception as e:
            logger.error(
                f"Error fetching service metadata for {participant_id} in {country_code}: {e}"
            )
            return None

    def fetch_international_search_mask(self, country_code):
        """
        Fetch International Search Mask (ISM) configuration from country's SMP
        This is the key function for dynamic form generation
        """
        try:
            smp_url = self.get_country_smp_url(country_code)
            if not smp_url:
                return self._get_fallback_ism(country_code)

            # Look for ISM service in SMP
            ism_url = urljoin(smp_url, f"/ism/{country_code}")

            response = self.session.get(ism_url)
            if response.status_code == 404:
                # Try alternative ISM endpoint
                ism_url = urljoin(smp_url, f"/services/ism/{country_code}")
                response = self.session.get(ism_url)

            if response.status_code == 200:
                return self._parse_ism_response(response.content, country_code)
            else:
                logger.warning(f"ISM not found for {country_code}, using fallback")
                return self._get_fallback_ism(country_code)

        except Exception as e:
            logger.error(f"Error fetching ISM for {country_code}: {e}")
            return self._get_fallback_ism(country_code)

    def _parse_ism_response(self, xml_content, country_code):
        """
        Parse ISM XML response into Django model format
        """
        try:
            root = ET.fromstring(xml_content)

            ism_config = {
                "country_code": country_code.upper(),
                "version": root.get("version", "1.0"),
                "effective_date": root.get("effectiveDate"),
                "fields": [],
            }

            # Parse search fields
            for field in root.findall(".//searchField"):
                field_config = {
                    "name": field.get("name"),
                    "label": field.get("label"),
                    "field_type": field.get("type", "text"),
                    "required": field.get("required", "false").lower() == "true",
                    "max_length": int(field.get("maxLength", 255)),
                    "validation_pattern": field.get("pattern"),
                    "description": field.get("description", ""),
                    "order": int(field.get("order", 0)),
                }
                ism_config["fields"].append(field_config)

            return ism_config

        except Exception as e:
            logger.error(f"Error parsing ISM response for {country_code}: {e}")
            return self._get_fallback_ism(country_code)

    def _get_fallback_ism(self, country_code):
        """
        Fallback ISM configuration when SMP is not available
        """
        country_code = country_code.upper()

        # Basic EU-standard ISM fields
        base_fields = [
            {
                "name": "patient_id",
                "label": "Patient ID",
                "field_type": "text",
                "required": True,
                "max_length": 50,
                "order": 1,
            },
            {
                "name": "first_name",
                "label": "First Name",
                "field_type": "text",
                "required": True,
                "max_length": 100,
                "order": 2,
            },
            {
                "name": "last_name",
                "label": "Last Name",
                "field_type": "text",
                "required": True,
                "max_length": 100,
                "order": 3,
            },
            {
                "name": "date_of_birth",
                "label": "Date of Birth",
                "field_type": "date",
                "required": True,
                "order": 4,
            },
        ]

        # Country-specific extensions based on OpenNCP patterns
        country_extensions = {
            "BE": [
                {
                    "name": "national_registry_number",
                    "label": "National Registry Number",
                    "field_type": "text",
                    "required": True,
                    "max_length": 11,
                    "order": 5,
                }
            ],
            "AT": [
                {
                    "name": "social_security_number",
                    "label": "Social Security Number",
                    "field_type": "text",
                    "required": True,
                    "max_length": 10,
                    "order": 5,
                },
                {
                    "name": "insurance_number",
                    "label": "Insurance Number",
                    "field_type": "text",
                    "required": False,
                    "max_length": 20,
                    "order": 6,
                },
            ],
            "HU": [
                {
                    "name": "taj_number",
                    "label": "TAJ Number",
                    "field_type": "text",
                    "required": True,
                    "max_length": 9,
                    "order": 5,
                },
                {
                    "name": "mothers_maiden_name",
                    "label": "Mother's Maiden Name",
                    "field_type": "text",
                    "required": False,
                    "max_length": 100,
                    "order": 6,
                },
            ],
            "IE": [
                {
                    "name": "pps_number",
                    "label": "PPS Number",
                    "field_type": "text",
                    "required": True,
                    "max_length": 8,
                    "order": 5,
                },
                {
                    "name": "medical_card_number",
                    "label": "Medical Card Number",
                    "field_type": "text",
                    "required": False,
                    "max_length": 20,
                    "order": 6,
                },
            ],
            "EU": [
                {
                    "name": "eu_patient_id",
                    "label": "EU Patient ID",
                    "field_type": "text",
                    "required": True,
                    "max_length": 50,
                    "order": 5,
                }
            ],
        }

        fields = base_fields.copy()
        if country_code in country_extensions:
            fields.extend(country_extensions[country_code])

        return {
            "country_code": country_code,
            "version": "1.0",
            "effective_date": "2025-01-01",
            "source": "fallback",
            "fields": fields,
        }

    def test_connectivity(self):
        """
        Test connectivity to European SMP infrastructure
        """
        results = {}

        # Test main SMP admin URL
        try:
            response = self.session.head(self.SMP_ADMIN_URL, timeout=10)
            results["smp_admin"] = {
                "url": self.SMP_ADMIN_URL,
                "status": response.status_code,
                "accessible": response.status_code == 200,
            }
        except Exception as e:
            results["smp_admin"] = {
                "url": self.SMP_ADMIN_URL,
                "status": "error",
                "accessible": False,
                "error": str(e),
            }

        # Test a few country SMPs
        test_countries = ["ie", "be", "at", "eu"]
        results["country_smps"] = {}

        for country in test_countries:
            try:
                smp_url = self.get_country_smp_url(country)
                if smp_url:
                    response = self.session.head(smp_url, timeout=10)
                    results["country_smps"][country] = {
                        "url": smp_url,
                        "status": response.status_code,
                        "accessible": response.status_code
                        in [200, 404],  # 404 is OK for SMP root
                    }
                else:
                    results["country_smps"][country] = {
                        "url": None,
                        "accessible": False,
                        "error": "Could not determine SMP URL",
                    }
            except Exception as e:
                results["country_smps"][country] = {
                    "url": smp_url if "smp_url" in locals() else None,
                    "accessible": False,
                    "error": str(e),
                }

        return results


# Singleton instance
european_smp_client = EuropeanSMPClient()
