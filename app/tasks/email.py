"""Blocking SMTP delivery isolated inside Celery workers."""

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="auth.send_email",
    autoretry_for=(OSError, smtplib.SMTPException),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)  # type: ignore[untyped-decorator]
def send_email(recipient: str, subject: str, body: str) -> None:
    """Deliver one text email; retries happen entirely in the worker."""
    settings = get_settings()
    if settings.smtp_host is None:
        logger.warning(
            "SMTP_HOST is not configured; email to %s was skipped",
            recipient,
        )
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(
                settings.smtp_username,
                settings.smtp_password.get_secret_value(),
            )
        smtp.send_message(message)
