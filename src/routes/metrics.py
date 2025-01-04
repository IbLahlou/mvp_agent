# src/routes/metrics.py
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import (
    generate_latest, 
    CONTENT_TYPE_LATEST,
    Counter, 
    Histogram,
    REGISTRY
)

# Create metrics
REQUESTS = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Create router
router = APIRouter(tags=["metrics"])

@router.get(
    "/metrics",
    response_class=Response,
    summary="Get Prometheus Metrics",
    description="Returns all collected metrics in Prometheus text format"
)
async def metrics():
    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

# Helper functions to update metrics
def track_request(method: str, endpoint: str, status_code: int):
    """Track HTTP request metrics"""
    REQUESTS.labels(
        method=method,
        endpoint=endpoint,
        status=status_code
    ).inc()

def track_latency(method: str, endpoint: str, duration: float):
    """Track request latency"""
    LATENCY.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)