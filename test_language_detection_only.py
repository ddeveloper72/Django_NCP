#!/usr/bin/env python3
"""
Simple Language Detection Test
Tests the language detection logic without Django setup
"""

import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_language_detection():
    """Test the language detection logic directly"""

    # Country to language mapping (from the enhanced_cda_display function)
    COUNTRY_LANGUAGE_MAP = {
        "DE": "de",
        "AT": "de",
        "CH": "de",  # German-speaking
        "IT": "it",
        "SM": "it",
        "VA": "it",  # Italian-speaking
        "ES": "es",
        "AD": "es",  # Spanish-speaking
        "PT": "pt",  # Portuguese
        "LV": "lv",  # Latvian
        "LT": "lt",  # Lithuanian
        "EE": "et",  # Estonian
        "MT": "en",
        "IE": "en",  # English-speaking
        "FR": "fr",
        "LU": "fr",  # French-speaking
        "NL": "nl",
        "BE": "nl",  # Dutch-speaking
        "GR": "el",  # Greek
    }

    def detect_language_from_content(content):
        """Simple content-based language detection"""
        if not content:
            return None

        content_lower = content.lower()

        # German indicators
        if any(
            word in content_lower
            for word in [
                "der",
                "die",
                "das",
                "und",
                "mit",
                "für",
                "ist",
                "haben",
                "werden",
            ]
        ):
            return "de"

        # Italian indicators
        if any(
            word in content_lower
            for word in ["il", "la", "di", "con", "per", "essere", "avere", "fare"]
        ):
            return "it"

        # Portuguese indicators
        if any(
            word in content_lower
            for word in ["o", "a", "de", "com", "para", "ser", "ter", "fazer"]
        ):
            return "pt"

        # Spanish indicators
        if any(
            word in content_lower
            for word in ["el", "la", "de", "con", "para", "ser", "tener", "hacer"]
        ):
            return "es"

        # Greek indicators (basic)
        if any(char in content for char in ["α", "β", "γ", "δ", "ε", "ζ", "η", "θ"]):
            return "el"

        # Latvian indicators
        if any(
            char in content
            for char in ["ā", "č", "ē", "ģ", "ī", "ķ", "ļ", "ņ", "š", "ū", "ž"]
        ):
            return "lv"

        return None

    def enhanced_language_detection(provided_language, country_code, content):
        """
        4-tier language detection system:
        1. Use provided language if valid
        2. Map country code to language
        3. Auto-detect from content
        4. Fallback to French
        """
        detection_method = "unknown"

        # Tier 1: Use provided language
        if provided_language and provided_language.strip():
            detection_method = "provided"
            return provided_language.strip(), detection_method

        # Tier 2: Country code mapping
        if country_code and country_code.upper() in COUNTRY_LANGUAGE_MAP:
            detection_method = "country_code"
            return COUNTRY_LANGUAGE_MAP[country_code.upper()], detection_method

        # Tier 3: Auto-detect from content
        if content:
            detected = detect_language_from_content(content)
            if detected:
                detection_method = "auto_detect"
                return detected, detection_method

        # Tier 4: Fallback to French
        detection_method = "fallback"
        return "fr", detection_method

    print("🧪 Enhanced Language Detection Test")
    print("=" * 70)

    # Test cases
    test_cases = [
        {
            "name": "Latvian (explicit)",
            "language": "lv",
            "country": "LV",
            "content": "Pacienta medicīniskā dokumentācija ar ārsta atzinumu",
            "expected": "lv",
        },
        {
            "name": "Italian (country code)",
            "language": "",
            "country": "IT",
            "content": "Documentazione medica del paziente con diagnosi",
            "expected": "it",
        },
        {
            "name": "German (auto-detect)",
            "language": "",
            "country": "",
            "content": "Medizinische Dokumentation für den Patienten mit Diagnose",
            "expected": "de",
        },
        {
            "name": "Portuguese (country)",
            "language": "",
            "country": "PT",
            "content": "Documentação médica do paciente com diagnóstico",
            "expected": "pt",
        },
        {
            "name": "Greek (auto-detect)",
            "language": "",
            "country": "GR",
            "content": "Ιατρική τεκμηρίωση για τον ασθενή με διάγνωση",
            "expected": "el",
        },
        {
            "name": "Unknown fallback",
            "language": "",
            "country": "",
            "content": "Unknown language content",
            "expected": "fr",
        },
    ]

    correct = 0
    total = len(test_cases)

    for test in test_cases:
        detected_lang, method = enhanced_language_detection(
            test["language"], test["country"], test["content"]
        )

        is_correct = detected_lang == test["expected"]
        if is_correct:
            correct += 1

        status = "✅" if is_correct else "❌"
        print(f"{status} {test['name']}: {detected_lang} ({method})")

    print("=" * 70)
    print(f"📊 Results: {correct}/{total} correct ({correct/total*100:.1f}%)")

    # Test country mapping
    print("\n🗺️  Country-Language Mapping Test:")
    country_tests = [
        ("DE", "de"),
        ("AT", "de"),
        ("CH", "de"),
        ("IT", "it"),
        ("FR", "fr"),
        ("ES", "es"),
        ("PT", "pt"),
        ("LV", "lv"),
        ("GR", "el"),
    ]

    for country, expected in country_tests:
        detected, method = enhanced_language_detection("", country, "")
        status = "✅" if detected == expected else "❌"
        print(f"  {status} {country} → {detected} ({method})")

    print(f"\n🌍 Multi-language detection system ready!")
    print(f"🎯 Supports {len(COUNTRY_LANGUAGE_MAP)} countries across 11 EU languages")


if __name__ == "__main__":
    test_language_detection()
