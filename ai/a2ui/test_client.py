"""
A2UI测试客户端
展示如何通过HTTP API和WebSocket与A2UI服务交互
"""
import asyncio
import aiohttp
import json
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


async def test_health_check():
    """测试健康检查"""
    logger.info("\n=== 测试健康检查 ===")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            data = await response.json()
            logger.info(f"健康状态: {json.dumps(data, indent=2, ensure_ascii=False)}")


async def test_list_agents():
    """测试获取Agent列表"""
    logger.info("\n=== 测试Agent列表 ===")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/agents") as response:
            data = await response.json()
            logger.info(f"可用Agent: {json.dumps(data, indent=2, ensure_ascii=False)}")


async def test_chat_with_ai(message: str, session_id: str = "test_session"):
    """测试与AI助手聊天"""
    logger.info(f"\n=== 测试AI聊天 ===")
    logger.info(f"用户: {message}")

    payload = {
        "message": message,
        "session_id": session_id,
        "agent_type": "ai_assistant"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/chat", json=payload) as response:
            data = await response.json()
            logger.info(f"AI助手: {data['response']}")
            return data


async def test_weather_query(city: str):
    """测试天气查询"""
    logger.info(f"\n=== 测试天气查询 ===")
    logger.info(f"查询城市: {city}")

    payload = {
        "message": city,
        "session_id": "weather_test",
        "agent_type": "weather"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/chat", json=payload) as response:
            data = await response.json()
            logger.info(f"天气结果: {data['response']}")
            return data


async def test_calculator(expression: str):
    """测试计算器"""
    logger.info(f"\n=== 测试计算器 ===")
    logger.info(f"表达式: {expression}")

    payload = {
        "message": expression,
        "session_id": "calc_test",
        "agent_type": "calculator"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/chat", json=payload) as response:
            data = await response.json()
            logger.info(f"计算结果: {data['response']}")
            return data


async def test_conversation_history(session_id: str = "test_session"):
    """测试获取对话历史"""
    logger.info(f"\n=== 测试对话历史 ===")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/history/{session_id}") as response:
            data = await response.json()
            logger.info(f"历史记录数: {data['count']}")
            for i, msg in enumerate(data['history'], 1):
                logger.info(f"  {i}. [{msg['role']}] {msg['content'][:50]}...")
            return data


async def test_websocket_chat():
    """测试WebSocket实时聊天"""
    logger.info("\n=== 测试WebSocket聊天 ===")

    client_id = "test_ws_client"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{WS_URL}/ws/{client_id}") as ws:
            logger.info("WebSocket连接已建立")

            # 发送聊天消息
            messages = [
                "你好！",
                "今天天气怎么样？",
                "帮我计算 100 + 200",
            ]

            for msg in messages:
                logger.info(f"\n发送: {msg}")

                await ws.send_json({
                    "type": "chat",
                    "message": msg,
                    "agent_type": "ai_assistant"
                })

                # 接收响应
                async for response in ws:
                    if response.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(response.data)
                        logger.info(f"收到 [{data['type']}]: {data.get('message', data)}")

                        if data['type'] == 'response':
                            break

                await asyncio.sleep(1)

            logger.info("\nWebSocket测试完成")


async def test_multiple_queries():
    """测试并发查询多个Agent"""
    logger.info("\n=== 测试并发查询 ===")

    tasks = [
        test_chat_with_ai("你好，AI助手！", "concurrent_1"),
        test_weather_query("北京"),
        test_weather_query("上海"),
        test_calculator("123 + 456"),
        test_calculator("100 * 99"),
    ]

    results = await asyncio.gather(*tasks)
    logger.info(f"\n完成 {len(results)} 个并发请求")


async def run_interactive_demo():
    """交互式演示"""
    logger.info("\n" + "=" * 60)
    logger.info("A2UI 交互式演示")
    logger.info("=" * 60)

    # 1. 健康检查
    await test_health_check()
    await asyncio.sleep(1)

    # 2. 获取Agent列表
    await test_list_agents()
    await asyncio.sleep(1)

    # 3. AI对话测试
    await test_chat_with_ai("你好！")
    await asyncio.sleep(1)
    await test_chat_with_ai("你能做什么？")
    await asyncio.sleep(1)

    # 4. 天气查询测试
    await test_weather_query("北京")
    await asyncio.sleep(1)
    await test_weather_query("上海")
    await asyncio.sleep(1)

    # 5. 计算器测试
    await test_calculator("(100 + 200) * 3")
    await asyncio.sleep(1)
    await test_calculator("999 / 3")
    await asyncio.sleep(1)

    # 6. 查看对话历史
    await test_conversation_history()
    await asyncio.sleep(1)

    # 7. 并发测试
    await test_multiple_queries()
    await asyncio.sleep(1)

    # 8. WebSocket测试
    try:
        await test_websocket_chat()
    except Exception as e:
        logger.error(f"WebSocket测试失败: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("所有测试完成！")
    logger.info("=" * 60)


async def simple_chat():
    """简单的命令行聊天界面"""
    logger.info("\n=== A2UI 命令行聊天 ===")
    logger.info("输入 'quit' 退出")
    logger.info("输入 '/weather 城市名' 查询天气")
    logger.info("输入 '/calc 表达式' 进行计算")
    logger.info("-" * 40)

    session_id = "cli_session"

    while True:
        try:
            user_input = input("\n你: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'quit':
                logger.info("再见！")
                break

            # 解析命令
            if user_input.startswith("/weather "):
                city = user_input[9:].strip()
                await test_weather_query(city)

            elif user_input.startswith("/calc "):
                expression = user_input[6:].strip()
                await test_calculator(expression)

            else:
                await test_chat_with_ai(user_input, session_id)

        except KeyboardInterrupt:
            logger.info("\n\n再见！")
            break
        except Exception as e:
            logger.error(f"错误: {e}")


def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # 命令行聊天模式
        asyncio.run(simple_chat())
    else:
        # 自动化测试模式
        asyncio.run(run_interactive_demo())


if __name__ == "__main__":
    main()
