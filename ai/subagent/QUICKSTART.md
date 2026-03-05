"""
SubAgent Architecture - Quick Start Guide
==========================================

This guide will help you get started with the SubAgent architecture in 5 minutes.

## What is SubAgent?

SubAgent is a hierarchical agent coordination system where:
- A **Coordinator Agent** breaks down complex tasks
- Multiple **Specialized Sub-Agents** handle specific types of work
- Results are automatically aggregated into coherent answers

## Quick Start

### 1. Run the Simple Demo (30 seconds)

```bash
python -m ai.subagent.simple_demo
```

This will show you a basic example of task coordination.

### 2. Run the Comprehensive Demo (2 minutes)

```bash
python -m ai.subagent.demo
```

This demonstrates:
- Simple task delegation
- Complex task decomposition
- Parallel execution
- Error handling
- Registry monitoring
- Complete workflow pipeline

### 3. Start the Web Service (API Mode)

```bash
uvicorn ai.subagent.web_service:app --port 8001
```

Then visit: http://localhost:8001/docs for interactive API documentation.

### 4. Use the Python Client

```python
from ai.subagent import (
    CoordinatorAgent,
    SubAgentRegistry,
    ResearchSubAgent,
    CodeGenerationSubAgent
)

# Setup
registry = SubAgentRegistry()
registry.register(ResearchSubAgent())
registry.register(CodeGenerationSubAgent())

coordinator = CoordinatorAgent(registry)

# Execute a task
result = await coordinator.execute_complex_task(
    "Create a function to calculate factorial with explanation"
)

print(result['result']['final_answer'])
```

### 5. Use the REST API Client

```python
from ai.subagent.client_examples import SubAgentClient

client = SubAgentClient("http://localhost:8001")

# Execute task
result = client.execute_task(
    "Explain binary search and implement it in Python"
)

print(f"Success: {result['success']}")
print(f"Answer: {result['result']['final_answer']}")
```

## Available Sub-Agents

1. **DataAnalysisSubAgent**
   - Statistical analysis
   - Data summarization
   - Pattern detection
   - Trend analysis

2. **CodeGenerationSubAgent**
   - Code generation
   - Refactoring
   - Bug fixing
   - Code review

3. **ResearchSubAgent**
   - Information gathering
   - Knowledge synthesis
   - Literature review
   - Summarization

4. **ValidationSubAgent**
   - Quality assurance
   - Output validation
   - Consistency checking
   - Error detection

## Common Use Cases

### Use Case 1: Ask a Research Question

```python
result = await coordinator.execute_complex_task(
    "Explain how neural networks work",
    decompose=False  # Simple research task
)
```

### Use Case 2: Generate and Validate Code

```python
result = await coordinator.execute_complex_task(
    "Create a binary search tree implementation with validation",
    decompose=True,   # Break into subtasks
    validate_results=True  # Validate the output
)
```

### Use Case 3: Data Analysis Pipeline

```python
result = await coordinator.execute_complex_task(
    "Analyze sales data [100, 200, 150, 300, 250] and create a visualization",
    decompose=True
)
```

### Use Case 4: Complete Development Workflow

```python
# Research → Code → Analyze → Validate
result = await coordinator.execute_complex_task(
    \"\"\"
    1. Research quicksort algorithm
    2. Implement it in Python
    3. Analyze time complexity
    4. Validate the implementation
    \"\"\",
    decompose=True,
    validate_results=True
)
```

## API Examples

### Execute Task (REST)

```bash
curl -X POST "http://localhost:8001/api/task" \\
  -H "Content-Type: application/json" \\
  -d '{
    "task": "Explain recursion with examples",
    "decompose": false,
    "validate": false
  }'
```

### Get System Status

```bash
curl "http://localhost:8001/api/status"
```

### List All Agents

```bash
curl "http://localhost:8001/api/agents"
```

### View Task History

```bash
curl "http://localhost:8001/api/history?limit=5"
```

## Creating Custom Sub-Agents

```python
from ai.subagent import BaseSubAgent, SubAgentCapability, TaskContext, TaskResult

class TranslationAgent(BaseSubAgent):
    def __init__(self):
        super().__init__(
            agent_id="translator",
            name="Translation Agent",
            capabilities=[SubAgentCapability.TRANSLATION]
        )

    async def execute_task(self, task: str, context: TaskContext) -> TaskResult:
        # Your translation logic here
        translated = await self.translate(task)

        return TaskResult(
            task_id=context.task_id,
            success=True,
            data={"translation": translated}
        )

    def can_handle(self, task_type: str) -> bool:
        return "translate" in task_type.lower()

# Register your custom agent
registry.register(TranslationAgent())
```

## Advanced Features

### Parallel Task Execution

```python
tasks = [
    "Explain async/await in Python",
    "Generate a quicksort implementation",
    "Analyze dataset [1, 5, 10, 15, 20]"
]

results = await asyncio.gather(*[
    coordinator.execute_complex_task(task, decompose=False)
    for task in tasks
])
```

### Load Balancing

The registry automatically selects the least-busy agent:

```python
# Register multiple agents of the same type
registry.register(DataAnalysisSubAgent("analyst-1"))
registry.register(DataAnalysisSubAgent("analyst-2"))

# Tasks are automatically distributed
```

### Monitoring and Status

```python
# Get registry status
status = registry.get_registry_status()
print(f"Total agents: {status['total_agents']}")

# Get individual agent status
agent = registry.get_agent("code_generator")
print(f"Tasks completed: {agent.get_status()['completed_tasks']}")

# Get coordinator history
history = coordinator.get_task_history(limit=10)
```

## Testing

```bash
# Run all tests
pytest ai/subagent/test_subagent.py -v

# Run specific test
pytest ai/subagent/test_subagent.py::TestCoordinatorAgent -v

# Run with coverage
pytest ai/subagent/test_subagent.py --cov=ai.subagent
```

## Architecture Diagram

```
User Request
     ↓
CoordinatorAgent (Orchestrator)
     ↓
Task Decomposition (via LLM)
     ↓
SubAgentRegistry (Router)
     ↓
┌─────────────┬─────────────┬─────────────┬──────────────┐
│   Research  │    Code     │   Analysis  │  Validation  │
│   SubAgent  │  SubAgent   │  SubAgent   │   SubAgent   │
└─────────────┴─────────────┴─────────────┴──────────────┘
     ↓             ↓              ↓              ↓
     └─────────────┴──────────────┴──────────────┘
                    ↓
            Result Aggregation
                    ↓
            Final Answer to User
```

## Performance Tips

1. **Use decompose=False for simple tasks** - Skips decomposition overhead
2. **Disable validation for non-critical tasks** - Saves execution time
3. **Register multiple agents** - Enables parallel execution and load balancing
4. **Use streaming for long tasks** - Get progress updates in real-time
5. **Monitor agent status** - Identify bottlenecks and busy agents

## Troubleshooting

**Problem: "No agent found for capability"**
```python
# Solution: Register an agent with that capability
registry.register(ResearchSubAgent())
```

**Problem: Tasks taking too long**
```python
# Solution: Disable decomposition or validation
result = await coordinator.execute_complex_task(
    task,
    decompose=False,
    validate_results=False
)
```

**Problem: Import errors**
```python
# Solution: Ensure you're in the project root
import sys
sys.path.insert(0, "/path/to/llm-demo")
```

## Next Steps

1. Read the full documentation: [ai/subagent/README.md](README.md)
2. Explore the demos: `python -m ai.subagent.demo`
3. Review test cases: [ai/subagent/test_subagent.py](test_subagent.py)
4. Check client examples: [ai/subagent/client_examples.py](client_examples.py)
5. Create your own custom agents!

## Support

- GitHub Issues: Report bugs or request features
- Documentation: See README.md for detailed API docs
- Examples: Check demo.py and client_examples.py

Happy coding with SubAgents! 🚀
"""
