"""
A2A协议完整示例
演示多个Agent之间的通信和协作
"""
import asyncio
import logging

from a2a.message_broker import MessageBroker
from a2a.demo_agents import (
    WeatherAgent,
    DataAnalysisAgent,
    TaskCoordinatorAgent,
    MonitorAgent
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_communication():
    """示例1: 基本的Agent间通信"""
    print("\n" + "="*60)
    print("示例1: 基本Agent通信")
    print("="*60)

    broker = MessageBroker()

    # 创建Agents
    weather_agent = WeatherAgent("weather_agent", broker)
    analysis_agent = DataAnalysisAgent("analysis_agent", broker)

    # 启动Agents
    await weather_agent.start()
    await analysis_agent.start()

    try:
        # 1. 查询天气
        print("\n>>> 查询北京天气...")
        result = await weather_agent.send_request(
            "weather_agent",
            "query_weather",
            {"city": "beijing"}
        )
        print(f"天气查询结果: {result}")

        # 2. 数据分析
        print("\n>>> 分析数据...")
        result = await analysis_agent.send_request(
            "analysis_agent",
            "analyze_data",
            {"data": [10, 20, 30, 40, 50]}
        )
        print(f"分析结果: {result}")

    finally:
        await weather_agent.stop()
        await analysis_agent.stop()


async def demo_multi_agent_coordination():
    """示例2: 多Agent协作"""
    print("\n" + "="*60)
    print("示例2: 多Agent协作 - 天气分析任务")
    print("="*60)

    broker = MessageBroker()

    # 创建Agents
    weather_agent = WeatherAgent("weather_agent", broker)
    analysis_agent = DataAnalysisAgent("analysis_agent", broker)
    coordinator = TaskCoordinatorAgent("coordinator", broker)

    # 启动Agents
    await weather_agent.start()
    await analysis_agent.start()
    await coordinator.start()

    try:
        # 协调器发起复杂任务
        print("\n>>> 协调器发起天气分析任务...")
        result = await coordinator.send_request(
            "coordinator",
            "coordinate_task",
            {
                "task_type": "weather_analysis",
                "cities": ["beijing", "shanghai", "guangzhou"]
            },
            timeout=30.0  # 增加超时时间
        )

        print(f"\n任务完成! 结果:")
        print(f"城市天气信息:")
        for info in result.get("weather_info", []):
            city = info["city"]
            data = info["data"]
            print(f"  - {city}: {data['temperature']}°C, {data['condition']}")

        stats = result.get("temperature_stats", {})
        print(f"\n温度统计:")
        print(f"  平均温度: {stats.get('mean', 0):.1f}°C")
        print(f"  标准差: {stats.get('std_dev', 0):.1f}")

    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        # 确保在停止前有足够时间处理消息
        await asyncio.sleep(0.5)
        await coordinator.stop()
        await weather_agent.stop()
        await analysis_agent.stop()


async def demo_notification_system():
    """示例3: 通知系统"""
    print("\n" + "="*60)
    print("示例3: 事件通知系统")
    print("="*60)

    broker = MessageBroker()

    # 创建Agents
    weather_agent = WeatherAgent("weather_agent", broker)
    monitor_agent = MonitorAgent("monitor_agent", broker)

    # 启动Agents
    await weather_agent.start()
    await monitor_agent.start()

    try:
        # 发送系统事件通知
        print("\n>>> 发送系统事件...")

        await weather_agent.send_notification(
            "monitor_agent",
            "system_event",
            {
                "type": "weather_update",
                "description": "天气数据已更新",
                "affected_cities": ["beijing", "shanghai"]
            }
        )

        await asyncio.sleep(0.5)

        await weather_agent.send_notification(
            "monitor_agent",
            "system_event",
            {
                "type": "api_call",
                "description": "外部API调用",
                "endpoint": "/weather/query"
            }
        )

        await asyncio.sleep(0.5)

        # 查看监控日志
        print("\n监控日志摘要:")
        events = monitor_agent.get_event_log()
        for idx, event in enumerate(events, 1):
            print(f"{idx}. [{event['timestamp']}] {event['event']['type']}: {event['event']['description']}")

    finally:
        await weather_agent.stop()
        await monitor_agent.stop()


async def demo_concurrent_requests():
    """示例4: 并发请求处理"""
    print("\n" + "="*60)
    print("示例4: 并发请求处理")
    print("="*60)

    broker = MessageBroker()

    weather_agent = WeatherAgent("weather_agent", broker)
    analysis_agent = DataAnalysisAgent("analysis_agent", broker)

    await weather_agent.start()
    await analysis_agent.start()

    try:
        print("\n>>> 并发发送多个请求...")

        # 并发发送多个不同类型的请求
        tasks = [
            weather_agent.send_request("weather_agent", "query_weather", {"city": "beijing"}),
            weather_agent.send_request("weather_agent", "query_weather", {"city": "shanghai"}),
            analysis_agent.send_request("analysis_agent", "analyze_data", {"data": [1, 2, 3, 4, 5]}),
            analysis_agent.send_request("analysis_agent", "calculate_stats", {"numbers": [10, 20, 30]}),
        ]

        results = await asyncio.gather(*tasks)

        print("\n所有请求完成!")
        for idx, result in enumerate(results, 1):
            print(f"结果 {idx}: {result}")

    finally:
        await weather_agent.stop()
        await analysis_agent.stop()


async def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("A2A协议完整示例 Demo")
    print("="*60)

    # 运行所有示例
    await demo_basic_communication()
    await asyncio.sleep(1)

    await demo_multi_agent_coordination()
    await asyncio.sleep(1)

    await demo_notification_system()
    await asyncio.sleep(1)

    await demo_concurrent_requests()

    print("\n" + "="*60)
    print("所有示例完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
