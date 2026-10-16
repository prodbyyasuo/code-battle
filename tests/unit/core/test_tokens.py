from uuid import uuid4

import pytest

from app.core.config import get_settings
from app.core.tokens import InvalidTokenError, TokenService
from app.domain import TokenType


@pytest.fixture
def tokens() -> TokenService:
    return TokenService(get_settings())


def test_token_pair_has_required_distinct_purposes(
    tokens: TokenService,
) -> None:
    user_id = uuid4()

    pair = tokens.create_pair(user_id)
    access = tokens.decode(
        pair.access_token,
        expected_type=TokenType.ACCESS,
    )
    refresh = tokens.decode(
        pair.refresh_token,
        expected_type=TokenType.REFRESH,
    )

    assert access.subject == user_id
    assert refresh.subject == user_id
    assert access.jti != refresh.jti
    assert pair.access_expires_in > 0


def test_refresh_token_cannot_be_used_as_access(
    tokens: TokenService,
) -> None:
    pair = tokens.create_pair(uuid4())

    with pytest.raises(InvalidTokenError):
        tokens.decode(
            pair.refresh_token,
            expected_type=TokenType.ACCESS,
        )


def test_tampered_token_is_rejected(tokens: TokenService) -> None:
    pair = tokens.create_pair(uuid4())
    tampered = f"{pair.access_token[:-1]}x"

    with pytest.raises(InvalidTokenError):
        tokens.decode(tampered, expected_type=TokenType.ACCESS)


def test_account_action_tokens_are_not_interchangeable(
    tokens: TokenService,
) -> None:
    verification = tokens.create_email_verification_token(uuid4())

    with pytest.raises(InvalidTokenError):
        tokens.decode(
            verification,
            expected_type=TokenType.PASSWORD_RESET,
        )
