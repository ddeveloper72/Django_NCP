"""
Session Security Configuration and Key Management
EU NCP Portal - Healthcare Session Security

Provides secure key management, session encryption, and security utilities
for patient data session protection with rotating encryption keys.
"""

import os
import base64
import secrets
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class SessionSecurityConfig:
    """
    Configuration manager for session security settings.
    """

    # Default security settings
    DEFAULT_SESSION_TIMEOUT = 30  # minutes
    DEFAULT_ENCRYPTION_KEY_ROTATION = 24  # hours
    DEFAULT_MAX_CONCURRENT_SESSIONS = 3
    DEFAULT_RATE_LIMIT_REQUESTS = 60  # per minute

    @classmethod
    def get_session_timeout(cls) -> int:
        """Get session timeout in minutes."""
        return getattr(settings, "PATIENT_SESSION_TIMEOUT", cls.DEFAULT_SESSION_TIMEOUT)

    @classmethod
    def get_encryption_key_rotation_hours(cls) -> int:
        """Get encryption key rotation interval in hours."""
        return getattr(
            settings, "SESSION_KEY_ROTATION_HOURS", cls.DEFAULT_ENCRYPTION_KEY_ROTATION
        )

    @classmethod
    def get_max_concurrent_sessions(cls) -> int:
        """Get maximum concurrent sessions per user."""
        return getattr(
            settings,
            "MAX_CONCURRENT_PATIENT_SESSIONS",
            cls.DEFAULT_MAX_CONCURRENT_SESSIONS,
        )

    @classmethod
    def get_rate_limit_requests(cls) -> int:
        """Get rate limit requests per minute."""
        return getattr(
            settings, "PATIENT_SESSION_RATE_LIMIT", cls.DEFAULT_RATE_LIMIT_REQUESTS
        )

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return getattr(settings, "DEBUG", True) is False

    @classmethod
    def get_encryption_algorithm(cls) -> str:
        """Get encryption algorithm for session data."""
        return getattr(settings, "SESSION_ENCRYPTION_ALGORITHM", "Fernet")


