# src/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, CollectorRegistry
import logging
import sys
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent.parent)
sys.path.append(src_path)

from src.cache.redis_manager import RedisManager
from src.config.settings import Settings
from src.agents.base_agent import BaseAgent
from src.services.call_service import CallService
from src.services.feedback_service import FeedbackService

from src.routes.agent import get_agent_router
from src.routes.feedback import get_feedback_router
from src.routes.calls import get_calls_router
from src.routes.health import get_health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a custom registry for metrics
metrics_registry = CollectorRegistry()

# Initialize metrics with custom registry
REQUEST_COUNT = Counter(
    'langchain_api_requests_total', 
    'Total API requests',
    registry=metrics_registry
)
REQUEST_LATENCY = Histogram(
    'langchain_api_request_duration_seconds', 
    'API request latency',
    registry=metrics_registry
)

def create_app() -> FastAPI:
    # Initialize FastAPI app
    app = FastAPI(title="LangChain Agent API")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize services
    settings = Settings()
    redis_manager = RedisManager()
    base_agent = BaseAgent()
    call_service = CallService(redis_manager)
    feedback_service = FeedbackService(redis_manager)

    @app.on_event("startup")
    async def startup_event():
        """Initialize connections and services on startup"""
        try:
            # Connect to Redis
            logger.info("Connecting to Redis...")
            await redis_manager.connect()
            logger.info("Redis connection established")
            
            # Include routers
            app.include_router(get_health_router(metrics_registry))
            app.include_router(get_agent_router(redis_manager, base_agent, call_service))
            app.include_router(get_feedback_router(feedback_service))
            app.include_router(get_calls_router(call_service))
            
            logger.info("All routes initialized")
            
        except Exception as e:
            logger.error(f"Startup error: {str(e)}")
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up connections on shutdown"""
        logger.info("Shutting down...")
        await redis_manager.disconnect()
        logger.info("Cleanup completed")

    return app

def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the Uvicorn server"""
    try:
        logger.info(f"Starting server on {host}:{port}")
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        sys.exit(1)

# Create the FastAPI application instance
app = create_app()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LangChain Agent API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )