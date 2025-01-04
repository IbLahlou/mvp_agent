import json
from redis.asyncio import Redis
from typing import Optional
from src.config.settings import Settings

class RedisManager:
    def __init__(self):
        """Initialize Redis manager with settings."""
        self.settings = Settings()
        self._redis: Optional[Redis] = None

    async def connect(self):
        """Establish connection to Redis."""
        try:
            if not self._redis:
                self._redis = Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    password=self.settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                # Test the connection
                await self._redis.ping()
                print("Redis connection established")
        except Exception as e:
            self._redis = None
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        return self._redis is not None

    async def get_cached_response(self, query: str) -> Optional[str]:
        """Retrieve cached response for a query."""
        if not self._redis:
            raise ConnectionError("Redis not connected")

        key = f"agent_response:{query}"
        try:
            cached = await self._redis.get(key)
            return json.loads(cached) if cached else None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return None
        except Exception as e:
            print(f"Redis get error: {str(e)}")
            return None

    async def cache_response(self, query: str, response: str):
        """Cache a response with the specified TTL."""
        if not self._redis:
            raise ConnectionError("Redis not connected")

        key = f"agent_response:{query}"
        try:
            await self._redis.setex(
                key,
                self.settings.REDIS_CACHE_TTL,
                json.dumps(response)
            )
        except Exception as e:
            print(f"Redis set error: {str(e)}")
            raise