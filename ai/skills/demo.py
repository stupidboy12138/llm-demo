"""
Comprehensive Skills Framework Demo

Demonstrates all features of the skills system:
- Skill registration and discovery
- Skill execution with context
- Skill chaining and composition
- Caching and retry logic
- Event hooks and monitoring
- Batch execution
"""

import asyncio
import uuid
from typing import Any, Dict

from .base_skill import SkillContext, SkillCategory
from .skill_registry import SkillRegistry
from .skill_executor import SkillExecutor
from .skill_chain import SkillChain
from .example_skills import (
    TextSummarizerSkill,
    DataValidatorSkill,
    MathCalculatorSkill,
    JSONTransformerSkill,
    TextAnalyzerSkill,
    DataAggregatorSkill,
    FeishuDocumentReaderSkill
)


async def demo_basic_execution():
    """Demo 1: Basic skill execution"""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Skill Execution")
    print("=" * 60)

    # Create registry and executor
    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register skills
    registry.register(TextAnalyzerSkill())
    registry.register(MathCalculatorSkill())

    # Execute text analyzer
    print("\n1. Text Analysis:")
    context = SkillContext(execution_id=str(uuid.uuid4()))
    result = await executor.execute(
        "text_analyzer",
        context=context,
        text="The quick brown fox jumps over the lazy dog. This is a sample text for analysis."
    )

    if result.success:
        print(f"  ✓ Success!")
        print(f"  - Words: {result.data['word_count']}")
        print(f"  - Sentences: {result.data['sentence_count']}")
        print(f"  - Unique words: {result.data['unique_words']}")
        print(f"  - Execution time: {result.execution_time:.3f}s")
    else:
        print(f"  ✗ Failed: {result.error}")

    # Execute calculator
    print("\n2. Math Calculation:")
    result = await executor.execute(
        "math_calculator",
        expression="(10 + 20) * 3 / 2",
        precision=2
    )

    if result.success:
        print(f"  ✓ Success!")
        print(f"  - Expression: {result.data['expression']}")
        print(f"  - Result: {result.data['result']}")
    else:
        print(f"  ✗ Failed: {result.error}")


async def demo_skill_discovery():
    """Demo 2: Skill discovery and metadata"""
    print("\n" + "=" * 60)
    print("DEMO 2: Skill Discovery")
    print("=" * 60)

    registry = SkillRegistry()

    # Register multiple skills
    skills = [
        TextSummarizerSkill(),
        DataValidatorSkill(),
        MathCalculatorSkill(),
        JSONTransformerSkill(),
        TextAnalyzerSkill(),
        DataAggregatorSkill()
    ]

    for skill in skills:
        registry.register(skill)

    print(f"\n1. Total registered skills: {len(registry)}")

    # List by category
    print("\n2. Skills by category:")
    for category in SkillCategory:
        category_skills = registry.get_by_category(category)
        if category_skills:
            print(f"  {category.value}:")
            for skill in category_skills:
                print(f"    - {skill.metadata.name}: {skill.metadata.description}")

    # Search skills
    print("\n3. Search for 'text' skills:")
    text_skills = registry.search("text")
    for skill in text_skills:
        print(f"  - {skill.metadata.name}")

    # Show skill metadata
    print("\n4. Detailed metadata for 'text_analyzer':")
    skill = registry.get("text_analyzer")
    if skill:
        metadata_dict = skill.metadata.to_dict()
        print(f"  Name: {metadata_dict['name']}")
        print(f"  Description: {metadata_dict['description']}")
        print(f"  Category: {metadata_dict['category']}")
        print(f"  Tags: {', '.join(metadata_dict['tags'])}")
        print(f"  Parameters:")
        for param in metadata_dict['parameters']:
            print(f"    - {param['name']} ({param['type']}): {param['description']}")


async def demo_validation():
    """Demo 3: Data validation skill"""
    print("\n" + "=" * 60)
    print("DEMO 3: Data Validation")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)
    registry.register(DataValidatorSkill())

    # Define schema
    schema = {
        "name": {"type": str, "required": True},
        "age": {"type": int, "required": True, "min": 0, "max": 150},
        "email": {
            "type": str,
            "required": True,
            "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"
        }
    }

    # Test valid data
    print("\n1. Validating valid data:")
    valid_data = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    }

    result = await executor.execute(
        "data_validator",
        data=valid_data,
        schema=schema
    )

    print(f"  Valid: {result.data['is_valid']}")
    if result.data['errors']:
        print(f"  Errors: {result.data['errors']}")

    # Test invalid data
    print("\n2. Validating invalid data:")
    invalid_data = {
        "name": "Jane Doe",
        "age": 200,  # Invalid: exceeds max
        "email": "invalid-email"  # Invalid: bad format
    }

    result = await executor.execute(
        "data_validator",
        data=invalid_data,
        schema=schema
    )

    print(f"  Valid: {result.data['is_valid']}")
    if result.data['errors']:
        print(f"  Errors:")
        for error in result.data['errors']:
            print(f"    - {error}")


