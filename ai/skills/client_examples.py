"""
Client Examples for Skills Web Service

Demonstrates how to interact with the skills API.
"""

import requests
import json
import asyncio
import httpx
from typing import Dict, Any


BASE_URL = "http://localhost:8002"


def example_list_skills():
    """Example: List all available skills"""
    print("\n" + "=" * 50)
    print("Example 1: List All Skills")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/skills")

    if response.status_code == 200:
        skills = response.json()
        print(f"\nFound {len(skills)} skills:")

        for skill in skills:
            print(f"\n  {skill['name']} ({skill['category']})")
            print(f"    {skill['description']}")
            print(f"    Tags: {', '.join(skill['tags'])}")
    else:
        print(f"Error: {response.status_code}")


def example_execute_skill():
    """Example: Execute a skill"""
    print("\n" + "=" * 50)
    print("Example 2: Execute Text Analyzer")
    print("=" * 50)

    payload = {
        "skill_name": "text_analyzer",
        "parameters": {
            "text": "Artificial intelligence and machine learning are transforming technology. "
                    "Deep learning models enable powerful applications."
        },
        "use_cache": True
    }

    response = requests.post(f"{BASE_URL}/api/execute", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Execution successful!")
        print(f"  Execution ID: {result['execution_id']}")
        print(f"  Execution time: {result['execution_time']:.3f}s")
        print(f"\n  Results:")
        print(f"    - Words: {result['data']['word_count']}")
        print(f"    - Sentences: {result['data']['sentence_count']}")
        print(f"    - Unique words: {result['data']['unique_words']}")
        print(f"    - Top words: {result['data']['top_words'][:5]}")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_execute_calculator():
    """Example: Execute calculator skill"""
    print("\n" + "=" * 50)
    print("Example 3: Execute Math Calculator")
    print("=" * 50)

    payload = {
        "skill_name": "math_calculator",
        "parameters": {
            "expression": "(100 + 50) * 2 - 10",
            "precision": 2
        }
    }

    response = requests.post(f"{BASE_URL}/api/execute", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Calculation successful!")
        print(f"  Expression: {result['data']['expression']}")
        print(f"  Result: {result['data']['result']}")
    else:
        print(f"Error: {response.status_code}")


def example_batch_execution():
    """Example: Batch execution"""
    print("\n" + "=" * 50)
    print("Example 4: Batch Execution")
    print("=" * 50)

    payload = {
        "tasks": [
            {
                "skill_name": "math_calculator",
                "parameters": {"expression": "10 + 20"}
            },
            {
                "skill_name": "math_calculator",
                "parameters": {"expression": "50 * 2"}
            },
            {
                "skill_name": "math_calculator",
                "parameters": {"expression": "pow(2, 8)"}
            }
        ],
        "max_concurrent": 3
    }

    response = requests.post(f"{BASE_URL}/api/batch", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Batch execution completed!")
        print(f"  Total tasks: {result['total_tasks']}")
        print(f"\n  Results:")

        for i, r in enumerate(result['results'], 1):
            if r['success']:
                print(f"    {i}. {r['data']['expression']} = {r['data']['result']}")
            else:
                print(f"    {i}. Error: {r['error']}")
    else:
        print(f"Error: {response.status_code}")


def example_chain_execution():
    """Example: Execute a skill chain"""
    print("\n" + "=" * 50)
    print("Example 5: Chain Execution")
    print("=" * 50)

    payload = {
        "chain_name": "TextAnalysisChain",
        "steps": [
            {
                "skill_name": "text_analyzer",
                "parameters": {
                    "text": "Machine learning enables computers to learn from data. "
                            "Deep learning uses neural networks."
                }
            },
            {
                "skill_name": "text_summarizer",
                "parameters": {
                    "text": "Machine learning enables computers to learn from data. "
                            "Deep learning uses neural networks.",
                    "max_length": 50
                }
            }
        ]
    }

    response = requests.post(f"{BASE_URL}/api/chain", json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Chain execution completed!")
        print(f"  Execution time: {result['execution_time']:.3f}s")
        print(f"  Steps executed: {result['metadata']['executed_steps']}")
        print(f"\n  Final result:")
        print(f"    {result['data']}")
    else:
        print(f"Error: {response.status_code}")


def example_search_skills():
    """Example: Search for skills"""
    print("\n" + "=" * 50)
    print("Example 6: Search Skills")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/search", params={"q": "text"})

    if response.status_code == 200:
        results = response.json()
        print(f"\nFound {len(results)} skills matching 'text':")

        for skill in results:
            print(f"  - {skill['name']}: {skill['description']}")
    else:
        print(f"Error: {response.status_code}")


def example_get_statistics():
    """Example: Get system statistics"""
    print("\n" + "=" * 50)
    print("Example 7: System Statistics")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/api/statistics")

    if response.status_code == 200:
        stats = response.json()
        print(f"\nRegistry Statistics:")
        print(f"  Total skills: {stats['registry']['total_skills']}")
        print(f"  By category:")
        for cat, count in stats['registry']['categories'].items():
            print(f"    - {cat}: {count}")

        print(f"\nExecutor Statistics:")
        print(f"  Total executions: {stats['executor']['total_executions']}")
        print(f"  Success rate: {stats['executor']['success_rate']:.1%}")
        print(f"  Cache size: {stats['executor']['cache_size']}")
    else:
        print(f"Error: {response.status_code}")


async def example_streaming_execution():
    """Example: Streaming execution"""
    print("\n" + "=" * 50)
    print("Example 8: Streaming Execution")
    print("=" * 50)

    payload = {
        "skill_name": "text_analyzer",
        "parameters": {
            "text": "Streaming example text for analysis."
        }
    }

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/execute/stream",
            json=payload,
            timeout=30.0
        ) as response:
            print("\nStreaming response:")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    event = data.get("event")

                    if event == "start":
                        print(f"  ▶ Started: {data['skill']}")
                    elif event == "result":
                        print(f"  ✓ Result: {data['data']}")
                    elif event == "complete":
                        print(f"  ■ Completed in {data['execution_time']:.3f}s")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("SKILLS WEB SERVICE - CLIENT EXAMPLES")
    print("=" * 60)
    print("\nMake sure the web service is running:")
    print("  python -m ai.skills.web_service")
    print(f"\nConnecting to: {BASE_URL}")

    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n✗ Service is not responding properly!")
            return
    except requests.exceptions.RequestException:
        print("\n✗ Could not connect to service!")
        print("Please start the service first:")
        print("  python -m ai.skills.web_service")
        return

    print("✓ Service is running\n")

    # Run examples
    try:
        example_list_skills()
        example_execute_skill()
        example_execute_calculator()
        example_batch_execution()
        example_chain_execution()
        example_search_skills()
        example_get_statistics()

        # Run async example
        print("\nRunning async example...")
        asyncio.run(example_streaming_execution())

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")

    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
