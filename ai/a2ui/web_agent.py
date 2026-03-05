"""
WebAgent - 连接Web界面和A2A协议的桥梁
负责处理HTTP请求并转换为A2A消息
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import logging

from a2a.protocol import A2AMessage, MessageType
from a2a.message_broker import MessageBroker
from a2a.agent_impl import BrokerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebAgent(BrokerAgent):
    """Web界面代理 - 处理来自Web的请求"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "WebAgent", broker)
        self.conversation_history: Dict[str, List[Dict]] = {}

        # 注册处理器
        self.register_handler("chat", self.handle_chat)
        self.register_handler("get_history", self.handle_get_history)
        self.register_handler("clear_history", self.handle_clear_history)

    async def handle_chat(self, message: A2AMessage) -> Dict:
        """处理聊天请求"""
        user_input = message.payload.get("message", "")
        session_id = message.payload.get("session_id", "default")

        # 保存用户消息到历史
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []

        self.conversation_history[session_id].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"[WebAgent] 处理聊天请求: {user_input[:50]}...")

        # 这里可以路由到不同的Agent处理
        # 示例：转发给AI助手Agent
        response_text = f"收到消息: {user_input}"

        # 保存助手响应到历史
        self.conversation_history[session_id].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "response": response_text,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_get_history(self, message: A2AMessage) -> Dict:
        """获取会话历史"""
        session_id = message.payload.get("session_id", "default")
        history = self.conversation_history.get(session_id, [])

        return {
            "history": history,
            "session_id": session_id,
            "count": len(history)
        }

    async def handle_clear_history(self, message: A2AMessage) -> Dict:
        """清除会话历史"""
        session_id = message.payload.get("session_id", "default")

        if session_id in self.conversation_history:
            del self.conversation_history[session_id]

        return {
            "success": True,
            "session_id": session_id,
            "message": "历史已清除"
        }

    async def forward_to_agent(self, target_agent: str, action: str, payload: Dict) -> Dict:
        """转发请求到其他Agent"""
        try:
            response = await self.send_request(target_agent, action, payload)
            return response
        except Exception as e:
            logger.error(f"[WebAgent] 转发失败: {e}")
            return {"error": str(e)}
