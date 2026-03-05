"""
A2A协议简化示例
清晰演示Agent之间的通信
"""
import asyncio
from a2a.message_broker import MessageBroker
from a2a.demo_agents import WeatherAgent, DataAnalysisAgent


async def main():
    """简单演示"""
    print("=" * 60)
    print("A2A Protocol Simple Demo")
    print("=" * 60)

    # 创建消息代理
    broker = MessageBroker()

    # 创建Agent
    weather = WeatherAgent("weather_agent", broker)
    analysis = DataAnalysisAgent("analysis_agent", broker)

    # 启动Agent
    await weather.start()
    await analysis.start()

    print("\n[1] Query Weather")
    print("-" * 60)
    result = await weather.send_request(
        "weather_agent",
        "query_weather",
        {"city": "beijing"}
    )
    print(f"City: {result['city']}")
    print(f"Temperature: {result['data']['temperature']}°C")
    print(f"Condition: {result['data']['condition']}")
    print(f"Humidity: {result['data']['humidity']}%")

    print("\n[2] Analyze Data")
    print("-" * 60)
    data = [15, 23, 18, 31, 27, 19, 22]
    result = await analysis.send_request(
        "analysis_agent",
        "analyze_data",
        {"data": data}
    )
    print(f"Data: {data}")
    print(f"Count: {result['count']}")
    print(f"Sum: {result['sum']}")
    print(f"Average: {result['avg']:.2f}")
    print(f"Max: {result['max']}")
    print(f"Min: {result['min']}")

    print("\n[3] Calculate Statistics")
    print("-" * 60)
    numbers = [10, 20, 30, 40, 50]
    result = await analysis.send_request(
        "analysis_agent",
        "calculate_stats",
        {"numbers": numbers}
    )
    print(f"Numbers: {numbers}")
    print(f"Mean: {result['mean']:.2f}")
    print(f"Variance: {result['variance']:.2f}")
    print(f"Standard Deviation: {result['std_dev']:.2f}")

    print("\n[4] Query Multiple Cities")
    print("-" * 60)
    cities = ["beijing", "shanghai", "guangzhou"]
    tasks = []
    for city in cities:
        task = weather.send_request(
            "weather_agent",
            "query_weather",
            {"city": city}
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    for result in results:
        if result['status'] == 'success':
            print(f"{result['city'].title()}: "
                  f"{result['data']['temperature']}°C, "
                  f"{result['data']['condition']}, "
                  f"Humidity {result['data']['humidity']}%")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

    # 停止Agent
    await weather.stop()
    await analysis.stop()


if __name__ == "__main__":
    # 禁用日志输出,使结果更清晰
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    asyncio.run(main())
