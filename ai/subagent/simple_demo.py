"""
Simple SubAgent Demo - Quick Start

A simplified version for quick testing of the subagent architecture.
"""

import asyncio
import sys
from pathlib import Path

# Fix imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.subagent import (
    CoordinatorAgent,
    SubAgentRegistry,
    DataAnalysisSubAgent,
    CodeGenerationSubAgent,
    ResearchSubAgent,
    ValidationSubAgent
)


async def main():
    """Simple demo showing basic subagent usage"""

    print("=" * 60)
    print("SubAgent Architecture - Simple Demo")
    print("=" * 60)

    # 1. Create registry
    print("\n[1] Setting up SubAgent Registry...")
    registry = SubAgentRegistry()

    # 2. Register specialized agents
    registry.register(DataAnalysisSubAgent())
    registry.register(CodeGenerationSubAgent())
    registry.register(ResearchSubAgent())
    registry.register(ValidationSubAgent())

    print(f"✓ Registered {len(registry)} agents")

    # 3. Create coordinator
    print("\n[2] Creating Coordinator Agent...")
    coordinator = CoordinatorAgent(registry)
    print("✓ Coordinator ready")

    # 4. Execute a complex task
    print("\n[3] Executing complex task...")
    task = """
    Create a Python function that calculates the Fibonacci sequence up to n terms.
    Include documentation, error handling, and explain the time complexity.
    """

    result = await coordinator.execute_complex_task(
        task,
        decompose=True,
        validate_results=True
    )

    # 5. Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Task ID: {result['task_id']}")
    print(f"Success: {result['success']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Subtasks Executed: {result['subtasks_executed']}")

    if result['success']:
        print("\n--- Final Answer ---")
        print(result['result']['final_answer'][:800])
        print("\n... (truncated)")

        print(f"\n--- Validation ---")
        validation = result['result'].get('validation', {})
        print(f"Validated: {validation.get('is_valid', 'N/A')}")
        print(f"Score: {validation.get('validation_score', 'N/A')}")

    # 6. Show registry status
    print("\n" + "=" * 60)
    print("REGISTRY STATUS")
    print("=" * 60)
    status = registry.get_registry_status()
    for agent in status['agents']:
        print(f"- {agent['name']}: {agent['completed_tasks']} tasks completed")


if __name__ == "__main__":
    asyncio.run(main())
