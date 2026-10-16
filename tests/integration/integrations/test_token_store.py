from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.db.redis import redis_client
from app.domain import TokenType
from app.integrations import RedisOneTimeTokenStore

pytestmark = pytest.mark.integration


async def test_one_time_token_store_rejects_replay() -> None:
    store = RedisOneTimeTokenStore(redis_client)
    token_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(seconds=30)

    first_use = await store.consume(
        token_type=TokenType.REFRESH,
        jti=token_id,
        expires_at=expires_at,
    )
    replay = await store.consume(
        token_type=TokenType.REFRESH,
        jti=token_id,
        expires_at=expires_at,
    )

    assert first_use is True
    assert replay is False
