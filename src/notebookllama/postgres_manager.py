"""
PostgreSQL-based document storage and vector search system
Replaces LlamaCloud index functionality with local PostgreSQL + pgvector
"""

import os
import json
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import asyncio
from datetime import datetime

import pandas as pd
from sqlalchemy import (
    create_engine, 
    Column, 
    String, 
    Text, 
    Integer, 
    DateTime, 
    Float,
    JSON,
    Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.postgres import PGVectorStore 
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.core.response import Response

from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class DocumentRecord(Base):
    """Enhanced document record with embeddings support"""
    __tablename__ = "documents_enhanced"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    q_and_a = Column(Text, nullable=False)
    mindmap = Column(Text, nullable=False)
    bullet_points = Column(Text, nullable=False)
    
    # Enhanced fields
    doc_metadata = Column(JSON, nullable=True)
    extracted_tables = Column(JSON, nullable=True)
    extracted_images = Column(JSON, nullable=True)
    
    # Embedding fields
    content_embedding = Column(Vector(1536), nullable=True)  # OpenAI embeddings dimension
    summary_embedding = Column(Vector(1536), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)


class DocumentChunk(Base):
    """Document chunks for better retrieval"""
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String, default="text")  # text, table, image_caption, etc.
    
    # Embedding
    embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


@dataclass
class EnhancedDocument:
    """Enhanced document container"""
    id: str
    document_name: str
    content: str
    summary: str
    q_and_a: str
    mindmap: str
    bullet_points: str
    doc_metadata: Optional[Dict[str, Any]] = None
    extracted_tables: Optional[List[Dict]] = None
    extracted_images: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    is_processed: bool = False


