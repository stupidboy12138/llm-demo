# SubAgent Architecture

A hierarchical agent system where a coordinator agent delegates specialized tasks to multiple sub-agents.

## Architecture Overview

```
┌─────────────────────────────────────┐
│      Coordinator Agent              │
│  (Task Decomposition & Orchestration)│
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│  SubAgent   │  │  SubAgent   │
│  Registry   │  │   Pool      │
└──────┬──────┘  └──────┬──────┘
       │                │
       ▼                ▼
┌──────────────────────────────┐
│  Specialized Sub-Agents      │
├──────────────────────────────┤
│  • DataAnalysisSubAgent      │
│  • CodeGenerationSubAgent    │
│  • ResearchSubAgent          │
│  • ValidationSubAgent        │
└──────────────────────────────┘
```

## Features

- **Task Decomposition**: Automatically breaks complex tasks into manageable subtasks
- **Capability-Based Routing**: Routes tasks to agents based on their capabilities
- **Parallel Execution**: Executes independent subtasks concurrently
- **Result Aggregation**: Combines results from multiple agents into coherent answers
- **Validation**: Optional quality checking of results
- **Error Handling**: Graceful failure handling with detailed error reporting
- **Monitoring**: Real-time status tracking of all agents and tasks

## Core Components

### 1. BaseSubAgent
Abstract base class defining the interface for all sub-agents.

```python
from ai.subagent import BaseSubAgent, SubAgentCapability, TaskContext, TaskResult

class CustomAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            agent_id="custom",
            name="Custom Agent",
            capabilities=[SubAgentCapability.RESEARCH]
        )

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        # Your implementation
        pass

    def can_handle(self, task_type: str) -> bool:
        return "custom" in task_type.lower()
```

### 2. SubAgentRegistry
Manages registration and discovery of sub-agents.

```python
from ai.subagent import SubAgentRegistry

registry = SubAgentRegistry()
registry.register(my_agent)
agent = registry.find_best_agent(SubAgentCapability.RESEARCH)
```

### 3. CoordinatorAgent
Main orchestrator that coordinates multiple sub-agents.

```python
from ai.subagent import CoordinatorAgent

coordinator = CoordinatorAgent(registry)
result = await coordinator.execute_complex_task(
    "Your complex task here",
    decompose=True,
    validate_results=True
)
```

### 4. Specialized Agents

#### DataAnalysisSubAgent
- Statistical analysis
- Data summarization
- Pattern detection
- Trend analysis

#### CodeGenerationSubAgent
- Code generation
- Code refactoring
- Bug fixing
- Code review

#### ResearchSubAgent
- Information synthesis
- Literature review
- Knowledge extraction
- Summarization

#### ValidationSubAgent
- Output validation
- Quality assurance
- Consistency checking
- Error detection

## Quick Start

### Simple Usage

```python
import asyncio
from ai.subagent import (
    CoordinatorAgent,
    SubAgentRegistry,
    ResearchSubAgent
)

async def main():
    # Setup
    registry = SubAgentRegistry()
    registry.register(ResearchSubAgent())
    coordinator = CoordinatorAgent(registry)

    # Execute task
    result = await coordinator.execute_complex_task(
        "Explain quantum computing in simple terms"
    )

    print(result['result']['final_answer'])

asyncio.run(main())
```

### Running the Demo

```bash
# Full comprehensive demo
python -m ai.subagent.demo

# Quick start demo
python -m ai.subagent.simple_demo
```

## Usage Examples

### Example 1: Single Agent Task

```python
from ai.subagent import DataAnalysisSubAgent, TaskContext

agent = DataAnalysisSubAgent()
context = TaskContext(task_id="t1", task_type="analysis")

result = await agent.execute_with_tracking(
    "Analyze the trend in [10, 15, 18, 22, 25, 30]",
    context
)

print(result.data)
```

### Example 2: Complex Multi-Agent Task

