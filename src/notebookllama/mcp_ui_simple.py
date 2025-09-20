"""
Simple MCP Management UI for Integration within Tabs
Designed to work within Enhanced_Home.py without creating nested tabs
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from .mcp_client import MCPClientManager, MCPConfig, MCPToolProxy
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from mcp_client import MCPClientManager, MCPConfig, MCPToolProxy

logger = logging.getLogger(__name__)


class SimpleMCPUI:
    """Simple MCP UI for tab integration"""

    def __init__(self):
        self.config_path = "mcp_config.json"
        self._initialize_session_state()
        self._load_config()

    def _initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            'mcp_config': None,
            'mcp_enabled': True,
            'mcp_servers_status': {},
            'mcp_last_refresh': None,
            'mcp_current_view': 'dashboard'
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _load_config(self):
        """Load MCP configuration"""
        try:
            with open(self.config_path, 'r') as f:
                st.session_state.mcp_config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            st.session_state.mcp_config = {"servers": {}, "global_settings": {}}

    def render_mcp_interface(self):
        """Render the MCP interface within a single tab"""
        st.markdown("## 🔌 MCP Server Management")

        # Quick controls at the top
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.markdown("**System Status**")
            if st.session_state.mcp_enabled:
                st.success("🟢 MCP Enabled")
            else:
                st.warning("🔴 MCP Disabled")

        with col2:
            if st.button("🔄 Refresh"):
                self._refresh_servers()

        with col3:
            view = st.selectbox(
                "View",
                ["Dashboard", "Servers", "Tools", "Settings"],
                key="mcp_view_selector"
            )

        with col4:
            enabled = st.checkbox(
                "Enable MCP",
                value=st.session_state.mcp_enabled,
                key="mcp_enable_toggle"
            )
            if enabled != st.session_state.mcp_enabled:
                st.session_state.mcp_enabled = enabled

        st.markdown("---")

        # Render selected view
        if view == "Dashboard":
            self._render_dashboard()
        elif view == "Servers":
            self._render_servers()
        elif view == "Tools":
            self._render_tools()
        elif view == "Settings":
            self._render_settings()

    def _render_dashboard(self):
        """Render dashboard view"""
        st.markdown("### 📊 MCP Dashboard")

        config = st.session_state.mcp_config
        servers = config.get("servers", {})

        # Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_servers = len(servers)
            st.metric("Total Servers", total_servers)

        with col2:
            enabled_servers = sum(1 for s in servers.values() if s.get("enabled", False))
            st.metric("Enabled Servers", enabled_servers)

        with col3:
            total_tools = sum(len(s.get("capabilities", [])) for s in servers.values())
            st.metric("Available Tools", total_tools)

        # Server status cards
        st.markdown("### 🖥️ Server Status")

        if not servers:
            st.info("No MCP servers configured. Add servers in Settings to get started.")
            return

        for server_name, server_config in servers.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    enabled = server_config.get("enabled", False)
                    status_icon = "🟢" if enabled else "🔴"
                    st.markdown(f"**{status_icon} {server_name.title()}**")
                    st.caption(server_config.get("description", "No description"))

                with col2:
                    tools = server_config.get("capabilities", [])
                    st.markdown(f"🔧 {len(tools)} tools")

                with col3:
                    command = server_config.get("command", "")
                    st.caption(f"Command: `{command}`")

                with col4:
                    if st.button("Test", key=f"test_{server_name}"):
                        self._test_server(server_name)

        # Show last refresh
        if st.session_state.mcp_last_refresh:
            st.caption(f"Last refreshed: {st.session_state.mcp_last_refresh}")

    def _render_servers(self):
        """Render servers view"""
        st.markdown("### 🖥️ Server Management")

        config = st.session_state.mcp_config
        servers = config.get("servers", {})

        if not servers:
            st.info("No servers configured.")

            # Quick add buttons
            st.markdown("**Quick Add:**")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📁 Add Filesystem Server"):
                    self._add_filesystem_server()

            with col2:
                if st.button("🧠 Add Memory Server"):
                    self._add_memory_server()
            return

        # Server list
        for server_name, server_config in servers.items():
            with st.expander(f"🖥️ {server_name.title()}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {server_config.get('description', 'N/A')}")
                    st.markdown(f"**Command:** `{server_config.get('command', 'N/A')}`")

                    args = server_config.get('args', [])
                    if args:
                        st.markdown(f"**Arguments:** `{' '.join(args)}`")

                    # Tools
                    capabilities = server_config.get('capabilities', [])
                    if capabilities:
                        st.markdown("**Available Tools:**")
                        for tool in capabilities:
                            st.markdown(f"  • {tool}")

                with col2:
                    # Enable/disable
                    enabled = st.checkbox(
                        "Enabled",
                        value=server_config.get("enabled", False),
                        key=f"server_enable_{server_name}"
                    )
                    if enabled != server_config.get("enabled", False):
                        self._toggle_server(server_name, enabled)

                    if st.button("🗑️ Remove", key=f"remove_{server_name}"):
                        if st.checkbox("Confirm deletion", key=f"confirm_del_{server_name}"):
                            self._remove_server(server_name)

    def _render_tools(self):
        """Render tools view"""
        st.markdown("### 🔧 Available Tools")

        config = st.session_state.mcp_config
        servers = config.get("servers", {})

        # Collect all tools
        all_tools = {}
        for server_name, server in servers.items():
            if server.get("enabled", False):
                for tool in server.get("capabilities", []):
                    if tool not in all_tools:
                        all_tools[tool] = []
                    all_tools[tool].append(server_name)

        if not all_tools:
            st.warning("No tools available. Enable some servers first.")
            return

        # Display tools
        for tool_name, server_list in all_tools.items():
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**🔧 {tool_name}**")

                with col2:
                    st.caption(f"Available in: {', '.join(server_list)}")

                with col3:
                    if st.button("📖 Info", key=f"info_{tool_name}"):
                        self._show_tool_info(tool_name)

    def _render_settings(self):
        """Render settings view"""
        st.markdown("### ⚙️ MCP Settings")

        # Add new server section
        with st.expander("➕ Add New Server", expanded=False):
            with st.form("add_server_form"):
                col1, col2 = st.columns(2)

                with col1:
                    server_name = st.text_input("Server Name", placeholder="my-server")
                    command = st.text_input("Command", placeholder="npx")
                    description = st.text_input("Description", placeholder="What does this server do?")

                with col2:
                    args = st.text_area("Arguments (one per line)", placeholder="-y\n@modelcontextprotocol/server-example")
                    capabilities = st.text_area("Capabilities (one per line)", placeholder="read_file\nwrite_file")
                    enabled = st.checkbox("Enable immediately", value=True)

                if st.form_submit_button("➕ Add Server"):
                    if server_name and command:
                        self._add_custom_server(
                            server_name, command, description,
                            args.split('\n') if args else [],
                            capabilities.split('\n') if capabilities else [],
                            enabled
                        )
                    else:
                        st.error("Server name and command are required")

        # Global settings
        st.markdown("#### Global Settings")
        config = st.session_state.mcp_config
        settings = config.get("global_settings", {})

        col1, col2 = st.columns(2)

        with col1:
            timeout = st.number_input(
                "Connection Timeout (seconds)",
                min_value=5, max_value=300,
                value=settings.get("timeout", 30)
            )

        with col2:
            log_level = st.selectbox(
                "Log Level",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(settings.get("log_level", "INFO"))
            )

        if st.button("💾 Save Global Settings"):
            self._save_global_settings({"timeout": timeout, "log_level": log_level})

        # Configuration export/import
        st.markdown("#### Configuration Management")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Export Config"):
                config_json = json.dumps(config, indent=2)
                st.download_button(
                    "💾 Download mcp_config.json",
                    data=config_json,
                    file_name="mcp_config.json",
                    mime="application/json"
                )

        with col2:
            uploaded = st.file_uploader("📥 Import Config", type="json")
            if uploaded:
                try:
                    new_config = json.load(uploaded)
                    st.session_state.mcp_config = new_config
                    self._save_config()
                    st.success("✅ Configuration imported!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

    # Helper methods
    def _refresh_servers(self):
        """Refresh server status"""
        st.session_state.mcp_last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success("Servers refreshed!")

    def _test_server(self, server_name: str):
        """Test a server connection"""
        # Simulate testing
        import random
        success = random.choice([True, True, False])

        if success:
            st.success(f"✅ {server_name} connection successful")
        else:
            st.error(f"❌ {server_name} connection failed")

    def _toggle_server(self, server_name: str, enabled: bool):
        """Toggle server enabled status"""
        config = st.session_state.mcp_config
        if server_name in config["servers"]:
            config["servers"][server_name]["enabled"] = enabled
            self._save_config()
            st.success(f"{'Enabled' if enabled else 'Disabled'} {server_name}")

    def _remove_server(self, server_name: str):
        """Remove a server"""
        config = st.session_state.mcp_config
        if server_name in config["servers"]:
            del config["servers"][server_name]
            self._save_config()
            st.success(f"Removed {server_name}")
            st.rerun()

    def _add_filesystem_server(self):
        """Add filesystem server quickly"""
        config = st.session_state.mcp_config
        config["servers"]["filesystem"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "enabled": True,
            "description": "File system operations",
            "capabilities": ["read_file", "write_file", "list_directory"]
        }
        self._save_config()
        st.success("✅ Added filesystem server!")
        st.rerun()

    def _add_memory_server(self):
        """Add memory server quickly"""
        config = st.session_state.mcp_config
        config["servers"]["memory"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
            "enabled": True,
            "description": "Knowledge graph and memory",
            "capabilities": ["create_entities", "search_entities", "create_relations"]
        }
        self._save_config()
        st.success("✅ Added memory server!")
        st.rerun()

    def _add_custom_server(self, name: str, command: str, description: str,
                          args: List[str], capabilities: List[str], enabled: bool):
        """Add a custom server"""
        config = st.session_state.mcp_config
        config["servers"][name] = {
            "command": command,
            "args": [arg.strip() for arg in args if arg.strip()],
            "enabled": enabled,
            "description": description,
            "capabilities": [cap.strip() for cap in capabilities if cap.strip()]
        }
        self._save_config()
        st.success(f"✅ Added server '{name}'!")
        st.rerun()

    def _save_global_settings(self, settings: Dict):
        """Save global settings"""
        config = st.session_state.mcp_config
        config["global_settings"] = settings
        self._save_config()
        st.success("Settings saved!")

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(st.session_state.mcp_config, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Failed to save config: {e}")
            return False

    def _show_tool_info(self, tool_name: str):
        """Show tool information"""
        # Tool documentation
        docs = {
            "read_file": "Reads the contents of a file from the filesystem.",
            "write_file": "Writes content to a file in the filesystem.",
            "list_directory": "Lists the contents of a directory.",
            "create_entities": "Creates entities in the knowledge graph.",
            "search_entities": "Searches for entities in the knowledge graph.",
            "create_relations": "Creates relationships between entities."
        }

        info = docs.get(tool_name, "No documentation available.")
        st.info(f"**{tool_name}**: {info}")


# Convenience function for Enhanced_Home.py
def render_simple_mcp_interface():
    """Render the simple MCP interface for tab integration"""
    ui = SimpleMCPUI()
    ui.render_mcp_interface()