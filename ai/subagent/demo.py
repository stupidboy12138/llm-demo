"""
SubAgent Demo - Comprehensive Example

This demo showcases the complete subagent architecture with various scenarios:
1. Simple task delegation
2. Complex task decomposition and coordination
3. Multi-agent collaboration
4. Error handling and validation
"""

import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.logging import RichHandler

from ai.subagent import (
    CoordinatorAgent,
    SubAgentRegistry,
    DataAnalysisSubAgent,
    CodeGenerationSubAgent,
    ResearchSubAgent,
    ValidationSubAgent
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)
console = Console()


async def demo_simple_task():
    """Demo 1: Simple task delegation to a single sub-agent"""
    console.print(Panel.fit(
        "[bold cyan]Demo 1: Simple Task Delegation[/bold cyan]",
        border_style="cyan"
    ))

    # Create registry and register agents
    registry = SubAgentRegistry()
    registry.register(ResearchSubAgent())

    # Get agent and execute task
    agent = registry.find_best_agent(SubAgentCapability.RESEARCH)

    from ai.subagent.base_subagent import TaskContext
    context = TaskContext(
        task_id="task-001",
        task_type="research"
    )

    result = await agent.execute_with_tracking(
        "Explain what is machine learning in simple terms",
        context
    )

    console.print(f"\n[green]✓ Task completed in {result.execution_time:.2f}s[/green]")
    console.print(f"[bold]Result:[/bold]\n{result.data.get('summary', '')}\n")


async def demo_complex_task():
    """Demo 2: Complex task with decomposition and multiple agents"""
    console.print(Panel.fit(
        "[bold cyan]Demo 2: Complex Task Coordination[/bold cyan]",
        border_style="cyan"
    ))

    # Setup registry with multiple specialized agents
    registry = SubAgentRegistry()
    registry.register(DataAnalysisSubAgent())
    registry.register(CodeGenerationSubAgent())
    registry.register(ResearchSubAgent())
    registry.register(ValidationSubAgent())

    # Create coordinator
    coordinator = CoordinatorAgent(registry)

    # Execute complex task
    complex_task = """
    Create a Python function that analyzes a list of numbers and returns:
    1. Statistical summary (mean, median, std dev)
    2. Visualizes the data distribution
    3. Identifies any outliers
    Include proper documentation and unit tests.
    """

    result = await coordinator.execute_complex_task(
        complex_task,
        decompose=True,
        validate_results=True
    )

    console.print(f"\n[green]✓ Complex task completed in {result['execution_time']:.2f}s[/green]")
    console.print(f"[bold]Subtasks executed:[/bold] {result['subtasks_executed']}")
    console.print(f"[bold]Success:[/bold] {result['success']}\n")

    if result['success']:
        console.print(Panel(
            result['result']['final_answer'][:500] + "...",
            title="[bold]Final Answer[/bold]",
            border_style="green"
        ))


