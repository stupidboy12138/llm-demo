"""
Feishu Document Reader Skill Implementation

This skill provides functionality to read and extract content from Feishu (Lark) documents
including text content, metadata, tables, and comments.
"""

from ..base_skill import (
    BaseSkill,
    SkillCategory,
    SkillContext,
    SkillResult,
    SkillParameter,
    SkillMetadata
)
from typing import Dict, Any, Optional, List
import asyncio
import json
import os
from datetime import datetime, timedelta


class FeishuDocumentReaderSkill(BaseSkill):
    """Skill for reading Feishu (Lark) documents"""

    def __init__(self):
        metadata = SkillMetadata(
            name="feishu_document_reader",
            description="Read and extract content from Feishu (Lark) documents including text, metadata, tables, and comments",
            category=SkillCategory.API_INTEGRATION,
            version="1.0.0",
            author="Demo",
            tags=["feishu", "lark", "document", "api", "reading"],
            examples=[
                "Read a Feishu document by URL",
                "Extract text content from a Feishu doc",
                "Get document metadata including title and author",
                "Read tables from a Feishu document",
                "Extract comments from a document"
            ],
            parameters=[
                SkillParameter(
                    name="document_url",
                    type=str,
                    description="URL of the Feishu document to read",
                    required=True
                ),
                SkillParameter(
                    name="extract_type",
                    type=str,
                    description="Type of content to extract: 'content', 'metadata', 'tables', 'comments', or 'all'",
                    required=False,
                    default="all"
                ),
                SkillParameter(
                    name="app_id",
                    type=str,
                    description="Feishu App ID (can also be set via FEISHU_APP_ID environment variable)",
                    required=False
                ),
                SkillParameter(
                    name="app_secret",
                    type=str,
                    description="Feishu App Secret (can also be set via FEISHU_APP_SECRET environment variable)",
                    required=False
                ),
                SkillParameter(
                    name="include_formatting",
                    type=bool,
                    description="Whether to preserve formatting in extracted content",
                    required=False,
                    default=True
                )
            ],
            dependencies=["requests", "python-dotenv"]
        )
        super().__init__(metadata)
        self._session = None
        self._access_token = None
        self._token_expires_at = None

    async def initialize(self) -> None:
        """Initialize the skill and setup API client"""
        try:
            import requests
            from dotenv import load_dotenv

            # Load environment variables
            load_dotenv()

            self._session = requests.Session()
            self._session.headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'FeishuDocumentReader/1.0'
            })

            self._is_initialized = True

        except ImportError as e:
            raise ImportError(f"Missing required dependency: {e}")

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._session:
            self._session.close()
            self._session = None
        self._access_token = None
        self._token_expires_at = None
        self._is_initialized = False

    async def _get_access_token(self, app_id: str, app_secret: str) -> str:
        """Get Feishu access token"""
        import requests

        # Check if token is still valid
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": app_id,
            "app_secret": app_secret
        }

        try:
            response = self._session.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to get access token: {data.get('msg')}")

            self._access_token = data["tenant_access_token"]
            expires_in = data.get("expire", 7200)  # Default 2 hours
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # Refresh 5 min early

            return self._access_token

        except requests.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")

    def _extract_document_info(self, document_url: str) -> Dict[str, str]:
        """Extract document type and ID from URL"""
        # Handle different Feishu document URL formats
        # Format 1: https://example.feishu.cn/docx/ABC123XYZ
        # Format 2: https://example.feishu.cn/sheets/ABC123XYZ
        # Format 3: https://example.feishu.cn/base/ABC123XYZ

        import re

        patterns = [
            r'https://([^.]+)\.feishu\.cn/(docx|sheets|base|mindnotes|bitable)/([a-zA-Z0-9]+)',
            r'https://([^.]+)\.larksuite\.com/(docx|sheets|base|mindnotes|bitable)/([a-zA-Z0-9]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, document_url)
            if match:
                return {
                    "tenant": match.group(1),
                    "doc_type": match.group(2),
                    "doc_token": match.group(3)
                }

        raise ValueError("Invalid Feishu document URL format")

    async def _read_document_content(self, doc_token: str, access_token: str, include_formatting: bool) -> Dict[str, Any]:
        """Read document content"""
        import requests

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/content"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to read document: {data.get('msg')}")

            content = data.get("data", {})

            # Extract text content
            text_content = self._extract_text_from_blocks(content.get("content", {}), include_formatting)

            return {
                "raw_content": content,
                "text_content": text_content,
                "block_count": len(content.get("content", {}).get("blocks", []))
            }

        except requests.RequestException as e:
            raise Exception(f"Failed to read document content: {str(e)}")

    def _extract_text_from_blocks(self, content: Dict[str, Any], include_formatting: bool) -> str:
        """Extract text from document blocks"""
        blocks = content.get("blocks", [])
        text_parts = []

        for block in blocks:
            block_type = block.get("type")

            if block_type == "text":
                elements = block.get("text", {}).get("elements", [])
                for element in elements:
                    text_run = element.get("textRun", {})
                    text = text_run.get("content", "")
                    if text:
                        if include_formatting and text_run.get("style"):
                            # Add basic formatting indicators
                            style = text_run.get("style", {})
                            if style.get("bold"):
                                text = f"**{text}**"
                            if style.get("italic"):
                                text = f"*{text}*"
                        text_parts.append(text)

            elif block_type == "heading1":
                text = self._extract_text_from_block(block)
                if include_formatting:
                    text_parts.append(f"# {text}")
                else:
                    text_parts.append(text)

            elif block_type == "heading2":
                text = self._extract_text_from_block(block)
                if include_formatting:
                    text_parts.append(f"## {text}")
                else:
                    text_parts.append(text)

            elif block_type == "bullet":
                text = self._extract_text_from_block(block)
                if include_formatting:
                    text_parts.append(f"• {text}")
                else:
                    text_parts.append(text)

            elif block_type == "ordered":
                text = self._extract_text_from_block(block)
                if include_formatting:
                    text_parts.append(f"1. {text}")
                else:
                    text_parts.append(text)

            elif block_type == "code":
                text = self._extract_text_from_block(block)
                if include_formatting:
                    text_parts.append(f"```\n{text}\n```")
                else:
                    text_parts.append(text)

            # Add spacing between blocks
            if text_parts and not text_parts[-1].endswith("\n"):
                text_parts.append("\n")

        return "".join(text_parts).strip()

    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """Extract text from a single block"""
        elements = block.get("text", {}).get("elements", [])
        text_parts = []

        for element in elements:
            text_run = element.get("textRun", {})
            text = text_run.get("content", "")
            if text:
                text_parts.append(text)

        return "".join(text_parts)

    async def _read_document_metadata(self, doc_token: str, access_token: str) -> Dict[str, Any]:
        """Read document metadata"""
        import requests

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to read document metadata: {data.get('msg')}")

            doc_data = data.get("data", {})

            return {
                "title": doc_data.get("title", ""),
                "owner_id": doc_data.get("owner_id"),
                "create_time": doc_data.get("create_time"),
                "edit_time": doc_data.get("edit_time"),
                "revision_id": doc_data.get("revision_id"),
                "document_status": doc_data.get("document_status"),
                "is_external": doc_data.get("is_external", False)
            }

        except requests.RequestException as e:
            raise Exception(f"Failed to read document metadata: {str(e)}")

    async def _read_document_tables(self, doc_token: str, access_token: str) -> List[Dict[str, Any]]:
        """Read tables from document"""
        import requests

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to read document blocks: {data.get('msg')}")

            blocks = data.get("data", {}).get("items", [])
            tables = []

            for block in blocks:
                if block.get("block_type") == "table":
                    table_data = await self._read_table_data(doc_token, block.get("block_id"), access_token)
                    tables.append({
                        "table_id": block.get("block_id"),
                        "table_data": table_data
                    })

            return tables

        except requests.RequestException as e:
            raise Exception(f"Failed to read document tables: {str(e)}")

    async def _read_table_data(self, doc_token: str, table_id: str, access_token: str) -> Dict[str, Any]:
        """Read data from a specific table"""
        import requests

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{table_id}/children"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                raise Exception(f"Failed to read table data: {data.get('msg')}")

            return data.get("data", {})

        except requests.RequestException as e:
            raise Exception(f"Failed to read table data: {str(e)}")

    async def _read_document_comments(self, doc_token: str, access_token: str) -> List[Dict[str, Any]]:
        """Read comments from document"""
        import requests

        url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/comments"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get("code") != 0:
                # Comments might not be available for all documents
                if data.get("code") == 62001:  # Permission denied
                    return []
                raise Exception(f"Failed to read comments: {data.get('msg')}")

            comments = data.get("data", {}).get("items", [])

            # Format comments
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    "comment_id": comment.get("id"),
                    "content": comment.get("content", [{}])[0].get("content", ""),
                    "author": comment.get("user_id"),
                    "create_time": comment.get("create_time"),
                    "replies": comment.get("replies", [])
                })

            return formatted_comments

        except requests.RequestException as e:
            raise Exception(f"Failed to read comments: {str(e)}")

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute the Feishu document reader skill"""
        try:
            document_url = kwargs.get("document_url")
            extract_type = kwargs.get("extract_type", "all")
            app_id = kwargs.get("app_id") or os.getenv("FEISHU_APP_ID")
            app_secret = kwargs.get("app_secret") or os.getenv("FEISHU_APP_SECRET")
            include_formatting = kwargs.get("include_formatting", True)

            # Validate credentials
            if not app_id or not app_secret:
                return SkillResult(
                    execution_id=context.execution_id,
                    success=False,
                    data=None,
                    error="Feishu App ID and App Secret are required. Set FEISHU_APP_ID and FEISHU_APP_SECRET environment variables or pass as parameters.",
                    error_type="AuthenticationError"
                )

            # Extract document info from URL
            doc_info = self._extract_document_info(document_url)

            # Get access token
            access_token = await self._get_access_token(app_id, app_secret)

            result = {
                "document_url": document_url,
                "document_info": doc_info,
                "extracted_at": datetime.now().isoformat()
            }

            # Extract based on type
            if extract_type == "all" or extract_type == "content":
                content_data = await self._read_document_content(
                    doc_info["doc_token"],
                    access_token,
                    include_formatting
                )
                result["content"] = content_data

            if extract_type == "all" or extract_type == "metadata":
                metadata = await self._read_document_metadata(
                    doc_info["doc_token"],
                    access_token
                )
                result["metadata"] = metadata

            if extract_type == "all" or extract_type == "tables":
                tables = await self._read_document_tables(
                    doc_info["doc_token"],
                    access_token
                )
                result["tables"] = tables

            if extract_type == "all" or extract_type == "comments":
                comments = await self._read_document_comments(
                    doc_info["doc_token"],
                    access_token
                )
                result["comments"] = comments

            return SkillResult(
                execution_id=context.execution_id,
                success=True,
                data=result,
                metadata={
                    "extract_type": extract_type,
                    "include_formatting": include_formatting
                }
            )

        except Exception as e:
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error=str(e),
                error_type=type(e).__name__
            )