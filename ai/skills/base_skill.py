"""
Base Skill Definition

Provides the abstract base class and core types for all skills.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio


class SkillCategory(Enum):
    """Categories of skills"""
    DATA_PROCESSING = "data_processing"
    TEXT_ANALYSIS = "text_analysis"
    CODE_GENERATION = "code_generation"
    WEB_SCRAPING = "web_scraping"
    API_INTEGRATION = "api_integration"
    FILE_OPERATIONS = "file_operations"
    COMPUTATION = "computation"
    REASONING = "reasoning"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"


@dataclass
class SkillParameter:
    """Definition of a skill parameter"""
    name: str
    type: type
    description: str
    required: bool = True
    default: Any = None
    validator: Optional[Callable[[Any], bool]] = None

    def validate(self, value: Any) -> bool:
        """Validate parameter value"""
        # Type check
        if not isinstance(value, self.type):
            return False

        # Custom validator
        if self.validator and not self.validator(value):
            return False

        return True


@dataclass
class SkillMetadata:
    """Metadata about a skill"""
    name: str
    description: str
    category: SkillCategory
    version: str = "1.0.0"
    author: str = "Unknown"
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    parameters: List[SkillParameter] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "examples": self.examples,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.__name__,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "dependencies": self.dependencies
        }


@dataclass
class SkillContext:
    """Context for skill execution"""
    execution_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_execution_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    timeout: Optional[float] = None  # in seconds
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SkillResult:
    """Result of skill execution"""
    execution_id: str
    success: bool
    data: Any
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "execution_id": self.execution_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "logs": self.logs
        }


class BaseSkill(ABC):
    """
    Abstract base class for all skills.

    A skill is a reusable, composable unit of AI capability.
    Each skill should:
    1. Have clear metadata describing its purpose and parameters
    2. Implement execution logic
    3. Handle errors gracefully
    4. Support async execution
    5. Be composable with other skills
    """

    def __init__(self, metadata: SkillMetadata):
        """
        Initialize the skill.

        Args:
            metadata: Skill metadata
        """
        self.metadata = metadata
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_execution_time = 0.0
        self._is_initialized = False

    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute the skill with given parameters.

        Args:
            context: Execution context
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult containing execution result
        """
        pass

    async def initialize(self) -> None:
        """
        Initialize the skill (load models, connect to services, etc.).
        Override this method if initialization is needed.
        """
        self._is_initialized = True

    async def cleanup(self) -> None:
        """
        Cleanup resources (close connections, free memory, etc.).
        Override this method if cleanup is needed.
        """
        self._is_initialized = False

    def validate_parameters(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate input parameters against skill metadata.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        for param in self.metadata.parameters:
            # Check required parameters
            if param.required and param.name not in kwargs:
                return False, f"Required parameter '{param.name}' is missing"

            # Validate parameter value
            if param.name in kwargs:
                value = kwargs[param.name]
                if not param.validate(value):
                    return False, f"Invalid value for parameter '{param.name}'"

        return True, None

    async def execute_with_tracking(self, context: SkillContext, **kwargs) -> SkillResult:
        """
        Execute skill with automatic tracking, validation, and error handling.

        Args:
            context: Execution context
            **kwargs: Skill parameters

        Returns:
            SkillResult
        """
        # Initialize if needed
        if not self._is_initialized:
            await self.initialize()

        # Validate parameters
        is_valid, error_msg = self.validate_parameters(**kwargs)
        if not is_valid:
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error=error_msg,
                error_type="ValidationError"
            )

        # Track execution
        self._execution_count += 1
        start_time = asyncio.get_event_loop().time()

        try:
            # Execute with timeout if specified
            if context.timeout:
                result = await asyncio.wait_for(
                    self.execute(context, **kwargs),
                    timeout=context.timeout
                )
            else:
                result = await self.execute(context, **kwargs)

            # Update stats
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            self._total_execution_time += execution_time

            if result.success:
                self._success_count += 1
            else:
                self._failure_count += 1

            return result

        except asyncio.TimeoutError:
            self._failure_count += 1
            execution_time = asyncio.get_event_loop().time() - start_time
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error=f"Execution timeout after {context.timeout}s",
                error_type="TimeoutError",
                execution_time=execution_time
            )
        except Exception as e:
            self._failure_count += 1
            execution_time = asyncio.get_event_loop().time() - start_time
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error=str(e),
                error_type=type(e).__name__,
                execution_time=execution_time
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        avg_time = (
            self._total_execution_time / self._execution_count
            if self._execution_count > 0
            else 0
        )
        success_rate = (
            self._success_count / self._execution_count
            if self._execution_count > 0
            else 0
        )

        return {
            "skill_name": self.metadata.name,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": success_rate,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_time,
            "is_initialized": self._is_initialized
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.metadata.name}, category={self.metadata.category.value})>"
