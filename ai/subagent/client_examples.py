"""
Web Service Client Examples

Examples of how to interact with the SubAgent web service.
"""

import requests
import json
from typing import Dict, Any


class SubAgentClient:
    """Client for interacting with SubAgent API"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the SubAgent API
        """
        self.base_url = base_url.rstrip('/')

    def execute_task(
        self,
        task: str,
        decompose: bool = True,
        validate: bool = True,
        priority: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a task via the API.

        Args:
            task: Task description
            decompose: Whether to decompose the task
            validate: Whether to validate results
            priority: Task priority (1-5)

        Returns:
            Task execution result
        """
        response = requests.post(
            f"{self.base_url}/api/task",
            json={
                "task": task,
                "decompose": decompose,
                "validate": validate,
                "priority": priority
            }
        )
        response.raise_for_status()
        return response.json()

    def execute_task_stream(self, task: str):
        """
        Execute a task with streaming response.

        Args:
            task: Task description

        Yields:
            Progress updates from the task execution
        """
        response = requests.post(
            f"{self.base_url}/api/task/stream",
            json={"task": task, "decompose": True, "validate": True},
            stream=True
        )

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    yield json.loads(line[6:])

    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        response = requests.get(f"{self.base_url}/api/status")
        response.raise_for_status()
        return response.json()

    def list_agents(self) -> list:
        """List all agents"""
        response = requests.get(f"{self.base_url}/api/agents")
        response.raise_for_status()
        return response.json()

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get specific agent details"""
        response = requests.get(f"{self.base_url}/api/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

    def get_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get task history"""
        response = requests.get(f"{self.base_url}/api/history?limit={limit}")
        response.raise_for_status()
        return response.json()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get available capabilities"""
        response = requests.get(f"{self.base_url}/api/capabilities")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


def example_basic_usage():
    """Example 1: Basic task execution"""
    print("=" * 60)
    print("Example 1: Basic Task Execution")
    print("=" * 60)

    client = SubAgentClient()

    # Execute a simple task
    result = client.execute_task(
        task="Explain what is a binary tree and provide a Python implementation",
        decompose=True,
        validate=True
    )

    print(f"\nTask ID: {result['task_id']}")
    print(f"Success: {result['success']}")
    print(f"Execution Time: {result['execution_time']:.2f}s")
    print(f"Subtasks: {result['subtasks_executed']}")

    if result['success']:
        print(f"\nAnswer Preview:")
        print(result['result']['final_answer'][:300] + "...")


def example_streaming():
    """Example 2: Streaming task execution"""
    print("\n" + "=" * 60)
    print("Example 2: Streaming Execution")
    print("=" * 60)

    client = SubAgentClient()

    task = "Create a sorting algorithm comparison with time complexity analysis"

    print(f"\nExecuting: {task}")
    print("\nProgress:")

    for update in client.execute_task_stream(task):
        status = update.get('status')
        if status == 'started':
            print(f"✓ Started task")
        elif status == 'completed':
            print(f"✓ Completed in {update['result']['execution_time']:.2f}s")
        elif 'subtask' in update:
            print(f"  → Subtask {update['subtask']} completed")


def example_agent_monitoring():
    """Example 3: Agent status monitoring"""
    print("\n" + "=" * 60)
    print("Example 3: Agent Monitoring")
    print("=" * 60)

    client = SubAgentClient()

    # Get system status
    status = client.get_status()
    print(f"\nSystem Status: {status['status']}")
    print(f"Total Agents: {status['total_agents']}")
    print(f"Tasks Executed: {status['total_tasks_executed']}")

    # List all agents
    agents = client.list_agents()
    print(f"\n{'Agent ID':<20} {'Name':<25} {'Completed Tasks':<15}")
    print("-" * 60)
    for agent in agents:
        print(f"{agent['agent_id']:<20} {agent['name']:<25} {agent['completed_tasks']:<15}")

    # Get capabilities
    capabilities = client.get_capabilities()
    print(f"\n\nAvailable Capabilities:")
    for cap, agents_list in capabilities.items():
        print(f"  {cap}: {len(agents_list)} agent(s)")


def example_batch_processing():
    """Example 4: Batch task processing"""
    print("\n" + "=" * 60)
    print("Example 4: Batch Processing")
    print("=" * 60)

    client = SubAgentClient()

    tasks = [
        "Calculate the Fibonacci sequence for n=10",
        "Explain the difference between stack and queue",
        "Implement a simple calculator class in Python",
        "What are the SOLID principles in software engineering?"
    ]

    print(f"\nProcessing {len(tasks)} tasks...\n")

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] Processing: {task[:50]}...")
        try:
            result = client.execute_task(task, decompose=False, validate=False)
            results.append(result)
            status = "✓" if result['success'] else "✗"
            print(f"     {status} Completed in {result['execution_time']:.2f}s")
        except Exception as e:
            print(f"     ✗ Error: {e}")

    # Summary
    successful = sum(1 for r in results if r['success'])
    total_time = sum(r['execution_time'] for r in results)

    print(f"\nBatch Summary:")
    print(f"  Total Tasks: {len(tasks)}")
    print(f"  Successful: {successful}")
    print(f"  Total Time: {total_time:.2f}s")
    print(f"  Avg Time: {total_time/len(results):.2f}s")


def example_task_history():
    """Example 5: View task history"""
    print("\n" + "=" * 60)
    print("Example 5: Task History")
    print("=" * 60)

    client = SubAgentClient()

    history = client.get_history(limit=5)

    print(f"\nShowing {history['total']} most recent tasks:\n")

    for i, task_record in enumerate(history['history'], 1):
        print(f"{i}. Task ID: {task_record['task_id']}")
        print(f"   Task: {task_record['task'][:60]}...")
        print(f"   Subtasks: {task_record['subtasks_count']}")
        print(f"   Success: {task_record['success']}")
        print(f"   Time: {task_record['execution_time']:.2f}s")
        print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("SubAgent Web Service Client Examples")
    print("=" * 60)
    print("\nMake sure the service is running:")
    print("  uvicorn ai.subagent.web_service:app --port 8001\n")

    client = SubAgentClient()

    # Health check
    try:
        health = client.health_check()
        print(f"✓ Service is healthy: {health}")
    except Exception as e:
        print(f"✗ Service is not available: {e}")
        print("\nPlease start the service first.")
        return

    # Run examples
    try:
        example_basic_usage()
        example_agent_monitoring()
        example_batch_processing()
        example_task_history()
        # example_streaming()  # Uncomment if you want to test streaming

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")


if __name__ == "__main__":
    main()
