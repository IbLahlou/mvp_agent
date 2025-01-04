# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

# Database setup
os.makedirs('data', exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DocumentMetadata(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    vector_store_key = Column(String)  # To track which FAISS index this belongs to
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FAISS vectorstore initialization
embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_texts(
    texts=["Initial document"], 
    embedding=embeddings,
    metadatas=[{"source": "initialization"}]
)
# Save initial vectorstore
vector_store.save_local("data/faiss_index")