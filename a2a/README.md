# A2A (Agent-to-Agent) 协议示例

这是一个完整的Agent之间通信协议的Python实现示例。

## 功能特性

- **标准化消息格式**: 定义了统一的消息结构(请求/响应/通知/错误)
- **消息路由**: 通过MessageBroker实现Agent间的消息路由
- **异步通信**: 基于asyncio的异步消息处理
- **请求-响应模式**: 支持同步等待响应的请求模式
- **通知机制**: 支持单向通知消息
- **多Agent协作**: 支持多个Agent协同完成复杂任务

## 项目结构

```
a2a/
├── __init__.py           # 包初始化
├── protocol.py           # A2A协议定义(消息格式)
├── base_agent.py         # Agent基类
├── message_broker.py     # 消息代理(路由器)
├── agent_impl.py         # Agent具体实现
├── demo_agents.py        # 示例Agent(天气、分析、协调等)
├── demo.py              # 完整示例程序
└── README.md            # 说明文档
```

## 核心组件

### 1. A2AMessage (protocol.py)
定义了四种消息类型:
- **REQUEST**: 请求消息,需要响应
- **RESPONSE**: 响应消息
- **NOTIFICATION**: 通知消息,不需要响应
- **ERROR**: 错误消息

### 2. BaseAgent (base_agent.py)
Agent基类,提供:
- 消息处理器注册
- 发送/接收消息
- 请求-响应模式
- 通知发送

### 3. MessageBroker (message_broker.py)
消息代理,负责:
- Agent注册/注销
- 消息路由
- 广播消息

### 4. 示例Agents (demo_agents.py)
- **WeatherAgent**: 天气查询服务
- **DataAnalysisAgent**: 数据分析服务
- **TaskCoordinatorAgent**: 任务协调器
- **MonitorAgent**: 系统监控

## 运行示例

```bash
# 进入项目目录
cd c:\Users\xiaozongliu-jk\PycharmProjects\llm-demo

# 运行完整示例
python -m a2a.demo
```

## 示例说明

### 示例1: 基本Agent通信
演示单个Agent的请求-响应通信模式

### 示例2: 多Agent协作
演示TaskCoordinator协调WeatherAgent和DataAnalysisAgent完成复杂任务:
1. 并发查询多个城市天气
2. 收集温度数据
3. 调用分析Agent计算统计信息

### 示例3: 事件通知系统
演示使用通知机制实现事件监控系统

### 示例4: 并发请求处理
演示同时处理多个并发请求

## 使用方法

### 创建自定义Agent

```python
from a2a.agent_impl import BrokerAgent
from a2a.protocol import A2AMessage

class MyAgent(BrokerAgent):
    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "MyAgent", broker)

        # 注册消息处理器
        self.register_handler("my_action", self.handle_my_action)

    async def handle_my_action(self, message: A2AMessage):
        # 处理逻辑
        return {"result": "success"}
```

### 发送请求

```python
# 发送请求并等待响应
result = await agent.send_request(
    receiver_id="target_agent",
    action="query_weather",
    payload={"city": "beijing"}
)
```

### 发送通知

```python
# 发送通知(不等待响应)
await agent.send_notification(
    receiver_id="monitor_agent",
    action="event",
    payload={"type": "update"}
)
```

## 扩展建议

1. **持久化**: 添加消息持久化,防止消息丢失
2. **网络通信**: 将MessageBroker扩展为支持网络通信
3. **安全认证**: 添加Agent身份认证和消息加密
4. **消息队列**: 集成RabbitMQ/Kafka等消息队列
5. **监控面板**: 添加Web界面监控Agent状态和消息流
6. **负载均衡**: 支持相同类型的多个Agent实例

## 依赖

- Python 3.7+
- asyncio (标准库)

无需额外安装依赖包,使用Python标准库即可运行。
