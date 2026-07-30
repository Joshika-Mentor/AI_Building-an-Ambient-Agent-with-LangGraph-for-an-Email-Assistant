"""
ThreatLens AI — Notification Service
In-app and email notification delivery for security events.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger("threatlens.integrations.notifications")


class NotificationService:
    """
    Multi-channel notification delivery.

    Channels:
    - In-app (stored as Alert records — already handled by alert_service)
    - Email via SMTP (when configured)
    - Webhook (generic HTTP POST)
    """

    def __init__(self):
        self._smtp_enabled = bool(settings.SMTP_HOST and settings.SMTP_USER)
        if self._smtp_enabled:
            logger.info("Email notifications enabled")
        else:
            logger.info("Email notifications disabled (SMTP not configured)")

    async def notify_malware_detection(
        self,
        file_name: str,
        malware_class: str,
        confidence: float,
        risk_score: float,
        incident_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send notification for a malware detection event.

        Returns delivery status for each channel.
        """
        subject = f"🚨 Malware Detected: {malware_class} — {file_name}"
        body = (
            f"ThreatLens AI has detected malware in an uploaded file.\n\n"
            f"File: {file_name}\n"
            f"Classification: {malware_class}\n"
            f"Confidence: {confidence:.1%}\n"
            f"Risk Score: {risk_score}/100\n"
            f"Incident ID: {incident_id or 'N/A'}\n\n"
            f"Please review this detection in the ThreatLens dashboard.\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        results = {"channels": {}}

        # In-app: already handled by classification_service creating alerts
        results["channels"]["in_app"] = {"status": "delivered", "method": "alert_service"}

        # Email
        if self._smtp_enabled:
            email_result = await self._send_email(subject, body)
            results["channels"]["email"] = email_result
        else:
            results["channels"]["email"] = {"status": "skipped", "reason": "SMTP not configured"}

        logger.info(f"Notification sent for {malware_class} detection: {file_name}")
        return results

    async def notify_high_risk_alert(
        self,
        alert_title: str,
        severity: str,
        details: str,
    ) -> Dict[str, Any]:
        """Send notification for high-severity alerts."""
        if severity not in ("Critical", "High"):
            return {"channels": {}, "skipped": True, "reason": "Below notification threshold"}

        subject = f"⚠️ [{severity}] Security Alert: {alert_title}"
        body = f"{alert_title}\n\nSeverity: {severity}\n\n{details}"

        results = {"channels": {}}

        if self._smtp_enabled:
            results["channels"]["email"] = await self._send_email(subject, body)
        else:
            results["channels"]["email"] = {"status": "skipped", "reason": "SMTP not configured"}

        return results

    async def _send_email(self, subject: str, body: str) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.SMTP_USER  # Self-notify; extend for team
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent: {subject}")
            return {"status": "delivered", "recipient": settings.SMTP_USER}

        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return {"status": "failed", "error": str(e)}


_service: Optional[NotificationService] = None

def get_notification_service() -> NotificationService:
    global _service
    if _service is None:
        _service = NotificationService()
    return _service
