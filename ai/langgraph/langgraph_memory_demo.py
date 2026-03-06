"""
LangGraph Agent 记忆方案演示

集成三种主流记忆方案:
1. Short-term Memory  - MemorySaver Checkpointer (线程内会话历史持久化)
2. Long-term Memory   - InMemoryStore (跨线程用户信息持久化)
3. Summary Memory     - 对话摘要压缩 (管理超长对话的上下文窗口)
"""

import asyncio
import json
import uuid
from typing import Annotated

from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.store.memory import InMemoryStore
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing_extensions import TypedDict


# ============================================================
# LLM 配置
# ============================================================

LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-deepbank-dev"
# MODEL = "360/gpt-5.2-thinking"
MODEL = "360/claude-4.5-sonnet"

llm = ChatOpenAI(
    model=MODEL,
    base_url=LITELLM_API_BASE,
    api_key=LITELLM_API_KEY,
    temperature=0.5,
    timeout=100,
    max_tokens=1000,
)

# ============================================================
# 记忆方案 1: Short-term Memory (短期记忆)
#
# 使用 MemorySaver 作为 Checkpointer,为每个 thread_id 维护独立
# 的对话历史。同一 thread_id 下的多轮对话自动延续上下文,不同
# thread_id 之间互相隔离。
#
# 生产环境可替换为 PostgresSaver / SqliteSaver 等持久化方案。
# ============================================================

checkpointer = MemorySaver()

# ============================================================
# 记忆方案 2: Long-term Memory (长期记忆)
#
# 使用 InMemoryStore 作为跨线程的持久化文档存储。按 namespace
# (如 user_id) 组织,存储用户偏好、关键事实等信息,在不同对话
# 线程中都能召回。
#
# 生产环境可替换为 PostgresStore 并配合 Embeddings 实现语义搜索。
# ============================================================

long_term_store = InMemoryStore()

# 对话摘要触发阈值: 消息数超过此值时自动生成摘要并裁剪旧消息
SUMMARY_MESSAGE_THRESHOLD = 10


# ============================================================
# State 定义: 增加 summary 字段支持摘要记忆
# ============================================================

