# src/routes/feedback.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    query_id: str
    rating: int
    comment: Optional[str] = None

@router.post("")
async def add_feedback(request: Request, feedback: FeedbackCreate):
    """Add new feedback"""
    try:
        redis = request.app.state.redis
        
        feedback_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query_id": feedback.query_id,
            "rating": feedback.rating,
            "comment": feedback.comment
        }
        
        await redis.store_feedback(feedback_data)
        return {"message": "Feedback added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def get_feedback(request: Request, limit: int = 100):
    """Get recent feedback"""
    try:
        redis = request.app.state.redis
        feedback_list = await redis.get_feedback(limit)
        return {"feedback": feedback_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))