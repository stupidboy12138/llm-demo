"""
具体Agent实现
使用消息代理的Agent实现
"""
from .base_agent import BaseAgent
from .protocol import A2AMessage
from .message_broker import MessageBroker
import asyncio
import logging

logger = logging.getLogger(__name__)


class BrokerAgent(BaseAgent):
    """使用MessageBroker的Agent实现"""

    def __init__(self, agent_id: str, name: str, broker: MessageBroker):
        super().__init__(agent_id, name)
        self.broker = broker
        self.message_queue = None
        self.receive_task = None

    async def send_message(self, message: A2AMessage):
        """通过broker发送消息"""
        await self.broker.route_message(message)

    async def start(self):
        """启动Agent"""
        if self.running:
            return

        self.running = True
        self.message_queue = self.broker.register_agent(self.agent_id)
        self.receive_task = asyncio.create_task(self._receive_loop())
        logger.info(f"[{self.name}] 已启动")

    async def stop(self):
        """停止Agent"""
        if not self.running:
            return

        self.running = False
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        self.broker.unregister_agent(self.agent_id)
        logger.info(f"[{self.name}] 已停止")

    async def _receive_loop(self):
        """消息接收循环"""
        while self.running:
            try:
                message = await self.message_queue.get()
                await self.handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.name}] 处理消息出错: {e}")
