from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
from typing import Optional
from src.cache.redis_manager import RedisManager
from src.config.settings import Settings
from src.agents.base_agent import BaseAgent

class Query(BaseModel):
    query: str

class AgentResponse(BaseModel):
    result: str
    source: str

# Initialize FastAPI app
app = FastAPI(title="LangChain Agent API")

# Initialize settings and managers
settings = Settings()
redis_manager = RedisManager()
base_agent: Optional[BaseAgent] = None

# Metrics
REQUESTS = Counter('http_requests_total', 'Total HTTP requests')
LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.on_event("startup")
async def startup_event():
    """Initialize connections and services on startup."""
    global base_agent
    try:
        await redis_manager.connect()
        base_agent = BaseAgent()
    except Exception as e:
        print(f"Failed to initialize services: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    await redis_manager.disconnect()

@app.get("/metrics")
async def metrics():
    """Endpoint for Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "LangChain Agent API is running"}

@app.post("/agent/execute", response_model=AgentResponse)
async def execute_agent(query: Query):
    """Execute the agent with the given query."""
    REQUESTS.inc()
    
    try:
        # Check Redis connection
        if not redis_manager.is_connected():
            await redis_manager.connect()

        # Try to get cached response
        cached_response = await redis_manager.get_cached_response(query.query)
        if cached_response:
            return AgentResponse(result=cached_response, source="cache")

        # Execute query using agent
        if not base_agent:
            raise HTTPException(
                status_code=503, 
                detail="Agent not initialized"
            )

        result = await base_agent.execute(query.query)
        
        # Cache the result if valid
        if result:
            await redis_manager.cache_response(query.query, result)
            return AgentResponse(result=result, source="agent")
        else:
            raise HTTPException(
                status_code=500,
                detail="Agent returned empty result"
            )

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Redis connection error: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )