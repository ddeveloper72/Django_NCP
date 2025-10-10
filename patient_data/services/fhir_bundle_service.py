"""
FHIR Bundle Processing Service

Handles parsing FHIR bundles, extracting patient data, and converting to patient summaries.
Supports FHIR R4 format and generates comprehensive patient summaries with all available resources.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fhir.resources.bundle import Bundle
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.medication import Medication
from fhir.resources.medicationstatement import MedicationStatement
from fhir.resources.observation import Observation
from fhir.resources.procedure import Procedure
from fhir.resources.encounter import Encounter
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.immunization import Immunization
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.organization import Organization
from fhir.resources.practitioner import Practitioner
from fhir.resources.composition import Composition

logger = logging.getLogger(__name__)


class FHIRBundleService:
    """Service for processing FHIR bundles and extracting patient summaries."""

    def __init__(self):
        self.supported_resource_types = {
            "Patient",
            "Condition",
            "Medication",
            "MedicationStatement",
            "Observation",
            "Procedure",
            "Encounter",
            "AllergyIntolerance",
            "Immunization",
            "DiagnosticReport",
            "Organization",
            "Practitioner",
            "Composition",
        }

    def parse_fhir_bundle(self, bundle_data: Union[str, dict]) -> Dict[str, Any]:
        """
        Parse FHIR bundle and extract structured patient summary.

        Args:
            bundle_data: FHIR bundle as JSON string or dict

        Returns:
            Dict containing parsed patient summary with all sections
        """
        try:
            # Parse bundle data
            if isinstance(bundle_data, str):
                bundle_dict = json.loads(bundle_data)
            else:
                bundle_dict = bundle_data

            bundle = Bundle(**bundle_dict)

            # Extract resources by type
            resources = self._extract_resources_by_type(bundle)

            # Generate patient summary
            summary = self._generate_patient_summary(resources)

            return {
                "success": True,
                "patient_summary": summary,
                "resource_counts": {
                    resource_type: len(resource_list)
                    for resource_type, resource_list in resources.items()
                },
                "bundle_id": bundle.id,
                "bundle_timestamp": (
                    bundle.timestamp.isoformat() if bundle.timestamp else None
                ),
            }

        except Exception as e:
            logger.error(f"Error parsing FHIR bundle: {str(e)}")
            return {"success": False, "error": str(e), "patient_summary": None}

    def _extract_resources_by_type(self, bundle: Bundle) -> Dict[str, List[Any]]:
        """Extract and categorize resources from FHIR bundle."""
        resources = {
            resource_type: [] for resource_type in self.supported_resource_types
        }

        if bundle.entry:
            for entry in bundle.entry:
                if entry.resource:
                    resource_type = entry.resource.get_resource_type()
                    if resource_type in self.supported_resource_types:
                        resources[resource_type].append(entry.resource)

        return resources

    def _generate_patient_summary(
        self, resources: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive patient summary from FHIR resources."""
        summary = {
            "patient_demographics": self._extract_patient_demographics(
                resources.get("Patient", [])
            ),
            "conditions": self._extract_conditions(resources.get("Condition", [])),
            "medications": self._extract_medications(
                resources.get("MedicationStatement", []),
                resources.get("Medication", []),
            ),
            "observations": self._extract_observations(
                resources.get("Observation", [])
            ),
            "procedures": self._extract_procedures(resources.get("Procedure", [])),
            "allergies": self._extract_allergies(
                resources.get("AllergyIntolerance", [])
            ),
            "immunizations": self._extract_immunizations(
                resources.get("Immunization", [])
            ),
            "encounters": self._extract_encounters(resources.get("Encounter", [])),
            "diagnostic_reports": self._extract_diagnostic_reports(
                resources.get("DiagnosticReport", [])
            ),
            "care_providers": self._extract_care_providers(
                resources.get("Practitioner", []), resources.get("Organization", [])
            ),
            "composition": self._extract_composition(resources.get("Composition", [])),
            "summary_metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_resources": sum(
                    len(resource_list) for resource_list in resources.values()
                ),
                "resource_types_present": [rt for rt, rl in resources.items() if rl],
            },
        }

        return summary

    def _extract_patient_demographics(self, patients: List[Patient]) -> Dict[str, Any]:
        """Extract patient demographic information."""
        if not patients:
            return {}

        patient = patients[0]  # Primary patient
        demographics = {
            "id": patient.id,
            "identifiers": [],
            "name": {},
            "birth_date": None,
            "gender": None,
            "address": [],
            "telecom": [],
            "marital_status": None,
            "communication": [],
        }

        # Extract identifiers
        if patient.identifier:
            for identifier in patient.identifier:
                demographics["identifiers"].append(
                    {
                        "system": identifier.system,
                        "value": identifier.value,
                        "type": identifier.type.text if identifier.type else None,
                    }
                )

        # Extract name
        if patient.name:
            name = patient.name[0]
            demographics["name"] = {
                "family": name.family,
                "given": name.given,
                "prefix": name.prefix,
                "suffix": name.suffix,
                "text": name.text,
            }

        # Extract other demographics
        demographics["birth_date"] = (
            patient.birthDate.isoformat() if patient.birthDate else None
        )
        demographics["gender"] = patient.gender

        # Extract addresses
        if patient.address:
            for address in patient.address:
                demographics["address"].append(
                    {
                        "line": address.line,
                        "city": address.city,
                        "state": address.state,
                        "postal_code": address.postalCode,
                        "country": address.country,
                        "use": address.use,
                    }
                )

        # Extract telecom
        if patient.telecom:
            for telecom in patient.telecom:
                demographics["telecom"].append(
                    {
                        "system": telecom.system,
                        "value": telecom.value,
                        "use": telecom.use,
                    }
                )

        return demographics

    def _extract_conditions(self, conditions: List[Condition]) -> List[Dict[str, Any]]:
        """Extract condition/diagnosis information."""
        condition_list = []

        for condition in conditions:
            condition_data = {
                "id": condition.id,
                "code": (
                    self._extract_codeable_concept(condition.code)
                    if condition.code
                    else None
                ),
                "clinical_status": (
                    condition.clinicalStatus.coding[0].code
                    if condition.clinicalStatus
                    else None
                ),
                "verification_status": (
                    condition.verificationStatus.coding[0].code
                    if condition.verificationStatus
                    else None
                ),
                "category": (
                    [self._extract_codeable_concept(cat) for cat in condition.category]
                    if condition.category
                    else []
                ),
                "severity": (
                    self._extract_codeable_concept(condition.severity)
                    if condition.severity
                    else None
                ),
                "onset": self._extract_onset(condition),
                "recorded_date": (
                    condition.recordedDate.isoformat()
                    if condition.recordedDate
                    else None
                ),
                "notes": (
                    [note.text for note in condition.note] if condition.note else []
                ),
            }
            condition_list.append(condition_data)

        return condition_list

    def _extract_medications(
        self,
        medication_statements: List[MedicationStatement],
        medications: List[Medication],
    ) -> List[Dict[str, Any]]:
        """Extract medication information."""
        medication_list = []

        # Create medication lookup
        med_lookup = {med.id: med for med in medications}

        for med_statement in medication_statements:
            med_data = {
                "id": med_statement.id,
                "status": med_statement.status,
                "medication": None,
                "dosage": [],
                "effective_period": None,
                "date_asserted": (
                    med_statement.dateAsserted.isoformat()
                    if med_statement.dateAsserted
                    else None
                ),
                "reason_code": (
                    [
                        self._extract_codeable_concept(reason)
                        for reason in med_statement.reasonCode
                    ]
                    if med_statement.reasonCode
                    else []
                ),
            }

            # Extract medication details
            if med_statement.medicationCodeableConcept:
                med_data["medication"] = self._extract_codeable_concept(
                    med_statement.medicationCodeableConcept
                )
            elif (
                med_statement.medicationReference
                and med_statement.medicationReference.reference
            ):
                med_id = med_statement.medicationReference.reference.split("/")[-1]
                if med_id in med_lookup:
                    medication = med_lookup[med_id]
                    med_data["medication"] = {
                        "code": (
                            self._extract_codeable_concept(medication.code)
                            if medication.code
                            else None
                        ),
                        "form": (
                            self._extract_codeable_concept(medication.form)
                            if medication.form
                            else None
                        ),
                    }

            # Extract dosage
            if med_statement.dosage:
                for dosage in med_statement.dosage:
                    dosage_data = {
                        "text": dosage.text,
                        "timing": str(dosage.timing) if dosage.timing else None,
                        "route": (
                            self._extract_codeable_concept(dosage.route)
                            if dosage.route
                            else None
                        ),
                        "dose_quantity": (
                            str(dosage.doseAndRate[0].doseQuantity)
                            if dosage.doseAndRate and dosage.doseAndRate[0].doseQuantity
                            else None
                        ),
                    }
                    med_data["dosage"].append(dosage_data)

            # Extract effective period
            if med_statement.effectivePeriod:
                med_data["effective_period"] = {
                    "start": (
                        med_statement.effectivePeriod.start.isoformat()
                        if med_statement.effectivePeriod.start
                        else None
                    ),
                    "end": (
                        med_statement.effectivePeriod.end.isoformat()
                        if med_statement.effectivePeriod.end
                        else None
                    ),
                }

            medication_list.append(med_data)

        return medication_list

    def _extract_observations(
        self, observations: List[Observation]
    ) -> List[Dict[str, Any]]:
        """Extract observation/vital signs information."""
        observation_list = []

        for obs in observations:
            obs_data = {
                "id": obs.id,
                "status": obs.status,
                "category": (
                    [self._extract_codeable_concept(cat) for cat in obs.category]
                    if obs.category
                    else []
                ),
                "code": self._extract_codeable_concept(obs.code) if obs.code else None,
                "value": self._extract_observation_value(obs),
                "effective_datetime": (
                    obs.effectiveDateTime.isoformat() if obs.effectiveDateTime else None
                ),
                "issued": obs.issued.isoformat() if obs.issued else None,
                "interpretation": (
                    [
                        self._extract_codeable_concept(interp)
                        for interp in obs.interpretation
                    ]
                    if obs.interpretation
                    else []
                ),
                "reference_range": self._extract_reference_range(obs),
                "component": [],
            }

            # Extract components for complex observations
            if obs.component:
                for component in obs.component:
                    comp_data = {
                        "code": (
                            self._extract_codeable_concept(component.code)
                            if component.code
                            else None
                        ),
                        "value": self._extract_observation_value(component),
                        "interpretation": (
                            [
                                self._extract_codeable_concept(interp)
                                for interp in component.interpretation
                            ]
                            if component.interpretation
                            else []
                        ),
                    }
                    obs_data["component"].append(comp_data)

            observation_list.append(obs_data)

        return observation_list

    def _extract_procedures(self, procedures: List[Procedure]) -> List[Dict[str, Any]]:
        """Extract procedure information."""
        procedure_list = []

        for procedure in procedures:
            proc_data = {
                "id": procedure.id,
                "status": procedure.status,
                "code": (
                    self._extract_codeable_concept(procedure.code)
                    if procedure.code
                    else None
                ),
                "category": (
                    self._extract_codeable_concept(procedure.category)
                    if procedure.category
                    else None
                ),
                "performed_datetime": (
                    procedure.performedDateTime.isoformat()
                    if procedure.performedDateTime
                    else None
                ),
                "performed_period": None,
                "reason_code": (
                    [
                        self._extract_codeable_concept(reason)
                        for reason in procedure.reasonCode
                    ]
                    if procedure.reasonCode
                    else []
                ),
                "body_site": (
                    [
                        self._extract_codeable_concept(site)
                        for site in procedure.bodySite
                    ]
                    if procedure.bodySite
                    else []
                ),
                "outcome": (
                    self._extract_codeable_concept(procedure.outcome)
                    if procedure.outcome
                    else None
                ),
                "notes": (
                    [note.text for note in procedure.note] if procedure.note else []
                ),
            }

            if procedure.performedPeriod:
                proc_data["performed_period"] = {
                    "start": (
                        procedure.performedPeriod.start.isoformat()
                        if procedure.performedPeriod.start
                        else None
                    ),
                    "end": (
                        procedure.performedPeriod.end.isoformat()
                        if procedure.performedPeriod.end
                        else None
                    ),
                }

            procedure_list.append(proc_data)

        return procedure_list

    def _extract_allergies(
        self, allergies: List[AllergyIntolerance]
    ) -> List[Dict[str, Any]]:
        """Extract allergy and intolerance information."""
        allergy_list = []

        for allergy in allergies:
            allergy_data = {
                "id": allergy.id,
                "clinical_status": (
                    allergy.clinicalStatus.coding[0].code
                    if allergy.clinicalStatus
                    else None
                ),
                "verification_status": (
                    allergy.verificationStatus.coding[0].code
                    if allergy.verificationStatus
                    else None
                ),
                "type": allergy.type,
                "category": allergy.category,
                "criticality": allergy.criticality,
                "code": (
                    self._extract_codeable_concept(allergy.code)
                    if allergy.code
                    else None
                ),
                "onset_datetime": (
                    allergy.onsetDateTime.isoformat() if allergy.onsetDateTime else None
                ),
                "recorded_date": (
                    allergy.recordedDate.isoformat() if allergy.recordedDate else None
                ),
                "reactions": [],
            }

            # Extract reactions
            if allergy.reaction:
                for reaction in allergy.reaction:
                    reaction_data = {
                        "substance": (
                            self._extract_codeable_concept(reaction.substance)
                            if reaction.substance
                            else None
                        ),
                        "manifestation": (
                            [
                                self._extract_codeable_concept(manif)
                                for manif in reaction.manifestation
                            ]
                            if reaction.manifestation
                            else []
                        ),
                        "severity": reaction.severity,
                        "onset": reaction.onset,
                        "description": reaction.description,
                    }
                    allergy_data["reactions"].append(reaction_data)

            allergy_list.append(allergy_data)

        return allergy_list

    def _extract_immunizations(
        self, immunizations: List[Immunization]
    ) -> List[Dict[str, Any]]:
        """Extract immunization information."""
        immunization_list = []

        for immunization in immunizations:
            imm_data = {
                "id": immunization.id,
                "status": immunization.status,
                "vaccine_code": (
                    self._extract_codeable_concept(immunization.vaccineCode)
                    if immunization.vaccineCode
                    else None
                ),
                "occurrence_datetime": (
                    immunization.occurrenceDateTime.isoformat()
                    if immunization.occurrenceDateTime
                    else None
                ),
                "recorded": (
                    immunization.recorded.isoformat() if immunization.recorded else None
                ),
                "lot_number": immunization.lotNumber,
                "expiration_date": (
                    immunization.expirationDate.isoformat()
                    if immunization.expirationDate
                    else None
                ),
                "site": (
                    self._extract_codeable_concept(immunization.site)
                    if immunization.site
                    else None
                ),
                "route": (
                    self._extract_codeable_concept(immunization.route)
                    if immunization.route
                    else None
                ),
                "dose_quantity": (
                    str(immunization.doseQuantity)
                    if immunization.doseQuantity
                    else None
                ),
                "reason_code": (
                    [
                        self._extract_codeable_concept(reason)
                        for reason in immunization.reasonCode
                    ]
                    if immunization.reasonCode
                    else []
                ),
                "notes": (
                    [note.text for note in immunization.note]
                    if immunization.note
                    else []
                ),
            }

            immunization_list.append(imm_data)

        return immunization_list

    def _extract_encounters(self, encounters: List[Encounter]) -> List[Dict[str, Any]]:
        """Extract encounter information."""
        encounter_list = []

        for encounter in encounters:
            enc_data = {
                "id": encounter.id,
                "status": encounter.status,
                "class": encounter.class_fhir.code if encounter.class_fhir else None,
                "type": (
                    [
                        self._extract_codeable_concept(enc_type)
                        for enc_type in encounter.type
                    ]
                    if encounter.type
                    else []
                ),
                "priority": (
                    self._extract_codeable_concept(encounter.priority)
                    if encounter.priority
                    else None
                ),
                "period": None,
                "reason_code": (
                    [
                        self._extract_codeable_concept(reason)
                        for reason in encounter.reasonCode
                    ]
                    if encounter.reasonCode
                    else []
                ),
                "diagnosis": [],
                "hospitalization": None,
            }

            # Extract period
            if encounter.period:
                enc_data["period"] = {
                    "start": (
                        encounter.period.start.isoformat()
                        if encounter.period.start
                        else None
                    ),
                    "end": (
                        encounter.period.end.isoformat()
                        if encounter.period.end
                        else None
                    ),
                }

            # Extract diagnosis
            if encounter.diagnosis:
                for diagnosis in encounter.diagnosis:
                    diag_data = {
                        "condition_reference": (
                            diagnosis.condition.reference
                            if diagnosis.condition
                            else None
                        ),
                        "use": (
                            self._extract_codeable_concept(diagnosis.use)
                            if diagnosis.use
                            else None
                        ),
                        "rank": diagnosis.rank,
                    }
                    enc_data["diagnosis"].append(diag_data)

            # Extract hospitalization
            if encounter.hospitalization:
                enc_data["hospitalization"] = {
                    "admit_source": (
                        self._extract_codeable_concept(
                            encounter.hospitalization.admitSource
                        )
                        if encounter.hospitalization.admitSource
                        else None
                    ),
                    "discharge_disposition": (
                        self._extract_codeable_concept(
                            encounter.hospitalization.dischargeDisposition
                        )
                        if encounter.hospitalization.dischargeDisposition
                        else None
                    ),
                }

            encounter_list.append(enc_data)

        return encounter_list

    def _extract_diagnostic_reports(
        self, reports: List[DiagnosticReport]
    ) -> List[Dict[str, Any]]:
        """Extract diagnostic report information."""
        report_list = []

        for report in reports:
            report_data = {
                "id": report.id,
                "status": report.status,
                "category": (
                    [self._extract_codeable_concept(cat) for cat in report.category]
                    if report.category
                    else []
                ),
                "code": (
                    self._extract_codeable_concept(report.code) if report.code else None
                ),
                "effective_datetime": (
                    report.effectiveDateTime.isoformat()
                    if report.effectiveDateTime
                    else None
                ),
                "issued": report.issued.isoformat() if report.issued else None,
                "conclusion": report.conclusion,
                "conclusion_code": (
                    [
                        self._extract_codeable_concept(code)
                        for code in report.conclusionCode
                    ]
                    if report.conclusionCode
                    else []
                ),
                "result_references": (
                    [result.reference for result in report.result]
                    if report.result
                    else []
                ),
            }

            report_list.append(report_data)

        return report_list

    def _extract_care_providers(
        self, practitioners: List[Practitioner], organizations: List[Organization]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract care provider information."""
        providers = {"practitioners": [], "organizations": []}

        # Extract practitioners
        for practitioner in practitioners:
            prac_data = {
                "id": practitioner.id,
                "name": [],
                "telecom": [],
                "qualification": [],
            }

            if practitioner.name:
                for name in practitioner.name:
                    prac_data["name"].append(
                        {
                            "family": name.family,
                            "given": name.given,
                            "prefix": name.prefix,
                            "suffix": name.suffix,
                            "text": name.text,
                        }
                    )

            if practitioner.telecom:
                for telecom in practitioner.telecom:
                    prac_data["telecom"].append(
                        {
                            "system": telecom.system,
                            "value": telecom.value,
                            "use": telecom.use,
                        }
                    )

            if practitioner.qualification:
                for qual in practitioner.qualification:
                    prac_data["qualification"].append(
                        {
                            "code": (
                                self._extract_codeable_concept(qual.code)
                                if qual.code
                                else None
                            ),
                            "period": (
                                {
                                    "start": (
                                        qual.period.start.isoformat()
                                        if qual.period and qual.period.start
                                        else None
                                    ),
                                    "end": (
                                        qual.period.end.isoformat()
                                        if qual.period and qual.period.end
                                        else None
                                    ),
                                }
                                if qual.period
                                else None
                            ),
                        }
                    )

            providers["practitioners"].append(prac_data)

        # Extract organizations
        for organization in organizations:
            org_data = {
                "id": organization.id,
                "name": organization.name,
                "type": (
                    [
                        self._extract_codeable_concept(org_type)
                        for org_type in organization.type
                    ]
                    if organization.type
                    else []
                ),
                "telecom": [],
                "address": [],
            }

            if organization.telecom:
                for telecom in organization.telecom:
                    org_data["telecom"].append(
                        {
                            "system": telecom.system,
                            "value": telecom.value,
                            "use": telecom.use,
                        }
                    )

            if organization.address:
                for address in organization.address:
                    org_data["address"].append(
                        {
                            "line": address.line,
                            "city": address.city,
                            "state": address.state,
                            "postal_code": address.postalCode,
                            "country": address.country,
                            "use": address.use,
                        }
                    )

            providers["organizations"].append(org_data)

        return providers

    def _extract_composition(self, compositions: List[Composition]) -> Dict[str, Any]:
        """Extract composition information (document structure)."""
        if not compositions:
            return {}

        composition = compositions[0]  # Primary composition
        comp_data = {
            "id": composition.id,
            "status": composition.status,
            "type": (
                self._extract_codeable_concept(composition.type)
                if composition.type
                else None
            ),
            "category": (
                [self._extract_codeable_concept(cat) for cat in composition.category]
                if composition.category
                else []
            ),
            "title": composition.title,
            "date": composition.date.isoformat() if composition.date else None,
            "author_references": (
                [author.reference for author in composition.author]
                if composition.author
                else []
            ),
            "sections": [],
        }

        # Extract sections
        if composition.section:
            for section in composition.section:
                section_data = {
                    "title": section.title,
                    "code": (
                        self._extract_codeable_concept(section.code)
                        if section.code
                        else None
                    ),
                    "text": (
                        section.text.div if section.text and section.text.div else None
                    ),
                    "entry_references": (
                        [entry.reference for entry in section.entry]
                        if section.entry
                        else []
                    ),
                }
                comp_data["sections"].append(section_data)

        return comp_data

    # Helper methods
    def _extract_codeable_concept(self, codeable_concept) -> Dict[str, Any]:
        """Extract codeable concept information."""
        if not codeable_concept:
            return None

        concept_data = {"text": codeable_concept.text, "coding": []}

        if codeable_concept.coding:
            for coding in codeable_concept.coding:
                concept_data["coding"].append(
                    {
                        "system": coding.system,
                        "code": coding.code,
                        "display": coding.display,
                        "version": coding.version,
                    }
                )

        return concept_data

    def _extract_onset(self, condition) -> Dict[str, Any]:
        """Extract onset information from condition."""
        onset_data = {}

        if hasattr(condition, "onsetDateTime") and condition.onsetDateTime:
            onset_data["datetime"] = condition.onsetDateTime.isoformat()
        elif hasattr(condition, "onsetAge") and condition.onsetAge:
            onset_data["age"] = str(condition.onsetAge)
        elif hasattr(condition, "onsetPeriod") and condition.onsetPeriod:
            onset_data["period"] = {
                "start": (
                    condition.onsetPeriod.start.isoformat()
                    if condition.onsetPeriod.start
                    else None
                ),
                "end": (
                    condition.onsetPeriod.end.isoformat()
                    if condition.onsetPeriod.end
                    else None
                ),
            }
        elif hasattr(condition, "onsetRange") and condition.onsetRange:
            onset_data["range"] = str(condition.onsetRange)
        elif hasattr(condition, "onsetString") and condition.onsetString:
            onset_data["string"] = condition.onsetString

        return onset_data

    def _extract_observation_value(self, observation) -> Dict[str, Any]:
        """Extract observation value (can be various types)."""
        value_data = {}

        if hasattr(observation, "valueQuantity") and observation.valueQuantity:
            value_data["quantity"] = {
                "value": observation.valueQuantity.value,
                "unit": observation.valueQuantity.unit,
                "system": observation.valueQuantity.system,
                "code": observation.valueQuantity.code,
            }
        elif (
            hasattr(observation, "valueCodeableConcept")
            and observation.valueCodeableConcept
        ):
            value_data["codeable_concept"] = self._extract_codeable_concept(
                observation.valueCodeableConcept
            )
        elif hasattr(observation, "valueString") and observation.valueString:
            value_data["string"] = observation.valueString
        elif (
            hasattr(observation, "valueBoolean")
            and observation.valueBoolean is not None
        ):
            value_data["boolean"] = observation.valueBoolean
        elif (
            hasattr(observation, "valueInteger")
            and observation.valueInteger is not None
        ):
            value_data["integer"] = observation.valueInteger
        elif hasattr(observation, "valueRange") and observation.valueRange:
            value_data["range"] = str(observation.valueRange)
        elif hasattr(observation, "valueRatio") and observation.valueRatio:
            value_data["ratio"] = str(observation.valueRatio)
        elif hasattr(observation, "valueSampledData") and observation.valueSampledData:
            value_data["sampled_data"] = str(observation.valueSampledData)
        elif hasattr(observation, "valueTime") and observation.valueTime:
            value_data["time"] = observation.valueTime.isoformat()
        elif hasattr(observation, "valueDateTime") and observation.valueDateTime:
            value_data["datetime"] = observation.valueDateTime.isoformat()
        elif hasattr(observation, "valuePeriod") and observation.valuePeriod:
            value_data["period"] = {
                "start": (
                    observation.valuePeriod.start.isoformat()
                    if observation.valuePeriod.start
                    else None
                ),
                "end": (
                    observation.valuePeriod.end.isoformat()
                    if observation.valuePeriod.end
                    else None
                ),
            }

        return value_data

    def _extract_reference_range(self, observation) -> List[Dict[str, Any]]:
        """Extract reference range information from observation."""
        if not hasattr(observation, "referenceRange") or not observation.referenceRange:
            return []

        ranges = []
        for ref_range in observation.referenceRange:
            range_data = {
                "low": str(ref_range.low) if ref_range.low else None,
                "high": str(ref_range.high) if ref_range.high else None,
                "type": (
                    self._extract_codeable_concept(ref_range.type)
                    if ref_range.type
                    else None
                ),
                "applies_to": (
                    [
                        self._extract_codeable_concept(applies)
                        for applies in ref_range.appliesTo
                    ]
                    if ref_range.appliesTo
                    else []
                ),
                "age": str(ref_range.age) if ref_range.age else None,
                "text": ref_range.text,
            }
            ranges.append(range_data)

        return ranges

    def generate_html_summary(self, patient_summary: Dict[str, Any]) -> str:
        """Generate HTML patient summary from parsed FHIR data."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FHIR Patient Summary</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .section { margin-bottom: 30px; }
                .section h2 { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
                .section h3 { color: #666; }
                .patient-info { background: #e8f5e8; padding: 15px; border-radius: 5px; }
                .demographics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
                .detail-item { margin-bottom: 10px; }
                .detail-label { font-weight: bold; color: #555; }
                .detail-value { margin-left: 10px; }
                .condition-item, .medication-item, .observation-item { 
                    background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #ccc; 
                }
                .active { border-left-color: #e74c3c; }
                .inactive { border-left-color: #95a5a6; }
                .table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .table th { background-color: #f2f2f2; }
                .metadata { background: #f0f8ff; padding: 10px; border-radius: 5px; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <!-- Content will be dynamically generated -->
        </body>
        </html>
        """

        # Generate the HTML content based on patient_summary
        # This would be implemented to create comprehensive HTML from the parsed data

        return html_template

    def convert_to_pdf_data(self, patient_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Convert patient summary to PDF-ready data structure."""
        pdf_data = {
            "title": "FHIR Patient Summary",
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_info": patient_summary.get("patient_demographics", {}),
            "sections": [],
        }

        # Add sections based on available data
        section_mapping = {
            "conditions": "Medical Conditions",
            "medications": "Current Medications",
            "observations": "Vital Signs & Lab Results",
            "procedures": "Procedures & Interventions",
            "allergies": "Allergies & Intolerances",
            "immunizations": "Immunization History",
            "encounters": "Healthcare Encounters",
            "diagnostic_reports": "Diagnostic Reports",
        }

        for key, title in section_mapping.items():
            if patient_summary.get(key):
                pdf_data["sections"].append(
                    {"title": title, "data": patient_summary[key], "type": key}
                )

        return pdf_data
