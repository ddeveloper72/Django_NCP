#!/usr/bin/env python
"""Analyze remaining hardcoded strings and assess translation needs"""

import re


def analyze_hardcoded_strings():
    with open(
        "templates/jinja2/patient_data/patient_cda.html", "r", encoding="utf-8"
    ) as f:
        content = f.read()

    # Find hardcoded patterns
    patterns = [
        (r'\b(Name|Address|Email|Phone)\b(?!["\']|\s*[|}])', "Basic Labels"),
        (r">\s*[A-Z][a-z]+\s*<", "HTML Content"),
        (r'\b(Contact|Information|Details)\b(?!["\']|\s*[|}])', "Information Labels"),
    ]

    all_violations = {}

    for pattern, category in patterns:
        violations = []
        matches = re.finditer(pattern, content)
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            line_start = content.rfind("\n", 0, match.start()) + 1
            line_end = content.find("\n", match.end())
            if line_end == -1:
                line_end = len(content)
            line = content[line_start:line_end].strip()

            # Skip if already wrapped in template translation
            if "template_translations" not in line:
                violations.append((line_num, match.group().strip(), line))

        if violations:
            all_violations[category] = violations

    return all_violations


def print_analysis():
    violations = analyze_hardcoded_strings()

    print("HARDCODED STRING ANALYSIS")
    print("=" * 50)

    unique_terms = set()
    total_count = 0

    for category, items in violations.items():
        print(f"\n{category}:")
        print("-" * 20)
        for line_num, term, context in items[:5]:  # Show first 5
            print(f"  Line {line_num}: '{term}'")
            unique_terms.add(term.lower())
            total_count += 1

        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")
            total_count += len(items) - 5

    print(f"\nSUMMARY:")
    print(f"Total violations: {total_count}")
    print(f"Unique terms: {sorted(unique_terms)}")

    return unique_terms


if __name__ == "__main__":
    unique_terms = print_analysis()

    # EU language analysis
    print(f"\nEU TRANSLATION REQUIREMENTS:")
    print("=" * 50)

    # Common EU translations for these basic terms
    basic_translations = {
        "name": {
            "de": "Name",
            "fr": "Nom",
            "es": "Nombre",
            "it": "Nome",
            "nl": "Naam",
            "pl": "Nazwa",
            "cs": "Jméno",
            "hu": "Név",
            "lv": "Vārds",
            "pt": "Nome",
            "ro": "Nume",
            "sv": "Namn",
        },
        "address": {
            "de": "Adresse",
            "fr": "Adresse",
            "es": "Dirección",
            "it": "Indirizzo",
            "nl": "Adres",
            "pl": "Adres",
            "cs": "Adresa",
            "hu": "Cím",
            "lv": "Adrese",
            "pt": "Endereço",
            "ro": "Adresă",
            "sv": "Adress",
        },
        "email": {
            "de": "E-Mail",
            "fr": "E-mail",
            "es": "Correo electrónico",
            "it": "Email",
            "nl": "E-mail",
            "pl": "E-mail",
            "cs": "E-mail",
            "hu": "E-mail",
            "lv": "E-pasts",
            "pt": "Email",
            "ro": "Email",
            "sv": "E-post",
        },
        "phone": {
            "de": "Telefon",
            "fr": "Téléphone",
            "es": "Teléfono",
            "it": "Telefono",
            "nl": "Telefoon",
            "pl": "Telefon",
            "cs": "Telefon",
            "hu": "Telefon",
            "lv": "Tālrunis",
            "pt": "Telefone",
            "ro": "Telefon",
            "sv": "Telefon",
        },
    }

    print("Required translations for basic UI terms:")
    for term in sorted(unique_terms):
        if term in basic_translations:
            print(f"\n{term.upper()}:")
            for lang, translation in basic_translations[term].items():
                print(f"  {lang}: {translation}")
        else:
            print(f"\n{term.upper()}: (needs research)")
