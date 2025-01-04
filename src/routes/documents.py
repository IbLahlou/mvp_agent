# src/routes/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import tempfile
import os

from src.services.document_service import DocumentService
from src.database import get_db
from src.services.vector_store import VectorStore

router = APIRouter(prefix="/documents", tags=["documents"])

def get_documents_router(document_service: DocumentService) -> APIRouter:
    
    @router.post("/upload")
    async def upload_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Upload and process a PDF document."""
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file.seek(0)
                
                # Process document
                document = await document_service.process_pdf(
                    tmp_file,
                    file.filename
                )
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return {
                "message": "Document processed successfully",
                "document_id": document.id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/search")
    async def search_documents(
        query: str,
        limit: int = 5,
        db: Session = Depends(get_db)
    ):
        """Search through documents."""
        try:
            results = await document_service.search_documents(query, limit)
            return {"results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/{document_id}")
    async def get_document(
        document_id: int,
        db: Session = Depends(get_db)
    ):
        """Get document details by ID."""
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "id": document.id,
            "filename": document.filename,
            "created_at": document.created_at
        }
    
    return router