class EncryptionKeyManager:
    """
    Manages encryption keys for patient session data.

    Features:
    - Rotating encryption keys
    - Key derivation from master secret
    - Secure key storage and retrieval
    - Key versioning for data migration
    """

    CACHE_KEY_PREFIX = "session_encryption_key"
    MASTER_KEY_ENV_VAR = "PATIENT_SESSION_MASTER_KEY"

    def __init__(self):
        self.master_key = self._get_or_create_master_key()

    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key."""

        # Try to get from environment variable
        master_key_b64 = os.environ.get(self.MASTER_KEY_ENV_VAR)
        if master_key_b64:
            try:
                return base64.urlsafe_b64decode(master_key_b64)
            except Exception as e:
                logger.error(f"Invalid master key in environment: {e}")

        # Generate new master key if not found
        if SessionSecurityConfig.is_production():
            raise ValueError(
                f"Master key not found in environment variable {self.MASTER_KEY_ENV_VAR}. "
                "Please set this in production environment."
            )

        # Development: generate and log temporary key
        master_key = secrets.token_bytes(32)
        master_key_b64 = base64.urlsafe_b64encode(master_key).decode()
        logger.warning(
            f"Generated temporary master key for development: {master_key_b64}\n"
            f"Set {self.MASTER_KEY_ENV_VAR}={master_key_b64} in production"
        )
        return master_key

    def get_current_key(self) -> Fernet:
        """Get current encryption key for new sessions."""
        key_version = self._get_current_key_version()
        return self._get_key_for_version(key_version)

    def get_key_for_session(self, key_version: int) -> Fernet:
        """Get encryption key for specific session (by version)."""
        return self._get_key_for_version(key_version)

    def _get_current_key_version(self) -> int:
        """Get current key version based on time rotation."""
        rotation_hours = SessionSecurityConfig.get_encryption_key_rotation_hours()
        epoch_hours = int(timezone.now().timestamp() // 3600)
        return epoch_hours // rotation_hours

    def _get_key_for_version(self, version: int) -> Fernet:
        """Get encryption key for specific version."""
        cache_key = f"{self.CACHE_KEY_PREFIX}_{version}"

        # Try to get from cache first
        fernet_key = cache.get(cache_key)
        if fernet_key:
            return Fernet(fernet_key)

        # Derive key from master key and version
        derived_key = self._derive_key(version)
        fernet_key = base64.urlsafe_b64encode(derived_key)

        # Cache for 1 hour (but keep old keys for decryption)
        cache.set(cache_key, fernet_key, 3600)

        return Fernet(fernet_key)

    def _derive_key(self, version: int) -> bytes:
        """Derive encryption key from master key and version."""

        # Create salt from version
        salt = hashlib.sha256(f"session_key_v{version}".encode()).digest()

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key)

    def rotate_keys(self) -> None:
        """Force key rotation (for emergency key rotation)."""
        current_version = self._get_current_key_version()

        # Clear cached keys
        for i in range(max(0, current_version - 10), current_version + 2):
            cache_key = f"{self.CACHE_KEY_PREFIX}_{i}"
            cache.delete(cache_key)

        logger.info(f"Encryption keys rotated, current version: {current_version}")


class SessionEncryption:
    """
    Handles encryption and decryption of session data.
    """

    def __init__(self):
        self.key_manager = EncryptionKeyManager()

    def encrypt_session_data(self, data: Dict) -> Tuple[bytes, int]:
        """
        Encrypt session data.

        Returns:
            Tuple of (encrypted_data, key_version)
        """
        import json

        # Serialize data to JSON
        json_data = json.dumps(data, default=str)

        # Get current encryption key
        fernet = self.key_manager.get_current_key()
        key_version = self.key_manager._get_current_key_version()

        # Encrypt data
        encrypted_data = fernet.encrypt(json_data.encode())

        return encrypted_data, key_version

    def decrypt_session_data(self, encrypted_data: bytes, key_version: int) -> Dict:
        """
        Decrypt session data using specified key version.

        Args:
            encrypted_data: Encrypted data bytes
            key_version: Key version used for encryption

        Returns:
            Decrypted data dictionary
        """
        import json

        try:
            # Get the specific key version
            fernet = self.key_manager.get_key_for_session(key_version)

            # Decrypt data
            decrypted_bytes = fernet.decrypt(encrypted_data)
            json_data = decrypted_bytes.decode()

            # Parse JSON
            return json.loads(json_data)

        except Exception as e:
            logger.error(
                f"Failed to decrypt session data with key version {key_version}: {e}"
            )
            raise ValueError("Unable to decrypt session data")


class SessionValidator:
    """
    Validates session security and integrity.
    """

    @staticmethod
    def validate_session_token(token: str) -> bool:
        """Validate session token format and entropy."""

        # Check token format (UUID-like)
        if not token or len(token) < 32:
            return False

        # Check if token has sufficient entropy
        entropy = len(set(token))
        if entropy < 16:  # Should have at least 16 unique characters
            return False

        return True

    @staticmethod
    def validate_client_fingerprint(request, session) -> bool:
        """Validate client fingerprint for session security."""

        # Basic User-Agent consistency check
        current_ua = request.META.get("HTTP_USER_AGENT", "")
        current_ua_hash = hashlib.sha256(current_ua.encode()).hexdigest()

        # Check if user agent has changed (potential session hijacking)
        if hasattr(session, "user_agent_hash") and session.user_agent_hash:
            if session.user_agent_hash != current_ua_hash:
                logger.warning(f"User agent changed for session {session.session_id}")
                return False

        return True

    @staticmethod
    def check_suspicious_activity(session) -> bool:
        """Check for suspicious session activity patterns."""

        # Check access frequency
        if session.access_count > 1000:  # Very high access count
            recent_accesses = session.get_recent_access_count(minutes=5)
            if recent_accesses > 50:  # Too many accesses in short time
                logger.warning(
                    f"Suspicious high-frequency access for session {session.session_id}"
                )
                return True

        # Check geographic consistency (if IP geolocation available)
        # This would require external service integration

        return False


class SessionSecurity:
    """
    Main session security manager.

    Coordinates all security components for patient sessions.
    """

    def __init__(self):
        self.encryption = SessionEncryption()
        self.validator = SessionValidator()
        self.config = SessionSecurityConfig()

    def create_secure_token(self) -> str:
        """Create cryptographically secure session token."""
        return secrets.token_urlsafe(32)

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for secure storage."""
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_session_integrity(self, session, request) -> bool:
        """Comprehensive session integrity check."""

        # Validate token format
        if not self.validator.validate_session_token(session.session_id):
            logger.error(f"Invalid token format for session {session.session_id}")
            return False

        # Check client fingerprint
        if not self.validator.validate_client_fingerprint(request, session):
            logger.warning(
                f"Client fingerprint mismatch for session {session.session_id}"
            )
            return False

        # Check for suspicious activity
        if self.validator.check_suspicious_activity(session):
            logger.warning(
                f"Suspicious activity detected for session {session.session_id}"
            )
            return False

        # Check session expiration
        if session.is_expired():
            logger.info(f"Session {session.session_id} has expired")
            return False

        return True

    def encrypt_patient_data(self, data: Dict) -> Tuple[bytes, int]:
        """Encrypt patient data for secure storage."""
        return self.encryption.encrypt_session_data(data)

    def decrypt_patient_data(self, encrypted_data: bytes, key_version: int) -> Dict:
        """Decrypt patient data from secure storage."""
        return self.encryption.decrypt_session_data(encrypted_data, key_version)

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        timestamp = str(int(timezone.now().timestamp()))
        token_data = f"{session_id}:{timestamp}"
        return hashlib.sha256(token_data.encode()).hexdigest()

    def validate_csrf_token(
        self, session_id: str, token: str, max_age_minutes: int = 60
    ) -> bool:
        """Validate CSRF token for session."""
        try:
            # Extract timestamp from regenerated token
            current_time = int(timezone.now().timestamp())

            # Try different timestamps within the valid window
            for offset in range(0, max_age_minutes * 60, 60):
                test_timestamp = current_time - offset
                test_token_data = f"{session_id}:{test_timestamp}"
                test_token = hashlib.sha256(test_token_data.encode()).hexdigest()

                if test_token == token:
                    return True

            return False

        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False


# Global security instance
session_security = SessionSecurity()
