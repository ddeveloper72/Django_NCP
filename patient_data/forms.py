"""
Patient Data Forms
Django forms for patient search and data submission
"""

from django import forms
from .models import PatientData, MemberState

# Country choices for EU member states
COUNTRY_CHOICES = [
    ("", "Select Country"),
    ("AT", "Austria"),
    ("BE", "Belgium"),
    ("BG", "Bulgaria"),
    ("HR", "Croatia"),
    ("CY", "Cyprus"),
    ("CZ", "Czech Republic"),
    ("DK", "Denmark"),
    ("EE", "Estonia"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("DE", "Germany"),
    ("GR", "Greece"),
    ("HU", "Hungary"),
    ("IE", "Ireland"),
    ("IT", "Italy"),
    ("LV", "Latvia"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("MT", "Malta"),
    ("NL", "Netherlands"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("RO", "Romania"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("ES", "Spain"),
    ("SE", "Sweden"),
]

GENDER_CHOICES = [
    ("", "Select Gender"),
    ("M", "Male"),
    ("F", "Female"),
    ("O", "Other"),
    ("U", "Unknown"),
]


class PatientDataForm(forms.Form):
    """Form for patient search credentials"""

    given_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter given name (first name)",
            }
        ),
        label="Given Name",
    )

    family_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter family name (last name)",
            }
        ),
        label="Family Name",
    )

    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date", "placeholder": "YYYY-MM-DD"}
        ),
        label="Date of Birth",
    )

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Gender",
    )

    country_code = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Country of Origin",
    )

    patient_id = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter patient ID (if known)",
            }
        ),
        label="Patient ID (Optional)",
    )

    def save(self):
        """Save form data as a simplified PatientData object"""
        # For now, create a minimal record
        # In production, this would need proper integration with the patient identifier system

        from django.contrib.auth.models import User
        from .models import PatientIdentifier, MemberState

        # Get or create a default user for anonymous searches
        default_user, created = User.objects.get_or_create(
            username="patient_search_system",
            defaults={
                "first_name": "Patient Search",
                "last_name": "System",
                "email": "system@localhost",
            },
        )

        # Try to get the member state, or create a default one
        try:
            if self.cleaned_data.get("country_code"):
                member_state = MemberState.objects.get(
                    country_code=self.cleaned_data["country_code"]
                )
            else:
                # Default to Ireland for testing
                member_state, created = MemberState.objects.get_or_create(
                    country_code="IE",
                    defaults={
                        "country_name": "Ireland",
                        "language_code": "en-IE",
                        "ncp_endpoint": "http://localhost:8080/ncp",
                        "home_community_id": "1.2.3.4.5.6",
                    },
                )
        except MemberState.DoesNotExist:
            # Create a default member state
            member_state, created = MemberState.objects.get_or_create(
                country_code="IE",
                defaults={
                    "country_name": "Ireland",
                    "language_code": "en-IE",
                    "ncp_endpoint": "http://localhost:8080/ncp",
                    "home_community_id": "1.2.3.4.5.6",
                },
            )

        # Create or get patient identifier
        patient_id = (
            self.cleaned_data.get("patient_id")
            or f"search_{self.cleaned_data['given_name']}_{self.cleaned_data['family_name']}"
        )
        patient_identifier, created = PatientIdentifier.objects.get_or_create(
            patient_id=patient_id,
            home_member_state=member_state,
            defaults={"id_root": "1.2.3.4.5.6.7"},
        )

        # Create patient data record
        patient_data = PatientData.objects.create(
            patient_identifier=patient_identifier,
            given_name=self.cleaned_data["given_name"],
            family_name=self.cleaned_data["family_name"],
            birth_date=self.cleaned_data.get("birth_date"),
            gender=self.cleaned_data.get("gender", ""),
            accessed_by=default_user,
            consent_given=True,  # Assume consent for search
        )

        return patient_data
