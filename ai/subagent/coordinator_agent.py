"""
Coordinator Agent

Main agent that coordinates multiple sub-agents to accomplish complex tasks.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import logging

from .base_subagent import SubAgentCapability, TaskContext, TaskResult
from .subagent_registry import SubAgentRegistry

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Coordinator agent that manages and delegates tasks to sub-agents.

    Responsibilities:
    - Task decomposition
    - Sub-agent selection
    - Task delegation
    - Result aggregation
    - Workflow orchestration
    """

    def __init__(
        self,
        registry: SubAgentRegistry,
        api_base: str = None,
        api_key: str = None
    ):
        """
        Initialize the coordinator agent.

        Args:
            registry: SubAgentRegistry instance
            api_base: LLM API base URL
            api_key: LLM API key
        """
        self.registry = registry
        self.llm = ChatOpenAI(
            model="360/qwen3-32b",
            temperature=0.4,
            base_url=api_base or "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1",
            api_key=api_key or "sk-deepbank-dev"
        )
        self._task_history: List[Dict[str, Any]] = []

    async def execute_complex_task(
        self,
        task: str,
        decompose: bool = True,
        validate_results: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a complex task by coordinating sub-agents.

        Args:
            task: The complex task description
            decompose: Whether to decompose the task into subtasks
            validate_results: Whether to validate final results

        Returns:
            Aggregated results from all sub-agents
        """
        logger.info(f"Coordinator received task: {task}")

        task_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Step 1: Decompose task if needed
            if decompose:
                subtasks = await self._decompose_task(task)
            else:
                subtasks = [{"task": task, "capability": None}]

            logger.info(f"Decomposed into {len(subtasks)} subtasks")

            # Step 2: Execute subtasks in parallel or sequence
            results = await self._execute_subtasks(subtasks, task_id)

            # Step 3: Aggregate results
            aggregated = await self._aggregate_results(task, results)

            # Step 4: Validate if requested
            if validate_results:
                validation = await self._validate_results(aggregated)
                aggregated["validation"] = validation

            # Record in history
            execution_time = (datetime.now() - start_time).total_seconds()
            self._task_history.append({
                "task_id": task_id,
                "task": task,
                "subtasks_count": len(subtasks),
                "success": aggregated.get("success", False),
                "execution_time": execution_time,
                "timestamp": start_time
            })

            return {
                "task_id": task_id,
                "task": task,
                "success": True,
                "result": aggregated,
                "execution_time": execution_time,
                "subtasks_executed": len(results)
            }

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {
                "task_id": task_id,
                "task": task,
                "success": False,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }

    async def _decompose_task(self, task: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex task into subtasks.

        Args:
            task: The complex task

        Returns:
            List of subtasks with assigned capabilities
        """
        system_prompt = f"""You are a task decomposition expert. Break down complex tasks into
        smaller, manageable subtasks. For each subtask, identify the required capability from:
        {', '.join([cap.value for cap in SubAgentCapability])}

        Return a JSON array of objects with keys: task, capability, priority (1-5).
        If the task is simple, return a single subtask."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Decompose this task:\n{task}")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response
        import json
        try:
            subtasks = json.loads(response.content)
            if not isinstance(subtasks, list):
                subtasks = [subtasks]
        except json.JSONDecodeError:
            # Fallback: treat as single task
            subtasks = [{
                "task": task,
                "capability": "research",
                "priority": 3
            }]

        return subtasks

    async def _execute_subtasks(
        self,
        subtasks: List[Dict[str, Any]],
        parent_task_id: str
    ) -> List[TaskResult]:
        """
        Execute all subtasks using appropriate sub-agents.

        Args:
            subtasks: List of subtasks to execute
            parent_task_id: ID of the parent task

        Returns:
            List of task results
        """
        tasks = []

        for idx, subtask in enumerate(subtasks):
            task_text = subtask["task"]
            capability_str = subtask.get("capability", "research")
            priority = subtask.get("priority", 3)

            # Map capability string to enum
            try:
                capability = SubAgentCapability(capability_str)
            except ValueError:
                capability = SubAgentCapability.RESEARCH

            # Find best agent
            agent = self.registry.find_best_agent(capability, task_text)

            if not agent:
                logger.warning(f"No agent found for capability: {capability}")
                continue

            # Create task context
            context = TaskContext(
                task_id=f"{parent_task_id}-{idx}",
                task_type=capability_str,
                priority=priority,
                parent_task_id=parent_task_id,
                metadata={"subtask_index": idx}
            )

            # Schedule execution
            tasks.append(agent.execute_with_tracking(task_text, context))

        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            return [r for r in results if isinstance(r, TaskResult)]

        return []

    async def _aggregate_results(
        self,
        original_task: str,
        results: List[TaskResult]
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple sub-agents.

        Args:
            original_task: The original task
            results: List of subtask results

        Returns:
            Aggregated result
        """
        if not results:
            return {"success": False, "error": "No results to aggregate"}

        # Combine all successful results
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # Use LLM to synthesize final answer
        system_prompt = """You are a result synthesizer. Combine the following results
        from different specialized agents into a coherent, comprehensive answer."""

        results_text = "\n\n".join([
            f"Result {i+1}:\n{r.data}"
            for i, r in enumerate(successful_results)
        ])

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Original task: {original_task}\n\nResults:\n{results_text}")
        ]

        response = await self.llm.ainvoke(messages)

        return {
            "success": len(successful_results) > 0,
            "final_answer": response.content,
            "successful_subtasks": len(successful_results),
            "failed_subtasks": len(failed_results),
            "detailed_results": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "data": r.data,
                    "error": r.error,
                    "execution_time": r.execution_time
                }
                for r in results
            ]
        }

    async def _validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the aggregated results using ValidationSubAgent.

        Args:
            results: Aggregated results

        Returns:
            Validation result
        """
        validator = self.registry.find_best_agent(SubAgentCapability.VALIDATION)

        if not validator:
            return {"validated": False, "reason": "No validator available"}

        context = TaskContext(
            task_id=str(uuid.uuid4()),
            task_type="validation",
            priority=4
        )

        validation_task = f"Validate these results:\n{results.get('final_answer', '')}"
        result = await validator.execute_with_tracking(validation_task, context)

        return result.data if result.success else {"validated": False, "error": result.error}

    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent task history"""
        return self._task_history[-limit:]

    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status"""
        return {
            "coordinator": "active",
            "total_tasks_executed": len(self._task_history),
            "registry_status": self.registry.get_registry_status()
        }
