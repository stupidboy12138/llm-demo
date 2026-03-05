"""
消息代理
负责在多个Agent之间路由和分发消息
"""
from typing import Dict
from .protocol import A2AMessage
import asyncio
import logging

logger = logging.getLogger(__name__)


class MessageBroker:
    """消息代理 - 负责Agent之间的消息路由"""

    def __init__(self):
        self.agents: Dict[str, asyncio.Queue] = {}

    def register_agent(self, agent_id: str) -> asyncio.Queue:
        """注册Agent并返回其消息队列"""
        if agent_id not in self.agents:
            self.agents[agent_id] = asyncio.Queue()
            logger.info(f"[Broker] 注册Agent: {agent_id}")
        return self.agents[agent_id]

    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"[Broker] 注销Agent: {agent_id}")

    async def route_message(self, message: A2AMessage):
        """路由消息到目标Agent"""
        receiver_id = message.receiver_id

        if receiver_id in self.agents:
            await self.agents[receiver_id].put(message)
            logger.info(f"[Broker] 路由消息: {message.sender_id} -> {receiver_id}")
        else:
            logger.warning(f"[Broker] 目标Agent不存在: {receiver_id}")

    async def broadcast_message(self, message: A2AMessage, exclude_sender: bool = True):
        """广播消息给所有Agent"""
        for agent_id, queue in self.agents.items():
            if exclude_sender and agent_id == message.sender_id:
                continue
            await queue.put(message)
        logger.info(f"[Broker] 广播消息: {message.sender_id} -> 所有Agent")
