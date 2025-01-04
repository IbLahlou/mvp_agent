# src/services/vector_store.py
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional
import os

class VectorStoreService:
    def __init__(self, api_key: str):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        self.store_path = "data/vector_store"
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self._initialize_store()

    def _initialize_store(self):
        """Initialize or load existing vector store"""
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.store_path):
            self.db = FAISS.load_local(self.store_path, self.embeddings)
        else:
            self.db = FAISS.from_texts(
                texts=["initialization"], 
                embedding=self.embeddings
            )
            self.db.save_local(self.store_path)

    async def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """Add texts to vector store"""
        # Split texts if they're too long
        all_splits = []
        all_metadatas = []
        
        for i, text in enumerate(texts):
            splits = self.text_splitter.split_text(text)
            all_splits.extend(splits)
            
            if metadatas:
                all_metadatas.extend([metadatas[i]] * len(splits))
        
        # Add to vector store
        self.db.add_texts(
            texts=all_splits,
            metadatas=all_metadatas if all_metadatas else None
        )
        # Save updated store
        self.db.save_local(self.store_path)

    async def similarity_search(self, query: str, k: int = 4):
        """Search for similar texts"""
        return self.db.similarity_search(query, k=k)

    async def similarity_search_with_score(self, query: str, k: int = 4):
        """Search for similar texts and return with scores"""
        return self.db.similarity_search_with_score(query, k=k)