"""
SubAgent Architecture Module

This module provides a hierarchical agent architecture where a coordinator agent
can delegate specialized tasks to multiple sub-agents.
"""

from .base_subagent import BaseSubAgent, SubAgentCapability
from .coordinator_agent import CoordinatorAgent
from .subagent_registry import SubAgentRegistry
from .specialized_agents import (
    DataAnalysisSubAgent,
    CodeGenerationSubAgent,
    ResearchSubAgent,
    ValidationSubAgent
)

__all__ = [
    'BaseSubAgent',
    'SubAgentCapability',
    'CoordinatorAgent',
    'SubAgentRegistry',
    'DataAnalysisSubAgent',
    'CodeGenerationSubAgent',
    'ResearchSubAgent',
    'ValidationSubAgent'
]
