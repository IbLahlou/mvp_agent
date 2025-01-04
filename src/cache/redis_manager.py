# src/cache/redis_manager.py
from redis.asyncio import Redis
from typing import Optional, List, Dict
import json
from datetime import datetime

class RedisManager:
    def __init__(self):
        self._redis: Optional[Redis] = None
        
    async def connect(self, host: str = "localhost", port: int = 6379, password: Optional[str] = None):
        """Connect to Redis"""
        if not self._redis:
            self._redis = Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True
            )
            await self._redis.ping()
            print("Redis connection established")
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def get_cached_response(self, query: str) -> Optional[str]:
        """Get cached response for a query"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        key = f"response:{query}"
        try:
            cached = await self._redis.get(key)
            return json.loads(cached) if cached else None
        except Exception as e:
            print(f"Redis get error: {str(e)}")
            return None
    
    async def cache_response(self, query: str, response: str, ttl: int = 3600):
        """Cache a response with TTL"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        key = f"response:{query}"
        try:
            await self._redis.setex(
                key,
                ttl,
                json.dumps(response)
            )
        except Exception as e:
            print(f"Redis set error: {str(e)}")
    
    async def store_call(self, query: str, response: str):
        """Store a call record"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        call_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response
        }
        
        try:
            await self._redis.lpush("calls", json.dumps(call_data))
        except Exception as e:
            print(f"Redis call storage error: {str(e)}")
    
    async def get_calls(self, limit: int = 100) -> List[Dict]:
        """Get recent calls"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        try:
            calls = await self._redis.lrange("calls", 0, limit - 1)
            return [json.loads(call) for call in calls]
        except Exception as e:
            print(f"Redis get calls error: {str(e)}")
            return []

    async def store_feedback(self, feedback_data: Dict):
        """Store feedback"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        try:
            await self._redis.lpush("feedback", json.dumps(feedback_data))
        except Exception as e:
            print(f"Redis feedback storage error: {str(e)}")
            raise

    async def get_feedback(self, limit: int = 100) -> List[Dict]:
        """Get stored feedback"""
        if not self._redis:
            raise ConnectionError("Redis not connected")
        
        try:
            feedback = await self._redis.lrange("feedback", 0, limit - 1)
            return [json.loads(f) for f in feedback]
        except Exception as e:
            print(f"Redis get feedback error: {str(e)}")
            return []