import asyncio
from typing import Annotated

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_mcp_adapters.client import MultiServerMCPClient


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-deepbank-dev"
# MODEL="360/deepseek-v3.1"
# MODEL="360/gpt-5.2-thinking"
MODEL="360/claude-4.5-sonnet"

llm = ChatOpenAI(
    model=MODEL,  # 根据LiteLLM实际支持的模型调整
    base_url=LITELLM_API_BASE,
    api_key=LITELLM_API_KEY,
    temperature=0.5,
    timeout=100,
    max_tokens=1000,
)

async def create_react_agent():
    #memory
    checkpointer = InMemorySaver()
    #mcp
    client = MultiServerMCPClient(
        {
            # "math": {
            #     "command": "python",
            #     # Replace with absolute path to your math_server.py file
            #     "args": ["/path/to/math_server.py"],
            #     "transport": "stdio",
            # },
            "github": {
                "url": "https://api.githubcopilot.com/mcp/",
                "transport": "streamable_http",
                "headers": {"Authorization": "Bearer "},
            },
            "weather":{
                "url": "http://127.0.0.1:8000/mcp/",
                "transport": "streamable_http",
            }
        }
    )
    # 获取 MCP 工具
    tools = await client.get_tools()
    print(f"已加载 {len(tools)} 个 MCP 工具: {[t.name for t in tools]}")

    # 使用预建的 ReAct agent 模式
    tool_node = ToolNode(tools)

    def should_continue(state: State):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    llm_with_tools = llm.bind_tools(tools)
    async def chatbot(state: State):
        return {"messages": [await llm_with_tools.ainvoke(state["messages"])]}

    graph = StateGraph(State)
    graph.add_node("agent", chatbot)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")  # 循环回 agent

    return graph.compile()

async def run_agent():

    """异步运行 agent 和 MCP 工具"""
    agent = await create_react_agent()

    # 调用 agent
    from langchain_core.messages import HumanMessage
    messages = [HumanMessage(content="请使用github工具，列出GitHub账户中所有的仓库，并告诉我一共有几个")]
    # messages = [HumanMessage(content="York今天天气怎么样")]
    messages = await agent.ainvoke({"messages": messages})
    for m in messages["messages"]:
        m.pretty_print()

if __name__ == "__main__":
    # 运行异步代码
    asyncio.run(run_agent())