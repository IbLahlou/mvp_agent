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
from src.services.request_logger import RequestLogger
from src.services.vector_store_manager import VectorStoreManager
from src.config.settings import Settings

from src.routes import agent, documents, metrics , feedback
from src.middleware.logging_middleware import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Setup and cleanup of application resources"""
    try:
        # Initialize settings
        settings = Settings()
        app.state.settings = settings
        
        # Initialize Redis
        redis = RedisManager()
        await redis.connect(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD
        )
        app.state.redis = redis
        
        # Initialize Vector Store Manager
        vector_store_manager = VectorStoreManager(settings)
        app.state.vector_store_manager = vector_store_manager
        
        # Initialize services
        document_service = DocumentService(redis)
        app.state.document_service = document_service
        
        # Initialize PDF Processor
        pdf_processor = PDFProcessor(document_service, settings)
        app.state.pdf_processor = pdf_processor
        
        # Initialize AI Agent
        app.state.agent = BaseAgent()
        
        # Initialize Request Logger
        app.state.request_logger = RequestLogger()
        
        # Update vector store with initial content if needed
        initial_content = [
            "DialFlow provides advanced AI solutions for businesses.",
            "Our platform offers seamless integration capabilities.",
            "DialFlow supports multiple business use cases and industries."
        ]
        await vector_store_manager.update_document_store(
            doc_id="core_info",
            texts=initial_content,
            metadata={"type": "general"}
        )
        
        print("✅ All services initialized successfully")
        
        yield
        
        # Cleanup
        if hasattr(app.state, 'redis'):
            await app.state.redis.disconnect()
        
        print("🧹 Cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        raise

app = FastAPI(
    title="DialFlow Assistant API",
    description="API for document processing and DialFlow agent interactions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Track request metrics"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Track metrics
    metrics.track_request(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    )
    metrics.track_latency(
        method=request.method,
        endpoint=request.url.path,
        duration=duration
    )
    
    return response

# Register routes
app.include_router(documents.router,  tags=["documents"])
app.include_router(agent.router, prefix="/agent", tags=["agent"])
app.include_router(metrics.router) 
app.include_router(feedback.router) 

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "DialFlow Assistant API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check(request: Request):
    """Detailed health check endpoint"""
    try:
        health_status = {
            "status": "ok",
            "timestamp": time.time(),
            "components": {}
        }
        
        # Check Redis
        try:
            if request.app.state.redis.is_connected():
                health_status["components"]["redis"] = "ok"
            else:
                health_status["components"]["redis"] = "error"
        except:
            health_status["components"]["redis"] = "error"
        
        # Check Vector Store
        try:
            vector_info = await request.app.state.vector_store_manager.get_document_info("core_info")
            if vector_info:
                health_status["components"]["vector_store"] = "ok"
            else:
                health_status["components"]["vector_store"] = "warning"
        except:
            health_status["components"]["vector_store"] = "error"
        
        # Check other components
        health_status["components"].update({
            "agent": "ok" if hasattr(request.app.state, 'agent') else "error",
            "document_service": "ok" if hasattr(request.app.state, 'document_service') else "error",
            "pdf_processor": "ok" if hasattr(request.app.state, 'pdf_processor') else "error"
        })
        
        # Overall status
        if any(v == "error" for v in health_status["components"].values()):
            health_status["status"] = "error"
        elif any(v == "warning" for v in health_status["components"].values()):
            health_status["status"] = "warning"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )