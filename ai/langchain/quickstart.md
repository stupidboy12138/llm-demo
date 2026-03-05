# 快速入门指南

## 1. 安装依赖

```bash
# 确保在项目根目录
cd C:\Users\xiaozongliu-jk\PycharmProjects\llm-demo

# 使用 uv 同步依赖
uv sync
```

## 2. 启动服务

```bash
# 进入 langchain 目录
cd ai\langchain

# 启动 FastAPI 服务
python langchain_demo.py
```

服务启动后，你会看到：
```
🚀 LangChain Agent API 启动成功!
📝 API文档地址: http://localhost:8000/docs
```

## 3. 测试服务

### 方式1: 浏览器访问

打开浏览器访问：http://localhost:8000/docs

你将看到 Swagger UI 界面，可以直接测试所有 API 端点。

### 方式2: 使用测试脚本

```bash
# 在另一个终端窗口运行
python test_client.py
```

### 方式3: 交互式模式

```bash
python test_client.py interactive
```

然后你可以与 Agent 进行对话：
```
你: 现在几点了？
Agent: 当前时间是: 2026-01-05 10:30:00

你: 帮我计算 123 * 456
Agent: 计算结果: 123 * 456 = 56088
```

### 方式4: 使用 curl

```bash
# Windows PowerShell
curl -X POST "http://localhost:8000/agent/chat" `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"现在几点了？\"}'
```

## 4. API 端点说明

### GET /health
健康检查端点

### POST /agent/chat
普通对话（非流式）

请求示例：
```json
{
  "message": "现在几点了？",
  "history": []
}
```

### POST /agent/chat-stream
流式对话（SSE）

返回 Server-Sent Events 格式的流式响应。

### POST /agent/batch
批量并发请求

请求示例：
```json
[
  {"message": "现在几点？"},
  {"message": "100 + 200 等于多少？"}
]
```

## 5. 常见问题

### 无法启动服务？

1. 检查端口 8000 是否被占用：
```bash
netstat -ano | findstr :8000
```

2. 如果被占用，可以修改 `langchain_demo.py` 中的端口号。

### Agent 无法调用 LiteLLM API？

1. 检查网络连接
2. 确认 API 密钥有效
3. 查看控制台错误日志

### 工具没有被调用？

这是正常的。Agent 会根据用户问题自动判断是否需要使用工具。例如：
- "现在几点？" → 会调用 `get_current_time` 工具
- "你好" → 不会调用任何工具，直接回答

## 6. 自定义开发

### 添加新工具

在 `langchain_demo.py` 中添加：

```python
@tool
def your_custom_tool(param: str) -> str:
    """工具描述，Agent 会根据这个描述决定何时使用"""
    # 实现你的逻辑
    return "结果"

# 添加到工具列表
tools = [get_current_time, calculate_math, search_knowledge, your_custom_tool]
```

### 修改系统提示词

在 `LangChainAgent.__init__` 方法中修改 `self.system_prompt`。

### 调整模型参数

修改 `ChatOpenAI` 的参数：
```python
self.llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,  # 调整温度
    max_tokens=2000,  # 设置最大 token 数
)
```

## 7. 性能优化

### 使用多进程

生产环境使用 Gunicorn：
```bash
pip install gunicorn
gunicorn langchain_demo:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 添加缓存

可以集成 Redis 等缓存系统来缓存常见查询结果。

### 限流

使用 FastAPI 的 `slowapi` 中间件添加请求限流：
```bash
pip install slowapi
```

## 8. 部署建议

### Docker 部署

创建 Dockerfile：
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "ai/langchain/langchain_demo.py"]
```

### 环境变量

建议将敏感信息移到环境变量：
```python
import os
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "your-default-key")
```

## 需要帮助？

查看完整文档：[README.md](README.md)

