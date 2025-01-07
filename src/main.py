# src/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from src.config.settings import Settings
from src.agents.base_agent import BaseAgent
from src.cache.redis_manager import RedisManager
from src.services.document_service import DocumentService
from src.services.pdf_processor import PDFProcessor
from src.services.prompt_processor import PromptProcessor  # Add this import
from src.routes import agent, calls, documents, feedback, metrics
from src.routes.agent_chat import get_agent_chat_router
from src.routes.prompt_processing import get_prompt_processing_router  # Add this import
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
    
    # Initialize PDF Processor
    pdf_processor = PDFProcessor(document_service, settings)
    app.state.pdf_processor = pdf_processor
    
    # Initialize Prompt Processor
    prompt_processor = PromptProcessor(
        openai_api_key=settings.OPENAI_API_KEY,
        model_name=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE
    )
    app.state.prompt_processor = prompt_processor
    
    # Initialize routers with dependencies
    app.include_router(agent.router)
    app.include_router(calls.router)
    app.include_router(
        documents.get_documents_router(
            document_service=app.state.document_service,
            settings=app.state.settings
        )
    )
    app.include_router(feedback.router)
    app.include_router(metrics.router)
    app.include_router(get_agent_chat_router())
    
    # Add the new prompt processing router
    app.include_router(
        get_prompt_processing_router(settings=app.state.settings)
    )
    
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