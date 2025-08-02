#!/usr/bin/env python3
"""
Standalone CDA Translation Test
Tests the CDA translation functionality without Django dependencies

This script allows us to continue developing the CDA translation service
while Django import issues are being resolved.
"""

import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
import re

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@dataclass
class TranslationResult:
    """Results from CDA translation processing"""

    original_language: str
    target_language: str
    original_content: str
    translated_content: str
    sections: List[Dict]
    translation_quality: float
    medical_terms_count: int


class SimpleCDATranslator:
    """
    Simplified CDA translator for testing medical terminology translation
    """

    def __init__(self):
        # Medical terminology dictionary (French to English)
        self.medical_terms = {
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
            "langue": "tongue",
            # Medical conditions
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
            "constipation": "constipation",
            "fatigue": "fatigue",
            "faiblesse": "weakness",
            "vertige": "dizziness",
            "éruption": "rash",
            "démangeaison": "itching",
            "gonflement": "swelling",
            "hypertension": "hypertension",
            "diabète": "diabetes",
            "asthme": "asthma",
            "cancer": "cancer",
            "tumeur": "tumor",
            "fracture": "fracture",
            "blessure": "injury",
            "allergie": "allergy",
            # Pharmaceutical terms
            "médicament": "medication",
            "comprimé": "tablet",
            "gélule": "capsule",
            "sirop": "syrup",
            "injection": "injection",
            "pommade": "ointment",
            "crème": "cream",
            "gouttes": "drops",
            "dose": "dose",
            "posologie": "dosage",
            "traitement": "treatment",
            "prescription": "prescription",
            "ordonnance": "prescription",
            "antibiotique": "antibiotic",
            "antidouleur": "painkiller",
            "anti-inflammatoire": "anti-inflammatory",
            "vitamines": "vitamins",
            "supplément": "supplement",
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
            "opération": "operation",
            "intervention": "intervention",
            "hospitalisation": "hospitalization",
            "urgences": "emergency",
            "réanimation": "intensive care",
            "rééducation": "rehabilitation",
            "physiothérapie": "physiotherapy",
            # General medical terms
            "patient": "patient",
            "médecin": "doctor",
            "infirmier": "nurse",
            "hôpital": "hospital",
            "clinique": "clinic",
            "pharmacie": "pharmacy",
            "laboratoire": "laboratory",
            "symptôme": "symptom",
            "signe": "sign",
            "antécédent": "medical history",
            "allergie": "allergy",
            "effet secondaire": "side effect",
            "contre-indication": "contraindication",
            "récupération": "recovery",
            "guérison": "healing",
            "prévention": "prevention",
            "vaccin": "vaccine",
            "immunisation": "immunization",
        }

    def translate_text(
        self, text: str, source_lang: str = "fr", target_lang: str = "en"
    ) -> str:
        """
        Translate text using medical terminology dictionary
        """
        if source_lang == target_lang:
            return text

        translated_text = text
        medical_terms_found = 0

        # Apply medical terminology translations
        for french_term, english_term in self.medical_terms.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(french_term), re.IGNORECASE)
            if pattern.search(translated_text):
                translated_text = pattern.sub(english_term, translated_text)
                medical_terms_found += 1

        return translated_text

    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on common words
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
            "pour",
            "par",
            "sur",
            "dans",
            "médecin",
            "patient",
            "maladie",
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
        ]

        text_lower = text.lower()
        french_count = sum(1 for word in french_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)

        if french_count > english_count:
            return "fr"
        elif english_count > french_count:
            return "en"
        else:
            return "unknown"

    def parse_html_cda(self, html_content: str) -> Dict:
        """
        Parse HTML CDA document and extract key sections
        """
        sections = []

        # Use regex to find section blocks with French titles
        section_pattern = r'<div[^>]*class="section"[^>]*>.*?<h3[^>]*title="([^"]*)"[^>]*>([^<]+)</h3>.*?<div[^>]*class="section-body"[^>]*>(.*?)</div>'

        matches = re.findall(section_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for i, (english_title, french_title, content) in enumerate(matches):
            # Clean the content by removing HTML tags
            clean_content = re.sub(r"<[^>]+>", " ", content)
            clean_content = re.sub(r"\s+", " ", clean_content).strip()

            sections.append(
                {
                    "section_id": f"section_{i+1}",
                    "title": french_title.strip(),
                    "english_title": english_title.strip(),
                    "content": clean_content,
                    "raw_content": content.strip(),
                    "line_count": (
                        len(clean_content.split("\n")) if clean_content else 0
                    ),
                }
            )

        # If no structured sections found, try alternative parsing
        if not sections:
            # Look for h2, h3 headers as section dividers
            header_pattern = r"<h[23][^>]*>([^<]+)</h[23]>"
            headers = re.findall(header_pattern, html_content, re.IGNORECASE)

            if headers:
                # Split content by headers
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
                                "title": header.strip(),
                                "english_title": "",
                                "content": clean_content,
                                "raw_content": content.strip(),
                                "line_count": (
                                    len(clean_content.split("\n"))
                                    if clean_content
                                    else 0
                                ),
                            }
                        )

        # Extract full text content
        full_text = re.sub(r"<[^>]+>", " ", html_content)
        full_text = re.sub(r"\s+", " ", full_text).strip()

        return {
            "sections": sections,
            "full_text": full_text,
            "total_sections": len(sections),
            "document_language": (
                "fr"
                if any(
                    word in full_text.lower()
                    for word in ["le", "la", "les", "de", "du", "et"]
                )
                else "unknown"
            ),
        }

    def translate_cda_document(
        self, content: str, source_lang: str = None
    ) -> TranslationResult:
        """
        Translate a CDA document with medical terminology
        """
        if source_lang is None:
            source_lang = self.detect_language(content)

        target_lang = "en"

        # Parse the document structure
        parsed_doc = self.parse_html_cda(content)

        # Translate each section
        translated_sections = []
        total_medical_terms = 0

        for section in parsed_doc["sections"]:
            original_title = section["title"]
            original_content = section["content"]
            english_title = section.get("english_title", "")

            # Translate title and content
            translated_title = (
                self.translate_text(original_title, source_lang, target_lang)
                if original_title
                else ""
            )
            translated_content = self.translate_text(
                original_content, source_lang, target_lang
            )

            # Count medical terms found
            medical_terms_in_section = sum(
                1
                for term in self.medical_terms.keys()
                if term.lower() in original_content.lower()
            )
            total_medical_terms += medical_terms_in_section

            translated_sections.append(
                {
                    "section_id": section.get(
                        "section_id", f"section_{len(translated_sections)+1}"
                    ),
                    "title": original_title,
                    "translated_title": translated_title,
                    "english_title": english_title,
                    "original_content": original_content,
                    "translated_content": translated_content,
                    "medical_terms_count": medical_terms_in_section,
                    "line_count": section["line_count"],
                }
            )

        # Translate full document
        translated_full_text = self.translate_text(
            parsed_doc["full_text"], source_lang, target_lang
        )

        # Calculate translation quality (rough estimate)
        quality_score = min(
            1.0, total_medical_terms / max(1, len(parsed_doc["sections"]) * 2)
        )

        return TranslationResult(
            original_language=source_lang,
            target_language=target_lang,
            original_content=content,
            translated_content=translated_full_text,
            sections=translated_sections,
            translation_quality=quality_score,
            medical_terms_count=total_medical_terms,
        )


def test_luxembourg_cda():
    """
    Test the CDA translation with Luxembourg sample data
    """
    print("🏥 CDA Translation Test - Luxembourg Medical Documents")
    print("=" * 60)

    # Initialize translator
    translator = SimpleCDATranslator()

    # Test with Luxembourg HTML CDA file
    lu_html_file = (
        project_root / "test_data" / "eu_member_states" / "LU" / "DefaultXsltOutput.htm"
    )

    if not lu_html_file.exists():
        print(f"❌ Luxembourg CDA file not found: {lu_html_file}")
        return

    print(f"📄 Loading CDA document: {lu_html_file.name}")

    try:
        # Try UTF-8 first, fall back to other encodings
        encodings_to_try = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
        html_content = None

        for encoding in encodings_to_try:
            try:
                with open(lu_html_file, "r", encoding=encoding) as f:
                    html_content = f.read()
                print(f"✅ Successfully loaded with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue

        if html_content is None:
            print(f"❌ Could not read file with any encoding")
            return

        print(f"📊 Document size: {len(html_content):,} characters")

        # Translate the document
        result = translator.translate_cda_document(html_content)

        print(f"\n🌍 Language Detection:")
        print(f"   Source Language: {result.original_language.upper()}")
        print(f"   Target Language: {result.target_language.upper()}")

        print(f"\n📋 Translation Results:")
        print(f"   Sections Found: {len(result.sections)}")
        print(f"   Medical Terms Translated: {result.medical_terms_count}")
        print(f"   Translation Quality: {result.translation_quality:.1%}")

        print(f"\n📑 Document Sections:")
        for i, section in enumerate(result.sections, 1):
            print(f"   {i}. {section['title']}")
            if section.get("english_title"):
                print(f"      English: {section['english_title']}")
            print(
                f"      Lines: {section['line_count']}, Medical Terms: {section['medical_terms_count']}"
            )

            # Show a sample of original vs translated content
            original_sample = (
                section["original_content"][:150] + "..."
                if len(section["original_content"]) > 150
                else section["original_content"]
            )
            translated_sample = (
                section["translated_content"][:150] + "..."
                if len(section["translated_content"]) > 150
                else section["translated_content"]
            )

            print(f"      Original:   {original_sample}")
            print(f"      Translated: {translated_sample}")
            print()

        # Show full document preview
        print(f"\n📜 Document Preview (first 300 characters):")
        print(f"   Original:   {result.original_content[:300]}...")
        print(f"   Translated: {result.translated_content[:300]}...")

        print(f"\n✅ CDA Translation Test Completed Successfully!")
        print(f"   Ready for Django integration and enhanced UI display")

    except Exception as e:
        print(f"❌ Error during translation: {e}")
        import traceback

        traceback.print_exc()


def test_medical_terminology():
    """
    Test the medical terminology translation specifically
    """
    print("\n🔬 Medical Terminology Translation Test")
    print("=" * 50)

    translator = SimpleCDATranslator()

    # Test French medical phrases
    test_phrases = [
        "Le patient souffre de maladie du coeur et a besoin d'un traitement.",
        "Prescription: comprimé d'antibiotique, 3 fois par jour après les repas.",
        "Symptômes: fièvre, toux, et mal de tête depuis 3 jours.",
        "Examen médical: radiographie du poumon, analyse de sang.",
        "Antécédents: allergie aux anti-inflammatoires, diabète contrôlé.",
    ]

    for i, phrase in enumerate(test_phrases, 1):
        translated = translator.translate_text(phrase, "fr", "en")
        print(f"\n{i}. Original:   {phrase}")
        print(f"   Translated: {translated}")

    print(f"\n📊 Medical Dictionary Stats:")
    print(f"   Total Terms: {len(translator.medical_terms)}")
    print(f"   Categories: Anatomy, Conditions, Medications, Procedures")


if __name__ == "__main__":
    print("🚀 Starting CDA Translation System Test")
    print("🏥 EU NCP - Cross-Border Healthcare Document Translation")
    print()

    # Run medical terminology test
    test_medical_terminology()

    # Run Luxembourg CDA test
    test_luxembourg_cda()

    print(f"\n🎯 Next Steps:")
    print(f"   1. Integrate with Django views and templates")
    print(f"   2. Add bilingual side-by-side display")
    print(f"   3. Implement section-level translation toggles")
    print(f"   4. Add translation quality indicators")
    print(f"   5. Create export functionality (PDF, XML)")
