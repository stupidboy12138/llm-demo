"""
MCP Complete Demo

This demo showcases the full Model Context Protocol implementation:
- Server setup with resources, tools, and prompts
- Client connection and capability discovery
- Resource reading
- Tool execution
- Prompt template retrieval
"""

import asyncio
from .mcp_server import MCPServer
from .mcp_client import MCPClient, print_section


async def demo_basic_workflow():
    """Demonstrate basic MCP workflow"""
    print_section("MCP Basic Workflow Demo")

    # 1. Create and start server
    print("[*] Step 1: Creating MCP Server...")
    server = MCPServer(name="Demo MCP Server", version="1.0.0")
    print(f"   [OK] Server created: {server.name}")

    # 2. Create client
    print("\n[*] Step 2: Creating MCP Client...")
    client = MCPClient(server)
    print("   [OK] Client created")

    # 3. Initialize connection
    print("\n[*] Step 3: Initializing Connection...")
    init_result = await client.initialize()
    print(f"   [OK] Connected to {client.server_info['name']}")
    print(f"   Protocol: {init_result['protocolVersion']}")

    # 4. Discover resources
    print("\n[*] Step 4: Discovering Resources...")
    resources = await client.list_resources()
    print(f"   [OK] Found {len(resources)} resources:")
    for res in resources:
        print(f"      - {res['name']} ({res['uri']})")

    # 5. Read a resource
    print("\n[*] Step 5: Reading Resource...")
    content = await client.read_resource("file://demo.txt")
    text = content['contents'][0]['text']
    print(f"   [OK] Resource content preview:")
    print(f"      {text[:100]}...")

    # 6. Discover tools
    print("\n[*] Step 6: Discovering Tools...")
    tools = await client.list_tools()
    print(f"   [OK] Found {len(tools)} tools:")
    for tool in tools:
        print(f"      - {tool['name']}: {tool['description']}")

    # 7. Execute a tool
    print("\n[*] Step 7: Executing Tool (calculate)...")
    result = await client.call_tool("calculate", {"expression": "2 ** 10"})
    print(f"   [OK] Calculation result: {result}")

    # 8. Discover prompts
    print("\n[*] Step 8: Discovering Prompts...")
    prompts = await client.list_prompts()
    print(f"   [OK] Found {len(prompts)} prompts:")
    for prompt in prompts:
        print(f"      - {prompt['name']}: {prompt['description']}")

    # 9. Get a prompt
    print("\n[*] Step 9: Getting Prompt Template...")
    prompt = await client.get_prompt("summarize", {
        "text": "This is a long text that needs summarization.",
        "max_length": "50 words"
    })
    print(f"   [OK] Prompt retrieved: {prompt['description']}")

    print("\n" + "="*60)
    print("[OK] Basic workflow completed successfully!")
    print("="*60 + "\n")


async def demo_advanced_scenarios():
    """Demonstrate advanced MCP scenarios"""
    print_section("MCP Advanced Scenarios")

    server = MCPServer()
    client = MCPClient(server)
    await client.initialize()

    # Scenario 1: Multi-step tool execution
    print("[1] Scenario 1: Multi-step File Operations")
    print("-" * 60)

    # Create a file
    print("[1.1] Creating file with content...")
    content_to_write = """# MCP Demo Output

This file was created by the MCP demo.

## Features Demonstrated:
- Resource discovery and reading
- Tool execution
- Prompt template retrieval

## Test Data:
- Timestamp: 2024-01-08
- Server: Demo MCP Server
- Protocol: MCP 2024-11-05
"""

    write_result = await client.call_tool("write_file", {
        "path": "mcp_demo_output.md",
        "content": content_to_write
    })
    print(f"   Result: {write_result}")

    # Read it back
    print("\n[1.2] Reading file back...")
    read_result = await client.call_tool("read_file", {
        "path": "mcp_demo_output.md"
    })
    print(f"   Preview: {read_result[:150]}...")

    # Scenario 2: Batch calculations
    print("\n[2] Scenario 2: Batch Calculations")
    print("-" * 60)

    expressions = [
        "2 ** 8",
        "sum([1, 2, 3, 4, 5])",
        "round(3.14159, 2)",
        "max([10, 25, 15, 30])"
    ]

    for i, expr in enumerate(expressions, 1):
        result = await client.call_tool("calculate", {"expression": expr})
        print(f"[2.{i}] {result}")

    # Scenario 3: Prompt template generation
    print("\n[3] Scenario 3: Prompt Template Generation")
    print("-" * 60)

    code_sample = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

    prompt = await client.get_prompt("code_review", {
        "code": code_sample,
        "language": "Python"
    })

    print("Generated prompt for code review:")
    for msg in prompt['messages']:
        print(f"\n[{msg['role'].upper()}]:")
        print(msg['content']['text'][:200] + "...")

    print("\n" + "="*60)
    print("[OK] Advanced scenarios completed!")
    print("="*60 + "\n")


async def demo_error_handling():
    """Demonstrate error handling"""
    print_section("MCP Error Handling Demo")

    server = MCPServer()
    client = MCPClient(server)
    await client.initialize()

    print("Testing error scenarios...\n")

    # Test 1: Invalid resource
    print("[Test 1] Attempting to read non-existent resource...")
    try:
        await client.read_resource("file://nonexistent.txt")
    except Exception as e:
        print(f"   [ERROR] Caught expected error: {e}\n")

    # Test 2: Invalid tool
    print("[Test 2] Attempting to call non-existent tool...")
    try:
        await client.call_tool("invalid_tool", {})
    except Exception as e:
        print(f"   [ERROR] Caught expected error: {e}\n")

    # Test 3: Invalid tool arguments
    print("[Test 3] Attempting to call tool with missing arguments...")
    try:
        await client.call_tool("read_file", {})
    except Exception as e:
        print(f"   [ERROR] Caught expected error: {e}\n")

    # Test 4: Invalid calculation
    print("[Test 4] Attempting invalid calculation...")
    result = await client.call_tool("calculate", {"expression": "1 / 0"})
    print(f"   [WARNING] Result: {result}\n")

    print("="*60)
    print("[OK] Error handling tests completed!")
    print("="*60 + "\n")


async def main():
    """Run all demos"""
    print("\n" + "="*60)
    print(" " * 15 + "MCP COMPLETE DEMO")
    print("="*60 + "\n")

    print("This demo will showcase:")
    print("  - Basic MCP workflow")
    print("  - Advanced scenarios")
    print("  - Error handling")
    print("\n" + "="*60 + "\n")

    # Run demos
    await demo_basic_workflow()
    await asyncio.sleep(1)

    await demo_advanced_scenarios()
    await asyncio.sleep(1)

    await demo_error_handling()

    print("\n" + "="*60)
    print(" " * 10 + "*** ALL DEMOS COMPLETED! ***")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
