"""
MCP Configuration Management
Handles MCP server configurations and settings
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MCPConfig:
    """Manages MCP server configurations"""

    def __init__(self, config_file: str = "mcp_config.json"):
        self.config_file = Path(config_file)
        self.servers = self.load_configs()

    def load_configs(self) -> Dict[str, Any]:
        """Load MCP server configurations"""
        default_config = {
            "servers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.cwd())],
                    "enabled": True,
                    "description": "File system operations and management",
                    "capabilities": ["read_file", "write_file", "list_directory", "search_files"]
                },
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "enabled": True,
                    "description": "Knowledge graph and memory management",
                    "capabilities": ["create_entities", "create_relations", "search_nodes"]
                },
                "postgres": {
                    "command": "npx",
                    "args": [
                        "-y", "enhanced-postgres-mcp-server",
                        f"postgresql://postgres:admin@localhost:5432/notebookllama_enhanced"
                    ],
                    "enabled": False,
                    "description": "PostgreSQL database operations",
                    "capabilities": ["query", "insert", "update", "delete"]
                }
            },
            "global_settings": {
                "timeout": 30,
                "retry_attempts": 3,
                "log_level": "INFO"
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all required fields exist
                    return self._merge_configs(default_config, loaded_config)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config

    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge loaded config with defaults"""
        result = default.copy()
        if "servers" in loaded:
            result["servers"].update(loaded["servers"])
        if "global_settings" in loaded:
            result["global_settings"].update(loaded["global_settings"])
        return result

    def save_config(self, config: Optional[Dict] = None):
        """Save MCP configuration to file"""
        config_to_save = config or self.servers
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            logger.info(f"MCP configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_enabled_servers(self) -> Dict[str, Dict]:
        """Get only enabled server configurations"""
        return {
            name: config
            for name, config in self.servers.get("servers", {}).items()
            if config.get("enabled", False)
        }

    def enable_server(self, server_name: str):
        """Enable a specific MCP server"""
        if server_name in self.servers.get("servers", {}):
            self.servers["servers"][server_name]["enabled"] = True
            self.save_config()
            logger.info(f"Enabled MCP server: {server_name}")
        else:
            logger.error(f"Server not found: {server_name}")

    def disable_server(self, server_name: str):
        """Disable a specific MCP server"""
        if server_name in self.servers.get("servers", {}):
            self.servers["servers"][server_name]["enabled"] = False
            self.save_config()
            logger.info(f"Disabled MCP server: {server_name}")
        else:
            logger.error(f"Server not found: {server_name}")

    def add_server(self, name: str, command: str, args: List[str],
                   description: str = "", capabilities: List[str] = None):
        """Add a new MCP server configuration"""
        new_server = {
            "command": command,
            "args": args,
            "enabled": False,
            "description": description,
            "capabilities": capabilities or []
        }

        if "servers" not in self.servers:
            self.servers["servers"] = {}

        self.servers["servers"][name] = new_server
        self.save_config()
        logger.info(f"Added new MCP server: {name}")

    def remove_server(self, server_name: str):
        """Remove a MCP server configuration"""
        if server_name in self.servers.get("servers", {}):
            del self.servers["servers"][server_name]
            self.save_config()
            logger.info(f"Removed MCP server: {server_name}")
        else:
            logger.error(f"Server not found: {server_name}")

    def get_server_config(self, server_name: str) -> Optional[Dict]:
        """Get configuration for a specific server"""
        return self.servers.get("servers", {}).get(server_name)

    def list_servers(self) -> List[str]:
        """List all configured server names"""
        return list(self.servers.get("servers", {}).keys())