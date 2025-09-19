"""
Enhanced querying system using PostgreSQL and local embeddings
Replaces LlamaCloud index with local vector search
"""

import os
from typing import Union, Optional
from dotenv import load_dotenv

try:
    from .postgres_manager import DOCUMENT_MANAGER
except ImportError:
    # Fallback for when module is imported directly
    from postgres_manager import DOCUMENT_MANAGER

load_dotenv()


class EnhancedQueryEngine:
    """
    Enhanced query engine using PostgreSQL vector search
    """
    
    def __init__(self):
        self.document_manager = DOCUMENT_MANAGER
    
    def query_index_sync(self, question: str) -> Union[str, None]:
        """
        Synchronous wrapper for query_index that avoids async conflicts
        """
        print(f"Starting query for: {question}")

        try:
            # Direct synchronous query using the vector index's query engine
            if self.document_manager.vector_index:
                print("Using vector index for search...")

                # Create a comprehensive query engine from the index with better response generation
                from llama_index.core.prompts import PromptTemplate

                # Custom prompt template for more comprehensive responses
                qa_template = PromptTemplate(
                    "Context information is below.\n"
                    "---------------------\n"
                    "{context_str}\n"
                    "---------------------\n"
                    "Given the context information and not prior knowledge, "
                    "answer the question in detail. Provide a comprehensive response "
                    "that thoroughly addresses the question using the available information. "
                    "Include specific details, examples, and explanations from the context.\n"
                    "Question: {query_str}\n"
                    "Answer: "
                )

                query_engine = self.document_manager.vector_index.as_query_engine(
                    similarity_top_k=10,  # Get more relevant chunks
                    response_mode="compact",  # Use compact mode for more detailed responses
                    verbose=True,  # Enable verbose output for debugging
                    text_qa_template=qa_template  # Use custom prompt for detailed responses
                )

                # Execute the query synchronously
                response = query_engine.query(question)

                if response and response.response:
                    print(f"Vector search found response: {len(str(response.response))} characters")
                    print(f"DEBUG: Response content: {str(response.response)[:500]}")
                    print(f"DEBUG: Number of source nodes: {len(response.source_nodes) if response.source_nodes else 0}")

                    # Format the response with sources
                    formatted_response = f"{response.response}\n\n"

                    if response.source_nodes:
                        formatted_response += "\n\n**Sources:**\n"
                        for i, node in enumerate(response.source_nodes[:3]):  # Limit to top 3 sources
                            print(f"DEBUG: Source {i+1} preview: {node.text[:200]}")
                            # Show more context from sources
                            source_text = node.text[:300].strip()
                            if len(node.text) > 300:
                                source_text += "..."
                            formatted_response += f"{i+1}. {source_text}\n\n"

                    return formatted_response
                else:
                    print("Vector search returned no results")
                    return "I couldn't find relevant information in the document to answer your question."
            else:
                print("Vector index not available")
                return "The document index is not available. Please ensure a document has been processed."

        except Exception as e:
            print(f"Error in query_index_sync: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return f"I encountered an error while searching: {str(e)}"

    async def query_index(self, question: str) -> Union[str, None]:
        """
        Query the document index using vector search
        
        Args:
            question: The question to search for
            
        Returns:
            Formatted response with sources or None if no answer found
        """
        print(f"Starting query for: {question}")
        
        try:
            # First, try using the vector index if available
            if self.document_manager.vector_index:
                print("Using vector index for search...")
                response = await self.document_manager.query_documents(question)
                if response:
                    print(f"Vector search found response: {len(response)} characters")
                    return response
                else:
                    print("Vector search returned no results")
            else:
                print("Vector index not available - falling back to direct search")
            
            # Fallback to semantic search
            print("Trying semantic search fallback...")
            search_results = await self.document_manager.search_documents(
                query=question,
                limit=5,
                similarity_threshold=0.5  # Lower threshold for better recall
            )
            
            print(f"Found {len(search_results)} semantic search results")
            
            if not search_results:
                print("No semantic search results found")
                return None
            
            # Build response from search results
            response_parts = []
            sources = []
            
            for doc, similarity in search_results:
                print(f"   - Document: {doc.document_name} (similarity: {similarity:.2f})")
                
                # Always include content if it exists and is relevant
                if doc.content and len(doc.content.strip()) > 50:
                    if self._is_relevant_to_question(question, doc.content):
                        # Use the most relevant part of the content
                        content_snippet = self._extract_relevant_snippet(question, doc.content)
                        response_parts.append(content_snippet)
                        sources.append(f"{doc.document_name} (similarity: {similarity:.2f})")
                    elif self._is_relevant_to_question(question, doc.summary):
                        response_parts.append(doc.summary)
                        sources.append(f"{doc.document_name} - Summary (similarity: {similarity:.2f})")
                elif doc.summary and len(doc.summary.strip()) > 20:
                    response_parts.append(doc.summary)
                    sources.append(f"{doc.document_name} - Summary (similarity: {similarity:.2f})")
            
            if not response_parts:
                print("No relevant content found in search results")
                return None
            
            # Combine responses
            combined_response = "\n\n".join(response_parts[:3])  # Limit to top 3
            
            formatted_response = (
                "## Answer\n\n"
                + combined_response
                + "\n\n## Sources\n\n- "
                + "\n- ".join(sources[:3])
            )
            
            print(f"Generated response with {len(formatted_response)} characters")
            return formatted_response
            
        except Exception as e:
            print(f"Error in query_index: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return None
    
    def _is_relevant_to_question(self, question: str, text: str) -> bool:
        """
        Simple relevance check based on keyword overlap
        """
        question_words = set(question.lower().split())
        text_words = set(text.lower().split())
        
        # Calculate word overlap
        overlap = len(question_words.intersection(text_words))
        relevance_threshold = max(1, len(question_words) * 0.15)  # At least 15% overlap
        
        return overlap >= relevance_threshold
    
    def _extract_relevant_snippet(self, question: str, content: str, max_length: int = 800) -> str:
        """
        Extract the most relevant snippet from content based on question
        """
        question_words = set(word.lower() for word in question.split() if len(word) > 3)
        
        # Split content into sentences
        sentences = content.replace('\n', ' ').split('. ')
        
        # Score sentences based on question word overlap
        scored_sentences = []
        for sentence in sentences:
            sentence_words = set(word.lower() for word in sentence.split())
            overlap = len(question_words.intersection(sentence_words))
            if overlap > 0:
                scored_sentences.append((overlap, sentence.strip()))
        
        if not scored_sentences:
            # If no overlap found, return beginning of content
            return content[:max_length] + ("..." if len(content) > max_length else "")
        
        # Sort by relevance and combine top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        
        snippet = ""
        for score, sentence in scored_sentences[:3]:  # Top 3 sentences
            if len(snippet) + len(sentence) < max_length:
                snippet += sentence + ". "
            else:
                break
        
        return snippet.strip() or content[:max_length] + ("..." if len(content) > max_length else "")
    
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
