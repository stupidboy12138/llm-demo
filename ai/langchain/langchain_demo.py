"""
基于LangChain的Agent Demo
使用LiteLLM API作为模型后端
封装为高性能异步FastAPI服务
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
import uvicorn


# ============ 配置部分 ============
LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-deepbank-dev"


# ============ Pydantic模型定义 ============
class MessageInput(BaseModel):
    """消息输入模型"""
    role: str = Field(..., description="消息角色: user, assistant, system")
    content: str = Field(..., description="消息内容")


class AgentRequest(BaseModel):
    """Agent请求模型"""
    message: str = Field(..., description="用户输入的消息")
    history: Optional[List[MessageInput]] = Field(default=None, description="历史对话记录")
    stream: bool = Field(default=False, description="是否流式返回")


class AgentResponse(BaseModel):
    """Agent响应模型"""
    message: str = Field(..., description="Agent的回复")
    intermediate_steps: List[Dict[str, Any]] = Field(default=[], description="中间步骤")
    execution_time: float = Field(..., description="执行时间（秒）")


# ============ 工具定义 ============
@tool
def get_current_time(query: str = "") -> str:
    """获取当前时间的工具。当需要知道当前日期和时间时使用此工具。"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"当前时间是: {current_time}"


@tool
def calculate_math(expression: str) -> str:
    """计算数学表达式的工具。当需要进行数学计算时使用此工具。输入应该是一个数学表达式，例如: '2+2' 或 '10*5'。"""
    try:
        # 安全的数学表达式计算
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "错误: 表达式包含不允许的字符"
        
        result = eval(expression, {"__builtins__": {}}, {})
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def search_knowledge(query: str) -> str:
    """知识库搜索工具。当需要搜索特定知识或信息时使用此工具。输入应该是你想要搜索的关键词或问题。"""
    knowledge_base = {
        "python": "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。",
        "langchain": "LangChain是一个用于开发由语言模型驱动的应用程序的框架。",
        "fastapi": "FastAPI是一个现代、快速的Web框架，用于构建API。",
        "agent": "Agent是能够感知环境并采取行动以实现目标的自主实体。",
    }
    
    query_lower = query.lower()
    for key, value in knowledge_base.items():
        if key in query_lower:
            return f"找到相关信息: {value}"
    
    return "未找到相关信息，这是一个模拟的知识库。"


# 创建工具列表
tools = [get_current_time, calculate_math, search_knowledge]


# ============ Agent类 ============
class LangChainAgent:
    """LangChain Agent封装类"""
    
    def __init__(self):
        """初始化Agent"""
        # 配置LiteLLM模型（使用OpenAI兼容接口）
        self.llm = ChatOpenAI(
            model="deepseek-r1-0528",  # 根据LiteLLM实际支持的模型调整
            openai_api_base=LITELLM_API_BASE,
            openai_api_key=LITELLM_API_KEY,
            temperature=0.7,
            streaming=True,
        )
        
        # 系统提示词
        self.system_prompt = """你是一个智能助手，能够使用各种工具来帮助用户解决问题。

你有以下能力：
1. 获取当前时间
2. 进行数学计算
3. 搜索知识库

请根据用户的需求，选择合适的工具来完成任务。如果不需要使用工具，可以直接回答。
请用简洁、友好的方式与用户交流。"""
        
        # 创建内存保存器
        self.memory = MemorySaver()
        
        # 使用 LangGraph 创建 ReAct agent
        self.agent = create_agent(
            self.llm,
            tools,
            system_prompt=self.system_prompt,
            checkpointer=self.memory
        )
    
    async def ainvoke(
        self, 
        message: str, 
        history: Optional[List[MessageInput]] = None,
        thread_id: str = "default"
    ) -> Dict[str, Any]:
        """异步调用Agent"""
        # 构建消息列表
        messages = []
        
        # 添加历史记录
        if history:
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    messages.append(SystemMessage(content=msg.content))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))
        
        # 配置线程ID
        config = {"configurable": {"thread_id": thread_id}}
        
        # 执行agent
        result = await self.agent.ainvoke(
            {"messages": messages},
            config=config
        )
        
        # 提取输出
        output_message = ""
        if result and "messages" in result:
            last_message = result["messages"][-1]
            output_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        return {
            "output": output_message,
            "messages": result.get("messages", []),
        }
    
    async def astream(
        self, 
        message: str, 
        history: Optional[List[MessageInput]] = None,
        thread_id: str = "default"
    ):
        """异步流式调用Agent"""
        # 构建消息列表
        messages = []
        
        # 添加历史记录
        if history:
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    messages.append(SystemMessage(content=msg.content))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))
        
        # 配置线程ID
        config = {"configurable": {"thread_id": thread_id}}
        
        # 流式执行agent
        async for event in self.agent.astream_events(
            {"messages": messages},
            config=config,
            version="v2"
        ):
            yield event


