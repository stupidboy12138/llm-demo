"""
A2UI配置文件
"""
from typing import Dict, Any
from pydantic import BaseModel


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    reload: bool = False


class LLMConfig(BaseModel):
    """LLM模型配置"""
    api_base: str = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
    api_key: str = "sk-deepbank-dev"
    model: str = "360/qwen3-32b"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    streaming: bool = True


class AgentConfig(BaseModel):
    """Agent配置"""
    request_timeout: float = 30.0
    max_retries: int = 3
    enable_history: bool = True
    max_history_length: int = 100
    context_window: int = 10  # 上下文窗口大小


class APIConfig(BaseModel):
    """API配置"""
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]


class Config(BaseModel):
    """总配置"""
    server: ServerConfig = ServerConfig()
    llm: LLMConfig = LLMConfig()
    agent: AgentConfig = AgentConfig()
    api: APIConfig = APIConfig()

    # 环境配置
    debug: bool = False
    environment: str = "development"

    # Agent启用配置
    enabled_agents: Dict[str, bool] = {
        "ai_assistant": True,
        "weather": True,
        "calculator": True,
        "task_coordinator": True
    }


# 默认配置
default_config = Config()


def load_config() -> Config:
    """加载配置"""
    # TODO: 从文件或环境变量加载配置
    return default_config
