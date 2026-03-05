"""
Quick Start Guide for MCP Demo
"""

# ============================================================================
#  MCP (Model Context Protocol) Quick Start
# ============================================================================

"""
OVERVIEW:
---------
This directory contains a complete MCP implementation with:
- MCP Server: Provides resources, tools, and prompts
- MCP Client: Connects to and interacts with MCP servers
- Demo: Comprehensive examples of all features

RUNNING THE DEMO:
-----------------
python -m ai.mcp.demo

This will demonstrate:
1. Basic MCP workflow (initialization, discovery, usage)
2. Advanced scenarios (file operations, calculations, prompts)
3. Error handling

BASIC USAGE EXAMPLE:
--------------------
"""

import asyncio
from ai.mcp.mcp_server import MCPServer
from ai.mcp.mcp_client import MCPClient


async def quick_example():
    # 1. Create server and client
    server = MCPServer()
    client = MCPClient(server)

    # 2. Initialize connection
    await client.initialize()
    print(f"Connected to: {client.server_info['name']}")

    # 3. List resources
    resources = await client.list_resources()
    print(f"Found {len(resources)} resources")

    # 4. Read a resource
    content = await client.read_resource("system://info")
    print("Resource content:", content)

    # 5. Execute a tool
    result = await client.call_tool("calculate", {"expression": "2 + 2"})
    print(f"Calculation result: {result}")

    # 6. Get a prompt template
    prompt = await client.get_prompt("code_review", {
        "code": "def hello(): pass",
        "language": "Python"
    })
    print(f"Prompt: {prompt['description']}")


"""
AVAILABLE RESOURCES:
--------------------
- system://info          : Server information and statistics
- file://demo.txt        : Demo text file

AVAILABLE TOOLS:
----------------
- read_file              : Read file from filesystem
  Parameters: path (required)

- write_file             : Write content to file
  Parameters: path (required), content (required)

- calculate              : Evaluate math expression
  Parameters: expression (required)

AVAILABLE PROMPTS:
------------------
- code_review            : Generate code review prompt
  Arguments: code (required), language (optional)

- summarize              : Generate summarization prompt
  Arguments: text (required), max_length (optional)

EXTENDING THE SERVER:
---------------------
"""


# Add custom resource
async def add_custom_resource():
    from ai.mcp.mcp_server import Resource

    server = MCPServer()
    server.register_resource(Resource(
        uri="custom://my-data",
        name="My Custom Resource",
        description="Custom data source",
        mime_type="application/json"
    ))


# Add custom tool
async def add_custom_tool():
    from ai.mcp.mcp_server import Tool

    server = MCPServer()
    server.register_tool(Tool(
        name="my_tool",
        description="Does something useful",
        input_schema={
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Input parameter"}
            },
            "required": ["param"]
        }
    ))
    # Note: You need to implement the handler in mcp_server._handle_call_tool


"""
API METHODS:
------------
Client methods:
- await client.initialize()
- await client.list_resources()
- await client.read_resource(uri)
- await client.list_tools()
- await client.call_tool(name, arguments)
- await client.list_prompts()
- await client.get_prompt(name, arguments)

PROTOCOL:
---------
Uses JSON-RPC 2.0 over custom transport
Message format:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {"name": "calculate", "arguments": {"expression": "2+2"}}
}

FOR MORE DETAILS:
-----------------
See README.md in ai/mcp/ directory
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nRunning quick example...\n")
    asyncio.run(quick_example())
