"""
Specialized Sub-Agent Implementations

Contains concrete implementations of various specialized sub-agents.
"""

import asyncio
import json
import re
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .base_subagent import (
    BaseSubAgent,
    SubAgentCapability,
    TaskContext,
    TaskResult
)


class DataAnalysisSubAgent(BaseSubAgent):
    """
    Sub-agent specialized in data analysis tasks.

    Capabilities:
    - Statistical analysis
    - Data summarization
    - Pattern detection
    - Trend analysis
    """

    def __init__(self, agent_id: str = "data_analyst", api_base: str = None, api_key: str = None):
        super().__init__(
            agent_id=agent_id,
            name="Data Analysis Agent",
            capabilities=[SubAgentCapability.DATA_ANALYSIS]
        )
        self.llm = ChatOpenAI(
            model="360/qwen3-32b",
            temperature=0.1,
            base_url=api_base or "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1",
            api_key=api_key or "sk-deepbank-dev"
        )

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the task type"""
        data_tasks = ["analyze", "statistics", "summary", "trend", "pattern", "correlation"]
        return any(keyword in task_type.lower() for keyword in data_tasks)

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        """Execute data analysis task"""
        system_prompt = """You are a data analysis expert. Analyze the given data or question
        and provide insights, statistics, and actionable conclusions.
        Return your response in JSON format with keys: analysis, insights, recommendations."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task)
            ]

            response = await self.llm.ainvoke(messages)

            # Try to parse as JSON, fallback to structured text
            try:
                result_data = json.loads(response.content)
            except json.JSONDecodeError:
                result_data = {
                    "analysis": response.content,
                    "insights": [],
                    "recommendations": []
                }

            return TaskResult(
                task_id=context.task_id,
                success=True,
                data=result_data,
                metadata={"agent": self.agent_id, "model": "360/qwen3-32b"}
            )

        except Exception as e:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                data=None,
                error=f"Analysis failed: {str(e)}"
            )


class CodeGenerationSubAgent(BaseSubAgent):
    """
    Sub-agent specialized in code generation and modification.

    Capabilities:
    - Code generation
    - Code refactoring
    - Bug fixing
    - Code review
    """

    def __init__(self, agent_id: str = "code_generator", api_base: str = None, api_key: str = None):
        super().__init__(
            agent_id=agent_id,
            name="Code Generation Agent",
            capabilities=[SubAgentCapability.CODE_GENERATION]
        )
        self.llm = ChatOpenAI(
            model="360/qwen3-32b",
            temperature=0.2,
            base_url=api_base or "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1",
            api_key=api_key or "sk-deepbank-dev"
        )

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the task type"""
        code_tasks = ["code", "generate", "implement", "refactor", "fix", "bug", "function", "class"]
        return any(keyword in task_type.lower() for keyword in code_tasks)

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        """Execute code generation task"""
        system_prompt = """You are an expert software engineer. Generate high-quality,
        well-documented code based on the requirements. Follow best practices and include
        error handling. Return response in JSON format with keys: code, language, explanation, tests."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task)
            ]

            response = await self.llm.ainvoke(messages)

            # Extract code blocks
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', response.content, re.DOTALL)

            result_data = {
                "code": code_blocks[0][1].strip() if code_blocks else response.content,
                "language": code_blocks[0][0] if code_blocks else "python",
                "explanation": response.content,
                "tests": []
            }

            return TaskResult(
                task_id=context.task_id,
                success=True,
                data=result_data,
                metadata={"agent": self.agent_id, "language": result_data["language"]}
            )

        except Exception as e:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                data=None,
                error=f"Code generation failed: {str(e)}"
            )


class ResearchSubAgent(BaseSubAgent):
    """
    Sub-agent specialized in research and information gathering.

    Capabilities:
    - Information synthesis
    - Literature review
    - Fact checking
    - Knowledge extraction
    """

    def __init__(self, agent_id: str = "researcher", api_base: str = None, api_key: str = None):
        super().__init__(
            agent_id=agent_id,
            name="Research Agent",
            capabilities=[SubAgentCapability.RESEARCH, SubAgentCapability.SUMMARIZATION]
        )
        self.llm = ChatOpenAI(
            model="360/qwen3-32b",
            temperature=0.3,
            base_url=api_base or "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1",
            api_key=api_key or "sk-deepbank-dev"
        )

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the task type"""
        research_tasks = ["research", "investigate", "find", "search", "summarize", "explain", "learn"]
        return any(keyword in task_type.lower() for keyword in research_tasks)

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        """Execute research task"""
        system_prompt = """You are a research expert. Provide comprehensive, well-researched
        answers with citations and sources when possible. Structure your response with clear
        sections: summary, detailed_findings, key_points, sources."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task)
            ]

            response = await self.llm.ainvoke(messages)

            result_data = {
                "summary": response.content[:200],
                "detailed_findings": response.content,
                "key_points": self._extract_key_points(response.content),
                "sources": []
            }

            return TaskResult(
                task_id=context.task_id,
                success=True,
                data=result_data,
                metadata={"agent": self.agent_id, "word_count": len(response.content.split())}
            )

        except Exception as e:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                data=None,
                error=f"Research failed: {str(e)}"
            )

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text"""
        lines = text.split('\n')
        key_points = []
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '•')) or re.match(r'^\d+\.', line):
                key_points.append(line.lstrip('-*•').strip())
        return key_points[:5]  # Return top 5


class ValidationSubAgent(BaseSubAgent):
    """
    Sub-agent specialized in validation and quality checking.

    Capabilities:
    - Output validation
    - Quality assurance
    - Consistency checking
    - Error detection
    """

    def __init__(self, agent_id: str = "validator", api_base: str = None, api_key: str = None):
        super().__init__(
            agent_id=agent_id,
            name="Validation Agent",
            capabilities=[SubAgentCapability.VALIDATION]
        )
        self.llm = ChatOpenAI(
            model="360/qwen3-32b",
            temperature=0,
            base_url=api_base or "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1",
            api_key=api_key or "sk-deepbank-dev"
        )

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the task type"""
        validation_tasks = ["validate", "verify", "check", "review", "quality", "test"]
        return any(keyword in task_type.lower() for keyword in validation_tasks)

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        """Execute validation task"""
        system_prompt = """You are a quality assurance expert. Validate the given content
        for correctness, completeness, and quality. Return JSON with keys:
        is_valid, validation_score (0-100), issues, suggestions."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Validate the following:\n{task}")
            ]

            response = await self.llm.ainvoke(messages)

            # Try to parse as JSON
            try:
                result_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback structure
                result_data = {
                    "is_valid": "error" not in response.content.lower(),
                    "validation_score": 70,
                    "issues": [],
                    "suggestions": [response.content]
                }

            return TaskResult(
                task_id=context.task_id,
                success=True,
                data=result_data,
                metadata={"agent": self.agent_id}
            )

        except Exception as e:
            return TaskResult(
                task_id=context.task_id,
                success=False,
                data=None,
                error=f"Validation failed: {str(e)}"
            )