async def demo_skill_chain():
    """Demo 4: Chaining skills together"""
    print("\n" + "=" * 60)
    print("DEMO 4: Skill Chain")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register skills
    registry.register(TextAnalyzerSkill())
    registry.register(JSONTransformerSkill())
    registry.register(DataValidatorSkill())

    # Create chain
    chain = SkillChain(executor, "TextProcessingChain")

    print("\nCreating chain: Analyze → Transform → Validate")

    # Step 1: Analyze text
    chain.add_step(
        "text_analyzer",
        parameters={"text": "Machine learning is transforming artificial intelligence. Deep learning enables powerful models."}
    )

    # Step 2: Transform the result
    chain.add_step(
        "json_transformer",
        transform_input=lambda data: {
            "data": data,
            "mapping": {
                "word_count": "total_words",
                "sentence_count": "total_sentences"
            },
            "keep_unmapped": True
        }
    )

    # Step 3: Validate transformed data
    chain.add_step(
        "data_validator",
        transform_input=lambda data: {
            "data": data["transformed"],
            "schema": {
                "total_words": {"type": int, "required": True, "min": 0},
                "total_sentences": {"type": int, "required": True, "min": 0}
            }
        }
    )

    # Execute chain
    print("\nExecuting chain...")
    result = await chain.execute()

    if result.success:
        print(f"\n✓ Chain completed successfully!")
        print(f"  - Total execution time: {result.execution_time:.3f}s")
        print(f"  - Steps executed: {result.metadata['executed_steps']}")
        print(f"  - Final result: {result.data}")

        # Show step details
        print("\n  Step details:")
        for step_result in result.metadata['step_results']:
            print(f"    Step {step_result.get('execution_id', 'N/A')}: "
                  f"{'✓' if step_result['success'] else '✗'} "
                  f"({step_result['execution_time']:.3f}s)")
    else:
        print(f"\n✗ Chain failed: {result.error}")


async def demo_caching():
    """Demo 5: Result caching"""
    print("\n" + "=" * 60)
    print("DEMO 5: Result Caching")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry, cache_ttl=60)  # 60s cache
    registry.register(MathCalculatorSkill())

    expression = "pow(2, 10) + pow(3, 5)"

    # First execution
    print("\n1. First execution (no cache):")
    result1 = await executor.execute(
        "math_calculator",
        expression=expression
    )
    print(f"  Result: {result1.data['result']}")
    print(f"  Time: {result1.execution_time:.3f}s")

    # Second execution (cached)
    print("\n2. Second execution (from cache):")
    result2 = await executor.execute(
        "math_calculator",
        expression=expression
    )
    print(f"  Result: {result2.data['result']}")
    print(f"  Time: {result2.execution_time:.3f}s")

    # Stats
    stats = executor.get_statistics()
    print(f"\n3. Cache statistics:")
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Cache size: {stats['cache_size']}")


async def demo_hooks():
    """Demo 6: Event hooks"""
    print("\n" + "=" * 60)
    print("DEMO 6: Event Hooks")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)
    registry.register(TextAnalyzerSkill())

    # Define hooks
    async def before_hook(skill_name, context, params):
        print(f"  [HOOK] Before executing: {skill_name}")

    async def after_hook(skill_name, result):
        print(f"  [HOOK] After executing: {skill_name}")
        print(f"  [HOOK] Success: {result.success}")

    # Register hooks
    executor.register_hook("before_execute", before_hook)
    executor.register_hook("after_execute", after_hook)

    print("\nExecuting skill with hooks:")
    result = await executor.execute(
        "text_analyzer",
        text="This is a test."
    )

    print(f"\nResult: {result.data['word_count']} words")


async def demo_batch_execution():
    """Demo 7: Batch execution"""
    print("\n" + "=" * 60)
    print("DEMO 7: Batch Execution")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)
    registry.register(MathCalculatorSkill())

    # Define batch tasks
    tasks = [
        ("math_calculator", {"expression": "10 + 20"}),
        ("math_calculator", {"expression": "100 * 2"}),
        ("math_calculator", {"expression": "pow(5, 3)"}),
        ("math_calculator", {"expression": "max(10, 20, 30)"}),
    ]

    print(f"\nExecuting {len(tasks)} tasks in parallel (max 3 concurrent):")

    # Execute batch
    results = await executor.execute_batch(tasks, max_concurrent=3)

    # Show results
    for i, result in enumerate(results):
        if result.success:
            print(f"  {i+1}. {result.data['expression']} = {result.data['result']}")
        else:
            print(f"  {i+1}. Error: {result.error}")


