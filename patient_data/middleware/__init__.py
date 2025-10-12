"""
Patient Data Middleware

This package contains middleware for ensuring GDPR-compliant patient data handling.

Session Isolation Middleware
----------------------------

The PatientSessionIsolationMiddleware ensures that each Django session contains data 
for only one patient at a time, preventing serious GDPR data breaches that could occur 
if patient data gets mixed between sessions.

Features:
- Automatic Session Isolation: Detects when a new patient is accessed and clears any existing patient data
- GDPR Compliance: Prevents mixing of patient data between sessions
- Comprehensive Logging: All isolation events are logged for audit trails
- Healthcare Data Security: Protects sensitive healthcare information

Usage:
Add to Django settings in MIDDLEWARE:
    'patient_data.middleware.session_isolation.PatientSessionIsolationMiddleware',

Security Benefits:
1. Data Isolation: Ensures one patient per session
2. Automatic Cleanup: Clears conflicting patient data automatically  
3. Audit Trail: Logs all isolation actions for compliance
4. GDPR Protection: Prevents unauthorized patient data mixing
"""
