from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from src.services.vector_store_manager import VectorStoreManager
import json
from googletrans import Translator
import logging

router = APIRouter(tags=["agent"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

translator = Translator()

class BusinessType(str, Enum):
    B2C = "B2C"
    B2B = "B2B"
    STUDENT = "student"
    RESEARCH = "research"
    EMPLOYEE = "employee"
    BOSS = "boss"
    RND = "rnd"
    DEVELOPMENT = "dev"

class DomainType(str, Enum):
    TECH = "tech"
    HEALTH = "health"
    EDU = "edu"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

class Framework(str, Enum):
    AIDA = "AIDA"
    PAS = "PAS"
    FAB = "FAB"
    STAR = "STAR"
    BAB = "BAB"
    PASTOR = "PASTOR"
    QUEST = "QUEST"

class Language(str, Enum):
    EN = "eng"
    AR = "ar"
    FR = "fr"
    ES = "es"

class BaseRequest(BaseModel):
    company_name: str
    business_type: BusinessType
    framework: Optional[Framework] = Framework.STAR
    word_limit: Optional[int] = 150
    lang: Optional[Language] = Language.EN
    person_name: Optional[str] = "Valued Customer"  # Default name if not provided

class PresentationRequest(BaseRequest):
    topic: str
    domain_type: Optional[DomainType] = DomainType.TECH
    speaker: Optional[str] = "DialFlow Representative"  # Default speaker if not provided

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

async def get_relevant_context(agent, query: str, business_type: str, context_type: str, retrieve_history: bool = False) -> List[str]:
    try:
        if retrieve_history:
            logger.info(f"Retrieving conversation history for query: {query}")
            return agent.state.conversation_history.get(query, ["No prior context available."])
        
        enhanced_query = f"""
        Context: {context_type}
        Business Type: {business_type}
        Query: {query}
        """
        logger.info(f"Searching FAISS vector store with enhanced query: {enhanced_query}")
        
        vector_store = agent.state.vector_store_manager
        results = await vector_store.search_documents(
            query=enhanced_query,
            filter_dict={"context_type": context_type},
            k=4
        )
        
        if not results:
            logger.warning(f"No results found for query: {enhanced_query}. Falling back to default search.")
            results = await vector_store.search_documents(
                query="DialFlow core features and capabilities",
                k=2
            )
        
        context = [doc.page_content for doc, score in results if score < 1.0]
        
        if not context:
            logger.warning(f"No relevant context found for query: {enhanced_query}. Using default context.")
            context = [
                "DialFlow provides AI-powered solutions customized for your needs.",
                "Our platform offers seamless integration and scalable performance."
            ]
        
        logger.info(f"Retrieved context for query: {enhanced_query}")
        return context
    except Exception as e:
        logger.error(f"Error getting context for query: {enhanced_query}. Error: {e}")
        return []

def translate_text(text: str, target_lang: Language) -> str:
    try:
        lang_codes = {
            Language.EN: 'en',
            Language.AR: 'ar',
            Language.FR: 'fr',
            Language.ES: 'es'
        }
        translation = translator.translate(text, dest=lang_codes.get(target_lang, 'en'))
        return translation.text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def get_framework_structure(framework: Framework) -> str:
    return {
        Framework.AIDA: "1. Attention\n2. Interest\n3. Desire\n4. Action",
        Framework.PAS: "1. Problem\n2. Agitation\n3. Solution",
        Framework.FAB: "1. Features\n2. Advantages\n3. Benefits",
        Framework.STAR: "1. Situation\n2. Task\n3. Action\n4. Result",
        Framework.BAB: "1. Before\n2. After\n3. Bridge",
        Framework.PASTOR: "1. Problem\n2. Amplify\n3. Story\n4. Transform\n5. Offer\n6. Response",
        Framework.QUEST: "1. Qualify\n2. Understand\n3. Educate\n4. Stimulate\n5. Transition"
    }[framework]

def create_presentation_prompt(req: PresentationRequest, context: List[str]) -> str:
    # Prepare the presentation content using a general template
    presentation_template = f"""
    CALL SCRIPT: PRESENTATION ABOUT DIALFLOW

    Good day, everyone. This is {req.speaker}, and I’m here to introduce you to DialFlow, an innovative startup that specializes in providing intelligent consulting and AI-driven solutions. Our primary focus is to help businesses like yours achieve their goals by effectively leveraging advanced AI technology.

    Based on  ({req.business_type.value}) for ({req.domain_type.value}), here’s how DialFlow can benefit you:

    {". ".join(context)}

    Today, we’ll use the {req.framework.value} framework to guide our discussion. This framework helps us focus on key areas that are critical for your business success. We’ll start by understanding your current challenges, explore opportunities for improvement, and then discuss how DialFlow’s solutions can help you achieve your goals.

    Would you like to explore how DialFlow can help you further? We can also provide a detailed follow-up with visuals and metrics if needed.

    P.S. We retrieved your name, {req.person_name}, from the DialFlow platform to personalize this interaction.
    """

    return translate_text(presentation_template, req.lang)

def create_consulting_prompt(req: ConsultingRequest, context: List[str]) -> str:
    framework_text = get_framework_structure(req.framework)
    context_text = "\n".join(f"- {ctx}" for ctx in context)
    base_prompt = f"""
    CALL SCRIPT: CONSULTING CALL

    Hello {req.person_name}, this is DialFlow, your partner in intelligent consulting.
    Our mission is to empower businesses like yours with data-driven strategies and personalized insights.

    I understand that your primary concern is: {req.demand}. Let’s break this down using the {req.framework.value} framework:

    {framework_text}

    Based on ({req.business_type.value}) and the context we’ve gathered from the platform:
    {context_text}

    Here’s how DialFlow can help:
    1. **Identify the Root Cause**: We’ll analyze why you don’t have this service or what’s causing the issue.
    2. **Provide Tailored Solutions**: We’ll recommend solutions that align with your business goals.
    3. **Implement and Monitor**: We’ll help you implement the solution and monitor its effectiveness.

    Would you like to dive deeper into any of these steps or discuss how DialFlow can address your specific concern?
    """
    return translate_text(base_prompt, req.lang)

def create_support_prompt(req: TechnicalSupportRequest, context: List[str]) -> str:
    framework_text = get_framework_structure(req.framework)
    context_text = "\n".join(f"- {ctx}" for ctx in context)
    base_prompt = f"""
    CALL SCRIPT: TECHNICAL SUPPORT

    Hello {req.person_name}, this is DialFlow technical support.
    We’re here to assist you with your issue: {req.issue}. With your business type ({req.business_type.value}), we aim to deliver precise solutions that meet your needs.

    Here’s what we’ve found related to your concern:
    {context_text}

    Using the {req.framework.value} framework, we propose a detailed troubleshooting process and guidance for future prevention.
    Let’s address this together—do you have specific preferences or additional details to share before we proceed?

    P.S. We retrieved your name, {req.person_name}, from the DialFlow platform to personalize this interaction.
    """
    return translate_text(base_prompt, req.lang)


@router.post("/presentation")
async def get_presentation(request: Request, req: PresentationRequest):
    try:
        agent = request.app.state.agent
        retrieve_history = req.framework == Framework.QUEST
        context = await get_relevant_context(
            agent,
            req.topic,
            req.business_type.value,
            "presentation",
            retrieve_history
        )
        
        # Generate the presentation content using the `create_presentation_prompt` function
        presentation_text = create_presentation_prompt(req, context)

        # Translate the presentation text if needed
        translated_text = translate_text(presentation_text, req.lang)

        # Prepare the response
        return AgentResponse(
            response=translated_text,
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in /presentation endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consulting")
async def get_consulting(request: Request, req: ConsultingRequest):
    try:
        agent = request.app.state.agent
        retrieve_history = req.framework == Framework.QUEST
        context = await get_relevant_context(
            agent,
            req.demand,
            req.business_type.value,
            "consulting",
            retrieve_history
        )
        
        messages = [
            SystemMessage(content=f"You are a DialFlow a consulting voice agent speaking in {req.lang.value}."),
            HumanMessage(content=create_consulting_prompt(req, context))
        ]
        
        response = await agent.llm.ainvoke(messages)
        
        return AgentResponse(
            response=translate_text(response.content, req.lang),
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in /consulting endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/technical_support")
async def get_technical_support(request: Request, req: TechnicalSupportRequest):
    try:
        agent = request.app.state.agent
        retrieve_history = req.framework == Framework.QUEST
        context = await get_relevant_context(
            agent,
            req.issue,
            req.business_type.value,
            "technical",
            retrieve_history
        )
        
        messages = [
            SystemMessage(content=f"You are a DialFlow technical a consulting voice agent speaking in {req.lang.value}."),
            HumanMessage(content=create_support_prompt(req, context))
        ]
        
        response = await agent.llm.ainvoke(messages)
        
        return AgentResponse(
            response=translate_text(response.content, req.lang),
            context_used=context,
            framework_used=req.framework,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Error in /technical_support endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/business-types")
async def get_business_types():
    return list(BusinessType)

@router.get("/domain-types")
async def get_domain_types():
    return list(DomainType)

@router.get("/frameworks")
async def get_frameworks():
    return {framework.name: framework.value for framework in Framework}