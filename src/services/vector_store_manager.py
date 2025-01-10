# src/services/vector_store_manager.py
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
import shutil
from datetime import datetime
import json
from typing import List, Dict, Optional, Tuple
import asyncio

class VectorStoreManager:
    def __init__(self, settings):
        self.settings = settings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-large"
        )
        self.vector_dir = "vector_store"
        self._ensure_directory()
        self.metadata_file = os.path.join(self.vector_dir, "metadata.json")
        self.load_metadata()

    def _ensure_directory(self):
        """Ensure vector store directory exists"""
        if not os.path.exists(self.vector_dir):
            os.makedirs(self.vector_dir)

    def load_metadata(self):
        """Load vector store metadata"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    "last_updated": None,
                    "documents": {},
                    "global_store": None
                }
        except Exception as e:
            print(f"Error loading metadata: {e}")
            self.metadata = {
                "last_updated": None,
                "documents": {},
                "global_store": None
            }

    def save_metadata(self):
        """Save vector store metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")

    async def update_document_store(
        self,
        doc_id: str,
        texts: List[str],
        metadata: Optional[Dict] = None
    ) -> str:
        """Update vector store for a specific document"""
        try:
            # Create store path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            store_path = os.path.join(self.vector_dir, f"doc_{doc_id}_{timestamp}")
            
            # Create metadatas list
            metadatas = []
            base_metadata = metadata or {}
            base_metadata["doc_id"] = doc_id
            base_metadata["timestamp"] = timestamp
            
            for _ in texts:
                metadatas.append(base_metadata.copy())
            
            # Create and save vector store
            vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            vector_store.save_local(store_path)
            
            # Update metadata
            self.metadata["documents"][doc_id] = {
                "timestamp": timestamp,
                "path": store_path,
                "metadata": base_metadata
            }
            self.metadata["last_updated"] = timestamp
            self.save_metadata()
            
            return store_path
        except Exception as e:
            print(f"Error updating document store: {e}")
            raise

    async def search_documents(
        self,
        query: str,
        filter_dict: Optional[Dict] = None,
        k: int = 4
    ) -> List[Tuple]:
        """Search across all valid vector stores"""
        try:
            results = []
            
            # Get valid stores
            valid_stores = []
            for doc_id, info in self.metadata["documents"].items():
                store_path = info["path"]
                if os.path.exists(store_path):
                    valid_stores.append(store_path)
            
            if not valid_stores:
                return []
            
            # Search each store
            for store_path in valid_stores:
                try:
                    vector_store = FAISS.load_local(
                        store_path,
                        self.embeddings
                    )
                    
                    search_kwargs = {}
                    if filter_dict:
                        search_kwargs["filter"] = filter_dict
                    
                    store_results = vector_store.similarity_search_with_score(
                        query=query,
                        k=k,
                        **search_kwargs
                    )
                    results.extend(store_results)
                except Exception as e:
                    print(f"Error searching store {store_path}: {e}")
                    continue
            
            # Sort by score and take top k
            results.sort(key=lambda x: x[1])
            return results[:k]
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    async def delete_document(self, doc_id: str):
        """Delete document from vector store"""
        try:
            if doc_id in self.metadata["documents"]:
                info = self.metadata["documents"][doc_id]
                store_path = info["path"]
                
                # Delete vector store files
                if os.path.exists(store_path):
                    shutil.rmtree(store_path)
                
                # Update metadata
                del self.metadata["documents"][doc_id]
                self.metadata["last_updated"] = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                self.save_metadata()
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            raise

    async def cleanup_old_stores(self, days: int = 7):
        """Clean up old vector stores"""
        try:
            cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
            
            for doc_id, info in list(self.metadata["documents"].items()):
                store_timestamp = datetime.strptime(
                    info["timestamp"], 
                    '%Y%m%d_%H%M%S'
                ).timestamp()
                
                if store_timestamp < cutoff:
                    await self.delete_document(doc_id)
            
        except Exception as e:
            print(f"Error during cleanup: {e}")

    async def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """Get information about a stored document"""
        return self.metadata["documents"].get(doc_id)