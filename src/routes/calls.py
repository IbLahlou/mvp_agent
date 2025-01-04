# src/routes/calls.py
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/calls", tags=["calls"])

@router.get("")
async def get_calls(request: Request, limit: int = 100):
    try:
        redis = request.app.state.redis
        calls = await redis.get_calls(limit)
        return {"calls": calls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))