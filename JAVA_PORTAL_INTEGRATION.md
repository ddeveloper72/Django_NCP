# Java Portal Integration Configuration

## Django NCP Server API Endpoints

Your Django NCP server is running on: <http://127.0.0.1:8000>

### Available API Endpoints for Java Portal

#### 1. Countries API

- **URL**: `http://127.0.0.1:8000/api/countries/`
- **Method**: GET
- **Description**: Get list of available EU countries with their NCPs
- **Response**: JSON array with country codes, names, NCP URLs

#### 2. Patient Lookup API  

- **URL**: `http://127.0.0.1:8000/api/patient/lookup/`
- **Method**: POST
- **Description**: Search for patient across EU healthcare networks
- **Body**: JSON with patient search criteria

#### 3. Patient Document API

- **URL**: `http://127.0.0.1:8000/api/patient/{patient_id}/document/{type}/`
- **Method**: GET
- **Description**: Retrieve patient documents
- **Parameters**:
  - `patient_id`: Patient identifier
  - `type`: Document type (PS, eP, eD, LAB)

### Docker Configuration

If your Java portal runs in Docker, update the connection URL to:

- **From container**: `http://host.docker.internal:8000/api/`
- **Or add network**: Connect containers to same Docker network

### SMP Configuration

Current SMP sources (admin-configurable):

- **European**: <https://smp-ehealth-trn.acc.edelivery.tech.ec.europa.eu>
- **Local**: <http://localhost:8290/smp>

The Django server automatically uses the admin-configured SMP source.

### CORS Configuration

If you encounter CORS issues, the Django server may need CORS headers for cross-origin requests from your Java portal.

### Testing

Test the API endpoints:

```bash
# Test countries endpoint
curl http://127.0.0.1:8000/api/countries/

# Test patient lookup
curl -X POST http://127.0.0.1:8000/api/patient/lookup/ \
  -H "Content-Type: application/json" \
  -d '{"country": "AT", "search_criteria": {...}}'
```

## Next Steps

1. **Update Java portal configuration** to point to Django API
2. **Restart Java portal container** with new API URLs
3. **Test integration** using the available endpoints
4. **Configure SMP source** via Django admin if needed (European vs Local)
