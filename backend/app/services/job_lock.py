import logging
import uuid
from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LockHandle:
    key: str
    token: str
    acquired: bool
    backend: str


class RedisJobLockService:
    def __init__(self) -> None:
        self._client: Redis | None = None

    def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(settings.redis_url, decode_responses=True)
        return self._client

    def acquire(self, key: str, ttl_seconds: int = 60 * 60) -> LockHandle:
        token = uuid.uuid4().hex
        try:
            acquired = bool(self._get_client().set(key, token, nx=True, ex=max(1, ttl_seconds)))
            return LockHandle(key=key, token=token, acquired=acquired, backend="redis")
        except RedisError:
            logger.warning("Redis indisponível para lock '%s'. Seguindo sem lock distribuído.", key, exc_info=True)
            return LockHandle(key=key, token=token, acquired=True, backend="fallback")

    def release(self, handle: LockHandle) -> None:
        if not handle.acquired or handle.backend != "redis":
            return
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        end
        return 0
        """
        try:
            self._get_client().eval(script, 1, handle.key, handle.token)
        except RedisError:
            logger.warning("Falha ao liberar lock '%s' no Redis.", handle.key, exc_info=True)


job_lock_service = RedisJobLockService()
