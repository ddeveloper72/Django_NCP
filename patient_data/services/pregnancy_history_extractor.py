# patient_data/services/pregnancy_history_extractor.py

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CurrentPregnancyStatus:
    """Current pregnancy status information"""
    observation_date: str = ""
    pregnancy_status: str = ""
    pregnancy_status_code: str = ""
    pregnancy_status_code_system: str = ""
    delivery_date_estimated: str = ""
    effective_time: str = ""
    
@dataclass 
class PreviousPregnancyHistory:
    """Individual previous pregnancy record"""
    outcome: str = ""
    outcome_code: str = ""
    outcome_code_system: str = ""
    number: int = 0
    outcome_dates: List[str] = None
    effective_time: str = ""
    
    def __post_init__(self):
        if self.outcome_dates is None:
            self.outcome_dates = []

@dataclass
class PregnancyOverview:
    """Overview of all pregnancy outcomes"""
    outcome: str = ""
    outcome_code: str = ""
    outcome_code_system: str = ""
    outcome_dates: List[str] = None
    total_count: int = 0
    
    def __post_init__(self):
        if self.outcome_dates is None:
            self.outcome_dates = []

@dataclass
class PregnancyHistoryData:
    """Complete pregnancy history data structure"""
    current_pregnancy: Optional[CurrentPregnancyStatus] = None
    previous_pregnancies: List[PreviousPregnancyHistory] = None
    pregnancy_overview: List[PregnancyOverview] = None
    
    def __post_init__(self):
        if self.previous_pregnancies is None:
            self.previous_pregnancies = []
        if self.pregnancy_overview is None:
            self.pregnancy_overview = []

class PregnancyHistoryExtractor:
    """Extracts comprehensive pregnancy history data from CDA documents"""
    
    def __init__(self):
        # Define XML namespace mappings for CDA parsing
        self.namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Clinical codes for pregnancy-related observations
        self.pregnancy_codes = {
            # Current pregnancy status
            "82810-3": "pregnancy_status",  # Pregnancy status
            "11778-8": "delivery_date_estimated",  # Delivery date estimated
            "77386006": "pregnant",  # Pregnant (SNOMED)
            
            # Previous pregnancy outcomes
            "281050002": "livebirth",  # Livebirth (SNOMED)
            "57797005": "termination",  # Termination of pregnancy (SNOMED)
            "93857-1": "pregnancy_outcome_date",  # Pregnancy outcome date
            
            # Additional outcome codes
            "237364002": "stillbirth",  # Stillbirth (SNOMED)
            "17369002": "miscarriage",  # Miscarriage (SNOMED)
        }
    
    def extract_pregnancy_history(self, cda_content: str) -> PregnancyHistoryData:
        """
        Extract complete pregnancy history data from CDA XML
        
        Args:
            cda_content (str): Raw CDA XML content
            
        Returns:
            PregnancyHistoryData: Comprehensive pregnancy history structure
        """
        try:
            root = ET.fromstring(cda_content)
            
            # Find the pregnancy history section using LOINC code
            # History of pregnancies section code: 10162-6
            # Use a more robust approach to find the section
            pregnancy_section = None
            sections = root.findall(".//hl7:section", self.namespaces)
            
            for section in sections:
                code_elem = section.find("hl7:code", self.namespaces)
                if code_elem is not None and code_elem.get("code") == "10162-6":
                    pregnancy_section = section
                    break
            
            if pregnancy_section is None:
                logger.info("No Pregnancy History section found")
                return PregnancyHistoryData()
            
            # Extract data for all three tabs
            current_pregnancy = self._extract_current_pregnancy(pregnancy_section)
            previous_pregnancies = self._extract_previous_pregnancies(pregnancy_section)
            pregnancy_overview = self._extract_pregnancy_overview(pregnancy_section)
            
            result = PregnancyHistoryData(
                current_pregnancy=current_pregnancy,
                previous_pregnancies=previous_pregnancies,
                pregnancy_overview=pregnancy_overview
            )
            
            total_entries = len(previous_pregnancies) + len(pregnancy_overview)
            if current_pregnancy:
                total_entries += 1
                
            logger.info(f"Successfully extracted pregnancy history: {total_entries} total entries")
            return result
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in pregnancy history extraction: {e}")
            return PregnancyHistoryData()
        except Exception as e:
            logger.error(f"Unexpected error in pregnancy history extraction: {e}")
            return PregnancyHistoryData()
    
    def _extract_current_pregnancy(self, section) -> Optional[CurrentPregnancyStatus]:
        """Extract current pregnancy status data"""
        try:
            # Look for current pregnancy status entry (code 82810-3)
            current_obs = None
            entries = section.findall(".//hl7:entry", self.namespaces)
            
            for entry in entries:
                obs = entry.find(".//hl7:observation", self.namespaces)
                if obs is not None:
                    code_elem = obs.find("hl7:code", self.namespaces)
                    if code_elem is not None and code_elem.get("code") == "82810-3":
                        current_obs = obs
                        break
            
            if current_obs is None:
                return None
            
            # Extract observation date
            observation_date = self._extract_effective_time(current_obs)
            
            # Extract pregnancy status from value element
            pregnancy_status = ""
            pregnancy_status_code = ""
            pregnancy_status_code_system = ""
            
            value_elem = current_obs.find("hl7:value", self.namespaces)
            if value_elem is not None:
                pregnancy_status = value_elem.get("displayName", "")
                pregnancy_status_code = value_elem.get("code", "")
                pregnancy_status_code_system = value_elem.get("codeSystem", "")
            
            # Extract delivery date estimated from nested entryRelationship
            delivery_date = ""
            entry_rel = current_obs.find(".//hl7:entryRelationship/hl7:observation", self.namespaces)
            if entry_rel is not None:
                code_elem = entry_rel.find("hl7:code", self.namespaces)
                if code_elem is not None and code_elem.get("code") == "11778-8":
                    delivery_value = entry_rel.find("hl7:value", self.namespaces)
                    if delivery_value is not None:
                        delivery_date = delivery_value.get("value", "")
            
            return CurrentPregnancyStatus(
                observation_date=self._format_date(observation_date),
                pregnancy_status=pregnancy_status,
                pregnancy_status_code=pregnancy_status_code,
                pregnancy_status_code_system=pregnancy_status_code_system,
                delivery_date_estimated=self._format_date(delivery_date),
                effective_time=observation_date
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract current pregnancy status: {e}")
            return None
    
    def _extract_previous_pregnancies(self, section) -> List[PreviousPregnancyHistory]:
        """Extract previous pregnancy history records"""
        try:
            pregnancies = []
            
            # Look for pregnancy outcome entries
            outcome_codes = ["281050002", "57797005", "237364002", "17369002"]  # livebirth, termination, stillbirth, miscarriage
            entries = section.findall(".//hl7:entry", self.namespaces)
            
            for entry in entries:
                obs = entry.find(".//hl7:observation", self.namespaces)
                if obs is not None:
                    code_elem = obs.find("hl7:code", self.namespaces)
                    if code_elem is not None:
                        code = code_elem.get("code", "")
                        if code in outcome_codes:
                            pregnancy = self._extract_single_pregnancy_outcome(obs, code)
                            if pregnancy:
                                pregnancies.append(pregnancy)
            
            # Associate dates with pregnancy outcomes
            pregnancies = self._associate_outcome_dates_properly(section, pregnancies)
            
            # Group pregnancies by outcome type and aggregate counts
            pregnancies = self._group_and_aggregate_pregnancies(pregnancies)
            
            logger.info(f"Extracted {len(pregnancies)} previous pregnancy records")
            return pregnancies
            
        except Exception as e:
            logger.warning(f"Failed to extract previous pregnancies: {e}")
            return []
    
    def _extract_single_pregnancy_outcome(self, obs_element, outcome_code: str) -> Optional[PreviousPregnancyHistory]:
        """Extract data from a single pregnancy outcome observation"""
        try:
            # Get outcome name from code
            outcome = self._get_outcome_name(outcome_code)
            
            # Extract number from value element
            number = 0
            value_elem = obs_element.find("hl7:value", self.namespaces)
            if value_elem is not None and value_elem.get("value"):
                try:
                    number = int(value_elem.get("value", "0"))
                except ValueError:
                    number = 0
            
            # Extract effective time from this observation
            effective_time = self._extract_effective_time(obs_element)
            
            # Get code system information
            code_elem = obs_element.find("hl7:code", self.namespaces)
            code_system = code_elem.get("codeSystem", "") if code_elem is not None else ""
            
            # For now, return without dates - dates will be added by section-level processing
            outcome_dates = []
            
            return PreviousPregnancyHistory(
                outcome=outcome,
                outcome_code=outcome_code,
                outcome_code_system=code_system,
                number=number,
                outcome_dates=outcome_dates,  # Will be populated by _associate_outcome_dates_properly
                effective_time=effective_time
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract single pregnancy outcome: {e}")
            return None
    
    def _extract_pregnancy_overview(self, section) -> List[PregnancyOverview]:
        """Extract pregnancy overview data by aggregating all outcome types"""
        try:
            overview = []
            
            # First get all outcome counts
            outcome_codes = ["281050002", "57797005", "237364002", "17369002"]  # livebirth, termination, stillbirth, miscarriage
            entries = section.findall(".//hl7:entry", self.namespaces)
            
            # Collect all individual pregnancy outcomes
            individual_outcomes = []
            for entry in entries:
                obs = entry.find(".//hl7:observation", self.namespaces)
                if obs is not None:
                    code_elem = obs.find("hl7:code", self.namespaces)
                    if code_elem is not None:
                        code = code_elem.get("code", "")
                        if code in outcome_codes:
                            pregnancy = self._extract_single_pregnancy_outcome(obs, code)
                            if pregnancy:
                                individual_outcomes.append(pregnancy)
            
            # Associate dates properly
            individual_outcomes = self._associate_outcome_dates_properly(section, individual_outcomes)
            
            # Group by outcome type for overview
            grouped_overview = {}
            for pregnancy in individual_outcomes:
                outcome_key = pregnancy.outcome
                if outcome_key not in grouped_overview:
                    grouped_overview[outcome_key] = {
                        'outcome': pregnancy.outcome,
                        'outcome_code': pregnancy.outcome_code,
                        'outcome_code_system': pregnancy.outcome_code_system,
                        'dates': [],
                        'count': 0
                    }
                
                # Add the dates from this specific pregnancy
                if pregnancy.outcome_dates:
                    grouped_overview[outcome_key]['dates'].extend(pregnancy.outcome_dates)
                
                # Add to count
                grouped_overview[outcome_key]['count'] += max(1, pregnancy.number)
            
            # Convert to PregnancyOverview objects
            for group_data in grouped_overview.values():
                # Remove duplicates and sort dates
                unique_dates = list(set(group_data['dates']))
                unique_dates.sort()
                
                overview_entry = PregnancyOverview(
                    outcome=group_data['outcome'],
                    outcome_code=group_data['outcome_code'],
                    outcome_code_system=group_data['outcome_code_system'],
                    outcome_dates=unique_dates,
                    total_count=group_data['count']
                )
                overview.append(overview_entry)
            
            logger.info(f"Created {len(overview)} pregnancy overview entries")
            return overview
            
        except Exception as e:
            logger.warning(f"Failed to extract pregnancy overview: {e}")
            return []
    
    def _group_and_aggregate_pregnancies(self, pregnancies: List[PreviousPregnancyHistory]) -> List[PreviousPregnancyHistory]:
        """Group pregnancies by outcome type and aggregate their dates and counts"""
        if not pregnancies:
            return []
        
        # Group by outcome type
        grouped = {}
        for pregnancy in pregnancies:
            outcome_key = pregnancy.outcome
            if outcome_key not in grouped:
                grouped[outcome_key] = {
                    'outcome': pregnancy.outcome,
                    'outcome_code': pregnancy.outcome_code,
                    'outcome_code_system': pregnancy.outcome_code_system,
                    'dates': [],
                    'count': 0
                }
            
            # Add the date from this specific pregnancy
            if pregnancy.outcome_dates:
                grouped[outcome_key]['dates'].extend(pregnancy.outcome_dates)
            
            # Add to count
            grouped[outcome_key]['count'] += max(1, pregnancy.number)
        
        # Convert back to PreviousPregnancyHistory objects
        result = []
        for group_data in grouped.values():
            # Remove duplicates and sort dates
            unique_dates = list(set(group_data['dates']))
            unique_dates.sort()
            
            pregnancy = PreviousPregnancyHistory(
                outcome=group_data['outcome'],
                outcome_code=group_data['outcome_code'],
                outcome_code_system=group_data['outcome_code_system'],
                number=group_data['count'],
                outcome_dates=unique_dates,
                effective_time=""  # Not relevant for aggregated data
            )
            result.append(pregnancy)
        
        return result

    def _associate_outcome_dates_properly(self, section, pregnancies: List[PreviousPregnancyHistory]) -> List[PreviousPregnancyHistory]:
        """Properly associate outcome dates with pregnancy records based on outcome type"""
        try:
            # Find all date observations (code 93857-1)
            entries = section.findall(".//hl7:entry", self.namespaces)
            date_observations = []
            
            for entry in entries:
                obs = entry.find(".//hl7:observation", self.namespaces)
                if obs is not None:
                    code_elem = obs.find("hl7:code", self.namespaces)
                    if code_elem is not None and code_elem.get("code") == "93857-1":
                        # Extract date from effectiveTime
                        effective_time = self._extract_effective_time(obs)
                        if effective_time:
                            # Extract outcome code from value element
                            value_elem = obs.find("hl7:value", self.namespaces)
                            if value_elem is not None:
                                outcome_code = value_elem.get("code", "")
                                if outcome_code:
                                    date_observations.append({
                                        'outcome_code': outcome_code,
                                        'date': self._format_date(effective_time)
                                    })
            
            # Associate dates with pregnancies based on outcome code
            for pregnancy in pregnancies:
                pregnancy.outcome_dates = []
                for date_obs in date_observations:
                    if date_obs['outcome_code'] == pregnancy.outcome_code and date_obs['date']:
                        pregnancy.outcome_dates.append(date_obs['date'])
            
            logger.info(f"Associated dates for {len(pregnancies)} pregnancy outcomes")
            return pregnancies
            
        except Exception as e:
            logger.warning(f"Failed to associate outcome dates: {e}")
            return pregnancies

    def _associate_outcome_dates(self, section, pregnancies: List[PreviousPregnancyHistory]):
        """Associate outcome dates with pregnancy records - DEPRECATED"""
        # This method is no longer used as dates are now extracted directly 
        # from each observation's effectiveTime in _extract_single_pregnancy_outcome
        pass
    
    def _get_outcome_name(self, outcome_code: str) -> str:
        """Get human-readable outcome name from code"""
        outcome_names = {
            "281050002": "Livebirth",
            "57797005": "Termination of pregnancy", 
            "237364002": "Stillbirth",
            "17369002": "Miscarriage"
        }
        return outcome_names.get(outcome_code, f"Outcome {outcome_code}")
    
    def _extract_effective_time(self, element) -> str:
        """Extract effective time from observation element"""
        try:
            time_elem = element.find("hl7:effectiveTime", self.namespaces)
            if time_elem is not None:
                return time_elem.get("value", "")
            return ""
        except Exception:
            return ""
    
    def _format_date(self, date_string: str) -> str:
        """Format CDA date string to human-readable format"""
        if not date_string or len(date_string) < 8:
            return date_string
        
        try:
            # Handle YYYYMMDD format
            if len(date_string) >= 8:
                year = date_string[:4]
                month = date_string[4:6]
                day = date_string[6:8]
                
                # Create readable date
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime("%B %d, %Y")
                
        except (ValueError, IndexError):
            pass
        
        return date_string