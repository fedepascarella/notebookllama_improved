"""
MCP Client Module for NotebookLlama
Provides integration with Model Context Protocol servers
"""

from .client import MCPClientManager
from .config import MCPConfig
from .tool_proxy import MCPToolProxy

__all__ = [
    "MCPClientManager",
    "MCPConfig",
    "MCPToolProxy"
]