"""Asynchronous hand-off of authentication emails to Celery."""

import asyncio
from typing import Protocol
from urllib.parse import urlencode

from app.core.config import Settings
from app.tasks.email import send_email


class EmailDispatcher(Protocol):
    """Queue account emails without performing SMTP in the API process."""

    async def send_verification(self, email: str, token: str) -> None:
        """Queue an email-verification message."""
        ...

    async def send_password_reset(self, email: str, token: str) -> None:
        """Queue a password-reset message."""
        ...


class CeleryEmailDispatcher:
    """Publish email jobs to the Celery broker."""

    def __init__(self, settings: Settings) -> None:
        self._frontend_url = settings.frontend_url.rstrip("/")

    async def send_verification(self, email: str, token: str) -> None:
        query = urlencode({"token": token})
        link = f"{self._frontend_url}/verify-email?{query}"
        await asyncio.to_thread(
            send_email.delay,
            email,
            "Verify your Code Battle email",
            f"Open this link to verify your email:\n\n{link}\n",
        )

    async def send_password_reset(self, email: str, token: str) -> None:
        query = urlencode({"token": token})
        link = f"{self._frontend_url}/reset-password?{query}"
        await asyncio.to_thread(
            send_email.delay,
            email,
            "Reset your Code Battle password",
            f"Open this link to reset your password:\n\n{link}\n",
        )
