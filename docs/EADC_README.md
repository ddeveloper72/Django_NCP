# EADC (Epsos Automatic Data Collector) Integration

## Overview

The EADC integration provides administrative services for clinical document transformation and validation within the Django NCP system. This is a **restricted administrative service** that requires proper authentication and authorization.

## Security Model

### User Roles

1. **EADC Administrators**
   - Full access to all EADC functions
   - Can perform document transformations
   - Can process patient documents
   - Can manage EADC settings
   - Requires `is_staff=True` OR membership in `eadc_administrators` group

2. **EADC Operators**
   - Can view documents and perform validation
   - Cannot perform transformations (read-only operations)
   - Can access demo documents
   - Requires membership in `eadc_operators` group

3. **Regular Users**
   - No access to EADC services
   - Redirected to admin login when attempting access

### Authentication & Authorization

- All EADC views require login (`@login_required`)
- Access control via `@user_passes_test` decorators
- Staff members (`is_staff=True`) automatically have admin privileges
- Group-based permissions for fine-grained access control

## Setup Instructions

### 1. Create User Groups and Permissions

Run the management command to set up EADC groups:

```bash
python manage.py setup_eadc_groups
```

To create demo users for testing:

```bash
python manage.py setup_eadc_groups --create-demo-users
```

This creates:

- `eadc_admin` user (password: `eadc_admin_password`)
- `eadc_operator` user (password: `eadc_operator_password`)

### 2. Assign Users to Groups

Via Django Admin:

1. Go to `/admin/auth/user/`
2. Edit user
3. Add to appropriate groups:
   - `eadc_administrators` for full access
   - `eadc_operators` for read-only access

Via Management Command (for existing users):

```python
from django.contrib.auth.models import User, Group

# Add user to administrators
user = User.objects.get(username='your_admin_user')
admin_group = Group.objects.get(name='eadc_administrators')
user.groups.add(admin_group)

# Add user to operators
user = User.objects.get(username='your_operator_user')
operator_group = Group.objects.get(name='eadc_operators')
user.groups.add(operator_group)
```

### 3. Configure EADC Resources Path

Update `patient_data/eadc_config.py` with the correct path to your EADC resources:

```python
EADC_CONFIG = {
    'EADC_RESOURCES_PATH': '/path/to/your/EADC_resources',
    # ... other settings
}
```

## Features

### Document Validation

- Validates CDA documents against epSOS schemas
- Checks for required elements and sections
- Identifies epSOS compliance status
- Provides detailed validation reports

### Document Transformation

- Transforms national CDA formats to epSOS standard
- Transforms epSOS format back to national formats
- Supports Patient Summary (PS), ePrescription (EP), eDispensation (ED)
- Maintains audit trail of all transformations

### Demo Document Processing

- Processes demo documents from EADC resources
- Creates sample clinical documents
- Demonstrates transformation pipeline
- Safe testing environment

### Patient Document Management

- Processes existing patient clinical documents
- Applies EADC transformations to patient data
- Updates document format and metadata
- Maintains document history

## API Endpoints

### Admin/Operator Access Required

- `/patient_data/eadc/` - Dashboard
- `/patient_data/eadc/validate/` - Document validation (AJAX)
- `/patient_data/eadc/demo/<type>/` - Process demo documents
- `/patient_data/eadc/patient/<id>/` - Patient document management
- `/patient_data/eadc/history/` - Transformation history
- `/patient_data/eadc/download/<id>/<format>/` - Download documents

### Admin-Only Access

- `/patient_data/eadc/transform/` - Document transformation (AJAX)
- `/patient_data/eadc/process_document/<id>/` - Process patient documents

## Configuration

### Supported Document Types

```python
SUPPORTED_DOCUMENT_TYPES = {
    'PS': {
        'name': 'Patient Summary',
        'template_id': '1.3.6.1.4.1.12559.11.10.1.3.1.1.3'
    },
    'EP': {
        'name': 'ePrescription',
        'template_id': '1.3.6.1.4.1.12559.11.10.1.3.1.1.1'
    },
    'ED': {
        'name': 'eDispensation',
        'template_id': '1.3.6.1.4.1.12559.11.10.1.3.1.1.2'
    }
}
```

### Security Settings

```python
SECURITY = {
    'REQUIRE_STAFF_ACCESS': True,
    'REQUIRE_GROUP_MEMBERSHIP': True,
    'LOG_ALL_ACTIVITIES': True,
    'AUDIT_RETENTION_DAYS': 90
}
```

## Audit and Logging

All EADC activities are logged with:

- User identification
- Timestamp
- Action performed
- Success/failure status
- Error details (if any)

Audit trails are maintained for:

- Document validations
- Document transformations
- User access attempts
- Administrative actions

## Error Handling

The system provides comprehensive error handling:

- Invalid document format errors
- Transformation failures
- Permission denied scenarios
- Resource not found errors
- Network/timeout issues

## Security Considerations

1. **Access Control**: Strict role-based access control
2. **Audit Logging**: All activities are logged
3. **Data Validation**: Input validation and sanitization
4. **Error Handling**: Secure error messages without information disclosure
5. **Session Management**: Proper authentication state management

## Troubleshooting

### Common Issues

1. **Access Denied**
   - Check user has proper group membership
   - Verify user is staff member (for admin functions)
   - Check EADC groups exist

2. **EADC Resources Not Found**
   - Verify `EADC_RESOURCES_PATH` in configuration
   - Check filesystem permissions
   - Ensure EADC resources directory exists

3. **Transformation Failures**
   - Check document format and structure
   - Verify required CDA elements are present
   - Review validation errors

### Debug Commands

```bash
# Check user groups
python manage.py shell
from django.contrib.auth.models import User
user = User.objects.get(username='your_user')
print(user.groups.all())

# Check EADC configuration
from patient_data.eadc_config import is_eadc_enabled
print(is_eadc_enabled())

# Test permissions
from patient_data.eadc_views import is_eadc_admin, is_eadc_operator
print(f"Admin: {is_eadc_admin(user)}")
print(f"Operator: {is_eadc_operator(user)}")
```

## Production Deployment

1. **Change Default Passwords**: Update demo user passwords
2. **Configure HTTPS**: Ensure secure communication
3. **Set Up Monitoring**: Monitor EADC service health
4. **Backup Strategy**: Include EADC audit logs in backups
5. **Resource Limits**: Configure appropriate resource limits
6. **Log Rotation**: Set up log rotation for audit files

## Integration with OpenNCP

The EADC service integrates with OpenNCP infrastructure:

- Uses real OpenNCP configuration files
- Supports standard epSOS transformations
- Compatible with OpenNCP member state mappings
- Follows epSOS clinical document specifications

This ensures compatibility with the broader OpenNCP ecosystem while providing a user-friendly administrative interface for document management.
