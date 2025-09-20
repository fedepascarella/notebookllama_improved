"""
MCP Management UI Components for Streamlit
Provides user interface for managing MCP server connections and configurations
"""

import streamlit as st
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from .mcp_client import MCPClientManager, MCPConfig, MCPToolProxy
    from .mcp_enhanced_workflow_v2 import MCPEnhancedWorkflowV2, create_mcp_enhanced_workflow_v2
except ImportError:
    # Fallback for when running standalone
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from mcp_client import MCPClientManager, MCPConfig, MCPToolProxy
    from mcp_enhanced_workflow_v2 import MCPEnhancedWorkflowV2, create_mcp_enhanced_workflow_v2

logger = logging.getLogger(__name__)

class MCPUIManager:
    """Manages MCP UI components and state"""

    def __init__(self):
        self.config = None
        self.client = None
        self.proxy = None
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables for MCP UI"""
        if 'mcp_config' not in st.session_state:
            st.session_state.mcp_config = None

        if 'mcp_client' not in st.session_state:
            st.session_state.mcp_client = None

        if 'mcp_connection_status' not in st.session_state:
            st.session_state.mcp_connection_status = {}

        if 'mcp_available_tools' not in st.session_state:
            st.session_state.mcp_available_tools = {}

        if 'mcp_health_status' not in st.session_state:
            st.session_state.mcp_health_status = {}

        if 'mcp_enable_integration' not in st.session_state:
            st.session_state.mcp_enable_integration = True

        if 'mcp_enabled' not in st.session_state:
            st.session_state.mcp_enabled = st.session_state.mcp_enable_integration

        if 'mcp_last_refresh' not in st.session_state:
            st.session_state.mcp_last_refresh = None

    def render_mcp_sidebar(self):
        """Render MCP management section in sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔌 **MCP Integration**")

        # MCP enable/disable toggle
        enable_mcp = st.sidebar.checkbox(
            "Enable MCP Integration",
            value=st.session_state.mcp_enable_integration,
            help="Enable Model Context Protocol server integration"
        )
        st.session_state.mcp_enable_integration = enable_mcp

        if enable_mcp:
            # Connection status indicator
            if st.session_state.mcp_health_status:
                status = st.session_state.mcp_health_status.get("overall_status", "unknown")
                if status == "healthy":
                    st.sidebar.success("🟢 MCP Connected")
                elif status == "degraded":
                    st.sidebar.warning("🟡 MCP Partially Connected")
                else:
                    st.sidebar.error("🔴 MCP Disconnected")
            else:
                st.sidebar.info("⚪ MCP Not Initialized")

            # Quick actions
            if st.sidebar.button("🔄 Refresh MCP", key="mcp_refresh_sidebar"):
                asyncio.run(self.refresh_mcp_status())

            # Show basic stats
            if st.session_state.mcp_health_status:
                total_tools = st.session_state.mcp_health_status.get("total_tools", 0)
                servers = st.session_state.mcp_health_status.get("servers", {})
                connected_servers = sum(1 for server in servers.values() if server.get("connected", False))

                st.sidebar.metric("Connected Servers", f"{connected_servers}/{len(servers)}")
                st.sidebar.metric("Available Tools", total_tools)

        else:
            st.sidebar.info("MCP Integration disabled")

    def render_mcp_management_tab(self):
        """Render complete MCP management interface as a tab"""
        st.header("🔌 MCP Server Management")
        st.markdown("Manage Model Context Protocol server connections and configurations")

        # Main MCP management interface
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.subheader("Server Status")

        with col2:
            if st.button("🔄 Refresh Status", key="mcp_refresh_main"):
                with st.spinner("Refreshing MCP status..."):
                    asyncio.run(self.refresh_mcp_status())
                st.rerun()

        with col3:
            if st.button("⚡ Test Connections", key="mcp_test_connections"):
                with st.spinner("Testing MCP connections..."):
                    asyncio.run(self.test_all_connections())

        # Configuration section
        st.markdown("---")
        self._render_server_configuration()

        # Connection status section
        st.markdown("---")
        self._render_connection_status()

        # Tools and capabilities section
        st.markdown("---")
        self._render_tools_section()

        # Advanced settings
        st.markdown("---")
        self._render_advanced_settings()

    def _render_server_configuration(self):
        """Render server configuration section"""
        st.subheader("🛠️ Server Configuration")

        # Load current configuration
        try:
            config = MCPConfig("mcp_config.json")
            servers = config.servers.get("servers", {})

            if not servers:
                st.warning("No MCP servers configured")
                return

            # Display each server configuration
            for server_name, server_config in servers.items():
                with st.expander(f"🖥️ {server_name.title()} Server", expanded=False):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**Description:** {server_config.get('description', 'No description')}")
                        st.markdown(f"**Command:** `{server_config.get('command', 'N/A')}`")

                        args = server_config.get('args', [])
                        if args:
                            st.markdown(f"**Arguments:** `{' '.join(args)}`")

                        capabilities = server_config.get('capabilities', [])
                        if capabilities:
                            st.markdown("**Capabilities:**")
                            for cap in capabilities:
                                st.markdown(f"  • {cap}")

                    with col2:
                        # Enable/disable toggle
                        current_enabled = server_config.get('enabled', False)
                        enabled = st.checkbox(
                            "Enabled",
                            value=current_enabled,
                            key=f"enable_{server_name}"
                        )

                        if enabled != current_enabled:
                            if enabled:
                                config.enable_server(server_name)
                                st.success(f"✅ {server_name} enabled")
                            else:
                                config.disable_server(server_name)
                                st.info(f"ℹ️ {server_name} disabled")
                            st.rerun()

        except Exception as e:
            st.error(f"Error loading server configuration: {str(e)}")

    def _render_connection_status(self):
        """Render connection status section"""
        st.subheader("🔌 Connection Status")

        if not st.session_state.mcp_health_status:
            st.info("Click 'Refresh Status' to check MCP server connections")
            return

        health = st.session_state.mcp_health_status
        servers = health.get("servers", {})

        if not servers:
            st.warning("No server status information available")
            return

        # Overall status
        overall_status = health.get("overall_status", "unknown")
        status_colors = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴",
            "unknown": "⚪"
        }

        st.markdown(f"**Overall Status:** {status_colors.get(overall_status, '⚪')} {overall_status.title()}")

        # Individual server status
        for server_name, server_info in servers.items():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    st.markdown(f"**{server_name.title()}**")

                with col2:
                    connected = server_info.get("connected", False)
                    status_icon = "🟢" if connected else "🔴"
                    st.markdown(f"{status_icon} {'Connected' if connected else 'Disconnected'}")

                with col3:
                    responsive = server_info.get("responsive", False)
                    resp_icon = "✅" if responsive else "❌"
                    st.markdown(f"{resp_icon} {'Responsive' if responsive else 'Unresponsive'}")

                with col4:
                    tools_count = server_info.get("tools_count", 0)
                    st.markdown(f"🔧 {tools_count} tools")

        # Show errors if any
        errors = health.get("errors", [])
        if errors:
            st.warning("**Connection Errors:**")
            for error in errors:
                st.markdown(f"• {error}")

        # Last updated
        if st.session_state.mcp_last_refresh:
            st.caption(f"Last updated: {st.session_state.mcp_last_refresh}")

    def _render_tools_section(self):
        """Render available tools section"""
        st.subheader("🔧 Available Tools")

        if not st.session_state.mcp_available_tools:
            st.info("No tools information available. Refresh status to load tools.")
            return

        tools = st.session_state.mcp_available_tools

        for server_name, server_tools in tools.items():
            if server_tools:
                with st.expander(f"🖥️ {server_name.title()} Tools ({len(server_tools)} available)"):
                    for tool in server_tools:
                        tool_name = getattr(tool, 'name', 'Unknown Tool')
                        tool_desc = getattr(tool, 'description', 'No description available')

                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.markdown(f"**{tool_name}**")
                        with col2:
                            st.markdown(tool_desc)

    def _render_advanced_settings(self):
        """Render advanced MCP settings"""
        with st.expander("⚙️ Advanced Settings", expanded=False):
            st.subheader("Advanced MCP Configuration")

            # Workflow integration settings
            st.markdown("**Workflow Integration**")
            enable_workflow = st.checkbox(
                "Enable MCP Enhanced Workflow",
                value=True,
                help="Use MCP enhancements in document processing workflow"
            )

            # Timeout settings
            st.markdown("**Connection Settings**")
            timeout = st.number_input(
                "Connection Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=60,
                help="Timeout for MCP server connections"
            )

            # Debug settings
            st.markdown("**Debug Options**")
            debug_mode = st.checkbox(
                "Enable Debug Logging",
                value=False,
                help="Enable detailed logging for MCP operations"
            )

            # Configuration export/import
            st.markdown("**Configuration Management**")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📤 Export Config"):
                    try:
                        config = MCPConfig("mcp_config.json")
                        config_json = json.dumps(config.servers, indent=2)
                        st.download_button(
                            label="Download mcp_config.json",
                            data=config_json,
                            file_name="mcp_config.json",
                            mime="application/json"
                        )
                    except Exception as e:
                        st.error(f"Error exporting config: {str(e)}")

            with col2:
                uploaded_config = st.file_uploader(
                    "📥 Import Config",
                    type="json",
                    help="Upload MCP configuration file"
                )

                if uploaded_config is not None:
                    try:
                        config_data = json.load(uploaded_config)
                        # Validate and save configuration
                        st.success("Configuration imported successfully!")
                    except Exception as e:
                        st.error(f"Error importing config: {str(e)}")

    async def refresh_mcp_status(self):
        """Refresh MCP connection status and available tools"""
        try:
            # Initialize MCP client
            client = MCPClientManager("mcp_config.json")
            proxy = MCPToolProxy(client)

            # Initialize connections
            await proxy.initialize()

            # Get health status
            health_status = await proxy.health_check()
            st.session_state.mcp_health_status = health_status

            # Get connection status
            connection_status = client.get_connection_status()
            st.session_state.mcp_connection_status = connection_status

            # Get available tools
            available_tools = await client.list_all_tools()
            st.session_state.mcp_available_tools = available_tools

            # Update last refresh time
            st.session_state.mcp_last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Store client instances
            st.session_state.mcp_client = client
            st.session_state.mcp_proxy = proxy

            logger.info("MCP status refreshed successfully")

        except Exception as e:
            logger.error(f"Error refreshing MCP status: {e}")
            st.error(f"Failed to refresh MCP status: {str(e)}")

    async def test_all_connections(self):
        """Test all MCP server connections"""
        try:
            if not st.session_state.mcp_proxy:
                await self.refresh_mcp_status()

            proxy = st.session_state.mcp_proxy
            if proxy:
                # Perform comprehensive health check
                health = await proxy.health_check()

                # Show test results
                st.success("✅ Connection test completed!")

                # Display detailed results
                servers = health.get("servers", {})
                for server_name, server_info in servers.items():
                    connected = server_info.get("connected", False)
                    responsive = server_info.get("responsive", False)

                    if connected and responsive:
                        st.success(f"✅ {server_name}: Connected and responsive")
                    elif connected:
                        st.warning(f"⚠️ {server_name}: Connected but not responsive")
                    else:
                        st.error(f"❌ {server_name}: Connection failed")

            else:
                st.error("MCP proxy not available for testing")

        except Exception as e:
            logger.error(f"Error testing MCP connections: {e}")
            st.error(f"Connection test failed: {str(e)}")

# ====================================
# CONVENIENCE FUNCTIONS
# ====================================

def render_mcp_sidebar():
    """Convenience function to render MCP sidebar"""
    ui_manager = MCPUIManager()
    ui_manager.render_mcp_sidebar()

def render_mcp_management_tab():
    """Convenience function to render MCP management tab"""
    ui_manager = MCPUIManager()
    ui_manager.render_mcp_management_tab()

def get_mcp_enhanced_workflow():
    """Get MCP enhanced workflow v2 with current settings"""
    enable_mcp = st.session_state.get('mcp_enable_integration', True)
    return create_mcp_enhanced_workflow_v2(enable_mcp=enable_mcp, timeout=300, verbose=True)

def is_mcp_enabled():
    """Check if MCP integration is enabled"""
    return st.session_state.get('mcp_enable_integration', True)

def get_mcp_status():
    """Get current MCP status information"""
    return {
        "enabled": is_mcp_enabled(),
        "health": st.session_state.get('mcp_health_status', {}),
        "connections": st.session_state.get('mcp_connection_status', {}),
        "tools": st.session_state.get('mcp_available_tools', {}),
        "last_refresh": st.session_state.get('mcp_last_refresh', None)
    }