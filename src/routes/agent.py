# src/routes/agent.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from src.cache.redis_manager import RedisManager
from src.agents.base_agent import BaseAgent
from src.services.call_service import CallService

router = APIRouter(prefix="/agent", tags=["agent"])

class Query(BaseModel):
    query: str

class AgentResponse(BaseModel):
    result: str
    source: str
    query_id: str

def get_agent_router(
    redis_manager: RedisManager,
    base_agent: BaseAgent,
    call_service: CallService
) -> APIRouter:
    
    @router.post("/execute")
    async def execute_agent(query: Query, background_tasks: BackgroundTasks):
        try:
            # Check cache first
            cached_response = await redis_manager.get_cached_response(query.query)
            if cached_response:
                query_id = f"cached_{str(hash(query.query))}"
                background_tasks.add_task(
                    call_service.add_call,
                    query.query,
                    cached_response
                )
                return AgentResponse(
                    result=cached_response,
                    source="cache",
                    query_id=query_id
                )

            # Execute with agent if not cached
            result = await base_agent.execute(query.query)
            if result:
                query_id = f"agent_{str(hash(query.query))}"
                await redis_manager.cache_response(query.query, result)
                background_tasks.add_task(
                    call_service.add_call,
                    query.query,
                    result
                )
                return AgentResponse(
                    result=result,
                    source="agent",
                    query_id=query_id
                )
            raise HTTPException(status_code=500, detail="Empty result from agent")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
