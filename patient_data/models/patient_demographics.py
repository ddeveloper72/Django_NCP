"""
Patient Demographics Data Models

Django NCP Healthcare Portal - Unified Patient Data Structures
Generated: December 19, 2024
Purpose: Standardized patient demographic models for CDA and FHIR sources
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import re


@dataclass
class PatientIdentifier:
    """
    Standardized patient identifier for European healthcare systems
    
    Supports both CDA XML and FHIR identifier formats with European
    healthcare organization compatibility.
    """
    extension: str
    root: str = ""
    assigning_authority_name: str = ""
    identifier_type: str = "primary"
    
    def __post_init__(self):
        """Validate and normalize identifier data"""
        if not self.extension:
            raise ValueError("Patient identifier extension cannot be empty")
            
        # Normalize identifier type
        if self.identifier_type not in ["primary", "secondary", "national", "local"]:
            self.identifier_type = "primary"
    
    def get_display_value(self) -> str:
        """
        Get formatted identifier for UI display
        
        Returns:
            str: Formatted identifier (e.g., "2-1234-W7")
        """
        return self.extension
    
    def get_full_identifier(self) -> str:
        """
        Get complete identifier with root and extension
        
        Returns:
            str: Complete identifier format
        """
        if self.root:
            return f"{self.root}^^^{self.extension}"
        return self.extension
    
    def is_european_health_id(self) -> bool:
        """
        Check if identifier matches European Health ID patterns
        
        Returns:
            bool: True if matches EU health ID format
        """
        # European health ID patterns (simplified)
        eu_patterns = [
            r'\d+-\d+-[A-Z]\d+',  # Portuguese format: 2-1234-W7
            r'[A-Z]{2}\d{8,12}',  # Generic European format
            r'\d{8,12}',          # Numeric format
        ]
        
        for pattern in eu_patterns:
            if re.match(pattern, self.extension):
                return True
        return False


@dataclass
class PatientDemographics:
    """
    Unified patient demographics model for Django NCP
    
    Consolidates patient data from CDA XML, FHIR bundles, and session data
    into a standardized format with helper methods for template rendering.
    """
    given_name: str = "Unknown"
    family_name: str = "Unknown"
    birth_date: str = ""
    gender: str = "Unknown"
    patient_id: str = ""
    identifiers: List[PatientIdentifier] = field(default_factory=list)
    
    # Optional extended demographic data
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    marital_status: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize patient data"""
        # Normalize names
        self.given_name = self.given_name.strip() if self.given_name else "Unknown"
        self.family_name = self.family_name.strip() if self.family_name else "Unknown"
        
        # Normalize gender
        if self.gender:
            gender_lower = self.gender.lower()
            if gender_lower in ['f', 'female', 'feminino', 'féminin']:
                self.gender = "Female"
            elif gender_lower in ['m', 'male', 'masculino', 'masculin']:
                self.gender = "Male"
            else:
                self.gender = self.gender.title()
        else:
            self.gender = "Unknown"
    
    def get_display_name(self) -> str:
        """
        Get formatted patient name for UI display
        
        Returns:
            str: Full patient name (e.g., "Diana Ferreira")
        """
        if self.given_name == "Unknown" and self.family_name == "Unknown":
            return "Unknown Patient"
        
        names = [name for name in [self.given_name, self.family_name] if name != "Unknown"]
        return " ".join(names) if names else "Unknown Patient"
    
    def get_formatted_birth_date(self) -> str:
        """
        Get formatted birth date for UI display
        
        Returns:
            str: Formatted date (e.g., "08/05/1982") or empty string
        """
        if not self.birth_date:
            return ""
            
        # Handle different input formats
        try:
            # Try parsing CDA format: 19820508
            if len(self.birth_date) == 8 and self.birth_date.isdigit():
                year = self.birth_date[:4]
                month = self.birth_date[4:6]
                day = self.birth_date[6:8]
                return f"{day}/{month}/{year}"
            
            # Try parsing ISO format: 1982-05-08
            elif '-' in self.birth_date:
                date_obj = datetime.strptime(self.birth_date, '%Y-%m-%d')
                return date_obj.strftime('%d/%m/%Y')
            
            # Try parsing already formatted: 08/05/1982
            elif '/' in self.birth_date and len(self.birth_date) == 10:
                return self.birth_date
                
        except (ValueError, IndexError):
            pass
            
        return self.birth_date  # Return as-is if can't format
    
    def get_primary_identifier(self) -> Optional[PatientIdentifier]:
        """
        Get primary patient identifier
        
        Returns:
            PatientIdentifier: Primary identifier or None if not found
        """
        if not self.identifiers:
            return None
            
        # Look for explicitly marked primary identifier
        for identifier in self.identifiers:
            if identifier.identifier_type == "primary":
                return identifier
        
        # Return first identifier if no primary found
        return self.identifiers[0]
    
    def get_all_identifiers_display(self) -> List[str]:
        """
        Get all identifiers formatted for display
        
        Returns:
            List[str]: List of formatted identifier strings
        """
        return [identifier.get_display_value() for identifier in self.identifiers]
    
    def get_age_at_date(self, reference_date: Optional[datetime] = None) -> Optional[int]:
        """
        Calculate patient age at reference date
        
        Args:
            reference_date: Date to calculate age at (defaults to today)
            
        Returns:
            int: Age in years or None if birth date invalid
        """
        if not self.birth_date:
            return None
            
        try:
            # Parse birth date
            if len(self.birth_date) == 8 and self.birth_date.isdigit():
                birth_year = int(self.birth_date[:4])
                birth_month = int(self.birth_date[4:6])
                birth_day = int(self.birth_date[6:8])
                birth_date_obj = datetime(birth_year, birth_month, birth_day)
            elif '-' in self.birth_date:
                birth_date_obj = datetime.strptime(self.birth_date, '%Y-%m-%d')
            else:
                return None
                
            # Calculate age
            ref_date = reference_date or datetime.now()
            age = ref_date.year - birth_date_obj.year
            
            # Adjust if birthday hasn't occurred this year
            if (ref_date.month, ref_date.day) < (birth_date_obj.month, birth_date_obj.day):
                age -= 1
                
            return max(0, age)  # Ensure non-negative age
            
        except (ValueError, TypeError):
            return None
    
    def to_template_context(self) -> Dict[str, Any]:
        """
        Create template context dictionary
        
        Returns:
            Dict: Complete template context for patient demographics
        """
        primary_id = self.get_primary_identifier()
        
        return {
            'demographics': {
                'given_name': self.given_name,
                'family_name': self.family_name,
                'birth_date': self.birth_date,
                'gender': self.gender,
                'patient_id': self.patient_id,
                'patient_identifiers': [
                    {
                        'extension': id.extension,
                        'root': id.root,
                        'assigning_authority_name': id.assigning_authority_name,
                        'identifier_type': id.identifier_type
                    }
                    for id in self.identifiers
                ],
                'address': self.address,
                'phone': self.phone,
                'email': self.email,
                'marital_status': self.marital_status
            },
            'display_name': self.get_display_name(),
            'formatted_birth_date': self.get_formatted_birth_date(),
            'primary_identifier': {
                'extension': primary_id.extension,
                'root': primary_id.root,
                'assigning_authority_name': primary_id.assigning_authority_name,
                'display_value': primary_id.get_display_value()
            } if primary_id else None,
            'all_identifiers': self.get_all_identifiers_display(),
            'age': self.get_age_at_date(),
            'is_female': self.gender.lower() == 'female',
            'is_male': self.gender.lower() == 'male',
        }
    
    def to_legacy_context(self) -> Dict[str, Any]:
        """
        Create legacy template context for backward compatibility
        
        Returns:
            Dict: Context matching existing template expectations
        """
        primary_id = self.get_primary_identifier()
        
        # Create the legacy format that existing templates expect
        legacy_context = {
            'given_name': self.given_name,
            'family_name': self.family_name,
            'birth_date': self.birth_date,
            'gender': self.gender,
            'patient_identifiers': [
                {
                    'extension': id.extension,
                    'root': id.root,
                    'assigning_authority_name': id.assigning_authority_name
                }
                for id in self.identifiers
            ]
        }
        
        # Add computed fields that templates expect
        if primary_id:
            legacy_context['primary_identifier_extension'] = primary_id.extension
            legacy_context['primary_identifier_root'] = primary_id.root
            
        return legacy_context
    
    @classmethod
    def from_session_data(cls, session_data: Dict[str, Any]) -> 'PatientDemographics':
        """
        Create PatientDemographics from existing session data format
        
        Args:
            session_data: Dictionary containing patient data from session
            
        Returns:
            PatientDemographics: Populated demographics object
        """
        identifiers = []
        
        # Extract identifiers from session data
        if 'patient_identifiers' in session_data:
            for id_data in session_data['patient_identifiers']:
                identifier = PatientIdentifier(
                    extension=id_data.get('extension', ''),
                    root=id_data.get('root', ''),
                    assigning_authority_name=id_data.get('assigning_authority_name', ''),
                    identifier_type='primary' if not identifiers else 'secondary'
                )
                identifiers.append(identifier)
        
        return cls(
            given_name=session_data.get('given_name', 'Unknown'),
            family_name=session_data.get('family_name', 'Unknown'),
            birth_date=session_data.get('birth_date', ''),
            gender=session_data.get('gender', 'Unknown'),
            patient_id=session_data.get('patient_id', ''),
            identifiers=identifiers,
            address=session_data.get('address'),
            phone=session_data.get('phone'),
            email=session_data.get('email'),
            marital_status=session_data.get('marital_status')
        )
    
    def __str__(self) -> str:
        """String representation of patient demographics"""
        return f"PatientDemographics(name='{self.get_display_name()}', birth_date='{self.birth_date}', gender='{self.gender}')"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return (f"PatientDemographics("
                f"given_name='{self.given_name}', "
                f"family_name='{self.family_name}', "
                f"birth_date='{self.birth_date}', "
                f"gender='{self.gender}', "
                f"identifiers={len(self.identifiers)} items)")