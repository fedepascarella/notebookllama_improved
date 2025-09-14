"""
Enhanced MCP server using Docling and PostgreSQL
Replaces LlamaCloud dependencies
"""

import os
import sys
from typing import List, Union, Literal

from fastmcp import FastMCP

# Import enhanced modules
from docling_processor import DOCLING_PROCESSOR
from enhanced_querying import QUERY_ENGINE
from mindmap import get_mind_map

# MCP server instance
mcp: FastMCP = FastMCP(name="Enhanced MCP For NotebookLM")


@mcp.tool(
    name="process_file_tool",
    description="Process files using Docling and produce summaries, question-answers and highlights.",
)
async def process_file_tool(
    filename: str,
) -> Union[str, Literal["Sorry, your file could not be processed."]]:
    """
    Process a file using the enhanced Docling processor
    
    Args:
        filename: Path to the file to process
        
    Returns:
        JSON string with notebook data + separator + markdown content
    """
    try:
        notebook_json, md_content = await DOCLING_PROCESSOR.process_file_complete(filename)
        
        if notebook_json is None:
            return "Sorry, your file could not be processed."
        
        if md_content is None:
            md_content = ""
        
        return notebook_json + "\n%separator%\n" + md_content
        
    except Exception as e:
        print(f"Error in process_file_tool: {e}")
        return "Sorry, your file could not be processed."


@mcp.tool(
    name="get_mind_map_tool", 
    description="Generate a mind map from summary and highlights using local processing."
)
async def get_mind_map_tool(
    summary: str, 
    highlights: List[str]
) -> Union[str, Literal["Sorry, mind map creation failed."]]:
    """
    Generate a mind map from summary and highlights
    
    Args:
        summary: Document summary
        highlights: List of key highlights
        
    Returns:
        HTML file path for the mind map
    """
    try:
        mind_map_file = await get_mind_map(summary=summary, highlights=highlights)
        
        if mind_map_file is None:
            return "Sorry, mind map creation failed."
        
        return mind_map_file
        
    except Exception as e:
        print(f"Error in get_mind_map_tool: {e}")
        return "Sorry, mind map creation failed."


@mcp.tool(
    name="query_index_tool", 
    description="Query the enhanced PostgreSQL document index with vector search."
)
async def query_index_tool(question: str) -> str:
    """
    Query the document index using enhanced search capabilities
    
    Args:
        question: Question to search for
        
    Returns:
        Answer with sources or error message
    """
    try:
        response = await QUERY_ENGINE.query_index(question=question)
        
        if response is None:
            return "Sorry, I was unable to find an answer to your question."
        
        return response
        
    except Exception as e:
        print(f"Error in query_index_tool: {e}")
        return "Sorry, I was unable to find an answer to your question."


@mcp.tool(
    name="search_documents_tool",
    description="Search documents by content using semantic search."
)
async def search_documents_tool(
    query: str, 
    limit: int = 5
) -> Union[str, Literal["No documents found."]]:
    """
    Search documents by content with semantic search
    
    Args:
        query: Search query
        limit: Maximum number of results (default: 5)
        
    Returns:
        JSON string with search results
    """
    try:
        documents = await QUERY_ENGINE.search_documents_by_content(
            query=query, 
            limit=limit
        )
        
        if not documents:
            return "No documents found."
        
        # Format results
        results = []
        for doc in documents:
            result = {
                "id": doc.id,
                "name": doc.document_name,
                "summary": doc.summary[:200] + "..." if len(doc.summary) > 200 else doc.summary,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "is_processed": doc.is_processed
            }
            results.append(result)
        
        import json
        return json.dumps(results, indent=2)
        
    except Exception as e:
        print(f"Error in search_documents_tool: {e}")
        return "No documents found."


@mcp.tool(
    name="get_document_stats_tool",
    description="Get statistics about the document collection."
)
async def get_document_stats_tool() -> str:
    """
    Get statistics about the document collection
    
    Returns:
        JSON string with collection stats
    """
    try:
        stats = await QUERY_ENGINE.get_document_stats()
        
        import json
        return json.dumps(stats, indent=2)
        
    except Exception as e:
        print(f"Error in get_document_stats_tool: {e}")
        return "{\"error\": \"Could not retrieve document statistics\"}"


@mcp.tool(
    name="extract_tables_and_images_tool",
    description="Extract tables and images from a document using Docling."
)
async def extract_tables_and_images_tool(filename: str) -> str:
    """
    Extract tables and images from a document
    
    Args:
        filename: Path to the file to process
        
    Returns:
        JSON string with extraction results
    """
    try:
        images, tables = await DOCLING_PROCESSOR.extract_plots_and_tables(filename)
        
        # Format results
        result = {
            "images": images or [],
            "tables_count": len(tables) if tables else 0,
            "tables_info": []
        }
        
        if tables:
            for i, table in enumerate(tables):
                table_info = {
                    "index": i,
                    "rows": len(table),
                    "columns": len(table.columns),
                    "column_names": table.columns.tolist()
                }
                result["tables_info"].append(table_info)
        
        import json
        return json.dumps(result, indent=2)
        
    except Exception as e:
        print(f"Error in extract_tables_and_images_tool: {e}")
        return "{\"error\": \"Could not extract tables and images\"}"


if __name__ == "__main__":
    # Run the MCP server
    print("Starting Enhanced MCP Server for NotebookLM...")
    print("Using Docling for document processing and PostgreSQL for storage")
    mcp.run(transport="streamable-http")
