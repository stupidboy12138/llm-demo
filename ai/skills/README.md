# AI Skills Framework

A flexible, composable skills system for building AI capabilities with reusable, testable components.

## Overview

The Skills Framework provides a robust architecture for defining, registering, executing, and composing AI skills. Each skill is a self-contained unit of functionality that can be executed independently or combined with other skills.

## Key Features

- **Skill Registry**: Centralized registration and discovery of skills
- **Skill Executor**: Advanced execution engine with caching, retry logic, and monitoring
- **Skill Chains**: Compose multiple skills into workflows
- **Event Hooks**: Subscribe to execution events
- **Batch Execution**: Run multiple skills in parallel
- **Web API**: FastAPI-based REST service
- **Type Safety**: Full type hints and validation

## Architecture

```
ai/skills/
├── __init__.py              # Package exports
├── base_skill.py            # Core abstractions and types
├── skill_registry.py        # Skill registration and discovery
├── skill_executor.py        # Execution engine with caching/retry
├── skill_chain.py           # Skill composition and workflows
├── example_skills.py        # Example skill implementations
├── demo.py                  # Comprehensive demo
├── simple_demo.py           # Quick start demo
├── web_service.py           # FastAPI web service
├── client_examples.py       # API client examples
└── README.md                # This file
```

## Quick Start

### Basic Usage

```python
import asyncio
from ai.skills import SkillRegistry, SkillExecutor
from ai.skills.example_skills import TextAnalyzerSkill

async def main():
    # Setup
    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register skill
    registry.register(TextAnalyzerSkill())

    # Execute
    result = await executor.execute(
        "text_analyzer",
        text="Hello world! This is a test."
    )

    print(f"Word count: {result.data['word_count']}")

asyncio.run(main())
```

### Run Simple Demo

```bash
python -m ai.skills.simple_demo
```

### Run Comprehensive Demo

```bash
python -m ai.skills.demo
```

### Start Web Service

```bash
# Start service
python -m ai.skills.web_service
# Or with uvicorn
uvicorn ai.skills.web_service:app --port 8002

# API docs available at http://localhost:8002/docs
```

### Run Client Examples

```bash
python -m ai.skills.client_examples
```

## Core Concepts

### 1. Skills

Skills are reusable units of functionality defined by extending `BaseSkill`:

```python
from ai.skills import BaseSkill, SkillMetadata, SkillParameter, SkillCategory

class CustomSkill(BaseSkill):
    def __init__(self):
        metadata = SkillMetadata(
            name="custom_skill",
            description="Does something useful",
            category=SkillCategory.DATA_PROCESSING,
            parameters=[
                SkillParameter(
                    name="input",
                    type=str,
                    description="Input data",
                    required=True
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context, **kwargs):
        input_data = kwargs.get("input")
        # Process data...
        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={"result": "processed"}
        )
```

### 2. Registry

The registry manages skill lifecycle and discovery:

```python
from ai.skills import SkillRegistry

registry = SkillRegistry()

# Register skills
registry.register(CustomSkill())

# Discover skills
skill = registry.get("custom_skill")
skills_by_category = registry.get_by_category(SkillCategory.DATA_PROCESSING)
search_results = registry.search("text")
```

### 3. Executor

The executor handles skill execution with advanced features:

```python
from ai.skills import SkillExecutor, SkillContext

executor = SkillExecutor(registry, cache_ttl=300)

# Basic execution
result = await executor.execute(
    "skill_name",
    param1="value1"
)

# With context
context = SkillContext(
    execution_id="custom-id",
    timeout=10.0,
    max_retries=3
)
result = await executor.execute(
    "skill_name",
    context=context,
    use_cache=True
)

# Batch execution
tasks = [
    ("skill1", {"param": "value1"}),
    ("skill2", {"param": "value2"}),
]
results = await executor.execute_batch(tasks, max_concurrent=5)
```

### 4. Chains

Chains enable sequential skill composition:

```python
from ai.skills import SkillChain

chain = SkillChain(executor, "MyChain")

# Add steps
chain.add_step(
    "text_analyzer",
    parameters={"text": "Sample text"}
)

chain.add_step(
    "text_summarizer",
    transform_input=lambda data: {
        "text": f"Analysis: {data['word_count']} words",
        "max_length": 100
    },
    on_error="continue"  # Options: stop, continue, retry
)

# Execute chain
result = await chain.execute()
```

### 5. Event Hooks

Subscribe to execution events:

```python
async def before_execute(skill_name, context, params):
    print(f"Executing {skill_name}")

async def after_execute(skill_name, result):
    print(f"Completed: {skill_name}")

executor.register_hook("before_execute", before_execute)
executor.register_hook("after_execute", after_execute)
```

## Available Skills

The framework includes several example skills:

