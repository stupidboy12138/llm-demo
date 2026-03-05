# Feishu Document Reader Skill

A skill for reading and extracting content from Feishu (Lark) documents. This skill supports reading document content, metadata, tables, and comments from Feishu documents using the Feishu Open API.

## Features

- **Document Content Extraction**: Extract text content from Feishu documents with optional formatting preservation
- **Metadata Reading**: Get document metadata including title, owner, creation time, and modification time
- **Table Extraction**: Read and extract data from tables within documents
- **Comments Reading**: Extract comments and discussions from documents
- **Flexible Extraction**: Choose to extract specific content types or all content at once

## Prerequisites

1. **Feishu App Credentials**: You need to create a Feishu app and obtain:
   - App ID
   - App Secret

2. **Environment Variables**: Set the following environment variables:
   ```bash
   export FEISHU_APP_ID="your_app_id"
   export FEISHU_APP_SECRET="your_app_secret"
   ```

3. **Document Access**: Ensure your Feishu app has permission to access the documents you want to read

## Installation

The skill is included in the skills framework. Make sure to install the required dependencies:

```bash
pip install requests python-dotenv
```

## Usage

### Basic Usage

```python
from ai.skills.skill_registry import SkillRegistry
from ai.skills.skill_executor import SkillExecutor
from ai.skills.feishu_document_reader import FeishuDocumentReaderSkill

# Initialize
registry = SkillRegistry()
executor = SkillExecutor(registry)

# Register the skill
feishu_skill = FeishuDocumentReaderSkill()
registry.register(feishu_skill)

# Execute the skill
result = await executor.execute(
    "feishu_document_reader",
    document_url="https://example.feishu.cn/docx/ABC123XYZ",
    extract_type="all"  # or 'content', 'metadata', 'tables', 'comments'
)

if result.success:
    print("Document content:", result.data["content"]["text_content"])
    print("Document title:", result.data["metadata"]["title"])
else:
    print("Error:", result.error)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_url` | str | Yes | URL of the Feishu document to read |
| `extract_type` | str | No | Type of content to extract: 'content', 'metadata', 'tables', 'comments', or 'all' (default: 'all') |
| `app_id` | str | No | Feishu App ID (can use FEISHU_APP_ID env var) |
| `app_secret` | str | No | Feishu App Secret (can use FEISHU_APP_SECRET env var) |
| `include_formatting` | bool | No | Whether to preserve formatting in extracted content (default: True) |

### Extract Types

- **all**: Extract all available content types
- **content**: Extract only the document text content
- **metadata**: Extract only document metadata
- **tables**: Extract only tables from the document
- **comments**: Extract only comments from the document

## Supported Document Types

The skill supports various Feishu document types:
- **docx**: Feishu documents (docx)
- **sheets**: Feishu spreadsheets
- **base**: Feishu databases
- **mindnotes**: Feishu mind maps
- **bitable**: Feishu bitables

## Output Format

The skill returns a structured result with the following data:

```json
{
  "document_url": "https://example.feishu.cn/docx/ABC123XYZ",
  "document_info": {
    "tenant": "example",
    "doc_type": "docx",
    "doc_token": "ABC123XYZ"
  },
  "extracted_at": "2024-01-01T12:00:00",
  "content": {
    "raw_content": {...},
    "text_content": "Extracted text content...",
    "block_count": 42
  },
  "metadata": {
    "title": "Document Title",
    "owner_id": "user123",
    "create_time": "2024-01-01T10:00:00",
    "edit_time": "2024-01-01T11:30:00",
    "revision_id": "rev123",
    "document_status": "normal",
    "is_external": false
  },
  "tables": [
    {
      "table_id": "table123",
      "table_data": {...}
    }
  ],
  "comments": [
    {
      "comment_id": "comment123",
      "content": "This is a comment",
      "author": "user456",
      "create_time": "2024-01-01T11:00:00",
      "replies": []
    }
  ]
}
```

## Error Handling

The skill handles various error scenarios:
- Missing credentials
- Invalid document URLs
- API authentication failures
- Document access permission issues
- Network errors

## Testing

Run the test script to verify the skill is working:

```bash
python -m ai.skills.feishu_document_reader.test_skill
```

Run the example usage script with a real document:

```bash
python -m ai.skills.feishu_document_reader.scripts.example_usage "https://your.feishu.cn/docx/DOC123" all
```

## Creating a Feishu App

1. Go to [Feishu Open Platform](https://open.feishu.cn/)
2. Create a new app
3. Enable the following permissions:
   - `docs:document:readonly` - Read document content
   - `docs:document:readonly:comment` - Read document comments
4. Get your App ID and App Secret from the app credentials page
5. Set the environment variables with your credentials

## Limitations

- Requires valid Feishu app credentials
- Document must be accessible by the app
- Some document types may have limited support
- Large documents may take time to process
- Rate limits apply based on Feishu API quotas

## Troubleshooting

### Authentication Error
- Verify your App ID and App Secret are correct
- Check that environment variables are set properly
- Ensure your app has the required permissions

### Document Not Found
- Verify the document URL is correct
- Check that the document exists and is accessible
- Ensure your app has permission to access the document

### Empty Content
- Some documents may have restricted access
- Check if the document has any content
- Verify the extract_type parameter is set correctly