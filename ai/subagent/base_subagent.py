"""
Base SubAgent Definition

Provides the abstract base class for all sub-agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime


class SubAgentCapability(Enum):
    """Enumeration of sub-agent capabilities"""
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    RESEARCH = "research"
    VALIDATION = "validation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


@dataclass
class TaskContext:
    """Context information for a task"""
    task_id: str
    task_type: str
    priority: int = 1  # 1-5, where 5 is highest
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    sub_results: List['TaskResult'] = field(default_factory=list)


class BaseSubAgent(ABC):
    """
    Abstract base class for all sub-agents.

    Each sub-agent should:
    1. Declare its capabilities
    2. Implement task execution logic
    3. Handle errors gracefully
    4. Provide status reporting
    """

    def __init__(self, agent_id: str, name: str, capabilities: List[SubAgentCapability]):
        """
        Initialize the sub-agent.

        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name
            capabilities: List of capabilities this agent provides
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self._active_tasks: Dict[str, TaskContext] = {}
        self._completed_tasks: List[str] = []
        self._is_busy = False

    @abstractmethod
    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        """
        Execute a task assigned to this sub-agent.

        Args:
            task: The task description or instruction
            context: Additional context for task execution

        Returns:
            TaskResult containing the execution result
        """
        pass

    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """
        Determine if this agent can handle the given task type.

        Args:
            task_type: The type of task to check

        Returns:
            True if this agent can handle the task
        """
        pass

    async def preprocess(self, task: str, context: TaskContext) -> Dict[str, Any]:
        """
        Preprocess the task before execution (can be overridden).

        Args:
            task: The task description
            context: Task context

        Returns:
            Preprocessed data
        """
        return {"task": task, "context": context}

    async def postprocess(self, result: TaskResult) -> TaskResult:
        """
        Postprocess the result after execution (can be overridden).

        Args:
            result: The raw task result

        Returns:
            Processed task result
        """
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this sub-agent"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": [cap.value for cap in self.capabilities],
            "is_busy": self._is_busy,
            "active_tasks": len(self._active_tasks),
            "completed_tasks": len(self._completed_tasks)
        }

    def has_capability(self, capability: SubAgentCapability) -> bool:
        """Check if this agent has a specific capability"""
        return capability in self.capabilities

    async def execute_with_tracking(self, task: str, context: TaskContext) -> TaskResult:
        """
        Execute task with tracking and error handling.

        Args:
            task: The task to execute
            context: Task context

        Returns:
            TaskResult
        """
        self._is_busy = True
        self._active_tasks[context.task_id] = context
        start_time = asyncio.get_event_loop().time()

        try:
            # Preprocess
            preprocessed = await self.preprocess(task, context)

            # Execute
            result = await self.execute_task(task, context)

            # Postprocess
            result = await self.postprocess(result)

            # Calculate execution time
            result.execution_time = asyncio.get_event_loop().time() - start_time

            return result

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            return TaskResult(
                task_id=context.task_id,
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time
            )
        finally:
            self._is_busy = False
            self._active_tasks.pop(context.task_id, None)
            self._completed_tasks.append(context.task_id)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name})>"
