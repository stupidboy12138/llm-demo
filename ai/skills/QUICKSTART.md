# Skills Framework - Quick Start Guide

## 5-Minute Quick Start

### 1. Run the Simple Demo

```bash
python -m ai.skills.simple_demo
```

This will demonstrate:
- Skill registration
- Text analysis
- Math calculation
- Skill chaining
- Statistics

### 2. Run the Comprehensive Demo

```bash
python -m ai.skills.demo
```

This showcases all features:
- Basic execution
- Skill discovery
- Data validation
- Skill chains
- Caching
- Event hooks
- Batch execution
- Error handling
- Statistics & monitoring

### 3. Start the Web Service

```bash
python -m ai.skills.web_service
```

Or with uvicorn:

```bash
uvicorn ai.skills.web_service:app --port 8002 --reload
```

Then visit:
- API: http://localhost:8002
- Interactive docs: http://localhost:8002/docs
- Alternative docs: http://localhost:8002/redoc

### 4. Test the API

```bash
python -m ai.skills.client_examples
```

## Basic Usage Example

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
        text="Hello world! This is AI."
    )

    print(f"Words: {result.data['word_count']}")
    print(f"Sentences: {result.data['sentence_count']}")

asyncio.run(main())
```

## Available Skills

1. **text_analyzer** - Text statistics and analysis
2. **text_summarizer** - Text summarization
3. **math_calculator** - Mathematical expressions
4. **data_validator** - Schema validation
5. **json_transformer** - JSON transformation
6. **data_aggregator** - Data aggregation

## API Examples

### List Skills

```bash
curl http://localhost:8002/api/skills
```

### Execute a Skill

```bash
curl -X POST http://localhost:8002/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "text_analyzer",
    "parameters": {"text": "Sample text"}
  }'
```

### Batch Execution

```bash
curl -X POST http://localhost:8002/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"skill_name": "math_calculator", "parameters": {"expression": "10 + 20"}},
      {"skill_name": "math_calculator", "parameters": {"expression": "5 * 4"}}
    ]
  }'
```

### Execute a Chain

```bash
curl -X POST http://localhost:8002/api/chain \
  -H "Content-Type: application/json" \
  -d '{
    "chain_name": "MyChain",
    "steps": [
      {"skill_name": "text_analyzer", "parameters": {"text": "Hello world"}},
      {"skill_name": "text_summarizer", "parameters": {"text": "Hello world", "max_length": 50}}
    ]
  }'
```

## Creating Your First Skill

```python
from ai.skills import (
    BaseSkill, SkillMetadata, SkillParameter,
    SkillCategory, SkillContext, SkillResult
)

class MySkill(BaseSkill):
    def __init__(self):
        metadata = SkillMetadata(
            name="my_skill",
            description="My custom skill",
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

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        input_data = kwargs.get("input")

        # Your logic here
        result = input_data.upper()

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={"output": result}
        )

# Use it
registry.register(MySkill())
result = await executor.execute("my_skill", input="hello")
print(result.data["output"])  # "HELLO"
```

## Creating a Skill Chain

```python
from ai.skills import SkillChain

chain = SkillChain(executor, "ProcessingChain")

# Step 1: Analyze
chain.add_step(
    "text_analyzer",
    parameters={"text": "Sample text to analyze"}
)

# Step 2: Transform the result
chain.add_step(
    "json_transformer",
    transform_input=lambda data: {
        "data": data,
        "mapping": {"word_count": "words"}
    }
)

# Execute
result = await chain.execute()
```

## Using Hooks

```python
async def log_execution(skill_name, context, params):
    print(f"Executing {skill_name}")

async def log_completion(skill_name, result):
    print(f"Completed {skill_name} in {result.execution_time}s")

executor.register_hook("before_execute", log_execution)
executor.register_hook("after_execute", log_completion)
```

## Common Patterns

### Pattern 1: Simple Execution

```python
result = await executor.execute("skill_name", param="value")
if result.success:
    print(result.data)
else:
    print(f"Error: {result.error}")
```

### Pattern 2: With Timeout and Retry

```python
from ai.skills import SkillContext

context = SkillContext(
    execution_id="custom-id",
    timeout=10.0,      # 10 second timeout
    max_retries=3      # Retry up to 3 times
)

result = await executor.execute(
    "skill_name",
    context=context,
    param="value"
)
```

### Pattern 3: Batch Processing

```python
tasks = [
    ("skill1", {"param": "value1"}),
    ("skill2", {"param": "value2"}),
    ("skill3", {"param": "value3"}),
]

results = await executor.execute_batch(tasks, max_concurrent=5)

for i, result in enumerate(results):
    if result.success:
        print(f"Task {i}: {result.data}")
```

### Pattern 4: Chained Processing

```python
chain = SkillChain(executor)

chain.add_step("skill1", parameters={"param": "value"})
chain.add_step(
    "skill2",
    transform_input=lambda data: {"param": data["output"]},
    on_error="continue"  # or "stop", "retry"
)

result = await chain.execute()
```

## Monitoring and Statistics

```python
# Skill statistics
skill = registry.get("skill_name")
stats = skill.get_statistics()
print(f"Executions: {stats['execution_count']}")
print(f"Success rate: {stats['success_rate']:.1%}")

# Executor statistics
stats = executor.get_statistics()
print(f"Total: {stats['total_executions']}")
print(f"Cache: {stats['cache_size']} items")

# Registry statistics
stats = registry.get_statistics()
print(f"Skills: {stats['total_skills']}")
```

## Troubleshooting

### Issue: Skill not found

```python
# Check if skill is registered
if "skill_name" in registry:
    print("Skill is registered")
else:
    print("Skill not found")

# List all skills
for skill in registry.list_all():
    print(skill.metadata.name)
```

### Issue: Parameter validation error

```python
# Check skill metadata
skill = registry.get("skill_name")
metadata = skill.metadata.to_dict()

for param in metadata['parameters']:
    print(f"{param['name']}: {param['type']} (required: {param['required']})")
```

### Issue: Execution timeout

```python
# Increase timeout
context = SkillContext(
    execution_id="id",
    timeout=30.0  # 30 seconds
)

result = await executor.execute("skill_name", context=context)
```

## Next Steps

1. Read the full documentation: [README.md](README.md)
2. Explore example skills: [example_skills.py](example_skills.py)
3. Run comprehensive demo: `python -m ai.skills.demo`
4. Start web service and try the API
5. Create your own custom skills

## Support

- Full documentation: [ai/skills/README.md](README.md)
- Project documentation: [CLAUDE.md](../../CLAUDE.md)
- Examples: [demo.py](demo.py), [simple_demo.py](simple_demo.py)
- API examples: [client_examples.py](client_examples.py)
