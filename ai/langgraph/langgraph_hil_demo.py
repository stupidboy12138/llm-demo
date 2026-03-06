import asyncio
import json
from typing import Annotated

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
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

async def create_react_agent(enable_hil: bool = False):
    """创建 ReAct Agent

    Args:
        enable_hil: 是否启用人机协作（Human-in-the-Loop）。
                    启用后会在工具执行前暂停，等待人工审核确认。
    """
    checkpointer = InMemorySaver()

    client = MultiServerMCPClient(
        {
            "github": {
                "url": "https://api.githubcopilot.com/mcp/",
                "transport": "streamable_http",
                "headers": {"Authorization": "Bearer "},
            },
            "weather": {
                "url": "http://127.0.0.1:8000/mcp/",
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    print(f"已加载 {len(tools)} 个 MCP 工具: {[t.name for t in tools]}")

    tool_node = ToolNode(tools)

    llm_with_tools = llm.bind_tools(tools)

    async def chatbot(state: State):
        return {"messages": [await llm_with_tools.ainvoke(state["messages"])]}

    def human_review(state: State) -> Command[str]:
        """人工审核节点: 使用 interrupt() 暂停执行，展示工具调用信息并等待人类确认。

        人类可以:
          - 输入 "approve" / "yes" / "y": 批准执行
          - 输入 "reject" / "no" / "n":  拒绝执行，返回拒绝消息给 agent
          - 输入其他文本:                 作为反馈发送给 agent 重新规划
        """
        last_message = state["messages"][-1]

        tool_calls_info = []
        for tc in last_message.tool_calls:
            tool_calls_info.append({
                "tool": tc["name"],
                "args": tc["args"],
                "id": tc["id"],
            })

        human_response = interrupt({
            "question": "Agent 请求调用以下工具，是否批准？",
            "tool_calls": tool_calls_info,
            "options": "输入 approve/yes/y 批准 | reject/no/n 拒绝 | 其他文本作为反馈"
        })

        review = str(human_response).strip().lower()

        if review in ("approve", "yes", "y"):
            return Command(goto="tools")

        if review in ("reject", "no", "n"):
            tool_messages = [
                ToolMessage(
                    content="工具调用已被用户拒绝。",
                    tool_call_id=tc["id"],
                )
                for tc in last_message.tool_calls
            ]
            return Command(goto="agent", update={"messages": tool_messages})

        tool_messages = [
            ToolMessage(
                content=f"工具调用未执行。用户反馈: {human_response}",
                tool_call_id=tc["id"],
            )
            for tc in last_message.tool_calls
        ]
        return Command(goto="agent", update={"messages": tool_messages})

    def should_continue(state: State):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "human_review" if enable_hil else "tools"
        return END

    # 构建状态图
    #
    # 不启用 HIL:
    #   START -> agent --(tool_calls)--> tools -> agent
    #                  \--(no tools)---> END
    #
    # 启用 HIL:
    #   START -> agent --(tool_calls)--> human_review --(approve)--> tools -> agent
    #                  \                             \--(reject/feedback)--> agent
    #                   \--(no tools)---> END
    graph = StateGraph(State)
    graph.add_node("agent", chatbot)
    graph.add_node("tools", tool_node)

    if enable_hil:
        graph.add_node("human_review", human_review)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)

    if enable_hil:
        graph.add_edge("tools", "agent")
    else:
        graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)

async def run_agent():
    """异步运行 agent 和 MCP 工具（无 HIL）"""
    agent = await create_react_agent(enable_hil=False)

    config = {"configurable": {"thread_id": "main"}}
    messages = [HumanMessage(content="请使用github工具，列出GitHub账户中所有的仓库，并告诉我一共有几个")]
    result = await agent.ainvoke({"messages": messages}, config=config)
    for m in result["messages"]:
        m.pretty_print()


async def run_agent_with_hil():
    """异步运行 agent 并启用人机协作（HIL）

    工作流:
      1. 用户输入自然语言请求
      2. Agent 规划并发起工具调用
      3. 执行暂停 (interrupt)，在终端展示待执行的工具调用详情
      4. 用户审核后输入 approve/reject/反馈
      5. 根据用户决策继续执行或重新规划
      6. 循环直到 Agent 给出最终回复
    """
    agent = await create_react_agent(enable_hil=True)

    config = {"configurable": {"thread_id": "hil-thread"}}
    user_input = input("\n请输入你的问题 (直接回车使用默认问题): ").strip()
    if not user_input:
        user_input = "New York今天天气怎么样"

    print(f"\n>> 用户: {user_input}")
    print("-" * 50)

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )

    while True:
        state = await agent.aget_state(config)

        if not state.next:
            print("\n" + "=" * 50)
            print("Agent 最终回复:")
            print("=" * 50)
            last_msg = state.values["messages"][-1]
            print(last_msg.content)
            break

        # 有 interrupt 等待人工审核
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                for intr in task.interrupts:
                    interrupt_value = intr.value
                    print(f"\n{'=' * 50}")
                    print(f"  [HIL] {interrupt_value.get('question', '')}")
                    print(f"{'=' * 50}")
                    for i, tc in enumerate(interrupt_value.get("tool_calls", [])):
                        print(f"  [{i + 1}] 工具: {tc['tool']}")
                        args_str = json.dumps(tc["args"], ensure_ascii=False, indent=4)
                        print(f"      参数: {args_str}")
                    print(f"\n  {interrupt_value.get('options', '')}")
                    print(f"{'=' * 50}")

        human_input = input("\n你的决策: ").strip()
        if not human_input:
            human_input = "approve"

        print(f"\n>> 用户决策: {human_input}")
        print("-" * 50)

        result = await agent.ainvoke(
            Command(resume=human_input),
            config=config,
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--hil":
        asyncio.run(run_agent_with_hil())
    else:
        asyncio.run(run_agent())