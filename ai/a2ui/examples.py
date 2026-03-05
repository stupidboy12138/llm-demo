"""
A2UI使用示例集合
展示各种使用场景和最佳实践
"""
import asyncio
import aiohttp
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


# ============================================================================
# 示例1: 基础聊天
# ============================================================================

async def example_basic_chat():
    """示例: 基础AI对话"""
    logger.info("\n" + "=" * 60)
    logger.info("示例1: 基础AI对话")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        messages = [
            "你好！",
            "你能做什么？",
            "帮我总结一下你的功能"
        ]

        for msg in messages:
            logger.info(f"\n用户: {msg}")

            async with session.post(f"{BASE_URL}/chat", json={
                "message": msg,
                "session_id": "example1",
                "agent_type": "ai_assistant"
            }) as response:
                data = await response.json()
                logger.info(f"AI: {data['response']}")

            await asyncio.sleep(1)


# ============================================================================
# 示例2: 多Agent使用
# ============================================================================

async def example_multiple_agents():
    """示例: 使用不同的Agent"""
    logger.info("\n" + "=" * 60)
    logger.info("示例2: 多Agent使用")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        # AI助手
        logger.info("\n--- AI助手 ---")
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "你好，请介绍你自己",
            "agent_type": "ai_assistant"
        }) as response:
            data = await response.json()
            logger.info(f"AI: {data['response']}")

        await asyncio.sleep(1)

        # 天气查询
        logger.info("\n--- 天气查询 ---")
        cities = ["北京", "上海", "广州"]
        for city in cities:
            async with session.post(f"{BASE_URL}/chat", json={
                "message": city,
                "agent_type": "weather"
            }) as response:
                data = await response.json()
                logger.info(f"{city}: {data['response']}")
            await asyncio.sleep(0.5)

        # 计算器
        logger.info("\n--- 计算器 ---")
        calculations = [
            "100 + 200",
            "(50 + 30) * 2",
            "999 / 3"
        ]
        for calc in calculations:
            async with session.post(f"{BASE_URL}/chat", json={
                "message": calc,
                "agent_type": "calculator"
            }) as response:
                data = await response.json()
                logger.info(f"{calc} = {data['response']}")
            await asyncio.sleep(0.5)


# ============================================================================
# 示例3: 并发请求
# ============================================================================

async def example_concurrent_requests():
    """示例: 并发处理多个请求"""
    logger.info("\n" + "=" * 60)
    logger.info("示例3: 并发请求处理")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 创建多个并发任务
        tasks = [
            session.post(f"{BASE_URL}/chat", json={
                "message": "你好",
                "agent_type": "ai_assistant"
            }),
            session.post(f"{BASE_URL}/chat", json={
                "message": "北京",
                "agent_type": "weather"
            }),
            session.post(f"{BASE_URL}/chat", json={
                "message": "上海",
                "agent_type": "weather"
            }),
            session.post(f"{BASE_URL}/chat", json={
                "message": "100 * 99",
                "agent_type": "calculator"
            }),
            session.post(f"{BASE_URL}/chat", json={
                "message": "200 + 300",
                "agent_type": "calculator"
            }),
        ]

        logger.info(f"发送 {len(tasks)} 个并发请求...")

        # 并发执行
        responses = await asyncio.gather(*tasks)

        # 处理响应
        for i, response in enumerate(responses, 1):
            data = await response.json()
            logger.info(f"{i}. {data['response'][:80]}...")

        logger.info(f"\n完成 {len(responses)} 个并发请求")


# ============================================================================
# 示例4: 会话管理
# ============================================================================

