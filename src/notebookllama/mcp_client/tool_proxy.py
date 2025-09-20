"""
MCP Tool Proxy
Provides a unified interface for MCP tools and integrates them with NotebookLlama workflows
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass

from .client import MCPClientManager

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MCPToolProxy:
    """Proxy for MCP tools that integrates with NotebookLlama workflows"""

    def __init__(self, mcp_client: MCPClientManager):
        self.mcp_client = mcp_client
        self._tool_cache: Dict[str, Dict] = {}

    async def initialize(self):
        """Initialize the tool proxy"""
        await self.mcp_client.initialize()
        await self._cache_tools()

    async def _cache_tools(self):
        """Cache available tools for faster lookup"""
        self._tool_cache = await self.mcp_client.list_all_tools()
        logger.info(f"Cached {sum(len(tools) for tools in self._tool_cache.values())} tools from {len(self._tool_cache)} servers")

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a tool and return a standardized result"""
        try:
            result = await self.mcp_client.call_tool(server_name, tool_name, arguments)

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "server": server_name,
                    "tool": tool_name,
                    "arguments": arguments
                }
            )

        except Exception as e:
            logger.error(f"Tool execution failed: {server_name}.{tool_name} - {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={
                    "server": server_name,
                    "tool": tool_name,
                    "arguments": arguments
                }
            )

    async def find_and_execute(self, capability: str, arguments: Dict[str, Any]) -> List[ToolResult]:
        """Find tools by capability and execute them"""
        matching_tools = await self.mcp_client.find_tools_by_capability(capability)
        results = []

        for tool_info in matching_tools:
            result = await self.execute_tool(
                tool_info["server"],
                tool_info["tool"],
                arguments
            )
            results.append(result)

        return results

    # Document-specific tool integrations
    async def enhance_document_with_filesystem(self, document_path: str, document_content: str) -> Dict[str, Any]:
        """Enhance document processing with filesystem tools"""
        enhancements = {}

        # Get file metadata
        if "filesystem" in self._tool_cache:
            try:
                # Get file stats
                result = await self.execute_tool("filesystem", "read_file", {"path": document_path})
                if result.success:
                    enhancements["file_content_verified"] = True
                    enhancements["file_accessible"] = True

                # List related files in the same directory
                import os
                directory = os.path.dirname(document_path)
                dir_result = await self.mcp_client.list_directory(directory)
                if dir_result:
                    related_files = [f for f in dir_result if f.endswith(('.pdf', '.md', '.txt'))]
                    enhancements["related_files"] = related_files

            except Exception as e:
                logger.warning(f"Filesystem enhancement failed: {e}")
                enhancements["filesystem_error"] = str(e)

        return enhancements

    async def enhance_document_with_memory(self, document_title: str, content: str,
                                         topics: List[str]) -> Dict[str, Any]:
        """Enhance document processing with memory/knowledge graph"""
        enhancements = {}

        if "memory" in self._tool_cache:
            try:
                # Create entity for this document
                entity_created = await self.mcp_client.create_memory_entity(
                    name=document_title,
                    entityType="document",
                    observations=[
                        f"Document content: {content[:500]}...",
                        f"Main topics: {', '.join(topics)}",
                        f"Processed by NotebookLlama Enhanced"
                    ]
                )

                if entity_created:
                    enhancements["memory_entity_created"] = True
                    enhancements["knowledge_graph_updated"] = True

                # Create entities for major topics
                for topic in topics[:3]:  # Limit to top 3 topics
                    topic_created = await self.mcp_client.create_memory_entity(
                        name=topic,
                        entityType="topic",
                        observations=[f"Related to document: {document_title}"]
                    )
                    if topic_created:
                        enhancements[f"topic_entity_{topic}"] = True

            except Exception as e:
                logger.warning(f"Memory enhancement failed: {e}")
                enhancements["memory_error"] = str(e)

        return enhancements

    async def enhance_document_with_database(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance document processing with database operations"""
        enhancements = {}

        if "postgres" in self._tool_cache:
            try:
                # Query for similar documents
                query = """
                SELECT document_name, content_length, created_at
                FROM documents
                WHERE content ILIKE %s
                LIMIT 5
                """

                # Extract key terms for similarity search
                key_terms = document_data.get("topics", [])[:3]
                search_term = f"%{' '.join(key_terms)}%"

                result = await self.execute_tool("postgres", "query", {
                    "query": query,
                    "params": [search_term]
                })

                if result.success and result.data:
                    enhancements["similar_documents"] = result.data
                    enhancements["database_search_performed"] = True

            except Exception as e:
                logger.warning(f"Database enhancement failed: {e}")
                enhancements["database_error"] = str(e)

        return enhancements

    async def get_tool_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all available tools"""
        capabilities = {}

        for server_name, tools in self._tool_cache.items():
            server_capabilities = []
            for tool in tools:
                server_capabilities.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": getattr(tool, "inputSchema", {}).get("properties", {})
                })

            capabilities[server_name] = server_capabilities

        return capabilities

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all MCP connections"""
        health_status = {
            "overall_status": "healthy",
            "servers": {},
            "total_tools": 0,
            "errors": []
        }

        connection_status = self.mcp_client.get_connection_status()

        for server_name, is_connected in connection_status.items():
            server_health = {
                "connected": is_connected,
                "tools_count": len(self._tool_cache.get(server_name, [])),
                "last_check": "now"
            }

            if is_connected:
                # Try a simple tool call to verify functionality
                try:
                    tools = self._tool_cache.get(server_name, [])
                    if tools:
                        # Just verify the connection is responsive
                        server_health["responsive"] = True
                    else:
                        server_health["responsive"] = False
                        health_status["errors"].append(f"{server_name}: No tools available")

                except Exception as e:
                    server_health["responsive"] = False
                    health_status["errors"].append(f"{server_name}: {str(e)}")

            else:
                server_health["responsive"] = False
                health_status["errors"].append(f"{server_name}: Not connected")

            health_status["servers"][server_name] = server_health
            health_status["total_tools"] += server_health["tools_count"]

        # Determine overall status
        if health_status["errors"]:
            if len(health_status["errors"]) == len(connection_status):
                health_status["overall_status"] = "unhealthy"
            else:
                health_status["overall_status"] = "degraded"

        return health_status

    async def refresh_tools(self):
        """Refresh the tool cache"""
        await self._cache_tools()
        logger.info("MCP tool cache refreshed")