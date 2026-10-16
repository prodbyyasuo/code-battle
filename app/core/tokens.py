"""JWT creation and validation with strict token-purpose separation."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.core.config import Settings
from app.domain import TokenType

_REQUIRED_CLAIMS = ("sub", "type", "jti", "iat", "exp", "iss", "aud")


class InvalidTokenError(Exception):
    """The JWT is invalid, expired, or has the wrong purpose."""


@dataclass(frozen=True, slots=True)
class TokenPayload:
    """Validated claims used by the application."""

    subject: UUID
    token_type: TokenType
    jti: UUID
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class EncodedTokenPair:
    """A newly issued access and refresh token pair."""

    access_token: str
    refresh_token: str
    access_expires_in: int


class TokenService:
    """Issue and validate all application JWTs."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._access_ttl = timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        self._refresh_ttl = timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
        self._email_verification_ttl = timedelta(
            hours=settings.jwt_email_verification_expire_hours
        )
        self._password_reset_ttl = timedelta(
            minutes=settings.jwt_password_reset_expire_minutes
        )

    def create_pair(self, subject: UUID) -> EncodedTokenPair:
        """Create an access token and an independently identified refresh."""
        return EncodedTokenPair(
            access_token=self._encode(
                subject=subject,
                token_type=TokenType.ACCESS,
                ttl=self._access_ttl,
            ),
            refresh_token=self._encode(
                subject=subject,
                token_type=TokenType.REFRESH,
                ttl=self._refresh_ttl,
            ),
            access_expires_in=int(self._access_ttl.total_seconds()),
        )

    def create_email_verification_token(self, subject: UUID) -> str:
        """Create a short-lived one-time email verification token."""
        return self._encode(
            subject=subject,
            token_type=TokenType.EMAIL_VERIFICATION,
            ttl=self._email_verification_ttl,
        )

    def create_password_reset_token(self, subject: UUID) -> str:
        """Create a short-lived one-time password reset token."""
        return self._encode(
            subject=subject,
            token_type=TokenType.PASSWORD_RESET,
            ttl=self._password_reset_ttl,
        )

    def decode(
        self,
        token: str,
        *,
        expected_type: TokenType,
    ) -> TokenPayload:
        """Validate signature, lifetime, required claims, and token purpose."""
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": list(_REQUIRED_CLAIMS)},
            )
            token_type = TokenType(str(claims["type"]))
            if token_type is not expected_type:
                raise InvalidTokenError("Unexpected token type")

            return TokenPayload(
                subject=UUID(str(claims["sub"])),
                token_type=token_type,
                jti=UUID(str(claims["jti"])),
                issued_at=datetime.fromtimestamp(
                    int(claims["iat"]),
                    UTC,
                ),
                expires_at=datetime.fromtimestamp(
                    int(claims["exp"]),
                    UTC,
                ),
            )
        except InvalidTokenError:
            raise
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise InvalidTokenError("Invalid token") from error

    def _encode(
        self,
        *,
        subject: UUID,
        token_type: TokenType,
        ttl: timedelta,
    ) -> str:
        now = datetime.now(UTC)
        claims = {
            "sub": str(subject),
            "type": token_type.value,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + ttl,
            "iss": self._issuer,
            "aud": self._audience,
        }
        return jwt.encode(
            claims,
            self._secret,
            algorithm=self._algorithm,
        )
