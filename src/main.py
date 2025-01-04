# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config.settings import Settings
from src.agents.base_agent import BaseAgent
from src.routes import agent, calls, documents, feedback

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Initialize Agent
        base_agent = BaseAgent()
        print("Services initialized")
        yield
    finally:
        # Cleanup
        print("Shutting down")

app = FastAPI(
    title="LangChain Agent API",
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

# Include routers
app.include_router(agent.router)
app.include_router(calls.router)
app.include_router(documents.router)
app.include_router(feedback.router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )