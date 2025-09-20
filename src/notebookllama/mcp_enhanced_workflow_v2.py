"""
MCP Enhanced Workflow V2 Module - NotebookLLaMA Enhanced
Integrates MCP client capabilities with the enhanced workflow v2 system
"""

import asyncio
import logging
import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from llama_index.core.workflow import Workflow, step, Context
from llama_index.core.workflow.events import StartEvent, StopEvent

# Import the V2 workflow and its components
from .enhanced_workflow_v2 import EnhancedWorkflowV2
from .workflow_events import (
    DocumentProcessedEvent,
    ContentEnhancedEvent,
    NotebookReadyEvent,
    WorkflowErrorEvent,
    create_document_processed_event,
    create_content_enhanced_event
)
from .content_enhancer import ContentEnhancer, create_content_enhancer
from .mind_map_generator import MindMapGenerator, create_mind_map_generator
from .fixed_docling_processor import DoclingProcessor, create_docling_processor

# Import MCP client components
from .mcp_client import MCPClientManager, MCPToolProxy

logger = logging.getLogger(__name__)


class MCPEnhancedWorkflowV2(EnhancedWorkflowV2):
    """
    MCP Enhanced Workflow V2 for NotebookLLaMA
    Extends the enhanced workflow v2 with MCP server integration capabilities

    This properly integrates with:
    - Docling document processing (preserves all content)
    - OpenAI content enhancement (generates summaries, Q&A)
    - MCP server capabilities (filesystem, memory, database)
    """

    def __init__(self, enable_mcp: bool = True, **kwargs):
        """
        Initialize MCP Enhanced Workflow V2

        Args:
            enable_mcp: Whether to enable MCP integration
            **kwargs: Additional arguments for parent workflow
        """
        super().__init__(**kwargs)
        self.enable_mcp = enable_mcp
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # MCP components
        self.mcp_client = None
        self.mcp_proxy = None
        self._mcp_initialized = False
        self._mcp_available_tools = {}

        if self.enable_mcp:
            self._init_mcp_services()

    def _init_mcp_services(self) -> None:
        """Initialize MCP services"""
        try:
            # Initialize MCP client manager
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_config.json')
            if os.path.exists(config_path):
                self.mcp_client = MCPClientManager(config_path)
                self.mcp_proxy = MCPToolProxy(self.mcp_client)
                self.logger.info("MCP services initialized")
            else:
                self.logger.warning(f"MCP config not found at {config_path}, MCP features disabled")
                self.enable_mcp = False
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP services: {e}")
            self.enable_mcp = False

    async def _initialize_mcp_connections(self) -> None:
        """Initialize MCP connections and cache available tools"""
        if not self.enable_mcp or self._mcp_initialized:
            return

        try:
            self.logger.info("Initializing MCP connections...")
            await self.mcp_proxy.initialize()

            # Get available tools
            self._mcp_available_tools = await self.mcp_proxy.get_tool_capabilities()

            # Perform health check
            health = await self.mcp_proxy.health_check()
            self.logger.info(f"MCP Health Status: {health['overall_status']}")
            self.logger.info(f"Available tools: {health['total_tools']} from {len(health['servers'])} servers")

            self._mcp_initialized = True

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP connections: {e}")
            self.enable_mcp = False

    @step
    async def process_document(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> DocumentProcessedEvent:
        """
        Step 1: Process document with Docling + MCP enhancements
        Preserves ALL content and adds MCP metadata
        """
        # Initialize MCP if needed
        if self.enable_mcp and not self._mcp_initialized:
            await self._initialize_mcp_connections()

        # Run parent's document processing first
        document_event = await super().process_document(ctx, ev)

        # If MCP is enabled, add MCP enhancements
        if self.enable_mcp and self._mcp_initialized:
            try:
                file_path = getattr(ev, 'file_path', None)
                if file_path:
                    # Add MCP filesystem metadata
                    mcp_metadata = await self._get_mcp_file_metadata(file_path)
                    document_event.metadata.update(mcp_metadata)

                    # Store document in MCP memory if available
                    if "memory" in self._mcp_available_tools:
                        await self._store_in_mcp_memory(
                            document_event.title,
                            document_event.raw_content[:5000],  # Store first 5000 chars
                            document_event.metadata
                        )

                    self.logger.info("Added MCP enhancements to document processing")
            except Exception as e:
                self.logger.error(f"MCP enhancement failed: {e}")
                # Continue without MCP enhancements

        return document_event

    @step
    async def enhance_content(
        self,
        ctx: Context,
        ev: DocumentProcessedEvent
    ) -> ContentEnhancedEvent:
        """
        Step 2: Enhance content with LLM + MCP capabilities
        Generates real summaries, Q&A, topics, and adds MCP insights
        """
        # Run parent's content enhancement first
        enhanced_event = await super().enhance_content(ctx, ev)

        # If MCP is enabled, add MCP-based enhancements
        if self.enable_mcp and self._mcp_initialized:
            try:
                # Find similar documents using MCP memory
                if "memory" in self._mcp_available_tools:
                    similar_docs = await self._find_similar_documents(
                        enhanced_event.summary,
                        enhanced_event.topics
                    )
                    enhanced_event.enhancement_metadata["similar_documents"] = similar_docs

                    # Create knowledge graph relationships
                    await self._create_knowledge_graph_relationships(
                        ev.title,
                        enhanced_event.topics,
                        enhanced_event.key_points
                    )

                # Add database insights if available
                if "postgres" in self._mcp_available_tools:
                    db_insights = await self._get_database_insights(ev.title)
                    enhanced_event.enhancement_metadata["db_insights"] = db_insights

                self.logger.info("Added MCP enhancements to content")

            except Exception as e:
                self.logger.error(f"MCP content enhancement failed: {e}")
                # Continue without MCP enhancements

        return enhanced_event

    @step
    async def generate_notebook(
        self,
        ctx: Context,
        ev: ContentEnhancedEvent
    ) -> NotebookReadyEvent:
        """
        Step 3: Generate final notebook with mind map + MCP insights
        Creates complete notebook structure with MCP-enhanced content
        """
        # Run parent's notebook generation
        notebook_event = await super().generate_notebook(ctx, ev)

        # If MCP is enabled, add MCP status to notebook
        if self.enable_mcp and self._mcp_initialized:
            try:
                # Add MCP status section to formatted summary
                mcp_status = await self._get_mcp_status_summary()
                if mcp_status:
                    notebook_event.formatted_summary += f"\n\n## MCP Integration Status\n\n{mcp_status}"

                # Add similar documents section if found
                similar_docs = ev.enhancement_metadata.get("similar_documents", [])
                if similar_docs:
                    similar_section = "\n\n## Similar Documents Found\n\n"
                    for doc in similar_docs[:3]:  # Limit to top 3
                        similar_section += f"- {doc}\n"
                    notebook_event.formatted_highlights += similar_section

                self.logger.info("Added MCP insights to notebook")

            except Exception as e:
                self.logger.error(f"MCP notebook enhancement failed: {e}")
                # Continue without MCP enhancements

        return notebook_event

    # MCP Helper Methods

    async def _get_mcp_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata using MCP filesystem tools"""
        metadata = {"mcp_file_metadata": {}}

        try:
            if "filesystem" in self._mcp_available_tools:
                # Get file info
                file_info = await self.mcp_proxy.mcp_client.call_tool(
                    "filesystem",
                    "read_file",
                    {"path": file_path}
                )

                # Get related files in directory
                dir_path = os.path.dirname(file_path)
                related_files = await self.mcp_proxy.mcp_client.call_tool(
                    "filesystem",
                    "list_directory",
                    {"path": dir_path}
                )

                metadata["mcp_file_metadata"] = {
                    "file_accessible": file_info is not None,
                    "related_files": related_files[:5] if related_files else []
                }

        except Exception as e:
            self.logger.error(f"Failed to get MCP file metadata: {e}")

        return metadata

    async def _store_in_mcp_memory(self, title: str, content: str, metadata: Dict) -> None:
        """Store document in MCP memory server"""
        try:
            await self.mcp_proxy.mcp_client.call_tool(
                "memory",
                "create_entities",
                {
                    "entities": [{
                        "name": title,
                        "entityType": "document",
                        "observations": [content[:1000]]  # Store first 1000 chars
                    }]
                }
            )
            self.logger.info(f"Stored document '{title}' in MCP memory")
        except Exception as e:
            self.logger.error(f"Failed to store in MCP memory: {e}")

    async def _find_similar_documents(self, summary: str, topics: List[str]) -> List[str]:
        """Find similar documents using MCP memory"""
        similar = []

        try:
            # Search by topics
            for topic in topics[:3]:  # Search top 3 topics
                results = await self.mcp_proxy.mcp_client.call_tool(
                    "memory",
                    "search_entities",
                    {"query": topic}
                )
                if results:
                    similar.extend([r.get("name", "") for r in results[:2]])

            # Remove duplicates
            similar = list(set(similar))

        except Exception as e:
            self.logger.error(f"Failed to find similar documents: {e}")

        return similar[:5]  # Return top 5

    async def _create_knowledge_graph_relationships(
        self,
        title: str,
        topics: List[str],
        key_points: List[str]
    ) -> None:
        """Create knowledge graph relationships in MCP memory"""
        try:
            relations = []

            # Create topic relationships
            for topic in topics:
                relations.append({
                    "from": title,
                    "to": topic,
                    "relationType": "has_topic"
                })

            # Create key point relationships
            for point in key_points[:3]:  # Limit to avoid too many relations
                relations.append({
                    "from": title,
                    "to": point[:50],  # Truncate long points
                    "relationType": "key_point"
                })

            if relations:
                await self.mcp_proxy.mcp_client.call_tool(
                    "memory",
                    "create_relations",
                    {"relations": relations[:10]}  # Limit total relations
                )
                self.logger.info(f"Created {len(relations)} knowledge graph relationships")

        except Exception as e:
            self.logger.error(f"Failed to create knowledge graph: {e}")

    async def _get_database_insights(self, title: str) -> Dict[str, Any]:
        """Get database insights using MCP PostgreSQL tools"""
        insights = {}

        try:
            # Query for document statistics
            result = await self.mcp_proxy.mcp_client.call_tool(
                "postgres",
                "query",
                {
                    "query": "SELECT COUNT(*) as total_docs FROM documents",
                    "params": []
                }
            )

            if result:
                insights["total_documents"] = result.get("rows", [[0]])[0][0]

        except Exception as e:
            self.logger.error(f"Failed to get database insights: {e}")

        return insights

    async def _get_mcp_status_summary(self) -> str:
        """Get MCP status summary for display"""
        try:
            health = await self.mcp_proxy.health_check()

            status = []
            status.append(f"- **Status**: {health['overall_status']}")
            status.append(f"- **Active Servers**: {len(health['servers'])}")
            status.append(f"- **Available Tools**: {health['total_tools']}")

            # Add server details
            for server in health['servers'][:3]:  # Limit to 3 servers
                if server['status'] == 'healthy':
                    status.append(f"- **{server['name']}**: ✅ Connected")
                else:
                    status.append(f"- **{server['name']}**: ❌ {server.get('error', 'Disconnected')}")

            return "\n".join(status)

        except Exception as e:
            self.logger.error(f"Failed to get MCP status: {e}")
            return "MCP status unavailable"

    async def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP integration status"""
        if not self._mcp_initialized:
            return {
                "status": "not_initialized",
                "enabled": self.enable_mcp,
                "message": "MCP integration has not been initialized"
            }

        try:
            health = await self.mcp_proxy.health_check()
            return {
                "status": "active",
                "enabled": self.enable_mcp,
                "initialized": self._mcp_initialized,
                "health": health,
                "available_servers": list(self._mcp_available_tools.keys()),
                "total_tools": sum(len(tools) for tools in self._mcp_available_tools.values())
            }
        except Exception as e:
            return {
                "status": "error",
                "enabled": self.enable_mcp,
                "error": str(e)
            }


# Factory functions

def create_mcp_enhanced_workflow_v2(enable_mcp: bool = True, **kwargs) -> MCPEnhancedWorkflowV2:
    """
    Create MCP enhanced workflow v2 with proper configuration

    Args:
        enable_mcp: Whether to enable MCP integration
        **kwargs: Additional workflow parameters

    Returns:
        MCPEnhancedWorkflowV2 instance
    """
    return MCPEnhancedWorkflowV2(enable_mcp=enable_mcp, **kwargs)


async def run_mcp_enhanced_workflow_v2(
    file_path: str,
    document_title: str,
    enable_mcp: bool = True
) -> Dict[str, Any]:
    """
    Run the MCP enhanced workflow v2 asynchronously
    Designed for Streamlit integration with proper error handling

    Args:
        file_path: Path to the document file
        document_title: Title of the document
        enable_mcp: Whether to enable MCP integration

    Returns:
        Dictionary containing processing results
    """
    logger.info(f"Starting MCP enhanced workflow v2 for: {document_title}")

    try:
        # Create and run workflow
        workflow = create_mcp_enhanced_workflow_v2(
            enable_mcp=enable_mcp,
            timeout=300,
            verbose=True
        )

        # Create StartEvent with file information
        start_event = StartEvent()
        start_event.file_path = file_path
        start_event.document_title = document_title

        # Run workflow
        result = await workflow.run(start_event=start_event)

        logger.info("MCP enhanced workflow v2 completed successfully")

        # Add MCP status to result if enabled
        if enable_mcp:
            mcp_status = await workflow.get_mcp_status()
            result["mcp_status"] = mcp_status

        return result

    except asyncio.TimeoutError:
        logger.error("Workflow timed out")
        return {
            "status": "timeout",
            "error": "Processing timed out - document may be too large or complex",
            "summary": "Processing was interrupted due to timeout. Please try with a smaller document.",
            "q_and_a": "**Why did processing timeout?**\n\nThe document may be very large or complex. Try breaking it into smaller sections.",
            "bullet_points": "## Timeout Information\n\n- Status: ⏱️ Timed out\n- Suggestion: Try smaller documents\n- Content: Not fully processed",
            "mcp_status": {"status": "timeout", "enabled": enable_mcp}
        }

    except Exception as e:
        logger.error(f"Workflow failed with exception: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "summary": "Document processing failed due to a technical error. Please try again or contact support.",
            "q_and_a": "**What went wrong?**\n\nA technical error occurred during processing. The system has logged the issue for investigation.",
            "bullet_points": "## Error Information\n\n- Status: ❌ Failed\n- Action: Try again or contact support\n- Details: Error logged for investigation",
            "mcp_status": {"status": "error", "enabled": enable_mcp, "error": str(e)}
        }