"""
Unit Tests for Skills Framework

Tests core functionality of the skills system.
"""

import pytest
import asyncio
from typing import Any

from ai.skills import (
    BaseSkill,
    SkillCategory,
    SkillContext,
    SkillResult,
    SkillParameter,
    SkillMetadata,
    SkillRegistry,
    SkillExecutor,
    SkillChain
)
from ai.skills.example_skills import (
    TextAnalyzerSkill,
    MathCalculatorSkill,
    DataValidatorSkill,
    JSONTransformerSkill
)


# Test Skill Implementation
class TestSkill(BaseSkill):
    """Simple test skill"""

    def __init__(self):
        metadata = SkillMetadata(
            name="test_skill",
            description="Test skill for unit tests",
            category=SkillCategory.COMPUTATION,
            parameters=[
                SkillParameter(
                    name="value",
                    type=int,
                    description="Test value",
                    required=True
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        value = kwargs.get("value", 0)
        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={"doubled": value * 2}
        )


class TestSkillMetadata:
    """Test skill metadata"""

    def test_metadata_creation(self):
        metadata = SkillMetadata(
            name="test",
            description="Test skill",
            category=SkillCategory.DATA_PROCESSING,
            version="1.0.0",
            tags=["test"],
            parameters=[
                SkillParameter(
                    name="param1",
                    type=str,
                    description="Test parameter",
                    required=True
                )
            ]
        )

        assert metadata.name == "test"
        assert metadata.category == SkillCategory.DATA_PROCESSING
        assert len(metadata.parameters) == 1

    def test_metadata_to_dict(self):
        metadata = SkillMetadata(
            name="test",
            description="Test skill",
            category=SkillCategory.DATA_PROCESSING
        )

        data = metadata.to_dict()
        assert data["name"] == "test"
        assert data["category"] == "data_processing"


class TestSkillParameter:
    """Test skill parameters"""

    def test_parameter_validation_success(self):
        param = SkillParameter(
            name="test",
            type=str,
            description="Test",
            required=True
        )

        assert param.validate("hello") is True

    def test_parameter_validation_type_error(self):
        param = SkillParameter(
            name="test",
            type=int,
            description="Test",
            required=True
        )

        assert param.validate("hello") is False

    def test_parameter_custom_validator(self):
        param = SkillParameter(
            name="test",
            type=int,
            description="Test",
            required=True,
            validator=lambda x: x > 0
        )

        assert param.validate(10) is True
        assert param.validate(-5) is False


class TestBaseSkill:
    """Test base skill functionality"""

    @pytest.mark.asyncio
    async def test_skill_execution(self):
        skill = TestSkill()
        context = SkillContext(execution_id="test-1")

        result = await skill.execute_with_tracking(context, value=10)

        assert result.success is True
        assert result.data["doubled"] == 20

    @pytest.mark.asyncio
    async def test_parameter_validation(self):
        skill = TestSkill()

        # Valid parameters
        is_valid, error = skill.validate_parameters(value=10)
        assert is_valid is True
        assert error is None

        # Missing required parameter
        is_valid, error = skill.validate_parameters()
        assert is_valid is False
        assert "missing" in error.lower()

    @pytest.mark.asyncio
    async def test_skill_statistics(self):
        skill = TestSkill()
        await skill.initialize()

        context1 = SkillContext(execution_id="test-1")
        context2 = SkillContext(execution_id="test-2")

        await skill.execute_with_tracking(context1, value=10)
        await skill.execute_with_tracking(context2, value=20)

        stats = skill.get_statistics()
        assert stats["execution_count"] == 2
        assert stats["success_count"] == 2
        assert stats["success_rate"] == 1.0


class TestSkillRegistry:
    """Test skill registry"""

    def test_register_skill(self):
        registry = SkillRegistry()
        skill = TestSkill()

        registry.register(skill)

        assert len(registry) == 1
        assert "test_skill" in registry

    def test_get_skill(self):
        registry = SkillRegistry()
        skill = TestSkill()
        registry.register(skill)

        retrieved = registry.get("test_skill")
        assert retrieved is not None
        assert retrieved.metadata.name == "test_skill"

    def test_unregister_skill(self):
        registry = SkillRegistry()
        skill = TestSkill()
        registry.register(skill)

        result = registry.unregister("test_skill")
        assert result is True
        assert len(registry) == 0

    def test_get_by_category(self):
        registry = SkillRegistry()
        registry.register(TestSkill())
        registry.register(TextAnalyzerSkill())

        computation_skills = registry.get_by_category(SkillCategory.COMPUTATION)
        assert len(computation_skills) == 1

        text_skills = registry.get_by_category(SkillCategory.TEXT_ANALYSIS)
        assert len(text_skills) == 1

    def test_search_skills(self):
        registry = SkillRegistry()
        registry.register(TestSkill())
        registry.register(TextAnalyzerSkill())

        results = registry.search("test")
        assert len(results) >= 1

        results = registry.search("text")
        assert len(results) >= 1


class TestSkillExecutor:
    """Test skill executor"""

    @pytest.mark.asyncio
    async def test_execute_skill(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        result = await executor.execute("test_skill", value=5)

        assert result.success is True
        assert result.data["doubled"] == 10

    @pytest.mark.asyncio
    async def test_skill_not_found(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)

        result = await executor.execute("nonexistent_skill")

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_caching(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry, cache_ttl=60)
        registry.register(TestSkill())

        # First execution
        result1 = await executor.execute("test_skill", value=5)
        time1 = result1.execution_time

        # Second execution (should be cached)
        result2 = await executor.execute("test_skill", value=5)
        time2 = result2.execution_time

        # Both should have same result
        assert result1.data == result2.data

        stats = executor.get_statistics()
        assert stats["cache_size"] > 0

    @pytest.mark.asyncio
    async def test_batch_execution(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        tasks = [
            ("test_skill", {"value": 1}),
            ("test_skill", {"value": 2}),
            ("test_skill", {"value": 3}),
        ]

        results = await executor.execute_batch(tasks, max_concurrent=2)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].data["doubled"] == 2
        assert results[1].data["doubled"] == 4
        assert results[2].data["doubled"] == 6

    @pytest.mark.asyncio
    async def test_execution_hooks(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        hook_calls = []

        async def before_hook(skill_name, context, params):
            hook_calls.append(("before", skill_name))

        async def after_hook(skill_name, result):
            hook_calls.append(("after", skill_name))

        executor.register_hook("before_execute", before_hook)
        executor.register_hook("after_execute", after_hook)

        await executor.execute("test_skill", value=5)

        assert len(hook_calls) == 2
        assert hook_calls[0] == ("before", "test_skill")
        assert hook_calls[1] == ("after", "test_skill")


class TestSkillChain:
    """Test skill chain"""

    @pytest.mark.asyncio
    async def test_chain_execution(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        chain = SkillChain(executor, "TestChain")
        chain.add_step("test_skill", parameters={"value": 5})
        chain.add_step(
            "test_skill",
            transform_input=lambda data: {"value": data["doubled"]}
        )

        result = await chain.execute()

        assert result.success is True
        assert result.data["doubled"] == 20  # 5 * 2 * 2

    @pytest.mark.asyncio
    async def test_chain_with_error_stop(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        chain = SkillChain(executor, "TestChain")
        chain.add_step("test_skill", parameters={"value": 5})
        chain.add_step("nonexistent_skill", on_error="stop")

        result = await chain.execute()

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_chain_with_error_continue(self):
        registry = SkillRegistry()
        executor = SkillExecutor(registry)
        registry.register(TestSkill())

        chain = SkillChain(executor, "TestChain")
        chain.add_step("test_skill", parameters={"value": 5})
        chain.add_step("nonexistent_skill", on_error="continue")
        chain.add_step("test_skill", parameters={"value": 10})

        result = await chain.execute()

        # Should complete despite error in middle
        assert result.success is True
        assert result.data["doubled"] == 20


class TestExampleSkills:
    """Test example skills"""

    @pytest.mark.asyncio
    async def test_text_analyzer(self):
        skill = TextAnalyzerSkill()
        context = SkillContext(execution_id="test-1")

        result = await skill.execute(context, text="Hello world! This is a test.")

        assert result.success is True
        assert result.data["word_count"] == 6
        assert result.data["sentence_count"] == 2

    @pytest.mark.asyncio
    async def test_math_calculator(self):
        skill = MathCalculatorSkill()
        context = SkillContext(execution_id="test-1")

        result = await skill.execute(context, expression="10 + 20 * 2")

        assert result.success is True
        assert result.data["result"] == 50

    @pytest.mark.asyncio
    async def test_data_validator(self):
        skill = DataValidatorSkill()
        context = SkillContext(execution_id="test-1")

        schema = {
            "name": {"type": str, "required": True},
            "age": {"type": int, "required": True, "min": 0}
        }

        # Valid data
        result = await skill.execute(
            context,
            data={"name": "John", "age": 30},
            schema=schema
        )

        assert result.success is True
        assert result.data["is_valid"] is True

        # Invalid data
        result = await skill.execute(
            context,
            data={"name": "Jane"},  # Missing age
            schema=schema
        )

        assert result.success is True
        assert result.data["is_valid"] is False
        assert len(result.data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_json_transformer(self):
        skill = JSONTransformerSkill()
        context = SkillContext(execution_id="test-1")

        data = {"old_field": "value", "another": "data"}
        mapping = {"old_field": "new_field"}

        result = await skill.execute(
            context,
            data=data,
            mapping=mapping,
            keep_unmapped=False
        )

        assert result.success is True
        assert "new_field" in result.data["transformed"]
        assert result.data["transformed"]["new_field"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
