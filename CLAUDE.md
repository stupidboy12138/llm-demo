# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LLM demonstration project showcasing various agent architectures and LLM frameworks including LangChain, LangGraph, a custom Agent-to-Agent (A2A) communication protocol, and Google's A2UI (Agent-to-User Interface) protocol.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt

# Activate virtual environment (if needed)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Running Examples

**A2A Protocol Demo:**
```bash
python -m a2a.demo
python -m a2a.simple_demo
```

**A2UI Protocol Demo (Google's Agent-to-User Interface):**
```bash
# Run comprehensive demo
python -m a2ui.demo

# Run simple demo
python -m a2ui.simple_demo
```

**LangChain Agent Service:**
```bash
cd ai/langchain
python langchain_demo.py
# Service starts at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**LangGraph Examples:**
```bash
python -m ai.langgraph.demo
python -m ai.langgraph.langgraph_workflows
python -m ai.langgraph.langgraph_thinking
```

**Skills Framework:**
```bash
# Run simple demo
python -m ai.skills.simple_demo

# Run comprehensive demo (all features)
python -m ai.skills.demo

# Start web service
python -m ai.skills.web_service
# Or with uvicorn
uvicorn ai.skills.web_service:app --port 8002
# Service starts at http://localhost:8002
# API docs at http://localhost:8002/docs

# Run client examples
python -m ai.skills.client_examples
```

**SubAgent Architecture:**
```bash
# Run comprehensive demo
python -m ai.subagent.demo

# Run simple demo
python -m ai.subagent.simple_demo

# Start web service
uvicorn ai.subagent.web_service:app --port 8001
# Service starts at http://localhost:8001
# API docs at http://localhost:8001/docs

# Run client examples
python -m ai.subagent.client_examples

# Run tests
pytest ai/subagent/test_subagent.py -v
```

## Architecture

### A2UI (Agent-to-User Interface) Protocol (`a2ui/`)

Implementation of Google's A2UI protocol (v0.9) that enables AI agents to generate rich, interactive UIs through declarative JSON format. Based on https://github.com/google/A2UI

**Core Concepts:**
- **Security-first**: Declarative data format, not executable code
- **LLM-friendly**: Flat component list with ID references for incremental updates
- **Framework-agnostic**: Same JSON payload works across different renderers

**Core Components:**
- **protocol.py**: Message types (CreateSurface, UpdateComponents, UpdateDataModel, DeleteSurface), component definitions (Text, Button, TextField, Row, Column, Card, etc.), and client events (ActionEvent, ErrorEvent)
- **builder.py**: Fluent builder API for constructing A2UI surfaces and components
- **renderer.py**: Base renderer class and ConsoleRenderer for terminal output
- **agent.py**: Base A2UIAgent class and SimpleA2UIAgent for demonstration

**Message Flow:**
1. Server sends `CreateSurface` to initialize a UI surface
2. Server sends `UpdateComponents` with component tree (must include "root" component)
3. Server sends `UpdateDataModel` to populate data bindings
4. Client sends `ActionEvent` when user interacts with UI

**Component Types:**
- Display: Text, Image, Icon, Video, AudioPlayer
- Layout: Row, Column, List, Card, Tabs, Divider, Modal
- Input: Button, TextField, CheckBox, ChoicePicker, Slider, DateTimeInput

### A2A (Agent-to-Agent) Protocol (`a2a/`)

A custom implementation of an agent communication protocol supporting asynchronous message passing between autonomous agents.

**Core Components:**
- **protocol.py**: Defines message format with 4 types (REQUEST, RESPONSE, NOTIFICATION, ERROR)
- **base_agent.py**: Abstract base class providing message handling, request-response patterns, and notification mechanisms
- **message_broker.py**: Central message router handling agent registration and message routing
- **agent_impl.py**: Concrete implementations inheriting from BaseAgent
- **demo_agents.py**: Sample agents (WeatherAgent, DataAnalysisAgent, TaskCoordinatorAgent, MonitorAgent)

**Key Patterns:**
- Request-response pattern: Use `send_request()` to send and await response
- Notification pattern: Use `send_notification()` for fire-and-forget messages
- Message correlation: Uses `correlation_id` to link requests with responses
- Async handlers: All message handlers are async functions registered via `register_handler()`

### LangChain Integration (`ai/langchain/`)

FastAPI-based asynchronous service wrapping LangChain agents with custom tools.

**Key Features:**
- Uses LiteLLM as backend (OpenAI-compatible API)
- Three built-in tools: `get_current_time`, `calculate_math`, `search_knowledge`
- Supports streaming responses via SSE
- Batch request processing
- Conversation history management

**API Configuration:**
```python
LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-deepbank-dev"
```

**Endpoints:**
- `POST /agent/chat` - Non-streaming chat
- `POST /agent/chat-stream` - Streaming chat with SSE
- `POST /agent/batch` - Batch processing
- `GET /health` - Health check

### LangGraph Workflows (`ai/langgraph/`)

Demonstrates LangGraph's state graph capabilities for building multi-step LLM workflows.

**Key Concepts:**
- State management using TypedDict
- Node-based workflow with conditional branching
- Checkpoint/memory support with `MemorySaver`
- Tool binding and structured outputs

### Skills Framework (`ai/skills/`)

A flexible, composable skills system for building AI capabilities with reusable, testable components.

**Core Components:**
- **base_skill.py**: Abstract base class and core types (SkillCategory, SkillContext, SkillResult, SkillParameter)
- **skill_registry.py**: Centralized registration, discovery, and lifecycle management of skills
- **skill_executor.py**: Execution engine with caching, retry logic, event hooks, and monitoring
- **skill_chain.py**: Enables composition and sequential execution of multiple skills
- **example_skills.py**: Sample skill implementations (TextAnalyzer, MathCalculator, DataValidator, etc.)

**Key Features:**
- **Modular Design**: Self-contained, reusable skills with clear metadata
- **Discovery**: Search skills by name, category, or tags
- **Caching**: Automatic result caching with TTL
- **Retry Logic**: Configurable retry with exponential backoff
- **Composition**: Chain multiple skills into workflows
- **Event Hooks**: Subscribe to execution events (before_execute, after_execute, on_cache_hit)
- **Batch Execution**: Run multiple skills in parallel with concurrency control
- **Statistics**: Track execution metrics and performance
- **Web API**: FastAPI service with REST and streaming endpoints

**Skill Categories:**
- `DATA_PROCESSING` - Data manipulation and aggregation
- `TEXT_ANALYSIS` - Text analytics and NLP
- `CODE_GENERATION` - Code generation and manipulation
- `COMPUTATION` - Mathematical and computational tasks
- `VALIDATION` - Data validation and quality checks
- `TRANSFORMATION` - Data transformation and mapping

**API Endpoints (Web Service):**
- `GET /api/skills` - List all registered skills
- `GET /api/skills/{name}` - Get skill details and metadata
- `POST /api/execute` - Execute a single skill
- `POST /api/execute/stream` - Execute with streaming response (SSE)
- `POST /api/batch` - Execute multiple skills in parallel
- `POST /api/chain` - Execute a skill chain/workflow
- `GET /api/statistics` - Get execution statistics
- `GET /api/history` - Get execution history
- `GET /api/search?q=query` - Search for skills

### SubAgent Architecture (`ai/subagent/`)

A hierarchical agent coordination system where a coordinator agent manages multiple specialized sub-agents.

**Core Components:**
- **base_subagent.py**: Abstract base class defining the sub-agent interface with task execution, capability checking, and status tracking
- **subagent_registry.py**: Registry for agent registration, discovery, and load balancing
- **coordinator_agent.py**: Main orchestrator that decomposes tasks, delegates to sub-agents, and aggregates results
- **specialized_agents.py**: Concrete implementations (DataAnalysisSubAgent, CodeGenerationSubAgent, ResearchSubAgent, ValidationSubAgent)

**Key Features:**
- Task decomposition: Automatically breaks complex tasks into subtasks
- Capability-based routing: Routes tasks to appropriate agents based on capabilities
- Parallel execution: Runs independent subtasks concurrently
- Result aggregation: Combines results from multiple agents into coherent answers
- Validation: Optional quality checking of results
- Web API: FastAPI service exposing the architecture via REST endpoints

**API Endpoints (Web Service):**
- `POST /api/task` - Execute a task
- `POST /api/task/stream` - Execute with streaming response (SSE)
- `GET /api/status` - Get system status
- `GET /api/agents` - List all agents
- `GET /api/history` - Get task history
- `GET /api/capabilities` - Get available capabilities

**Capabilities:**
- `DATA_ANALYSIS` - Statistical analysis, data summarization, pattern detection
- `CODE_GENERATION` - Code generation, refactoring, bug fixing
- `RESEARCH` - Information gathering, synthesis, summarization
- `VALIDATION` - Quality assurance, consistency checking

## Project Structure

```
llm-demo/
├── a2a/                    # Custom A2A protocol implementation
│   ├── protocol.py         # Message format definitions
│   ├── base_agent.py       # Agent base class
│   ├── message_broker.py   # Message routing
│   ├── agent_impl.py       # Concrete agent implementations
│   ├── demo_agents.py      # Example agents
│   └── demo.py            # Demo scenarios
├── a2ui/                   # Google A2UI protocol implementation
│   ├── protocol.py         # Message types and component definitions
│   ├── builder.py          # Fluent builder API
│   ├── renderer.py         # Base renderer and ConsoleRenderer
│   ├── agent.py            # A2UIAgent base class and SimpleA2UIAgent
│   ├── demo.py             # Comprehensive demo
│   └── simple_demo.py      # Quick start demo
├── ai/
│   ├── langchain/         # LangChain + FastAPI service
│   │   ├── langchain_demo.py  # Main service file
│   │   └── test_client.py     # Client examples
│   ├── langgraph/         # LangGraph workflow examples
│   │   ├── langgraph_workflows.py  # State graph examples
│   │   └── langgraph_thinking.py   # Thinking/reasoning patterns
│   ├── skills/            # Composable skills framework
│   │   ├── base_skill.py          # Core abstractions and types
│   │   ├── skill_registry.py      # Skill registration and discovery
│   │   ├── skill_executor.py      # Execution engine
│   │   ├── skill_chain.py         # Skill composition
│   │   ├── example_skills.py      # Example implementations
│   │   ├── web_service.py         # FastAPI web service
│   │   ├── client_examples.py     # API client examples
│   │   ├── demo.py                # Comprehensive demo
│   │   ├── simple_demo.py         # Quick start demo
│   │   └── README.md              # Framework documentation
│   └── subagent/          # Hierarchical agent coordination
│       ├── base_subagent.py      # Base class and interfaces
│       ├── subagent_registry.py  # Agent registration and discovery
│       ├── coordinator_agent.py  # Main orchestrator
│       ├── specialized_agents.py # Specialized agent implementations
│       ├── web_service.py        # FastAPI web service
│       ├── client_examples.py    # API client examples
│       ├── demo.py               # Comprehensive demo
│       ├── simple_demo.py        # Quick start demo
│       └── test_subagent.py      # Unit tests
├── pyproject.toml         # Project dependencies
└── main.py               # Entry point (placeholder)
```

## Dependencies

Core dependencies (see [pyproject.toml](pyproject.toml)):
- `langchain>=1.2.0` - LLM application framework
- `langgraph>=1.0.5` - State graph workflows
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.0` - ASGI server
- `langchain-openai>=0.2.0` - OpenAI integration
- `langchain-anthropic>=1.3.0` - Anthropic integration
- `pydantic>=2.10.0` - Data validation

## Adding Custom Tools (LangChain)

Tools must be decorated with `@tool` and include clear docstrings:

```python
from langchain_core.tools import tool

@tool
def your_tool(param: str) -> str:
    """Tool description explaining when to use this tool."""
    # Implementation
    return result
```

Add to tools list in [ai/langchain/langchain_demo.py](ai/langchain/langchain_demo.py).

## Creating Custom Agents (A2A)

Extend `BrokerAgent` and register handlers:

```python
from a2a.agent_impl import BrokerAgent
from a2a.protocol import A2AMessage

class CustomAgent(BrokerAgent):
    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "CustomAgent", broker)
        self.register_handler("action_name", self.handle_action)

    async def handle_action(self, message: A2AMessage):
        # Process message
        return {"result": "data"}
```

## LangGraph State Graphs

Define state with TypedDict, create nodes as functions, and build graph:

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    field1: str
    field2: str

def node_function(state: State):
    return {"field1": "updated"}

graph = StateGraph(State)
graph.add_node("node_name", node_function)
graph.add_edge(START, "node_name")
graph.add_edge("node_name", END)
app = graph.compile()
```

## Creating Skills

Extend `BaseSkill` to create custom skills:

```python
from ai.skills import (
    BaseSkill, SkillMetadata, SkillParameter, SkillCategory,
    SkillContext, SkillResult
)

class CustomSkill(BaseSkill):
    def __init__(self):
        metadata = SkillMetadata(
            name="custom_skill",
            description="Does something useful",
            category=SkillCategory.DATA_PROCESSING,
            version="1.0.0",
            tags=["custom", "example"],
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
        # Process data...
        result = process(input_data)

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data=result
        )

# Register and use
from ai.skills import SkillRegistry, SkillExecutor

registry = SkillRegistry()
executor = SkillExecutor(registry)

registry.register(CustomSkill())
result = await executor.execute("custom_skill", input="test")
```

## Creating Skill Chains

Compose multiple skills into workflows:

```python
from ai.skills import SkillChain

chain = SkillChain(executor, "MyWorkflow")

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

## Creating SubAgents

Extend `BaseSubAgent` to create custom sub-agents:

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
        result = await process_task(task)
        return TaskResult(
            task_id=context.task_id,
            success=True,
            data=result
        )

    def can_handle(self, task_type: str) -> bool:
        return "custom" in task_type.lower()

# Register and use
from ai.subagent import SubAgentRegistry, CoordinatorAgent

registry = SubAgentRegistry()
registry.register(CustomAgent())
coordinator = CoordinatorAgent(registry)

result = await coordinator.execute_complex_task("Your task here")
```

## Creating A2UI Agents

Extend `A2UIAgent` to create agents that generate rich UIs:

```python
from a2ui import A2UIAgent, A2UIAgentConfig, A2UIAgentResponse, TextVariant

class MyUIAgent(A2UIAgent):
    def __init__(self):
        config = A2UIAgentConfig(
            agent_id="my_agent",
            name="My UI Agent",
            description="Generates custom UIs"
        )
        super().__init__(config)

    async def process_query(self, query: str, context: dict | None = None) -> A2UIAgentResponse:
        surface = self.create_surface()
        c = self.component()

        # Build UI components
        surface.add_components(
            c.column("root", ["title", "content", "action_btn"]),
            c.text("title", f"Response to: {query}", variant=TextVariant.H1),
            c.text("content", "Your content here"),
            c.button("action_btn", "btn_label", "my_action", primary=True),
            c.text("btn_label", "Click Me"),
        )

        # Set data model for bindings
        surface.set_root_data({"user": {"name": "Alice"}})

        return A2UIAgentResponse(
            text="Here's your UI",
            ui_messages=surface.to_json()
        )

# Use the agent
agent = MyUIAgent()
response = await agent.process_query("Show me a dashboard")
print(response.ui_messages)  # A2UI JSON messages
```

## Using A2UI Builder Directly

```python
from a2ui import A2UIBuilder, ComponentBuilder, TextVariant, Justification

builder = A2UIBuilder()
c = ComponentBuilder

# Create a surface
surface = builder.create_surface("my_surface")

# Add components with fluent API
surface.add_components(
    c.column("root", ["header", "form", "buttons"]),
    c.text("header", "Contact Form", variant=TextVariant.H1),
    c.column("form", ["name_field", "email_field"]),
    c.text_field("name_field", "Name", value=c.path("/form/name")),
    c.text_field("email_field", "Email", value=c.path("/form/email")),
    c.row("buttons", ["submit_btn"], justify=Justification.END),
    c.button("submit_btn", "submit_label", "submit",
             context=[("name", c.path("/form/name"))], primary=True),
    c.text("submit_label", "Submit"),
)

# Set initial data
surface.set_root_data({"form": {"name": "", "email": ""}})

# Get A2UI JSON messages
messages = surface.to_json()
```

## Testing APIs

**LangChain:**
Use the provided test client in [ai/langchain/test_client.py](ai/langchain/test_client.py) for examples of:
- Streaming responses
- Batch requests
- History management
- Error handling

**Skills:**
Use the client examples in [ai/skills/client_examples.py](ai/skills/client_examples.py) for:
- Skill discovery and metadata
- Single skill execution
- Batch execution
- Chain execution
- Streaming responses
- Statistics and monitoring

Full documentation available in [ai/skills/README.md](ai/skills/README.md)

**SubAgent:**
Use the client examples in [ai/subagent/client_examples.py](ai/subagent/client_examples.py) for:
- Task execution
- Streaming responses
- Agent monitoring
- Batch processing
- Task history

Run tests:
```bash
pytest ai/subagent/test_subagent.py -v
```
