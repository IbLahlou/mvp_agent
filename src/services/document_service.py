# src/services/document_service.py
from datetime import datetime
import json
from typing import List, Dict, Optional
from pydantic import BaseModel

class DocumentMetadata(BaseModel):
    doc_id: str  # Added doc_id field
    filename: str
    timestamp: str
    status: str
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None

class DocumentService:
    def __init__(self, redis_manager):
        self.redis_manager = redis_manager
        self.docs_key = "embedded_documents"
        
    async def log_document_start(self, filename: str) -> str:
        """Log the start of document processing"""
        doc_id = f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        metadata = DocumentMetadata(
            doc_id=doc_id,  # Include doc_id in metadata
            filename=filename,
            timestamp=datetime.utcnow().isoformat(),
            status="processing",
            chunk_count=0,
            embedding_model=None
        )
        
        await self.redis_manager._redis.hset(
            self.docs_key,
            doc_id,
            metadata.model_dump_json()
        )
        
        return doc_id
    
    async def update_document_status(
        self, 
        doc_id: str, 
        status: str,
        chunk_count: Optional[int] = None,
        embedding_model: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update document processing status"""
        current_data = await self.redis_manager._redis.hget(self.docs_key, doc_id)
        if current_data:
            metadata_dict = json.loads(current_data)
            metadata_dict["doc_id"] = doc_id  # Ensure doc_id is present
            metadata = DocumentMetadata(**metadata_dict)
            
            metadata.status = status
            if chunk_count is not None:
                metadata.chunk_count = chunk_count
            if embedding_model is not None:
                metadata.embedding_model = embedding_model
            if error_message is not None:
                metadata.error_message = error_message
                
            await self.redis_manager._redis.hset(
                self.docs_key,
                doc_id,
                metadata.model_dump_json()
            )
    
    async def get_document_status(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get status of a specific document"""
        data = await self.redis_manager._redis.hget(self.docs_key, doc_id)
        if data:
            metadata_dict = json.loads(data)
            metadata_dict["doc_id"] = doc_id  # Ensure doc_id is present
            return DocumentMetadata(**metadata_dict)
        return None
    
    async def get_all_documents(self) -> List[Dict]:
        """Get status of all documents"""
        all_docs = await self.redis_manager._redis.hgetall(self.docs_key)
        documents = []
        
        for doc_id, metadata in all_docs.items():
            metadata_dict = json.loads(metadata)
            metadata_dict["doc_id"] = doc_id  # Ensure doc_id is present
            documents.append(metadata_dict)
            
        return documents
    
    async def delete_document(self, doc_id: str):
        """Delete document metadata from Redis"""
        await self.redis_manager.ensure_connected()
        await self.redis_manager._redis.hdel(self.docs_key, doc_id)