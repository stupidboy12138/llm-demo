# A2UI - Agent to UI Interface Demo

完整的 A2A 协议与 Web UI 集成示例，展示如何构建基于 Agent 的 Web 应用。

## 📋 目录结构

```
ai/a2ui/
├── __init__.py           # 包初始化
├── web_agent.py          # WebAgent - Web界面代理
├── demo_agents.py        # 示例Agent实现
│   ├── AIAssistantAgent  # AI智能助手
│   ├── WeatherAgent      # 天气查询服务
│   ├── CalculatorAgent   # 数学计算器
│   └── TaskCoordinatorAgent # 任务协调器
├── api_server.py         # FastAPI服务器
├── demo.py               # 启动脚本
├── test_client.py        # 测试客户端
├── static/
│   └── index.html        # Web前端界面
└── README.md             # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

确保已安装所有必需的依赖：

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install fastapi uvicorn aiohttp websockets
```

### 2. 启动服务

```bash
# 方法1: 使用启动脚本
python -m ai.a2ui.demo

# 方法2: 直接运行API服务器
python -m ai.a2ui.api_server

# 方法3: 使用 uvicorn
uvicorn ai.a2ui.api_server:app --host 0.0.0.0 --port 8000
```

### 3. 访问界面

服务启动后，访问：

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 4. 运行测试

```bash
# 自动化测试
python -m ai.a2ui.test_client

# 命令行聊天模式
python -m ai.a2ui.test_client chat
```

## 🎯 功能特性

### 1. 多Agent支持

系统包含多个功能性Agent：

#### AI智能助手 (`ai_assistant`)
- 智能对话和问答
- 上下文记忆
- 多轮对话支持

**示例**:
```python
# API调用
POST /chat
{
  "message": "你好，你能做什么？",
  "session_id": "user123",
  "agent_type": "ai_assistant"
}
```

#### 天气查询 (`weather_agent`)
- 查询城市天气
- 温度、湿度、天气状况
- 未来天气预报

**示例**:
```python
# 查询天气
POST /chat
{
  "message": "北京",
  "agent_type": "weather"
}

# 支持的城市
北京、上海、广州、深圳、成都
```

#### 计算器 (`calculator_agent`)
- 基础数学运算
- 复杂表达式计算
- 支持数学函数（sin, cos, sqrt等）

**示例**:
```python
# 简单计算
POST /chat
{
  "message": "100 + 200 * 3",
  "agent_type": "calculator"
}
```

#### 任务协调器 (`task_coordinator`)
- 多Agent协作
- 复杂任务分解
- 并发处理

### 2. RESTful API

#### 聊天接口
```http
POST /chat
Content-Type: application/json

{
  "message": "用户消息",
  "session_id": "会话ID（可选）",
  "agent_type": "ai_assistant|weather|calculator"
}
```

#### 获取Agent列表
```http
GET /agents
```

#### 会话历史
```http
# 获取历史
GET /history/{session_id}

# 清除历史
DELETE /history/{session_id}
```

#### 健康检查
```http
GET /health
```

### 3. WebSocket支持

实时双向通信：

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client_id');

// 发送消息
ws.send(JSON.stringify({
  type: "chat",
  message: "你好",
  agent_type: "ai_assistant"
}));

// 接收消息
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### 4. Web前端界面

现代化的Web UI，支持：

- 实时聊天界面
- Agent切换
- 消息历史
- 示例快捷按钮
- 响应式设计

## 📖 使用示例

### Python客户端示例

```python
import aiohttp
import asyncio

async def chat_with_ai():
    url = "http://localhost:8000/chat"

    async with aiohttp.ClientSession() as session:
        # 与AI助手对话
        async with session.post(url, json={
            "message": "你好，AI助手！",
            "session_id": "test_session",
            "agent_type": "ai_assistant"
        }) as response:
            data = await response.json()
            print(f"AI: {data['response']}")

        # 查询天气
        async with session.post(url, json={
            "message": "北京",
            "agent_type": "weather"
        }) as response:
            data = await response.json()
            print(f"天气: {data['response']}")

        # 计算
        async with session.post(url, json={
            "message": "123 + 456",
            "agent_type": "calculator"
        }) as response:
            data = await response.json()
            print(f"结果: {data['response']}")

asyncio.run(chat_with_ai())
```

### cURL示例

```bash
# AI对话
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "agent_type": "ai_assistant"}'

# 查询天气
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "上海", "agent_type": "weather"}'

# 计算
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "100 * 99", "agent_type": "calculator"}'

# 获取Agent列表
curl http://localhost:8000/agents

# 健康检查
curl http://localhost:8000/health
```

### JavaScript/Fetch示例

```javascript
// 发送聊天消息
async function sendMessage(message, agentType = 'ai_assistant') {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: 'web_session',
      agent_type: agentType
    })
  });

  const data = await response.json();
  return data.response;
}

// 使用示例
sendMessage("你好！").then(response => {
  console.log("AI:", response);
});

sendMessage("北京", "weather").then(response => {
  console.log("天气:", response);
});
```

## 🏗️ 架构设计

### 系统架构

