"""
SubAgent Web Service

FastAPI service exposing the subagent architecture via REST API.

Usage:
    uvicorn ai.subagent.web_service:app --reload --port 8001

Endpoints:
    POST /api/task - Execute a task
    GET /api/status - Get system status
    GET /api/agents - List all agents
    GET /api/history - Get task history
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime

from ai.subagent import (
    CoordinatorAgent,
    SubAgentRegistry,
    DataAnalysisSubAgent,
    CodeGenerationSubAgent,
    ResearchSubAgent,
    ValidationSubAgent
)

# Initialize FastAPI app
app = FastAPI(
    title="SubAgent API",
    description="Hierarchical agent coordination system",
    version="1.0.0"
)

# Global registry and coordinator
registry = SubAgentRegistry()
coordinator: Optional[CoordinatorAgent] = None


# Pydantic models
class TaskRequest(BaseModel):
    """Request model for task execution"""
    task: str = Field(..., description="Task description")
    decompose: bool = Field(True, description="Whether to decompose the task")
    validate: bool = Field(True, description="Whether to validate results")
    priority: int = Field(3, ge=1, le=5, description="Task priority (1-5)")


class TaskResponse(BaseModel):
    """Response model for task execution"""
    task_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
    subtasks_executed: int


class AgentStatus(BaseModel):
    """Model for agent status"""
    agent_id: str
    name: str
    capabilities: List[str]
    is_busy: bool
    active_tasks: int
    completed_tasks: int


class SystemStatus(BaseModel):
    """Model for system status"""
    status: str
    total_agents: int
    total_tasks_executed: int
    uptime: str


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global coordinator

    # Register all specialized agents
    registry.register(DataAnalysisSubAgent())
    registry.register(CodeGenerationSubAgent())
    registry.register(ResearchSubAgent())
    registry.register(ValidationSubAgent())

    # Create coordinator
    coordinator = CoordinatorAgent(registry)

    print("✓ SubAgent service started")
    print(f"✓ Registered {len(registry)} agents")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SubAgent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.post("/api/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a task using the agent coordination system.

    Args:
        request: TaskRequest containing task details

    Returns:
        TaskResponse with execution results
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    try:
        result = await coordinator.execute_complex_task(
            task=request.task,
            decompose=request.decompose,
            validate_results=request.validate
        )

        return TaskResponse(
            task_id=result["task_id"],
            success=result["success"],
            result=result.get("result"),
            error=result.get("error"),
            execution_time=result["execution_time"],
            subtasks_executed=result.get("subtasks_executed", 0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/task/stream")
async def execute_task_stream(request: TaskRequest):
    """
    Execute a task with streaming response (SSE).

    Args:
        request: TaskRequest containing task details

    Returns:
        Streaming response with task progress
    """
    async def generate():
        try:
            yield f"data: {json.dumps({'status': 'started', 'task': request.task})}\n\n"

            result = await coordinator.execute_complex_task(
                task=request.task,
                decompose=request.decompose,
                validate_results=request.validate
            )

            # Stream subtask results
            if "result" in result and "detailed_results" in result["result"]:
                for idx, sub_result in enumerate(result["result"]["detailed_results"]):
                    yield f"data: {json.dumps({'subtask': idx, 'result': sub_result})}\n\n"
                    await asyncio.sleep(0.1)

            # Final result
            yield f"data: {json.dumps({'status': 'completed', 'result': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """
    Get system status.

    Returns:
        System status including agent information
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    status = coordinator.get_status()
    registry_status = registry.get_registry_status()

    return SystemStatus(
        status="running",
        total_agents=registry_status["total_agents"],
        total_tasks_executed=status["total_tasks_executed"],
        uptime="unknown"  # TODO: Calculate actual uptime
    )


@app.get("/api/agents", response_model=List[AgentStatus])
async def list_agents():
    """
    List all registered agents.

    Returns:
        List of agent status information
    """
    registry_status = registry.get_registry_status()

    return [
        AgentStatus(
            agent_id=agent["agent_id"],
            name=agent["name"],
            capabilities=agent["capabilities"],
            is_busy=agent["is_busy"],
            active_tasks=agent["active_tasks"],
            completed_tasks=agent["completed_tasks"]
        )
        for agent in registry_status["agents"]
    ]


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get detailed information about a specific agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent status and details
    """
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return agent.get_status()


@app.get("/api/history")
async def get_history(limit: int = 10):
    """
    Get task execution history.

    Args:
        limit: Maximum number of history items to return

    Returns:
        List of recent tasks
    """
    if not coordinator:
        raise HTTPException(status_code=503, detail="Coordinator not initialized")

    history = coordinator.get_task_history(limit=limit)

    return {
        "total": len(history),
        "limit": limit,
        "history": history
    }


@app.get("/api/capabilities")
async def get_capabilities():
    """
    Get all available capabilities in the system.

    Returns:
        List of capabilities and their agent mappings
    """
    registry_status = registry.get_registry_status()

    capabilities = {}
    for agent in registry_status["agents"]:
        for cap in agent["capabilities"]:
            if cap not in capabilities:
                capabilities[cap] = []
            capabilities[cap].append({
                "agent_id": agent["agent_id"],
                "agent_name": agent["name"]
            })

    return capabilities


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "coordinator": coordinator is not None,
        "agents": len(registry)
    }


# Example usage in Python client
"""
import requests

# Execute task
response = requests.post(
    "http://localhost:8001/api/task",
    json={
        "task": "Create a Python function to calculate prime numbers",
        "decompose": True,
        "validate": True
    }
)
print(response.json())

# Get status
status = requests.get("http://localhost:8001/api/status")
print(status.json())

# List agents
agents = requests.get("http://localhost:8001/api/agents")
print(agents.json())
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
