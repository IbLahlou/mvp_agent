# src/core/cache.py
from redis.asyncio import Redis
from typing import Optional
import json

class Cache:
    """Simple Redis cache implementation"""
    
    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.redis = Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            
    async def add_to_list(self, list_key: str, value: dict):
        """Add value to a Redis list"""
        try:
            await self.redis.lpush(list_key, json.dumps(value))
        except Exception as e:
            print(f"Cache list add error: {str(e)}")
    
    async def get_list(self, list_key: str, start: int = 0, end: int = -1) -> List[dict]:
        """Get values from a Redis list"""
        try:
            items = await self.redis.lrange(list_key, start, end)
            return [json.loads(item) for item in items]
        except Exception as e:
            print(f"Cache list get error: {str(e)}")
            return []