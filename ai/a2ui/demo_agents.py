"""
示例Agent实现 - 使用真实LLM模型
包含多个功能性Agent用于演示
"""
import asyncio
from datetime import datetime
import logging
from typing import Dict, List, Optional
import random

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from a2a.protocol import A2AMessage
from a2a.message_broker import MessageBroker
from a2a.agent_impl import BrokerAgent
from .config import default_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAssistantAgent(BrokerAgent):
    """AI助手Agent - 使用真实LLM进行智能对话"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "AI智能助手", broker)
        self.conversation_context: Dict[str, List] = {}

        # 初始化LLM模型
        llm_config = default_config.llm
        self.llm = ChatOpenAI(
            model=llm_config.model,
            base_url=llm_config.api_base,
            api_key=llm_config.api_key,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
            timeout=llm_config.timeout,
        )

        # 系统提示词
        self.system_prompt = """你是一个友好、专业的AI助手，隶属于A2UI系统。

你的能力包括：
1. 智能对话 - 回答各种问题，提供有价值的信息
2. 任务协调 - 可以调用天气Agent、计算器Agent等协作完成任务
3. 上下文理解 - 记住对话历史，提供连贯的交互体验

回答要求：
- 友好、专业、简洁
- 中文回答（除非用户使用其他语言）
- 对于天气查询，建议使用天气Agent
- 对于计算任务，建议使用计算器Agent
- 保持对话的连贯性和上下文相关性"""

        # 注册处理器
        self.register_handler("chat", self.handle_chat)
        self.register_handler("chat_stream", self.handle_chat_stream)
        self.register_handler("summarize", self.handle_summarize)

    async def handle_chat(self, message: A2AMessage) -> Dict:
        """处理聊天消息"""
        user_message = message.payload.get("message", "")
        session_id = message.payload.get("session_id", "default")

        logger.info(f"[AI助手] 处理消息: {user_message[:50]}... (session: {session_id})")

        try:
            # 构建消息历史
            messages = self._build_message_history(session_id, user_message)

            # 调用LLM
            response = await asyncio.to_thread(self.llm.invoke, messages)
            response_text = response.content

            # 保存到上下文
            self._save_to_context(session_id, user_message, response_text)

            logger.info(f"[AI助手] 生成响应: {response_text[:50]}...")

            return {
                "response": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "model": default_config.llm.model
            }

        except Exception as e:
            logger.error(f"[AI助手] 错误: {e}")
            return {
                "response": f"抱歉，处理您的请求时出错了: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "error": True
            }

    async def handle_chat_stream(self, message: A2AMessage) -> Dict:
        """处理流式聊天消息"""
        user_message = message.payload.get("message", "")
        session_id = message.payload.get("session_id", "default")

        logger.info(f"[AI助手] 流式处理: {user_message[:50]}...")

        try:
            messages = self._build_message_history(session_id, user_message)

            # 流式响应（这里简化处理，实际可以用SSE）
            full_response = ""
            async for chunk in self._stream_response(messages):
                full_response += chunk

            self._save_to_context(session_id, user_message, full_response)

            return {
                "response": full_response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "stream": True
            }

        except Exception as e:
            logger.error(f"[AI助手] 流式错误: {e}")
            return {
                "response": f"抱歉，处理出错: {str(e)}",
                "session_id": session_id,
                "error": True
            }

    async def _stream_response(self, messages):
        """流式生成响应"""
        try:
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"流式生成错误: {e}")
            yield f"[错误: {str(e)}]"

    def _build_message_history(self, session_id: str, user_message: str) -> List:
        """构建消息历史"""
        messages = [SystemMessage(content=self.system_prompt)]

        # 获取上下文历史
        if session_id in self.conversation_context:
            context = self.conversation_context[session_id]
            # 只保留最近的N条消息
            max_context = default_config.agent.context_window
            recent_context = context[-(max_context * 2):]  # 用户+助手成对

            for ctx in recent_context:
                if ctx["role"] == "user":
                    messages.append(HumanMessage(content=ctx["content"]))
                else:
                    messages.append(AIMessage(content=ctx["content"]))

        # 添加当前消息
        messages.append(HumanMessage(content=user_message))

        return messages

    def _save_to_context(self, session_id: str, user_message: str, ai_response: str):
        """保存到上下文"""
        if session_id not in self.conversation_context:
            self.conversation_context[session_id] = []

        context = self.conversation_context[session_id]
        context.append({"role": "user", "content": user_message})
        context.append({"role": "assistant", "content": ai_response})

        # 限制历史长度
        max_length = default_config.agent.max_history_length
        if len(context) > max_length:
            self.conversation_context[session_id] = context[-max_length:]

    async def handle_summarize(self, message: A2AMessage) -> Dict:
        """总结对话"""
        session_id = message.payload.get("session_id", "default")

        if session_id not in self.conversation_context:
            return {"summary": "暂无对话历史"}

        messages = self.conversation_context[session_id]
        count = len(messages)

        # 使用LLM生成总结
        try:
            summary_prompt = f"请总结以下对话（共{count // 2}轮）:\n\n"
            for msg in messages:
                role = "用户" if msg["role"] == "user" else "助手"
                summary_prompt += f"{role}: {msg['content']}\n"

            summary_messages = [
                SystemMessage(content="你是一个专业的对话总结助手，请简洁准确地总结对话内容。"),
                HumanMessage(content=summary_prompt)
            ]

            response = await asyncio.to_thread(self.llm.invoke, summary_messages)

            return {
                "summary": response.content,
                "message_count": count,
                "session_id": session_id
            }
        except Exception as e:
            return {
                "summary": f"总结失败: {str(e)}",
                "message_count": count
            }


class WeatherAgent(BrokerAgent):
    """天气查询Agent"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "天气查询服务", broker)

        # 模拟天气数据库
        self.weather_data = {
            "北京": {"temp": 15, "condition": "晴朗", "humidity": 45, "wind": "东北风3级"},
            "上海": {"temp": 22, "condition": "多云", "humidity": 65, "wind": "东南风2级"},
            "广州": {"temp": 28, "condition": "小雨", "humidity": 80, "wind": "南风4级"},
            "深圳": {"temp": 27, "condition": "阴天", "humidity": 75, "wind": "东风3级"},
            "成都": {"temp": 18, "condition": "雾", "humidity": 85, "wind": "无持续风向"},
        }

        self.register_handler("query", self.handle_query)
        self.register_handler("forecast", self.handle_forecast)

    async def handle_query(self, message: A2AMessage) -> Dict:
        """查询天气"""
        city = message.payload.get("message", "").strip()

        logger.info(f"[天气查询] 查询城市: {city}")

        if city in self.weather_data:
            weather = self.weather_data[city]
            response_text = (
                f"📍 {city}当前天气：\n"
                f"🌡️ 温度：{weather['temp']}°C\n"
                f"☁️ 天气：{weather['condition']}\n"
                f"💧 湿度：{weather['humidity']}%\n"
                f"🌬️ 风力：{weather['wind']}"
            )
        else:
            available_cities = "、".join(self.weather_data.keys())
            response_text = f"抱歉，暂不支持查询 {city} 的天气。\n\n当前支持的城市：{available_cities}"

        return {
            "response": response_text,
            "city": city,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_forecast(self, message: A2AMessage) -> Dict:
        """天气预报（未来3天）"""
        city = message.payload.get("city", "")

        if city in self.weather_data:
            base_weather = self.weather_data[city]
            forecast = []

            for i in range(1, 4):
                day_weather = {
                    "day": f"未来第{i}天",
                    "temp_high": base_weather["temp"] + random.randint(-3, 5),
                    "temp_low": base_weather["temp"] - random.randint(3, 8),
                    "condition": random.choice(["晴", "多云", "阴", "小雨"])
                }
                forecast.append(day_weather)

            response_text = f"📍 {city} 未来3天天气预报：\n\n"
            for day in forecast:
                response_text += f"{day['day']}: {day['condition']} {day['temp_low']}~{day['temp_high']}°C\n"

            return {
                "response": response_text,
                "city": city,
                "forecast": forecast
            }
        else:
            return {
                "response": f"无法获取 {city} 的天气预报",
                "city": city
            }


class CalculatorAgent(BrokerAgent):
    """计算器Agent - 安全的数学计算"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "数学计算器", broker)
        self.register_handler("calculate", self.handle_calculate)

    async def handle_calculate(self, message: A2AMessage) -> Dict:
        """执行计算"""
        expression = message.payload.get("message", "").strip()

        logger.info(f"[计算器] 计算: {expression}")

        try:
            # 安全的数学计算（简化版）
            # 生产环境应使用 sympy 或 ast.literal_eval
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("表达式包含不允许的字符")

            result = eval(expression, {"__builtins__": {}}, {})

            response_text = f"🔢 计算结果：\n\n{expression} = {result}"

            return {
                "response": response_text,
                "expression": expression,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[计算器] 计算错误: {e}")
            return {
                "response": f"❌ 计算失败：{str(e)}\n\n请确保输入的是有效的数学表达式。",
                "expression": expression,
                "error": str(e)
            }


class TaskCoordinatorAgent(BrokerAgent):
    """任务协调器 - 使用LLM进行智能任务分解和协调"""

    def __init__(self, agent_id: str, broker: MessageBroker):
        super().__init__(agent_id, "任务协调器", broker)

        # 初始化LLM
        llm_config = default_config.llm
        self.llm = ChatOpenAI(
            model=llm_config.model,
            base_url=llm_config.api_base,
            api_key=llm_config.api_key,
            temperature=0.3,  # 较低温度，更确定性
            max_tokens=llm_config.max_tokens,
            timeout=llm_config.timeout,
        )

        self.register_handler("coordinate", self.handle_coordinate)

    async def handle_coordinate(self, message: A2AMessage) -> Dict:
        """协调多个Agent完成复杂任务"""
        task_description = message.payload.get("message", "")

        logger.info(f"[任务协调器] 协调任务: {task_description[:50]}...")

        try:
            # 使用LLM分析任务
            analysis_prompt = f"""分析以下用户请求，判断需要调用哪些Agent：

可用的Agent：
1. ai_assistant - AI智能助手，用于一般对话和问答
2. weather - 天气查询服务，查询城市天气
3. calculator - 数学计算器，执行数学运算

用户请求：{task_description}

请以JSON格式返回需要调用的Agent列表和参数，格式如下：
{{
    "agents": [
        {{"agent": "agent_name", "action": "action_name", "params": {{}}}},
        ...
    ],
    "explanation": "为什么需要这些Agent"
}}"""

            messages = [
                SystemMessage(content="你是一个任务分解专家，负责分析用户请求并决定调用哪些Agent。"),
                HumanMessage(content=analysis_prompt)
            ]

            response = await asyncio.to_thread(self.llm.invoke, messages)

            # 简化处理，实际应解析JSON
            result_text = f"📋 任务分析：\n\n{response.content}\n\n"
            result_text += "✅ 任务协调完成"

            return {
                "response": result_text,
                "task": task_description,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[任务协调器] 错误: {e}")
            return {
                "response": f"任务协调失败: {str(e)}",
                "error": True
            }
