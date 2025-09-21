"""
Dynamic Clinical Table Handler
Uses admin-configured columns to build tables with comprehensive data extraction
"""

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

from patient_data.models import ClinicalSectionConfig, DataExtractionLog

from .deep_xml_extractor import DeepXMLExtractor

logger = logging.getLogger(__name__)


class DynamicClinicalTableHandler:
    """
    Creates clinical tables based on admin-configured column settings
    and deep XML endpoint extraction
    """

    def __init__(self):
        self.extractor = DeepXMLExtractor()
        self.default_configs = self._get_default_configurations()

    def create_dynamic_clinical_table(
        self,
        entries_data: List[Dict],
        section_code: str,
        xml_content: str = None,
        patient_id: str = None,
    ) -> Dict[str, Any]:
        """
        Create clinical table with dynamically configured columns

        Args:
            entries_data: Processed entry data from CDA processor
            section_code: LOINC section code
            xml_content: Raw XML for deep extraction (optional)
            patient_id: Patient identifier for logging

        Returns:
            Enhanced clinical table structure
        """
        try:
            # Get column configuration for this section
            column_configs = self._get_section_column_config(section_code)

            # Perform deep extraction if XML provided
            deep_data = {}
            if xml_content and patient_id:
                logger.info(
                    f"🔬 Performing deep XML extraction for section {section_code}"
                )
                deep_data = self.extractor.extract_all_endpoints(
                    xml_content, section_code, patient_id
                )

            # Build table structure
            clinical_table = {
                "title": self._get_section_title(section_code),
                "section_code": section_code,
                "headers": self._build_table_headers(column_configs),
                "rows": [],
                "entry_count": len(entries_data),
                "available_endpoints": deep_data.get("discovered_fields", []),
                "endpoint_summary": deep_data.get("endpoint_summary", {}),
                "column_config_source": "admin" if column_configs else "default",
                "deep_extraction_enabled": bool(xml_content),
            }

            # Process each entry with dynamic column extraction
            for i, entry in enumerate(entries_data):
                # Merge standard entry data with deep extraction data
                enhanced_entry = entry.copy()
                if deep_data and i < len(deep_data.get("entries", [])):
                    enhanced_entry.update(deep_data["entries"][i])

                # Create table row using configured columns
                row = self._create_dynamic_row(
                    enhanced_entry, column_configs, section_code
                )
                clinical_table["rows"].append(row)

            # Calculate enhanced metrics
            clinical_table.update(self._calculate_table_metrics(clinical_table["rows"]))

            logger.info(
                f"✅ Created dynamic table: {len(clinical_table['rows'])} rows, {len(clinical_table['headers'])} columns"
            )

            return clinical_table

        except Exception as e:
            logger.error(f"❌ Dynamic table creation failed: {e}")
            return self._create_fallback_table(entries_data, section_code)

    def _get_section_column_config(self, section_code: str) -> List[Dict[str, Any]]:
        """Get column configuration for section (from admin or defaults)"""

        try:
            # Try to get from database (admin-configured)
            configs = ClinicalSectionConfig.objects.filter(
                section_code=section_code, is_enabled=True
            ).order_by("display_order", "display_label")

            if configs.exists():
                logger.info(f"📋 Using admin-configured columns for {section_code}")
                return [self._config_to_dict(config) for config in configs]

        except Exception as e:
            logger.warning(f"⚠️ Could not load admin config: {e}")

        # Fallback to defaults
        logger.info(f"📋 Using default columns for {section_code}")
        return self.default_configs.get(section_code, self.default_configs["default"])

    def _config_to_dict(self, config) -> Dict[str, Any]:
        """Convert database config to dictionary"""
        return {
            "key": config.column_key,
            "label": config.display_label,
            "type": config.column_type,
            "primary": config.is_primary,
            "xpath_patterns": config.xpath_patterns,
            "field_mappings": config.field_mappings,
            "css_class": config.css_class,
            "order": config.display_order,
        }

    def _build_table_headers(
        self, column_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build table headers from column configuration"""

        headers = []
        for config in column_configs:
            header = {
                "key": config["key"],
                "label": config["label"],
                "type": config.get("type", "text"),
                "primary": config.get("primary", False),
                "css_class": config.get("css_class", ""),
                "sortable": config.get("type") in ["date", "numeric", "text"],
                "filterable": config.get("type") in ["status", "codes", "text"],
            }
            headers.append(header)

        return headers

    def _create_dynamic_row(
        self,
        entry: Dict[str, Any],
        column_configs: List[Dict[str, Any]],
        section_code: str,
    ) -> Dict[str, Any]:
        """Create table row using dynamic column configuration"""

        row = {
            "entry_id": entry.get("id", f"unknown_{hash(str(entry))}"),
            "has_medical_codes": False,
            "terminology_quality": "basic",
            "endpoint_coverage": 0,
            "data": {},
        }

        fields = entry.get("fields", {})
        all_entry_data = {**fields, **entry}  # Merge fields with direct entry data

        for config in column_configs:
            column_key = config["key"]
            column_type = config.get("type", "text")

            # Extract data using multiple strategies
            cell_data = self._extract_cell_data(all_entry_data, config, section_code)

            # Apply type-specific formatting
            formatted_data = self._format_cell_data(cell_data, column_type)

            row["data"][column_key] = formatted_data

            # Update row metadata
            if formatted_data.get("has_codes") or formatted_data.get("has_terminology"):
                row["has_medical_codes"] = True
                row["terminology_quality"] = "enhanced"

        # Calculate endpoint coverage
        available_fields = len([k for k in all_entry_data.keys() if all_entry_data[k]])
        configured_fields = len(column_configs)
        row["endpoint_coverage"] = (
            min(100, (available_fields / configured_fields) * 100)
            if configured_fields > 0
            else 0
        )

        return row

    def _extract_cell_data(
        self, entry_data: Dict[str, Any], config: Dict[str, Any], section_code: str
    ) -> Dict[str, Any]:
        """Extract cell data using configured field mappings and XPath patterns"""

        result = {
            "value": "Not specified",
            "has_terminology": False,
            "has_codes": False,
            "codes": [],
            "source_field": None,
            "extraction_method": "none",
        }

        # Strategy 1: Field mappings (preferred)
        field_mappings = config.get("field_mappings", [])
        if field_mappings:
            for field_pattern in field_mappings:
                if field_pattern in entry_data:
                    field_data = entry_data[field_pattern]

                    if isinstance(field_data, dict):
                        result["value"] = field_data.get(
                            "value", field_data.get("display_name", "Not specified")
                        )
                        result["has_terminology"] = field_data.get(
                            "has_valueset", False
                        )
                        result["source_field"] = field_pattern
                        result["extraction_method"] = "field_mapping"

                        # Extract codes if available
                        if "code" in field_data and field_data["code"]:
                            result["codes"] = [
                                {
                                    "code": field_data["code"],
                                    "system": field_data.get("system_name", "Unknown"),
                                    "display": field_data.get("display_name", ""),
                                    "badge": self._get_system_badge(
                                        field_data.get("code_system", "")
                                    ),
                                }
                            ]
                            result["has_codes"] = True

                        break
                    elif field_data:  # Simple value
                        result["value"] = str(field_data)
                        result["source_field"] = field_pattern
                        result["extraction_method"] = "field_mapping"
                        break

        # Strategy 2: Pattern matching in all fields
        if result["value"] == "Not specified":
            column_key = config["key"]

            # Look for similar field names
            matching_fields = []
            for field_name, field_value in entry_data.items():
                if (
                    column_key.lower() in field_name.lower()
                    or field_name.lower() in column_key.lower()
                ):
                    matching_fields.append((field_name, field_value))

            if matching_fields:
                field_name, field_value = matching_fields[0]  # Take first match

                if isinstance(field_value, dict):
                    result["value"] = field_value.get(
                        "value", field_value.get("display_name", str(field_value))
                    )
                else:
                    result["value"] = str(field_value)

                result["source_field"] = field_name
                result["extraction_method"] = "pattern_matching"

        # Strategy 3: Specialized extraction by column type
        if result["value"] == "Not specified":
            result = self._specialized_extraction(entry_data, config, section_code)

        return result

    def _specialized_extraction(
        self, entry_data: Dict[str, Any], config: Dict[str, Any], section_code: str
    ) -> Dict[str, Any]:
        """Specialized extraction based on column type and section"""

        column_key = config["key"]
        column_type = config.get("type", "text")

        result = {
            "value": "Not specified",
            "has_terminology": False,
            "has_codes": False,
            "codes": [],
            "source_field": None,
            "extraction_method": "specialized",
        }

        # Codes column - use our existing 3-tier strategy
        if column_key == "codes":
            codes = self._extract_medical_codes(entry_data, section_code)
            result.update(
                {
                    "codes": codes,
                    "has_codes": len(codes) > 0,
                    "count": len(codes),
                    "extraction_method": "3_tier_codes",
                }
            )

        # Date extraction
        elif column_type == "date":
            date_fields = [
                "effective_time_low_0",
                "effective_time_0",
                "effectiveTime",
                "date",
                "onset_date",
            ]
            for field in date_fields:
                if field in entry_data:
                    date_value = entry_data[field]
                    if isinstance(date_value, dict):
                        result["value"] = date_value.get(
                            "formatted", date_value.get("value", "Not specified")
                        )
                    else:
                        result["value"] = str(date_value)
                    result["source_field"] = field
                    break

        # Status extraction
        elif column_type == "status":
            status_fields = ["status_code_0", "statusCode", "status", "current_status"]
            for field in status_fields:
                if field in entry_data:
                    status_value = entry_data[field]
                    if isinstance(status_value, dict):
                        result["value"] = status_value.get("value", "Unknown")
                    else:
                        result["value"] = str(status_value)
                    result["source_field"] = field
                    break

        return result

    def _extract_medical_codes(
        self, entry_data: Dict[str, Any], section_code: str
    ) -> List[Dict[str, Any]]:
        """Enhanced medical codes extraction using 3-tier strategy"""

        codes = []

        # Look for code fields with numeric values
        for field_name, field_value in entry_data.items():
            if "code_" in field_name and isinstance(field_value, dict):
                code_val = field_value.get("value")
                if code_val and str(code_val).isdigit() and len(str(code_val)) >= 6:
                    codes.append(
                        {
                            "code": str(code_val),
                            "system": field_value.get("system_name", "SNOMED CT"),
                            "display": field_value.get("display_name", ""),
                            "badge": self._get_system_badge(
                                field_value.get("code_system", "2.16.840.1.113883.6.96")
                            ),
                        }
                    )

        return codes

    def _format_cell_data(
        self, cell_data: Dict[str, Any], column_type: str
    ) -> Dict[str, Any]:
        """Apply type-specific formatting to cell data"""

        if column_type == "date":
            date_formats = self._format_date_for_mobile(cell_data["value"])
            return {
                "value": cell_data["value"],
                "type": "date",
                "formatted": self._format_date_display(cell_data["value"]),
                "mobile_formats": date_formats,
                "source_field": cell_data.get("source_field"),
            }

        elif column_type == "status":
            return {
                "value": cell_data["value"],
                "type": "status",
                "css_class": self._get_status_css_class(cell_data["value"]),
                "source_field": cell_data.get("source_field"),
            }

        elif column_type == "codes":
            return {
                "codes": cell_data.get("codes", []),
                "count": len(cell_data.get("codes", [])),
                "has_codes": len(cell_data.get("codes", [])) > 0,
                "extraction_method": cell_data.get("extraction_method"),
            }

        else:  # text, numeric, etc.
            return {
                "value": cell_data["value"],
                "has_terminology": cell_data.get("has_terminology", False),
                "source_field": cell_data.get("source_field"),
            }

    def _get_system_badge(self, code_system: str) -> str:
        """Get CSS badge class for code system"""
        badge_map = {
            "2.16.840.1.113883.6.96": "badge bg-primary",  # SNOMED CT
            "2.16.840.1.113883.6.1": "badge bg-info",  # LOINC
            "2.16.840.1.113883.6.90": "badge bg-success",  # ICD-10
            "2.16.840.1.113883.6.73": "badge bg-warning",  # ATC
        }
        return badge_map.get(code_system, "badge bg-secondary")

    def _get_status_css_class(self, status_value: str) -> str:
        """Get CSS class for status display"""
        status_map = {
            "active": "badge bg-success",
            "completed": "badge bg-primary",
            "inactive": "badge bg-secondary",
            "unknown": "badge bg-warning",
        }
        return status_map.get(status_value.lower(), "badge bg-light")

    def _format_date_display(self, date_value: str) -> str:
        """Format date for display with mobile-friendly options"""
        if not date_value or date_value == "Not specified":
            return "Not specified"

        # Handle HL7 format
        if len(date_value) >= 8 and date_value.isdigit():
            try:
                year = date_value[:4]
                month = date_value[4:6]
                day = date_value[6:8]
                # Return formatted date
                return f"{day}/{month}/{year}"
            except:
                pass

        return date_value

    def _format_date_for_mobile(self, date_value: str) -> Dict[str, str]:
        """Format date with mobile-friendly display options"""
        if not date_value or date_value == "Not specified":
            return {"short": "N/A", "long": "Not specified", "mobile": "Not specified"}

        # Handle HL7 format
        if len(date_value) >= 8 and date_value.isdigit():
            try:
                year = date_value[:4]
                month = date_value[4:6]
                day = date_value[6:8]

                # Create different format options
                month_names = {
                    "01": "Jan",
                    "02": "Feb",
                    "03": "Mar",
                    "04": "Apr",
                    "05": "May",
                    "06": "Jun",
                    "07": "Jul",
                    "08": "Aug",
                    "09": "Sep",
                    "10": "Oct",
                    "11": "Nov",
                    "12": "Dec",
                }

                return {
                    "short": f"{day}/{month}/{year[-2:]}",  # 15/03/24
                    "long": f"{day}/{month}/{year}",  # 15/03/2024
                    "mobile": f"{day} {month_names.get(month, month)} {year}",  # 15 Mar 2024
                }
            except:
                pass

        return {"short": date_value, "long": date_value, "mobile": date_value}

    def _calculate_table_metrics(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate enhanced table metrics"""

        total_rows = len(rows)
        if total_rows == 0:
            return {"medical_terminology_coverage": 0, "average_endpoint_coverage": 0}

        coded_rows = sum(1 for row in rows if row.get("has_medical_codes", False))
        total_coverage = sum(row.get("endpoint_coverage", 0) for row in rows)

        return {
            "medical_terminology_coverage": (coded_rows / total_rows) * 100,
            "average_endpoint_coverage": total_coverage / total_rows,
            "enhanced_rows": coded_rows,
            "total_rows": total_rows,
        }

    def _get_default_configurations(self) -> Dict[str, List[Dict[str, Any]]]:
        """Default column configurations for each section"""

        return {
            "11450-4": [  # Medical Conditions & Problems
                {
                    "key": "condition",
                    "label": "Condition",
                    "type": "text",
                    "primary": True,
                    "field_mappings": ["Problem DisplayName", "Condition", "problem"],
                },
                {
                    "key": "onset_date",
                    "label": "Onset Date",
                    "type": "date",
                    "field_mappings": ["effective_time_low_0", "onset_date"],
                },
                {
                    "key": "status",
                    "label": "Current Status",
                    "type": "status",
                    "field_mappings": ["status_code_0", "status"],
                },
                {
                    "key": "severity",
                    "label": "Severity",
                    "type": "severity",
                    "field_mappings": ["severity", "problem_severity"],
                },
                {
                    "key": "codes",
                    "label": "Medical Codes",
                    "type": "codes",
                    "field_mappings": [],
                },
            ],
            "47519-4": [  # Clinical Procedures
                {
                    "key": "procedure",
                    "label": "Procedure",
                    "type": "text",
                    "primary": True,
                    "field_mappings": ["Procedure DisplayName", "procedure"],
                },
                {
                    "key": "date_performed",
                    "label": "Date Performed",
                    "type": "date",
                    "field_mappings": ["effective_time_0", "date"],
                },
                {
                    "key": "status",
                    "label": "Status",
                    "type": "status",
                    "field_mappings": ["status_code_0", "status"],
                },
                {
                    "key": "provider",
                    "label": "Healthcare Provider",
                    "type": "text",
                    "field_mappings": ["performer", "provider"],
                },
                {
                    "key": "codes",
                    "label": "Medical Codes",
                    "type": "codes",
                    "field_mappings": [],
                },
            ],
            "default": [
                {
                    "key": "item",
                    "label": "Item",
                    "type": "text",
                    "primary": True,
                    "field_mappings": ["displayName", "name", "title"],
                },
                {
                    "key": "date",
                    "label": "Date",
                    "type": "date",
                    "field_mappings": ["effective_time_0", "date"],
                },
                {
                    "key": "status",
                    "label": "Status",
                    "type": "status",
                    "field_mappings": ["status_code_0", "status"],
                },
                {
                    "key": "codes",
                    "label": "Medical Codes",
                    "type": "codes",
                    "field_mappings": [],
                },
            ],
        }

    def _get_section_title(self, section_code: str) -> str:
        """Get display title for section"""
        titles = {
            "11450-4": "Medical Conditions & Problems",
            "47519-4": "Clinical Procedures",
            "48765-2": "Allergies and Adverse Reactions",
            "10160-0": "Current & Past Medications",
        }
        return titles.get(section_code, "Clinical Information")

    def _create_fallback_table(
        self, entries_data: List[Dict], section_code: str
    ) -> Dict[str, Any]:
        """Create basic fallback table if dynamic creation fails"""
        return {
            "title": self._get_section_title(section_code),
            "section_code": section_code,
            "headers": [
                {"key": "item", "label": "Item", "type": "text", "primary": True},
                {"key": "status", "label": "Status", "type": "status"},
            ],
            "rows": [],
            "entry_count": len(entries_data),
            "error": "Dynamic table creation failed - using fallback",
        }
