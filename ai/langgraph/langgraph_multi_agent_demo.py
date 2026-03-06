"""
LangGraph 多智能体系统 Demo

演示两种主流多智能体架构模式:
1. Supervisor 模式 — 中心化协调器将任务路由到专业 Agent，Agent 完成后交回 Supervisor 决定下一步
2. Swarm/Handoff 模式 — Agent 之间可通过 handoff 工具相互转交控制权，无需中心协调

依赖: langchain-openai, langgraph, langchain-core
运行: python -m ai.langgraph.langgraph_multi_agent_demo
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# ============================================================
# LLM 配置
# ============================================================

LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-deepbank-dev"
MODEL = "360/claude-4.5-sonnet"


def create_llm(temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
    return ChatOpenAI(
        model=MODEL,
        base_url=LITELLM_API_BASE,
        api_key=LITELLM_API_KEY,
        temperature=temperature,
        timeout=120,
        max_tokens=max_tokens,
    )


# ============================================================
# 工具定义 — 每类 Agent 拥有专属工具集
# ============================================================

# ---------- 研究员 Agent 工具 ----------

@tool
def search_web(query: str) -> str:
    """搜索网络获取最新技术信息。参数 query: 搜索关键词。"""
    knowledge = {
        "ai": "2025年AI领域进展: OpenAI o3发布, Claude 4系列上线, Gemini 2.0支持原生多模态。"
              "多智能体系统成为热门方向，LangGraph、AutoGen、CrewAI 成为主流框架。",
        "python": "Python 3.13 正式发布，引入自由线程模式(free-threading)和实验性JIT编译器，性能大幅提升。",
        "langgraph": "LangGraph 是 LangChain 团队开发的多智能体编排框架，支持状态图、检查点、"
                     "人机交互和多种协作模式(Supervisor / Swarm / Hierarchical)。",
        "multi-agent": "主流多智能体架构: 1) Supervisor 模式 — 中心路由; "
                       "2) Swarm/Handoff 模式 — 去中心化转交; "
                       "3) Hierarchical 模式 — 分层管理。",
        "rag": "RAG (检索增强生成) 最新进展: Self-RAG 自适应检索、CRAG 修正式检索、"
               "GraphRAG 基于知识图谱的检索。",
    }
    for key, value in knowledge.items():
        if key in query.lower():
            return value
    return f"关于 '{query}' 的搜索结果: 暂无精确匹配，建议使用更具体的关键词。"


@tool
def fetch_arxiv_papers(topic: str) -> str:
    """获取 arXiv 上与主题相关的最新论文摘要。参数 topic: 论文主题。"""
    papers = {
        "multi-agent": (
            "1. 'AgentVerse: Facilitating Multi-Agent Collaboration' — 提出多智能体协作新范式\n"
            "2. 'AutoGen: Enabling Next-Gen LLM Applications' — 微软可对话多智能体框架\n"
            "3. 'CAMEL: Communicative Agents for Mind Exploration' — 角色扮演式多Agent协作"
        ),
        "rag": (
            "1. 'Self-RAG: Learning to Retrieve, Generate and Critique' — 自适应检索增强\n"
            "2. 'CRAG: Corrective Retrieval Augmented Generation' — 修正式RAG\n"
            "3. 'GraphRAG: Unlocking LLM Discovery on Narrative Text' — 图结构RAG"
        ),
        "agent": (
            "1. 'ReAct: Synergizing Reasoning and Acting in LLMs' — 经典推理-行动框架\n"
            "2. 'Toolformer: LLMs Can Teach Themselves to Use Tools' — 工具学习\n"
            "3. 'Tree of Thoughts: Deliberate Problem Solving with LLMs' — 思维树搜索"
        ),
    }
    for key, value in papers.items():
        if key in topic.lower():
            return value
    return f"关于 '{topic}' 的论文: 建议尝试 'multi-agent'、'rag'、'agent' 等关键词。"


# ---------- 程序员 Agent 工具 ----------

@tool
def execute_python(code: str) -> str:
    """在安全沙箱中执行 Python 代码并返回结果。参数 code: Python 代码字符串。"""
    SAFE_BUILTINS = {
        "len": len, "range": range, "list": list, "dict": dict, "tuple": tuple,
        "set": set, "str": str, "int": int, "float": float, "bool": bool,
        "sum": sum, "max": max, "min": min, "abs": abs, "round": round, "pow": pow,
        "sorted": sorted, "reversed": reversed, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter, "print": print,
        "isinstance": isinstance, "type": type, "True": True, "False": False, "None": None,
    }
    try:
        local_vars: dict = {}
        exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
        if "result" in local_vars:
            return f"执行成功，result = {local_vars['result']}"
        output_vars = {k: v for k, v in local_vars.items() if not k.startswith("_")}
        return f"代码执行完成。变量: {output_vars}" if output_vars else "代码执行完成，无返回值。"
    except Exception as e:
        return f"执行错误: {type(e).__name__}: {e}"


@tool
def review_code(code: str) -> str:
    """对代码进行质量审查并给出改进建议。参数 code: 待审查的代码。"""
    lines = code.strip().splitlines()
    non_empty = [l for l in lines if l.strip()]
    issues = []
    if not any('"""' in code or "'''" in code for _ in [1]):
        issues.append("缺少文档字符串(docstring)")
    if not any("->" in l for l in lines):
        issues.append("缺少返回类型标注")
    if any(len(l) > 100 for l in lines):
        issues.append("存在超过 100 字符的行，建议拆分")
    long_funcs = [l.strip() for l in lines if l.strip().startswith("def ")]
    if len(non_empty) > 30 and len(long_funcs) <= 1:
        issues.append("函数过长，建议拆分为更小的函数")

    return json.dumps({
        "总行数": len(lines),
        "有效行数": len(non_empty),
        "函数数量": len(long_funcs),
        "复杂度评级": "低" if len(non_empty) < 15 else "中" if len(non_empty) < 40 else "高",
        "发现的问题": issues if issues else ["代码质量良好，未发现明显问题"],
    }, ensure_ascii=False, indent=2)


