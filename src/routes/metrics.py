# src/routes/metrics.py
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

router = APIRouter(tags=["metrics"])

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

def track_request(method: str, endpoint: str, status_code: int):
    """Track request metrics"""
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code)
    ).inc()

def track_latency(method: str, endpoint: str, duration: float):
    """Track request latency"""
    REQUEST_LATENCY.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

@router.get("/metrics")
async def metrics():
    """Get Prometheus metrics"""
    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )