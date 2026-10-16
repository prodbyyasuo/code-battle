from typing import cast

from app.main import create_app


def test_stage_four_routes_are_registered() -> None:
    paths = cast(dict[str, object], create_app().openapi()["paths"])

    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths
    assert "/api/v1/auth/email-verification/request" in paths
    assert "/api/v1/auth/email-verification/confirm" in paths
    assert "/api/v1/auth/password-reset/request" in paths
    assert "/api/v1/auth/password-reset/confirm" in paths
    assert "/api/v1/users/me" in paths
    assert "/api/v1/users/{user_id}" in paths
