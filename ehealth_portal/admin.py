from django.contrib import admin
from .models import (
    Country,
    InternationalSearchMask,
    SearchFieldType,
    SearchField,
    PatientSearchResult,
)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_available", "created_at"]
    list_filter = ["is_available", "is_test_environment"]
    search_fields = ["code", "name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(InternationalSearchMask)
class InternationalSearchMaskAdmin(admin.ModelAdmin):
    list_display = ["country", "mask_name", "mask_version", "is_active", "created_at"]
    list_filter = ["country", "is_active"]
    search_fields = ["mask_name", "country__name"]
    readonly_fields = ["created_at", "updated_at", "last_synchronized"]


@admin.register(PatientSearchResult)
class PatientSearchResultAdmin(admin.ModelAdmin):
    list_display = ["country", "searched_by", "patient_found", "search_timestamp"]
    list_filter = ["country", "patient_found", "search_timestamp"]
    search_fields = ["searched_by__username", "country__name"]
    readonly_fields = ["search_timestamp", "search_fields", "patient_data"]


@admin.register(SearchFieldType)
class SearchFieldTypeAdmin(admin.ModelAdmin):
    list_display = ["type_code", "display_name", "html_input_type"]
    search_fields = ["type_code", "display_name", "description"]
    readonly_fields = []


@admin.register(SearchField)
class SearchFieldAdmin(admin.ModelAdmin):
    list_display = ["search_mask", "field_type", "label", "is_required", "field_order"]
    list_filter = ["field_type", "is_required", "search_mask__country"]
    search_fields = ["label", "search_mask__country__name"]
    readonly_fields = []
