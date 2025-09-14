"""
Enhanced querying system using PostgreSQL and local embeddings
Replaces LlamaCloud index with local vector search
"""

import os
from typing import Union, Optional
from dotenv import load_dotenv

from postgres_manager import DOCUMENT_MANAGER

load_dotenv()


class EnhancedQueryEngine:
    """
    Enhanced query engine using PostgreSQL vector search
    """
    
    def __init__(self):
        self.document_manager = DOCUMENT_MANAGER
    
    async def query_index(self, question: str) -> Union[str, None]:
        """
        Query the document index using vector search
        
        Args:
            question: The question to search for
            
        Returns:
            Formatted response with sources or None if no answer found
        """
        try:
            # First, try using the vector index if available
            if self.document_manager.vector_index:
                response = await self.document_manager.query_documents(question)
                if response:
                    return response
            
            # Fallback to semantic search
            search_results = await self.document_manager.search_documents(
                query=question,
                limit=5,
                similarity_threshold=0.6
            )
            
            if not search_results:
                return None
            
            # Build response from search results
            response_parts = []
            sources = []
            
            for doc, similarity in search_results:
                # Add relevant content based on the question
                if self._is_relevant_to_question(question, doc.summary):
                    response_parts.append(doc.summary)
                    sources.append(f"{doc.document_name} (similarity: {similarity:.2f})")
                elif self._is_relevant_to_question(question, doc.content[:500]):
                    # Use first 500 chars if summary not relevant
                    response_parts.append(doc.content[:500] + "...")
                    sources.append(f"{doc.document_name} (similarity: {similarity:.2f})")
            
            if not response_parts:
                return None
            
            # Combine responses
            combined_response = "\n\n".join(response_parts[:3])  # Limit to top 3
            
            formatted_response = (
                "## Answer\n\n"
                + combined_response
                + "\n\n## Sources\n\n- "
                + "\n- ".join(sources)
            )
            
            return formatted_response
            
        except Exception as e:
            print(f"Error in query_index: {e}")
            return None
    
    def _is_relevant_to_question(self, question: str, text: str) -> bool:
        """
        Simple relevance check based on keyword overlap
        """
        question_words = set(question.lower().split())
        text_words = set(text.lower().split())
        
        # Calculate word overlap
        overlap = len(question_words.intersection(text_words))
        relevance_threshold = max(1, len(question_words) * 0.2)  # At least 20% overlap
        
        return overlap >= relevance_threshold
    
    async def search_documents_by_content(
        self, 
        query: str, 
        limit: int = 10
    ) -> list:
        """
        Search documents by content
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        try:
            search_results = await self.document_manager.search_documents(
                query=query,
                limit=limit,
                similarity_threshold=0.5
            )
            
            return [doc for doc, _ in search_results]
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    async def get_document_by_name(self, document_name: str) -> Optional[object]:
        """
        Get a specific document by name
        
        Args:
            document_name: Name of the document
            
        Returns:
            Document object or None if not found
        """
        try:
            documents = self.document_manager.get_documents(names=[document_name])
            return documents[0] if documents else None
            
        except Exception as e:
            print(f"Error getting document by name: {e}")
            return None
    
    async def get_all_documents(self) -> list:
        """
        Get all documents from the database
        
        Returns:
            List of all documents
        """
        try:
            return self.document_manager.get_documents()
        except Exception as e:
            print(f"Error getting all documents: {e}")
            return []
    
    async def get_document_stats(self) -> dict:
        """
        Get statistics about the document collection
        
        Returns:
            Dictionary with stats
        """
        try:
            documents = await self.get_all_documents()
            
            stats = {
                "total_documents": len(documents),
                "processed_documents": sum(1 for doc in documents if doc.is_processed),
                "total_content_length": sum(len(doc.content) for doc in documents),
                "document_names": [doc.document_name for doc in documents],
                "recent_documents": [
                    doc.document_name for doc in sorted(
                        documents, 
                        key=lambda x: x.created_at or "", 
                        reverse=True
                    )[:5]
                ]
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {}


# Global query engine instance
QUERY_ENGINE = EnhancedQueryEngine()


# Legacy compatibility functions
async def query_index(question: str) -> Union[str, None]:
    """Legacy compatibility function"""
    return await QUERY_ENGINE.query_index(question)
