#!/usr/bin/env python3
"""
Feishu Document Reader Example

This script demonstrates how to use the FeishuDocumentReaderSkill to read
content from Feishu (Lark) documents.

Prerequisites:
1. Create a Feishu app and get App ID and App Secret
2. Set environment variables FEISHU_APP_ID and FEISHU_APP_SECRET
3. Have access to the Feishu document you want to read

Usage:
    python example_usage.py <document_url> [extract_type]

Example:
    python example_usage.py "https://example.feishu.cn/docx/ABC123XYZ" all
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path to import skills
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai.skills.skill_registry import SkillRegistry
from ai.skills.skill_executor import SkillExecutor
from ai.skills.feishu_document_reader import FeishuDocumentReaderSkill


async def main():
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <document_url> [extract_type]")
        print("Example: python example_usage.py 'https://example.feishu.cn/docx/ABC123XYZ' all")
        sys.exit(1)

    document_url = sys.argv[1]
    extract_type = sys.argv[2] if len(sys.argv) > 2 else "all"

    # Check for credentials
    app_id = os.getenv("FEISHU_APP_ID")
    app_secret = os.getenv("FEISHU_APP_SECRET")

    if not app_id or not app_secret:
        print("Error: Please set FEISHU_APP_ID and FEISHU_APP_SECRET environment variables")
        print("You can get these from your Feishu app settings")
        sys.exit(1)

    # Initialize skill registry and executor
    registry = SkillRegistry()
    executor = SkillExecutor(registry)

    # Register the Feishu reader skill
    feishu_skill = FeishuDocumentReaderSkill()
    registry.register(feishu_skill)

    print(f"Reading Feishu document: {document_url}")
    print(f"Extract type: {extract_type}")
    print("-" * 50)

    try:
        # Execute the skill
        result = await executor.execute(
            "feishu_document_reader",
            document_url=document_url,
            extract_type=extract_type,
            include_formatting=True
        )

        if result.success:
            print("Document read successfully!")
            print(f"Execution time: {result.execution_time:.2f}s")
            print("\nResults:")

            data = result.data

            # Display metadata
            if "metadata" in data:
                print("\n=== Document Metadata ===")
                metadata = data["metadata"]
                print(f"Title: {metadata.get('title', 'N/A')}")
                print(f"Owner ID: {metadata.get('owner_id', 'N/A')}")
                print(f"Create Time: {metadata.get('create_time', 'N/A')}")
                print(f"Last Edit: {metadata.get('edit_time', 'N/A')}")

            # Display content
            if "content" in data:
                print("\n=== Document Content ===")
                content = data["content"]
                print(f"Text Content:\n{content.get('text_content', 'N/A')}")
                print(f"Block Count: {content.get('block_count', 0)}")

            # Display tables
            if "tables" in data and data["tables"]:
                print("\n=== Tables ===")
                for i, table in enumerate(data["tables"], 1):
                    print(f"Table {i}: {table.get('table_id', 'N/A')}")
                    # You can further process table data here

            # Display comments
            if "comments" in data and data["comments"]:
                print("\n=== Comments ===")
                for i, comment in enumerate(data["comments"], 1):
                    print(f"Comment {i}:")
                    print(f"  Author: {comment.get('author', 'N/A')}")
                    print(f"  Content: {comment.get('content', 'N/A')}")
                    print(f"  Time: {comment.get('create_time', 'N/A')}")

            # Save full result to file
            output_file = f"feishu_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result.data, f, ensure_ascii=False, indent=2)
            print(f"\nFull results saved to: {output_file}")

        else:
            print(f"Failed to read document: {result.error}")
            print(f"Error Type: {result.error_type}")
            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")

    except Exception as e:
        print(f"Error executing skill: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())