class State(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str


# ============================================================
# Agent 构建 (带 MCP 工具 + 完整记忆)
# ============================================================

async def create_react_agent():
    """创建带有 MCP 工具和完整记忆功能的 ReAct Agent"""
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
    return _build_graph(tools)


def create_memory_agent():
    """创建不依赖 MCP 的纯记忆演示 Agent (无需外部服务)"""
    return _build_graph(tools=[])


def _build_graph(tools: list):
    """构建带有三种记忆方案的状态图"""
    llm_with_tools = llm.bind_tools(tools) if tools else llm
    tool_node = ToolNode(tools) if tools else None

    # --- Agent 节点: 整合长期记忆 + 对话摘要到上下文 ---
    async def chatbot(state: State, config, *, store):
        user_id = config.get("configurable", {}).get("user_id", "default")
        namespace = ("memories", user_id)

        # 从长期记忆 Store 中检索该用户的已知信息
        memories = store.search(namespace)
        memory_context = ""
        if memories:
            facts = [m.value.get("fact", str(m.value)) for m in memories]
            memory_context = "已知用户信息:\n" + "\n".join(f"- {f}" for f in facts)

        # 组装系统提示: 对话摘要 + 长期记忆
        system_parts = []
        summary = state.get("summary", "")
        if summary:
            system_parts.append(f"之前的对话摘要:\n{summary}")
        if memory_context:
            system_parts.append(memory_context)

        messages = list(state["messages"])
        if system_parts:
            messages = [SystemMessage(content="\n\n".join(system_parts))] + messages

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # --- 长期记忆提取节点: 从对话中抽取关键用户信息 ---
    async def extract_memories(state: State, config, *, store):
        user_id = config.get("configurable", {}).get("user_id", "default")
        namespace = ("memories", user_id)

        human_msgs = [m for m in state["messages"] if hasattr(m, "type") and m.type == "human"]
        if not human_msgs:
            return {}

        last_msg = human_msgs[-1].content
        extraction_prompt = (
            "分析以下用户消息,提取值得长期记住的用户偏好、个人信息或重要事实。\n"
            "如果有值得记住的信息,返回 JSON 列表,格式: [{\"fact\": \"...\"}]\n"
            "如果没有值得记住的信息,返回空列表 []\n"
            "只返回 JSON,不要其他内容。\n\n"
            f"用户消息: {last_msg}"
        )
        try:
            response = await llm.ainvoke([HumanMessage(content=extraction_prompt)])
            content = response.content.strip()
            if "[" in content:
                content = content[content.index("["):content.rindex("]") + 1]
                facts = json.loads(content)
                for fact in facts:
                    if isinstance(fact, dict) and "fact" in fact:
                        store.put(namespace, str(uuid.uuid4())[:8], {"fact": fact["fact"]})
        except Exception:
            pass
        return {}

    # --- 记忆方案 3: 对话摘要节点 ---
    async def summarize_conversation(state: State):
        """当消息数超过阈值时,使用 LLM 生成对话摘要并裁剪旧消息"""
        summary = state.get("summary", "")
        if summary:
            prompt = (
                f"这是之前的对话摘要:\n{summary}\n\n"
                "请结合以上摘要和下方新的对话内容,生成一份更新后的简洁摘要:"
            )
        else:
            prompt = "请对以下对话内容生成简洁的摘要,保留关键信息:"

        messages = state["messages"] + [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages)

        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
        return {"summary": response.content, "messages": delete_messages}

    # --- 路由逻辑 ---
    def after_agent(state: State):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "extract_memories"

    def after_extract(state: State):
        if len(state["messages"]) > SUMMARY_MESSAGE_THRESHOLD:
            return "summarize"
        return END

    # --- 构建状态图 ---
    #
    #  START -> agent --(tool_calls)--> tools -> agent  (工具循环)
    #                \                                 
    #                 `--(no tools)---> extract_memories (提取长期记忆)
    #                                       |
    #                                       +--(消息数 > 阈值)--> summarize -> END
    #                                       |
    #                                       `--(消息数 <= 阈值)--> END
    #
    graph = StateGraph(State)
    graph.add_node("agent", chatbot)
    graph.add_node("extract_memories", extract_memories)
    graph.add_node("summarize", summarize_conversation)

    if tool_node:
        graph.add_node("tools", tool_node)
        graph.add_edge("tools", "agent")

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", after_agent,
                                {"tools": "tools", "extract_memories": "extract_memories"} if tool_node
                                else {"extract_memories": "extract_memories"})
    graph.add_conditional_edges("extract_memories", after_extract)
    graph.add_edge("summarize", END)

    return graph.compile(checkpointer=checkpointer, store=long_term_store)


# ============================================================
# 演示函数
# ============================================================

async def demo_short_term_memory(agent):
    """演示 1: 短期记忆 — 同一 thread_id 内多轮对话自动延续上下文"""
    print("\n" + "=" * 60)
    print(" 演示 1: Short-term Memory (短期记忆 / Checkpointer)")
    print("  同一个 thread_id 内的多轮对话会自动记住上下文")
    print("=" * 60)

    config = {"configurable": {"thread_id": "thread-1", "user_id": "user_alice"}}

    print("\n--- 第 1 轮对话 ---")
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="你好,我叫Alice,我是一名Python开发者")]},
        config=config,
    )
    print(f"AI: {result['messages'][-1].content}")

    print("\n--- 第 2 轮对话 (同一线程,应记住名字) ---")
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="你还记得我叫什么吗?我是做什么的?")]},
        config=config,
    )
    print(f"AI: {result['messages'][-1].content}")

    print("\n--- 新线程 (thread-2,短期记忆隔离) ---")
    config_new = {"configurable": {"thread_id": "thread-2", "user_id": "user_alice"}}
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="你知道我叫什么名字吗?")]},
        config=config_new,
    )
    print(f"AI: {result['messages'][-1].content}")


