# Patient Session Cleanup System

This document describes the comprehensive patient session cleanup system implemented to ensure HIPAA-compliant security for patient data in the Django NCP Server.

## 🎯 Overview

The patient session cleanup system provides multiple ways to remove sensitive patient data from user sessions:

1. **Automatic cleanup** on browser close/tab close
2. **Manual cleanup** via API endpoints and UI buttons
3. **Server startup cleanup** to clear orphaned sessions
4. **Middleware-based cleanup** for timeout and security enforcement
5. **Emergency cleanup** for immediate full session clearing

## 🔧 Components

### 1. API Endpoints (`eu_ncp_server/urls.py`)

#### `/api/clear-patient-session/` (POST)

- **Purpose**: Clear patient data from current session
- **Method**: POST
- **Response**: JSON with success status and items cleared
- **Usage**: Called by manual cleanup buttons or JavaScript

#### `/api/emergency-session-cleanup/` (POST)

- **Purpose**: Clear ALL session data (emergency use)
- **Method**: POST
- **Response**: JSON with success status
- **Usage**: Emergency situations requiring complete session reset

### 2. JavaScript Library (`templates/patient_session_cleanup.js`)

**Features:**

- Automatic cleanup on browser/tab close using `beforeunload` event
- Cleanup on page visibility changes (tab switching)
- Manual cleanup via button clicks
- Uses `sendBeacon` API for reliable cleanup during page unload
- Fallback to synchronous requests if `sendBeacon` unavailable

**Usage:**

```html
<script src="{% static 'js/patient_session_cleanup.js' %}"></script>
```

**API:**

```javascript
// Manual cleanup
window.clearPatientSession()

// Emergency cleanup
window.emergencySessionCleanup()

// Disable/enable automatic cleanup
window.patientSessionCleanup.disable()
window.patientSessionCleanup.enable()
```

### 3. UI Components (`templates/patient_session_cleanup_buttons.html`)

**Features:**

- Bootstrap-styled cleanup buttons
- Session activity monitor
- Keyboard shortcuts (Ctrl+Shift+C, Ctrl+Shift+E)
- Success/error message display
- Responsive design

**Usage:**

```django
{% include 'patient_session_cleanup_buttons.html' %}
```

### 4. Management Commands

#### `cleanup_patient_sessions`

- **Purpose**: Bulk cleanup of patient session data
- **Location**: `patient_data/management/commands/cleanup_patient_sessions.py`
- **Options**:
  - `--dry-run`: Show what would be cleaned
  - `--force`: Skip confirmations
  - `--unauthenticated-only`: Only clean unauthenticated sessions
  - `--expired-only`: Only clean expired sessions

**Usage:**

```bash
python manage.py cleanup_patient_sessions --dry-run
python manage.py cleanup_patient_sessions --unauthenticated-only --force
```

#### `startup_cleanup_patient_sessions`

- **Purpose**: Clean patient sessions on server startup
- **Location**: `patient_data/management/commands/startup_cleanup_patient_sessions.py`
- **Options**:
  - `--all-sessions`: Clean ALL sessions (including authenticated)
  - `--older-than-hours`: Only clean sessions older than specified hours
  - `--dry-run`: Show what would be cleaned
  - `--force`: Skip confirmations

**Usage:**

```bash
python manage.py startup_cleanup_patient_sessions --older-than-hours 24 --force
```

### 5. Security Middleware (`patient_data/middleware/patient_session_security.py`)

**Classes:**

#### `PatientSessionSecurityMiddleware`

- **Purpose**: Enforce patient session security policies
- **Features**:
  - Automatic timeout enforcement
  - Unauthenticated session cleanup
  - Security headers for patient data pages
  - Activity tracking

#### `PatientSessionCleanupMiddleware`

- **Purpose**: Clean patient data on logout
- **Features**:
  - Detects logout events
  - Automatic patient data cleanup
  - Logging of cleanup actions

**Configuration:**

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'patient_data.middleware.patient_session_security.PatientSessionSecurityMiddleware',
    'patient_data.middleware.patient_session_security.PatientSessionCleanupMiddleware',
]

# Session timeout settings
PATIENT_SESSION_TIMEOUT = 30  # minutes
PATIENT_MAX_INACTIVE_TIME = 60  # minutes
```

### 6. Startup Script (`startup_with_cleanup.py`)

**Purpose**: Start Django server with automatic cleanup
**Features**:

- Runs startup cleanup before server start
- Configurable cleanup options
- Informative startup messages

**Usage:**

```bash
python startup_with_cleanup.py
python startup_with_cleanup.py --port 8080 --all-sessions --force
python startup_with_cleanup.py --dry-run --older-than-hours 12
```

## 🚀 Quick Start

### 1. Basic Setup

Add the middleware to your Django settings:

```python
# settings.py
MIDDLEWARE = [
    # ... existing middleware
    'patient_data.middleware.patient_session_security.PatientSessionSecurityMiddleware',
    'patient_data.middleware.patient_session_security.PatientSessionCleanupMiddleware',
]
```

### 2. Include JavaScript in Templates

In your base template:

```html
<!-- Base template -->
<script src="{% static 'js/patient_session_cleanup.js' %}"></script>
```

### 3. Add UI Components to Patient Pages

In patient data templates:

```django
{% load static %}

