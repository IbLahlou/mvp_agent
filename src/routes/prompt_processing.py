# src/routes/prompt_processing.py
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
from src.services.prompt_processor import PromptProcessor  # Add this import

class ProcessingRequest(BaseModel):
    query: str
    doc_id: str
    max_results: Optional[int] = 4

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main features?",
                "doc_id": "doc_123abc",
                "max_results": 4
            }
        }

class ProcessingResponse(BaseModel):
    processed_response: str
    confidence: float
    original_results: List[dict]
    
    class Config:
        json_schema_extra = {
            "example": {
                "processed_response": "Based on the documentation, the main features include...",
                "confidence": 0.85,
                "original_results": []
            }
        }

def get_prompt_processing_router(settings) -> APIRouter:
    router = APIRouter(prefix="/process", tags=["prompt-processing"])
    processor = PromptProcessor(
        openai_api_key=settings.OPENAI_API_KEY,
        model_name=settings.MODEL_NAME,
        temperature=settings.TEMPERATURE
    )

    @router.post(
        "/search",
        response_model=ProcessingResponse,
        summary="Process Search Results",
        description="Search document and process results using prompt engineering"
    )
    async def process_search(request: Request, proc_request: ProcessingRequest):
        try:
            # Get document service from app state
            doc_service = request.app.state.document_service
            
            # Verify document exists and is ready
            doc_status = await doc_service.get_document_status(proc_request.doc_id)
            if not doc_status:
                raise HTTPException(status_code=404, detail="Document not found")
            if doc_status.status != "completed":
                raise HTTPException(
                    status_code=400,
                    detail=f"Document is not ready. Status: {doc_status.status}"
                )
            
            # Get PDF processor from app state and search document
            pdf_processor = request.app.state.pdf_processor
            search_results = await pdf_processor.search_document(
                doc_id=proc_request.doc_id,
                query=proc_request.query,
                k=proc_request.max_results
            )
            
            # Process results using prompt engineering
            processed = await processor.process_search_results(
                results=search_results,
                query=proc_request.query
            )
            
            return ProcessingResponse(
                processed_response=processed["processed_response"],
                confidence=processed["confidence"],
                original_results=processed["original_results"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing search: {str(e)}"
            )

    return router