async def demo_long_term_memory(agent):
    """演示 2: 长期记忆 — 跨线程的用户信息持久化"""
    print("\n" + "=" * 60)
    print(" 演示 2: Long-term Memory (长期记忆 / Store)")
    print("  用户信息跨线程持久化,新对话也能回忆用户偏好")
    print("=" * 60)

    config1 = {"configurable": {"thread_id": "lt-thread-1", "user_id": "user_bob"}}
    print("\n--- 线程 1: 告知个人信息 ---")
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="我叫Bob,我喜欢用Rust编程,最爱吃川菜")]},
        config=config1,
    )
    print(f"AI: {result['messages'][-1].content}")

    # 查看已提取的长期记忆
    memories = list(long_term_store.search(("memories", "user_bob")))
    print(f"\n  [Store] 已提取 {len(memories)} 条长期记忆:")
    for m in memories:
        print(f"    [{m.key}] {m.value}")

    config2 = {"configurable": {"thread_id": "lt-thread-2", "user_id": "user_bob"}}
    print("\n--- 线程 2 (新对话): 验证长期记忆召回 ---")
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="你了解我的编程偏好和饮食喜好吗?请推荐一些适合我的东西")]},
        config=config2,
    )
    print(f"AI: {result['messages'][-1].content}")


async def demo_summary_memory(agent):
    """演示 3: 摘要记忆 — 长对话自动压缩,管理上下文窗口"""
    print("\n" + "=" * 60)
    print(" 演示 3: Summary Memory (摘要记忆)")
    print(f"  消息数超过 {SUMMARY_MESSAGE_THRESHOLD} 时自动生成摘要并裁剪旧消息")
    print("=" * 60)

    config = {"configurable": {"thread_id": "summary-thread", "user_id": "user_carol"}}

    conversations = [
        "你好,我是Carol,一名前端开发者",
        "我最近在学习React和TypeScript",
        "你觉得Vue和React哪个更适合大型项目?",
        "我目前的项目大约有50个页面",
        "团队有8个人,其中3个是初级开发者",
        "我们目前用的是JavaScript,想迁移到TypeScript",
        "预算和时间都比较紧张",
    ]

    for i, msg in enumerate(conversations):
        print(f"\n--- 第 {i + 1} 轮 ---")
        print(f"用户: {msg}")
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=msg)]},
            config=config,
        )
        print(f"AI: {result['messages'][-1].content[:200]}...")

        state = await agent.aget_state(config)
        msg_count = len(state.values.get("messages", []))
        summary = state.values.get("summary", "")
        print(f"  [状态] 消息数: {msg_count}, 摘要: {'有' if summary else '无'}")
        if summary:
            print(f"  [摘要内容] {summary[:150]}...")


# ============================================================
# 入口
# ============================================================

async def run_agent():
    """运行带 MCP 工具的 Agent"""
    agent = await create_react_agent()

    from langchain_core.messages import HumanMessage
    config = {"configurable": {"thread_id": "main", "user_id": "default"}}
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="York今天天气怎么样")]},
        config=config,
    )
    for m in result["messages"]:
        m.pretty_print()


async def run_memory_demo():
    """运行三种记忆方案的完整演示 (无需 MCP 服务)"""
    agent = create_memory_agent()

    print("=" * 60)
    print(" LangGraph Agent 记忆方案演示")
    print("=" * 60)
    print("三种主流记忆方案:")
    print("  1. Short-term Memory  — MemorySaver Checkpointer (线程级)")
    print("  2. Long-term Memory   — InMemoryStore (跨线程)")
    print("  3. Summary Memory     — 对话摘要压缩 (长对话管理)")
    print("=" * 60)

    await demo_short_term_memory(agent)
    await demo_long_term_memory(agent)
    await demo_summary_memory(agent)


if __name__ == "__main__":
    # 记忆演示 (无需外部 MCP 服务)
    asyncio.run(run_memory_demo())

    # 带 MCP 工具的完整 Agent (需要 MCP 服务运行中)
    # asyncio.run(run_agent())