async def example_session_management():
    """示例: 会话历史管理"""
    logger.info("\n" + "=" * 60)
    logger.info("示例4: 会话历史管理")
    logger.info("=" * 60)

    session_id = "session_demo"

    async with aiohttp.ClientSession() as session:
        # 发送多条消息
        messages = [
            "我叫张三",
            "我今年25岁",
            "我喜欢编程",
            "你还记得我的名字吗？"
        ]

        for msg in messages:
            logger.info(f"\n用户: {msg}")
            async with session.post(f"{BASE_URL}/chat", json={
                "message": msg,
                "session_id": session_id,
                "agent_type": "ai_assistant"
            }) as response:
                data = await response.json()
                logger.info(f"AI: {data['response']}")
            await asyncio.sleep(1)

        # 获取会话历史
        logger.info("\n--- 会话历史 ---")
        async with session.get(f"{BASE_URL}/history/{session_id}") as response:
            data = await response.json()
            logger.info(f"历史记录数: {data['count']}")
            for i, item in enumerate(data['history'], 1):
                logger.info(f"{i}. [{item['role']}] {item['content'][:50]}...")

        # 清除历史
        logger.info("\n清除会话历史...")
        async with session.delete(f"{BASE_URL}/history/{session_id}") as response:
            data = await response.json()
            logger.info(f"清除结果: {data}")


# ============================================================================
# 示例5: WebSocket实时通信
# ============================================================================

async def example_websocket():
    """示例: WebSocket实时通信"""
    logger.info("\n" + "=" * 60)
    logger.info("示例5: WebSocket实时通信")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"ws://localhost:8000/ws/example_client") as ws:
            logger.info("WebSocket连接已建立")

            # 发送消息并接收响应
            messages = [
                ("ai_assistant", "你好，这是WebSocket通信"),
                ("weather", "北京"),
                ("calculator", "123 + 456"),
            ]

            for agent_type, msg in messages:
                logger.info(f"\n发送 [{agent_type}]: {msg}")

                # 发送
                await ws.send_json({
                    "type": "chat",
                    "message": msg,
                    "agent_type": agent_type
                })

                # 接收ACK和响应
                async for response in ws:
                    if response.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(response.data)

                        if data['type'] == 'ack':
                            logger.info("收到确认")
                        elif data['type'] == 'response':
                            logger.info(f"响应: {data['message']}")
                            break

                await asyncio.sleep(1)

            logger.info("\nWebSocket通信完成")


# ============================================================================
# 示例6: 错误处理
# ============================================================================

async def example_error_handling():
    """示例: 错误处理和重试"""
    logger.info("\n" + "=" * 60)
    logger.info("示例6: 错误处理")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 测试不支持的城市
        logger.info("\n--- 测试错误情况 ---")

        # 不存在的城市
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "火星",
            "agent_type": "weather"
        }) as response:
            data = await response.json()
            logger.info(f"查询火星天气: {data['response']}")

        # 无效的计算表达式
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "abc + xyz",
            "agent_type": "calculator"
        }) as response:
            data = await response.json()
            logger.info(f"无效计算: {data['response']}")

        # 带超时的重试
        logger.info("\n--- 重试机制 ---")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with session.post(
                    f"{BASE_URL}/chat",
                    json={"message": "测试", "agent_type": "ai_assistant"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    data = await response.json()
                    logger.info(f"请求成功: {data['response'][:50]}...")
                    break
            except asyncio.TimeoutError:
                logger.warning(f"尝试 {attempt + 1}/{max_retries} 超时")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    logger.error("所有重试均失败")


# ============================================================================
# 示例7: 批量处理
# ============================================================================

async def example_batch_processing():
    """示例: 批量处理多个请求"""
    logger.info("\n" + "=" * 60)
    logger.info("示例7: 批量处理")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 批量查询多个城市天气
        cities = ["北京", "上海", "广州", "深圳", "成都"]

        logger.info(f"批量查询 {len(cities)} 个城市的天气...")

        tasks = []
        for city in cities:
            task = session.post(f"{BASE_URL}/chat", json={
                "message": city,
                "agent_type": "weather"
            })
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        logger.info("\n天气查询结果:")
        for city, response in zip(cities, responses):
            data = await response.json()
            logger.info(f"  {city}: {data['response']}")


# ============================================================================
# 示例8: 复杂工作流
# ============================================================================

async def example_complex_workflow():
    """示例: 复杂的多步骤工作流"""
    logger.info("\n" + "=" * 60)
    logger.info("示例8: 复杂工作流")
    logger.info("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 场景: 旅行规划助手
        logger.info("\n场景: 旅行规划")

        # 步骤1: 询问目的地建议
        logger.info("\n步骤1: 询问AI建议")
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "我想去旅游，你有什么建议吗？",
            "session_id": "travel_plan",
            "agent_type": "ai_assistant"
        }) as response:
            data = await response.json()
            logger.info(f"AI建议: {data['response']}")

        await asyncio.sleep(1)

        # 步骤2: 查询多个城市天气
        logger.info("\n步骤2: 查询候选城市天气")
        cities = ["北京", "上海", "广州"]

        weather_tasks = []
        for city in cities:
            task = session.post(f"{BASE_URL}/chat", json={
                "message": city,
                "agent_type": "weather"
            })
            weather_tasks.append(task)

        weather_responses = await asyncio.gather(*weather_tasks)

        for city, response in zip(cities, weather_responses):
            data = await response.json()
            logger.info(f"  {city}: {data['response']}")

        await asyncio.sleep(1)

        # 步骤3: 计算旅行预算
        logger.info("\n步骤3: 计算预算")
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "(3000 + 2000 + 1500) / 3",
            "agent_type": "calculator"
        }) as response:
            data = await response.json()
            logger.info(f"平均预算: {data['response']}")

        # 步骤4: 总结
        logger.info("\n步骤4: AI总结")
        async with session.post(f"{BASE_URL}/chat", json={
            "message": "根据天气和预算，给出最终建议",
            "session_id": "travel_plan",
            "agent_type": "ai_assistant"
        }) as response:
            data = await response.json()
            logger.info(f"最终建议: {data['response']}")


