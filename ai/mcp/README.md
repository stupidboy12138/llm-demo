# MCP (Model Context Protocol) Demo

This directory contains a complete implementation of the Model Context Protocol (MCP), demonstrating how to build context-aware AI applications.

## Overview

MCP is a protocol for AI models to access external context through:
- **Resources**: Static or dynamic data sources (files, APIs, databases)
- **Tools**: Executable functions the model can call
- **Prompts**: Pre-defined prompt templates

## Files

- **[mcp_server.py](mcp_server.py)**: MCP server implementation with resources, tools, and prompts
- **[mcp_client.py](mcp_client.py)**: MCP client for connecting to and interacting with servers
- **[demo.py](demo.py)**: Complete demo showcasing all MCP features

## Quick Start

### Run the Complete Demo

```bash
python -m ai.mcp.demo
```

This will demonstrate:
1. Basic MCP workflow (initialization, discovery, usage)
2. Advanced scenarios (multi-step operations, batch processing)
3. Error handling

### Run Client Demo Only

```bash
python -m ai.mcp.mcp_client
```

### Run Server Only

```bash
python -m ai.mcp.mcp_server
```

## Features

### 🗂️ Resources

The server provides these built-in resources:

- **system://info** - Server information and statistics
- **file://demo.txt** - Demo text file content

### 🔧 Tools

Three built-in tools are available:

1. **read_file** - Read file content from filesystem
   ```python
   await client.call_tool("read_file", {"path": "file.txt"})
   ```

2. **write_file** - Write content to a file
   ```python
   await client.call_tool("write_file", {
       "path": "output.txt",
       "content": "Hello, World!"
   })
   ```

3. **calculate** - Evaluate mathematical expressions
   ```python
   await client.call_tool("calculate", {"expression": "2 ** 10"})
   ```

### 💭 Prompts

Two pre-defined prompt templates:

1. **code_review** - Generate code review prompts
   ```python
   await client.get_prompt("code_review", {
       "code": "def hello(): ...",
       "language": "Python"
   })
   ```

2. **summarize** - Generate text summarization prompts
   ```python
   await client.get_prompt("summarize", {
       "text": "Long text...",
       "max_length": "100 words"
   })
   ```

## Usage Example

```python
import asyncio
from ai.mcp.mcp_server import MCPServer
from ai.mcp.mcp_client import MCPClient

async def main():
    # Create server and client
    server = MCPServer()
    client = MCPClient(server)

    # Initialize connection
    await client.initialize()

    # List available resources
    resources = await client.list_resources()
    print(f"Found {len(resources)} resources")

    # Read a resource
    content = await client.read_resource("system://info")
    print(content)

    # List available tools
    tools = await client.list_tools()
    print(f"Found {len(tools)} tools")

    # Execute a tool
    result = await client.call_tool("calculate", {
        "expression": "10 + 20"
    })
    print(f"Result: {result}")

    # Get a prompt template
    prompt = await client.get_prompt("code_review", {
        "code": "def hello(): print('hi')",
        "language": "Python"
    })
    print(prompt)

asyncio.run(main())
```

## Architecture

### Server Components

```
MCPServer
├── Resources (uri → Resource)
├── Tools (name → Tool)
├── Prompts (name → Prompt)
└── Message Handler
    ├── initialize
    ├── resources/list, resources/read
    ├── tools/list, tools/call
    └── prompts/list, prompts/get
```

### Client Components

```
MCPClient
├── Connection Management
├── Message Protocol (JSON-RPC 2.0)
└── API Methods
    ├── initialize()
    ├── list_resources(), read_resource()
    ├── list_tools(), call_tool()
    └── list_prompts(), get_prompt()
```

## Protocol

The implementation follows JSON-RPC 2.0 protocol:

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "calculate",
    "arguments": {"expression": "2 + 2"}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {"type": "text", "text": "2 + 2 = 4"}
    ]
  }
}
```

## Extending the Demo

### Add Custom Resources

```python
from ai.mcp.mcp_server import MCPServer, Resource

server = MCPServer()
server.register_resource(Resource(
    uri="custom://my-resource",
    name="My Custom Resource",
    description="Description here",
    mime_type="application/json"
))
```

### Add Custom Tools

```python
from ai.mcp.mcp_server import Tool

server.register_tool(Tool(
    name="my_tool",
    description="Does something useful",
    input_schema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter"}
        },
        "required": ["param"]
    }
))

# Implement the tool handler in _handle_call_tool method
```

### Add Custom Prompts

```python
from ai.mcp.mcp_server import Prompt

server.register_prompt(Prompt(
    name="my_prompt",
    description="Custom prompt template",
    arguments=[
        {"name": "input", "description": "Input text", "required": "true"}
    ]
))

# Implement the prompt generator in _handle_get_prompt method
```

## Expected Output

When you run the demo, you'll see:

```
============================================================
  MCP COMPLETE DEMO
============================================================

This demo will showcase:
  • Basic MCP workflow
  • Advanced scenarios
  • Error handling

============================================================

============================================================
  MCP Basic Workflow Demo
============================================================

🚀 Step 1: Creating MCP Server...
   ✅ Server created: Demo MCP Server

🔌 Step 2: Creating MCP Client...
   ✅ Client created

🤝 Step 3: Initializing Connection...
   ✅ Connected to Demo MCP Server
   📋 Protocol: 2024-11-05

[... more output ...]

============================================================
          🎉 ALL DEMOS COMPLETED! 🎉
============================================================
```

## Integration with AI Models

This MCP implementation can be integrated with LLMs to provide:

1. **Context Awareness**: Models can access resources for up-to-date information
2. **Action Capabilities**: Models can execute tools to perform tasks
3. **Structured Prompting**: Models can use pre-defined prompt templates

See the LangChain and LangGraph examples in the parent directory for integration patterns.

## References

- MCP Specification: https://modelcontextprotocol.io
- JSON-RPC 2.0: https://www.jsonrpc.org/specification
