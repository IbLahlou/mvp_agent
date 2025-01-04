# src/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from src.config.settings import Settings
from src.agents.base_agent import BaseAgent
from src.cache.redis_manager import RedisManager
from src.services.document_service import DocumentService
from src.routes import agent, calls, documents, feedback, metrics
from src.routes.metrics import track_request, track_latency

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize settings and services
    settings = Settings()
    app.state.settings = settings
    
    # Create and store agent
    app.state.agent = BaseAgent()
    
    # Create and connect Redis
    redis = RedisManager()
    await redis.connect()
    app.state.redis = redis
    
    # Initialize DocumentService with Redis manager
    document_service = DocumentService(app.state.redis)
    app.state.document_service = document_service
    
    # Initialize routers with dependencies
    app.include_router(agent.router)  # Changed from get_agent_router
    app.include_router(calls.router)  # Assuming similar pattern for other routers
    app.include_router(
        documents.get_documents_router(
            document_service=app.state.document_service,
            settings=app.state.settings
        )
    )
    app.include_router(feedback.router)
    app.include_router(metrics.router)
    
    yield
    
    # Cleanup
    if hasattr(app.state, 'redis'):
        await app.state.redis.disconnect()

app = FastAPI(
    title="LangChain Agent API",
    description="API for document processing and LangChain agent interactions",
    version="1.0.0",
    lifespan=lifespan
)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    track_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    )
    
    track_latency(
        method=request.method,
        endpoint=request.url.path,
        duration=duration
    )
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )