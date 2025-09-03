"""
EU Translation Library for Basic UI Terms
Provides translations for common form labels across all 27 EU member states
"""

from typing import Dict, Optional


class EUBasicUITranslations:
    """
    Translation library for basic UI terms used in healthcare forms
    Covers all 27 EU member state languages
    """

    def __init__(self):
        # Complete translation matrix for basic UI terms
        self.translations = {
            # NAME translations
            "name": {
                "bg": "Име",  # Bulgarian
                "cs": "Jméno",  # Czech
                "da": "Navn",  # Danish
                "de": "Name",  # German
                "el": "Όνομα",  # Greek
                "en": "Name",  # English
                "es": "Nombre",  # Spanish
                "et": "Nimi",  # Estonian
                "fi": "Nimi",  # Finnish
                "fr": "Nom",  # French
                "hr": "Ime",  # Croatian
                "hu": "Név",  # Hungarian
                "it": "Nome",  # Italian
                "lt": "Vardas",  # Lithuanian
                "lv": "Vārds",  # Latvian
                "mt": "Isem",  # Maltese
                "nl": "Naam",  # Dutch
                "pl": "Nazwa",  # Polish
                "pt": "Nome",  # Portuguese
                "ro": "Nume",  # Romanian
                "sk": "Meno",  # Slovak
                "sl": "Ime",  # Slovenian
                "sv": "Namn",  # Swedish
            },
            # ADDRESS translations
            "address": {
                "bg": "Адрес",  # Bulgarian
                "cs": "Adresa",  # Czech
                "da": "Adresse",  # Danish
                "de": "Adresse",  # German
                "el": "Διεύθυνση",  # Greek
                "en": "Address",  # English
                "es": "Dirección",  # Spanish
                "et": "Aadress",  # Estonian
                "fi": "Osoite",  # Finnish
                "fr": "Adresse",  # French
                "hr": "Adresa",  # Croatian
                "hu": "Cím",  # Hungarian
                "it": "Indirizzo",  # Italian
                "lt": "Adresas",  # Lithuanian
                "lv": "Adrese",  # Latvian
                "mt": "Indirizz",  # Maltese
                "nl": "Adres",  # Dutch
                "pl": "Adres",  # Polish
                "pt": "Endereço",  # Portuguese
                "ro": "Adresă",  # Romanian
                "sk": "Adresa",  # Slovak
                "sl": "Naslov",  # Slovenian
                "sv": "Adress",  # Swedish
            },
            # EMAIL translations
            "email": {
                "bg": "Имейл",  # Bulgarian
                "cs": "E-mail",  # Czech
                "da": "E-mail",  # Danish
                "de": "E-Mail",  # German
                "el": "Email",  # Greek
                "en": "Email",  # English
                "es": "Correo electrónico",  # Spanish
                "et": "E-post",  # Estonian
                "fi": "Sähköposti",  # Finnish
                "fr": "E-mail",  # French
                "hr": "E-pošta",  # Croatian
                "hu": "E-mail",  # Hungarian
                "it": "Email",  # Italian
                "lt": "El. paštas",  # Lithuanian
                "lv": "E-pasts",  # Latvian
                "mt": "Email",  # Maltese
                "nl": "E-mail",  # Dutch
                "pl": "E-mail",  # Polish
                "pt": "Email",  # Portuguese
                "ro": "Email",  # Romanian
                "sk": "E-mail",  # Slovak
                "sl": "E-pošta",  # Slovenian
                "sv": "E-post",  # Swedish
            },
            # PHONE translations
            "phone": {
                "bg": "Телефон",  # Bulgarian
                "cs": "Telefon",  # Czech
                "da": "Telefon",  # Danish
                "de": "Telefon",  # German
                "el": "Τηλέφωνο",  # Greek
                "en": "Phone",  # English
                "es": "Teléfono",  # Spanish
                "et": "Telefon",  # Estonian
                "fi": "Puhelin",  # Finnish
                "fr": "Téléphone",  # French
                "hr": "Telefon",  # Croatian
                "hu": "Telefon",  # Hungarian
                "it": "Telefono",  # Italian
                "lt": "Telefonas",  # Lithuanian
                "lv": "Tālrunis",  # Latvian
                "mt": "Telefown",  # Maltese
                "nl": "Telefoon",  # Dutch
                "pl": "Telefon",  # Polish
                "pt": "Telefone",  # Portuguese
                "ro": "Telefon",  # Romanian
                "sk": "Telefón",  # Slovak
                "sl": "Telefon",  # Slovenian
                "sv": "Telefon",  # Swedish
            },
            # CONTACT translations
            "contact": {
                "bg": "Контакт",  # Bulgarian
                "cs": "Kontakt",  # Czech
                "da": "Kontakt",  # Danish
                "de": "Kontakt",  # German
                "el": "Επικοινωνία",  # Greek
                "en": "Contact",  # English
                "es": "Contacto",  # Spanish
                "et": "Kontakt",  # Estonian
                "fi": "Yhteystieto",  # Finnish
                "fr": "Contact",  # French
                "hr": "Kontakt",  # Croatian
                "hu": "Kapcsolat",  # Hungarian
                "it": "Contatto",  # Italian
                "lt": "Kontaktas",  # Lithuanian
                "lv": "Kontakts",  # Latvian
                "mt": "Kuntatt",  # Maltese
                "nl": "Contact",  # Dutch
                "pl": "Kontakt",  # Polish
                "pt": "Contacto",  # Portuguese
                "ro": "Contact",  # Romanian
                "sk": "Kontakt",  # Slovak
                "sl": "Stik",  # Slovenian
                "sv": "Kontakt",  # Swedish
            },
            # ORGANIZATION translations
            "organization": {
                "bg": "Организация",  # Bulgarian
                "cs": "Organizace",  # Czech
                "da": "Organisation",  # Danish
                "de": "Organisation",  # German
                "el": "Οργανισμός",  # Greek
                "en": "Organization",  # English
                "es": "Organización",  # Spanish
                "et": "Organisatsioon",  # Estonian
                "fi": "Organisaatio",  # Finnish
                "fr": "Organisation",  # French
                "hr": "Organizacija",  # Croatian
                "hu": "Szervezet",  # Hungarian
                "it": "Organizzazione",  # Italian
                "lt": "Organizacija",  # Lithuanian
                "lv": "Organizācija",  # Latvian
                "mt": "Organizzazzjoni",  # Maltese
                "nl": "Organisatie",  # Dutch
                "pl": "Organizacja",  # Polish
                "pt": "Organização",  # Portuguese
                "ro": "Organizație",  # Romanian
                "sk": "Organizácia",  # Slovak
                "sl": "Organizacija",  # Slovenian
                "sv": "Organisation",  # Swedish
            },
            # INFORMATION translations
            "information": {
                "bg": "Информация",  # Bulgarian
                "cs": "Informace",  # Czech
                "da": "Information",  # Danish
                "de": "Information",  # German
                "el": "Πληροφορίες",  # Greek
                "en": "Information",  # English
                "es": "Información",  # Spanish
                "et": "Informatsioon",  # Estonian
                "fi": "Tieto",  # Finnish
                "fr": "Information",  # French
                "hr": "Informacije",  # Croatian
                "hu": "Információ",  # Hungarian
                "it": "Informazioni",  # Italian
                "lt": "Informacija",  # Lithuanian
                "lv": "Informācija",  # Latvian
                "mt": "Informazzjoni",  # Maltese
                "nl": "Informatie",  # Dutch
                "pl": "Informacja",  # Polish
                "pt": "Informação",  # Portuguese
                "ro": "Informații",  # Romanian
                "sk": "Informácie",  # Slovak
                "sl": "Informacije",  # Slovenian
                "sv": "Information",  # Swedish
            },
            # DETAILS translations
            "details": {
                "bg": "Детайли",  # Bulgarian
                "cs": "Podrobnosti",  # Czech
                "da": "Detaljer",  # Danish
                "de": "Details",  # German
                "el": "Λεπτομέρειες",  # Greek
                "en": "Details",  # English
                "es": "Detalles",  # Spanish
                "et": "Üksikasjad",  # Estonian
                "fi": "Tiedot",  # Finnish
                "fr": "Détails",  # French
                "hr": "Pojedinosti",  # Croatian
                "hu": "Részletek",  # Hungarian
                "it": "Dettagli",  # Italian
                "lt": "Išsamiau",  # Lithuanian
                "lv": "Sīkāka informācija",  # Latvian
                "mt": "Dettalji",  # Maltese
                "nl": "Details",  # Dutch
                "pl": "Szczegóły",  # Polish
                "pt": "Detalhes",  # Portuguese
                "ro": "Detalii",  # Romanian
                "sk": "Podrobnosti",  # Slovak
                "sl": "Podrobnosti",  # Slovenian
                "sv": "Detaljer",  # Swedish
            },
        }

    def get_translation(self, term: str, language: str) -> str:
        """
        Get translation for a basic UI term

        Args:
            term: UI term key (name, address, email, phone, etc.)
            language: ISO 639-1 language code

        Returns:
            Translated term or English fallback
        """
        term_lower = term.lower()

        if term_lower in self.translations:
            return self.translations[term_lower].get(
                language, self.translations[term_lower]["en"]
            )

        # Fallback to original term if not found
        return term

    def get_all_translations_for_language(self, language: str) -> Dict[str, str]:
        """
        Get all basic UI translations for a specific language

        Args:
            language: ISO 639-1 language code

        Returns:
            Dictionary of term -> translation mappings
        """
        result = {}
        for term, translations in self.translations.items():
            result[term] = translations.get(language, translations["en"])

        return result

    def get_supported_languages(self) -> list:
        """Get list of all supported EU languages"""
        return list(self.translations["name"].keys())


# Global instance for easy import
eu_ui_translations = EUBasicUITranslations()
