"""
Skills Framework Web Service

FastAPI-based web service for skill execution.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import asyncio
import json
import uuid

from .base_skill import SkillContext, SkillCategory
from .skill_registry import SkillRegistry
from .skill_executor import SkillExecutor
from .skill_chain import SkillChain, ChainStep
from .example_skills import (
    TextAnalyzerSkill,
    MathCalculatorSkill,
    TextSummarizerSkill,
    DataValidatorSkill,
    JSONTransformerSkill,
    DataAggregatorSkill
)

# Initialize FastAPI
app = FastAPI(
    title="AI Skills Framework API",
    description="Web service for executing AI skills",
    version="1.0.0"
)

# Global registry and executor
registry = SkillRegistry()
executor = SkillExecutor(registry, cache_ttl=300)


# Request/Response models
class SkillExecutionRequest(BaseModel):
    """Request to execute a skill"""
    skill_name: str = Field(..., description="Name of the skill to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")
    use_cache: bool = Field(default=True, description="Whether to use cache")
    timeout: Optional[float] = Field(default=None, description="Execution timeout in seconds")


class SkillExecutionResponse(BaseModel):
    """Response from skill execution"""
    execution_id: str
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchExecutionRequest(BaseModel):
    """Request for batch execution"""
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks to execute")
    max_concurrent: int = Field(default=5, description="Maximum concurrent executions")


class ChainExecutionRequest(BaseModel):
    """Request to execute a skill chain"""
    chain_name: str = Field(..., description="Name of the chain")
    steps: List[Dict[str, Any]] = Field(..., description="Chain steps")
    initial_input: Optional[Any] = Field(default=None, description="Initial input to chain")


class SkillInfo(BaseModel):
    """Skill information"""
    name: str
    description: str
    category: str
    version: str
    tags: List[str]
    parameters: List[Dict[str, Any]]


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize skills on startup"""
    # Register all example skills
    registry.register(TextAnalyzerSkill())
    registry.register(MathCalculatorSkill())
    registry.register(TextSummarizerSkill())
    registry.register(DataValidatorSkill())
    registry.register(JSONTransformerSkill())
    registry.register(DataAggregatorSkill())

    await registry.initialize_all()
    print(f"✓ Registered {len(registry)} skills")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await registry.cleanup_all()


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Skills Framework",
        "version": "1.0.0",
        "endpoints": {
            "skills": "/api/skills",
            "execute": "/api/execute",
            "batch": "/api/batch",
            "chain": "/api/chain",
            "statistics": "/api/statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "skills_registered": len(registry)
    }


@app.get("/api/skills", response_model=List[SkillInfo])
async def list_skills():
    """List all registered skills"""
    skills = registry.list_all()
    return [
        SkillInfo(
            name=skill.metadata.name,
            description=skill.metadata.description,
            category=skill.metadata.category.value,
            version=skill.metadata.version,
            tags=skill.metadata.tags,
            parameters=[
                {
                    "name": p.name,
                    "type": p.type.__name__,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in skill.metadata.parameters
            ]
        )
        for skill in skills
    ]


@app.get("/api/skills/{skill_name}")
async def get_skill(skill_name: str):
    """Get details of a specific skill"""
    skill = registry.get(skill_name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    return {
        "metadata": skill.metadata.to_dict(),
        "statistics": skill.get_statistics()
    }


@app.get("/api/skills/category/{category}")
async def get_skills_by_category(category: str):
    """Get skills by category"""
    try:
        cat = SkillCategory(category)
        skills = registry.get_by_category(cat)
        return [skill.metadata.to_dict() for skill in skills]
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {category}")


@app.post("/api/execute", response_model=SkillExecutionResponse)
async def execute_skill(request: SkillExecutionRequest):
    """Execute a single skill"""
    # Create context
    context = SkillContext(
        execution_id=str(uuid.uuid4()),
        timeout=request.timeout
    )

    # Execute
    result = await executor.execute(
        request.skill_name,
        context=context,
        use_cache=request.use_cache,
        **request.parameters
    )

    if not result.success and result.error_type == "SkillNotFoundError":
        raise HTTPException(status_code=404, detail=result.error)

    return SkillExecutionResponse(
        execution_id=result.execution_id,
        success=result.success,
        data=result.data,
        error=result.error,
        execution_time=result.execution_time,
        metadata=result.metadata
    )


@app.post("/api/execute/stream")
async def execute_skill_stream(request: SkillExecutionRequest):
    """Execute a skill with streaming response"""

    async def generate():
        # Send start event
        yield f"data: {json.dumps({'event': 'start', 'skill': request.skill_name})}\n\n"

        # Create context
        context = SkillContext(
            execution_id=str(uuid.uuid4()),
            timeout=request.timeout
        )

        # Execute
        result = await executor.execute(
            request.skill_name,
            context=context,
            use_cache=request.use_cache,
            **request.parameters
        )

        # Send result
        yield f"data: {json.dumps({'event': 'result', 'data': result.data, 'success': result.success})}\n\n"

        # Send complete event
        yield f"data: {json.dumps({'event': 'complete', 'execution_time': result.execution_time})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/batch")
async def execute_batch(request: BatchExecutionRequest):
    """Execute multiple skills in parallel"""
    tasks = [
        (task["skill_name"], task.get("parameters", {}))
        for task in request.tasks
    ]

    results = await executor.execute_batch(tasks, max_concurrent=request.max_concurrent)

    return {
        "total_tasks": len(tasks),
        "results": [
            {
                "execution_id": r.execution_id,
                "success": r.success,
                "data": r.data,
                "error": r.error,
                "execution_time": r.execution_time
            }
            for r in results
        ]
    }


@app.post("/api/chain")
async def execute_chain(request: ChainExecutionRequest):
    """Execute a skill chain"""
    chain = SkillChain(executor, request.chain_name)

    # Build chain
    for step in request.steps:
        chain.add_step(
            skill_name=step["skill_name"],
            parameters=step.get("parameters", {}),
            on_error=step.get("on_error", "stop")
        )

    # Execute
    result = await chain.execute(initial_input=request.initial_input)

    return {
        "execution_id": result.execution_id,
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "execution_time": result.execution_time,
        "metadata": result.metadata
    }


@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics"""
    return {
        "registry": registry.get_statistics(),
        "executor": executor.get_statistics()
    }


@app.get("/api/history")
async def get_history(limit: int = 100):
    """Get execution history"""
    history = executor.get_history(limit=limit)

    return {
        "total": len(history),
        "executions": [
            {
                "skill_name": skill_name,
                "execution_id": result.execution_id,
                "success": result.success,
                "execution_time": result.execution_time
            }
            for skill_name, result in history
        ]
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear the executor cache"""
    executor.clear_cache()
    return {"message": "Cache cleared successfully"}


@app.get("/api/search")
async def search_skills(q: str):
    """Search for skills"""
    results = registry.search(q)
    return [
        {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "category": skill.metadata.category.value
        }
        for skill in results
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
