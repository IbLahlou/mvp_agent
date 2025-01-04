# src/routes/feedback.py
from fastapi import APIRouter, HTTPException
from src.services.feedback_service import FeedbackService, FeedbackCreate

router = APIRouter(prefix="/feedback", tags=["feedback"])

def get_feedback_router(feedback_service: FeedbackService) -> APIRouter:
    @router.post("")
    async def add_feedback(feedback: FeedbackCreate):
        try:
            await feedback_service.add_feedback(feedback)
            return {"message": "Feedback added successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    @router.get("")
    async def get_feedback(limit: int = 100):
        try:
            feedback = await feedback_service.get_feedback(limit)
            return {"feedback": feedback}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router