```
┌─────────────┐
│  Web Browser│
│  (Frontend) │
└──────┬──────┘
       │ HTTP/WebSocket
       ▼
┌─────────────┐
│  FastAPI    │
│  API Server │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────────┐
│  WebAgent   │─────▶│  Message Broker  │
└─────────────┘      └────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              ┌─────▼─────┐       ┌────▼────┐
              │ AI Agent  │       │Weather  │
              │           │       │ Agent   │
              └───────────┘       └─────────┘
                    │                   │
              ┌─────▼─────┐       ┌────▼────┐
              │Calculator │       │  Task   │
              │  Agent    │       │Coordinator
              └───────────┘       └─────────┘
```

### 消息流程

1. **HTTP请求流程**:
   ```
   用户 → FastAPI → WebAgent → MessageBroker → 目标Agent
                                               ↓
   用户 ← FastAPI ← WebAgent ← MessageBroker ← 响应
   ```

2. **WebSocket流程**:
   ```
   用户 ⇄ WebSocket连接 ⇄ FastAPI ⇄ WebAgent ⇄ MessageBroker ⇄ Agent
   ```

3. **Agent间通信**:
   ```
   Agent A → MessageBroker → Agent B
                           ↓
   Agent A ← MessageBroker ← Agent B
   ```

### 核心组件

#### 1. WebAgent (web_agent.py)
- 桥接Web请求和A2A协议
- 会话管理
- 消息路由

#### 2. API Server (api_server.py)
- FastAPI应用
- RESTful API端点
- WebSocket支持
- CORS配置

#### 3. Demo Agents (demo_agents.py)
- 功能性Agent实现
- 消息处理逻辑
- 业务逻辑封装

## 🔧 自定义Agent

### 创建新Agent

```python
from a2a.agent_impl import BrokerAgent
from a2a.protocol import A2AMessage
from a2a.message_broker import MessageBroker

class CustomAgent(BrokerAgent):
    """自定义Agent"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "自定义Agent", broker)

        # 注册处理器
        self.register_handler("custom_action", self.handle_custom)

    async def handle_custom(self, message: A2AMessage) -> dict:
        """处理自定义消息"""
        data = message.payload.get("data", "")

        # 处理逻辑
        result = f"处理结果: {data}"

        return {
            "response": result,
            "timestamp": datetime.now().isoformat()
        }
```

### 注册到服务器

在 `api_server.py` 中添加：

```python
@app.on_event("startup")
async def startup_event():
    global custom_agent

    # ... 现有代码 ...

    # 创建自定义Agent
    custom_agent = CustomAgent("custom_agent", broker)
    await custom_agent.start()
```

### 添加API端点

```python
@app.post("/custom")
async def custom_endpoint(request: CustomRequest):
    response = await web_agent.forward_to_agent(
        "custom_agent",
        "custom_action",
        {"data": request.data}
    )
    return response
```

## 🧪 测试

### 自动化测试

```bash
# 运行完整测试套件
python -m ai.a2ui.test_client

# 测试包括:
# - 健康检查
# - Agent列表
# - AI对话
# - 天气查询
# - 计算器
# - 会话历史
# - 并发请求
# - WebSocket通信
```

### 交互式测试

```bash
# 命令行聊天界面
python -m ai.a2ui.test_client chat

# 可用命令:
# - 直接输入: 与AI助手对话
# - /weather 城市名: 查询天气
# - /calc 表达式: 计算
# - quit: 退出
```

### 性能测试

```python
# 并发测试
async def stress_test():
    tasks = []
    for i in range(100):
        task = send_message(f"测试消息 {i}")
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    print(f"完成 {len(results)} 个请求")
```

## 📊 监控与日志

### 日志配置

系统使用Python标准logging模块：

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 查看日志

```bash
# 启动服务时会输出详细日志
python -m ai.a2ui.demo

# 示例输出:
# 2024-01-08 15:00:00 - INFO - 初始化A2UI系统...
# 2024-01-08 15:00:01 - INFO - [WebAgent] 注册处理器: chat
# 2024-01-08 15:00:02 - INFO - A2UI系统启动完成!
```

## ⚠️ 注意事项

1. **安全性**
   - 示例代码中计算器使用`eval()`，生产环境应使用安全的表达式解析器
   - 添加输入验证和清理
   - 实施认证和授权机制

2. **扩展性**
   - MessageBroker是内存实现，可扩展为Redis/RabbitMQ
   - 会话历史存储在内存，生产环境应使用数据库

3. **错误处理**
   - 所有Agent操作都有超时设置
   - 异常会被捕获并返回错误消息
   - WebSocket断线会自动清理连接

## 🚀 部署建议

### 开发环境
```bash
uvicorn ai.a2ui.api_server:app --reload --host 0.0.0.0 --port 8000
```

### 生产环境
```bash
# 使用多worker
uvicorn ai.a2ui.api_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info

# 或使用gunicorn
gunicorn ai.a2ui.api_server:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "ai.a2ui.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 相关资源

- [A2A协议文档](../../a2a/README.md)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [WebSocket指南](https://websockets.readthedocs.io/)
- [LangChain集成](../langchain/README.md)

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

本项目遵循项目主许可证。
