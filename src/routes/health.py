# src/routes/health.py
from fastapi import APIRouter
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter(tags=["health"])

def get_health_router(registry: CollectorRegistry) -> APIRouter:
    @router.get("/health")
    async def health_check():
        return {"status": "ok"}
    
    @router.get("/metrics")
    async def metrics():
        return Response(
            generate_latest(registry),
            media_type=CONTENT_TYPE_LATEST
        )
    
    return router