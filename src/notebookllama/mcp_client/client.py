"""
MCP Client Implementation
Manages connections to MCP servers and tool execution
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool, TextContent, ImageContent
from mcp.client.stdio import stdio_client

from .config import MCPConfig

logger = logging.getLogger(__name__)

class MCPClientManager:
    """Manages multiple MCP server connections and tool execution"""

    def __init__(self, config_file: str = "mcp_config.json"):
        self.config = MCPConfig(config_file)
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, List[Tool]] = {}
        self.connection_status: Dict[str, bool] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize MCP client and connect to enabled servers"""
        if self._initialized:
            return

        logger.info("Initializing MCP Client Manager...")

        enabled_servers = self.config.get_enabled_servers()
        logger.info(f"Found {len(enabled_servers)} enabled MCP servers")

        for server_name, server_config in enabled_servers.items():
            await self.connect_to_server(server_name, server_config)

        self._initialized = True
        logger.info("MCP Client Manager initialization complete")

    async def connect_to_server(self, server_name: str, server_config: Dict) -> bool:
        """Connect to a specific MCP server"""
        try:
            logger.info(f"Connecting to MCP server: {server_name}")

            # For now, let's create a simple mock connection
            # This allows us to test the MCP client structure without requiring
            # actual MCP servers to be running
            logger.info(f"Creating mock connection for {server_name}")

            # Store mock session info
            self.sessions[server_name] = {
                "type": "mock",
                "server_config": server_config,
                "connected": True
            }
            self.connection_status[server_name] = True

            # Mock available tools based on capabilities
            mock_tools = []
            capabilities = server_config.get("capabilities", [])
            for capability in capabilities:
                mock_tool = type('MockTool', (), {
                    'name': capability,
                    'description': f"Mock {capability} tool for {server_name}"
                })()
                mock_tools.append(mock_tool)

            self.available_tools[server_name] = mock_tools

            logger.info(f"Connected to {server_name}: {len(mock_tools)} mock tools available")

            # Log available tools
            for tool in mock_tools:
                logger.debug(f"  - {tool.name}: {tool.description}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            self.connection_status[server_name] = False
            return False

    async def disconnect_from_server(self, server_name: str):
        """Disconnect from a specific MCP server"""
        if server_name in self.sessions:
            try:
                session = self.sessions[server_name]

                # Handle mock connections
                if isinstance(session, dict) and session.get("type") == "mock":
                    logger.info(f"Closing mock connection for {server_name}")
                else:
                    # Handle real connections
                    await session.close()

                del self.sessions[server_name]
                if server_name in self.available_tools:
                    del self.available_tools[server_name]
                self.connection_status[server_name] = False
                logger.info(f"Disconnected from MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool from a connected MCP server"""
        if not self._initialized:
            await self.initialize()

        if server_name not in self.sessions:
            raise ValueError(f"Not connected to server: {server_name}")

        session = self.sessions[server_name]

        try:
            logger.info(f"Calling {server_name}.{tool_name} with args: {arguments}")

            # Handle mock connections
            if isinstance(session, dict) and session.get("type") == "mock":
                logger.info(f"Mock tool call: {server_name}.{tool_name}")
                # Return mock result based on tool type
                if tool_name in ["read_file", "list_directory", "search_files"]:
                    mock_result = type('MockResult', (), {
                        'content': [type('MockContent', (), {
                            'text': f"Mock {tool_name} result for {arguments}"
                        })()]
                    })()
                    return mock_result
                else:
                    return f"Mock result for {tool_name} with args: {arguments}"

            # For real connections (when implemented)
            result = await session.call_tool(tool_name, arguments)

            logger.info(f"Tool call successful: {server_name}.{tool_name}")
            return result

        except Exception as e:
            logger.error(f"Tool call failed: {server_name}.{tool_name} - {e}")
            raise

    async def list_all_tools(self) -> Dict[str, List[Tool]]:
        """List all available tools from all connected servers"""
        if not self._initialized:
            await self.initialize()

        return self.available_tools.copy()

    async def find_tools_by_capability(self, capability: str) -> List[Dict[str, str]]:
        """Find tools that provide a specific capability"""
        matching_tools = []

        for server_name, tools in self.available_tools.items():
            for tool in tools:
                # Check if tool name or description contains the capability
                if (capability.lower() in tool.name.lower() or
                    capability.lower() in tool.description.lower()):
                    matching_tools.append({
                        "server": server_name,
                        "tool": tool.name,
                        "description": tool.description
                    })

        return matching_tools

    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all configured servers"""
        status = {}
        for server_name in self.config.list_servers():
            status[server_name] = self.connection_status.get(server_name, False)
        return status

    async def refresh_connections(self):
        """Refresh all MCP server connections"""
        logger.info("Refreshing MCP connections...")

        # Disconnect from all servers
        for server_name in list(self.sessions.keys()):
            await self.disconnect_from_server(server_name)

        # Reconnect to enabled servers
        enabled_servers = self.config.get_enabled_servers()
        for server_name, server_config in enabled_servers.items():
            await self.connect_to_server(server_name, server_config)

        logger.info("MCP connections refreshed")

    async def shutdown(self):
        """Shutdown all MCP connections"""
        logger.info("Shutting down MCP Client Manager...")

        for server_name in list(self.sessions.keys()):
            await self.disconnect_from_server(server_name)

        self._initialized = False
        logger.info("MCP Client Manager shutdown complete")

    # Helper methods for common operations
    async def read_file(self, file_path: str) -> Optional[str]:
        """Read a file using filesystem MCP server"""
        if "filesystem" in self.sessions:
            try:
                result = await self.call_tool("filesystem", "read_file", {"path": file_path})
                if result.content:
                    # Extract text content
                    for content in result.content:
                        if isinstance(content, TextContent):
                            return content.text
                return None
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return None
        else:
            logger.warning("Filesystem MCP server not available")
            return None

    async def list_directory(self, directory_path: str) -> Optional[List[str]]:
        """List directory contents using filesystem MCP server"""
        if "filesystem" in self.sessions:
            try:
                result = await self.call_tool("filesystem", "list_directory", {"path": directory_path})
                if result.content:
                    # Extract and parse directory listing
                    for content in result.content:
                        if isinstance(content, TextContent):
                            # Parse the text content to extract file names
                            # This may vary depending on the MCP server implementation
                            return content.text.split('\n')
                return []
            except Exception as e:
                logger.error(f"Failed to list directory {directory_path}: {e}")
                return None
        else:
            logger.warning("Filesystem MCP server not available")
            return None

    async def create_memory_entity(self, name: str, entityType: str, observations: List[str]) -> bool:
        """Create a memory entity using memory MCP server"""
        if "memory" in self.sessions:
            try:
                await self.call_tool("memory", "create_entities", {
                    "entities": [{
                        "name": name,
                        "entityType": entityType,
                        "observations": observations
                    }]
                })
                return True
            except Exception as e:
                logger.error(f"Failed to create memory entity {name}: {e}")
                return False
        else:
            logger.warning("Memory MCP server not available")
            return False