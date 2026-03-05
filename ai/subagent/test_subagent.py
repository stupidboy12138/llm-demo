"""
Unit Tests for SubAgent Architecture

Run with: pytest ai/subagent/test_subagent.py
"""

import pytest
import asyncio
from ai.subagent import (
    BaseSubAgent,
    SubAgentCapability,
    TaskContext,
    TaskResult,
    SubAgentRegistry,
    DataAnalysisSubAgent,
    CodeGenerationSubAgent,
    ResearchSubAgent,
    ValidationSubAgent,
    CoordinatorAgent
)


class MockSubAgent(BaseSubAgent):
    """Mock agent for testing"""

    def __init__(self, agent_id="mock", should_fail=False):
        super().__init__(
            agent_id=agent_id,
            name="Mock Agent",
            capabilities=[SubAgentCapability.RESEARCH]
        )
        self.should_fail = should_fail

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        if self.should_fail:
            raise Exception("Mock failure")

        return TaskResult(
            task_id=context.task_id,
            success=True,
            data={"mock_result": f"Processed: {task}"}
        )

    def can_handle(self, task_type: str) -> bool:
        return True


class TestBaseSubAgent:
    """Test BaseSubAgent functionality"""

    @pytest.mark.asyncio
    async def test_execute_with_tracking(self):
        agent = MockSubAgent()
        context = TaskContext(task_id="test-1", task_type="test")

        result = await agent.execute_with_tracking("test task", context)

        assert result.success is True
        assert result.task_id == "test-1"
        assert result.execution_time > 0
        assert "mock_result" in result.data

    @pytest.mark.asyncio
    async def test_error_handling(self):
        agent = MockSubAgent(should_fail=True)
        context = TaskContext(task_id="test-2", task_type="test")

        result = await agent.execute_with_tracking("test task", context)

        assert result.success is False
        assert result.error is not None
        assert "Mock failure" in result.error

    def test_get_status(self):
        agent = MockSubAgent()
        status = agent.get_status()

        assert status["agent_id"] == "mock"
        assert status["name"] == "Mock Agent"
        assert status["is_busy"] is False
        assert status["active_tasks"] == 0

    def test_has_capability(self):
        agent = MockSubAgent()

        assert agent.has_capability(SubAgentCapability.RESEARCH) is True
        assert agent.has_capability(SubAgentCapability.CODE_GENERATION) is False


class TestSubAgentRegistry:
    """Test SubAgentRegistry functionality"""

    def test_register_and_get_agent(self):
        registry = SubAgentRegistry()
        agent = MockSubAgent("test-agent")

        registry.register(agent)

        assert len(registry) == 1
        assert "test-agent" in registry
        assert registry.get_agent("test-agent") == agent

    def test_unregister_agent(self):
        registry = SubAgentRegistry()
        agent = MockSubAgent("test-agent")

        registry.register(agent)
        success = registry.unregister("test-agent")

        assert success is True
        assert len(registry) == 0
        assert registry.get_agent("test-agent") is None

    def test_get_agents_by_capability(self):
        registry = SubAgentRegistry()
        agent1 = MockSubAgent("agent-1")
        agent2 = DataAnalysisSubAgent("agent-2")

        registry.register(agent1)
        registry.register(agent2)

        research_agents = registry.get_agents_by_capability(SubAgentCapability.RESEARCH)
        analysis_agents = registry.get_agents_by_capability(SubAgentCapability.DATA_ANALYSIS)

        assert len(research_agents) == 1
        assert len(analysis_agents) == 1

    def test_find_best_agent(self):
        registry = SubAgentRegistry()
        agent1 = MockSubAgent("agent-1")
        agent2 = MockSubAgent("agent-2")

        registry.register(agent1)
        registry.register(agent2)

        best = registry.find_best_agent(SubAgentCapability.RESEARCH)

        assert best is not None
        assert best.agent_id in ["agent-1", "agent-2"]

    def test_get_registry_status(self):
        registry = SubAgentRegistry()
        registry.register(MockSubAgent("agent-1"))
        registry.register(DataAnalysisSubAgent("agent-2"))

        status = registry.get_registry_status()

        assert status["total_agents"] == 2
        assert len(status["agents"]) == 2


class TestSpecializedAgents:
    """Test specialized agent implementations"""

    @pytest.mark.asyncio
    async def test_data_analysis_agent(self):
        agent = DataAnalysisSubAgent()
        context = TaskContext(task_id="analysis-1", task_type="analysis")

        result = await agent.execute_with_tracking(
            "Analyze the trend: 10, 20, 30, 40, 50",
            context
        )

        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_code_generation_agent(self):
        agent = CodeGenerationSubAgent()
        context = TaskContext(task_id="code-1", task_type="code")

        result = await agent.execute_with_tracking(
            "Generate a function to calculate factorial",
            context
        )

        assert result.success is True
        assert "code" in result.data

    @pytest.mark.asyncio
    async def test_research_agent(self):
        agent = ResearchSubAgent()
        context = TaskContext(task_id="research-1", task_type="research")

        result = await agent.execute_with_tracking(
            "Explain what is recursion",
            context
        )

        assert result.success is True
        assert "summary" in result.data

    @pytest.mark.asyncio
    async def test_validation_agent(self):
        agent = ValidationSubAgent()
        context = TaskContext(task_id="validate-1", task_type="validation")

        result = await agent.execute_with_tracking(
            "def add(a, b): return a + b",
            context
        )

        assert result.success is True


class TestCoordinatorAgent:
    """Test CoordinatorAgent functionality"""

    @pytest.mark.asyncio
    async def test_simple_task_execution(self):
        registry = SubAgentRegistry()
        registry.register(ResearchSubAgent())

        coordinator = CoordinatorAgent(registry)

        result = await coordinator.execute_complex_task(
            "Explain binary search",
            decompose=False,
            validate_results=False
        )

        assert result["success"] is True
        assert "result" in result

    @pytest.mark.asyncio
    async def test_get_task_history(self):
        registry = SubAgentRegistry()
        registry.register(ResearchSubAgent())

        coordinator = CoordinatorAgent(registry)

        await coordinator.execute_complex_task("Test task", decompose=False)

        history = coordinator.get_task_history()

        assert len(history) == 1
        assert history[0]["task"] == "Test task"

    def test_get_status(self):
        registry = SubAgentRegistry()
        coordinator = CoordinatorAgent(registry)

        status = coordinator.get_status()

        assert "coordinator" in status
        assert "total_tasks_executed" in status
        assert "registry_status" in status


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
