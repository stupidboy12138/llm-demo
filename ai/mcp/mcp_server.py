"""
MCP Server Implementation

This module implements a Model Context Protocol server that provides:
1. Resources: File content, system info
2. Tools: File operations, calculator
3. Prompts: Pre-defined prompt templates
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== Data Models ====================

class Resource(BaseModel):
    """Resource that can be provided to the model"""
    uri: str = Field(..., description="Unique resource identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Resource description")
    mime_type: Optional[str] = Field(None, description="MIME type of the resource")


class Tool(BaseModel):
    """Tool that can be executed by the model"""
    name: str = Field(..., description="Tool identifier")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for input parameters")


class Prompt(BaseModel):
    """Prompt template"""
    name: str = Field(..., description="Prompt identifier")
    description: str = Field(..., description="Prompt description")
    arguments: List[Dict[str, str]] = Field(default_factory=list, description="Prompt arguments")


class Message(BaseModel):
    """MCP Protocol Message"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[int] = Field(None, description="Message ID")
    method: Optional[str] = Field(None, description="Method name")
    params: Optional[Dict[str, Any]] = Field(None, description="Method parameters")
    result: Optional[Any] = Field(None, description="Result (for responses)")
    error: Optional[Dict[str, Any]] = Field(None, description="Error (for error responses)")


# ==================== MCP Server ====================

