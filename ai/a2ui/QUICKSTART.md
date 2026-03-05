# A2UI 快速入门指南

5分钟上手 A2UI - Agent to UI Interface

## 🚀 快速开始

### 1. 启动服务（3种方式）

#### 方式1: 使用启动脚本（推荐）
```bash
python -m ai.a2ui.run
# 或
python ai/a2ui/run.py
```

#### 方式2: 直接运行demo
```bash
python -m ai.a2ui.demo
```

#### 方式3: 使用uvicorn
```bash
uvicorn ai.a2ui.api_server:app --reload
```

### 2. 访问界面

打开浏览器访问: **http://localhost:8000**

### 3. 开始使用

在Web界面上：
1. 选择一个Agent（左侧面板）
2. 输入消息
3. 点击发送
4. 查看响应

## 📝 基础示例

### Python客户端

```python
import aiohttp
import asyncio

async def chat():
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/chat', json={
            "message": "你好！",
            "agent_type": "ai_assistant"
        }) as response:
            data = await response.json()
            print(data['response'])

asyncio.run(chat())
```

### cURL命令

```bash
# AI对话
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "agent_type": "ai_assistant"}'

# 查询天气
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京", "agent_type": "weather"}'

# 计算
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "100 + 200", "agent_type": "calculator"}'
```

### JavaScript/Fetch

```javascript
async function chat(message, agentType = 'ai_assistant') {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: message,
      agent_type: agentType
    })
  });
  const data = await response.json();
  console.log(data.response);
}

// 使用
chat("你好！");
chat("北京", "weather");
chat("100 * 99", "calculator");
```

## 🧪 运行测试

### 自动化测试
```bash
python -m ai.a2ui.test_client
```

### 命令行聊天
```bash
python -m ai.a2ui.test_client chat
```

### 运行示例
```bash
# 运行所有示例
python -m ai.a2ui.examples

# 运行特定示例
python -m ai.a2ui.examples basic      # 基础聊天
python -m ai.a2ui.examples agents     # 多Agent
python -m ai.a2ui.examples concurrent # 并发请求
python -m ai.a2ui.examples ws         # WebSocket
```

## 🎯 可用的Agents

### 1. AI助手 (`ai_assistant`)
智能对话Agent，支持多轮对话

**示例**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你能做什么？", "agent_type": "ai_assistant"}'
```

### 2. 天气查询 (`weather`)
查询城市天气信息

**支持城市**: 北京、上海、广州、深圳、成都

**示例**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "上海", "agent_type": "weather"}'
```

### 3. 计算器 (`calculator`)
执行数学计算

**示例**:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "(100 + 200) * 3", "agent_type": "calculator"}'
```

## 📚 API端点

### 聊天接口
```
POST /chat
```

**请求体**:
```json
{
  "message": "你的消息",
  "session_id": "会话ID（可选）",
  "agent_type": "ai_assistant|weather|calculator"
}
```

**响应**:
```json
{
  "response": "Agent的响应",
  "session_id": "会话ID",
  "timestamp": "时间戳",
  "agent": "agent类型"
}
```

### 其他端点

```bash
# 健康检查
GET /health

# Agent列表
GET /agents

# 获取历史
GET /history/{session_id}

# 清除历史
DELETE /history/{session_id}

# API文档
GET /docs
```

## 🔌 WebSocket使用

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/my_client');

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

## ❓ 常见问题

### 1. 服务无法启动？

检查端口是否被占用:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

使用其他端口:
```bash
uvicorn ai.a2ui.api_server:app --port 8080
```

### 2. 连接错误？

确保服务已启动并运行:
```bash
curl http://localhost:8000/health
```

### 3. Agent不响应？

检查日志输出，确认Agent已正确初始化。

## 📖 下一步

- 阅读完整文档: [README.md](README.md)
- 查看示例代码: [examples.py](examples.py)
- 学习自定义Agent: [README.md#自定义Agent](README.md#自定义agent)
- 了解A2A协议: [../../a2a/README.md](../../a2a/README.md)

## 💡 提示

1. **使用会话ID**: 保持对话上下文
   ```python
   {"message": "消息", "session_id": "user123"}
   ```

2. **并发请求**: 使用`asyncio.gather()`提高性能
   ```python
   results = await asyncio.gather(*tasks)
   ```

3. **错误处理**: 总是检查响应状态
   ```python
   if response.ok:
       data = await response.json()
   else:
       print(f"错误: {response.status}")
   ```

4. **超时设置**: 为长时间操作设置超时
   ```python
   timeout = aiohttp.ClientTimeout(total=30)
   async with session.post(url, json=data, timeout=timeout) as response:
       ...
   ```

## 🎉 完成！

现在你已经掌握了A2UI的基础使用。开始构建你的Agent应用吧！

有问题？查看[完整文档](README.md)或提交Issue。
