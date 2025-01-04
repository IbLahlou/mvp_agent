# src/routes/health.py
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["health"])

def get_health_router() -> APIRouter:
    """
    Router for health check and metrics endpoints
    """
    @router.get("/")
    async def root():
        """Health check endpoint."""
        return {"status": "ok", "message": "LangChain Agent API is running"}

    @router.get("/metrics")
    async def metrics():
        """Endpoint for Prometheus metrics."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router