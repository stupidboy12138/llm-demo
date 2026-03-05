"""
示例Agent实现
包含各种功能的示例Agent
"""
from .agent_impl import BrokerAgent
from .protocol import A2AMessage
from typing import Dict
import asyncio


class WeatherAgent(BrokerAgent):
    """天气查询Agent"""

    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "WeatherAgent", broker)

        # 模拟天气数据
        self.weather_data = {
            "beijing": {"temperature": -5, "condition": "晴天", "humidity": 30},
            "shanghai": {"temperature": 8, "condition": "多云", "humidity": 60},
            "guangzhou": {"temperature": 18, "condition": "阴天", "humidity": 75},
        }

        # 注册处理器
        self.register_handler("query_weather", self.handle_query_weather)

    async def handle_query_weather(self, message: A2AMessage) -> Dict:
        """处理天气查询请求"""
        city = message.payload.get("city", "").lower()

        await asyncio.sleep(0.5)  # 模拟查询延迟

        if city in self.weather_data:
            return {
                "city": city,
                "data": self.weather_data[city],
                "status": "success"
            }
        else:
            return {
                "city": city,
                "error": f"未找到城市: {city}",
                "status": "error"
            }


class DataAnalysisAgent(BrokerAgent):
    """数据分析Agent"""

    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "DataAnalysisAgent", broker)
        self.register_handler("analyze_data", self.handle_analyze_data)
        self.register_handler("calculate_stats", self.handle_calculate_stats)

    async def handle_analyze_data(self, message: A2AMessage) -> Dict:
        """处理数据分析请求"""
        data = message.payload.get("data", [])

        await asyncio.sleep(0.3)  # 模拟分析时间

        if not data:
            return {"error": "没有提供数据", "status": "error"}

        return {
            "count": len(data),
            "sum": sum(data),
            "avg": sum(data) / len(data),
            "max": max(data),
            "min": min(data),
            "status": "success"
        }

    async def handle_calculate_stats(self, message: A2AMessage) -> Dict:
        """计算统计信息"""
        numbers = message.payload.get("numbers", [])

        if not numbers:
            return {"error": "没有提供数字", "status": "error"}

        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)

        return {
            "mean": mean,
            "variance": variance,
            "std_dev": variance ** 0.5,
            "status": "success"
        }


class TaskCoordinatorAgent(BrokerAgent):
    """任务协调Agent - 协调其他Agent完成复杂任务"""

    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "TaskCoordinatorAgent", broker)
        self.register_handler("coordinate_task", self.handle_coordinate_task)

    async def handle_coordinate_task(self, message: A2AMessage) -> Dict:
        """协调多个Agent完成任务"""
        task_type = message.payload.get("task_type")

        if task_type == "weather_analysis":
            return await self._handle_weather_analysis(message)
        else:
            return {"error": f"未知任务类型: {task_type}", "status": "error"}

    async def _handle_weather_analysis(self, message: A2AMessage) -> Dict:
        """处理天气分析任务 - 协调WeatherAgent和DataAnalysisAgent"""
        cities = message.payload.get("cities", [])

        if not cities:
            return {"error": "没有提供城市列表", "status": "error"}

        # 并发查询多个城市的天气
        weather_tasks = []
        for city in cities:
            task = self.send_request(
                "weather_agent",
                "query_weather",
                {"city": city}
            )
            weather_tasks.append(task)

        weather_results = await asyncio.gather(*weather_tasks, return_exceptions=True)

        # 收集温度数据
        temperatures = []
        weather_info = []

        for result in weather_results:
            if isinstance(result, Exception):
                continue
            if result.get("status") == "success":
                weather_info.append(result)
                temperatures.append(result["data"]["temperature"])

        # 如果有温度数据，发送给分析Agent
        if temperatures:
            stats_result = await self.send_request(
                "analysis_agent",
                "calculate_stats",
                {"numbers": temperatures}
            )

            return {
                "weather_info": weather_info,
                "temperature_stats": stats_result,
                "status": "success"
            }
        else:
            return {"error": "没有获取到有效的天气数据", "status": "error"}


class MonitorAgent(BrokerAgent):
    """监控Agent - 监听系统事件"""

    def __init__(self, agent_id: str, broker):
        super().__init__(agent_id, "MonitorAgent", broker)
        self.event_log = []
        self.register_handler("system_event", self.handle_system_event)

    async def handle_system_event(self, message: A2AMessage) -> Dict:
        """处理系统事件"""
        event = message.payload
        self.event_log.append({
            "timestamp": message.timestamp,
            "sender": message.sender_id,
            "event": event
        })

        print(f"\n[监控] 收到事件: {event.get('type')} - {event.get('description')}")

        return {"status": "logged"}

    def get_event_log(self):
        """获取事件日志"""
        return self.event_log
