# src/services/feedback_service.py
from datetime import datetime
import json
from typing import List, Dict
from pydantic import BaseModel
from src.cache.redis_manager import RedisManager

class FeedbackCreate(BaseModel):
    query_id: str
    rating: int
    comment: str | None = None

class FeedbackService:
    def __init__(self, redis_manager: RedisManager):
        self.redis_manager = redis_manager
        self.feedback_key = "agent_feedback"

    async def add_feedback(self, feedback: FeedbackCreate):
        """Add new feedback"""
        feedback_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_id": feedback.query_id,
            "rating": feedback.rating,
            "comment": feedback.comment
        }

        await self.redis_manager._redis.lpush(
            self.feedback_key,
            json.dumps(feedback_data)
        )

    async def get_feedback(self, limit: int = 100) -> List[Dict]:
        """Get recent feedback"""
        feedback = await self.redis_manager._redis.lrange(
            self.feedback_key,
            0,
            limit - 1
        )
        return [json.loads(f) for f in feedback]