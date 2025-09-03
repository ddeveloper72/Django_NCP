# Django EU eHealth NCP Server

A Django-based implementation of an EU eHealth National Contact Point (NCP) server, designed for cross-border healthcare data exchange.

## Project Overview

This project implements a complete Django-based EU eHealth infrastructure including:

- **NCP Server**: National Contact Point for cross-border patient data exchange
- **Patient Portal**: Web interface for patients and healthcare professionals  
- **SMP Integration**: Service Metadata Publisher communication
- **FHIR Services**: Support for EU eHealth FHIR profiles

## Architecture

Based on analysis of the Java-based DomiSMP and OpenNCP implementations, this Django version provides:

### Core Components

- `ncp_server/` - Main NCP backend services
- `patient_portal/` - User interface and patient management
- `smp_client/` - SMP (Service Metadata Publisher) integration
- `fhir_services/` - FHIR service implementations
- `security/` - Authentication, encryption, and audit logging

### Supported eHealth Services

1. Patient Summary (PS)
2. ePrescription (eP)
3. eDispensation (eD)
4. Laboratory Results
5. Hospital Discharge Reports
6. Medical Imaging Reports

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (venv)
- Docker (for testing with DomiSMP)

### Installation

1. **Clone and setup virtual environment:**

```bash
cd C:\Users\Duncan\VS_Code_Projects\django_ncp
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Environment configuration:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Database setup:**

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. **Run development server:**

```bash
python manage.py runserver
```

## Integration with DomiSMP

This Django NCP server is designed to integrate with the existing DomiSMP infrastructure:

- **SMP Communication**: Uses REST API to register and discover services
- **Service Metadata**: Publishes FHIR service endpoints to SMP
- **Security**: Compatible with DomiSMP security model

## Development

### Project Structure

```
django_ncp/
├── manage.py
├── requirements.txt
├── .env.example
├── ncp_project/          # Main Django project
├── ncp_server/           # Core NCP functionality
├── patient_portal/       # Web interface
├── smp_client/           # SMP integration
├── fhir_services/        # FHIR implementations
├── security/             # Security and audit
├── docs/                 # Documentation
├── tests/                # Test suites
└── config/               # Configuration files
```

### Testing

```bash
python manage.py test
```

### Docker Development

```bash
docker-compose up --build
```

## Security

- TLS/SSL encryption for all communications
- Digital certificate management
- Audit logging for all patient data access
- GDPR compliance features

## Documentation

- [API Documentation](docs/api.md)
- [FHIR Implementation Guide](docs/fhir.md)
- [SMP Integration Guide](docs/smp_integration.md)
- [Security Configuration](docs/security.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project implements EU eHealth specifications and follows applicable healthcare data protection regulations.

## Related Projects

- [DomiSMP](https://github.com/ddeveloper72/IESMP) - Service Metadata Publisher
- [OpenNCP](https://github.com/openncp/openncp) - Reference NCP implementation

---

**Note**: This is a Django implementation based on analysis of the Java-based EU eHealth infrastructure. It provides equivalent functionality while leveraging Python/Django ecosystem benefits.
