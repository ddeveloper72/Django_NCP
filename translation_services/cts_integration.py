"""
Central Terminology Server (CTS) Integration
Implements MVC (Master Value Set Catalogue) and MTC (Master Terminology Catalogue) synchronization
with the EU Central Terminology Server at webgate.training.ec.europa.eu
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class CTSAPIClient:
    """
    Client for Central Terminology Server (CTS) API integration
    Handles authentication, rate limiting, and API communication
    """

    def __init__(self, environment="training"):
        """
        Initialize CTS API client

        Args:
            environment: 'training', 'acceptance', or 'production'
        """
        self.environments = {
            "training": "https://webgate.training.ec.europa.eu/ehealth-term-portal/",
            "acceptance": "https://webgate.acceptance.ec.europa.eu/ehealth-term-portal/",
            "production": "https://webgate.ec.europa.eu/ehealth-term-portal/",
        }

        self.base_url = self.environments.get(
            environment, self.environments["training"]
        )
        self.session = self._create_session()
        self.country_code = getattr(settings, "CTS_COUNTRY_CODE", "IE")
        self.timeout = getattr(settings, "CTS_REQUEST_TIMEOUT", 30)

        # API endpoints
        self.endpoints = {
            "value_sets": "api/valuesets",
            "concepts": "api/concepts",
            "translations": "api/translations",
            "mappings": "api/mappings",
            "sync_status": "api/sync/status",
            "member_state_config": f"api/memberstate/{self.country_code}",
            "mvc_sync": "api/mvc/sync",
            "mtc_sync": "api/mtc/sync",
        }

    def _create_session(self):
        """Create HTTP session with retry strategy and proper headers"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Default headers
        session.headers.update(
            {
                "User-Agent": f"Django-NCP-Portal/{self.country_code}",
                "Accept": "application/json, application/xml",
                "Content-Type": "application/json",
            }
        )

        return session

    def get_value_sets(self, language="en", include_inactive=False) -> Dict[str, Any]:
        """
        Retrieve value sets from CTS

        Args:
            language: Language code (e.g., 'en', 'fr', 'de')
            include_inactive: Include inactive value sets

        Returns:
            Dictionary containing value sets data
        """
        try:
            params = {
                "language": language,
                "country": self.country_code,
                "includeInactive": str(include_inactive).lower(),
            }

            url = urljoin(self.base_url, self.endpoints["value_sets"])
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching value sets from CTS: {e}")
            return {"error": str(e), "value_sets": []}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CTS response: {e}")
            return {"error": "Invalid JSON response", "value_sets": []}

    def get_concept_mappings(
        self, source_code_system: str, target_code_system: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve concept mappings between terminology systems

        Args:
            source_code_system: Source terminology system OID
            target_code_system: Target terminology system OID (optional)

        Returns:
            Dictionary containing mapping data
        """
        try:
            params = {
                "sourceCodeSystem": source_code_system,
                "country": self.country_code,
            }

            if target_code_system:
                params["targetCodeSystem"] = target_code_system

            url = urljoin(self.base_url, self.endpoints["mappings"])
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching concept mappings from CTS: {e}")
            return {"error": str(e), "mappings": []}

    def get_translations(
        self, concept_id: str, target_languages: List[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve translations for a specific concept

        Args:
            concept_id: Concept identifier
            target_languages: List of target language codes

        Returns:
            Dictionary containing translation data
        """
        try:
            params = {"conceptId": concept_id, "country": self.country_code}

            if target_languages:
                params["languages"] = ",".join(target_languages)

            url = urljoin(self.base_url, self.endpoints["translations"])
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching translations from CTS: {e}")
            return {"error": str(e), "translations": []}

    def sync_mvc(self, force_full_sync=False) -> Dict[str, Any]:
        """
        Synchronize Master Value Set Catalogue (MVC) with CTS

        Args:
            force_full_sync: Force a complete synchronization

        Returns:
            Synchronization result
        """
        try:
            params = {
                "country": self.country_code,
                "fullSync": str(force_full_sync).lower(),
            }

            url = urljoin(self.base_url, self.endpoints["mvc_sync"])
            response = self.session.post(url, json=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error synchronizing MVC with CTS: {e}")
            return {"error": str(e), "success": False}

    def sync_mtc(self, force_full_sync=False) -> Dict[str, Any]:
        """
        Synchronize Master Terminology Catalogue (MTC) with CTS

        Args:
            force_full_sync: Force a complete synchronization

        Returns:
            Synchronization result
        """
        try:
            params = {
                "country": self.country_code,
                "fullSync": str(force_full_sync).lower(),
            }

            url = urljoin(self.base_url, self.endpoints["mtc_sync"])
            response = self.session.post(url, json=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error synchronizing MTC with CTS: {e}")
            return {"error": str(e), "success": False}

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get synchronization status for this member state

        Returns:
            Current sync status information
        """
        try:
            params = {"country": self.country_code}

            url = urljoin(self.base_url, self.endpoints["sync_status"])
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sync status from CTS: {e}")
            return {"error": str(e), "status": "unknown"}


class MVCManager:
    """
    Master Value Set Catalogue Manager
    Handles synchronization and management of value sets
    """

    def __init__(self, cts_client: CTSAPIClient = None):
        self.cts_client = cts_client or CTSAPIClient()

    def sync_value_sets(self, languages=["en"]) -> Dict[str, Any]:
        """
        Synchronize value sets with CTS for specified languages

        Args:
            languages: List of language codes to synchronize

        Returns:
            Synchronization results
        """
        from translation_manager.models import TerminologySystem, LanguageTranslation

        results = {
            "success": True,
            "languages_processed": [],
            "value_sets_updated": 0,
            "translations_added": 0,
            "errors": [],
        }

        try:
            with transaction.atomic():
                for language in languages:
                    logger.info(f"Synchronizing value sets for language: {language}")

                    # Fetch value sets from CTS
                    cts_data = self.cts_client.get_value_sets(language=language)

                    if "error" in cts_data:
                        results["errors"].append(
                            f"Language {language}: {cts_data['error']}"
                        )
                        continue

                    # Process value sets
                    for value_set in cts_data.get("value_sets", []):
                        self._process_value_set(value_set, language, results)

                    results["languages_processed"].append(language)

        except Exception as e:
            logger.error(f"Error during MVC synchronization: {e}")
            results["success"] = False
            results["errors"].append(str(e))

        return results

    def _process_value_set(self, value_set_data: Dict, language: str, results: Dict):
        """Process individual value set from CTS data"""
        from translation_manager.models import TerminologySystem, LanguageTranslation

        try:
            # Get or create terminology system
            system, created = TerminologySystem.objects.get_or_create(
                oid=value_set_data.get("oid"),
                defaults={
                    "name": value_set_data.get("name", "Unknown"),
                    "description": value_set_data.get("description", ""),
                    "version": value_set_data.get("version", ""),
                    "is_active": value_set_data.get("active", True),
                },
            )

            if created or system.updated_at < timezone.now() - timedelta(days=1):
                # Update system information
                system.name = value_set_data.get("name", system.name)
                system.description = value_set_data.get(
                    "description", system.description
                )
                system.version = value_set_data.get("version", system.version)
                system.is_active = value_set_data.get("active", system.is_active)
                system.save()
                results["value_sets_updated"] += 1

            # Process concepts and translations
            for concept in value_set_data.get("concepts", []):
                self._process_concept_translation(system, concept, language, results)

        except Exception as e:
            logger.error(f"Error processing value set {value_set_data.get('oid')}: {e}")
            results["errors"].append(f"Value set {value_set_data.get('oid')}: {str(e)}")

    def _process_concept_translation(
        self,
        system: "TerminologySystem",
        concept_data: Dict,
        language: str,
        results: Dict,
    ):
        """Process concept translation from CTS data"""
        from translation_manager.models import LanguageTranslation

        try:
            # Get or create translation
            translation, created = LanguageTranslation.objects.get_or_create(
                terminology_system=system,
                concept_code=concept_data.get("code"),
                language_code=language,
                defaults={
                    "display_name": concept_data.get("display_name", ""),
                    "definition": concept_data.get("definition", ""),
                    "is_active": concept_data.get("active", True),
                },
            )

            if created:
                results["translations_added"] += 1
            elif translation.updated_at < timezone.now() - timedelta(days=1):
                # Update existing translation
                translation.display_name = concept_data.get(
                    "display_name", translation.display_name
                )
                translation.definition = concept_data.get(
                    "definition", translation.definition
                )
                translation.is_active = concept_data.get(
                    "active", translation.is_active
                )
                translation.save()

        except Exception as e:
            logger.error(
                f"Error processing concept translation {concept_data.get('code')}: {e}"
            )


class MTCManager:
    """
    Master Terminology Catalogue Manager
    Handles synchronization and management of terminology mappings
    """

    def __init__(self, cts_client: CTSAPIClient = None):
        self.cts_client = cts_client or CTSAPIClient()

    def sync_concept_mappings(self, source_systems: List[str] = None) -> Dict[str, Any]:
        """
        Synchronize concept mappings with CTS

        Args:
            source_systems: List of source system OIDs to synchronize

        Returns:
            Synchronization results
        """
        from translation_manager.models import TerminologySystem, ConceptMapping

        results = {
            "success": True,
            "systems_processed": [],
            "mappings_updated": 0,
            "errors": [],
        }

        try:
            # Default to all active systems if none specified
            if not source_systems:
                source_systems = list(
                    TerminologySystem.objects.filter(is_active=True).values_list(
                        "oid", flat=True
                    )
                )

            with transaction.atomic():
                for source_oid in source_systems:
                    logger.info(f"Synchronizing mappings for system: {source_oid}")

                    # Fetch mappings from CTS
                    cts_data = self.cts_client.get_concept_mappings(source_oid)

                    if "error" in cts_data:
                        results["errors"].append(
                            f"System {source_oid}: {cts_data['error']}"
                        )
                        continue

                    # Process mappings
                    for mapping in cts_data.get("mappings", []):
                        self._process_concept_mapping(mapping, results)

                    results["systems_processed"].append(source_oid)

        except Exception as e:
            logger.error(f"Error during MTC synchronization: {e}")
            results["success"] = False
            results["errors"].append(str(e))

        return results

    def _process_concept_mapping(self, mapping_data: Dict, results: Dict):
        """Process individual concept mapping from CTS data"""
        from translation_manager.models import TerminologySystem, ConceptMapping

        try:
            # Get source and target systems
            source_system = TerminologySystem.objects.get(
                oid=mapping_data.get("source_system_oid")
            )
            target_system = TerminologySystem.objects.get(
                oid=mapping_data.get("target_system_oid")
            )

            # Get or create mapping
            mapping, created = ConceptMapping.objects.get_or_create(
                source_system=source_system,
                source_code=mapping_data.get("source_code"),
                target_system=target_system,
                target_code=mapping_data.get("target_code"),
                defaults={
                    "source_display_name": mapping_data.get("source_display_name", ""),
                    "target_display_name": mapping_data.get("target_display_name", ""),
                    "mapping_type": mapping_data.get("mapping_type", "EQUIVALENT"),
                    "confidence_score": mapping_data.get("confidence_score", 1.0),
                    "is_active": mapping_data.get("active", True),
                },
            )

            if created or mapping.updated_at < timezone.now() - timedelta(days=1):
                # Update mapping information
                mapping.source_display_name = mapping_data.get(
                    "source_display_name", mapping.source_display_name
                )
                mapping.target_display_name = mapping_data.get(
                    "target_display_name", mapping.target_display_name
                )
                mapping.mapping_type = mapping_data.get(
                    "mapping_type", mapping.mapping_type
                )
                mapping.confidence_score = mapping_data.get(
                    "confidence_score", mapping.confidence_score
                )
                mapping.is_active = mapping_data.get("active", mapping.is_active)
                mapping.save()
                results["mappings_updated"] += 1

        except TerminologySystem.DoesNotExist as e:
            logger.warning(f"Terminology system not found for mapping: {e}")
        except Exception as e:
            logger.error(f"Error processing concept mapping: {e}")
            results["errors"].append(f"Mapping error: {str(e)}")


class CTSTranslationService:
    """
    CTS-based translation service using MVC/MTC data
    Provides medical terminology translation using synchronized CTS data
    """

    def __init__(self, cts_client: CTSAPIClient = None):
        self.cts_client = cts_client or CTSAPIClient()
        self.mvc_manager = MVCManager(cts_client)
        self.mtc_manager = MTCManager(cts_client)

    def translate_concept(
        self, source_code: str, source_system_oid: str, target_language: str
    ) -> Optional[str]:
        """
        Translate a medical concept using CTS synchronized data

        Args:
            source_code: Source concept code
            source_system_oid: Source terminology system OID
            target_language: Target language code

        Returns:
            Translated term or None if not found
        """
        from translation_manager.models import TerminologySystem, LanguageTranslation

        try:
            # First try local synchronized data
            translation = LanguageTranslation.objects.filter(
                terminology_system__oid=source_system_oid,
                concept_code=source_code,
                language_code=target_language,
                is_active=True,
            ).first()

            if translation:
                return translation.display_name

            # If not found locally, try CTS API
            cts_data = self.cts_client.get_translations(
                concept_id=f"{source_system_oid}#{source_code}",
                target_languages=[target_language],
            )

            translations = cts_data.get("translations", [])
            for trans in translations:
                if trans.get("language") == target_language:
                    return trans.get("display_name")

            return None

        except Exception as e:
            logger.error(f"Error translating concept {source_code}: {e}")
            return None

    def find_equivalent_concept(
        self, source_code: str, source_system_oid: str, target_system_oid: str
    ) -> Optional[str]:
        """
        Find equivalent concept in target terminology system

        Args:
            source_code: Source concept code
            source_system_oid: Source terminology system OID
            target_system_oid: Target terminology system OID

        Returns:
            Target concept code or None if not found
        """
        from translation_manager.models import ConceptMapping

        try:
            # Try local synchronized mapping data
            mapping = ConceptMapping.objects.filter(
                source_system__oid=source_system_oid,
                source_code=source_code,
                target_system__oid=target_system_oid,
                is_active=True,
            ).first()

            if mapping:
                return mapping.target_code

            # If not found locally, try CTS API
            cts_data = self.cts_client.get_concept_mappings(
                source_code_system=source_system_oid,
                target_code_system=target_system_oid,
            )

            mappings = cts_data.get("mappings", [])
            for mapping in mappings:
                if mapping.get("source_code") == source_code:
                    return mapping.get("target_code")

            return None

        except Exception as e:
            logger.error(f"Error finding equivalent concept for {source_code}: {e}")
            return None

    def sync_all(self, languages=["en", "fr", "de", "es", "it"]) -> Dict[str, Any]:
        """
        Perform full synchronization of MVC and MTC with CTS

        Args:
            languages: List of languages to synchronize

        Returns:
            Combined synchronization results
        """
        results = {"mvc_sync": {}, "mtc_sync": {}, "overall_success": True}

        try:
            # Synchronize MVC (value sets and translations)
            logger.info("Starting MVC synchronization...")
            results["mvc_sync"] = self.mvc_manager.sync_value_sets(languages)

            # Synchronize MTC (concept mappings)
            logger.info("Starting MTC synchronization...")
            results["mtc_sync"] = self.mtc_manager.sync_concept_mappings()

            # Check overall success
            results["overall_success"] = results["mvc_sync"].get(
                "success", False
            ) and results["mtc_sync"].get("success", False)

        except Exception as e:
            logger.error(f"Error during full CTS synchronization: {e}")
            results["overall_success"] = False
            results["error"] = str(e)

        return results
