"""
FastAPI服务器 - 提供RESTful API和WebSocket接口
支持流式响应和A2UI协议
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import logging
import json
from pathlib import Path

from a2a.message_broker import MessageBroker
from ai.a2ui.config import default_config
from ai.a2ui.demo_agents import AIAssistantAgent, CalculatorAgent, WeatherAgent, TaskCoordinatorAgent
from ai.a2ui.web_agent import WebAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A2UI Demo", description="Agent to UI Interface - 真实LLM集成", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
broker: Optional[MessageBroker] = None
web_agent: Optional[WebAgent] = None
ai_agent: Optional[AIAssistantAgent] = None
weather_agent: Optional[WeatherAgent] = None
calculator_agent: Optional[CalculatorAgent] = None
coordinator_agent: Optional[TaskCoordinatorAgent] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    agent_type: Optional[str] = "ai_assistant"
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    agent: str
    model: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    global broker, web_agent, ai_agent, weather_agent, calculator_agent, coordinator_agent

    logger.info("初始化A2UI系统（真实LLM模式）...")
    logger.info(f"使用模型: {default_config.llm.model}")

    broker = MessageBroker()

    web_agent = WebAgent("web_agent", broker)
    await web_agent.start()

    ai_agent = AIAssistantAgent("ai_assistant", broker)
    await ai_agent.start()

    weather_agent = WeatherAgent("weather_agent", broker)
    await weather_agent.start()

    calculator_agent = CalculatorAgent("calculator_agent", broker)
    await calculator_agent.start()

    coordinator_agent = TaskCoordinatorAgent("task_coordinator", broker)
    await coordinator_agent.start()

    logger.info("A2UI系统启动完成!")


@app.on_event("shutdown")
async def shutdown_event():
    global web_agent, ai_agent, weather_agent, calculator_agent, coordinator_agent
    logger.info("关闭A2UI系统...")
    for agent in [web_agent, ai_agent, weather_agent, calculator_agent, coordinator_agent]:
        if agent:
            await agent.stop()


@app.get("/", response_class=HTMLResponse)
async def root():
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse("<h1>A2UI Demo</h1><p>访问 <a href='/docs'>/docs</a> 查看API</p>")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": default_config.llm.model,
        "agents": {
            "ai_assistant": ai_agent is not None,
            "weather": weather_agent is not None,
            "calculator": calculator_agent is not None,
            "coordinator": coordinator_agent is not None
        }
    }


@app.get("/agents")
async def list_agents():
    return [
        {"id": "ai_assistant", "name": "AI智能助手", "description": "使用真实LLM进行智能对话", "icon": "🤖"},
        {"id": "weather", "name": "天气查询", "description": "查询城市天气信息", "icon": "🌤️"},
        {"id": "calculator", "name": "计算器", "description": "执行数学计算", "icon": "🔢"},
        {"id": "coordinator", "name": "任务协调", "description": "智能任务分解和协调", "icon": "📋"},
    ]


@app.post("/chat")
async def chat(request: ChatRequest):
    if not web_agent:
        raise HTTPException(status_code=503, detail="系统未初始化")

    try:
        # 路由到对应Agent
        agent_map = {
            "ai_assistant": ("ai_assistant", "chat"),
            "weather": ("weather_agent", "query"),
            "calculator": ("calculator_agent", "calculate"),
            "coordinator": ("task_coordinator", "coordinate"),
        }

        if request.agent_type not in agent_map:
            raise HTTPException(status_code=400, detail=f"未知Agent: {request.agent_type}")

        target_agent, action = agent_map[request.agent_type]

        response = await web_agent.forward_to_agent(
            target_agent,
            action,
            {"message": request.message, "session_id": request.session_id}
        )

        if "error" in response and response.get("error") is True:
            raise HTTPException(status_code=500, detail=response.get("response", "处理失败"))

        return ChatResponse(
            response=response.get("response", str(response)),
            session_id=request.session_id,
            timestamp=response.get("timestamp", ""),
            agent=request.agent_type,
            model=response.get("model")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天响应"""
    if not ai_agent:
        raise HTTPException(status_code=503, detail="系统未初始化")

    async def generate():
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = ai_agent._build_message_history(request.session_id, request.message)

            yield f"data: {json.dumps({'type': 'start', 'session_id': request.session_id})}\n\n"

            full_response = ""
            for chunk in ai_agent.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"

            ai_agent._save_to_context(request.session_id, request.message, full_response)

            yield f"data: {json.dumps({'type': 'end', 'full_response': full_response})}\n\n"

        except Exception as e:
            logger.error(f"流式生成错误: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    if ai_agent and session_id in ai_agent.conversation_context:
        history = ai_agent.conversation_context[session_id]
        return {"history": history, "session_id": session_id, "count": len(history)}
    return {"history": [], "session_id": session_id, "count": 0}


@app.delete("/history/{session_id}")
async def clear_history(session_id: str):
    if ai_agent and session_id in ai_agent.conversation_context:
        del ai_agent.conversation_context[session_id]
    return {"success": True, "message": "历史已清除"}


# WebSocket
class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, client_id: str):
        await ws.accept()
        self.connections[client_id] = ws

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)

    async def send(self, data: dict, client_id: str):
        if client_id in self.connections:
            await self.connections[client_id].send_json(data)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                user_msg = data.get("message", "")
                agent_type = data.get("agent_type", "ai_assistant")
                stream = data.get("stream", False)

                await manager.send({"type": "ack"}, client_id)

                if stream and agent_type == "ai_assistant" and ai_agent:
                    # 流式响应
                    messages = ai_agent._build_message_history(client_id, user_msg)
                    full_response = ""

                    await manager.send({"type": "stream_start"}, client_id)

                    for chunk in ai_agent.llm.stream(messages):
                        if hasattr(chunk, 'content') and chunk.content:
                            full_response += chunk.content
                            await manager.send({"type": "stream_chunk", "content": chunk.content}, client_id)

                    ai_agent._save_to_context(client_id, user_msg, full_response)
                    await manager.send({"type": "stream_end", "full_response": full_response}, client_id)

                else:
                    # 非流式响应
                    agent_map = {
                        "ai_assistant": ("ai_assistant", "chat"),
                        "weather": ("weather_agent", "query"),
                        "calculator": ("calculator_agent", "calculate"),
                        "coordinator": ("task_coordinator", "coordinate"),
                    }

                    if agent_type in agent_map and web_agent:
                        target, action = agent_map[agent_type]
                        response = await web_agent.forward_to_agent(
                            target, action,
                            {"message": user_msg, "session_id": client_id}
                        )
                        await manager.send({
                            "type": "response",
                            "message": response.get("response", str(response)),
                            "agent": agent_type
                        }, client_id)

            elif msg_type == "ping":
                await manager.send({"type": "pong"}, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
