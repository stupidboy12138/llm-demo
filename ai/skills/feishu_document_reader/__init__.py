"""
Feishu Document Reader Skill

A skill for reading and extracting content from Feishu (Lark) documents.
Supports reading document content, metadata, tables, and comments.
"""

from .feishu_reader_skill import FeishuDocumentReaderSkill

__all__ = ["FeishuDocumentReaderSkill"]