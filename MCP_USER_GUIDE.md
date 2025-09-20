# MCP (Model Context Protocol) User Guide for NotebookLlama

## Table of Contents
1. [Overview](#overview)
2. [How MCP Works in NotebookLlama](#how-mcp-works)
3. [Available MCP Servers](#available-servers)
4. [Using the MCP Interface](#using-the-interface)
5. [Adding New Servers](#adding-servers)
6. [Tool Usage Examples](#tool-examples)
7. [Troubleshooting](#troubleshooting)

## Overview <a name="overview"></a>

MCP (Model Context Protocol) enhances NotebookLlama by connecting to external servers that provide specialized tools for document processing, knowledge management, and data operations.

### Key Benefits:
- 📁 **File System Access**: Read/write files, search directories
- 🧠 **Knowledge Graph**: Store and retrieve document relationships
- 🗄️ **Database Integration**: Query and store data in PostgreSQL
- 🌐 **Web Access**: Fetch and process web content
- 🔗 **Cross-Document Intelligence**: Find similar documents and build connections

## How MCP Works in NotebookLlama <a name="how-mcp-works"></a>

### Workflow Integration

When you upload a document with MCP enabled:

1. **Document Processing Phase**
   - Docling extracts content from your PDF
   - MCP stores document metadata in filesystem
   - Document is added to knowledge graph

2. **Content Enhancement Phase**
   - OpenAI generates summaries and Q&A
   - MCP searches for similar documents
   - Creates topic relationships in knowledge graph

3. **Output Generation Phase**
   - Mind map is created with connections
   - MCP insights are added to the summary
   - Similar documents are listed

### Automatic Tool Triggering

MCP tools are triggered automatically during workflow:

```
Document Upload
    ↓
[filesystem.read_file] → Get file metadata
    ↓
[memory.create_entities] → Store in knowledge graph
    ↓
[memory.search_entities] → Find similar documents
    ↓
[memory.create_relations] → Build topic network
```

## Available MCP Servers <a name="available-servers"></a>

### 1. Filesystem Server
**Purpose**: File and directory operations

**Tools**:
- `read_file`: Read file contents
- `write_file`: Write content to files
- `list_directory`: List directory contents
- `search_files`: Search for files by pattern

**Use Cases**:
- Access related documents
- Save processing results
- Manage document collections

### 2. Memory Server
**Purpose**: Knowledge graph and memory management

**Tools**:
- `create_entities`: Add documents/concepts to graph
- `search_entities`: Find related information
- `create_relations`: Link related concepts

**Use Cases**:
- Build document relationships
- Find similar content
- Create knowledge networks

### 3. PostgreSQL Server
**Purpose**: Database operations

**Tools**:
- `query`: Execute SQL queries
- `insert`: Add data to tables
- `update`: Modify existing data
- `delete`: Remove data

**Use Cases**:
- Store document metadata
- Query historical data
- Advanced analytics

### 4. GitHub Server (Optional)
**Purpose**: Repository access

**Tools**:
- `search_repos`: Search repositories
- `get_file`: Retrieve file contents
- `list_issues`: Get repository issues

### 5. Web Server (Optional)
**Purpose**: Web content access

**Tools**:
- `fetch_url`: Get web page content
- `search`: Web search
- `extract_content`: Parse web content

## Using the MCP Interface <a name="using-the-interface"></a>

### Accessing MCP Features

1. **Open NotebookLlama** and upload a document
2. **Click the MCP Tab** after processing
3. **View the Dashboard** to see server status

### Dashboard Overview

The MCP dashboard shows:
- **System Status**: Overall health of MCP system
- **Server Cards**: Individual server status
- **Available Tools**: Count of accessible tools
- **Recent Activity**: Last operations performed

### Testing Connections

To test a server connection:
1. Go to the **Servers** tab
2. Select a server
3. Click **Test Connection**
4. View the result (success/failure)

### Executing Tools

To manually execute a tool:
1. Go to the **Tools** tab
2. Select a tool from the dropdown
3. Enter required parameters
4. Click **Execute**
5. View the results

## Adding New Servers <a name="adding-servers"></a>

### Method 1: Quick Templates

1. Go to the **Add Server** tab
2. Click a template button (Filesystem, Memory, GitHub, Web)
3. Customize the configuration
4. Click **Add Server**

### Method 2: Custom Server

1. Go to the **Add Server** tab
2. Fill in the custom server form:
   - **Server Name**: Unique identifier
   - **Description**: What it does
   - **Command**: How to run it (npx, python, etc.)
   - **Arguments**: Command line arguments
   - **Capabilities**: Available tools
3. Click **Add Server**

### Method 3: Edit JSON

Edit `mcp_config.json` directly:

```json
{
  "servers": {
    "my-custom-server": {
      "command": "python",
      "args": ["my_server.py"],
      "enabled": true,
      "description": "My custom MCP server",
      "capabilities": ["tool1", "tool2"]
    }
  }
}
```

## Tool Usage Examples <a name="tool-examples"></a>

### Example 1: Finding Related Documents

When processing a document about "Machine Learning":
1. MCP automatically searches for similar documents
2. Creates relationships between topics
3. Shows related documents in the output

### Example 2: Building Knowledge Networks

For a research paper:
1. Entities are created for key concepts
2. Relations link related ideas
3. Knowledge graph grows with each document

### Example 3: Cross-Reference Information

When analyzing multiple PDFs:
1. MCP tracks all processed documents
2. Identifies common themes
3. Suggests connections between documents

## Troubleshooting <a name="troubleshooting"></a>

### Common Issues

#### MCP Tab Not Showing Content
- **Solution**: Refresh the page and ensure MCP is enabled in sidebar

#### Server Connection Failed
- **Check**: Server command is installed (e.g., `npm install -g @modelcontextprotocol/server-filesystem`)
- **Verify**: Arguments are correct in configuration
- **Test**: Run the command manually in terminal

#### Tools Not Working
- **Enable**: Ensure server is enabled in configuration
- **Refresh**: Click "Refresh All" to reconnect
- **Logs**: Check browser console for errors

### Installation Requirements

For MCP servers to work, you need:

1. **Node.js** installed for NPX-based servers
2. **Python** for Python-based servers
3. **Network access** for web-based servers

Install MCP servers:
```bash
# Filesystem server
npm install -g @modelcontextprotocol/server-filesystem

# Memory server
npm install -g @modelcontextprotocol/server-memory

# Other servers
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-web
```

### Debugging Tips

1. **Check Status**: Use dashboard to verify server status
2. **Test Tools**: Use Tools tab to test individual tools
3. **View Logs**: Check Settings > Log Level = DEBUG
4. **Manual Test**: Run server commands in terminal

## Advanced Configuration

### Global Settings

In the **Settings** tab, configure:
- **Connection Timeout**: How long to wait for servers
- **Retry Attempts**: Number of connection retries
- **Log Level**: Verbosity of logging
- **Auto-connect**: Connect on startup

### Import/Export Configuration

- **Export**: Download your `mcp_config.json`
- **Import**: Upload a saved configuration
- **Share**: Exchange configurations with team

## Best Practices

1. **Start Simple**: Begin with filesystem and memory servers
2. **Test First**: Always test connections before processing
3. **Monitor Status**: Check dashboard regularly
4. **Document Relations**: Use meaningful entity names
5. **Backup Config**: Export configuration regularly

## Support

For MCP-related issues:
1. Check this guide first
2. Review the [MCP Implementation Plan](MCP_IMPLEMENTATION_PLAN.md)
3. Check server documentation
4. Report issues on GitHub

---

## Quick Start Checklist

- [ ] MCP enabled in sidebar
- [ ] At least one server configured
- [ ] Server connection tested
- [ ] Document uploaded for processing
- [ ] MCP tab checked after processing
- [ ] Results include MCP enhancements