async def demo_parallel_execution():
    """Demo 3: Parallel execution of multiple independent tasks"""
    console.print(Panel.fit(
        "[bold cyan]Demo 3: Parallel Task Execution[/bold cyan]",
        border_style="cyan"
    ))

    # Setup
    registry = SubAgentRegistry()
    registry.register(DataAnalysisSubAgent("analyst-1"))
    registry.register(DataAnalysisSubAgent("analyst-2"))
    registry.register(ResearchSubAgent("researcher-1"))
    registry.register(CodeGenerationSubAgent("coder-1"))

    # Create multiple independent tasks
    from ai.subagent.base_subagent import TaskContext
    tasks = [
        ("Calculate factorial of 10 and explain the algorithm", "coder-1"),
        ("Analyze the trend: [1, 3, 7, 15, 31, 63]", "analyst-1"),
        ("Explain what is asyncio in Python", "researcher-1"),
        ("Find the mean and variance of [10, 20, 30, 40, 50]", "analyst-2")
    ]

    # Execute all tasks in parallel
    start_time = asyncio.get_event_loop().time()

    results = await asyncio.gather(*[
        registry.get_agent(agent_id).execute_with_tracking(
            task,
            TaskContext(task_id=f"parallel-{i}", task_type="parallel")
        )
        for i, (task, agent_id) in enumerate(tasks)
    ])

    total_time = asyncio.get_event_loop().time() - start_time

    # Display results
    table = Table(title="Parallel Execution Results")
    table.add_column("Task #", style="cyan")
    table.add_column("Agent", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Time (s)", style="yellow")

    for i, (result, (task, agent_id)) in enumerate(zip(results, tasks)):
        status = "✓ Success" if result.success else "✗ Failed"
        table.add_row(
            str(i + 1),
            agent_id,
            status,
            f"{result.execution_time:.2f}"
        )

    console.print(table)
    console.print(f"\n[green]Total parallel execution time: {total_time:.2f}s[/green]")


async def demo_error_handling():
    """Demo 4: Error handling and graceful degradation"""
    console.print(Panel.fit(
        "[bold cyan]Demo 4: Error Handling[/bold cyan]",
        border_style="cyan"
    ))

    registry = SubAgentRegistry()
    registry.register(CodeGenerationSubAgent())

    agent = registry.get_agent("code_generator")

    # Task that might cause issues
    from ai.subagent.base_subagent import TaskContext
    problematic_task = "Generate code in an invalid programming language: 'FooBar123'"

    result = await agent.execute_with_tracking(
        problematic_task,
        TaskContext(task_id="error-test", task_type="code")
    )

    if result.success:
        console.print("[green]✓ Task handled successfully[/green]")
        console.print(f"Result: {result.data}")
    else:
        console.print("[yellow]⚠ Task failed gracefully[/yellow]")
        console.print(f"Error: {result.error}")


async def demo_registry_status():
    """Demo 5: Registry status and agent monitoring"""
    console.print(Panel.fit(
        "[bold cyan]Demo 5: Registry Status Monitoring[/bold cyan]",
        border_style="cyan"
    ))

    # Setup registry with all agents
    registry = SubAgentRegistry()
    registry.register(DataAnalysisSubAgent())
    registry.register(CodeGenerationSubAgent())
    registry.register(ResearchSubAgent())
    registry.register(ValidationSubAgent())

    # Execute some tasks
    coordinator = CoordinatorAgent(registry)
    await coordinator.execute_complex_task(
        "Explain the difference between async and sync programming",
        decompose=False
    )

    # Display registry status
    status = registry.get_registry_status()

    table = Table(title="SubAgent Registry Status")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Capabilities", style="green")
    table.add_column("Tasks Completed", style="yellow")

    for agent_status in status['agents']:
        capabilities = ", ".join(agent_status['capabilities'])
        table.add_row(
            agent_status['agent_id'],
            agent_status['name'],
            capabilities,
            str(agent_status['completed_tasks'])
        )

    console.print(table)
    console.print(f"\n[bold]Total agents:[/bold] {status['total_agents']}")


async def demo_workflow():
    """Demo 6: Complete workflow - Research → Code → Analyze → Validate"""
    console.print(Panel.fit(
        "[bold cyan]Demo 6: Complete Workflow Pipeline[/bold cyan]",
        border_style="cyan"
    ))

    # Setup all agents
    registry = SubAgentRegistry()
    researcher = ResearchSubAgent("researcher")
    coder = CodeGenerationSubAgent("coder")
    analyst = DataAnalysisSubAgent("analyst")
    validator = ValidationSubAgent("validator")

    registry.register(researcher)
    registry.register(coder)
    registry.register(analyst)
    registry.register(validator)

    from ai.subagent.base_subagent import TaskContext

    # Step 1: Research
    console.print("\n[bold yellow]Step 1: Research Phase[/bold yellow]")
    research_result = await researcher.execute_with_tracking(
        "Research the quicksort algorithm and its time complexity",
        TaskContext(task_id="workflow-1", task_type="research")
    )
    console.print(f"✓ Research completed: {research_result.data['summary'][:100]}...")

    # Step 2: Code Generation
    console.print("\n[bold yellow]Step 2: Code Generation Phase[/bold yellow]")
    code_result = await coder.execute_with_tracking(
        "Implement quicksort algorithm in Python based on the research",
        TaskContext(task_id="workflow-2", task_type="code")
    )
    console.print(f"✓ Code generated ({len(code_result.data['code'])} characters)")

    # Step 3: Analysis
    console.print("\n[bold yellow]Step 3: Analysis Phase[/bold yellow]")
    analysis_result = await analyst.execute_with_tracking(
        f"Analyze the complexity and efficiency of this code:\n{code_result.data['code'][:200]}",
        TaskContext(task_id="workflow-3", task_type="analyze")
    )
    console.print(f"✓ Analysis completed")

    # Step 4: Validation
    console.print("\n[bold yellow]Step 4: Validation Phase[/bold yellow]")
    validation_result = await validator.execute_with_tracking(
        f"Validate this implementation:\n{code_result.data['code'][:200]}",
        TaskContext(task_id="workflow-4", task_type="validate")
    )
    console.print(f"✓ Validation score: {validation_result.data.get('validation_score', 0)}")

    console.print("\n[green]✓ Complete workflow finished successfully[/green]")


async def main():
    """Run all demos"""
    console.print(Panel.fit(
        "[bold magenta]SubAgent Architecture Demo[/bold magenta]\n"
        "Demonstrating hierarchical agent coordination",
        border_style="magenta"
    ))

    demos = [
        ("Simple Task Delegation", demo_simple_task),
        ("Complex Task Coordination", demo_complex_task),
        ("Parallel Execution", demo_parallel_execution),
        ("Error Handling", demo_error_handling),
        ("Registry Monitoring", demo_registry_status),
        ("Complete Workflow", demo_workflow)
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            console.print(f"\n{'='*60}")
            await demo_func()
            await asyncio.sleep(1)  # Brief pause between demos
        except Exception as e:
            console.print(f"[red]✗ Demo {i} failed: {str(e)}[/red]")
            logger.exception(f"Error in {name}")

    console.print(Panel.fit(
        "[bold green]All demos completed![/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    # Fix import issue
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from ai.subagent.base_subagent import SubAgentCapability

    asyncio.run(main())
