"""
Enhanced CDA Translation Service for Django NCP
Integrates the working CDA translation functionality with Django
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass
class CDASection:
    """Represents a translated CDA section"""

    section_id: str
    french_title: str
    english_title: str
    translated_title: str
    original_content: str
    translated_content: str
    medical_terms_count: int
    content_length: int


@dataclass
class CDATranslationResult:
    """Complete CDA translation result"""

    document_id: str
    source_language: str
    target_language: str
    total_sections: int
    sections: List[CDASection]
    medical_terms_translated: int
    translation_quality: float
    document_size: int


class EnhancedCDATranslationService:
    """
    Production-ready CDA translation service for EU cross-border healthcare
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self.medical_terms = self._load_medical_terminology()

    def _load_medical_terminology(self) -> Dict[str, str]:
        """Load comprehensive medical terminology dictionary"""
        return {
            # Anatomical terms
            "coeur": "heart",
            "poumon": "lung",
            "foie": "liver",
            "rein": "kidney",
            "cerveau": "brain",
            "estomac": "stomach",
            "intestin": "intestine",
            "muscle": "muscle",
            "os": "bone",
            "sang": "blood",
            "artère": "artery",
            "veine": "vein",
            "nerf": "nerve",
            "peau": "skin",
            "œil": "eye",
            "oreille": "ear",
            "nez": "nose",
            "bouche": "mouth",
            "dent": "tooth",
            # Medical conditions & symptoms
            "maladie": "disease",
            "infection": "infection",
            "inflammation": "inflammation",
            "douleur": "pain",
            "fièvre": "fever",
            "toux": "cough",
            "mal de tête": "headache",
            "nausée": "nausea",
            "vomissement": "vomiting",
            "diarrhée": "diarrhea",
            "fatigue": "fatigue",
            "faiblesse": "weakness",
            "vertige": "dizziness",
            "éruption": "rash",
            "gonflement": "swelling",
            "allergie": "allergy",
            "allergies": "allergies",
            "hypersensibilité": "hypersensitivity",
            "anaphylaxie": "anaphylaxis",
            "réaction": "reaction",
            "intolérances": "intolerances",
            "intolérance": "intolerance",
            # Pharmaceutical terms
            "médicament": "medication",
            "médicamenteuse": "medication",
            "médicamenteux": "medication",
            "comprimé": "tablet",
            "gélule": "capsule",
            "sirop": "syrup",
            "injection": "injection",
            "pommade": "ointment",
            "crème": "cream",
            "gouttes": "drops",
            "dose": "dose",
            "dosage": "dosage",
            "posologie": "dosage",
            "traitement": "treatment",
            "traitements": "treatments",
            "prescription": "prescription",
            "ordonnance": "prescription",
            "antibiotique": "antibiotic",
            "antidouleur": "painkiller",
            "anti-inflammatoire": "anti-inflammatory",
            "vitamines": "vitamins",
            # Medication forms and routes
            "sol buv": "oral solution",
            "cp": "tablet",
            "gél": "capsule",
            "orale": "oral",
            "par": "per",
            "jour": "day",
            "heure": "hour",
            "mg": "mg",
            "ml": "ml",
            "principe actif": "active ingredient",
            "forme pharmaceutique": "pharmaceutical form",
            "route": "route",
            "date de début": "start date",
            "date de fin": "end date",
            "notes": "notes",
            "nom commercial": "brand name",
            "code": "code",
            # Allergy and intolerance terms
            "agent causant": "causative agent",
            "manifestation": "manifestation",
            "sévérité": "severity",
            "statut": "status",
            "confirmée": "confirmed",
            "modérée": "moderate",
            "sévère": "severe",
            "éruption cutanée": "skin rash",
            "cutanée": "skin",
            "fruits de mer": "seafood",
            "pénicilline": "penicillin",
            "alimentaire": "food",
            # Vaccination terms
            "vaccination": "vaccination",
            "vaccin": "vaccine",
            "vaccins": "vaccines",
            "immunisation": "immunization",
            "rappel": "booster",
            "série": "series",
            "protocole": "protocol",
            "calendrier": "schedule",
            "administré": "administered",
            "administration": "administration",
            "date d'administration": "administration date",
            "lot": "batch",
            "grippe": "flu",
            "saisonnière": "seasonal",
            "contre": "against",
            # Clinical procedures
            "examen": "examination",
            "consultation": "consultation",
            "diagnostic": "diagnosis",
            "analyse": "analysis",
            "test": "test",
            "radiographie": "x-ray",
            "scanner": "CT scan",
            "IRM": "MRI",
            "échographie": "ultrasound",
            "biopsie": "biopsy",
            "chirurgie": "surgery",
            "chirurgical": "surgical",
            "chirurgicaux": "surgical",
            "opération": "operation",
            "intervention": "intervention",
            "hospitalisation": "hospitalization",
            "urgences": "emergency",
            "réanimation": "intensive care",
            "rééducation": "rehabilitation",
            # Medical specialties & personnel
            "patient": "patient",
            "patients": "patients",
            "médecin": "doctor",
            "infirmier": "nurse",
            "chirurgien": "surgeon",
            "spécialiste": "specialist",
            "généraliste": "general practitioner",
            "cardiologue": "cardiologist",
            # Healthcare facilities
            "hôpital": "hospital",
            "clinique": "clinic",
            "pharmacie": "pharmacy",
            "laboratoire": "laboratory",
            "cabinet": "office",
            "service": "department",
            # Medical terminology
            "symptôme": "symptom",
            "symptômes": "symptoms",
            "signe": "sign",
            "signes": "signs",
            "antécédent": "medical history",
            "antécédents": "medical history",
            "historique": "history",
            "prise": "intake",
            "effet": "effect",
            "effets": "effects",
            "secondaire": "side effect",
            "indésirable": "adverse",
            "indésirables": "adverse",
            "contre-indication": "contraindication",
            "précaution": "precaution",
            # Body systems
            "cardiovasculaire": "cardiovascular",
            "respiratoire": "respiratory",
            "digestif": "digestive",
            "neurologique": "neurological",
            "endocrinien": "endocrine",
            "immunologique": "immunological",
            # Medical devices & equipment
            "dispositif": "device",
            "dispositifs": "devices",
            "médical": "medical",
            "médicaux": "medical",
            "implant": "implant",
            "implants": "implants",
            "prothèse": "prosthesis",
            "stimulateur": "pacemaker",
            # Time & frequency terms
            "quotidien": "daily",
            "hebdomadaire": "weekly",
            "mensuel": "monthly",
            "chronique": "chronic",
            "aigu": "acute",
            "récurrent": "recurrent",
            "temporaire": "temporary",
            "permanent": "permanent",
            # Severity & status
            "grave": "severe",
            "léger": "mild",
            "modéré": "moderate",
            "contrôlé": "controlled",
            "stable": "stable",
            "instable": "unstable",
            "actif": "active",
            "inactif": "inactive",
            "résolu": "resolved",
            # Common medical phrases
            "surveillance": "monitoring",
            "suivi": "follow-up",
            "contrôle": "control",
            "prévention": "prevention",
            "dépistage": "screening",
            "diagnostic": "diagnosis",
            "pronostic": "prognosis",
            "récupération": "recovery",
            "guérison": "healing",
            "rémission": "remission",
            "rechute": "relapse",
            "évolution": "progression",
            # Administrative terms
            "dossier": "medical record",
            "fiche": "form",
            "rapport": "report",
            "compte-rendu": "report",
            "résultat": "result",
            "résultats": "results",
            "valeur": "value",
            "normale": "normal",
            "anormal": "abnormal",
            "référence": "reference",
            "seuil": "threshold",
            # Problems and issues
            "problème": "problem",
            "problèmes": "problems",
            "trouble": "disorder",
            "troubles": "disorders",
            "complication": "complication",
            "complications": "complications",
            "risque": "risk",
            "risques": "risks",
            "facteur": "factor",
            # General terms
            "santé": "health",
            "médecine": "medicine",
            "soins": "care",
            "thérapie": "therapy",
            "thérapeutique": "therapeutic",
            "clinique": "clinical",
            "pathologie": "pathology",
            "étiologie": "etiology",
            # Specific medication names and substances
            "zidovudine": "zidovudine",
            "ténofovir": "tenofovir",
            "névirapine": "nevirapine",
            "retrovir": "retrovir",
            "viread": "viread",
            "viramune": "viramune",
            "disoproxil": "disoproxil",
            "fumarate": "fumarate",
        }

    def translate_medical_text(
        self, text: str, source_lang: str = "fr"
    ) -> Tuple[str, int]:
        """
        Translate medical text using terminology dictionary
        Returns: (translated_text, medical_terms_count)
        """
        if source_lang == self.target_language:
            return text, 0

        translated_text = text
        medical_terms_found = 0

        # Apply medical terminology translations (case-insensitive)
        for french_term, english_term in self.medical_terms.items():
            pattern = re.compile(re.escape(french_term), re.IGNORECASE)
            if pattern.search(translated_text):
                translated_text = pattern.sub(english_term, translated_text)
                medical_terms_found += 1

        return translated_text, medical_terms_found

    def extract_cda_sections(self, html_content: str) -> List[Dict]:
        """
        Extract structured sections from CDA HTML document
        """
        sections = []

        # Primary pattern for Luxembourg CDA format with title attributes
        section_pattern = r'<h3[^>]*title="([^"]*)"[^>]*>([^<]+)</h3>.*?<div[^>]*class="section-body"[^>]*>(.*?)</div>'
        matches = re.findall(section_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for i, (english_hint, french_title, content) in enumerate(matches):
            # Clean content by removing HTML tags
            clean_content = re.sub(r"<[^>]+>", " ", content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()

            sections.append(
                {
                    "section_id": f"section_{i+1}",
                    "french_title": french_title.strip(),
                    "english_hint": english_hint.strip(),
                    "content": clean_content,
                    "raw_html": content.strip(),
                }
            )

        # Fallback 1: Look for XML-style section tags (for demo data)
        if not sections:
            xml_section_pattern = r"<section[^>]*>.*?<title>([^<]+)</title>.*?<text[^>]*>(.*?)</text>.*?</section>"
            xml_matches = re.findall(
                xml_section_pattern, html_content, re.DOTALL | re.IGNORECASE
            )

            for i, (title, content) in enumerate(xml_matches):
                # Handle table structure specially
                if "<table>" in content:
                    # Extract table data row by row
                    table_data = []

                    # Extract header row for context
                    header_pattern = r"<thead[^>]*>.*?<tr[^>]*>(.*?)</tr>.*?</thead>"
                    header_match = re.search(
                        header_pattern, content, re.DOTALL | re.IGNORECASE
                    )
                    if header_match:
                        header_cells = re.findall(
                            r"<th[^>]*>([^<]+)</th>",
                            header_match.group(1),
                            re.IGNORECASE,
                        )
                        table_data.append("Headers: " + " | ".join(header_cells))

                    # Extract data rows
                    tbody_pattern = r"<tbody[^>]*>(.*?)</tbody>"
                    tbody_match = re.search(
                        tbody_pattern, content, re.DOTALL | re.IGNORECASE
                    )
                    if tbody_match:
                        row_pattern = r"<tr[^>]*>(.*?)</tr>"
                        rows = re.findall(
                            row_pattern, tbody_match.group(1), re.DOTALL | re.IGNORECASE
                        )

                        for row in rows:
                            cell_data = re.findall(
                                r"<td[^>]*>([^<]*)</td>", row, re.IGNORECASE
                            )
                            if cell_data:
                                # Filter out empty cells and join meaningful data
                                meaningful_data = [
                                    cell.strip() for cell in cell_data if cell.strip()
                                ]
                                if meaningful_data:
                                    table_data.append(" | ".join(meaningful_data))

                    clean_content = " ".join(table_data)
                else:
                    # Extract content items for non-table content
                    content_items = re.findall(
                        r"<content[^>]*>([^<]+)</content>", content, re.IGNORECASE
                    )
                    clean_content = (
                        " ".join(content_items) if content_items else content
                    )

                    # Remove remaining HTML tags
                    clean_content = re.sub(r"<[^>]+>", " ", clean_content)

                clean_content = re.sub(r"\s+", " ", clean_content).strip()

                sections.append(
                    {
                        "section_id": f"section_{i+1}",
                        "french_title": title.strip(),
                        "english_hint": "",
                        "content": clean_content,
                        "raw_html": content.strip(),
                    }
                )

        # Fallback 2: Look for h2/h3 headers if no structured sections found
        if not sections:
            header_pattern = r"<h[23][^>]*>([^<]+)</h[23]>"
            headers = re.findall(header_pattern, html_content, re.IGNORECASE)

            if headers:
                parts = re.split(
                    r"<h[23][^>]*>[^<]+</h[23]>", html_content, flags=re.IGNORECASE
                )

                for i, header in enumerate(headers):
                    if i + 1 < len(parts):
                        content = parts[i + 1]
                        clean_content = re.sub(r"<[^>]+>", " ", content)
                        clean_content = re.sub(r"\s+", " ", clean_content).strip()

                        sections.append(
                            {
                                "section_id": f"section_{i+1}",
                                "french_title": header.strip(),
                                "english_hint": "",
                                "content": clean_content,
                                "raw_html": content.strip(),
                            }
                        )

        return sections

    def detect_source_language(self, text: str) -> str:
        """
        Detect document language based on common medical terms
        """
        french_indicators = [
            "le",
            "la",
            "les",
            "de",
            "du",
            "des",
            "et",
            "ou",
            "avec",
            "sans",
            "médecin",
            "patient",
            "maladie",
            "traitement",
            "médicament",
            "allergie",
            "vaccination",
            "historique",
            "problème",
        ]

        english_indicators = [
            "the",
            "and",
            "or",
            "with",
            "without",
            "for",
            "by",
            "on",
            "in",
            "doctor",
            "patient",
            "disease",
            "treatment",
            "medication",
            "allergy",
            "vaccination",
            "history",
            "problem",
        ]

        text_lower = text.lower()
        french_count = sum(1 for word in french_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)

        return (
            "fr"
            if french_count > english_count
            else "en" if english_count > 0 else "unknown"
        )

    def translate_cda_document(
        self, html_content: str, document_id: str = None
    ) -> CDATranslationResult:
        """
        Translate complete CDA document with medical terminology
        """
        # Detect source language
        source_language = self.detect_source_language(html_content)

        # Extract sections
        raw_sections = self.extract_cda_sections(html_content)

        # Translate each section
        translated_sections = []
        total_medical_terms = 0

        for section_data in raw_sections:
            # Translate title
            translated_title, title_terms = self.translate_medical_text(
                section_data["french_title"], source_language
            )

            # Translate content
            translated_content, content_terms = self.translate_medical_text(
                section_data["content"], source_language
            )

            medical_terms_in_section = title_terms + content_terms
            total_medical_terms += medical_terms_in_section

            translated_sections.append(
                CDASection(
                    section_id=section_data["section_id"],
                    french_title=section_data["french_title"],
                    english_title=section_data["english_hint"],
                    translated_title=translated_title,
                    original_content=section_data["content"],
                    translated_content=translated_content,
                    medical_terms_count=medical_terms_in_section,
                    content_length=len(section_data["content"]),
                )
            )

        # Calculate translation quality
        avg_terms_per_section = total_medical_terms / max(1, len(translated_sections))
        quality_score = min(1.0, avg_terms_per_section / 3.0)  # Normalize to 0-1

        return CDATranslationResult(
            document_id=document_id or "unknown",
            source_language=source_language,
            target_language=self.target_language,
            total_sections=len(translated_sections),
            sections=translated_sections,
            medical_terms_translated=total_medical_terms,
            translation_quality=quality_score,
            document_size=len(html_content),
        )

    def get_bilingual_display_data(
        self, translation_result: CDATranslationResult
    ) -> Dict:
        """
        Format translation result for bilingual display in Django templates
        """
        return {
            "document_info": {
                "document_id": translation_result.document_id,
                "source_language": translation_result.source_language.upper(),
                "target_language": translation_result.target_language.upper(),
                "total_sections": translation_result.total_sections,
                "document_size": f"{translation_result.document_size:,}",
                "translation_quality": f"{translation_result.translation_quality:.1%}",
                "medical_terms_translated": translation_result.medical_terms_translated,
            },
            "sections": [
                {
                    "section_id": section.section_id,
                    "title": {
                        "original": section.french_title,
                        "english_hint": section.english_title,
                        "translated": section.translated_title,
                    },
                    "content": {
                        "original": section.original_content,
                        "translated": section.translated_content,
                        "length": section.content_length,
                        "medical_terms": section.medical_terms_count,
                    },
                    "preview": {
                        "original": (
                            section.original_content[:150] + "..."
                            if len(section.original_content) > 150
                            else section.original_content
                        ),
                        "translated": (
                            section.translated_content[:150] + "..."
                            if len(section.translated_content) > 150
                            else section.translated_content
                        ),
                    },
                }
                for section in translation_result.sections
            ],
        }


# Test function for development
def test_enhanced_service():
    """Test the enhanced CDA translation service"""
    print("Testing Enhanced CDA Translation Service")
    print("=" * 50)

    # Initialize service
    service = EnhancedCDATranslationService(target_language="en")

    # Load Luxembourg test file
    test_file = (
        Path(__file__).parent.parent.parent
        / "test_data"
        / "eu_member_states"
        / "LU"
        / "DefaultXsltOutput.htm"
    )

    if test_file.exists():
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Translate document
        result = service.translate_cda_document(content, "LU_TEST_001")

        # Get display data
        display_data = service.get_bilingual_display_data(result)

        print(f"Translation completed:")
        print(f"   Document: {display_data['document_info']['document_id']}")
        print(
            f"   Language: {display_data['document_info']['source_language']} -> {display_data['document_info']['target_language']}"
        )
        print(f"   Sections: {display_data['document_info']['total_sections']}")
        print(f"   Quality: {display_data['document_info']['translation_quality']}")
        print(
            f"   Medical terms: {display_data['document_info']['medical_terms_translated']}"
        )

        return display_data
    else:
        print(f"Test file not found: {test_file}")
        return None


if __name__ == "__main__":
    test_enhanced_service()
