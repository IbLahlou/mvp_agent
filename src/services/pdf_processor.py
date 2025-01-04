# src/services/pdf_processor.py
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from typing import List, Dict
import os
import asyncio
from src.config.settings import Settings
from src.services.document_service import DocumentService

class PDFProcessor:
    def __init__(self, document_service: DocumentService, settings: Settings):
        self.document_service = document_service
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-large"
        )
        self.upload_dir = "uploads"
        self.vector_dir = "vector_store"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        for directory in [self.upload_dir, self.vector_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    async def save_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to disk"""
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        return file_path

    async def store_embeddings(self, doc_id: str, chunks: List, embeddings: List[List[float]]):
        """Store document chunks and embeddings in FAISS"""
        # Create vector store directory for this document
        doc_vector_path = os.path.join(self.vector_dir, doc_id)
        
        # Create and save FAISS index
        vector_store = FAISS.from_texts(
            texts=[chunk.page_content for chunk in chunks],
            embedding=self.embeddings,
            metadatas=[{
                'source': chunk.metadata.get('source', ''),
                'page': chunk.metadata.get('page', 0),
                'doc_id': doc_id
            } for chunk in chunks]
        )
        
        # Save the vector store
        vector_store.save_local(doc_vector_path)
        
        return doc_vector_path

    async def process_pdf(self, file_path: str, doc_id: str):
        """Process PDF file and create embeddings"""
        try:
            # Load PDF
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            # Split into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(pages)

            # Update status with chunk count
            await self.document_service.update_document_status(
                doc_id=doc_id,
                status="chunking_complete",
                chunk_count=len(chunks)
            )

            # Create embeddings
            await self.document_service.update_document_status(
                doc_id=doc_id,
                status="embedding",
                embedding_model=self.embeddings.model
            )

            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                self.embeddings.embed_documents,
                [chunk.page_content for chunk in chunks]
            )

            # Store embeddings in FAISS
            vector_store_path = await self.store_embeddings(doc_id, chunks, embeddings)

            # Update final status
            await self.document_service.update_document_status(
                doc_id=doc_id,
                status="completed",
                chunk_count=len(chunks),
                embedding_model=self.embeddings.model
            )

            return {
                "doc_id": doc_id,
                "chunks": len(chunks),
                "embeddings": len(embeddings),
                "vector_store_path": vector_store_path
            }

        except Exception as e:
            await self.document_service.update_document_status(
                doc_id=doc_id,
                status="error",
                error_message=str(e)
            )
            raise

    async def search_document(self, doc_id: str, query: str, k: int = 4) -> List[Dict]:
        """Search within a specific document's vector store"""
        try:
            doc_vector_path = os.path.join(self.vector_dir, doc_id)
            if not os.path.exists(doc_vector_path):
                raise ValueError(f"No vector store found for document {doc_id}")

            # Load the vector store
            vector_store = FAISS.load_local(
                doc_vector_path,
                self.embeddings
            )

            # Search
            results = vector_store.similarity_search_with_score(
                query=query,
                k=k
            )

            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })

            return formatted_results

        except Exception as e:
            raise ValueError(f"Error searching document: {str(e)}")