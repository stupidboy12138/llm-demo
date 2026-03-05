#!/usr/bin/env python3
"""
Web API Demo for Feishu Document Reader Skill

This script demonstrates how to use the FeishuDocumentReaderSkill
within the skills web service.
"""

import asyncio
import json
from typing import Dict, Any

# Import the skills framework
from ai.skills.skill_registry import SkillRegistry
from ai.skills.skill_executor import SkillExecutor
from ai.skills.feishu_document_reader import FeishuDocumentReaderSkill


async def demo_feishu_skill():
    """Demonstrate the Feishu document reader skill"""

    print("Feishu Document Reader - Web API Demo")
    print("=" * 50)

    # Initialize registry and executor
    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register the Feishu reader skill
    feishu_skill = FeishuDocumentReaderSkill()
    registry.register(feishu_skill)

    # Example 1: Get skill information
    print("\n1. Skill Information:")
    skill_info = {
        "name": feishu_skill.metadata.name,
        "description": feishu_skill.metadata.description,
        "category": feishu_skill.metadata.category.value,
        "version": feishu_skill.metadata.version,
        "parameters": [
            {
                "name": param.name,
                "type": param.type.__name__,
                "description": param.description,
                "required": param.required,
                "default": param.default
            }
            for param in feishu_skill.metadata.parameters
        ]
    }
    print(json.dumps(skill_info, indent=2))

    # Example 2: Simulate API request
    print("\n2. Simulating API Request:")

    # Example request data (as would come from web API)
    request_data = {
        "document_url": "https://example.feishu.cn/docx/ABC123XYZ",
        "extract_type": "metadata",
        "include_formatting": True
    }

    print(f"Request: {json.dumps(request_data, indent=2)}")

    # Execute skill
    try:
        result = await executor.execute(
            "feishu_document_reader",
            **request_data
        )

        print("\n3. Response:")
        response = {
            "success": result.success,
            "execution_id": result.execution_id,
            "execution_time": result.execution_time,
            "data": result.data if result.success else None,
            "error": result.error if not result.success else None,
            "error_type": result.error_type if not result.success else None
        }

        if result.success:
            print("Status: Success")
            print(f"Execution time: {result.execution_time:.3f}s")

            # Show sample of returned data
            if "metadata" in result.data:
                print("\nDocument Metadata:")
                metadata = result.data["metadata"]
                print(f"  Title: {metadata.get('title', 'N/A')}")
                print(f"  Owner ID: {metadata.get('owner_id', 'N/A')}")
                print(f"  Create Time: {metadata.get('create_time', 'N/A')}")
        else:
            print("Status: Failed")
            print(f"Error: {result.error}")
            print(f"Error Type: {result.error_type}")

    except Exception as e:
        print(f"\nError executing skill: {str(e)}")

    # Example 3: Show error handling
    print("\n4. Error Handling Example:")

    # Test with missing required parameter
    try:
        result = await executor.execute(
            "feishu_document_reader",
            extract_type="content"
            # Missing document_url
        )

        if not result.success:
            print(f"Expected error: {result.error}")
            print(f"Error type: {result.error_type}")
    except Exception as e:
        print(f"Error: {str(e)}")

    print("\n" + "=" * 50)
    print("Demo completed!")

    # Show how to integrate with web service
    print("\nIntegration with Web Service:")
    print("""
To use this skill in the web service, add it to the skill registry:

# In your web service initialization
registry = SkillRegistry()
registry.register(FeishuDocumentReaderSkill())

# Then in your API endpoint:
@app.post("/api/feishu/read")
async def read_feishu_document(request: FeishuReadRequest):
    result = await executor.execute(
        "feishu_document_reader",
        document_url=request.document_url,
        extract_type=request.extract_type or "all"
    )

    if result.success:
        return {
            "success": True,
            "data": result.data,
            "execution_time": result.execution_time
        }
    else:
        return {
            "success": False,
            "error": result.error,
            "error_type": result.error_type
        }
    """)


if __name__ == "__main__":
    asyncio.run(demo_feishu_skill())