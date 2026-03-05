"""
A2UI - Agent to UI Interface
将A2A协议的Agent能力通过Web UI暴露给用户
使用真实LLM模型进行智能对话
"""
from .config import default_config, Config, LLMConfig
from .demo import main

__all__ = ["default_config", "Config", "LLMConfig", "main"]
