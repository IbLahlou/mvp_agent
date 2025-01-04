# src/routes/agent.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from src.agents.base_agent import BaseAgent

router = APIRouter(
    prefix="/agent",
    tags=["agent"]
)

class Query(BaseModel):
    query: str
    context: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the main topic of the document?",
                "context": "Optional additional context"
            }
        }

class AgentResponse(BaseModel):
    response: str
    query_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "response": "The main topic is artificial intelligence.",
                "query_id": "query_123abc"
            }
        }

def get_agent_router(agent: BaseAgent) -> APIRouter:
    """
    Create and return an APIRouter for agent endpoints
    Args:
        agent: The BaseAgent instance to use for processing queries
    """
    
    @router.post(
        "/execute",
        response_model=AgentResponse,
        summary="Execute Agent Query",
        description="Execute a query using the LangChain agent"
    )
    async def execute_agent(
        query: Query,
        background_tasks: BackgroundTasks
    ):
        """Execute a query using the agent"""
        try:
            result = await agent.execute(query.query)
            query_id = f"agent_{hash(query.query)}"
            
            return AgentResponse(
                response=result,
                query_id=query_id
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error executing agent query: {str(e)}"
            )
    
    return router