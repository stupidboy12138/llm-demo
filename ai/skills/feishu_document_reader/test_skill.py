#!/usr/bin/env python3
"""
Test Feishu Document Reader Skill

Simple test script for the FeishuDocumentReaderSkill without Unicode issues.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai.skills.skill_registry import SkillRegistry
from ai.skills.skill_executor import SkillExecutor
from ai.skills.feishu_document_reader import FeishuDocumentReaderSkill


async def test_feishu_skill():
    print("Testing Feishu Document Reader Skill")
    print("=" * 50)

    # Initialize skill
    feishu_skill = FeishuDocumentReaderSkill()

    # Check metadata
    print("\n1. Skill Metadata:")
    metadata = feishu_skill.metadata
    print(f"   Name: {metadata.name}")
    print(f"   Description: {metadata.description}")
    print(f"   Category: {metadata.category.value}")
    print(f"   Version: {metadata.version}")
    print(f"   Parameters: {len(metadata.parameters)}")

    for param in metadata.parameters:
        required = "required" if param.required else "optional"
        print(f"   - {param.name} ({param.type.__name__}, {required}): {param.description}")

    # Test parameter validation
    print("\n2. Parameter Validation:")

    # Valid parameters
    valid_params = {
        "document_url": "https://example.feishu.cn/docx/ABC123XYZ",
        "extract_type": "all"
    }
    is_valid, error_msg = feishu_skill.validate_parameters(**valid_params)
    print(f"   Valid parameters: {is_valid}")
    if not is_valid:
        print(f"   Error: {error_msg}")

    # Invalid parameters (missing required)
    invalid_params = {
        "extract_type": "content"
    }
    is_valid, error_msg = feishu_skill.validate_parameters(**invalid_params)
    print(f"   Invalid parameters: {is_valid}")
    if not is_valid:
        print(f"   Error: {error_msg}")

    # Check environment variables
    print("\n3. Environment Setup:")
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if app_id and app_secret:
        print("   [OK] FEISHU_APP_ID and FEISHU_APP_SECRET are set")
        print(f"   [OK] App ID: {app_id[:10]}...")
        print("\n4. To test with a real document:")
        print("   python -m ai.skills.feishu_document_reader.scripts.example_usage")
        print("   <document_url> [extract_type]")
    else:
        print("   [ERROR] FEISHU_APP_ID and/or FEISHU_APP_SECRET not found")
        print("\n4. To use this skill:")
        print("   - Create a Feishu app at https://open.feishu.cn/")
        print("   - Set FEISHU_APP_ID and FEISHU_APP_SECRET environment variables")
        print("   - Run the example script with a document URL")

    print("\n" + "=" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_feishu_skill())