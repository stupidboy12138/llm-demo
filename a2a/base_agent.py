"""
基础Agent类
提供Agent的基本功能和消息处理能力
"""
from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional
from .protocol import A2AMessage, MessageType
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.running = False

    def register_handler(self, action: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[action] = handler
        logger.info(f"[{self.name}] 注册处理器: {action}")

    async def send_message(self, message: A2AMessage):
        """发送消息 - 子类需要实现具体的发送逻辑"""
        raise NotImplementedError

    async def send_request(self, receiver_id: str, action: str, payload: Dict = None, timeout: float = 10.0):
        """发送请求并等待响应"""
        message = A2AMessage.create_request(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            action=action,
            payload=payload
        )

        # 创建一个Future来等待响应
        future = asyncio.Future()
        self.pending_responses[message.message_id] = future

        logger.info(f"[{self.name}] 发送请求: {action} -> {receiver_id}")
        await self.send_message(message)

        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"[{self.name}] 请求超时: {action}")
            del self.pending_responses[message.message_id]
            raise

    async def send_response(self, original_message: A2AMessage, payload: Dict = None):
        """发送响应消息"""
        response = A2AMessage.create_response(
            sender_id=self.agent_id,
            receiver_id=original_message.sender_id,
            correlation_id=original_message.message_id,
            payload=payload
        )
        logger.info(f"[{self.name}] 发送响应 -> {original_message.sender_id}")
        await self.send_message(response)

    async def send_notification(self, receiver_id: str, action: str, payload: Dict = None):
        """发送通知消息"""
        notification = A2AMessage.create_notification(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            action=action,
            payload=payload
        )
        logger.info(f"[{self.name}] 发送通知: {action} -> {receiver_id}")
        await self.send_message(notification)

    async def handle_message(self, message: A2AMessage):
        """处理接收到的消息"""
        logger.info(f"[{self.name}] 收到消息: {message.message_type.value} from {message.sender_id}")

        if message.message_type == MessageType.REQUEST:
            await self._handle_request(message)
        elif message.message_type == MessageType.RESPONSE:
            await self._handle_response(message)
        elif message.message_type == MessageType.NOTIFICATION:
            await self._handle_notification(message)
        elif message.message_type == MessageType.ERROR:
            await self._handle_error(message)

    async def _handle_request(self, message: A2AMessage):
        """处理请求消息"""
        if message.action in self.message_handlers:
            handler = self.message_handlers[message.action]
            try:
                result = await handler(message)
                await self.send_response(message, result)
            except Exception as e:
                logger.error(f"[{self.name}] 处理请求失败: {e}")
                error_msg = A2AMessage.create_error(
                    sender_id=self.agent_id,
                    receiver_id=message.sender_id,
                    correlation_id=message.message_id,
                    error_msg=str(e)
                )
                await self.send_message(error_msg)
        else:
            logger.warning(f"[{self.name}] 未找到处理器: {message.action}")

    async def _handle_response(self, message: A2AMessage):
        """处理响应消息"""
        if message.correlation_id in self.pending_responses:
            future = self.pending_responses[message.correlation_id]
            future.set_result(message.payload)
            del self.pending_responses[message.correlation_id]

    async def _handle_notification(self, message: A2AMessage):
        """处理通知消息"""
        if message.action in self.message_handlers:
            handler = self.message_handlers[message.action]
            await handler(message)

    async def _handle_error(self, message: A2AMessage):
        """处理错误消息"""
        if message.correlation_id in self.pending_responses:
            future = self.pending_responses[message.correlation_id]
            error_msg = message.payload.get('error', 'Unknown error')
            future.set_exception(Exception(error_msg))
            del self.pending_responses[message.correlation_id]

    @abstractmethod
    async def start(self):
        """启动Agent"""
        pass

    @abstractmethod
    async def stop(self):
        """停止Agent"""
        pass
