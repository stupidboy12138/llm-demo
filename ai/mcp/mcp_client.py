"""
MCP Client Implementation

This module implements a Model Context Protocol client that can:
1. Connect to MCP servers
2. Discover and use resources
3. Execute tools
4. Retrieve prompt templates
"""

import asyncio
from typing import Any, Dict, List, Optional

from .mcp_server import Message, MCPServer


class MCPClient:
    """
    Model Context Protocol Client

    Connects to MCP servers and provides methods to interact with
    server capabilities (resources, tools, prompts).
    """

    def __init__(self, server: MCPServer):
        """
        Initialize MCP client

        Args:
            server: MCP server instance (in production, this would be a connection)
        """
        self.server = server
        self._message_id = 0
        self._initialized = False
        self._server_info = {}
        self._capabilities = {}

    def _next_message_id(self) -> int:
        """Generate next message ID"""
        self._message_id += 1
        return self._message_id

    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send request to server"""
        message = Message(
            jsonrpc="2.0",
            id=self._next_message_id(),
            method=method,
            params=params
        )

        response = await self.server.handle_request(message)

        if response.error:
            raise Exception(f"MCP Error: {response.error['message']}")

        return response.result

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection with server"""
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {
                "name": "Demo MCP Client",
                "version": "1.0.0"
            },
            "capabilities": {}
        })

        self._initialized = True
        self._server_info = result.get("serverInfo", {})
        self._capabilities = result.get("capabilities", {})

        return result

    def _ensure_initialized(self):
        """Ensure client is initialized"""
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources"""
        self._ensure_initialized()
        result = await self._send_request("resources/list")
        return result.get("resources", [])

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read resource content"""
        self._ensure_initialized()
        result = await self._send_request("resources/read", {"uri": uri})
        return result

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        self._ensure_initialized()
        result = await self._send_request("tools/list")
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool"""
        self._ensure_initialized()
        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        # Extract text from content
        content = result.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "")
        return ""

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts"""
        self._ensure_initialized()
        result = await self._send_request("prompts/list")
        return result.get("prompts", [])

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get prompt template"""
        self._ensure_initialized()
        result = await self._send_request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        return result

    @property
    def server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return self._server_info

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get server capabilities"""
        return self._capabilities


# ==================== Helper Functions ====================

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_resources(resources: List[Dict[str, Any]]):
    """Pretty print resources"""
    for resource in resources:
        print(f"[Resource] {resource['name']}")
        print(f"   URI: {resource['uri']}")
        print(f"   Type: {resource.get('mime_type', 'N/A')}")
        if resource.get('description'):
            print(f"   Description: {resource['description']}")
        print()


def print_tools(tools: List[Dict[str, Any]]):
    """Pretty print tools"""
    for tool in tools:
        print(f"[Tool] {tool['name']}")
        print(f"   {tool['description']}")
        props = tool['input_schema'].get('properties', {})
        if props:
            print(f"   Parameters:")
            for param_name, param_info in props.items():
                required = param_name in tool['input_schema'].get('required', [])
                req_mark = "*" if required else ""
                print(f"     - {param_name}{req_mark}: {param_info.get('description', '')}")
        print()


def print_prompts(prompts: List[Dict[str, Any]]):
    """Pretty print prompts"""
    for prompt in prompts:
        print(f"[Prompt] {prompt['name']}")
        print(f"   {prompt['description']}")
        if prompt.get('arguments'):
            print(f"   Arguments:")
            for arg in prompt['arguments']:
                req_mark = "*" if arg.get('required') == 'true' else ""
                print(f"     - {arg['name']}{req_mark}: {arg.get('description', '')}")
        print()


async def main():
    """Demo client usage"""

    # Create server and client
    print_section("MCP Demo - Initializing")
    server = MCPServer()
    client = MCPClient(server)

    # Initialize connection
    print("[*] Connecting to MCP server...")
    init_result = await client.initialize()
    print(f"[OK] Connected to: {client.server_info['name']} v{client.server_info['version']}")
    print(f"Protocol Version: {init_result['protocolVersion']}")

    # List and display resources
    print_section("Available Resources")
    resources = await client.list_resources()
    print_resources(resources)

    # Read a resource
    print_section("Reading Resource")
    print("[*] Reading system://info...")
    resource_content = await client.read_resource("system://info")
    for content in resource_content.get("contents", []):
        print(f"\nContent ({content['mimeType']}):")
        print(content['text'])

    # List and display tools
    print_section("Available Tools")
    tools = await client.list_tools()
    print_tools(tools)

    # Call tools
    print_section("Calling Tools")

    # 1. Calculate tool
    print("[*] Calculating: (10 + 20) * 3")
    calc_result = await client.call_tool("calculate", {
        "expression": "(10 + 20) * 3"
    })
    print(f"Result: {calc_result}\n")

    # 2. Write file tool
    print("[*] Writing test file...")
    write_result = await client.call_tool("write_file", {
        "path": "test_mcp_output.txt",
        "content": "Hello from MCP demo!\nThis file was created by the MCP write_file tool."
    })
    print(f"Result: {write_result}\n")

    # 3. Read file tool
    print("[*] Reading test file...")
    read_result = await client.call_tool("read_file", {
        "path": "test_mcp_output.txt"
    })
    print(f"Result:\n{read_result}\n")

    # List and display prompts
    print_section("Available Prompts")
    prompts = await client.list_prompts()
    print_prompts(prompts)

    # Get a prompt
    print_section("Getting Prompt Template")
    print("[*] Getting code_review prompt...")
    prompt_result = await client.get_prompt("code_review", {
        "code": "def hello():\n    print('Hello, World!')",
        "language": "Python"
    })
    print(f"Description: {prompt_result['description']}")
    print(f"\nGenerated Prompt:")
    for message in prompt_result.get("messages", []):
        print(f"[{message['role']}]: {message['content']['text']}")

    print_section("Demo Complete")
    print("[OK] All MCP operations completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
