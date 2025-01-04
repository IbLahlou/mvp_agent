# src/routes/documents.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import os

from src.agents.base_agent import BaseAgent

router = APIRouter(prefix="/documents", tags=["documents"])

def get_documents_router(agent: BaseAgent) -> APIRouter:
    
    @router.post("/upload")
    async def upload_document(
        file: UploadFile = File(...)
    ):
        """Upload and process a PDF document."""
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                
                # Process PDF
                loader = PyPDFLoader(tmp_file.name)
                pages = loader.load()
                
                # Split text
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                
                texts = []
                metadatas = []
                for page in pages:
                    page_texts = text_splitter.split_text(page.page_content)
                    texts.extend(page_texts)
                    metadatas.extend([{"source": file.filename, "page": page.metadata.get("page", 0)}] * len(page_texts))
                
                # Add to vector store
                await agent.add_documents(texts, metadatas)
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return {
                "message": "Document processed successfully",
                "chunks": len(texts)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router