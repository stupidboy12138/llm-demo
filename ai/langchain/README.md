# LangChain Agent Demo

这是一个基于 LangChain 和 LangGraph 的 Agent Demo，使用 LiteLLM API 作为模型后端，封装为高性能异步 FastAPI 服务。

> **注意**: 此项目使用 LangChain 1.2.0+ 和 LangGraph，采用新的 ReAct Agent API。

## 功能特性

### Agent 能力
- ⏰ **获取当前时间** - 查询当前日期和时间
- 🧮 **数学计算器** - 进行数学表达式计算
- 📚 **知识库搜索** - 搜索预置的知识库信息

### API 特性
- 🚀 **高性能异步** - 基于 FastAPI 和 asyncio
- 🌊 **流式响应** - 支持 Server-Sent Events (SSE) 流式输出
- 📦 **批量处理** - 支持异步并发批量请求
- 💬 **对话历史** - 支持多轮对话上下文
- 📝 **完整文档** - 自动生成的 Swagger/OpenAPI 文档

## 安装依赖

```bash
# 使用 uv 安装依赖（推荐）
uv sync

# 或使用 pip 安装
pip install -r requirements.txt
```

## 启动服务

```bash
# 进入项目目录
cd ai/langchain

# 启动服务
python langchain_demo.py
```

服务将在 `http://localhost:8000` 启动。

访问 `http://localhost:8000/docs` 查看 API 文档。

## API 使用示例

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

### 2. 普通对话（非流式）

```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "现在几点了？",
    "history": []
  }'
```

### 3. 流式对话

```bash
curl -X POST "http://localhost:8000/agent/chat-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我计算 123 * 456",
    "history": []
  }'
```

### 4. 带历史记录的对话

```bash
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "再加上100呢？",
    "history": [
      {
        "role": "user",
        "content": "帮我计算 123 * 456"
      },
      {
        "role": "assistant",
        "content": "计算结果: 123 * 456 = 56088"
      }
    ]
  }'
```

### 5. 批量请求

```bash
curl -X POST "http://localhost:8000/agent/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {"message": "现在几点？"},
    {"message": "100 + 200 等于多少？"},
    {"message": "什么是Python？"}
  ]'
```

## Python 客户端示例

```python
import asyncio
import httpx

async def test_chat():
    async with httpx.AsyncClient() as client:
        # 普通对话
        response = await client.post(
            "http://localhost:8000/agent/chat",
            json={
                "message": "现在几点了？",
                "history": []
            }
        )
        print(response.json())

async def test_stream():
    async with httpx.AsyncClient() as client:
        # 流式对话
        async with client.stream(
            "POST",
            "http://localhost:8000/agent/chat-stream",
            json={"message": "帮我计算 123 * 456"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    print(line[6:])

# 运行测试
asyncio.run(test_chat())
asyncio.run(test_stream())
```

## 配置说明

### LiteLLM API 配置

在 `langchain_demo.py` 中修改以下配置：

```python
LITELLM_API_BASE = "https://litellm-dev.sandbox.deepbank.daikuan.qihoo.net/v1"
LITELLM_API_KEY = "sk-KTstOcJjNhj6d5esFfwj9g"
```

### 模型配置

```python
self.llm = ChatOpenAI(
    model="gpt-4o-mini",  # 修改为实际支持的模型
    openai_api_base=LITELLM_API_BASE,
    openai_api_key=LITELLM_API_KEY,
    temperature=0.7,
    streaming=True,
)
```

## 自定义工具

可以在 `langchain_demo.py` 中添加自定义工具：

```python
def custom_tool(query: str) -> str:
    """自定义工具描述"""
    # 实现你的工具逻辑
    return "工具执行结果"

# 添加到工具列表
tools.append(
    Tool(
        name="自定义工具",
        func=custom_tool,
        description="工具的使用场景和说明",
    )
)
```

## 性能优化建议

### 生产环境配置

```python
uvicorn.run(
    "langchain_demo:app",
    host="0.0.0.0",
    port=8000,
    workers=4,  # 根据 CPU 核心数调整
    limit_concurrency=1000,  # 限制并发连接数
    timeout_keep_alive=30,
)
```

### 使用 Gunicorn

```bash
pip install gunicorn

gunicorn langchain_demo:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

## 项目结构

```
ai/langchain/
├── langchain_demo.py    # 主程序文件
├── README.md           # 使用说明
└── test_client.py      # 测试客户端
```

## 常见问题

### 1. API 连接失败

检查 LiteLLM API 的网络连接和认证信息是否正确。

### 2. Agent 不调用工具

确保提示词（prompt）清晰地说明了工具的使用场景，并且用户的问题确实需要使用工具。

### 3. 流式响应不完整

检查客户端是否正确处理 SSE 事件流，确保保持连接直到收到 `done` 事件。

## 许可证

MIT License

