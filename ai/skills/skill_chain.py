"""
Skill Chain

Enables composition and sequential execution of skills.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from .base_skill import SkillContext, SkillResult
from .skill_executor import SkillExecutor
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChainStep:
    """A step in a skill chain"""
    skill_name: str
    parameters: Dict[str, Any]
    transform_input: Optional[Callable[[Any], Dict[str, Any]]] = None
    transform_output: Optional[Callable[[Any], Any]] = None
    condition: Optional[Callable[[Any], bool]] = None  # Skip if returns False
    on_error: Optional[str] = None  # 'continue', 'stop', or 'retry'


class SkillChain:
    """
    Chain multiple skills together for sequential execution.

    Features:
    - Sequential skill execution
    - Data transformation between steps
    - Conditional execution
    - Error handling strategies
    - Result aggregation
    """

    def __init__(self, executor: SkillExecutor, name: str = "UnnamedChain"):
        """
        Initialize skill chain.

        Args:
            executor: Skill executor
            name: Chain name
        """
        self.executor = executor
        self.name = name
        self.steps: List[ChainStep] = []
        self._execution_log: List[Dict[str, Any]] = []

    def add_step(
        self,
        skill_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        transform_input: Optional[Callable[[Any], Dict[str, Any]]] = None,
        transform_output: Optional[Callable[[Any], Any]] = None,
        condition: Optional[Callable[[Any], bool]] = None,
        on_error: str = "stop"
    ) -> 'SkillChain':
        """
        Add a step to the chain.

        Args:
            skill_name: Name of the skill to execute
            parameters: Static parameters for the skill
            transform_input: Function to transform previous output to skill parameters
            transform_output: Function to transform skill output
            condition: Function to determine if step should execute
            on_error: Error handling strategy ('continue', 'stop', 'retry')

        Returns:
            Self for chaining
        """
        step = ChainStep(
            skill_name=skill_name,
            parameters=parameters or {},
            transform_input=transform_input,
            transform_output=transform_output,
            condition=condition,
            on_error=on_error
        )
        self.steps.append(step)
        return self

    async def execute(
        self,
        initial_input: Any = None,
        context: Optional[SkillContext] = None
    ) -> SkillResult:
        """
        Execute the entire chain.

        Args:
            initial_input: Initial input to the chain
            context: Execution context

        Returns:
            Final SkillResult
        """
        if not self.steps:
            return SkillResult(
                execution_id=str(uuid.uuid4()),
                success=False,
                data=None,
                error="Chain has no steps"
            )

        # Create context if not provided
        if context is None:
            context = SkillContext(execution_id=str(uuid.uuid4()))

        chain_execution_id = context.execution_id
        current_output = initial_input
        step_results = []

        logger.info(f"Starting chain execution: {self.name}")

        for i, step in enumerate(self.steps):
            step_name = f"{self.name}.step_{i}.{step.skill_name}"

            # Check condition
            if step.condition and not step.condition(current_output):
                logger.info(f"Skipping step {step_name} (condition not met)")
                continue

            # Prepare parameters
            params = step.parameters.copy()

            # Transform input if function provided
            if step.transform_input and current_output is not None:
                try:
                    transformed = step.transform_input(current_output)
                    params.update(transformed)
                except Exception as e:
                    logger.error(f"Error transforming input for {step_name}: {e}")
                    if step.on_error == "stop":
                        return SkillResult(
                            execution_id=chain_execution_id,
                            success=False,
                            data=None,
                            error=f"Input transformation failed: {e}",
                            metadata={"step": i, "step_results": step_results}
                        )
                    elif step.on_error == "continue":
                        continue

            # Create step context
            step_context = SkillContext(
                execution_id=f"{chain_execution_id}.step_{i}",
                parent_execution_id=chain_execution_id,
                metadata={"chain_name": self.name, "step_index": i}
            )

            # Execute skill
            logger.info(f"Executing step {step_name}")
            result = await self.executor.execute(
                step.skill_name,
                context=step_context,
                **params
            )

            # Log step execution
            self._execution_log.append({
                "step": i,
                "skill_name": step.skill_name,
                "success": result.success,
                "execution_time": result.execution_time,
                "error": result.error
            })

            step_results.append(result)

            # Handle errors
            if not result.success:
                logger.warning(f"Step {step_name} failed: {result.error}")

                if step.on_error == "stop":
                    return SkillResult(
                        execution_id=chain_execution_id,
                        success=False,
                        data=None,
                        error=f"Chain stopped at step {i}: {result.error}",
                        metadata={
                            "step": i,
                            "step_results": [r.to_dict() for r in step_results]
                        }
                    )
                elif step.on_error == "continue":
                    logger.info(f"Continuing despite error in {step_name}")
                    continue
                elif step.on_error == "retry":
                    # Simple retry logic (could be enhanced)
                    logger.info(f"Retrying {step_name}")
                    result = await self.executor.execute(
                        step.skill_name,
                        context=step_context,
                        **params
                    )
                    if not result.success:
                        return SkillResult(
                            execution_id=chain_execution_id,
                            success=False,
                            data=None,
                            error=f"Chain stopped at step {i} after retry: {result.error}",
                            metadata={
                                "step": i,
                                "step_results": [r.to_dict() for r in step_results]
                            }
                        )

            # Transform output
            current_output = result.data
            if step.transform_output:
                try:
                    current_output = step.transform_output(current_output)
                except Exception as e:
                    logger.error(f"Error transforming output for {step_name}: {e}")

        # Calculate total execution time
        total_time = sum(r.execution_time for r in step_results)

        logger.info(f"Chain execution completed: {self.name}")

        return SkillResult(
            execution_id=chain_execution_id,
            success=True,
            data=current_output,
            execution_time=total_time,
            metadata={
                "chain_name": self.name,
                "total_steps": len(self.steps),
                "executed_steps": len(step_results),
                "step_results": [r.to_dict() for r in step_results]
            }
        )

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self._execution_log.copy()

    def clear_log(self) -> None:
        """Clear execution log"""
        self._execution_log.clear()

    def __repr__(self) -> str:
        return f"<SkillChain(name={self.name}, steps={len(self.steps)})>"
