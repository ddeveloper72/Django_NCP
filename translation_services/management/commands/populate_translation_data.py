"""
Django NCP Translation Services Management Commands

Commands for populating and managing translation data.
"""

import json
from django.core.management.base import BaseCommand
from translation_manager.models import (
    TerminologySystem,
    ConceptMapping,
    LanguageTranslation,
    CountrySpecificMapping,
    TranslationService,
)


class Command(BaseCommand):
    help = "Populate sample terminology systems and translation data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--load-sample-data",
            action="store_true",
            help="Load sample terminology and translation data",
        )

    def handle(self, *args, **options):
        if options["load_sample_data"]:
            self.load_sample_data()
        else:
            self.stdout.write(
                self.style.WARNING("Use --load-sample-data to populate sample data")
            )

    def load_sample_data(self):
        """Load sample terminology systems and translations"""

        self.stdout.write("Loading sample terminology systems...")

        # Create ICD-10 terminology system
        icd10, created = TerminologySystem.objects.get_or_create(
            name="ICD-10",
            defaults={
                "version": "2019",
                "description": "International Classification of Diseases, 10th Revision",
                "oid": "2.16.840.1.113883.6.3",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created {icd10.name}")

        # Create SNOMED CT terminology system
        snomed, created = TerminologySystem.objects.get_or_create(
            name="SNOMED-CT",
            defaults={
                "version": "2023-07",
                "description": "Systematized Nomenclature of Medicine Clinical Terms",
                "oid": "2.16.840.1.113883.6.96",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created {snomed.name}")

        # Create epSOS terminology system (EU pivot)
        epsos, created = TerminologySystem.objects.get_or_create(
            name="epSOS",
            defaults={
                "version": "1.0",
                "description": "European Patients Smart Open Services Terminology",
                "oid": "1.3.6.1.4.1.12559.11.10.1.3.1.42.1",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created {epsos.name}")

        # Create ATC terminology system for medications
        atc, created = TerminologySystem.objects.get_or_create(
            name="ATC",
            defaults={
                "version": "2023",
                "description": "Anatomical Therapeutic Chemical Classification",
                "oid": "2.16.840.1.113883.6.73",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"Created {atc.name}")

        self.stdout.write("Loading sample concept mappings...")

        # Sample concept mappings for allergies
        allergy_mappings = [
            {
                "source_code": "T78.40",
                "source_system": icd10,
                "source_display": "Allergy, unspecified",
                "target_code": "ALG001",
                "target_system": epsos,
                "target_display": "Allergic disposition",
                "mapping_type": "EQUIVALENT",
            },
            {
                "source_code": "294505008",
                "source_system": snomed,
                "source_display": "Penicillin allergy",
                "target_code": "ALG002",
                "target_system": epsos,
                "target_display": "Beta-lactam antibiotic allergy",
                "mapping_type": "EQUIVALENT",
            },
        ]

        for mapping_data in allergy_mappings:
            mapping, created = ConceptMapping.objects.get_or_create(
                source_code=mapping_data["source_code"],
                source_system=mapping_data["source_system"],
                target_code=mapping_data["target_code"],
                target_system=mapping_data["target_system"],
                defaults={
                    "source_display_name": mapping_data["source_display"],
                    "target_display_name": mapping_data["target_display"],
                    "mapping_type": mapping_data["mapping_type"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"Created mapping: {mapping_data['source_code']} -> {mapping_data['target_code']}"
                )

        self.stdout.write("Loading sample language translations...")

        # Sample language translations for English, German, French
        language_translations = [
            # Allergic disposition translations
            {
                "terminology_system": epsos,
                "concept_code": "ALG001",
                "language_code": "en-GB",
                "translated_term": "Allergic disposition",
                "is_preferred": True,
            },
            {
                "terminology_system": epsos,
                "concept_code": "ALG001",
                "language_code": "de-DE",
                "translated_term": "Allergische Disposition",
                "is_preferred": True,
            },
            {
                "terminology_system": epsos,
                "concept_code": "ALG001",
                "language_code": "fr-FR",
                "translated_term": "Disposition allergique",
                "is_preferred": True,
            },
            # Beta-lactam antibiotic allergy translations
            {
                "terminology_system": epsos,
                "concept_code": "ALG002",
                "language_code": "en-GB",
                "translated_term": "Beta-lactam antibiotics, penicillins",
                "is_preferred": True,
            },
            {
                "terminology_system": epsos,
                "concept_code": "ALG002",
                "language_code": "de-DE",
                "translated_term": "Beta-Lactam-Antibiotika, Penicilline",
                "is_preferred": True,
            },
            {
                "terminology_system": epsos,
                "concept_code": "ALG002",
                "language_code": "fr-FR",
                "translated_term": "Antibiotiques bêta-lactamines, pénicillines",
                "is_preferred": True,
            },
        ]

        for translation_data in language_translations:
            translation, created = LanguageTranslation.objects.get_or_create(
                terminology_system=translation_data["terminology_system"],
                concept_code=translation_data["concept_code"],
                language_code=translation_data["language_code"],
                defaults={
                    "translated_name": translation_data["translated_term"],
                    "is_preferred": translation_data["is_preferred"],
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(
                    f"Created translation: {translation_data['concept_code']} -> {translation_data['language_code']}: {translation_data['translated_term']}"
                )

        # Create translation service entries
        self.stdout.write("Creating translation service configurations...")

        service_configs = [
            {
                "name": "FHIR Translation Service",
                "service_type": "TERMINOLOGY",
                "endpoint_url": "http://localhost:8000/api/translation/fhir/",
                "supported_languages": "en-GB,de-DE,fr-FR,es-ES,it-IT,pt-PT,nl-NL",
                "is_active": True,
            },
            {
                "name": "CDA Translation Service",
                "service_type": "TERMINOLOGY",
                "endpoint_url": "http://localhost:8000/api/translation/cda/",
                "supported_languages": "en-GB,de-DE,fr-FR,es-ES,it-IT,pt-PT,nl-NL",
                "is_active": True,
            },
        ]

        for service_data in service_configs:
            service, created = TranslationService.objects.get_or_create(
                name=service_data["name"],
                defaults={
                    "service_type": service_data["service_type"],
                    "endpoint_url": service_data["endpoint_url"],
                    "supported_languages": service_data["supported_languages"],
                    "is_active": service_data["is_active"],
                },
            )
            if created:
                self.stdout.write(f"Created translation service: {service.name}")

        self.stdout.write(
            self.style.SUCCESS("Successfully loaded sample translation data!")
        )
