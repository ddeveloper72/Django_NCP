# Jinja2 Template URL Usage Guide

## Quick Reference for Template URL Calls

### ✅ Correct Usage
```html
<!-- No parameters -->
<a href="{{ url('app:view_name') }}">Link</a>

<!-- Single parameter -->
<a href="{{ url('app:view_name', object.id) }}">Link</a>

<!-- Multiple parameters -->
<a href="{{ url('app:view_name', param1, param2) }}">Link</a>

<!-- Keyword arguments -->
<a href="{{ url('app:view_name', id=object.id) }}">Link</a>
```

### ❌ Common Mistakes
```html
<!-- Don't use Django template syntax in Jinja2 -->
<a href="{% url 'app:view_name' object.id %}">Wrong</a>

<!-- Don't concatenate URLs manually -->
<a href="/app/view/{{ object.id }}/">Fragile</a>
```

### Working Examples from This Project
```html
<!-- Patient data URLs -->
<a href="{{ url('patient_data:patient_data_form') }}">Back to Search</a>
<a href="{{ url('patient_data:patient_details', patient.id) }}">View Details</a>
<a href="{{ url('patient_data:patient_cda', patient.id) }}">View CDA</a>
<a href="{{ url('patient_data:download_cda_pdf', patient.id) }}">Download PDF</a>

<!-- Portal URLs -->
<a href="{{ url('portal:patient_search', country_code) }}">Search</a>
<a href="{{ url('portal:patient_data', country_code, patient_id) }}">Patient</a>
```

## If You Get URL Errors
1. Check that `eu_ncp_server/jinja2.py` uses `url_helper` function
2. Verify template syntax matches examples above
3. See `JINJA2_URL_CONFIGURATION.md` for detailed troubleshooting

---
**For developers:** Always test URL generation immediately after creating new templates!