class PostgreSQLDocumentManager:
    """
    Enhanced document manager with PostgreSQL and vector search capabilities
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        # Database setup
        self.database_url = database_url or self._build_database_url()
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        # Embedding setup
        if os.getenv("OPENAI_API_KEY"):
            self.embedding_model = OpenAIEmbedding(
                model=embedding_model,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.llm = OpenAI(
                model="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            self.embedding_model = None
            self.llm = None
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize vector store
        self._init_vector_store()

    def _build_database_url(self) -> str:
        """Build database URL from environment variables"""
        user = os.getenv('pgql_user', 'postgres')
        password = os.getenv('pgql_psw', 'admin')
        host = os.getenv('pgql_host', 'localhost')
        port = os.getenv('pgql_port', '5432')
        db_name = os.getenv('pgql_db', 'postgres')
        
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"

    def _init_vector_store(self):
        """Initialize PGVector store for vector search"""
        try:
            if self.embedding_model:
                print("Initializing vector store...")
                self.vector_store = PGVectorStore.from_params(
                    database=os.getenv('pgql_db', 'postgres'),
                    host=os.getenv('pgql_host', 'localhost'),
                    password=os.getenv('pgql_psw', 'admin'),
                    port=int(os.getenv('pgql_port', '5432')),
                    user=os.getenv('pgql_user', 'postgres'),
                    table_name="llamaindex_embedding",
                    embed_dim=1536,  # OpenAI embedding dimension
                )
                
                # Configure LlamaIndex settings
                Settings.embed_model = self.embedding_model
                Settings.llm = self.llm
                
                # Create vector index
                self.vector_index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store
                )
                print("Vector store initialized successfully")
            else:
                print("No embedding model available - vector store disabled")
                self.vector_store = None
                self.vector_index = None
        except Exception as e:
            print(f"CRITICAL: Could not initialize vector store: {e}")
            print(f"   - Check if PostgreSQL is running with pgvector extension")
            print(f"   - Verify OpenAI API key is valid")
            print(f"   - Confirm database connection parameters")
            self.vector_store = None
            self.vector_index = None

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    async def put_document(self, document: EnhancedDocument) -> str:
        """Store enhanced document with embeddings"""
        session = self.get_session()
        try:
            # Generate embeddings if model is available
            content_embedding = None
            summary_embedding = None
            
            if self.embedding_model:
                try:
                    # Only generate summary embedding here (content will be chunked later)
                    # Don't embed full content as it may exceed token limits
                    content_embedding = None  # Will be handled by chunks in _add_to_vector_store
                    summary_embedding = self.embedding_model.get_text_embedding(document.summary)
                    print(f"Generated summary embedding: {len(summary_embedding) if summary_embedding else 0} dimensions")
                except Exception as e:
                    print(f"Warning: Could not generate embeddings: {e}")
                    content_embedding = None
                    summary_embedding = None

            # Create document record
            doc_record = DocumentRecord(
                id=document.id,
                document_name=document.document_name,
                content=document.content,
                summary=document.summary,
                q_and_a=document.q_and_a,
                mindmap=document.mindmap,
                bullet_points=document.bullet_points,
                doc_metadata=document.doc_metadata,
                extracted_tables=document.extracted_tables,
                extracted_images=document.extracted_images,
                content_embedding=content_embedding,
                summary_embedding=summary_embedding,
                is_processed=document.is_processed,
            )
            
            session.add(doc_record)
            session.commit()
            
            # Create document chunks for better retrieval
            await self._create_document_chunks(document.id, document.content, session)
            
            # Add to vector store
            if self.vector_store and document.content:
                await self._add_to_vector_store(document)
            
            return document.id
            
        except Exception as e:
            session.rollback()
            raise Exception(f"Error storing document: {str(e)}")
        finally:
            session.close()

    async def _create_document_chunks(self, document_id: str, content: str, session: Session):
        """Create document chunks for better retrieval"""
        if not self.embedding_model:
            return
            
        try:
            # Simple chunking strategy
            words = content.split()
            chunk_size_words = self.chunk_size // 4  # Approximate words per chunk
            overlap_words = self.chunk_overlap // 4
            
            chunks = []
            for i in range(0, len(words), chunk_size_words - overlap_words):
                chunk_words = words[i:i + chunk_size_words]
                chunk_text = ' '.join(chunk_words)
                
                if chunk_text.strip():
                    # Generate embedding for chunk
                    try:
                        embedding = self.embedding_model.get_text_embedding(chunk_text)
                    except Exception as e:
                        print(f"Warning: Could not generate chunk embedding: {e}")
                        embedding = None
                    
                    chunk_record = DocumentChunk(
                        document_id=document_id,
                        chunk_text=chunk_text,
                        chunk_index=len(chunks),
                        embedding=embedding,
                        doc_metadata={"chunk_word_start": i, "chunk_word_end": i + chunk_size_words}
                    )
                    chunks.append(chunk_record)
            
            session.add_all(chunks)
            session.commit()
            
        except Exception as e:
            print(f"Warning: Could not create document chunks: {e}")

    async def _add_to_vector_store(self, document: EnhancedDocument):
        """Add document to vector store for semantic search"""
        if not self.vector_store:
            return

        try:
            # Create LlamaIndex documents with embeddings
            doc_nodes = []

            # Chunk the content to avoid token limits (8192 max for embeddings)
            max_chunk_size = 3000  # Conservative size to stay well under 8192 token limit
            content_chunks = []

            # Split content into chunks
            words = document.content.split()
            current_chunk = []
            current_size = 0

            for word in words:
                current_chunk.append(word)
                current_size += len(word) + 1  # +1 for space

                if current_size >= max_chunk_size:
                    chunk_text = ' '.join(current_chunk)
                    content_chunks.append(chunk_text)
                    current_chunk = []
                    current_size = 0

            # Add remaining words
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                content_chunks.append(chunk_text)

            print(f"Splitting document into {len(content_chunks)} chunks for embedding")
            print(f"First chunk preview: {content_chunks[0][:200]}..." if content_chunks else "No chunks created")

            # Process each chunk
            for i, chunk_text in enumerate(content_chunks):
                chunk_embedding = None

                if self.embedding_model:
                    try:
                        chunk_embedding = self.embedding_model.get_text_embedding(chunk_text)
                    except Exception as e:
                        print(f"Warning: Could not generate embedding for chunk {i+1}: {e}")
                        continue  # Skip this chunk but continue with others

                # Create node for this chunk
                chunk_node = TextNode(
                    text=chunk_text,
                    embedding=chunk_embedding,
                    doc_metadata={
                        "document_id": document.id,
                        "document_name": document.document_name,
                        "type": "content",
                        "chunk_index": i,
                        "total_chunks": len(content_chunks),
                        "created_at": document.created_at.isoformat() if document.created_at else None
                    }
                )
                doc_nodes.append(chunk_node)

            # Also add summary as a separate node
            if document.summary:
                summary_embedding = None
                if self.embedding_model:
                    try:
                        summary_embedding = self.embedding_model.get_text_embedding(document.summary)
                    except Exception as e:
                        print(f"Warning: Could not generate summary embedding: {e}")

                # Summary as separate node with embedding
                summary_node = TextNode(
                    text=document.summary,
                    embedding=summary_embedding,  # Set the embedding directly
                    doc_metadata={
                        "document_id": document.id,
                        "document_name": document.document_name,
                        "type": "summary",
                        "created_at": document.created_at.isoformat() if document.created_at else None
                    }
                )
                doc_nodes.append(summary_node)
            
            # Add nodes to vector store
            self.vector_store.add(doc_nodes)
            print(f"Successfully added {len(doc_nodes)} nodes to vector store")

            # Refresh the vector index to make new documents searchable
            if self.vector_index:
                # Recreate the index to ensure new documents are searchable
                from llama_index.core import VectorStoreIndex
                self.vector_index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store
                )
                print("Vector index refreshed with new documents")

        except Exception as e:
            print(f"Warning: Could not add to vector store: {e}")

    def get_documents(self, names: Optional[List[str]] = None) -> List[EnhancedDocument]:
        """Retrieve documents with enhanced data"""
        session = self.get_session()
        try:
            query = session.query(DocumentRecord)
            
            if names:
                query = query.filter(DocumentRecord.document_name.in_(names))
            
            query = query.order_by(DocumentRecord.created_at.desc())
            records = query.all()
            
            documents = []
            for record in records:
                doc = EnhancedDocument(
                    id=record.id,
                    document_name=record.document_name,
                    content=record.content,
                    summary=record.summary,
                    q_and_a=record.q_and_a,
                    mindmap=record.mindmap,
                    bullet_points=record.bullet_points,
                    doc_metadata=record.doc_metadata,
                    extracted_tables=record.extracted_tables,
                    extracted_images=record.extracted_images,
                    created_at=record.created_at,
                    is_processed=record.is_processed
                )
                documents.append(doc)
                
            return documents
            
        finally:
            session.close()

    def get_document_names(self) -> List[str]:
        """Get list of all document names"""
        session = self.get_session()
        try:
            names = session.query(DocumentRecord.document_name).distinct().all()
            return [name[0] for name in names]
        finally:
            session.close()

    async def search_documents(
        self, 
        query: str, 
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[EnhancedDocument, float]]:
        """Semantic search using embeddings"""
        if not self.embedding_model:
            # Fallback to basic text search
            return await self._basic_text_search(query, limit)
        
        session = self.get_session()
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.get_text_embedding(query)
            
            # Search using cosine similarity
            # This is a simplified version - you might want to use pgvector operators
            # For now, we'll use basic filtering and return top results
            
            records = session.query(DocumentRecord).filter(
                DocumentRecord.is_processed == True
            ).limit(limit * 2).all()  # Get more records to filter
            
            results = []
            for record in records:
                if record.content_embedding is not None and len(record.content_embedding) > 0:
                    # Calculate similarity (simplified)
                    similarity = self._calculate_similarity(query_embedding, record.content_embedding)
                    if similarity >= similarity_threshold:
                        doc = EnhancedDocument(
                            id=record.id,
                            document_name=record.document_name,
                            content=record.content,
                            summary=record.summary,
                            q_and_a=record.q_and_a,
                            mindmap=record.mindmap,
                            bullet_points=record.bullet_points,
                            doc_metadata=record.doc_metadata,
                            extracted_tables=record.extracted_tables,
                            extracted_images=record.extracted_images,
                            created_at=record.created_at,
                            is_processed=record.is_processed
                        )
                        results.append((doc, similarity))
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
            
        finally:
            session.close()

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            similarity = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            return float(similarity)
        except:
            return 0.0

    async def _basic_text_search(self, query: str, limit: int) -> List[Tuple[EnhancedDocument, float]]:
        """Basic text search fallback"""
        session = self.get_session()
        try:
            # Simple text matching
            records = session.query(DocumentRecord).filter(
                DocumentRecord.content.ilike(f"%{query}%")
            ).limit(limit).all()
            
            results = []
            for record in records:
                doc = EnhancedDocument(
                    id=record.id,
                    document_name=record.document_name,
                    content=record.content,
                    summary=record.summary,
                    q_and_a=record.q_and_a,
                    mindmap=record.mindmap,
                    bullet_points=record.bullet_points,
                    doc_metadata=record.doc_metadata,
                    extracted_tables=record.extracted_tables,
                    extracted_images=record.extracted_images,
                    created_at=record.created_at,
                    is_processed=record.is_processed
                )
                results.append((doc, 1.0))  # Mock similarity score
                
            return results
            
        finally:
            session.close()

    async def query_documents(self, question: str) -> Optional[str]:
        """Query documents using the vector index"""
        if not self.vector_index:
            return None
            
        try:
            # Create query engine with citations
            query_engine = CitationQueryEngine(
                retriever=self.vector_index.as_retriever(similarity_top_k=5),
                llm=self.llm,
                citation_chunk_size=256,
                citation_chunk_overlap=50,
            )
            
            # Query the index
            response = await query_engine.aquery(question)
            
            if not response.response:
                return None
                
            # Format response with sources
            sources = []
            if response.source_nodes:
                sources = [node.text for node in response.source_nodes]
            
            formatted_response = (
                "## Answer\n\n"
                + response.response
                + "\n\n## Sources\n\n- "
                + "\n- ".join(sources)
            )
            
            return formatted_response
            
        except Exception as e:
            print(f"Error querying documents: {e}")
            return None

    def disconnect(self) -> None:
        """Close database connections"""
        if hasattr(self, 'engine'):
            self.engine.dispose()


# Global instance
database_url = f"postgresql+psycopg2://{os.getenv('pgql_user')}:{os.getenv('pgql_psw')}@localhost:5432/{os.getenv('pgql_db')}"
DOCUMENT_MANAGER = PostgreSQLDocumentManager(database_url=database_url)