<!-- Include cleanup buttons -->
{% include 'patient_session_cleanup_buttons.html' %}

<!-- Your patient data content -->
<div class="patient-data">
    <!-- Patient information -->
</div>
```

### 4. Server Startup with Cleanup

Instead of `python manage.py runserver`, use:

```bash
python startup_with_cleanup.py
```

## 🔒 Security Features

### Automatic Cleanup Triggers

1. **Browser/Tab Close**: JavaScript detects `beforeunload` and `unload` events
2. **Page Visibility**: Cleanup when tab becomes hidden for extended periods
3. **User Logout**: Middleware detects logout and clears patient data
4. **Session Timeout**: Automatic cleanup after configurable inactive time
5. **Unauthenticated Access**: Immediate cleanup if user loses authentication

### Security Headers

For patient data pages, the middleware adds:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cache-Control: no-cache, no-store, must-revalidate`
- `Pragma: no-cache`
- `Expires: 0`
- `X-Patient-Data-Page: true`

### Activity Tracking

The system tracks patient session activity:

- Updates `patient_last_activity` timestamp
- Enforces configurable timeout periods
- Logs cleanup actions for audit trails

## 🛠️ Configuration Options

### Settings.py Configuration

```python
# Patient session security settings
PATIENT_SESSION_TIMEOUT = 30  # minutes (default: 30)
PATIENT_MAX_INACTIVE_TIME = 60  # minutes (default: 60)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'patient_session_security.log',
        },
    },
    'loggers': {
        'patient_data.middleware.patient_session_security': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 📊 Monitoring and Logging

### Log Messages

The system logs various events:

- Patient session cleanups with reasons
- Security policy violations
- Timeout events
- Manual cleanup requests
- Server startup cleanup results

### Example Log Entries

```
INFO: Patient session security cleanup triggered by: patient_session_timeout. Cleared 3 patient data items.
WARNING: Cleared patient data from unauthenticated session: p4myrkjery4mzutbmxl2e...
INFO: Manual patient session cleanup requested by user admin: 2 items cleared
INFO: Server startup patient session cleanup completed: 5 sessions, 12 items removed, 0 errors
```

## 🎛️ Advanced Usage

### Custom Cleanup Logic

You can extend the cleanup functionality:

```python
# Custom cleanup in views
from eu_ncp_server.urls import clear_patient_session_data

def my_view(request):
    # Custom logic
    if some_condition:
        cleared_items = clear_patient_session_data(request)
        logger.info(f"Custom cleanup: {cleared_items} items cleared")
```

### JavaScript Event Handling

```javascript
// Listen for cleanup events
document.addEventListener('patientSessionCleared', function(event) {
    console.log('Patient session cleared:', event.detail);
    // Custom handling
});

// Trigger manual cleanup
window.patientSessionCleanup.manualCleanup()
    .then(result => {
        console.log('Cleanup successful:', result);
    })
    .catch(error => {
        console.error('Cleanup failed:', error);
    });
```

## 🔧 Troubleshooting

### Common Issues

1. **JavaScript not working**: Ensure `patient_session_cleanup.js` is loaded
2. **Middleware not running**: Check middleware order in settings
3. **Cleanup not triggered**: Verify endpoint URLs and CSRF tokens
4. **Sessions not cleaned**: Check user authentication status

### Debug Mode

Enable debug logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'patient_data.middleware.patient_session_security': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Testing Cleanup

```bash
# Test startup cleanup
python manage.py startup_cleanup_patient_sessions --dry-run

# Test bulk cleanup
python manage.py cleanup_patient_sessions --dry-run

# Test with curl
curl -X POST http://localhost:8000/api/clear-patient-session/
```

## 📋 Compliance Notes

This system helps ensure compliance with:

- **HIPAA**: Automatic patient data cleanup
- **GDPR**: Right to be forgotten implementation
- **Healthcare standards**: Secure session management

The system provides audit trails and configurable security policies to meet various compliance requirements.

## 🎯 Best Practices

1. **Always use HTTPS** for patient data pages
2. **Configure appropriate timeouts** for your use case
3. **Monitor cleanup logs** for security auditing
4. **Test cleanup functionality** regularly
5. **Train users** on manual cleanup options
6. **Use startup cleanup** in production deployments
7. **Implement custom cleanup logic** for specific requirements

## 🔄 Future Enhancements

Potential improvements:

- Integration with external session stores (Redis, Memcached)
- Advanced cleanup policies based on data sensitivity
- Real-time session monitoring dashboard
- Integration with security incident response systems
- Automated compliance reporting
