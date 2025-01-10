# src/routes/agent.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from src.services.vector_store_manager import VectorStoreManager
import json

router = APIRouter(tags=["agent"])

# ============ Enums & Models ============

class BusinessType(str, Enum):
    B2C = "B2C"
    B2B = "B2B"
    RESEARCH = "Research"
    RND = "R&D"

class Framework(str, Enum):
    AIDA = "Attention, Interest, Desire, Action"
    PAS = "Problem, Agitation, Solution"
    FAB = "Features, Advantages, Benefits"
    STAR = "Situation, Task, Action, Result"
    BAB = "Before, After, Bridge"
    PASTOR = "Problem, Amplify, Story, Transform, Offer, Response"
    QUEST = "Qualify, Understand, Educate, Stimulate, Transition"

class BaseRequest(BaseModel):
    company_name: str
    business_type: BusinessType
    framework: Optional[Framework] = Framework.STAR
    word_limit: Optional[int] = 150

class PresentationRequest(BaseRequest):
    topic: str

class ConsultingRequest(BaseRequest):
    demand: str

class TechnicalSupportRequest(BaseRequest):
    issue: str
    priority: Optional[str] = "normal"

class AgentResponse(BaseModel):
    response: str
    context_used: List[str]
    framework_used: Framework
    timestamp: str

# ============ Helper Functions ============

async def get_relevant_context(agent, query: str, business_type: str, context_type: str) -> List[str]:
    """Get relevant context from FAISS"""
    try:
        # Build enhanced query
        enhanced_query = f"""
        Context: {context_type}
        Business Type: {business_type}
        Query: {query}
        """
        
        # Use vector store manager for search
        vector_store = agent.state.vector_store_manager
        results = await vector_store.search_documents(
            query=enhanced_query,
            filter_dict={"context_type": context_type},
            k=4
        )
        
        if not results:
            # Fall back to general DialFlow content
            results = await vector_store.search_documents(
                query="DialFlow core features and capabilities",
                k=2
            )
        
        # Format results
        context = []
        for doc, score in results:
            if score < 1.0:  # Filter out low relevance results
                context.append(doc.page_content)
        
        return context if context else [
            "DialFlow provides AI-powered solutions customized for your needs.",
            "Our platform offers seamless integration and scalable performance."
        ]
    except Exception as e:
        print(f"Error getting context: {e}")
        return []

def get_framework_structure(framework: Framework) -> str:
    """Get framework structure for prompts"""
    return {
        Framework.AIDA: "1. Attention\n2. Interest\n3. Desire\n4. Action",
        Framework.PAS: "1. Problem\n2. Agitation\n3. Solution",
        Framework.FAB: "1. Features\n2. Advantages\n3. Benefits",
        Framework.STAR: "1. Situation\n2. Task\n3. Action\n4. Result",
        Framework.BAB: "1. Before\n2. After\n3. Bridge",
        Framework.PASTOR: "1. Problem\n2. Amplify\n3. Story\n4. Transform\n5. Offer\n6. Response",
        Framework.QUEST: "1. Qualify\n2. Understand\n3. Educate\n4. Stimulate\n5. Transition"
    }[framework]

# ============ Prompt Functions ============

def create_presentation_prompt(req: PresentationRequest, context: List[str]) -> str:
    framework_text = get_framework_structure(req.framework)
    context_text = "\n".join(f"- {ctx}" for ctx in context)
    
    return f"""CALL SCRIPT: PRESENTATION

Hello, this is DialFlow, a startup specializing in intelligent consulting and AI-powered solutions. 
We focus on helping businesses like yours achieve their goals by leveraging advanced AI technologies. 

Today, we’d like to discuss the topic: {req.topic}. Our services are tailored to your business type ({req.business_type.value}), ensuring customized, impactful solutions.

Here’s what we’ve gathered about your company:
{context_text}

Using the {req.framework.value} framework, we propose actionable insights to address your needs. 
Would you like to explore how we can help further? We can also provide a detailed follow-up with visuals and metrics if needed.
"""

def create_consulting_prompt(req: ConsultingRequest, context: List[str]) -> str:
    framework_text = get_framework_structure(req.framework)
    context_text = "\n".join(f"- {ctx}" for ctx in context)
    
    return f"""CALL SCRIPT: CONSULTING

Hello, this is DialFlow, your partner in intelligent consulting. 
Our mission is to empower businesses like yours with data-driven strategies and personalized insights. 

We understand that your primary need is: {req.demand}. Based on our expertise and your business type ({req.business_type.value}), here’s what we’ve discovered:
{context_text}

By leveraging the {req.framework.value} framework, we can present a roadmap that emphasizes ROI, efficient implementation, and measurable outcomes. 
Would you be interested in a more detailed session to discuss these opportunities?
"""

def create_support_prompt(req: TechnicalSupportRequest, context: List[str]) -> str:
    framework_text = get_framework_structure(req.framework)
    context_text = "\n".join(f"- {ctx}" for ctx in context)
    
    return f"""CALL SCRIPT: TECHNICAL SUPPORT

Hello, this is DialFlow technical support. 
We’re here to assist you with your issue: {req.issue}. With your business type ({req.business_type.value}), we aim to deliver precise solutions that meet your needs. 

Here’s what we’ve found related to your concern:
{context_text}

Using the {req.framework.value} framework, we propose a detailed troubleshooting process and guidance for future prevention. 
Let’s address this together—do you have specific preferences or additional details to share before we proceed?
"""

# ============ Endpoints ============

@router.post("/presentation")
async def get_presentation(request: Request, req: PresentationRequest):
    """Generate DialFlow presentation"""
    try:
        agent = request.app.state.agent
        context = await get_relevant_context(
            agent, 
            req.topic, 
            req.business_type.value, 
            "presentation"
        )
        
        messages = [
            SystemMessage(content="You are a DialFlow presentation expert."),
            HumanMessage(content=create_presentation_prompt(req, context))
        ]
        
        response = await agent.llm.ainvoke(messages)
        
        return AgentResponse(
            response=response.content,
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consulting")
async def get_consulting(request: Request, req: ConsultingRequest):
    """Handle DialFlow consulting requests"""
    try:
        agent = request.app.state.agent
        context = await get_relevant_context(
            agent, 
            req.demand, 
            req.business_type.value, 
            "consulting"
        )
        
        messages = [
            SystemMessage(content="You are a DialFlow consulting expert."),
            HumanMessage(content=create_consulting_prompt(req, context))
        ]
        
        response = await agent.llm.ainvoke(messages)
        
        return AgentResponse(
            response=response.content,
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/technical_support")
async def get_technical_support(request: Request, req: TechnicalSupportRequest):
    """Handle DialFlow technical support"""
    try:
        agent = request.app.state.agent
        context = await get_relevant_context(
            agent, 
            req.issue, 
            req.business_type.value, 
            "technical"
        )
        
        messages = [
            SystemMessage(content="You are a DialFlow technical expert."),
            HumanMessage(content=create_support_prompt(req, context))
        ]
        
        response = await agent.llm.ainvoke(messages)
        
        return AgentResponse(
            response=response.content,
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/business-types")
async def get_business_types():
    """Get available business types"""
    return list(BusinessType)

@router.get("/frameworks")
async def get_frameworks():
    """Get available frameworks with descriptions"""
    return {framework.name: framework.value for framework in Framework}
