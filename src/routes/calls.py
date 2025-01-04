# src/routes/calls.py
from fastapi import APIRouter, HTTPException
from src.services.call_service import CallService

router = APIRouter(prefix="/calls", tags=["calls"])

def get_calls_router(call_service: CallService) -> APIRouter:
    @router.get("")
    async def get_calls(limit: int = 100):
        try:
            calls = await call_service.get_calls(limit)
            return {"calls": calls}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router