"""
LangChain Agent API 测试客户端
演示如何调用各种 API 端点
"""

import asyncio
import json
import httpx
from typing import List, Dict


BASE_URL = "http://localhost:8000"


async def test_health_check():
    """测试健康检查"""
    print("\n" + "="*50)
    print("测试: 健康检查")
    print("="*50)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


async def test_simple_chat():
    """测试简单对话"""
    print("\n" + "="*50)
    print("测试: 简单对话（非流式）")
    print("="*50)
    
    messages = [
        "你好，请介绍一下自己",
        "现在几点了？",
        "帮我计算 123 * 456",
        "什么是LangChain？",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for msg in messages:
            print(f"\n用户: {msg}")
            response = await client.post(
                f"{BASE_URL}/agent/chat",
                json={
                    "message": msg,
                    "history": []
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Agent: {result['message']}")
                print(f"执行时间: {result['execution_time']:.2f}秒")
                
                if result['intermediate_steps']:
                    print("中间步骤:")
                    for step in result['intermediate_steps']:
                        print(f"  - 工具: {step['tool']}")
                        print(f"    输出: {step['output']}")
            else:
                print(f"错误: {response.status_code}")
                print(response.text)


async def test_chat_with_history():
    """测试带历史记录的对话"""
    print("\n" + "="*50)
    print("测试: 带历史记录的对话")
    print("="*50)
    
    history = []
    messages = [
        "帮我计算 100 + 200",
        "再乘以 3 呢？",
        "最后加上 50",
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for msg in messages:
            print(f"\n用户: {msg}")
            
            response = await client.post(
                f"{BASE_URL}/agent/chat",
                json={
                    "message": msg,
                    "history": history
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"Agent: {result['message']}")
                
                # 更新历史记录
                history.append({
                    "role": "user",
                    "content": msg
                })
                history.append({
                    "role": "assistant",
                    "content": result['message']
                })
            else:
                print(f"错误: {response.status_code}")
                print(response.text)
                break


async def test_stream_chat():
    """测试流式对话"""
    print("\n" + "="*50)
    print("测试: 流式对话")
    print("="*50)
    
    message = "帮我计算 999 * 888，然后告诉我现在的时间"
    print(f"\n用户: {message}")
    print("Agent (流式): ", end="", flush=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/agent/chat-stream",
            json={"message": message}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        if data['type'] == 'content':
                            print(data['data'], end="", flush=True)
                        
                        elif data['type'] == 'tool_start':
                            print(f"\n[使用工具: {data['tool']}]", flush=True)
                            print(f"[输入: {data['input']}]", flush=True)
                        
                        elif data['type'] == 'tool_end':
                            print(f"[输出: {data['output']}]", flush=True)
                        
                        elif data['type'] == 'done':
                            print("\n[完成]", flush=True)
                        
                        elif data['type'] == 'error':
                            print(f"\n[错误: {data['message']}]", flush=True)
                    
                    except json.JSONDecodeError:
                        pass


async def test_batch_chat():
    """测试批量请求"""
    print("\n" + "="*50)
    print("测试: 批量请求（异步并发）")
    print("="*50)
    
    requests = [
        {"message": "现在几点？"},
        {"message": "10 + 20 等于多少？"},
        {"message": "50 * 3 等于多少？"},
        {"message": "什么是Python？"},
        {"message": "什么是FastAPI？"},
    ]
    
    print(f"\n发送 {len(requests)} 个并发请求...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/agent/batch",
            json=requests
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n总计: {result['total']} 个请求")
            print(f"总执行时间: {result['execution_time']:.2f}秒")
            print(f"平均每个请求: {result['execution_time']/result['total']:.2f}秒")
            
            print("\n结果:")
            for item in result['results']:
                idx = item['index']
                print(f"\n请求 #{idx + 1}: {requests[idx]['message']}")
                if item['success']:
                    print(f"回复: {item['message'][:100]}...")
                else:
                    print(f"错误: {item['error']}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("LangChain Agent API 测试套件")
    print("="*70)
    
    try:
        # 测试1: 健康检查
        await test_health_check()
        await asyncio.sleep(1)
        
        # 测试2: 简单对话
        await test_simple_chat()
        await asyncio.sleep(1)
        
        # 测试3: 带历史记录的对话
        await test_chat_with_history()
        await asyncio.sleep(1)
        
        # 测试4: 流式对话
        await test_stream_chat()
        await asyncio.sleep(1)
        
        # 测试5: 批量请求
        await test_batch_chat()
        
        print("\n" + "="*70)
        print("所有测试完成！")
        print("="*70)
    
    except httpx.ConnectError:
        print("\n错误: 无法连接到服务器")
        print("请确保服务已启动: python langchain_demo.py")
    
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


async def interactive_mode():
    """交互式模式"""
    print("\n" + "="*70)
    print("交互式对话模式")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空历史记录")
    print("="*70)
    
    history = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                user_input = input("\n你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("再见！")
                    break
                
                if user_input.lower() == 'clear':
                    history = []
                    print("历史记录已清空")
                    continue
                
                response = await client.post(
                    f"{BASE_URL}/agent/chat",
                    json={
                        "message": user_input,
                        "history": history
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\nAgent: {result['message']}")
                    
                    if result['intermediate_steps']:
                        print("\n[使用的工具:]")
                        for step in result['intermediate_steps']:
                            print(f"  • {step['tool']}: {step['output'][:80]}...")
                    
                    # 更新历史记录
                    history.append({
                        "role": "user",
                        "content": user_input
                    })
                    history.append({
                        "role": "assistant",
                        "content": result['message']
                    })
                else:
                    print(f"\n错误: {response.status_code}")
                    print(response.text)
            
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            
            except httpx.ConnectError:
                print("\n错误: 无法连接到服务器")
                print("请确保服务已启动: python langchain_demo.py")
                break
            
            except Exception as e:
                print(f"\n错误: {e}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        # 交互式模式
        asyncio.run(interactive_mode())
    else:
        # 运行所有测试
        asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()

