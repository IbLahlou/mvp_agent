# src/services/vector_store.py
import faiss
import numpy as np
from typing import List, Tuple
from pathlib import Path
import pickle
import os
from langchain_community.embeddings import OpenAIEmbeddings

class VectorStore:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.embeddings = OpenAIEmbeddings()
        self.chunk_ids = []
        
    def add_texts(self, texts: List[str]) -> List[str]:
        """Add texts to the vector store."""
        # Generate embeddings
        embeddings = self.embeddings.embed_documents(texts)
        
        # Generate IDs for new vectors
        start_idx = len(self.chunk_ids)
        new_ids = [f"vec_{i}" for i in range(start_idx, start_idx + len(texts))]
        
        # Add to FAISS index
        self.index.add(np.array(embeddings))
        self.chunk_ids.extend(new_ids)
        
        return new_ids
    
    def similarity_search(self, query: str, k: int = 4) -> List[Tuple[str, float]]:
        """Search for similar texts."""
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search in FAISS
        D, I = self.index.search(np.array([query_embedding]), k)
        
        # Return IDs and distances
        results = []
        for i, (dist, idx) in enumerate(zip(D[0], I[0])):
            if idx < len(self.chunk_ids):
                results.append((self.chunk_ids[idx], float(dist)))
        
        return results
    
    def save(self, directory: str):
        """Save the vector store to disk."""
        os.makedirs(directory, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, os.path.join(directory, "index.faiss"))
        
        # Save chunk IDs
        with open(os.path.join(directory, "chunk_ids.pkl"), "wb") as f:
            pickle.dump(self.chunk_ids, f)
    
    @classmethod
    def load(cls, directory: str) -> "VectorStore":
        """Load vector store from disk."""
        store = cls()
        
        # Load FAISS index
        store.index = faiss.read_index(os.path.join(directory, "index.faiss"))
        
        # Load chunk IDs
        with open(os.path.join(directory, "chunk_ids.pkl"), "rb") as f:
            store.chunk_ids = pickle.load(f)
        
        return store