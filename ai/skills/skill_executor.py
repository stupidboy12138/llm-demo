"""
Skill Executor

Handles skill execution with retry logic, caching, and monitoring.
"""

from typing import Dict, Any, Optional, Callable
from .base_skill import BaseSkill, SkillContext, SkillResult
from .skill_registry import SkillRegistry
import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class SkillExecutor:
    """
    Executor for running skills with advanced features.

    Features:
    - Retry logic with exponential backoff
    - Result caching
    - Execution monitoring
    - Concurrent execution
    - Event hooks
    """

    def __init__(self, registry: SkillRegistry, cache_ttl: int = 300):
        """
        Initialize executor.

        Args:
            registry: Skill registry
            cache_ttl: Cache time-to-live in seconds
        """
        self.registry = registry
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[SkillResult, datetime]] = {}
        self._hooks: Dict[str, list[Callable]] = defaultdict(list)
        self._execution_history: list[tuple[str, SkillResult]] = []
        self._max_history = 1000

    async def execute(
        self,
        skill_name: str,
        context: Optional[SkillContext] = None,
        use_cache: bool = True,
        **kwargs
    ) -> SkillResult:
        """
        Execute a skill.

        Args:
            skill_name: Name of the skill to execute
            context: Execution context (created if None)
            use_cache: Whether to use cached results
            **kwargs: Skill parameters

        Returns:
            SkillResult
        """
        # Get skill
        skill = self.registry.get(skill_name)
        if not skill:
            return SkillResult(
                execution_id=str(uuid.uuid4()),
                success=False,
                data=None,
                error=f"Skill '{skill_name}' not found",
                error_type="SkillNotFoundError"
            )

        # Create context if not provided
        if context is None:
            context = SkillContext(
                execution_id=str(uuid.uuid4())
            )

        # Check cache
        if use_cache:
            cached_result = self._get_from_cache(skill_name, kwargs)
            if cached_result:
                logger.info(f"Using cached result for {skill_name}")
                await self._trigger_hooks("on_cache_hit", skill_name, cached_result)
                return cached_result

        # Trigger pre-execution hooks
        await self._trigger_hooks("before_execute", skill_name, context, kwargs)

        # Execute with retry
        result = await self._execute_with_retry(skill, context, **kwargs)

        # Cache result if successful
        if result.success and use_cache:
            self._add_to_cache(skill_name, kwargs, result)

        # Add to history
        self._add_to_history(skill_name, result)

        # Trigger post-execution hooks
        await self._trigger_hooks("after_execute", skill_name, result)

        return result

    async def execute_batch(
        self,
        tasks: list[tuple[str, Dict[str, Any]]],
        max_concurrent: int = 5
    ) -> list[SkillResult]:
        """
        Execute multiple skills concurrently.

        Args:
            tasks: List of (skill_name, parameters) tuples
            max_concurrent: Maximum concurrent executions

        Returns:
            List of SkillResults
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_task(skill_name: str, params: Dict[str, Any]) -> SkillResult:
            async with semaphore:
                return await self.execute(skill_name, **params)

        tasks_coros = [
            execute_task(skill_name, params)
            for skill_name, params in tasks
        ]

        return await asyncio.gather(*tasks_coros, return_exceptions=False)

    async def _execute_with_retry(
        self,
        skill: BaseSkill,
        context: SkillContext,
        **kwargs
    ) -> SkillResult:
        """Execute skill with retry logic"""
        max_retries = context.max_retries
        retry_delay = 1.0  # Initial delay in seconds

        for attempt in range(max_retries + 1):
            context.retry_count = attempt

            result = await skill.execute_with_tracking(context, **kwargs)

            if result.success or attempt >= max_retries:
                return result

            # Exponential backoff
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
                logger.warning(
                    f"Retrying {skill.metadata.name} (attempt {attempt + 1}/{max_retries})"
                )

        return result

    def _get_cache_key(self, skill_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key from skill name and parameters"""
        # Simple string representation for now
        # In production, use proper hashing
        params_str = str(sorted(params.items()))
        return f"{skill_name}:{params_str}"

    def _get_from_cache(
        self,
        skill_name: str,
        params: Dict[str, Any]
    ) -> Optional[SkillResult]:
        """Get result from cache if available and not expired"""
        cache_key = self._get_cache_key(skill_name, params)

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]

            # Check if expired
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return result
            else:
                # Remove expired entry
                del self._cache[cache_key]

        return None

    def _add_to_cache(
        self,
        skill_name: str,
        params: Dict[str, Any],
        result: SkillResult
    ) -> None:
        """Add result to cache"""
        cache_key = self._get_cache_key(skill_name, params)
        self._cache[cache_key] = (result, datetime.now())

    def clear_cache(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        logger.info("Cache cleared")

    def _add_to_history(self, skill_name: str, result: SkillResult) -> None:
        """Add execution to history"""
        self._execution_history.append((skill_name, result))

        # Limit history size
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def get_history(self, limit: Optional[int] = None) -> list[tuple[str, SkillResult]]:
        """Get execution history"""
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history.copy()

    def register_hook(self, event: str, callback: Callable) -> None:
        """
        Register an event hook.

        Events:
        - before_execute: Called before skill execution
        - after_execute: Called after skill execution
        - on_cache_hit: Called when cache is used

        Args:
            event: Event name
            callback: Async callback function
        """
        self._hooks[event].append(callback)
        logger.info(f"Registered hook for event: {event}")

    async def _trigger_hooks(self, event: str, *args, **kwargs) -> None:
        """Trigger all hooks for an event"""
        for hook in self._hooks.get(event, []):
            try:
                await hook(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook error for {event}: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        total_executions = len(self._execution_history)
        successful = sum(1 for _, r in self._execution_history if r.success)

        return {
            "total_executions": total_executions,
            "successful_executions": successful,
            "failed_executions": total_executions - successful,
            "success_rate": successful / total_executions if total_executions > 0 else 0,
            "cache_size": len(self._cache),
            "cache_ttl": self.cache_ttl,
            "registered_hooks": {
                event: len(hooks)
                for event, hooks in self._hooks.items()
            }
        }
