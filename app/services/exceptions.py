"""Business-layer exceptions translated by the HTTP layer."""

from uuid import UUID


class ServiceError(Exception):
    """Base class for application-service failures."""


class AuthenticationError(ServiceError):
    """Credentials or an authentication token cannot be accepted."""


class AuthorizationError(ServiceError):
    """The authenticated user lacks the required role."""


class UserNotFoundError(ServiceError):
    """A requested user does not exist."""

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User {user_id} was not found")
