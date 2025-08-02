"""
Enhanced CDA Translation Service
Comprehensive translation service for CDA documents with section-by-section translation
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re
import logging
from django.utils.translation import gettext as _

from translation_services.terminology_translator import TerminologyTranslator
from translation_services.core import TranslationServiceFactory

logger = logging.getLogger(__name__)


@dataclass
class CDASection:
    """Represents a CDA document section with translation metadata"""
    section_id: str
    title: str
    original_title: str
    content: str
    original_content: str
    narrative_text: str
    original_narrative: str
    codes: List[Dict]
    translated_codes: List[Dict]
    translation_status: str  # 'original', 'translated', 'partial', 'failed'
    subsections: List['CDASection'] = None


@dataclass
class TranslatedCDADocument:
    """Complete translated CDA document structure"""
    document_id: str
    patient_info: Dict
    header_info: Dict
    sections: List[CDASection]
    terminology_translations: Dict
    translation_summary: Dict
    original_xml: str
    translated_xml: str
    translation_quality: str


class EnhancedCDATranslationService:
    """
    Enhanced CDA translation service providing comprehensive document translation
    including clinical sections, terminology, and narrative text
    """

    def __init__(self, target_language: str = "en"):
        self.target_language = target_language
        self.terminology_translator = TerminologyTranslator(target_language)
        self.translation_service = TranslationServiceFactory.get_cda_translation_service()
        
        # CDA namespaces for XML parsing
        self.namespaces = {
            'cda': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    def translate_cda_document(self, xml_content: str, source_language: str = "fr") -> TranslatedCDADocument:
        """
        Translate complete CDA document with section-by-section analysis
        
        Args:
            xml_content: Original CDA XML content
            source_language: Source language code
            
        Returns:
            TranslatedCDADocument with complete translation information
        """
        try:
            # Parse XML content
            root = ET.fromstring(xml_content)
            
            # Extract document structure
            document_id = self._extract_document_id(root)
            patient_info = self._extract_patient_info(root)
            header_info = self._extract_header_info(root)
            
            # Extract and translate sections
            sections = self._extract_and_translate_sections(root, source_language)
            
            # Get terminology translations
            terminology_translations = self._get_terminology_translations(sections)
            
            # Generate translation summary
            translation_summary = self._generate_translation_summary(sections, terminology_translations)
            
            # Generate translated XML (if needed)
            translated_xml = self._generate_translated_xml(root, sections)
            
            return TranslatedCDADocument(
                document_id=document_id,
                patient_info=patient_info,
                header_info=header_info,
                sections=sections,
                terminology_translations=terminology_translations,
                translation_summary=translation_summary,
                original_xml=xml_content,
                translated_xml=translated_xml,
                translation_quality=self._assess_translation_quality(translation_summary)
            )
            
        except Exception as e:
            logger.error(f"Error translating CDA document: {e}")
            raise

    def _extract_document_id(self, root: ET.Element) -> str:
        """Extract document ID from CDA header"""
        try:
            id_elem = root.find('.//cda:id', self.namespaces)
            if id_elem is not None:
                return id_elem.get('extension', 'unknown')
            return 'unknown'
        except Exception as e:
            logger.warning(f"Could not extract document ID: {e}")
            return 'unknown'

    def _extract_patient_info(self, root: ET.Element) -> Dict:
        """Extract patient information from CDA header"""
        try:
            patient_info = {}
            
            # Patient name
            name_elem = root.find('.//cda:patient/cda:name', self.namespaces)
            if name_elem is not None:
                given = name_elem.find('cda:given', self.namespaces)
                family = name_elem.find('cda:family', self.namespaces)
                patient_info['name'] = f"{given.text if given is not None else ''} {family.text if family is not None else ''}".strip()
            
            # Birth date
            birth_elem = root.find('.//cda:patient/cda:birthTime', self.namespaces)
            if birth_elem is not None:
                patient_info['birth_date'] = birth_elem.get('value', '')
            
            # Gender
            gender_elem = root.find('.//cda:patient/cda:administrativeGenderCode', self.namespaces)
            if gender_elem is not None:
                patient_info['gender'] = gender_elem.get('displayName', gender_elem.get('code', ''))
            
            return patient_info
            
        except Exception as e:
            logger.warning(f"Could not extract patient info: {e}")
            return {}

    def _extract_header_info(self, root: ET.Element) -> Dict:
        """Extract document header information"""
        try:
            header_info = {}
            
            # Title
            title_elem = root.find('.//cda:title', self.namespaces)
            if title_elem is not None:
                header_info['title'] = title_elem.text
            
            # Creation date
            date_elem = root.find('.//cda:effectiveTime', self.namespaces)
            if date_elem is not None:
                header_info['creation_date'] = date_elem.get('value', '')
            
            # Author
            author_elem = root.find('.//cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name', self.namespaces)
            if author_elem is not None:
                given = author_elem.find('cda:given', self.namespaces)
                family = author_elem.find('cda:family', self.namespaces)
                header_info['author'] = f"{given.text if given is not None else ''} {family.text if family is not None else ''}".strip()
            
            return header_info
            
        except Exception as e:
            logger.warning(f"Could not extract header info: {e}")
            return {}

    def _extract_and_translate_sections(self, root: ET.Element, source_language: str) -> List[CDASection]:
        """Extract all CDA sections and translate them"""
        sections = []
        
        try:
            # Find all section elements
            section_elements = root.findall('.//cda:section', self.namespaces)
            
            for i, section_elem in enumerate(section_elements):
                section = self._parse_section(section_elem, f"section_{i}", source_language)
                if section:
                    sections.append(section)
                    
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
        
        return sections

    def _parse_section(self, section_elem: ET.Element, section_id: str, source_language: str) -> Optional[CDASection]:
        """Parse individual CDA section"""
        try:
            # Extract title
            title_elem = section_elem.find('cda:title', self.namespaces)
            original_title = title_elem.text if title_elem is not None else "Untitled Section"
            
            # Extract narrative text
            text_elem = section_elem.find('cda:text', self.namespaces)
            original_narrative = self._extract_narrative_text(text_elem) if text_elem is not None else ""
            
            # Extract codes
            codes = self._extract_section_codes(section_elem)
            
            # Translate title
            translated_title = self._translate_text(original_title, source_language)
            
            # Translate narrative
            translated_narrative = self._translate_narrative(original_narrative, source_language)
            
            # Translate terminology codes
            translated_codes = self._translate_section_codes(codes)
            
            # Determine translation status
            translation_status = self._determine_translation_status(
                original_title, translated_title,
                original_narrative, translated_narrative,
                codes, translated_codes
            )
            
            return CDASection(
                section_id=section_id,
                title=translated_title,
                original_title=original_title,
                content=translated_narrative,
                original_content=original_narrative,
                narrative_text=translated_narrative,
                original_narrative=original_narrative,
                codes=codes,
                translated_codes=translated_codes,
                translation_status=translation_status
            )
            
        except Exception as e:
            logger.error(f"Error parsing section {section_id}: {e}")
            return None

    def _extract_narrative_text(self, text_elem: ET.Element) -> str:
        """Extract narrative text from CDA text element"""
        try:
            # Handle different CDA text structures
            if text_elem.text:
                return text_elem.text.strip()
            
            # Handle structured text (tables, lists, etc.)
            narrative_parts = []
            for elem in text_elem.iter():
                if elem.text and elem.text.strip():
                    narrative_parts.append(elem.text.strip())
                if elem.tail and elem.tail.strip():
                    narrative_parts.append(elem.tail.strip())
            
            return ' '.join(narrative_parts)
            
        except Exception as e:
            logger.warning(f"Error extracting narrative text: {e}")
            return ""

    def _extract_section_codes(self, section_elem: ET.Element) -> List[Dict]:
        """Extract coding information from section"""
        codes = []
        
        try:
            # Extract section code
            code_elem = section_elem.find('cda:code', self.namespaces)
            if code_elem is not None:
                codes.append({
                    'system': code_elem.get('codeSystem', ''),
                    'code': code_elem.get('code', ''),
                    'display': code_elem.get('displayName', ''),
                    'type': 'section_code'
                })
            
            # Extract entry codes
            entry_codes = section_elem.findall('.//cda:code', self.namespaces)
            for code_elem in entry_codes:
                codes.append({
                    'system': code_elem.get('codeSystem', ''),
                    'code': code_elem.get('code', ''),
                    'display': code_elem.get('displayName', ''),
                    'type': 'entry_code'
                })
                
        except Exception as e:
            logger.warning(f"Error extracting section codes: {e}")
        
        return codes

    def _translate_text(self, text: str, source_language: str) -> str:
        """Translate general text content"""
        # Implement basic text translation
        # This could integrate with Google Translate, Azure Translator, etc.
        if self.target_language == source_language:
            return text
        
        # For now, return with translation marker
        return f"[{self.target_language.upper()}] {text}"

    def _translate_narrative(self, narrative: str, source_language: str) -> str:
        """Translate narrative text while preserving clinical context"""
        if not narrative or self.target_language == source_language:
            return narrative
        
        # Apply terminology translation first
        terminology_result = self.terminology_translator.translate_clinical_document(
            narrative, source_language
        )
        
        # Then apply general text translation
        translated_text = self._translate_text(terminology_result['content'], source_language)
        
        return translated_text

    def _translate_section_codes(self, codes: List[Dict]) -> List[Dict]:
        """Translate terminology codes using terminology translator"""
        translated_codes = []
        
        for code in codes:
            translated_code = code.copy()
            
            if code.get('code') and code.get('system'):
                translation = self.terminology_translator._translate_term(
                    code=code['code'],
                    system=code['system'],
                    original_display=code.get('display')
                )
                
                if translation:
                    translated_code.update({
                        'translated_display': translation['display'],
                        'translation_quality': translation['quality'],
                        'translation_source': translation['source']
                    })
            
            translated_codes.append(translated_code)
        
        return translated_codes

    def _determine_translation_status(self, orig_title: str, trans_title: str,
                                    orig_narrative: str, trans_narrative: str,
                                    orig_codes: List[Dict], trans_codes: List[Dict]) -> str:
        """Determine overall translation status for section"""
        
        if self.target_language == 'en':  # Assuming source is English
            return 'original'
        
        # Check if any translations were applied
        has_title_translation = orig_title != trans_title
        has_narrative_translation = orig_narrative != trans_narrative
        has_code_translations = any(
            'translated_display' in code for code in trans_codes
        )
        
        if has_title_translation or has_narrative_translation or has_code_translations:
            if all([has_title_translation, has_narrative_translation, has_code_translations]):
                return 'translated'
            else:
                return 'partial'
        
        return 'failed'

    def _get_terminology_translations(self, sections: List[CDASection]) -> Dict:
        """Collect all terminology translations from sections"""
        terminology_translations = {}
        
        for section in sections:
            for code in section.translated_codes:
                if 'translated_display' in code:
                    key = f"{code.get('system', '')}#{code.get('code', '')}"
                    terminology_translations[key] = {
                        'original': code.get('display', ''),
                        'translated': code.get('translated_display', ''),
                        'quality': code.get('translation_quality', ''),
                        'source': code.get('translation_source', '')
                    }
        
        return terminology_translations

    def _generate_translation_summary(self, sections: List[CDASection], 
                                    terminology_translations: Dict) -> Dict:
        """Generate summary of translation activities"""
        total_sections = len(sections)
        translated_sections = len([s for s in sections if s.translation_status == 'translated'])
        partial_sections = len([s for s in sections if s.translation_status == 'partial'])
        failed_sections = len([s for s in sections if s.translation_status == 'failed'])
        
        return {
            'total_sections': total_sections,
            'translated_sections': translated_sections,
            'partial_sections': partial_sections,
            'failed_sections': failed_sections,
            'terminology_translations': len(terminology_translations),
            'translation_coverage': (translated_sections + partial_sections) / total_sections if total_sections > 0 else 0,
            'target_language': self.target_language
        }

    def _generate_translated_xml(self, root: ET.Element, sections: List[CDASection]) -> str:
        """Generate translated XML document (optional)"""
        # This would involve rebuilding the XML with translated content
        # For now, return original XML with translation metadata
        return ET.tostring(root, encoding='unicode')

    def _assess_translation_quality(self, translation_summary: Dict) -> str:
        """Assess overall translation quality"""
        coverage = translation_summary.get('translation_coverage', 0)
        
        if coverage >= 0.9:
            return 'excellent'
        elif coverage >= 0.7:
            return 'good'
        elif coverage >= 0.5:
            return 'fair'
        else:
            return 'poor'
