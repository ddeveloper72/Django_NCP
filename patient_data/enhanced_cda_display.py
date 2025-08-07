"""
CDA Display Tool Integration
Integrates the CTS-compliant Enhanced CDA Processor with the main CDA display system
"""

import logging
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from patient_data.services.enhanced_cda_processor import EnhancedCDAProcessor
from patient_data.translation_utils import (
    get_template_translations,
    detect_document_language,
)

logger = logging.getLogger(__name__)


class EnhancedCDADisplayView(View):
    """Enhanced CDA display view with CTS-compliant clinical sections"""

    def get(self, request, patient_id=None):
        """Display CDA document with enhanced clinical sections"""
        try:
            # Get patient CDA data (this would come from your existing patient data service)
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                return JsonResponse({"error": "Patient CDA data not found"}, status=404)

            # Detect document language
            source_language = detect_document_language(cda_content)
            target_language = request.GET.get("lang", "en")

            # Initialize enhanced processor
            processor = EnhancedCDAProcessor(target_language=target_language)

            # Process clinical sections with CTS compliance
            logger.info(f"Processing CDA content for patient {patient_id}")
            logger.info(
                f"Content type: {'XML' if '<?xml' in cda_content or '<ClinicalDocument' in cda_content else 'HTML'}"
            )
            logger.info(f"Content length: {len(cda_content)} characters")

            enhanced_sections = processor.process_clinical_sections(
                cda_content=cda_content, source_language=source_language
            )

            logger.info(f"Enhanced sections result: {enhanced_sections.keys()}")
            logger.info(
                f"Sections processed: {enhanced_sections.get('sections_count', 0)}"
            )
            logger.info(
                f"Content type detected: {enhanced_sections.get('content_type', 'unknown')}"
            )

            # Log each section for debugging
            for i, section in enumerate(enhanced_sections.get("sections", [])):
                section_code = section.get("section_code", "No code")
                title = section.get("title", {}).get("original", "No title")
                has_ps_table = section.get("has_ps_table", False)
                logger.info(
                    f"Section {i+1}: Code={section_code}, Title='{title}', Has_PS_Table={has_ps_table}"
                )

                # Check if section has value set data
                if "table_data" in section:
                    table_entries = len(section.get("table_data", []))
                    logger.info(f"  Table data entries: {table_entries}")

                    # Check first entry for value set fields
                    if table_entries > 0:
                        first_entry = section["table_data"][0]
                        entry_type = first_entry.get("type", "unknown")
                        logger.info(f"  First entry type: {entry_type}")

                        if "fields" in first_entry:
                            field_count = len(first_entry.get("fields", {}))
                            logger.info(
                                f"  Value set fields in first entry: {field_count}"
                            )
                            for field_name, field_info in first_entry.get(
                                "fields", {}
                            ).items():
                                has_valueset = field_info.get("has_valueset", False)
                                value = field_info.get("value", "No value")
                                logger.info(
                                    f"    {field_name}: {value} (has_valueset: {has_valueset})"
                                )
                else:
                    logger.info(f"  No table_data found in section")

            # Get template translations
            template_translations = get_template_translations(
                source_language=source_language, target_language=target_language
            )

            # Prepare context for template
            context = {
                "patient_id": patient_id,
                "enhanced_sections": enhanced_sections,
                "template_translations": template_translations,
                "source_language": source_language,
                "target_language": target_language,
                "document_metadata": {
                    "success": enhanced_sections.get("success", False),
                    "content_type": enhanced_sections.get("content_type", "unknown"),
                    "sections_count": enhanced_sections.get("sections_count", 0),
                    "coded_sections_count": enhanced_sections.get(
                        "coded_sections_count", 0
                    ),
                    "medical_terms_count": enhanced_sections.get(
                        "medical_terms_count", 0
                    ),
                    "translation_quality": enhanced_sections.get(
                        "translation_quality", "Basic"
                    ),
                    "uses_coded_sections": enhanced_sections.get(
                        "uses_coded_sections", False
                    ),
                },
            }

            return render(
                request, "jinja2/patient_data/enhanced_patient_cda.html", context
            )

        except Exception as e:
            logger.error(f"Error in enhanced CDA display: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content - placeholder for your existing service"""
        # This should integrate with your existing patient data service
        # For now, return mock content to demonstrate the enhanced display

        if not patient_id:
            return None

        # Mock CDA content - replace with your actual service
        mock_cda = f"""
        <html>
            <body>
                <div class="patient-summary">
                    <h1>Patient {patient_id} - Résumé Médical</h1>
                    
                    <section class="medication-summary" data-code="10160-0">
                        <h2>Résumé des médicaments</h2>
                        <table class="clinical-table">
                            <thead>
                                <tr>
                                    <th>Médicament</th>
                                    <th>Dosage</th>
                                    <th>Fréquence</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Amoxicilline</td>
                                    <td>500mg</td>
                                    <td>3 fois par jour</td>
                                    <td>Actif</td>
                                </tr>
                                <tr>
                                    <td>Paracétamol</td>
                                    <td>1000mg</td>
                                    <td>Au besoin</td>
                                    <td>Actif</td>
                                </tr>
                            </tbody>
                        </table>
                    </section>
                    
                    <section class="allergy-summary" data-code="48765-2">
                        <h2>Allergies et réactions indésirables</h2>
                        <table class="clinical-table">
                            <thead>
                                <tr>
                                    <th>Allergène</th>
                                    <th>Réaction</th>
                                    <th>Sévérité</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Pénicilline</td>
                                    <td>Éruption cutanée</td>
                                    <td>Modéré</td>
                                    <td>Confirmé</td>
                                </tr>
                            </tbody>
                        </table>
                    </section>
                    
                    <section class="problem-list" data-code="11450-4">
                        <h2>Liste des problèmes</h2>
                        <table class="clinical-table">
                            <thead>
                                <tr>
                                    <th>Condition</th>
                                    <th>Date de diagnostic</th>
                                    <th>Statut</th>
                                    <th>Code ICD-10</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Hypertension artérielle</td>
                                    <td>2023-01-15</td>
                                    <td>Actif</td>
                                    <td>I10</td>
                                </tr>
                                <tr>
                                    <td>Diabète type 2</td>
                                    <td>2022-08-20</td>
                                    <td>Actif</td>
                                    <td>E11</td>
                                </tr>
                            </tbody>
                        </table>
                    </section>
                    
                    <section class="vital-signs" data-code="8716-3">
                        <h2>Signes vitaux</h2>
                        <table class="clinical-table">
                            <thead>
                                <tr>
                                    <th>Paramètre</th>
                                    <th>Valeur</th>
                                    <th>Unité</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Tension artérielle</td>
                                    <td>140/90</td>
                                    <td>mmHg</td>
                                    <td>2025-08-05</td>
                                </tr>
                                <tr>
                                    <td>Glycémie</td>
                                    <td>7.2</td>
                                    <td>mmol/L</td>
                                    <td>2025-08-05</td>
                                </tr>
                            </tbody>
                        </table>
                    </section>
                </div>
            </body>
        </html>
        """

        return mock_cda


@method_decorator(csrf_exempt, name="dispatch")
class CDALanguageToggleView(View):
    """API endpoint for toggling between source and target language display"""

    def post(self, request):
        """Toggle language display for CDA sections"""
        try:
            data = json.loads(request.body)
            patient_id = data.get("patient_id")
            target_language = data.get("target_language", "en")
            section_id = data.get("section_id")

            if not patient_id or not section_id:
                return JsonResponse(
                    {"error": "Missing required parameters"}, status=400
                )

            # Get CDA content
            cda_content = self._get_patient_cda_content(patient_id)
            if not cda_content:
                return JsonResponse({"error": "Patient data not found"}, status=404)

            # Detect source language
            source_language = detect_document_language(cda_content)

            # Process with enhanced processor
            processor = EnhancedCDAProcessor(target_language=target_language)
            enhanced_sections = processor.process_clinical_sections(
                cda_content=cda_content, source_language=source_language
            )

            # Find the specific section
            section_data = None
            for section in enhanced_sections.get("sections", []):
                if section.get("section_id") == section_id:
                    section_data = section
                    break

            if not section_data:
                return JsonResponse({"error": "Section not found"}, status=404)

            return JsonResponse(
                {
                    "success": True,
                    "section_data": section_data,
                    "metadata": {
                        "source_language": source_language,
                        "target_language": target_language,
                        "has_ps_table": section_data.get("has_ps_table", False),
                        "is_coded_section": section_data.get("is_coded_section", False),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error in language toggle: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def _get_patient_cda_content(self, patient_id: str) -> Optional[str]:
        """Get patient CDA content - same as above"""
        # This should integrate with your existing patient data service
        return EnhancedCDADisplayView()._get_patient_cda_content(patient_id)


def get_enhanced_clinical_sections_api(request, patient_id):
    """API endpoint to get enhanced clinical sections data"""
    try:
        target_language = request.GET.get("lang", "en")

        # Get CDA content
        display_view = EnhancedCDADisplayView()
        cda_content = display_view._get_patient_cda_content(patient_id)

        if not cda_content:
            return JsonResponse({"error": "Patient data not found"}, status=404)

        # Detect source language and process
        source_language = detect_document_language(cda_content)
        processor = EnhancedCDAProcessor(target_language=target_language)

        enhanced_sections = processor.process_clinical_sections(
            cda_content=cda_content, source_language=source_language
        )

        return JsonResponse(
            {
                "success": True,
                "data": enhanced_sections,
                "metadata": {
                    "patient_id": patient_id,
                    "source_language": source_language,
                    "target_language": target_language,
                    "processing_timestamp": "2025-08-05T12:00:00Z",
                },
            }
        )

    except Exception as e:
        logger.error(f"Error in enhanced sections API: {e}")
        return JsonResponse({"error": str(e)}, status=500)
