"""
A2A协议核心定义
定义了Agent之间通信的消息格式和协议规范
"""
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from enum import Enum
import json
from datetime import datetime
import uuid


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class ActionType(Enum):
    """操作类型枚举"""
    QUERY = "query"
    COMMAND = "command"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class A2AMessage:
    """A2A协议消息格式"""
    message_id: str
    message_type: MessageType
    sender_id: str
    receiver_id: str
    timestamp: str
    action: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None  # 用于关联请求和响应

    @classmethod
    def create_request(cls, sender_id: str, receiver_id: str, action: str, payload: Dict[str, Any] = None):
        """创建请求消息"""
        return cls(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.REQUEST,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            payload=payload or {}
        )

    @classmethod
    def create_response(cls, sender_id: str, receiver_id: str, correlation_id: str, payload: Dict[str, Any] = None):
        """创建响应消息"""
        return cls(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.RESPONSE,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=datetime.now().isoformat(),
            payload=payload or {},
            correlation_id=correlation_id
        )

    @classmethod
    def create_notification(cls, sender_id: str, receiver_id: str, action: str, payload: Dict[str, Any] = None):
        """创建通知消息"""
        return cls(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.NOTIFICATION,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            payload=payload or {}
        )

    @classmethod
    def create_error(cls, sender_id: str, receiver_id: str, correlation_id: str, error_msg: str):
        """创建错误消息"""
        return cls(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ERROR,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=datetime.now().isoformat(),
            payload={"error": error_msg},
            correlation_id=correlation_id
        )

    def to_json(self) -> str:
        """转换为JSON字符串"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'A2AMessage':
        """从JSON字符串解析"""
        data = json.loads(json_str)
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)