# ---------- 数据分析师 Agent 工具 ----------

@tool
def calculate_statistics(numbers: list[float]) -> str:
    """对一组数值数据做描述性统计分析。参数 numbers: 数值列表。"""
    if not numbers:
        return "错误: 数据列表为空"
    n = len(numbers)
    mean = sum(numbers) / n
    sorted_nums = sorted(numbers)
    median = (
        sorted_nums[n // 2]
        if n % 2 == 1
        else (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
    )
    variance = sum((x - mean) ** 2 for x in numbers) / n
    std_dev = variance ** 0.5
    q1_idx, q3_idx = n // 4, 3 * n // 4
    return json.dumps({
        "样本量": n,
        "均值": round(mean, 2),
        "中位数": round(median, 2),
        "标准差": round(std_dev, 2),
        "最小值": min(numbers),
        "最大值": max(numbers),
        "极差": round(max(numbers) - min(numbers), 2),
        "Q1(25%)": round(sorted_nums[q1_idx], 2),
        "Q3(75%)": round(sorted_nums[q3_idx], 2),
    }, ensure_ascii=False, indent=2)


@tool
def generate_text_chart(data: dict, chart_type: str = "bar") -> str:
    """根据数据生成 ASCII 文本图表。参数 data: {标签: 数值} 字典; chart_type: bar 或 line。"""
    if not data:
        return "错误: 数据为空"
    max_val = max(data.values()) if data.values() else 1
    max_label_len = max(len(str(k)) for k in data)

    lines = [f"[{chart_type.upper()} 图表]", ""]
    if chart_type == "line":
        for key, val in data.items():
            pos = int(val / max_val * 40) if max_val else 0
            line = list(" " * 42)
            line[pos] = "*"
            lines.append(f"  {str(key):>{max_label_len}} |{''.join(line)}| {val}")
    else:
        for key, val in data.items():
            bar_len = int(val / max_val * 35) if max_val else 0
            lines.append(f"  {str(key):>{max_label_len}} | {'█' * bar_len} {val}")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# 模式一: Supervisor 多智能体
# ============================================================

AGENT_REGISTRY = {
    "researcher": {
        "label": "研究员",
        "tools": [search_web, fetch_arxiv_papers],
        "system_prompt": (
            "你是一位专业的研究员 Agent，擅长信息检索与知识整理。\n"
            "职责: 使用搜索和论文检索工具获取信息，提供简洁准确的研究报告。\n"
            "要求: 必须使用工具获取信息，不要凭空编造内容。"
        ),
    },
    "coder": {
        "label": "程序员",
        "tools": [execute_python, review_code],
        "system_prompt": (
            "你是一位资深程序员 Agent，擅长编写和审查代码。\n"
            "职责: 编写高质量 Python 代码、执行代码、审查代码质量。\n"
            "要求: 编写的代码应简洁、可读、有良好的错误处理。"
        ),
    },
    "analyst": {
        "label": "数据分析师",
        "tools": [calculate_statistics, generate_text_chart],
        "system_prompt": (
            "你是一位专业的数据分析师 Agent，擅长统计分析与数据可视化。\n"
            "职责: 使用统计工具分析数据，生成可视化图表，解读数据趋势。\n"
            "要求: 分析结果须包含关键统计指标和业务洞察。"
        ),
    },
}

SUPERVISOR_SYSTEM = """\
你是多智能体系统的 Supervisor（协调器）。你的职责是：根据用户请求和当前对话进展，决定下一步由哪个 Agent 处理，或是否结束。

可用 Agent:
- researcher — 研究员，擅长搜索信息、查找论文
- coder — 程序员，擅长写代码、分析代码
- analyst — 数据分析师，擅长统计分析、数据可视化

路由规则:
1. 分析用户请求的核心意图
2. 如果已有 Agent 返回了满足用户需求的结果，选择 FINISH
3. 如果任务需要多步协作（如先调研再编码），依次路由
4. 每次只选择一个 Agent

你必须且只回复一个 JSON:
{"next": "researcher|coder|analyst|FINISH", "reason": "简要说明选择原因"}
"""


class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str
    iteration: int


def _build_agent_node(agent_key: str):
    """为指定 Agent 构建一个可执行工具调用的图节点。"""
    config = AGENT_REGISTRY[agent_key]
    llm = create_llm()
    tools = config["tools"]
    llm_with_tools = llm.bind_tools(tools)
    tool_executor = ToolNode(tools)
    sys_msg = SystemMessage(content=config["system_prompt"])

    async def node_fn(state: SupervisorState) -> dict:
        user_msgs = [m for m in state["messages"] if isinstance(m, HumanMessage)][-3:]
        response = await llm_with_tools.ainvoke([sys_msg] + user_msgs)
        print(f"  [{config['label']}] 开始处理...")

        if response.tool_calls:
            tool_result = await tool_executor.ainvoke({"messages": [response]})
            summary = await llm.ainvoke(
                [sys_msg] + user_msgs + [response] + tool_result["messages"]
            )
            content = summary.content
        else:
            content = response.content

        print(f"  [{config['label']}] 完成")
        return {"messages": [AIMessage(content=f"[{config['label']}] {content}")]}

    return node_fn


def build_supervisor_graph() -> StateGraph:
    """
    构建 Supervisor 多智能体工作流:

        START → supervisor ──┬─→ researcher ──→ supervisor
                             ├─→ coder      ──→ supervisor
                             ├─→ analyst    ──→ supervisor
                             └─→ finish     ──→ END
    """
    llm = create_llm(temperature=0)
    max_iterations = 6

    async def supervisor_node(state: SupervisorState) -> dict:
        iteration = state.get("iteration", 0) + 1
        if iteration > max_iterations:
            print(f"  [Supervisor] 已达最大迭代次数 ({max_iterations})，强制结束")
            return {"next_agent": "FINISH", "iteration": iteration}

        response = await llm.ainvoke(
            [SystemMessage(content=SUPERVISOR_SYSTEM)] + state["messages"]
        )
        try:
            match = re.search(r"\{[^}]+\}", response.content)
            decision = json.loads(match.group()) if match else {}
            next_agent = decision.get("next", "FINISH")
            reason = decision.get("reason", "")
        except (json.JSONDecodeError, AttributeError):
            next_agent, reason = "FINISH", response.content

        print(f"  [Supervisor] 第 {iteration} 轮 → {next_agent}（{reason}）")
        return {
            "next_agent": next_agent,
            "iteration": iteration,
            "messages": [AIMessage(content=f"[Supervisor] → {next_agent}: {reason}")],
        }

    async def finish_node(state: SupervisorState) -> dict:
        agent_outputs = [
            m.content for m in state["messages"]
            if isinstance(m, AIMessage)
            and not m.content.startswith("[Supervisor]")
            and m.content.startswith("[")
        ]
        if not agent_outputs:
            return {"messages": [AIMessage(content="任务完成，但没有收到 Agent 输出。")]}

        summary_prompt = (
            "请根据以下各 Agent 的输出，为用户生成一份简洁、完整的最终回答:\n\n"
            + "\n\n".join(agent_outputs)
        )
        llm_final = create_llm()
        resp = await llm_final.ainvoke([
            SystemMessage(content="你是一个汇总助手，负责把多个 Agent 的结果整合成连贯的最终回答。"),
            HumanMessage(content=summary_prompt),
        ])
        return {"messages": [AIMessage(content=f"[最终回答] {resp.content}")]}

    def route(state: SupervisorState) -> str:
        target = state.get("next_agent", "FINISH")
        return target if target in AGENT_REGISTRY else "finish"

    graph = StateGraph(SupervisorState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("finish", finish_node)
    for key in AGENT_REGISTRY:
        graph.add_node(key, _build_agent_node(key))
        graph.add_edge(key, "supervisor")

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor", route,
        {**{k: k for k in AGENT_REGISTRY}, "finish": "finish"},
    )
    graph.add_edge("finish", END)
    return graph.compile()


# ============================================================
# 模式二: Swarm / Handoff 多智能体
# ============================================================

@tool
def handoff_to_researcher() -> str:
    """当需要搜索信息或查找资料时，转交给研究员 Agent。"""
    return "__handoff__researcher"


@tool
def handoff_to_coder() -> str:
    """当需要编写或分析代码时，转交给程序员 Agent。"""
    return "__handoff__coder"


@tool
def handoff_to_analyst() -> str:
    """当需要进行数据分析或统计计算时，转交给数据分析师 Agent。"""
    return "__handoff__analyst"


HANDOFF_TOOLS = [handoff_to_researcher, handoff_to_coder, handoff_to_analyst]
HANDOFF_MAP = {
    "handoff_to_researcher": "researcher",
    "handoff_to_coder": "coder",
    "handoff_to_analyst": "analyst",
}


class SwarmState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    current_agent: str
    handoff_count: int


def build_swarm_graph() -> StateGraph:
    """
    构建 Swarm/Handoff 多智能体工作流:

        START → triage ──→ agent_X ──(handoff)──→ agent_Y ──→ END
                                    └─(done)──────────────→ END

    每个 Agent 除了自身工具外，还持有 handoff 工具，可将任务转交给其他 Agent。
    """
    max_handoffs = 4

    def _build_swarm_node(agent_key: str):
        config = AGENT_REGISTRY[agent_key]
        llm = create_llm()
        own_tools = config["tools"]
        other_handoffs = [t for t in HANDOFF_TOOLS if agent_key not in t.name]
        all_tools = own_tools + other_handoffs
        llm_with_tools = llm.bind_tools(all_tools)
        own_tool_node = ToolNode(own_tools)

        extra_prompt = (
            "\n\n你可以使用 handoff 工具将任务转交给其他 Agent。"
            "只在任务明确超出你的能力范围时才转交，否则优先自己处理。"
        )
        sys_msg = SystemMessage(content=config["system_prompt"] + extra_prompt)

        async def node_fn(state: SwarmState) -> dict:
            handoff_count = state.get("handoff_count", 0)
            recent = state["messages"][-6:]
            response = await llm_with_tools.ainvoke([sys_msg] + recent)
            print(f"  [{config['label']}] 处理中...")

            if response.tool_calls:
                for tc in response.tool_calls:
                    if tc["name"] in HANDOFF_MAP and handoff_count < max_handoffs:
                        target = HANDOFF_MAP[tc["name"]]
                        print(f"  [{config['label']}] → 转交给 {AGENT_REGISTRY[target]['label']}")
                        return {
                            "current_agent": target,
                            "handoff_count": handoff_count + 1,
                            "messages": [AIMessage(
                                content=f"[{config['label']}] 此任务更适合"
                                        f"{AGENT_REGISTRY[target]['label']}，已转交。"
                            )],
                        }

                tool_result = await own_tool_node.ainvoke({"messages": [response]})
                summary = await llm.ainvoke(
                    [sys_msg] + recent + [response] + tool_result["messages"]
                )
                content = summary.content
            else:
                content = response.content

            print(f"  [{config['label']}] 完成")
            return {
                "current_agent": "__done__",
                "messages": [AIMessage(content=f"[{config['label']}] {content}")],
            }

        return node_fn

    async def triage_node(state: SwarmState) -> dict:
        """入口分诊节点: 快速判断应由哪个 Agent 首先处理。"""
        llm = create_llm(temperature=0)
        prompt = (
            "根据用户请求判断应交给哪个 Agent 处理。只回复一个单词:\n"
            "- researcher (信息搜索/资料查找)\n"
            "- coder (编程/代码相关)\n"
            "- analyst (数据分析/统计)\n"
        )
        resp = await llm.ainvoke(
            [SystemMessage(content=prompt)] + state["messages"]
        )
        chosen = "researcher"
        for key in AGENT_REGISTRY:
            if key in resp.content.strip().lower():
                chosen = key
                break
        print(f"  [分诊] → {AGENT_REGISTRY[chosen]['label']}")
        return {"current_agent": chosen}

    def route_after_triage(state: SwarmState) -> str:
        return state.get("current_agent", "researcher")

    def route_after_agent(state: SwarmState) -> str:
        cur = state.get("current_agent", "__done__")
        return cur if cur in AGENT_REGISTRY else "__done__"

    graph = StateGraph(SwarmState)
    graph.add_node("triage", triage_node)
    for key in AGENT_REGISTRY:
        graph.add_node(key, _build_swarm_node(key))
        graph.add_conditional_edges(
            key, route_after_agent,
            {**{k: k for k in AGENT_REGISTRY}, "__done__": END},
        )

    graph.add_edge(START, "triage")
    graph.add_conditional_edges(
        "triage", route_after_triage,
        {k: k for k in AGENT_REGISTRY},
    )
    return graph.compile()


# ============================================================
# 演示场景
# ============================================================

def print_banner(title: str):
    w = 68
    print("\n" + "=" * w)
    print(f"  {title}")
    print("=" * w)


def print_section(label: str):
    print(f"\n{'─' * 56}")
    print(f"  {label}")
    print(f"{'─' * 56}")


async def demo_supervisor():
    print_banner("模式一: Supervisor 多智能体")
    print("  Supervisor 根据用户意图将任务路由给专业 Agent，")
    print("  Agent 完成后交回 Supervisor 决定是否继续或结束。\n")

    app = build_supervisor_graph()

    scenarios = [
        ("搜索关于多智能体系统(multi-agent)的最新研究论文，并做简要总结", "跨领域调研"),
        ("帮我分析这组考试成绩: [85, 92, 78, 95, 88, 73, 91, 86, 79, 94]，给出统计报告和可视化", "数据分析"),
        ("写一个 Python 快速排序函数，执行测试并审查代码质量", "编码 + 审查"),
    ]

    for query, desc in scenarios:
        print_section(f"场景: {desc}")
        print(f"  用户: {query}\n")
        result = await app.ainvoke({
            "messages": [HumanMessage(content=query)],
            "next_agent": "",
            "iteration": 0,
        })
        final = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if final:
            print(f"\n  === 最终输出 ===\n{final[-1].content}\n")


async def demo_swarm():
    print_banner("模式二: Swarm / Handoff 多智能体")
    print("  入口分诊 Agent 判断首个处理者，Agent 之间可通过")
    print("  handoff 工具自行转交，无需中心化 Supervisor。\n")

    app = build_swarm_graph()

    scenarios = [
        ("帮我查找 RAG 相关的最新论文", "直接研究任务"),
        ("对数据 [120, 340, 89, 456, 230, 178, 392, 267, 145, 501] 做统计分析并画图表", "数据分析任务"),
    ]

    for query, desc in scenarios:
        print_section(f"场景: {desc}")
        print(f"  用户: {query}\n")
        result = await app.ainvoke({
            "messages": [HumanMessage(content=query)],
            "current_agent": "",
            "handoff_count": 0,
        })
        final = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if final:
            print(f"\n  === 最终输出 ===\n{final[-1].content}\n")


async def main():
    print(f"\n  LangGraph 多智能体系统 Demo")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  模型: {MODEL}\n")

    await demo_supervisor()
    await demo_swarm()

    print_banner("所有演示完成")


if __name__ == "__main__":
    asyncio.run(main())
