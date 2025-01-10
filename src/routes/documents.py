# src/routes/documents.py
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
from datetime import datetime
from src.services.document_service import DocumentService, DocumentMetadata
from src.services.pdf_processor import PDFProcessor

router = APIRouter(prefix="/doc", tags=["documents"])

class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    timestamp: str
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None

class DocumentList(BaseModel):
    documents: List[DocumentResponse]

class SearchQuery(BaseModel):
    query: str
    k: int = 4

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main features?",
                "k": 4
            }
        }

class SearchResponse(BaseModel):
    doc_id: str
    query: str
    results: List[Dict[str, Any]]
    total_results: int

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

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload and process a new document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    try:
        document_service = request.app.state.document_service
        pdf_processor = request.app.state.pdf_processor
        
        # Log document start
        doc_id = await document_service.log_document_start(file.filename)
        
        # Save file
        file_content = await file.read()
        file_path = await pdf_processor.save_file(file_content, file.filename)
        
        # Process in background
        background_tasks.add_task(
            process_document_background,
            pdf_processor,
            file_path,
            doc_id
        )
        
        return {
            "doc_id": doc_id,
            "status": "processing",
            "message": "Document uploaded and processing started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{doc_id}")
async def download_document(request: Request, doc_id: str):
    """Download a processed document"""
    try:
        document_service = request.app.state.document_service
        status = await document_service.get_document_status(doc_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
            
        file_path = os.path.join("uploads", status.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(
            file_path, 
            filename=status.filename,
            media_type='application/pdf'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=DocumentList)
async def list_documents(request: Request):
    """List all available documents"""
    try:
        document_service = request.app.state.document_service
        raw_documents = await document_service.get_all_documents()
        
        # Transform the documents to match the DocumentResponse model
        documents = []
        for doc in raw_documents:
            doc_response = DocumentResponse(
                doc_id=doc["doc_id"],
                filename=doc["filename"],
                status=doc["status"],
                timestamp=doc["timestamp"],
                chunk_count=doc.get("chunk_count"),
                embedding_model=doc.get("embedding_model"),
                error_message=doc.get("error_message")
            )
            documents.append(doc_response)
        
        return DocumentList(documents=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{doc_id}")
async def delete_document(request: Request, doc_id: str):
    """Delete a document and its associated data"""
    try:
        document_service = request.app.state.document_service
        pdf_processor = request.app.state.pdf_processor
        
        # Get document status
        status = await document_service.get_document_status(doc_id)
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete vector store
        vector_store_path = os.path.join(pdf_processor.vector_dir, doc_id)
        if os.path.exists(vector_store_path):
            import shutil
            shutil.rmtree(vector_store_path)
        
        # Delete uploaded file
        upload_path = os.path.join(pdf_processor.upload_dir, status.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        
        # Delete metadata
        await document_service.delete_document(doc_id)
        
        return {
            "message": f"Document {doc_id} and associated data deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getbyid/{doc_id}")
async def get_document_by_id(request: Request, doc_id: str):
    """Get document details by ID"""
    try:
        document_service = request.app.state.document_service
        status = await document_service.get_document_status(doc_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return DocumentResponse(
            doc_id=doc_id,
            filename=status.filename,
            status=status.status,
            timestamp=status.timestamp,
            chunk_count=status.chunk_count,
            embedding_model=status.embedding_model,
            error_message=status.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/{doc_id}", response_model=SearchResponse)
async def search_document(
    request: Request,
    doc_id: str,
    search_query: SearchQuery
):
    """Search within a processed document"""
    try:
        document_service = request.app.state.document_service
        pdf_processor = request.app.state.pdf_processor
        
        # Verify document exists and is ready
        status = await document_service.get_document_status(doc_id)
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if status.status != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Document is not ready for search. Current status: {status.status}"
            )

        # Perform search
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
        raise HTTPException(status_code=500, detail=str(e))