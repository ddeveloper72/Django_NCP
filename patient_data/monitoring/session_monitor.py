"""
Session Monitoring and Analytics
EU NCP Portal - Healthcare Session Monitoring

Provides comprehensive monitoring, analytics, and alerting for patient
data access sessions with security event detection and compliance reporting.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg, Max, Min
from django.core.mail import send_mail
from django.conf import settings
from collections import defaultdict, Counter
import hashlib

from patient_data.models.session_management import PatientSession, SessionAuditLog

logger = logging.getLogger(__name__)


class SecurityEventDetector:
    """
    Detects security events and anomalies in patient session data.

    Monitors for:
    - Unusual access patterns
    - Potential session hijacking
    - Brute force attempts
    - Data exfiltration patterns
    """

    # Security thresholds
    MAX_FAILED_ATTEMPTS = 5
    SUSPICIOUS_ACCESS_RATE = 30  # requests per minute
    SESSION_HIJACK_INDICATORS = ["ip_change", "ua_change", "geo_change"]

    def __init__(self):
        self.alert_handlers = []

    def add_alert_handler(self, handler):
        """Add alert handler for security events."""
        self.alert_handlers.append(handler)

    def detect_anomalies(self, time_window_hours: int = 24) -> List[Dict]:
        """
        Detect security anomalies in the specified time window.

        Returns list of detected security events.
        """
        anomalies = []
        cutoff_time = timezone.now() - timedelta(hours=time_window_hours)

        # Detect multiple failed login attempts
        anomalies.extend(self._detect_brute_force_attempts(cutoff_time))

        # Detect unusual access patterns
        anomalies.extend(self._detect_unusual_access_patterns(cutoff_time))

        # Detect potential session hijacking
        anomalies.extend(self._detect_session_hijacking(cutoff_time))

        # Detect data exfiltration patterns
        anomalies.extend(self._detect_data_exfiltration(cutoff_time))

        # Send alerts for detected anomalies
        for anomaly in anomalies:
            self._send_security_alert(anomaly)

        return anomalies

    def _detect_brute_force_attempts(self, cutoff_time: datetime) -> List[Dict]:
        """Detect potential brute force login attempts."""
        anomalies = []

        # Group failed attempts by IP address
        failed_attempts = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time,
                success=False,
                action__in=["session_creation_failed", "unauthorized_access_attempt"],
            )
            .values("client_ip")
            .annotate(attempt_count=Count("id"))
            .filter(attempt_count__gte=self.MAX_FAILED_ATTEMPTS)
        )

        for attempt in failed_attempts:
            anomalies.append(
                {
                    "type": "brute_force_attempt",
                    "severity": "high",
                    "source_ip": attempt["client_ip"],
                    "attempt_count": attempt["attempt_count"],
                    "time_window": cutoff_time,
                    "description": f"Multiple failed access attempts from IP {attempt['client_ip']}",
                }
            )

        return anomalies

    def _detect_unusual_access_patterns(self, cutoff_time: datetime) -> List[Dict]:
        """Detect unusual access rate patterns."""
        anomalies = []

        # Find sessions with unusually high access rates
        high_activity_sessions = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, action="session_access"
            )
            .values("session__session_id")
            .annotate(access_count=Count("id"))
            .filter(access_count__gte=self.SUSPICIOUS_ACCESS_RATE * 60)
        )  # per hour

        for session_data in high_activity_sessions:
            session_id = session_data["session__session_id"]
            access_count = session_data["access_count"]

            anomalies.append(
                {
                    "type": "unusual_access_pattern",
                    "severity": "medium",
                    "session_id": session_id,
                    "access_count": access_count,
                    "time_window": cutoff_time,
                    "description": f"Unusually high access rate for session {session_id}",
                }
            )

        return anomalies

    def _detect_session_hijacking(self, cutoff_time: datetime) -> List[Dict]:
        """Detect potential session hijacking indicators."""
        anomalies = []

        # Find sessions with IP address changes
        ip_changes = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, action="session_access"
            )
            .values("session__session_id")
            .annotate(unique_ips=Count("client_ip", distinct=True))
            .filter(unique_ips__gt=1)
        )

        for session_data in ip_changes:
            session_id = session_data["session__session_id"]
            unique_ips = session_data["unique_ips"]

            # Get the actual IP addresses for this session
            ips = (
                SessionAuditLog.objects.filter(
                    session__session_id=session_id, timestamp__gte=cutoff_time
                )
                .values_list("client_ip", flat=True)
                .distinct()
            )

            anomalies.append(
                {
                    "type": "potential_session_hijacking",
                    "severity": "high",
                    "session_id": session_id,
                    "ip_addresses": list(ips),
                    "unique_ip_count": unique_ips,
                    "time_window": cutoff_time,
                    "description": f"Session {session_id} accessed from multiple IP addresses",
                }
            )

        return anomalies

    def _detect_data_exfiltration(self, cutoff_time: datetime) -> List[Dict]:
        """Detect potential data exfiltration patterns."""
        anomalies = []

        # Find sessions with unusually large data transfers
        large_transfers = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, content_length__gt=1024 * 1024  # > 1MB
            )
            .values("session__session_id")
            .annotate(
                total_data=Count("content_length"), avg_size=Avg("content_length")
            )
        )

        for transfer in large_transfers:
            session_id = transfer["session__session_id"]

            anomalies.append(
                {
                    "type": "potential_data_exfiltration",
                    "severity": "medium",
                    "session_id": session_id,
                    "total_transfers": transfer["total_data"],
                    "avg_size_mb": transfer["avg_size"] / (1024 * 1024),
                    "time_window": cutoff_time,
                    "description": f"Large data transfers detected for session {session_id}",
                }
            )

        return anomalies

    def _send_security_alert(self, anomaly: Dict) -> None:
        """Send security alert for detected anomaly."""

        # Log the anomaly
        logger.warning(f"Security anomaly detected: {anomaly}")

        # Send alerts through registered handlers
        for handler in self.alert_handlers:
            try:
                handler(anomaly)
            except Exception as e:
                logger.error(f"Error sending security alert: {e}")


class SessionAnalytics:
    """
    Provides analytics and reporting for patient session usage.

    Generates reports for:
    - Session usage patterns
    - Security metrics
    - Performance analytics
    - Compliance reporting
    """

    def generate_usage_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive usage report."""
        cutoff_time = timezone.now() - timedelta(days=days)

        # Basic session statistics
        total_sessions = PatientSession.objects.filter(
            created_at__gte=cutoff_time
        ).count()
        active_sessions = PatientSession.objects.filter(
            created_at__gte=cutoff_time, status="active"
        ).count()
        expired_sessions = PatientSession.objects.filter(
            created_at__gte=cutoff_time, status="expired"
        ).count()

        # User activity statistics
        unique_users = (
            PatientSession.objects.filter(created_at__gte=cutoff_time)
            .values("user")
            .distinct()
            .count()
        )

        # Access pattern analysis
        hourly_distribution = self._get_hourly_access_distribution(cutoff_time)
        daily_distribution = self._get_daily_access_distribution(cutoff_time)

        # Performance metrics
        avg_session_duration = self._get_average_session_duration(cutoff_time)
        session_performance = self._get_session_performance_metrics(cutoff_time)

        # Security metrics
        security_events = self._get_security_event_summary(cutoff_time)

        return {
            "report_period": {
                "start_date": cutoff_time.isoformat(),
                "end_date": timezone.now().isoformat(),
                "days": days,
            },
            "session_statistics": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "unique_users": unique_users,
            },
            "access_patterns": {
                "hourly_distribution": hourly_distribution,
                "daily_distribution": daily_distribution,
            },
            "performance_metrics": {
                "average_session_duration_minutes": avg_session_duration,
                "performance_stats": session_performance,
            },
            "security_metrics": security_events,
        }

    def _get_hourly_access_distribution(self, cutoff_time: datetime) -> List[Dict]:
        """Get access distribution by hour of day."""

        hourly_stats = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, action="session_access"
            )
            .extra(select={"hour": "EXTRACT(hour FROM timestamp)"})
            .values("hour")
            .annotate(access_count=Count("id"))
            .order_by("hour")
        )

        return list(hourly_stats)

    def _get_daily_access_distribution(self, cutoff_time: datetime) -> List[Dict]:
        """Get access distribution by day of week."""

        daily_stats = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, action="session_access"
            )
            .extra(select={"day_of_week": "EXTRACT(dow FROM timestamp)"})
            .values("day_of_week")
            .annotate(access_count=Count("id"))
            .order_by("day_of_week")
        )

        return list(daily_stats)

    def _get_average_session_duration(self, cutoff_time: datetime) -> float:
        """Calculate average session duration in minutes."""

        completed_sessions = PatientSession.objects.filter(
            created_at__gte=cutoff_time, status__in=["expired", "terminated"]
        )

        total_duration = 0
        session_count = 0

        for session in completed_sessions:
            if session.last_accessed and session.created_at:
                duration = session.last_accessed - session.created_at
                total_duration += duration.total_seconds()
                session_count += 1

        if session_count > 0:
            return total_duration / session_count / 60  # Convert to minutes
        return 0.0

    def _get_session_performance_metrics(self, cutoff_time: datetime) -> Dict:
        """Get session performance metrics."""

        performance_stats = SessionAuditLog.objects.filter(
            timestamp__gte=cutoff_time, duration_ms__isnull=False
        ).aggregate(
            avg_response_time=Avg("duration_ms"),
            max_response_time=Max("duration_ms"),
            min_response_time=Min("duration_ms"),
        )

        # Count by status code
        status_distribution = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, response_status__isnull=False
            )
            .values("response_status")
            .annotate(count=Count("id"))
        )

        return {
            "response_times": performance_stats,
            "status_code_distribution": list(status_distribution),
        }

    def _get_security_event_summary(self, cutoff_time: datetime) -> Dict:
        """Get summary of security events."""

        failed_attempts = SessionAuditLog.objects.filter(
            timestamp__gte=cutoff_time, success=False
        ).count()

        unauthorized_attempts = SessionAuditLog.objects.filter(
            timestamp__gte=cutoff_time, action="unauthorized_access_attempt"
        ).count()

        session_rotations = SessionAuditLog.objects.filter(
            timestamp__gte=cutoff_time, action="session_rotated"
        ).count()

        return {
            "failed_attempts": failed_attempts,
            "unauthorized_attempts": unauthorized_attempts,
            "session_rotations": session_rotations,
        }

    def generate_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for auditing."""
        cutoff_time = timezone.now() - timedelta(days=days)

        # Data access audit
        data_access_logs = (
            SessionAuditLog.objects.filter(
                timestamp__gte=cutoff_time, action="session_access"
            )
            .values("session__user__username", "resource")
            .annotate(access_count=Count("id"))
        )

        # Security event summary
        security_events = (
            SessionAuditLog.objects.filter(timestamp__gte=cutoff_time, success=False)
            .values("action")
            .annotate(event_count=Count("id"))
        )

        # Session lifecycle compliance
        session_lifecycle = (
            PatientSession.objects.filter(created_at__gte=cutoff_time)
            .values("status")
            .annotate(count=Count("id"))
        )

        return {
            "compliance_period": {
                "start_date": cutoff_time.isoformat(),
                "end_date": timezone.now().isoformat(),
            },
            "data_access_audit": list(data_access_logs),
            "security_events": list(security_events),
            "session_lifecycle": list(session_lifecycle),
            "audit_trail_completeness": self._verify_audit_trail_completeness(
                cutoff_time
            ),
        }

    def _verify_audit_trail_completeness(self, cutoff_time: datetime) -> Dict:
        """Verify audit trail completeness for compliance."""

        # Check for sessions without corresponding audit logs
        sessions_without_logs = (
            PatientSession.objects.filter(created_at__gte=cutoff_time)
            .exclude(sessionauditlog__action="session_created")
            .count()
        )

        # Check for orphaned audit logs
        orphaned_logs = SessionAuditLog.objects.filter(
            timestamp__gte=cutoff_time, session__isnull=True
        ).count()

        total_sessions = PatientSession.objects.filter(
            created_at__gte=cutoff_time
        ).count()
        total_logs = SessionAuditLog.objects.filter(timestamp__gte=cutoff_time).count()

        return {
            "total_sessions": total_sessions,
            "total_audit_logs": total_logs,
            "sessions_without_logs": sessions_without_logs,
            "orphaned_logs": orphaned_logs,
            "audit_coverage_percentage": (
                ((total_sessions - sessions_without_logs) / total_sessions * 100)
                if total_sessions > 0
                else 100
            ),
        }


class AlertHandler:
    """
    Handles security alerts and notifications.
    """

    def __init__(self):
        self.email_recipients = getattr(settings, "SECURITY_ALERT_RECIPIENTS", [])

    def handle_security_alert(self, anomaly: Dict) -> None:
        """Handle security alert by sending notifications."""

        # Log the alert
        logger.critical(f"SECURITY ALERT: {anomaly['type']} - {anomaly['description']}")

        # Send email notification if configured
        if self.email_recipients:
            self._send_email_alert(anomaly)

        # Could integrate with external systems here
        # - Slack notifications
        # - PagerDuty alerts
        # - SIEM system integration

    def _send_email_alert(self, anomaly: Dict) -> None:
        """Send email alert for security anomaly."""

        subject = f"Security Alert: {anomaly['type']}"
        message = f"""
        Security Anomaly Detected

        Type: {anomaly['type']}
        Severity: {anomaly['severity']}
        Description: {anomaly['description']}

        Details:
        {json.dumps(anomaly, indent=2, default=str)}

        Please investigate immediately.
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=self.email_recipients,
                fail_silently=False,
            )
            logger.info(f"Security alert email sent for {anomaly['type']}")
        except Exception as e:
            logger.error(f"Failed to send security alert email: {e}")


