# src/services/call_service.py
from datetime import datetime
import json
from typing import List, Dict
from src.cache.redis_manager import RedisManager

class CallService:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.calls_key = "agent_calls"

    async def add_call(self, query: str, response: str):
        """Add a new call record"""
        call_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response
        }

        await self.redis_manager._redis.lpush(
            self.calls_key,
            json.dumps(call_data)
        )

    async def get_calls(self, limit: int = 100) -> List[Dict]:
        """Get recent calls"""
        calls = await self.redis_manager._redis.lrange(
            self.calls_key,
            0,
            limit - 1
        )
        return [json.loads(call) for call in calls]