class MCPServer:
    """
    Model Context Protocol Server

    Provides resources, tools, and prompts to AI models following the MCP specification.
    """

    def __init__(self, name: str = "Demo MCP Server", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.resources: Dict[str, Resource] = {}
        self.tools: Dict[str, Tool] = {}
        self.prompts: Dict[str, Prompt] = {}
        self._setup_default_capabilities()

    def _setup_default_capabilities(self):
        """Setup default resources, tools, and prompts"""

        # Register Resources
        self.register_resource(Resource(
            uri="system://info",
            name="System Information",
            description="Current system and server information",
            mime_type="application/json"
        ))

        self.register_resource(Resource(
            uri="file://demo.txt",
            name="Demo File",
            description="A demo text file resource",
            mime_type="text/plain"
        ))

        # Register Tools
        self.register_tool(Tool(
            name="read_file",
            description="Read content from a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to read"
                    }
                },
                "required": ["path"]
            }
        ))

        self.register_tool(Tool(
            name="write_file",
            description="Write content to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    }
                },
                "required": ["path", "content"]
            }
        ))

        self.register_tool(Tool(
            name="calculate",
            description="Perform mathematical calculation",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        ))

        # Register Prompts
        self.register_prompt(Prompt(
            name="code_review",
            description="Review code and provide feedback",
            arguments=[
                {"name": "code", "description": "Code to review", "required": "true"},
                {"name": "language", "description": "Programming language", "required": "false"}
            ]
        ))

        self.register_prompt(Prompt(
            name="summarize",
            description="Summarize text content",
            arguments=[
                {"name": "text", "description": "Text to summarize", "required": "true"},
                {"name": "max_length", "description": "Maximum summary length", "required": "false"}
            ]
        ))

    def register_resource(self, resource: Resource):
        """Register a resource"""
        self.resources[resource.uri] = resource

    def register_tool(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool

    def register_prompt(self, prompt: Prompt):
        """Register a prompt"""
        self.prompts[prompt.name] = prompt

    async def handle_request(self, message: Message) -> Message:
        """Handle incoming MCP request"""
        method = message.method
        params = message.params or {}

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "resources/list":
                result = await self._handle_list_resources(params)
            elif method == "resources/read":
                result = await self._handle_read_resource(params)
            elif method == "tools/list":
                result = await self._handle_list_tools(params)
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            elif method == "prompts/list":
                result = await self._handle_list_prompts(params)
            elif method == "prompts/get":
                result = await self._handle_get_prompt(params)
            else:
                raise ValueError(f"Unknown method: {method}")

            return Message(
                jsonrpc="2.0",
                id=message.id,
                result=result
            )

        except Exception as e:
            return Message(
                jsonrpc="2.0",
                id=message.id,
                error={
                    "code": -32000,
                    "message": str(e)
                }
            )

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "capabilities": {
                "resources": {"listChanged": True},
                "tools": {"listChanged": True},
                "prompts": {"listChanged": True}
            }
        }

    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        return {
            "resources": [
                resource.model_dump() for resource in self.resources.values()
            ]
        }

    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing 'uri' parameter")

        resource = self.resources.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")

        # Simulate reading resource content
        if uri == "system://info":
            content = json.dumps({
                "server_name": self.name,
                "server_version": self.version,
                "timestamp": datetime.now().isoformat(),
                "resources_count": len(self.resources),
                "tools_count": len(self.tools),
                "prompts_count": len(self.prompts)
            }, indent=2)
        elif uri == "file://demo.txt":
            content = "This is a demo file content from MCP server.\nIt demonstrates resource reading capability."
        else:
            content = f"Content of {uri}"

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.mime_type,
                    "text": content
                }
            ]
        }

    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "tools": [
                tool.model_dump() for tool in self.tools.values()
            ]
        }

    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing 'name' parameter")

        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        # Execute tool
        if tool_name == "read_file":
            result = await self._tool_read_file(arguments)
        elif tool_name == "write_file":
            result = await self._tool_write_file(arguments)
        elif tool_name == "calculate":
            result = await self._tool_calculate(arguments)
        else:
            raise ValueError(f"Tool not implemented: {tool_name}")

        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ]
        }

    async def _tool_read_file(self, arguments: Dict[str, Any]) -> str:
        """Tool: Read file"""
        path = arguments.get("path")
        if not path:
            raise ValueError("Missing 'path' argument")

        try:
            file_path = Path(path)
            if not file_path.exists():
                return f"Error: File not found: {path}"

            content = file_path.read_text(encoding="utf-8")
            return f"File content of {path}:\n\n{content}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    async def _tool_write_file(self, arguments: Dict[str, Any]) -> str:
        """Tool: Write file"""
        path = arguments.get("path")
        content = arguments.get("content")

        if not path:
            raise ValueError("Missing 'path' argument")
        if content is None:
            raise ValueError("Missing 'content' argument")

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    async def _tool_calculate(self, arguments: Dict[str, Any]) -> str:
        """Tool: Calculate mathematical expression"""
        expression = arguments.get("expression")
        if not expression:
            raise ValueError("Missing 'expression' argument")

        try:
            # Safe evaluation (limited to basic math)
            result = eval(expression, {"__builtins__": {}}, {})
            return f"{expression} = {result}"
        except Exception as e:
            return f"Error calculating expression: {str(e)}"

    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request"""
        return {
            "prompts": [
                prompt.model_dump() for prompt in self.prompts.values()
            ]
        }

    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if not prompt_name:
            raise ValueError("Missing 'name' parameter")

        prompt = self.prompts.get(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_name}")

        # Generate prompt content
        if prompt_name == "code_review":
            code = arguments.get("code", "")
            language = arguments.get("language", "unknown")
            content = f"Please review the following {language} code:\n\n{code}\n\nProvide feedback on:\n1. Code quality\n2. Potential bugs\n3. Performance issues\n4. Best practices"

        elif prompt_name == "summarize":
            text = arguments.get("text", "")
            max_length = arguments.get("max_length", "200 words")
            content = f"Please summarize the following text in {max_length}:\n\n{text}"

        else:
            content = f"Prompt template for {prompt_name}"

        return {
            "description": prompt.description,
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": content
                    }
                }
            ]
        }


# ==================== Server Runner ====================

async def run_server(host: str = "localhost", port: int = 3000):
    """Run the MCP server (simulation)"""
    server = MCPServer()

    print(f"[*] MCP Server '{server.name}' v{server.version} starting...")
    print(f"Host: {host}:{port}")
    print(f"Capabilities:")
    print(f"   - Resources: {len(server.resources)}")
    print(f"   - Tools: {len(server.tools)}")
    print(f"   - Prompts: {len(server.prompts)}")
    print("\n[OK] Server ready to accept connections\n")

    return server


if __name__ == "__main__":
    asyncio.run(run_server())