class SessionMonitor:
    """
    Main session monitoring coordinator.

    Coordinates security detection, analytics, and alerting.
    """

    def __init__(self):
        self.detector = SecurityEventDetector()
        self.analytics = SessionAnalytics()
        self.alert_handler = AlertHandler()

        # Register alert handler
        self.detector.add_alert_handler(self.alert_handler.handle_security_alert)

    def run_security_scan(self, hours: int = 24) -> List[Dict]:
        """Run comprehensive security scan."""
        logger.info(f"Running security scan for last {hours} hours")

        # Detect anomalies
        anomalies = self.detector.detect_anomalies(hours)

        logger.info(f"Security scan completed. Found {len(anomalies)} anomalies")
        return anomalies

    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily monitoring report."""
        logger.info("Generating daily session monitoring report")

        usage_report = self.analytics.generate_usage_report(days=1)
        compliance_report = self.analytics.generate_compliance_report(days=1)
        security_anomalies = self.detector.detect_anomalies(time_window_hours=24)

        return {
            "report_date": timezone.now().isoformat(),
            "usage_statistics": usage_report,
            "compliance_metrics": compliance_report,
            "security_anomalies": security_anomalies,
        }

    def get_session_health_status(self) -> Dict[str, Any]:
        """Get current session system health status."""

        # Active sessions count
        active_sessions = PatientSession.objects.filter(status="active").count()

        # Recent errors
        recent_errors = SessionAuditLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1), success=False
        ).count()

        # System performance
        avg_response_time = (
            SessionAuditLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1),
                duration_ms__isnull=False,
            ).aggregate(avg_time=Avg("duration_ms"))["avg_time"]
            or 0
        )

        # Health score calculation
        health_score = self._calculate_health_score(
            active_sessions, recent_errors, avg_response_time
        )

        return {
            "timestamp": timezone.now().isoformat(),
            "active_sessions": active_sessions,
            "recent_errors_1h": recent_errors,
            "avg_response_time_ms": avg_response_time,
            "health_score": health_score,
            "status": (
                "healthy"
                if health_score > 80
                else "degraded" if health_score > 60 else "critical"
            ),
        }

    def _calculate_health_score(
        self, active_sessions: int, recent_errors: int, avg_response_time: float
    ) -> int:
        """Calculate system health score (0-100)."""

        score = 100

        # Deduct for high error rate
        if recent_errors > 10:
            score -= min(50, recent_errors * 2)

        # Deduct for slow response times
        if avg_response_time > 1000:  # > 1 second
            score -= min(30, (avg_response_time - 1000) / 100)

        # Deduct for too many active sessions (potential DoS)
        if active_sessions > 1000:
            score -= min(20, (active_sessions - 1000) / 100)

        return max(0, int(score))


# Global monitor instance
session_monitor = SessionMonitor()
