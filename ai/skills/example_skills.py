"""
Example Skill Implementations

Demonstrates various types of skills with different capabilities.
"""

from .base_skill import (
    BaseSkill,
    SkillCategory,
    SkillContext,
    SkillResult,
    SkillParameter,
    SkillMetadata
)
from .feishu_document_reader import FeishuDocumentReaderSkill
import asyncio
import json
import re
from typing import Any, Dict


class TextSummarizerSkill(BaseSkill):
    """Skill for summarizing text"""

    def __init__(self):
        metadata = SkillMetadata(
            name="text_summarizer",
            description="Summarizes long text into concise summaries",
            category=SkillCategory.TEXT_ANALYSIS,
            version="1.0.0",
            author="Demo",
            tags=["text", "summarization", "nlp"],
            examples=[
                "Summarize a long article",
                "Create executive summary from report"
            ],
            parameters=[
                SkillParameter(
                    name="text",
                    type=str,
                    description="Text to summarize",
                    required=True
                ),
                SkillParameter(
                    name="max_length",
                    type=int,
                    description="Maximum length of summary",
                    required=False,
                    default=100
                ),
                SkillParameter(
                    name="style",
                    type=str,
                    description="Summary style (concise, detailed, bullet)",
                    required=False,
                    default="concise"
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute text summarization"""
        text = kwargs.get("text", "")
        max_length = kwargs.get("max_length", 100)
        style = kwargs.get("style", "concise")

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Simple summarization (in production, use actual LLM/model)
        sentences = text.split(". ")

        if style == "bullet":
            summary = "\n".join([f"• {s.strip()}" for s in sentences[:3]])
        else:
            summary = ". ".join(sentences[:2]) + "."
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={
                "original_length": len(text),
                "summary_length": len(summary),
                "summary": summary,
                "style": style
            },
            metadata={"compression_ratio": len(summary) / len(text) if text else 0}
        )


class DataValidatorSkill(BaseSkill):
    """Skill for validating data structures"""

    def __init__(self):
        metadata = SkillMetadata(
            name="data_validator",
            description="Validates data against rules and schemas",
            category=SkillCategory.VALIDATION,
            version="1.0.0",
            author="Demo",
            tags=["validation", "data", "quality"],
            parameters=[
                SkillParameter(
                    name="data",
                    type=dict,
                    description="Data to validate",
                    required=True
                ),
                SkillParameter(
                    name="schema",
                    type=dict,
                    description="Validation schema",
                    required=True
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute data validation"""
        data = kwargs.get("data", {})
        schema = kwargs.get("schema", {})

        errors = []
        warnings = []

        # Validate required fields
        for field, rules in schema.items():
            if rules.get("required", False) and field not in data:
                errors.append(f"Missing required field: {field}")
                continue

            if field in data:
                value = data[field]
                expected_type = rules.get("type")

                # Type validation
                if expected_type and not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' has invalid type. "
                        f"Expected {expected_type.__name__}, got {type(value).__name__}"
                    )

                # Range validation for numbers
                if isinstance(value, (int, float)):
                    min_val = rules.get("min")
                    max_val = rules.get("max")

                    if min_val is not None and value < min_val:
                        errors.append(f"Field '{field}' is below minimum: {min_val}")

                    if max_val is not None and value > max_val:
                        errors.append(f"Field '{field}' exceeds maximum: {max_val}")

                # Pattern validation for strings
                if isinstance(value, str):
                    pattern = rules.get("pattern")
                    if pattern and not re.match(pattern, value):
                        errors.append(f"Field '{field}' doesn't match pattern: {pattern}")

        success = len(errors) == 0

        return SkillResult(
            execution_id=context.execution_id,
            success=success,
            data={
                "is_valid": success,
                "errors": errors,
                "warnings": warnings,
                "validated_fields": len(data),
                "schema_fields": len(schema)
            },
            error="; ".join(errors) if errors else None,
            warnings=warnings
        )


class MathCalculatorSkill(BaseSkill):
    """Skill for performing mathematical calculations"""

    def __init__(self):
        metadata = SkillMetadata(
            name="math_calculator",
            description="Performs mathematical calculations and expressions",
            category=SkillCategory.COMPUTATION,
            version="1.0.0",
            author="Demo",
            tags=["math", "calculation", "computation"],
            parameters=[
                SkillParameter(
                    name="expression",
                    type=str,
                    description="Mathematical expression to evaluate",
                    required=True
                ),
                SkillParameter(
                    name="precision",
                    type=int,
                    description="Number of decimal places",
                    required=False,
                    default=2
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute calculation"""
        expression = kwargs.get("expression", "")
        precision = kwargs.get("precision", 2)

        try:
            # Safe evaluation (limited scope)
            allowed_names = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }

            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)

            # Round to precision
            if isinstance(result, float):
                result = round(result, precision)

            return SkillResult(
                execution_id=context.execution_id,
                success=True,
                data={
                    "expression": expression,
                    "result": result,
                    "precision": precision,
                    "type": type(result).__name__
                }
            )

        except Exception as e:
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error=f"Calculation error: {str(e)}",
                error_type="CalculationError"
            )


class JSONTransformerSkill(BaseSkill):
    """Skill for transforming JSON data"""

    def __init__(self):
        metadata = SkillMetadata(
            name="json_transformer",
            description="Transforms JSON data using mapping rules",
            category=SkillCategory.TRANSFORMATION,
            version="1.0.0",
            author="Demo",
            tags=["json", "transformation", "data"],
            parameters=[
                SkillParameter(
                    name="data",
                    type=dict,
                    description="JSON data to transform",
                    required=True
                ),
                SkillParameter(
                    name="mapping",
                    type=dict,
                    description="Field mapping rules",
                    required=True
                ),
                SkillParameter(
                    name="keep_unmapped",
                    type=bool,
                    description="Keep fields not in mapping",
                    required=False,
                    default=False
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute JSON transformation"""
        data = kwargs.get("data", {})
        mapping = kwargs.get("mapping", {})
        keep_unmapped = kwargs.get("keep_unmapped", False)

        result = {}

        # Apply mapping
        for source_field, target_field in mapping.items():
            if source_field in data:
                result[target_field] = data[source_field]

        # Keep unmapped fields if requested
        if keep_unmapped:
            for field, value in data.items():
                if field not in mapping and field not in result:
                    result[field] = value

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={
                "transformed": result,
                "original_fields": len(data),
                "transformed_fields": len(result),
                "mapping_applied": len(mapping)
            }
        )


class TextAnalyzerSkill(BaseSkill):
    """Skill for analyzing text statistics"""

    def __init__(self):
        metadata = SkillMetadata(
            name="text_analyzer",
            description="Analyzes text and provides statistics",
            category=SkillCategory.TEXT_ANALYSIS,
            version="1.0.0",
            author="Demo",
            tags=["text", "analysis", "statistics"],
            parameters=[
                SkillParameter(
                    name="text",
                    type=str,
                    description="Text to analyze",
                    required=True
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute text analysis"""
        text = kwargs.get("text", "")

        # Calculate statistics
        words = text.split()
        sentences = text.split(".")
        paragraphs = text.split("\n\n")

        # Word frequency
        word_freq = {}
        for word in words:
            word_lower = word.lower().strip(".,!?;:")
            if word_lower:
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={
                "character_count": len(text),
                "word_count": len(words),
                "sentence_count": len([s for s in sentences if s.strip()]),
                "paragraph_count": len([p for p in paragraphs if p.strip()]),
                "unique_words": len(word_freq),
                "top_words": top_words,
                "average_word_length": sum(len(w) for w in words) / len(words) if words else 0
            }
        )


class DataAggregatorSkill(BaseSkill):
    """Skill for aggregating data from multiple sources"""

    def __init__(self):
        metadata = SkillMetadata(
            name="data_aggregator",
            description="Aggregates and combines data from multiple sources",
            category=SkillCategory.DATA_PROCESSING,
            version="1.0.0",
            author="Demo",
            tags=["data", "aggregation", "merge"],
            parameters=[
                SkillParameter(
                    name="sources",
                    type=list,
                    description="List of data sources to aggregate",
                    required=True
                ),
                SkillParameter(
                    name="strategy",
                    type=str,
                    description="Aggregation strategy (merge, concat, reduce)",
                    required=False,
                    default="merge"
                )
            ]
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        """Execute data aggregation"""
        sources = kwargs.get("sources", [])
        strategy = kwargs.get("strategy", "merge")

        if not sources:
            return SkillResult(
                execution_id=context.execution_id,
                success=False,
                data=None,
                error="No sources provided"
            )

        result = None

        if strategy == "merge":
            # Merge dictionaries
            result = {}
            for source in sources:
                if isinstance(source, dict):
                    result.update(source)

        elif strategy == "concat":
            # Concatenate lists
            result = []
            for source in sources:
                if isinstance(source, list):
                    result.extend(source)

        elif strategy == "reduce":
            # Reduce to summary statistics
            result = {
                "total_sources": len(sources),
                "total_items": sum(len(s) if isinstance(s, (list, dict)) else 1 for s in sources),
                "data": sources
            }

        return SkillResult(
            execution_id=context.execution_id,
            success=True,
            data={
                "aggregated": result,
                "source_count": len(sources),
                "strategy": strategy
            }
        )
