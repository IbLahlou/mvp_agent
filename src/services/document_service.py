# src/services/document_service.py
from typing import List, BinaryIO
import hashlib
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.models.document import Document, DocumentChunk
from src.services.vector_store import VectorStore

class DocumentService:
    def __init__(self, db: Session, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def _compute_hash(self, file: BinaryIO) -> str:
        """Compute SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)
        file.seek(0)
        return sha256_hash.hexdigest()
    
    async def process_pdf(self, file: BinaryIO, filename: str) -> Document:
        """Process a PDF file and store its contents."""
        # Compute file hash
        content_hash = self._compute_hash(file)
        
        # Check if document already exists
        existing_doc = self.db.query(Document).filter_by(content_hash=content_hash).first()
        if existing_doc:
            return existing_doc
        
        # Create new document
        document = Document(
            filename=filename,
            content_hash=content_hash
        )
        self.db.add(document)
        
        # Process PDF content
        loader = PyPDFLoader(file)
        pages = loader.load()
        
        # Split into chunks
        chunks = []
        for page in pages:
            page_chunks = self.text_splitter.split_text(page.page_content)
            chunks.extend(page_chunks)
        
        # Add to vector store and create chunk records
        chunk_ids = self.vector_store.add_texts(chunks)
        
        for idx, (chunk_text, chunk_id) in enumerate(zip(chunks, chunk_ids)):
            chunk = DocumentChunk(
                document=document,
                content=chunk_text,
                chunk_index=idx,
                embedding_id=chunk_id
            )
            self.db.add(chunk)
        
        self.db.commit()
        return document
    
    async def search_documents(self, query: str, limit: int = 5) -> List[dict]:
        """Search for relevant document chunks."""
        # Get similar chunks from vector store
        similar_chunks = self.vector_store.similarity_search(query, k=limit)
        
        results = []
        for chunk_id, score in similar_chunks:
            # Get chunk from database
            chunk = self.db.query(DocumentChunk).filter_by(embedding_id=chunk_id).first()
            if chunk:
                results.append({
                    "document_id": chunk.document_id,
                    "filename": chunk.document.filename,
                    "content": chunk.content,
                    "score": score
                })
        
        return results
    
    def get_document(self, document_id: int) -> Document:
        """Get document by ID."""
        return self.db.query(Document).filter_by(id=document_id).first()