async def demo_error_handling():
    """Demo 8: Error handling and retry"""
    print("\n" + "=" * 60)
    print("DEMO 8: Error Handling & Retry")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)
    registry.register(MathCalculatorSkill())

    # Test invalid expression
    print("\n1. Invalid expression (should fail):")
    result = await executor.execute(
        "math_calculator",
        expression="invalid * expression"
    )

    if result.success:
        print(f"  ✓ Result: {result.data}")
    else:
        print(f"  ✗ Error: {result.error}")
        print(f"  Error type: {result.error_type}")

    # Test with retry
    print("\n2. Execution with retry context:")
    context = SkillContext(
        execution_id=str(uuid.uuid4()),
        max_retries=3
    )

    result = await executor.execute(
        "math_calculator",
        context=context,
        expression="10 / 0"  # Division by zero
    )

    print(f"  Success: {result.success}")
    print(f"  Retries attempted: {context.retry_count}")


async def demo_statistics():
    """Demo 9: Statistics and monitoring"""
    print("\n" + "=" * 60)
    print("DEMO 9: Statistics & Monitoring")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register skills
    registry.register(TextAnalyzerSkill())
    registry.register(MathCalculatorSkill())

    # Execute multiple times
    print("\nExecuting skills multiple times...")
    for i in range(5):
        await executor.execute("text_analyzer", text=f"Sample text {i}")
        await executor.execute("math_calculator", expression=f"{i} * 2")

    # Show skill statistics
    print("\n1. Skill Statistics:")
    text_analyzer = registry.get("text_analyzer")
    stats = text_analyzer.get_statistics()
    print(f"  Text Analyzer:")
    print(f"    - Executions: {stats['execution_count']}")
    print(f"    - Success rate: {stats['success_rate']:.1%}")
    print(f"    - Avg time: {stats['average_execution_time']:.3f}s")

    # Show registry statistics
    print("\n2. Registry Statistics:")
    reg_stats = registry.get_statistics()
    print(f"  Total skills: {reg_stats['total_skills']}")
    print(f"  By category:")
    for cat, count in reg_stats['categories'].items():
        print(f"    - {cat}: {count}")

    # Show executor statistics
    print("\n3. Executor Statistics:")
    exec_stats = executor.get_statistics()
    print(f"  Total executions: {exec_stats['total_executions']}")
    print(f"  Success rate: {exec_stats['success_rate']:.1%}")
    print(f"  Cache size: {exec_stats['cache_size']}")


async def demo_feishu_reader():
    """Demo: Feishu Document Reader Skill"""
    print("\n" + "=" * 60)
    print("DEMO: Feishu Document Reader")
    print("=" * 60)

    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register the Feishu reader skill
    feishu_skill = FeishuDocumentReaderSkill()
    registry.register(feishu_skill)

    print("\n1. Skill Metadata:")
    metadata = feishu_skill.metadata
    print(f"  - Name: {metadata.name}")
    print(f"  - Description: {metadata.description}")
    print(f"  - Category: {metadata.category.value}")
    print(f"  - Parameters: {len(metadata.parameters)}")
    for param in metadata.parameters:
        print(f"    • {param.name}: {param.description}")

    print("\n2. Example Usage (requires Feishu credentials):")
    print("  To use this skill, you need to:")
    print("  1. Create a Feishu app at https://open.feishu.cn/")
    print("  2. Set FEISHU_APP_ID and FEISHU_APP_SECRET environment variables")
    print("  3. Provide a Feishu document URL")
    print("\n  Example code:")
    print("  ```python")
    print("  result = await executor.execute(")
    print("      'feishu_document_reader',")
    print("      document_url='https://example.feishu.cn/docx/ABC123XYZ',")
    print("      extract_type='all'  # or 'content', 'metadata', 'tables', 'comments'")
    print("  )")
    print("  ```")

    # Check if credentials are available
    import os
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if app_id and app_secret:
        print("\n3. Credentials detected! You can run the full demo.")
        print("   Run: python -m ai.skills.feishu_document_reader.scripts.example_usage")
    else:
        print("\n3. No credentials found. Set FEISHU_APP_ID and FEISHU_APP_SECRET to test.")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("AI SKILLS FRAMEWORK - COMPREHENSIVE DEMO")
    print("=" * 60)

    demos = [
        ("Basic Execution", demo_basic_execution),
        ("Skill Discovery", demo_skill_discovery),
        ("Data Validation", demo_validation),
        ("Skill Chain", demo_skill_chain),
        ("Caching", demo_caching),
        ("Event Hooks", demo_hooks),
        ("Batch Execution", demo_batch_execution),
        ("Error Handling", demo_error_handling),
        ("Statistics", demo_statistics),
        ("Feishu Document Reader", demo_feishu_reader),
    ]

    for name, demo_func in demos:
        try:
            await demo_func()
            await asyncio.sleep(0.5)  # Brief pause between demos
        except Exception as e:
            print(f"\n✗ Demo '{name}' failed: {e}")

    print("\n" + "=" * 60)
    print("ALL DEMOS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