1. **TextAnalyzerSkill** - Analyzes text statistics (word count, sentences, frequency)
2. **TextSummarizerSkill** - Summarizes long text
3. **MathCalculatorSkill** - Evaluates mathematical expressions
4. **DataValidatorSkill** - Validates data against schemas
5. **JSONTransformerSkill** - Transforms JSON using mapping rules
6. **DataAggregatorSkill** - Aggregates data from multiple sources

## Web API

### Start Service

```bash
python -m ai.skills.web_service
```

Service runs on `http://localhost:8002` with interactive docs at `/docs`.

### API Endpoints

- `GET /api/skills` - List all skills
- `GET /api/skills/{name}` - Get skill details
- `POST /api/execute` - Execute a skill
- `POST /api/execute/stream` - Execute with streaming (SSE)
- `POST /api/batch` - Batch execution
- `POST /api/chain` - Execute a skill chain
- `GET /api/statistics` - System statistics
- `GET /api/history` - Execution history
- `GET /api/search?q=query` - Search skills

### Example API Usage

```python
import requests

# Execute skill
response = requests.post("http://localhost:8002/api/execute", json={
    "skill_name": "text_analyzer",
    "parameters": {"text": "Hello world"}
})

result = response.json()
print(result['data'])
```

## Creating Custom Skills

### Step 1: Define Skill Class

```python
from ai.skills import BaseSkill, SkillMetadata, SkillParameter, SkillCategory

class MyCustomSkill(BaseSkill):
    def __init__(self):
        metadata = SkillMetadata(
            name="my_skill",
            description="My custom skill",
            category=SkillCategory.DATA_PROCESSING,
            version="1.0.0",
            tags=["custom", "example"],
            parameters=[
                SkillParameter(
                    name="input",
                    type=str,
                    description="Input parameter",
                    required=True
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context, **kwargs):
        # Your logic here
        input_value = kwargs.get("input")
        result = process(input_value)

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data=result
        )
```

### Step 2: Register and Use

```python
registry.register(MyCustomSkill())
result = await executor.execute("my_skill", input="test")
```

## Advanced Features

### Caching

Results are automatically cached based on skill name and parameters:

```python
executor = SkillExecutor(registry, cache_ttl=300)  # 5 minute cache

# First call - executes skill
result1 = await executor.execute("skill_name", param="value")

# Second call - uses cache
result2 = await executor.execute("skill_name", param="value")
```

### Retry Logic

Failed executions can be automatically retried:

```python
context = SkillContext(
    execution_id="id",
    max_retries=3
)

result = await executor.execute("skill_name", context=context)
```

### Parameter Validation

Parameters are validated against skill metadata:

```python
# Automatic validation
result = await executor.execute(
    "skill_name",
    required_param="value"  # ✓ Valid
)

result = await executor.execute(
    "skill_name"  # ✗ Error: required_param missing
)
```

### Statistics & Monitoring

Track execution statistics:

```python
# Skill statistics
stats = skill.get_statistics()
print(f"Executions: {stats['execution_count']}")
print(f"Success rate: {stats['success_rate']}")

# Executor statistics
stats = executor.get_statistics()
print(f"Cache size: {stats['cache_size']}")

# Registry statistics
stats = registry.get_statistics()
print(f"Total skills: {stats['total_skills']}")
```

## Testing

```python
import pytest
from ai.skills import SkillRegistry, SkillExecutor
from ai.skills.example_skills import TextAnalyzerSkill

@pytest.mark.asyncio
async def test_text_analyzer():
    registry = SkillRegistry()
    executor = SkillExecutor(registry)
    registry.register(TextAnalyzerSkill())

    result = await executor.execute(
        "text_analyzer",
        text="Test text"
    )

    assert result.success
    assert result.data['word_count'] == 2
```

## Best Practices

1. **Single Responsibility**: Each skill should do one thing well
2. **Clear Metadata**: Provide detailed descriptions and parameter docs
3. **Error Handling**: Return appropriate errors with context
4. **Idempotency**: Skills should produce same output for same input
5. **Type Safety**: Use type hints and validation
6. **Testing**: Write tests for each skill
7. **Logging**: Log important events and errors

## Comparison with SubAgent

| Feature | Skills | SubAgent |
|---------|--------|----------|
| Architecture | Flat, composable | Hierarchical |
| Use Case | Reusable functions | Task decomposition |
| Complexity | Simple, focused | Complex workflows |
| Orchestration | Chains | Coordinator |
| Best For | Utilities, tools | Multi-step tasks |

## Contributing

To add new skills:

1. Create skill class extending `BaseSkill`
2. Add to `example_skills.py` or create new module
3. Register in web service startup
4. Add tests
5. Update documentation

## License

See project LICENSE file.
