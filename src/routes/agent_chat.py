# src/routes/agent_chat.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from langchain.schema import HumanMessage, SystemMessage

class ChatRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "What information do you have about system setup?"
            }
        }

class ChatResponse(BaseModel):
    response: str
    context_used: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the available documentation...",
                "context_used": ["Found in setup guide...", "From configuration section..."]
            }
        }

def get_agent_chat_router() -> APIRouter:
    router = APIRouter(prefix="/agent", tags=["agent-chat"])

    @router.post(
        "/chat",
        response_model=ChatResponse,
        summary="Chat with Knowledge Agent",
        description="Get responses based on all stored document knowledge"
    )
    async def chat_with_agent(request: Request, chat_request: ChatRequest):
        try:
            # Get the agent and LLM from app state
            agent = request.app.state.agent
            
            # Search across all documents
            search_results = agent._search_documents(chat_request.text)
            
            # Create messages for the LLM
            messages = [
                SystemMessage(content="""You are Sarah, a skilled professional support specialist. 
                    Respond to queries based on the provided context with expertise and natural warmth.
                    If the context doesn't contain relevant information, say so professionally."""),
                HumanMessage(content=f"""Context from documentation:
                    {search_results}
                    
                    User query: {chat_request.text}
                    
                    Please provide a helpful response based on this context.""")
            ]
            
            # Get response from LLM
            response = await agent.llm.ainvoke(messages)
            
            return ChatResponse(
                response=response.content,
                context_used=search_results.split("\n\n") if search_results else None
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing request: {str(e)}"
            )

    return router