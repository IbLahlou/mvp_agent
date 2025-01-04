# src/routes/documents.py
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
from src.services.document_service import DocumentService
from src.services.pdf_processor import PDFProcessor
from src.config.settings import Settings
import os

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    timestamp: str
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_123abc",
                "filename": "example.pdf",
                "status": "completed",
                "timestamp": "2024-01-04T12:00:00Z",
                "chunk_count": 42,
                "embedding_model": "text-embedding-ada-002",
                "error_message": None
            }
        }

class SearchQuery(BaseModel):
    query: str
    k: int = 4

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is machine learning?",
                "k": 4
            }
        }

class SearchResponse(BaseModel):
    doc_id: str
    query: str
    results: List[Dict[str, Any]]
    total_results: int

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123abc",
                "query": "What is machine learning?",
                "results": [
                    {
                        "content": "Machine learning is a subset of artificial intelligence...",
                        "page": 1,
                        "score": 0.89
                    }
                ],
                "total_results": 1
            }
        }

class UploadResponse(BaseModel):
    document_id: str
    status: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_123abc",
                "status": "processing",
                "message": "Document uploaded and processing started"
            }
        }

class DeleteResponse(BaseModel):
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Document doc_123abc and associated data deleted successfully"
            }
        }

async def process_document_background(
    pdf_processor: PDFProcessor,
    file_path: str,
    doc_id: str
):
    """Background task for processing PDF"""
    try:
        await pdf_processor.process_pdf(file_path, doc_id)
    except Exception as e:
        print(f"Error processing document {doc_id}: {str(e)}")

def get_documents_router(
    document_service: DocumentService,
    settings: Settings
) -> APIRouter:
    
    pdf_processor = PDFProcessor(document_service, settings)
    
    @router.post(
        "/upload",
        response_model=UploadResponse,
        status_code=202,
        responses={
            202: {"model": UploadResponse, "description": "Document accepted for processing"},
            400: {"description": "Invalid file format"},
            500: {"description": "Internal server error during processing"}
        }
    )
    async def upload_document(
        file: UploadFile = File(..., description="PDF file to upload and process"),
        background_tasks: BackgroundTasks = None
    ):
        """
        Upload a new PDF document for processing.
        
        The document will be:
        - Validated as a PDF file
        - Saved to temporary storage
        - Processed in the background
        - Split into chunks and embedded
        
        The processing status can be checked using the /status/{doc_id} endpoint.
        """
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        try:
            doc_id = await document_service.log_document_start(file.filename)
            file_content = await file.read()
            file_path = await pdf_processor.save_file(file_content, file.filename)
            
            background_tasks.add_task(
                process_document_background,
                pdf_processor,
                file_path,
                doc_id
            )
            
            return UploadResponse(
                document_id=doc_id,
                status="processing",
                message="Document uploaded and processing started"
            )
            
        except Exception as e:
            if 'doc_id' in locals():
                await document_service.update_document_status(
                    doc_id=doc_id,
                    status="error",
                    error_message=str(e)
                )
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )
    
    @router.get(
        "/status/{doc_id}",
        response_model=DocumentResponse,
        responses={
            404: {"description": "Document not found"},
            500: {"description": "Internal server error"}
        }
    )
    async def get_document_status(doc_id: str):
        """
        Get the current status and metadata of a specific document
        """
        try:
            status = await document_service.get_document_status(doc_id)
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            return {
                "id": doc_id,
                **status.model_dump()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting document status: {str(e)}"
            )
    
    @router.get(
        "/list",
        response_model=List[DocumentResponse],
        responses={
            500: {"description": "Internal server error"}
        }
    )
    async def list_documents():
        """
        Retrieve a list of all processed documents and their current status
        """
        try:
            documents = await document_service.get_all_documents()
            return documents
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error listing documents: {str(e)}"
            )

    @router.post(
        "/search/{doc_id}",
        response_model=SearchResponse,
        responses={
            404: {"description": "Document not found"},
            400: {"description": "Document not ready for search"},
            500: {"description": "Internal server error"}
        }
    )
    async def search_document(
        doc_id: str,
        search_query: SearchQuery
    ):
        """
        Search for specific content within a processed document
        """
        try:
            status = await document_service.get_document_status(doc_id)
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )
            
            if status.status != "completed":
                raise HTTPException(
                    status_code=400,
                    detail=f"Document is not ready for search. Current status: {status.status}"
                )

            results = await pdf_processor.search_document(
                doc_id=doc_id,
                query=search_query.query,
                k=search_query.k
            )
            
            return SearchResponse(
                doc_id=doc_id,
                query=search_query.query,
                results=results,
                total_results=len(results)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error searching document: {str(e)}"
            )

    @router.delete(
        "/{doc_id}",
        response_model=DeleteResponse,
        responses={
            404: {"description": "Document not found"},
            500: {"description": "Internal server error"}
        }
    )
    async def delete_document(doc_id: str):
        """
        Delete a document and all its associated data (vector store, uploaded file, metadata)
        """
        try:
            status = await document_service.get_document_status(doc_id)
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail="Document not found"
                )

            vector_store_path = os.path.join(pdf_processor.vector_dir, doc_id)
            if os.path.exists(vector_store_path):
                import shutil
                shutil.rmtree(vector_store_path)

            upload_path = os.path.join(pdf_processor.upload_dir, status.filename)
            if os.path.exists(upload_path):
                os.remove(upload_path)

            await document_service.delete_document(doc_id)

            return DeleteResponse(
                message=f"Document {doc_id} and associated data deleted successfully"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting document: {str(e)}"
            )
    
    return router