```python
registry = SubAgentRegistry()
registry.register(CodeGenerationSubAgent())
registry.register(ValidationSubAgent())

coordinator = CoordinatorAgent(registry)

result = await coordinator.execute_complex_task(
    """
    Create a binary search function in Python with:
    1. Proper error handling
    2. Docstrings
    3. Unit tests
    Then validate the implementation.
    """,
    decompose=True,
    validate_results=True
)
```

### Example 3: Parallel Execution

```python
tasks = [
    "Calculate factorial of 10",
    "Explain recursion",
    "Analyze array [1,2,3,4,5]"
]

results = await asyncio.gather(*[
    coordinator.execute_complex_task(task, decompose=False)
    for task in tasks
])
```

## Workflow Pipeline

You can chain multiple agents in a workflow:

```python
# Research → Code → Analyze → Validate
research = await research_agent.execute_task(...)
code = await code_agent.execute_task(research.data)
analysis = await analysis_agent.execute_task(code.data)
validation = await validation_agent.execute_task(analysis.data)
```

## API Configuration

The agents use LiteLLM by default. Configure via environment or constructor:

```python
agent = ResearchSubAgent(
    api_base="https://your-api-endpoint/v1",
    api_key="your-api-key"
)
```

## Monitoring & Status

```python
# Get registry status
status = registry.get_registry_status()
print(f"Total agents: {status['total_agents']}")

# Get agent status
agent_status = agent.get_status()
print(f"Completed tasks: {agent_status['completed_tasks']}")

# Get coordinator history
history = coordinator.get_task_history(limit=5)
```

## Error Handling

All agents handle errors gracefully:

```python
result = await agent.execute_with_tracking(task, context)

if result.success:
    print(f"Success: {result.data}")
else:
    print(f"Error: {result.error}")
    print(f"Execution time: {result.execution_time}s")
```

## Extending the System

### Creating Custom SubAgents

```python
from ai.subagent import BaseSubAgent, SubAgentCapability

class MyCustomAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_custom",
            name="My Custom Agent",
            capabilities=[SubAgentCapability.RESEARCH]
        )

    async def execute_task(self, task, context):
        # Your custom logic
        return TaskResult(
            task_id=context.task_id,
            success=True,
            data={"result": "my data"}
        )

    def can_handle(self, task_type):
        return "my_task" in task_type.lower()
```

### Adding New Capabilities

```python
# In base_subagent.py, extend SubAgentCapability enum
class SubAgentCapability(Enum):
    # ... existing capabilities
    MY_CAPABILITY = "my_capability"
```

## Best Practices

1. **Task Granularity**: Break tasks into focused, single-purpose subtasks
2. **Error Handling**: Always check `result.success` before using `result.data`
3. **Parallel Execution**: Use `decompose=True` for complex tasks to enable parallelization
4. **Resource Management**: Monitor agent status to avoid overloading
5. **Validation**: Enable `validate_results=True` for critical tasks
6. **Logging**: Use the built-in logging for debugging and monitoring

## Performance Considerations

- **Parallel Execution**: Independent subtasks run concurrently
- **Load Balancing**: Registry automatically selects least-busy agents
- **Caching**: Consider implementing result caching for repeated tasks
- **Timeouts**: Set appropriate timeouts for long-running tasks

## Troubleshooting

**Agent not found:**
```python
# Ensure agent is registered
registry.register(my_agent)
```

**Task decomposition fails:**
```python
# Use decompose=False for simple tasks
result = await coordinator.execute_complex_task(task, decompose=False)
```

**Import errors:**
```python
# Ensure project root is in sys.path
import sys
sys.path.insert(0, "/path/to/llm-demo")
```

## License

See project root LICENSE file.

## Contributing

1. Create custom agents extending BaseSubAgent
2. Add new capabilities to SubAgentCapability enum
3. Register agents in the demo files
4. Update documentation

## Related

- [LangChain Integration](../langchain/README.md)
- [LangGraph Workflows](../langgraph/README.md)
- [A2A Protocol](../../a2a/README.md)