# ============ FastAPI应用 ============
app = FastAPI(
    title="LangChain Agent API",
    description="基于LangChain和LiteLLM的高性能异步Agent服务",
    version="1.0.0",
)

# 全局agent实例
agent = LangChainAgent()

@app.post("/agent/chat", response_model=AgentResponse)
async def chat(request: AgentRequest):
    """
    与Agent对话（非流式）
    
    - **message**: 用户输入的消息
    - **history**: 历史对话记录（可选）
    - **stream**: 是否流式返回（此端点固定为False）
    """
    if request.stream:
        raise HTTPException(
            status_code=400, 
            detail="此端点不支持流式返回，请使用 /agent/chat-stream"
        )
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # 调用agent
        result = await agent.ainvoke(
            message=request.message,
            history=request.history,
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        # 提取中间步骤（从消息列表中提取工具调用）
        intermediate_steps = []
        if "messages" in result:
            for msg in result["messages"]:
                # 检查是否是工具消息
                if hasattr(msg, 'type'):
                    if msg.type == 'tool':
                        intermediate_steps.append({
                            "tool": msg.name if hasattr(msg, 'name') else "unknown",
                            "tool_input": {},
                            "output": msg.content if hasattr(msg, 'content') else str(msg),
                        })
                    elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            intermediate_steps.append({
                                "tool": tool_call.get('name', 'unknown'),
                                "tool_input": tool_call.get('args', {}),
                                "output": "",
                            })
        
        return AgentResponse(
            message=result.get("output", ""),
            intermediate_steps=intermediate_steps,
            execution_time=execution_time,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent执行错误: {str(e)}")


@app.post("/agent/chat-stream")
async def chat_stream(request: AgentRequest):
    """
    与Agent对话（流式）
    
    - **message**: 用户输入的消息
    - **history**: 历史对话记录（可选）
    - **stream**: 是否流式返回（此端点固定为True）
    """
    
    async def event_generator():
        """事件生成器"""
        try:
            async for event in agent.astream(
                message=request.message,
                history=request.history,
            ):
                # 过滤并格式化事件
                event_kind = event.get("event")
                
                if event_kind == "on_chat_model_stream":
                    # LLM输出流
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        content = chunk.content
                        if content:
                            yield f"data: {json.dumps({'type': 'content', 'data': content}, ensure_ascii=False)}\n\n"
                
                elif event_kind == "on_tool_start":
                    # 工具开始执行
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'input': tool_input}, ensure_ascii=False)}\n\n"
                
                elif event_kind == "on_tool_end":
                    # 工具执行完成
                    tool_name = event.get("name", "unknown")
                    output = event.get("data", {}).get("output", "")
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'output': str(output)}, ensure_ascii=False)}\n\n"
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/agent/batch")
async def batch_chat(requests: List[AgentRequest]):
    """
    批量处理请求（异步并发）
    
    - **requests**: 多个Agent请求
    """
    if len(requests) > 10:
        raise HTTPException(
            status_code=400, 
            detail="批量请求数量不能超过10个"
        )
    
    try:
        # 创建异步任务列表
        tasks = [
            agent.ainvoke(message=req.message, history=req.history)
            for req in requests
        ]
        
        # 并发执行所有任务
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # 处理结果
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                responses.append({
                    "index": i,
                    "success": False,
                    "error": str(result),
                })
            else:
                responses.append({
                    "index": i,
                    "success": True,
                    "message": result.get("output", ""),
                })
        
        return {
            "total": len(requests),
            "execution_time": end_time - start_time,
            "results": responses,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量处理错误: {str(e)}")


# ============ 主函数 ============
if __name__ == "__main__":
    # 启动FastAPI服务
    uvicorn.run(
        "langchain_demo:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1,  # 开发环境使用1个worker，生产环境可以增加
    )