# ============================================================================
# 主函数
# ============================================================================

async def run_all_examples():
    """运行所有示例"""
    logger.info("\n" + "=" * 60)
    logger.info("A2UI 完整示例演示")
    logger.info("=" * 60)

    # 检查服务是否运行
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                health = await response.json()
                logger.info(f"\n服务状态: {health['status']}")
    except Exception as e:
        logger.error(f"\n❌ 无法连接到服务器: {e}")
        logger.error("请先启动服务: python -m ai.a2ui.demo")
        return

    # 运行示例
    examples = [
        ("基础聊天", example_basic_chat),
        ("多Agent使用", example_multiple_agents),
        ("并发请求", example_concurrent_requests),
        ("会话管理", example_session_management),
        ("WebSocket通信", example_websocket),
        ("错误处理", example_error_handling),
        ("批量处理", example_batch_processing),
        ("复杂工作流", example_complex_workflow),
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            await func()
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"\n❌ 示例 '{name}' 失败: {e}")

        if i < len(examples):
            logger.info("\n" + "-" * 60)
            await asyncio.sleep(1)

    logger.info("\n" + "=" * 60)
    logger.info("所有示例完成！")
    logger.info("=" * 60)


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        example_name = sys.argv[1]

        examples_map = {
            "1": example_basic_chat,
            "basic": example_basic_chat,
            "2": example_multiple_agents,
            "agents": example_multiple_agents,
            "3": example_concurrent_requests,
            "concurrent": example_concurrent_requests,
            "4": example_session_management,
            "session": example_session_management,
            "5": example_websocket,
            "ws": example_websocket,
            "6": example_error_handling,
            "error": example_error_handling,
            "7": example_batch_processing,
            "batch": example_batch_processing,
            "8": example_complex_workflow,
            "workflow": example_complex_workflow,
        }

        example_func = examples_map.get(example_name)

        if example_func:
            asyncio.run(example_func())
        else:
            print(f"未知示例: {example_name}")
            print("\n可用示例:")
            print("  1/basic     - 基础聊天")
            print("  2/agents    - 多Agent使用")
            print("  3/concurrent - 并发请求")
            print("  4/session   - 会话管理")
            print("  5/ws        - WebSocket通信")
            print("  6/error     - 错误处理")
            print("  7/batch     - 批量处理")
            print("  8/workflow  - 复杂工作流")
    else:
        # 运行所有示例
        asyncio.run(run_all_examples())


if __name__ == "__main__":
    main()
